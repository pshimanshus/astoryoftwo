"""Actual-pixel QA and final audit for carousel packages.

The default path has no run ledger, agent report, approval ledger, Event A
provenance graph, or markdown checklist. Pre-generation prose can improve a
prompt, but only exact generated pixels can pass this module.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    SUPPORTED_NATIVE_FORMATS,
    expected_output_path,
    format_spec,
    locked_format_contract_fingerprint,
    locked_formats,
)


QUALITY_ARTIFACTS = {
    "proof_qa": "proof-qa.json",
    "visual_qa": "visual-qa.json",
    "final_images": "final-images.json",
    "final_audit": "final-audit.json",
}

BRANDMARK_PLACEMENT = "top-right"


@dataclass
class QualityContext:
    story: str
    title: str
    slug: str
    today: date
    out_dir: Path
    image_paths: list[Path]
    slide_count: int
    package: dict[str, Any]
    manifest: dict[str, Any]
    render_result: dict[str, Any]
    workspace_root: Path
    asset_root: Path | None = None
    visual_qa_path: Path | None = None


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _png_dimensions(path: Path) -> tuple[int, int]:
    payload = path.read_bytes()
    if len(payload) < 24 or payload[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("not a PNG")
    return int.from_bytes(payload[16:20], "big"), int.from_bytes(payload[20:24], "big")


def _records(value: Any, *, key: str = "slides") -> list[dict[str, Any]]:
    if isinstance(value, dict):
        value = value.get(key)
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []


def _pass(value: Any) -> bool:
    return isinstance(value, dict) and (
        value.get("pass") is True or str(value.get("status") or "").upper() == "PASS"
    )


def validate_anatomy_inventory_check(check: Any, *, slide_count: int) -> list[str]:
    issues: list[str] = []
    records = _records(check)
    if len(records) != slide_count:
        return [f"anatomy_inventory has {len(records)} slide records, expected {slide_count}"]
    for record in records:
        number = int(record.get("slide", 0) or 0)
        if _pass(record):
            continue
        expected_arms, observed_arms = record.get("expected_arms"), record.get("observed_arms")
        expected_hands, observed_hands = record.get("expected_hands"), record.get("observed_hands")
        if not all(isinstance(value, int) for value in (expected_arms, observed_arms, expected_hands, observed_hands)):
            issues.append(f"slide {number} anatomy inventory needs integer arm/hand counts")
            continue
        if expected_arms != observed_arms or expected_hands != observed_hands:
            issues.append(f"slide {number} anatomy inventory count mismatch")
        if record.get("unexpected_limbs") or record.get("duplicated_limbs"):
            issues.append(f"slide {number} anatomy inventory reports extra/duplicated limbs")
        if record.get("malformed_fingers") not in (False, [], None):
            issues.append(f"slide {number} anatomy inventory reports malformed fingers")
        hands = record.get("visible_hands")
        if isinstance(hands, list):
            for hand_index, hand in enumerate(hands, start=1):
                if not isinstance(hand, dict):
                    issues.append(f"slide {number} visible hand {hand_index} is malformed")
                    continue
                if not str(hand.get("owner") or "").strip():
                    issues.append(
                        f"slide {number} visible hand {hand_index} is not required by the locked scene and has no owner"
                    )
                elif hand.get("story_required") is False:
                    issues.append(
                        f"slide {number} visible hand {hand_index} is not required by the locked scene"
                    )
                if hand.get("attachment_visible") is False:
                    issues.append(f"slide {number} visible hand {hand_index} is not attached to a traceable arm")
                if hand.get("edge_entry_unexplained") is True:
                    issues.append(f"slide {number} visible hand {hand_index} has unexplained edge entry")
                if hand.get("contact_geometry_pass") is False:
                    issues.append(f"slide {number} visible hand {hand_index} fails hand-object contact geometry")
                if hand.get("solid_object_intersection") is True:
                    issues.append(f"slide {number} visible hand {hand_index} intersects or may intersect a solid object")
    return issues


def validate_spatial_topology_check(check: Any, *, slide_count: int) -> list[str]:
    issues: list[str] = []
    records = _records(check)
    if len(records) != slide_count:
        return [f"spatial_topology has {len(records)} slide records, expected {slide_count}"]
    for record in records:
        number = int(record.get("slide", 0) or 0)
        if _pass(record):
            continue
        for key in ("body_environment", "hand_object_contact", "person_separation"):
            value = record.get(key)
            if isinstance(value, dict) and not _pass(value):
                issues.append(f"slide {number} spatial topology failed {key}")
        if record.get("issues"):
            issues.append(f"slide {number} spatial topology reports visible defects")
        people = record.get("people")
        if isinstance(people, list):
            for person in people:
                if not isinstance(person, dict):
                    continue
                name = str(person.get("person") or "person")
                if person.get("silhouette_traceable") is False:
                    issues.append(f"slide {number} {name} silhouette is not fully traceable")
                for region in person.get("body_regions") or []:
                    if not isinstance(region, dict):
                        continue
                    expected = str(region.get("expected_relation") or "")
                    observed = str(region.get("observed_relation") or "")
                    if expected and observed and expected != observed:
                        issues.append(
                            f"slide {number} {name} expected {expected} but observed {observed}"
                        )
                    if region.get("solid_object_intersection") is True:
                        issues.append(
                            f"slide {number} {name} intersects or may intersect a solid object"
                        )
                    if region.get("morph_or_merge") is True:
                        issues.append(
                            f"slide {number} {name} morphs or merges into the environment"
                        )
                    evidence = str(region.get("evidence") or "").strip()
                    if evidence and (
                        region.get("boundary_continuous") is False
                        or region.get("occlusion_order_clear") is False
                    ):
                        issues.append(f"slide {number} {name}: {evidence}")
        for intersection in record.get("unresolved_intersections") or []:
            issues.append(f"slide {number} {intersection}")
    return issues


def validate_visual_richness_check(check: Any, *, slide_count: int) -> list[str]:
    issues: list[str] = []
    records = _records(check)
    if len(records) != slide_count:
        return [f"visual_richness has {len(records)} slide records, expected {slide_count}"]
    for record in records:
        number = int(record.get("slide", 0) or 0)
        if _pass(record):
            continue
        for key in ("foreground", "midground", "background", "focal_action", "cause_effect"):
            if not str(record.get(key) or "").strip():
                issues.append(f"slide {number} visual richness is missing {key}")
        if record.get("posed_portrait") is True or record.get("decorative_clutter") is True:
            issues.append(f"slide {number} visual richness failed scene-led composition")
    return issues


def validate_scene_entity_integrity_check(
    check: Any,
    *,
    slide_count: int,
    **_: Any,
) -> list[str]:
    issues: list[str] = []
    records = _records(check)
    if len(records) != slide_count:
        return [f"scene_entity_integrity has {len(records)} slide records, expected {slide_count}"]
    for record in records:
        number = int(record.get("slide", 0) or 0)
        if _pass(record):
            continue
        if record.get("expected_people") != record.get("observed_people"):
            issues.append(
                f"slide {number} expected {record.get('expected_people')} people but observed {record.get('observed_people')}"
            )
        for key in ("unexpected_entities", "unexpected_limbs", "duplicated_limbs"):
            if record.get(key):
                issues.append(
                    f"slide {number} reports {key}: "
                    + "; ".join(str(value) for value in record.get(key) or [])
                )
    return issues


def validate_source_assets(
    check: Any,
    *,
    package_dir: Path | None = None,
    **_: Any,
) -> list[str]:
    issues: list[str] = []
    records = _records(check)
    for record in records:
        asset = record.get("source_asset")
        if not isinstance(asset, dict):
            continue
        raw_path = asset.get("path")
        if package_dir is None or not raw_path:
            issues.append("source_asset needs a package-relative path")
            continue
        path = package_dir / str(raw_path)
        if not path.is_file():
            issues.append(f"source_asset is missing: {raw_path}")
            continue
        expected_hash = asset.get("sha256")
        actual_hashes = {_sha(path), _sha(path).removeprefix("sha256:")}
        if expected_hash not in actual_hashes:
            issues.append(f"source_asset hash is stale: {raw_path}")
    return issues


def validate_independent_reviewers(reviews: Any) -> list[str]:
    # Independent agents are optional. When reviewers are supplied, identities
    # must still be distinct so the evidence is honest.
    if not isinstance(reviews, dict) or not reviews:
        return []
    names = [
        str(value.get("reviewer_id") or value.get("reviewer") or "").strip()
        for value in reviews.values()
        if isinstance(value, dict)
    ]
    names = [name for name in names if name]
    return [] if len(names) == len(set(names)) else ["pixel QA reviewers are not independent"]


def required_artifacts() -> dict[str, str]:
    return dict(QUALITY_ARTIFACTS)


def _qa_map(payload: Any) -> dict[int, dict[str, Any]]:
    return {
        int(record.get("slide", 0) or 0): record
        for record in _records(payload)
        if int(record.get("slide", 0) or 0) > 0
    }


def _pixel_slide_issues(record: dict[str, Any] | None, *, copy: str, slide: int) -> list[str]:
    if not isinstance(record, dict):
        return [f"slide {slide} is missing actual-pixel QA"]
    checks = record.get("checks") if isinstance(record.get("checks"), dict) else record
    for key in (
        "semantic_action",
        "relationship_state",
        "anatomy_spatial",
        "identity",
        "exact_text",
        "brandmark",
        "style",
    ):
        check = checks.get(key)
        if not _pass(check):
            return [f"slide {slide} actual-pixel check failed: {key}"]
        evidence = str(check.get("evidence") or check.get("observed") or "").strip()
        if len(evidence) < 8:
            return [f"slide {slide} actual-pixel check lacks evidence: {key}"]
    exact = checks["exact_text"]
    if exact.get("expected") != copy:
        return [f"slide {slide} exact-text expectation is stale"]
    if exact.get("observed") != copy:
        return [f"slide {slide} rendered copy is not exact"]
    brandmark = checks["brandmark"]
    placement_evidence = " ".join(
        str(brandmark.get(key) or "")
        for key in ("position", "placement", "evidence", "observed")
    ).lower()
    if BRANDMARK_PLACEMENT not in placement_evidence:
        return [f"slide {slide} brandmark is not verified at {BRANDMARK_PLACEMENT}"]
    return []


def structured_visual_qa_gate(context: QualityContext) -> dict[str, Any]:
    path = context.visual_qa_path or context.out_dir / "visual-qa.json"
    issues: list[str] = []
    if not path.is_file():
        issues.append("visual-qa.json is missing")
    else:
        payload = _read_json(path)
        if not isinstance(payload, dict) or str(payload.get("status") or "").upper() != "PASS":
            issues.append("visual-qa.json status must be PASS")
        slides = context.package.get("slides") or []
        qa_map = _qa_map(payload)
        for slide in slides:
            issues.extend(
                _pixel_slide_issues(
                    qa_map.get(int(slide["slide"])),
                    copy=str(slide["copy"]),
                    slide=int(slide["slide"]),
                )
            )
    return {
        "stage": "actual_pixel_visual_qa",
        "status": "FAIL" if issues else "PASS",
        "pass": not issues,
        "issues": issues,
    }


def final_image_gate(context: QualityContext, final_files: list[Path] | None = None) -> dict[str, Any]:
    del final_files
    audit = build_final_audit(context.out_dir, write=False)
    return {
        "stage": "final_images",
        "status": "PASS" if audit["pass"] else "FAIL",
        "pass": audit["pass"],
        "issues": audit["issues"],
    }


def _reference_binding_issues(package_dir: Path, final: dict[str, Any]) -> list[str]:
    bindings = final.get("reference_bindings")
    if not isinstance(bindings, list) or not bindings:
        return ["final-images.json reference bindings are missing"]
    issues: list[str] = []
    saw_identity = False
    root = package_dir.resolve()
    for binding in bindings:
        if not isinstance(binding, dict):
            issues.append("final reference binding is malformed")
            continue
        raw_path = binding.get("path")
        roles = binding.get("roles")
        if not isinstance(raw_path, str) or not raw_path:
            issues.append("final reference binding path is missing")
            continue
        relative = Path(raw_path)
        if relative.is_absolute() or ".." in relative.parts:
            issues.append(f"final reference binding escapes the package: {raw_path}")
            continue
        path = package_dir / relative
        try:
            path.resolve().relative_to(root)
        except (OSError, ValueError):
            issues.append(f"final reference binding escapes the package: {raw_path}")
            continue
        if not path.is_file():
            issues.append(f"final reference file is missing: {raw_path}")
            continue
        if binding.get("sha256") != _sha(path):
            issues.append(f"final reference hash is stale: {raw_path}")
        if not isinstance(roles, list) or not roles:
            issues.append(f"final reference roles are missing: {raw_path}")
        elif "identity" in roles:
            saw_identity = True
    if not saw_identity:
        issues.append("final reference bindings contain no identity reference")
    return issues


def build_final_audit(
    package_or_context: Path | QualityContext,
    *_: Any,
    write: bool = False,
    **__: Any,
) -> dict[str, Any]:
    package_dir = (
        package_or_context.out_dir
        if isinstance(package_or_context, QualityContext)
        else Path(package_or_context)
    )
    issues: list[str] = []
    for required in ("creative-context.json", "format-contract.json", "slides.json", "prompt-pack.json", "final-images.json", "visual-qa.json"):
        if not (package_dir / required).is_file():
            issues.append(f"missing {required}")
    if issues:
        audit = {"schema_version": "carousel-final-audit/v2", "status": "FAIL", "pass": False, "issues": issues}
        if write:
            _write_json(package_dir / "final-audit.json", audit)
        return audit

    slides = _read_json(package_dir / "slides.json")
    final = _read_json(package_dir / "final-images.json")
    visual_qa = _read_json(package_dir / "visual-qa.json")
    if not isinstance(slides, list) or not slides:
        issues.append("slides.json is empty or malformed")
        slides = []
    if not isinstance(final, dict) or final.get("status") != "PUBLISH_READY":
        issues.append("final-images.json status must be PUBLISH_READY")
        final = {}
    issues.extend(_reference_binding_issues(package_dir, final))
    formats = list(locked_formats(package_dir))
    if final.get("requested_formats") != formats:
        issues.append("final-images.json formats do not match format-contract.json")
    if final.get("format_contract_sha256") != locked_format_contract_fingerprint(package_dir):
        issues.append("final-images.json format contract hash is stale")
    records = _records(final)
    if len(records) != len(slides):
        issues.append("final-images.json must contain the complete deck")
    final_by_number = {int(item.get("slide", 0) or 0): item for item in records}
    qa_map = _qa_map(visual_qa)
    asset_bindings: list[dict[str, Any]] = []
    for slide in slides:
        number = int(slide["slide"])
        record = final_by_number.get(number)
        if not isinstance(record, dict):
            issues.append(f"slide {number} final record is missing")
            continue
        if record.get("copy") != slide.get("copy"):
            issues.append(f"slide {number} final copy binding is stale")
        outputs = record.get("native_outputs")
        if not isinstance(outputs, dict) or set(outputs) != set(formats):
            issues.append(f"slide {number} final format set is wrong")
            continue
        for output_format in formats:
            binding = outputs[output_format]
            path = expected_output_path(package_dir, output_format, number)
            if not path.is_file():
                issues.append(f"slide {number} {output_format} final PNG is missing")
                continue
            try:
                width, height = _png_dimensions(path)
            except ValueError:
                issues.append(f"slide {number} {output_format} is not a PNG")
                continue
            expected_width, expected_height = format_spec(output_format)["target_size"]
            if (width, height) != (expected_width, expected_height):
                issues.append(f"slide {number} {output_format} dimensions are not native")
            if binding.get("path") != path.relative_to(package_dir).as_posix():
                issues.append(f"slide {number} {output_format} final path is stale")
            if binding.get("sha256") != _sha(path):
                issues.append(f"slide {number} {output_format} final hash is stale")
            if binding.get("width") != width or binding.get("height") != height:
                issues.append(f"slide {number} {output_format} final dimensions are stale")
            asset_bindings.append(
                {"slide": number, "format": output_format, "path": binding.get("path"), "sha256": binding.get("sha256")}
            )
        issues.extend(
            _pixel_slide_issues(
                qa_map.get(number),
                copy=str(slide.get("copy") or ""),
                slide=number,
            )
        )

    # A folder from an unrequested format must never become a hidden derivative.
    for output_format in SUPPORTED_NATIVE_FORMATS:
        if output_format in formats:
            continue
        folder = package_dir / str(format_spec(output_format)["folder"])
        if folder.is_dir() and any(folder.glob("*.png")):
            issues.append(f"unrequested format contains PNGs: {output_format}")

    audit = {
        "schema_version": "carousel-final-audit/v2",
        "status": "PASS" if not issues else "FAIL",
        "pass": not issues,
        "issues": issues,
        "slide_count": len(slides),
        "requested_formats": formats,
        "asset_bindings": asset_bindings,
    }
    if write:
        _write_json(package_dir / "final-audit.json", audit)
    return audit


def write_final_audit(package_dir: Path) -> dict[str, Any]:
    return build_final_audit(Path(package_dir), write=True)


def write_quality_artifacts(context: QualityContext) -> dict[str, Any]:
    """Compatibility entrypoint; never invents a final audit before final pixels."""
    if not (context.out_dir / "final-images.json").is_file():
        return {
            "schema_version": "carousel-final-audit/v2",
            "status": "NOT_READY",
            "pass": False,
            "issues": ["complete final deck does not exist"],
        }
    return write_final_audit(context.out_dir)


def build_run_ledger(context: QualityContext) -> dict[str, Any]:
    return {"status": "REMOVED", "reason": "generation-state.json is the sole transient state"}


def build_stage_reviews(context: QualityContext, ledger: dict[str, Any] | None = None) -> dict[str, Any]:
    del ledger
    return {"status": "REMOVED", "reason": "actual-pixel QA replaces review ceremony"}


def build_visual_qa(context: QualityContext) -> str:
    gate = structured_visual_qa_gate(context)
    return f"Actual-pixel QA: {gate['status']}"


def build_wiki_update(context: QualityContext, audit: dict[str, Any]) -> str:
    return (
        f"# {context.title}\n\nFinal audit: {audit.get('status', 'NOT_READY')}\n"
        f"Package: {context.out_dir}\n"
    )


def review_item(
    stage: str,
    expected: list[str],
    done: list[str],
    issues: list[str],
    notes: list[str] | None = None,
) -> dict[str, Any]:
    return {
        "stage": stage,
        "expected": expected,
        "done": done,
        "issues": issues,
        "notes": notes or [],
        "status": "FAIL" if issues else "PASS",
        "pass": not issues,
    }
