#!/usr/bin/env python3
"""Run scene preflight or validate Codex-authored pixel observations."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

from PIL import Image, UnidentifiedImageError


WORKSPACE_ROOT = Path(__file__).resolve().parents[4]
if str(WORKSPACE_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_ROOT))

from pipeline.agentic.workflow_doctor import inspect_carousel_package  # noqa: E402
from pipeline.stages.carousel_format_contract import (  # noqa: E402
    FORMAT_CONTRACT_FILENAME,
    format_spec,
    locked_formats,
)
from pipeline.stages.carousel_pixel_qa import (  # noqa: E402
    PIXEL_QA_SCHEMA_VERSION,
    validate_final_qa,
    validate_proof_qa,
)
from pipeline.stages.carousel_visual_storytelling import (  # noqa: E402
    first_failed_pixel_gate,
)


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        raise ValueError(f"Missing required artifact: {path}") from None
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def _records(payload: Any) -> list[dict[str, Any]]:
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if isinstance(payload, dict) and isinstance(payload.get("slides"), list):
        return [item for item in payload["slides"] if isinstance(item, dict)]
    return []


def _slide_number(record: dict[str, Any], fallback: int) -> int:
    try:
        return int(record.get("slide") or record.get("slide_number") or fallback)
    except (TypeError, ValueError):
        return fallback


def _text(record: dict[str, Any]) -> str:
    for key in ("text", "copy", "on_image_text", "slide_text"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _action(record: dict[str, Any]) -> str:
    for key in ("physical_action", "visual_sentence", "observable_action", "visual", "scene"):
        value = record.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _resolve_package_file(package: Path, raw_path: Any) -> Path | None:
    if not raw_path:
        return None
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = package / path
    try:
        relative = path.relative_to(package)
        current = package
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return None
        resolved = path.resolve(strict=True)
        resolved.relative_to(package.resolve(strict=True))
    except (FileNotFoundError, OSError, ValueError):
        return None
    return resolved if resolved.is_file() and not path.is_symlink() else None


def _is_v3_package(package: Path) -> bool:
    try:
        state = _read_json(package / "generation-state.json")
    except ValueError:
        return False
    return isinstance(state, dict) and state.get("schema_version") == "carousel-generation-state/v3"


def _preflight(package: Path) -> list[str]:
    slides = _records(_read_json(package / "slides.json"))
    prompt_pack = _read_json(package / "prompt-pack.json")
    prompts = _records(prompt_pack)
    if not slides:
        return ["slides.json has no slide records."]
    issues: list[str] = []

    if not (package / FORMAT_CONTRACT_FILENAME).is_file():
        issues.append("format-contract.json is missing.")
    else:
        try:
            locked_formats(package)
        except (ValueError, OSError, json.JSONDecodeError) as exc:
            issues.append(f"format-contract.json is invalid: {exc}")

    strict_v3 = _is_v3_package(package)
    refs = prompt_pack.get("identity_reference_images") if isinstance(prompt_pack, dict) else None
    if not isinstance(refs, list) or not refs:
        issues.append("prompt-pack.json has no attached Aachu/Zuv identity references.")
    else:
        for raw_path in refs:
            path = Path(str(raw_path)).expanduser()
            if not path.is_absolute():
                path = package / path
            if not path.is_file():
                issues.append(f"identity reference is missing: {path}")
        if strict_v3:
            roles = {
                role
                for raw_path in refs
                for role in ("aachu", "zuv", "together")
                if role in {part.lower() for part in Path(str(raw_path)).parts}
            }
            try:
                creative_context = _read_json(package / "creative-context.json")
            except ValueError:
                creative_context = {}
            selection = (
                creative_context.get("identity_reference_selection")
                if isinstance(creative_context, dict)
                else None
            )
            selected_records = (
                selection.get("selected_references")
                if isinstance(selection, dict)
                else None
            )
            if isinstance(selected_records, list):
                for record in selected_records:
                    if not isinstance(record, dict):
                        continue
                    path = str(record.get("path") or "")
                    role_text = str(record.get("role") or "").lower()
                    if path not in {str(value) for value in refs}:
                        continue
                    roles.update(
                        role for role in ("aachu", "zuv", "together") if role in role_text
                    )
            missing_roles = sorted({"aachu", "zuv", "together"} - roles)
            if missing_roles:
                issues.append(
                    "identity references must name Aachu, Zuv, and together roles; missing: "
                    + ", ".join(missing_roles)
                )
            for raw_path in refs:
                if _resolve_package_file(package, raw_path) is None:
                    issues.append(
                        f"identity reference must be a package-local non-symlinked file: {raw_path}"
                    )

    if strict_v3:
        style_refs = (
            prompt_pack.get("style_reference_images")
            if isinstance(prompt_pack, dict)
            else None
        )
        if not isinstance(style_refs, list) or not style_refs:
            issues.append("prompt-pack.json has no attached style references.")
        else:
            for raw_path in style_refs:
                if _resolve_package_file(package, raw_path) is None:
                    issues.append(
                        f"style reference must be a package-local non-symlinked file: {raw_path}"
                    )

    prompt_by_slide = {
        _slide_number(record, index): record
        for index, record in enumerate(prompts, start=1)
    }
    for index, slide in enumerate(slides, start=1):
        number = _slide_number(slide, index)
        exact_text = _text(slide)
        action = _action(slide)
        if not exact_text:
            issues.append(f"slide {number}: exact on-image text is missing")
        if len(action.split()) < 6:
            issues.append(
                f"slide {number}: needs one concrete physical action sentence with subject, action, target, and visible result"
            )
        prompt = prompt_by_slide.get(number)
        if prompt is None:
            issues.append(f"slide {number}: prompt-pack record is missing")
        elif exact_text and exact_text not in json.dumps(prompt, ensure_ascii=False):
            issues.append(f"slide {number}: prompt-pack does not preserve the exact slide text")
    return issues


def _active_qa_path(package: Path) -> Path:
    final_path = package / "visual-qa.json"
    if final_path.is_file():
        return final_path
    return package / "proof-qa.json"


def _strict_final_manifest(package: Path) -> tuple[dict[str, Any], Path]:
    candidates = (
        (package / "final-images.json", package),
        (
            package / ".internal" / "final-manifest-candidate.json",
            package / ".internal" / "final-audit-candidate",
        ),
    )
    for path, asset_root in candidates:
        if path.is_file():
            payload = _read_json(path)
            if isinstance(payload, dict):
                return payload, asset_root
            raise ValueError(f"{path} must contain an object.")
    raise ValueError("Missing current final manifest candidate for visual-qa.json.")


def _strict_postcheck(package: Path, qa_path: Path, qa: dict[str, Any]) -> list[str]:
    scope = qa.get("scope")
    if scope == "proof":
        issues = validate_proof_qa(package, qa)
    elif scope == "final":
        manifest, asset_root = _strict_final_manifest(package)
        issues = validate_final_qa(asset_root, qa, manifest)
    else:
        issues = ["pixel QA scope must be proof or final"]
    if issues:
        return issues

    report = inspect_carousel_package(package)
    issues.extend(
        f"doctor:{issue.code}: {issue.message}"
        for issue in report.issues
        if issue.severity == "blocker"
    )
    return list(dict.fromkeys(issues))


def _legacy_postcheck(package: Path, qa_path: Path, qa: dict[str, Any]) -> list[str]:
    """Keep archived v2 packages auditable without allowing legacy new writes."""

    qa = _read_json(qa_path)
    if not isinstance(qa, dict):
        return [f"{qa_path.name} must contain an object."]

    failed_gate = first_failed_pixel_gate(qa)
    if failed_gate is not None:
        return [failed_gate[1]]

    issues: list[str] = []
    status = str(qa.get("status") or qa.get("verdict") or "").strip().upper()
    if status != "PASS" or qa.get("pass") is False:
        issues.append(f"{qa_path.name} must record PASS and cannot set pass false.")

    try:
        requested_formats = set(locked_formats(package))
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        return [f"format-contract.json is invalid: {exc}"]
    seen: set[tuple[int, str]] = set()
    for index, record in enumerate(_records(qa), start=1):
        slide = _slide_number(record, index)
        outputs = record.get("native_outputs")
        if not isinstance(outputs, dict):
            issues.append(f"slide {slide}: native_outputs pixel bindings are missing")
            continue
        for output_format, binding in outputs.items():
            if not isinstance(binding, dict):
                issues.append(f"slide {slide} {output_format}: pixel binding must be an object")
                continue
            seen.add((slide, str(output_format)))
            path = _resolve_package_file(package, binding.get("path") or binding.get("relative_path"))
            if path is None:
                issues.append(f"slide {slide} {output_format}: reviewed package image is missing")
                continue
            recorded_hash = str(binding.get("sha256") or "").lower().removeprefix("sha256:")
            actual_hash = hashlib.sha256(path.read_bytes()).hexdigest()
            if not recorded_hash or recorded_hash != actual_hash:
                issues.append(f"slide {slide} {output_format}: reviewed SHA-256 is missing or stale")
            try:
                with Image.open(path) as image:
                    dimensions = tuple(image.size)
                    image.verify()
            except (UnidentifiedImageError, OSError, SyntaxError, ValueError):
                issues.append(f"slide {slide} {output_format}: reviewed file is not a decodable image")
                continue
            if output_format in requested_formats:
                expected = tuple(format_spec(str(output_format))["target_size"])
                if dimensions != expected:
                    issues.append(
                        f"slide {slide} {output_format}: dimensions are {dimensions[0]}x{dimensions[1]}, expected {expected[0]}x{expected[1]}"
                    )

    slide_count = len(_records(_read_json(package / "slides.json")))
    expected = {
        (slide, output_format)
        for slide in range(1, slide_count + 1)
        for output_format in requested_formats
    }
    if seen != expected:
        missing = sorted(expected - seen)
        if missing:
            issues.append("missing reviewed slide/format bindings: " + ", ".join(f"{slide}:{fmt}" for slide, fmt in missing))

    report = inspect_carousel_package(package)
    issues.extend(
        f"doctor:{issue.code}: {issue.message}"
        for issue in report.issues
        if issue.severity == "blocker"
    )
    return list(dict.fromkeys(issues))


def _postcheck(package: Path) -> list[str]:
    qa_path = _active_qa_path(package)
    qa = _read_json(qa_path)
    if not isinstance(qa, dict):
        return [f"{qa_path.name} must contain an object."]
    if qa.get("schema_version") == PIXEL_QA_SCHEMA_VERSION:
        return _strict_postcheck(package, qa_path, qa)
    return _legacy_postcheck(package, qa_path, qa)


def check_package(carousel_dir: Path, phase: str) -> dict[str, Any]:
    result: dict[str, Any] = {
        "carousel_dir": str(carousel_dir),
        "phase": phase,
        "checks": {},
    }
    failures: list[str] = []
    if phase in {"pre", "all"}:
        pre_issues = _preflight(carousel_dir)
        result["checks"]["copy_format_action_preflight"] = {
            "pass": not pre_issues,
            "issues": pre_issues,
        }
        failures.extend(f"pre: {issue}" for issue in pre_issues)
    if phase in {"post", "all"}:
        post_issues = _postcheck(carousel_dir)
        result["checks"]["bound_pixel_observation_qa"] = {
            "pass": not post_issues,
            "issues": post_issues,
        }
        failures.extend(f"post: {issue}" for issue in post_issues)
    result["pass"] = not failures
    result["issues"] = failures
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate carousel scene preflight or Codex-authored observations "
            "bound to current image bytes."
        )
    )
    parser.add_argument("--carousel-dir", required=True, type=Path)
    parser.add_argument("--phase", choices=("pre", "post", "all"), default="all")
    parser.add_argument("--compact", action="store_true")
    return parser


def main() -> int:
    args = build_parser().parse_args()
    carousel_dir = args.carousel_dir.expanduser().resolve()
    try:
        result = check_package(carousel_dir, args.phase)
    except ValueError as exc:
        result = {
            "carousel_dir": str(carousel_dir),
            "phase": args.phase,
            "pass": False,
            "issues": [str(exc)],
        }
    print(json.dumps(result, ensure_ascii=False, indent=None if args.compact else 2, separators=(",", ":") if args.compact else None))
    return 0 if result.get("pass") else 1


if __name__ == "__main__":
    raise SystemExit(main())
