"""Actual-pixel QA and final audit for carousel packages.

The default path has no run ledger, agent report, approval ledger, Event A
provenance graph, or markdown checklist. Pre-generation prose can improve a
prompt, but only exact generated pixels can pass this module.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    SUPPORTED_NATIVE_FORMATS,
    format_spec,
    locked_formats,
)
from pipeline.stages.carousel_generation_inputs import canonical_fingerprint


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")


def _sha(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def visual_qa_fingerprint(visual_qa: Any) -> str:
    """Bind QA JSON semantics independently of whitespace and key ordering."""

    return canonical_fingerprint(visual_qa)


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


def build_final_audit(
    package_dir: Path,
    *_: Any,
    write: bool = False,
    **__: Any,
) -> dict[str, Any]:
    package_dir = Path(package_dir)
    issues: list[str] = []
    for required in (
        "creative-context.json",
        "format-contract.json",
        "slides.json",
        "prompt-pack.json",
        "final-images.json",
        "visual-qa.json",
    ):
        if not (package_dir / required).is_file():
            issues.append(f"missing {required}")
    if issues:
        audit = {
            "schema_version": "carousel-final-audit/v3",
            "status": "FAIL",
            "issues": issues,
            "manifest_sha256": "",
            "visual_qa_sha256": "",
        }
        if write:
            _write_json(package_dir / "final-audit.json", audit)
        return audit

    try:
        final = _read_json(package_dir / "final-images.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        final = {}
        issues.append(f"final-images.json is invalid: {exc}")
    try:
        visual_qa = _read_json(package_dir / "visual-qa.json")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        visual_qa = {}
        issues.append(f"visual-qa.json is invalid: {exc}")
    if not isinstance(final, dict):
        final = {}
        issues.append("final-images.json must contain an inventory object")
    if not isinstance(visual_qa, dict):
        visual_qa = {}
        issues.append("visual-qa.json must contain an object")

    if final.get("schema_version") == "carousel-final-images/v3":
        from pipeline.stages.carousel_generation_inputs import build_generation_inputs
        from pipeline.stages.carousel_pixel_qa import (
            manifest_fingerprint,
            validate_final_qa,
        )

        issues.extend(validate_final_qa(package_dir, visual_qa, final))
        try:
            current_inputs = build_generation_inputs(package_dir)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            issues.append(str(exc))
            current_inputs = {"slides": {}}
        final_records = {
            str(int(item.get("slide", 0) or 0)): item
            for item in _records(final)
            if int(item.get("slide", 0) or 0) > 0
        }
        for number, fingerprints in current_inputs.get("slides", {}).items():
            if final_records.get(number, {}).get("input_sha256") != fingerprints.get(
                "input_sha256"
            ):
                issues.append(f"slide {number} final input fingerprint is stale")
        manifest_sha256 = manifest_fingerprint(final)
    else:
        # Archived v2 evidence remains readable, but new audits never certify
        # it as v3 publish evidence or mutate the package.
        issues.append("archived v2 final inventory is read-only")
        manifest_sha256 = _sha(package_dir / "final-images.json")

    # A folder from an unrequested format must never become a hidden derivative.
    requested_formats = set(locked_formats(package_dir))
    for output_format in SUPPORTED_NATIVE_FORMATS:
        if output_format in requested_formats:
            continue
        folder = package_dir / str(format_spec(output_format)["folder"])
        if folder.is_dir() and any(folder.glob("*.png")):
            issues.append(f"unrequested format contains PNGs: {output_format}")

    visual_qa_sha256 = visual_qa_fingerprint(visual_qa)
    stored_audit_path = package_dir / "final-audit.json"
    if stored_audit_path.is_file():
        try:
            stored_audit = _read_json(stored_audit_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            stored_audit = {}
            issues.append(f"final-audit.json is invalid: {exc}")
        if not isinstance(stored_audit, dict):
            issues.append("final-audit.json must contain an object")
            stored_audit = {}
        if stored_audit.get("schema_version") != "carousel-final-audit/v3":
            issues.append("stored final audit schema is missing or stale")
        if str(stored_audit.get("status") or "").upper() != "PASS":
            issues.append("stored final audit status must be PASS")
        if stored_audit.get("issues") != []:
            issues.append("stored final audit issues must be empty")
        if stored_audit.get("manifest_sha256") != manifest_sha256:
            issues.append("stored final audit manifest_sha256 is missing or stale")
        if stored_audit.get("visual_qa_sha256") != visual_qa_sha256:
            issues.append("stored final audit visual_qa_sha256 is missing or stale")

    audit = {
        "schema_version": "carousel-final-audit/v3",
        "status": "PASS" if not issues else "FAIL",
        "issues": issues,
        "manifest_sha256": manifest_sha256,
        "visual_qa_sha256": visual_qa_sha256,
    }
    if write:
        _write_json(package_dir / "final-audit.json", audit)
    return audit


__all__ = [
    "build_final_audit",
    "validate_anatomy_inventory_check",
    "validate_scene_entity_integrity_check",
    "validate_spatial_topology_check",
    "visual_qa_fingerprint",
]
