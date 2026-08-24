"""Fail-closed image handoff for the small carousel hot path.

There is one transient state file, one quarantine, and one pixel-QA contract.
Planning prose never certifies pixels. A proof is generated first, QA is bound
to its exact bytes, and the remaining deck is allowed only after explicit
creator approval. Failed slides are retried individually, at most twice.
``final-images.json`` and ``final-audit.json`` do not exist until the complete
deck has passed.
"""

from __future__ import annotations

import hashlib
import json
import re
import shutil
from collections.abc import Callable
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    FORMAT_CONTRACT_FILENAME,
    SUPPORTED_NATIVE_FORMATS,
    expected_output_path,
    format_spec,
    locked_format_contract_fingerprint,
    locked_formats,
    normalize_requested_formats,
    write_format_contract,
)
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt, extract_scene_summary
from pipeline.stages.carousel_visual_storytelling import physical_action_issue
from pipeline.stages.model_native_image_generation import existing_reference_paths


BACKEND = "codex_builtin"
GENERATION_MODE = "model_native_publishable"
MAX_SEMANTIC_ATTEMPTS = 2
MAX_VISUAL_QA_RETRIES = MAX_SEMANTIC_ATTEMPTS - 1  # compatibility name
STATE_FILE = "generation-state.json"
QUARANTINE_FOLDER = ".internal/visual-quarantine"
APPROVED_CANDIDATE_FOLDER = ".internal/approved-final-candidates"
PROMOTION_STAGING_FOLDER = ".internal/promotion-staging"
FINAL_AUDIT_CANDIDATE_FOLDER = ".internal/final-audit-candidate"
PROMPT_HANDOFF_ACTIVE_FOLDER = ".internal/compiled-prompts"
PROMPT_HANDOFF_STAGING_FOLDER = ".internal/compiled-prompts-staging"
ATTEMPT_LEDGER = STATE_FILE  # compatibility: attempts live in transient state
FULL_DECK_ATTEMPT_LEDGER = STATE_FILE
VISUAL_QA_REVIEW_KEYS: tuple[str, ...] = ()

PASS = "PASS"
PIXEL_CHECKS = (
    "semantic_action",
    "relationship_state",
    "anatomy_spatial",
    "identity",
    "exact_text",
    "brandmark",
    "style",
)


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path.name} must contain a JSON object.")
    return payload


def sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def sha256_binding(payload: bytes) -> str:
    return "sha256:" + sha256_bytes(payload)


def _canonical_hash(value: Any) -> str:
    return sha256_binding(
        json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode(
            "utf-8"
        )
    )


def remove_path_without_following(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def package_relative_path(carousel_dir: Path, path: Path) -> str:
    resolved_root = carousel_dir.resolve()
    resolved = path.resolve()
    if resolved != resolved_root and resolved_root not in resolved.parents:
        raise ValueError("Package artifact escaped the carousel directory.")
    return resolved.relative_to(resolved_root).as_posix()


def resolve_package_artifact_path(
    carousel_dir: Path,
    raw_path: str | Path | None,
    default: str,
) -> Path:
    candidate = Path(raw_path or default)
    if not candidate.is_absolute():
        candidate = carousel_dir / candidate
    package_relative_path(carousel_dir, candidate)
    return candidate


def _state_path(carousel_dir: Path) -> Path:
    return carousel_dir / STATE_FILE


def _load_state(carousel_dir: Path) -> dict[str, Any]:
    path = _state_path(carousel_dir)
    if path.is_file():
        return load_json(path)
    slides = _slides(carousel_dir)
    return {
        "schema_version": "carousel-generation-state/v2",
        "status": "draft",
        "stage": "proof",
        "slide_count": len(slides),
        "selected_slides": [],
        "requested_formats": list(locked_formats(carousel_dir)),
        "attempts_by_slide": {str(slide["slide"]): 0 for slide in slides},
        "approved_final_candidates": {},
        "qa_records": {},
        "next_action": "prepare_riskiest_proof",
    }


def _write_state(carousel_dir: Path, state: dict[str, Any]) -> dict[str, Any]:
    state = {
        "schema_version": "carousel-generation-state/v2",
        **state,
    }
    write_json(_state_path(carousel_dir), state)
    return state


def _slides(carousel_dir: Path) -> list[dict[str, Any]]:
    payload = json.loads((carousel_dir / "slides.json").read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("slides.json must contain at least one slide.")
    numbers = [int(item.get("slide", 0) or 0) for item in payload if isinstance(item, dict)]
    if numbers != list(range(1, len(payload) + 1)):
        raise ValueError("slides.json slide numbers must be unique and sequential from 1.")
    return payload


def _prompt_slides(carousel_dir: Path) -> list[dict[str, Any]]:
    prompts = load_json(carousel_dir / "prompt-pack.json").get("slides")
    if not isinstance(prompts, list) or not prompts:
        raise ValueError("prompt-pack.json must contain slide prompts.")
    return prompts


def _identity_paths(
    prompt_pack: dict[str, Any],
    *,
    package_dir: Path | None = None,
) -> list[Path]:
    values = [
        *(prompt_pack.get("identity_reference_images") or []),
        *(prompt_pack.get("identity_dossier_reference_images") or []),
    ]
    paths: list[Path] = []
    for value in values:
        path = Path(str(value)).expanduser()
        if not path.is_absolute() and package_dir is not None:
            path = package_dir / path
        if path.is_file():
            paths.append(path.resolve())
    return paths


def _reference_bindings(
    carousel_dir: Path,
    paths: list[Path],
) -> list[dict[str, str]]:
    return [
        {
            "path": package_relative_path(carousel_dir, path),
            "sha256": sha256_binding(path.read_bytes()),
        }
        for path in paths
    ]


def _package_reference_bindings(
    carousel_dir: Path,
    *,
    prompt_pack: dict[str, Any] | None = None,
    slides: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    prompt_pack = prompt_pack or load_json(carousel_dir / "prompt-pack.json")
    slides = slides or _slides(carousel_dir)
    raw_bindings: list[tuple[str, str]] = []
    for key, role in (
        ("identity_dossier_reference_images", "identity"),
        ("identity_reference_images", "identity"),
        ("style_reference_images", "style"),
    ):
        raw_bindings.extend((str(value), role) for value in prompt_pack.get(key, []))
    for slide in slides:
        raw_bindings.extend(
            (str(value), "story") for value in slide.get("source_images", [])
        )

    by_path: dict[str, dict[str, Any]] = {}
    for raw_path, role in raw_bindings:
        path = resolve_package_artifact_path(carousel_dir, raw_path, "")
        if not path.is_file():
            raise FileNotFoundError(f"Missing package-local {role} reference: {raw_path}")
        relative = package_relative_path(carousel_dir, path)
        binding = by_path.setdefault(
            relative,
            {
                "path": relative,
                "sha256": sha256_binding(path.read_bytes()),
                "roles": [],
            },
        )
        if role not in binding["roles"]:
            binding["roles"].append(role)
    return [by_path[path] for path in sorted(by_path)]


def prompt_handoff_relative_path(output_format: str, slide_number: int, kind: str) -> str:
    suffix = ".prompt.txt" if kind == "generator" else ".md"
    folder = str(format_spec(output_format)["prompt_folder"])
    return f"{PROMPT_HANDOFF_ACTIVE_FOLDER}/{folder}/slide-{slide_number:02d}{suffix}"


def generator_prompt_text(slide_prompt: dict[str, Any], output_format: str) -> str:
    number = int(slide_prompt["slide"])
    return compile_image_prompt(
        slide_number=number,
        slide_count=int(slide_prompt.get("slide_count") or 1),
        slide_copy=str(slide_prompt["text"]),
        visual=str(slide_prompt.get("scene") or extract_scene_summary(slide_prompt.get("prompt", ""))),
        format_key=output_format,
        style=str(slide_prompt.get("style") or "warm ivory paper, watercolor and loose ink"),
        negative=str(slide_prompt.get("negative_prompt") or ""),
        pose=slide_prompt.get("pose"),
        wardrobe=slide_prompt.get("wardrobe"),
        props=slide_prompt.get("props"),
        background=slide_prompt.get("background"),
        emotion=slide_prompt.get("emotion"),
    )


def build_handoff_markdown(
    *,
    carousel_dir: Path | None = None,
    slide_prompt: dict[str, Any] | None = None,
    output_format: str | None = None,
    generator_prompt_path: Path | None = None,
    identity_paths: list[Path] | None = None,
    source_paths: list[Path] | None = None,
    style_paths: list[Path] | None = None,
    **legacy: Any,
) -> str:
    # Small compatibility surface for callers that still pass the old
    # descriptive fields. The markdown deliberately points at the one compiled
    # prompt instead of serializing a second prompt body.
    if slide_prompt is None:
        prompt_filename = str(legacy.get("prompt_filename") or "slide.prompt.txt")
        references = [str(value) for value in legacy.get("reference_paths", [])]
        lines = [
            f"# Slide {int(legacy.get('slide_number', 0) or 0):02d} — "
            f"{legacy.get('output_label', 'Native output')}",
            "",
            "## Prompt Source",
            "",
            f"Paste the full prompt from `{prompt_filename}`.",
            "This handoff intentionally does not duplicate the prompt body.",
            "",
            f"Exact text: {legacy.get('exact_slide_copy', '')}",
            f"Expected output: {legacy.get('expected_file', '')}",
            *[f"- Reference: {value}" for value in references],
        ]
        return "\n".join(lines) + "\n"
    assert carousel_dir is not None
    assert output_format is not None
    assert generator_prompt_path is not None
    identity_paths = identity_paths or []
    spec = format_spec(output_format)
    references = [*identity_paths, *(source_paths or []), *(style_paths or [])]
    lines = [
        f"# Slide {int(slide_prompt['slide']):02d} — {spec['label']}",
        "",
        f"Generator prompt: `{package_relative_path(carousel_dir, generator_prompt_path)}`",
        f"Required output: {spec['target_size'][0]}x{spec['target_size'][1]} PNG",
        f"Exact text: {slide_prompt['text']}",
        "",
        "Attach these references:",
        *[f"- {package_relative_path(carousel_dir, path)}" for path in references],
        "",
        "Do not generate another aspect ratio unless it is locked in format-contract.json.",
    ]
    return "\n".join(lines) + "\n"


prompt_file_text = build_handoff_markdown


def build_compiled_prompt_handoff(
    carousel_dir: Path,
    *,
    slide_numbers: list[int],
    output_formats: list[str] | tuple[str, ...],
    prompt_source_root: Path | None = None,
) -> dict[str, Any]:
    root = prompt_source_root or carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    files: list[dict[str, Any]] = []
    for number in slide_numbers:
        for output_format in output_formats:
            folder = str(format_spec(output_format)["prompt_folder"])
            for suffix, kind in ((".prompt.txt", "generator"), (".md", "handoff")):
                path = root / folder / f"slide-{number:02d}{suffix}"
                if not path.is_file():
                    raise ValueError(f"Missing compiled {kind} prompt: {path}")
                files.append(
                    {
                        "slide": number,
                        "format": output_format,
                        "kind": kind,
                        "sha256": sha256_binding(path.read_bytes()),
                    }
                )
    source_inputs = [
        {
            "path": filename,
            "sha256": sha256_binding((carousel_dir / filename).read_bytes()),
        }
        for filename in ("slides.json", "prompt-pack.json")
    ]
    reference_bindings = _package_reference_bindings(carousel_dir)
    fingerprint_payload = {
        "files": files,
        "source_inputs": source_inputs,
        "reference_bindings": reference_bindings,
        "format_contract_sha256": locked_format_contract_fingerprint(carousel_dir),
    }
    return {
        "schema_version": "compiled-prompts/v2",
        "slides": list(slide_numbers),
        "formats": list(output_formats),
        "files": files,
        **fingerprint_payload,
        "fingerprint": _canonical_hash(fingerprint_payload),
    }


def compiled_prompt_handoff_integrity_issues(
    carousel_dir: Path,
    *,
    state: dict[str, Any] | None = None,
    **_: Any,
) -> list[str]:
    state = state or _load_state(carousel_dir)
    handoff = state.get("compiled_prompt_handoff")
    if not isinstance(handoff, dict):
        return ["compiled prompt handoff is missing"]
    try:
        current = build_compiled_prompt_handoff(
            carousel_dir,
            slide_numbers=[int(value) for value in handoff.get("slides", [])],
            output_formats=[str(value) for value in handoff.get("formats", [])],
        )
    except (OSError, ValueError) as exc:
        return [str(exc)]
    return [] if current == handoff else ["compiled prompt handoff is stale"]


def approved_proof_batch_handoff_attestation_issues(*_: Any, **__: Any) -> list[str]:
    """Legacy ceremony removed; exact proof hashes live in generation-state.json."""
    return []


def retry_prompt_handoff_attestation_issues(*_: Any, **__: Any) -> list[str]:
    return []


def creator_override_batch_handoff_integrity_issues(*_: Any, **__: Any) -> list[str]:
    return ["accepting a QA-failed proof is no longer supported"]


def identity_consistency_gate_reason(carousel_dir: Path) -> str | None:
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    return None if _identity_paths(prompt_pack, package_dir=carousel_dir) else (
        "Image generation requires at least one attached Aachu/Zuv identity reference."
    )


def visual_plan_quality_gate_reason(carousel_dir: Path) -> str | None:
    for slide in _slides(carousel_dir):
        if not str(slide.get("copy") or "").strip():
            return f"Slide {slide.get('slide')} is missing exact copy."
        action = str(slide.get("physical_action") or slide.get("visual") or "").strip()
        action_issue = physical_action_issue(action, copy=slide.get("copy"))
        if slide.get("needs_physical_action") is True or action_issue:
            detail = action_issue or "needs a concrete physical action"
            return f"Slide {slide.get('slide')} {detail}."
    return None


def pre_generation_review_gate_reason(carousel_dir: Path) -> str | None:
    return visual_plan_quality_gate_reason(carousel_dir) or identity_consistency_gate_reason(
        carousel_dir
    )


def infer_slide_count(carousel_dir: Path) -> int:
    return len(_slides(carousel_dir))


def proof_slide_from_gate(proof_gate: str | None, slides: list[dict[str, Any]]) -> int:
    if proof_gate:
        match = re.search(r"\bslide\s*(\d+)\b", str(proof_gate), flags=re.IGNORECASE)
        if match and any(int(slide["slide"]) == int(match.group(1)) for slide in slides):
            return int(match.group(1))
    # The densest physical scene is a better risk proof than an arbitrary cover.
    return int(
        max(
            slides,
            key=lambda item: len(str(item.get("scene") or item.get("prompt") or "").split()),
        )["slide"]
    )


def prepare_codex_builtin_image_generation(
    carousel_dir: Path,
    *,
    proof_slide: int | None = None,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    carousel_dir = Path(carousel_dir).expanduser()
    prior_formats = (
        list(locked_formats(carousel_dir))
        if (carousel_dir / FORMAT_CONTRACT_FILENAME).is_file()
        else []
    )
    if formats is not None:
        requested_formats = list(normalize_requested_formats(formats))
        write_format_contract(
            carousel_dir,
            requested_formats,
            source="creator_request",
            replace=True,
        )
    elif not (carousel_dir / FORMAT_CONTRACT_FILENAME).is_file():
        write_format_contract(carousel_dir, None, source="instagram_post_default")
    output_formats = list(locked_formats(carousel_dir))
    state = _load_state(carousel_dir)
    format_changed = bool(prior_formats and prior_formats != output_formats)
    if format_changed:
        # An explicit creator format correction invalidates every proof and
        # final candidate made against the earlier canvas contract. Retired
        # generated outputs are removed so stale PUBLISH_READY evidence cannot
        # coexist with the new proof request.
        for output_format in SUPPORTED_NATIVE_FORMATS:
            remove_path_without_following(
                carousel_dir / str(format_spec(output_format)["folder"])
            )
        for filename in (
            "final-images.json",
            "final-audit.json",
            "visual-qa.json",
            "proof-qa.json",
        ):
            remove_path_without_following(carousel_dir / filename)
        for folder in (
            APPROVED_CANDIDATE_FOLDER,
            QUARANTINE_FOLDER,
            PROMPT_HANDOFF_ACTIVE_FOLDER,
        ):
            remove_path_without_following(carousel_dir / folder)
        for key in (
            "compiled_prompt_handoff",
            "creator_approval",
            "creator_approval_issues",
            "proof_format_contract_sha256",
            "proof_image_set_sha256",
            "proof_qa_sha256",
            "quarantine_candidates",
            "image_set_sha256",
            "qa_path",
            "repair_scope",
            "repair_slides",
            "remaining_slides",
            "visual_qa_issues",
            "final_images_sha256",
            "final_audit_sha256",
        ):
            state.pop(key, None)
        state.update(
            {
                "status": "draft",
                "stage": "proof",
                "proof_approved": False,
                "selected_slides": [],
                "requested_formats": output_formats,
                "attempts_by_slide": {},
                "approved_final_candidates": {},
                "qa_records": {},
                "next_action": "prepare_riskiest_proof",
                "reason": "The creator changed the locked output format; a new proof is required.",
            }
        )
        _write_state(carousel_dir, state)
    current_format_fingerprint = locked_format_contract_fingerprint(carousel_dir)
    if (
        state.get("proof_approved") is True
        and state.get("proof_format_contract_sha256") != current_format_fingerprint
    ):
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "blocked",
                "next_action": "regenerate_proof_for_format_change",
                "reason": "The locked format changed after proof approval.",
            },
        )
    slide_plans = _slides(carousel_dir)
    slide_plan_by_number = {int(item["slide"]): item for item in slide_plans}
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    prompt_slides = _prompt_slides(carousel_dir)
    prompt_by_number = {int(item["slide"]): item for item in prompt_slides}
    visual_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_reason:
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "blocked",
                "next_action": "define_physical_actions",
                "reason": visual_reason,
            },
        )
    identity_paths = _identity_paths(prompt_pack, package_dir=carousel_dir)
    if not identity_paths:
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "blocked",
                "next_action": "attach_identity_references",
                "reason": "Actual Aachu/Zuv identity reference images are required before generation.",
            },
        )

    attempts = {
        str(key): int(value)
        for key, value in (state.get("attempts_by_slide") or {}).items()
    }
    for slide in slide_plans:
        attempts.setdefault(str(slide["slide"]), 0)
    approved = dict(state.get("approved_final_candidates") or {})
    if proof_slide is not None:
        selected = [int(proof_slide)]
        stage = "proof"
    elif state.get("stage") == "repair" and state.get("repair_slides"):
        selected = [int(value) for value in state["repair_slides"]]
        stage = "repair"
    elif state.get("proof_approved") is True or state.get("status") == "BATCH_ALLOWED":
        selected = [
            int(slide["slide"])
            for slide in slide_plans
            if str(slide["slide"]) not in approved
        ]
        stage = "batch"
    else:
        selected = [proof_slide_from_gate(prompt_pack.get("proof_gate"), prompt_slides)]
        stage = "proof"
    valid_numbers = set(prompt_by_number)
    if not selected or any(number not in valid_numbers for number in selected):
        raise ValueError("Selected proof/batch slides are not present in prompt-pack.json.")
    exhausted = [number for number in selected if attempts.get(str(number), 0) >= MAX_SEMANTIC_ATTEMPTS]
    if exhausted:
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "blocked_visual_qa",
                "repair_slides": exhausted,
                "next_action": "revise_copy_or_visual_premise",
                "reason": "Maximum two semantic image attempts reached for: "
                + ", ".join(str(value) for value in exhausted),
            },
        )

    active = carousel_dir / PROMPT_HANDOFF_ACTIVE_FOLDER
    staging = carousel_dir / PROMPT_HANDOFF_STAGING_FOLDER
    remove_path_without_following(staging)
    staging.mkdir(parents=True)
    style = str(prompt_pack.get("style_prompt") or "warm ivory paper, watercolor and loose ink")
    negative = str(prompt_pack.get("negative_prompt") or "")
    style_paths = [
        path
        for path in existing_reference_paths(prompt_pack, base_dir=carousel_dir)
        if path not in identity_paths
    ]
    records: list[dict[str, Any]] = []
    try:
        for number in selected:
            source = prompt_by_number[number]
            source_paths = [
                resolve_package_artifact_path(carousel_dir, raw_path, "")
                for raw_path in slide_plan_by_number[number].get("source_images", [])
            ]
            source = {
                **source,
                "slide_count": len(slide_plans),
                "style": style,
                "negative_prompt": source.get("negative_prompt") or negative,
            }
            prompt_files: dict[str, str] = {}
            for output_format in output_formats:
                folder = str(format_spec(output_format)["prompt_folder"])
                generator_path = staging / folder / f"slide-{number:02d}.prompt.txt"
                handoff_path = staging / folder / f"slide-{number:02d}.md"
                generator_path.parent.mkdir(parents=True, exist_ok=True)
                prompt_text = generator_prompt_text(source, output_format)
                generator_path.write_text(prompt_text, encoding="utf-8")
                # Prompt QA belongs here, close to the generator handoff. The
                # retired global checker required seven slogan fragments from
                # the old framework and was the main source of prompt bloat.
                # Exact copy and a compact budget are the enforceable inputs;
                # anatomy, identity, action, and style are verified on pixels.
                exact_copy = str(source["text"])
                if exact_copy not in prompt_text:
                    raise ValueError(f"Slide {number} compiled prompt dropped exact copy.")
                if len(prompt_text) > 8_000 or len(prompt_text.split()) > 900:
                    raise ValueError(f"Slide {number} compiled prompt exceeds the compact budget.")
                active_generator = active / folder / generator_path.name
                handoff_path.write_text(
                    build_handoff_markdown(
                        carousel_dir=carousel_dir,
                        slide_prompt=source,
                        output_format=output_format,
                        generator_prompt_path=active_generator,
                        identity_paths=identity_paths,
                        source_paths=source_paths,
                        style_paths=style_paths,
                    ),
                    encoding="utf-8",
                )
                prompt_files[output_format] = (
                    active / folder / generator_path.name
                ).relative_to(carousel_dir).as_posix()
            records.append(
                {
                    "slide": number,
                    "copy": source["text"],
                    "prompt_files": prompt_files,
                }
            )
        remove_path_without_following(active)
        staging.replace(active)
    finally:
        remove_path_without_following(staging)

    handoff = build_compiled_prompt_handoff(
        carousel_dir,
        slide_numbers=selected,
        output_formats=output_formats,
    )
    return _write_state(
        carousel_dir,
        {
            **state,
            "status": "handoff_ready",
            "stage": stage,
            "slide_count": len(slide_plans),
            "selected_slides": selected,
            "requested_formats": output_formats,
            "attempts_by_slide": attempts,
            "approved_final_candidates": approved,
            "identity_reference_bindings": _reference_bindings(carousel_dir, identity_paths),
            "reference_bindings": _package_reference_bindings(
                carousel_dir,
                prompt_pack=prompt_pack,
                slides=slide_plans,
            ),
            "compiled_prompt_handoff": handoff,
            "slides": records,
            "next_action": "generate_selected_slides",
        },
    )


def image_dimensions(image_bytes: bytes) -> dict[str, int]:
    if len(image_bytes) < 24 or image_bytes[:8] != b"\x89PNG\r\n\x1a\n":
        raise ValueError("Generated output must be a PNG.")
    return {
        "width": int.from_bytes(image_bytes[16:20], "big"),
        "height": int.from_bytes(image_bytes[20:24], "big"),
    }


def target_size_for_format(output_format: str) -> tuple[int, int]:
    width, height = format_spec(output_format)["target_size"]
    return int(width), int(height)


def source_size_for_format(output_format: str) -> tuple[int, int]:
    return target_size_for_format(output_format)


def allowed_source_sizes_for_format(output_format: str) -> list[tuple[int, int]]:
    return [target_size_for_format(output_format)]


def require_native_source_dimensions(
    *,
    image_bytes: bytes,
    output_format: str,
    slide_number: int,
    path: Path,
) -> dict[str, int]:
    dimensions = image_dimensions(image_bytes)
    expected = target_size_for_format(output_format)
    actual = (dimensions["width"], dimensions["height"])
    if actual != expected:
        raise ValueError(
            f"Slide {slide_number} {output_format} must be native {expected[0]}x{expected[1]}; "
            f"got {actual[0]}x{actual[1]} from {path}. Resizing/cropping is not allowed."
        )
    return dimensions


def normalize_for_upload(
    image_bytes: bytes,
    width: int,
    height: int,
) -> tuple[bytes, dict[str, Any], str, str | None]:
    dimensions = image_dimensions(image_bytes)
    if (dimensions["width"], dimensions["height"]) != (width, height):
        raise ValueError("Wrong-size generated image; native regeneration is required.")
    return image_bytes, dimensions, "native_exact", None


def reject_non_codex_builtin_sources(
    carousel_dir: Path,
    generated_paths_by_format: dict[str, list[str | Path]],
) -> None:
    blocked_roots = [
        carousel_dir / "legacy-preview-clean",
        carousel_dir / "legacy-preview-text",
        carousel_dir / "final",
        carousel_dir / "final-reels-stories",
        carousel_dir / "final-square",
    ]
    for paths in generated_paths_by_format.values():
        for raw in paths:
            path = Path(raw).expanduser()
            if not path.is_file():
                raise FileNotFoundError(f"Missing generated image: {path}")
            resolved = path.resolve()
            if any(root.resolve() == resolved or root.resolve() in resolved.parents for root in blocked_roots):
                raise ValueError("Existing preview/final files cannot be recycled as fresh model output.")


def quarantine_dir(carousel_dir: Path, retry_count: int) -> Path:
    # Compatibility helper. New storage is slide-local; retry_count names the attempt.
    return carousel_dir / QUARANTINE_FOLDER / f"attempt-{retry_count + 1:02d}"


def _quarantine_slide_dir(carousel_dir: Path, slide: int, attempt: int) -> Path:
    return carousel_dir / QUARANTINE_FOLDER / f"slide-{slide:02d}" / f"attempt-{attempt:02d}"


def quarantine_generated_sources(
    carousel_dir: Path,
    *,
    slides: list[dict[str, Any]],
    output_formats: list[str] | tuple[str, ...],
    generated_paths_by_format: dict[str, list[str | Path]],
    attempts_by_slide: dict[str, int],
    **_: Any,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for index, slide in enumerate(slides):
        number = int(slide["slide"])
        attempt = int(attempts_by_slide.get(str(number), 0)) + 1
        root = _quarantine_slide_dir(carousel_dir, number, attempt)
        remove_path_without_following(root)
        root.mkdir(parents=True)
        outputs: dict[str, Any] = {}
        for output_format in output_formats:
            source = Path(generated_paths_by_format[output_format][index]).expanduser()
            payload = source.read_bytes()
            dimensions = require_native_source_dimensions(
                image_bytes=payload,
                output_format=output_format,
                slide_number=number,
                path=source,
            )
            target = root / f"{output_format}.png"
            target.write_bytes(payload)
            outputs[output_format] = {
                "path": package_relative_path(carousel_dir, target),
                "sha256": sha256_binding(payload),
                **dimensions,
            }
        records.append(
            {
                "slide": number,
                "copy": slide["copy"],
                "attempt": attempt,
                "native_outputs": outputs,
            }
        )
    return records


def image_set_sha256(slides: list[dict[str, Any]]) -> str:
    bindings = [
        {
            "slide": int(slide["slide"]),
            "outputs": {
                key: value.get("sha256")
                for key, value in sorted((slide.get("native_outputs") or {}).items())
            },
        }
        for slide in slides
    ]
    return _canonical_hash(bindings)


def validate_quarantine_integrity(
    slides: list[dict[str, Any]],
    output_formats: list[str] | tuple[str, ...] | None = None,
    *,
    carousel_dir: Path | None = None,
    **_: Any,
) -> list[str]:
    issues: list[str] = []
    formats = tuple(output_formats or ())
    for slide in slides:
        number = int(slide.get("slide", 0) or 0)
        outputs = slide.get("native_outputs")
        if not isinstance(outputs, dict):
            issues.append(f"slide {number} native outputs are missing")
            continue
        if formats and set(outputs) != set(formats):
            issues.append(f"slide {number} formats do not match the current lock")
        for output_format, binding in outputs.items():
            if not isinstance(binding, dict):
                issues.append(f"slide {number} {output_format} binding is malformed")
                continue
            if carousel_dir is None:
                continue
            try:
                path = resolve_package_artifact_path(carousel_dir, binding.get("path"), "")
            except ValueError as exc:
                issues.append(str(exc))
                continue
            if not path.is_file():
                issues.append(f"slide {number} {output_format} quarantine file is missing")
                continue
            payload = path.read_bytes()
            try:
                dimensions = image_dimensions(payload)
            except ValueError as exc:
                issues.append(f"slide {number} {output_format}: {exc}")
                continue
            if binding.get("sha256") != sha256_binding(payload):
                issues.append(f"slide {number} {output_format} quarantine hash is stale")
            if binding.get("width") != dimensions["width"] or binding.get("height") != dimensions["height"]:
                issues.append(f"slide {number} {output_format} quarantine dimensions are stale")
    return issues


def _qa_slide_map(visual_qa: dict[str, Any]) -> dict[int, dict[str, Any]]:
    raw = visual_qa.get("slides")
    if not isinstance(raw, list):
        return {}
    return {
        int(item.get("slide", 0) or 0): item
        for item in raw
        if isinstance(item, dict) and int(item.get("slide", 0) or 0) > 0
    }


def _check_pass(record: dict[str, Any], name: str) -> tuple[bool, str]:
    checks = record.get("checks")
    check = checks.get(name) if isinstance(checks, dict) else record.get(name)
    if not isinstance(check, dict):
        return False, f"missing {name} actual-pixel check"
    if str(check.get("status") or "").upper() != PASS and check.get("pass") is not True:
        return False, f"{name} failed"
    evidence = str(check.get("evidence") or check.get("observed") or "").strip()
    if len(evidence) < 8:
        return False, f"{name} needs concrete visible evidence"
    return True, ""


def _qa_slide_issues(
    qa_record: dict[str, Any] | None,
    candidate: dict[str, Any],
    *,
    carousel_dir: Path | None,
) -> list[str]:
    number = int(candidate["slide"])
    if not isinstance(qa_record, dict):
        return [f"slide {number} is missing from pixel QA"]
    issues: list[str] = []
    bindings = qa_record.get("native_outputs") or qa_record.get("formats")
    if not isinstance(bindings, dict):
        return [f"slide {number} QA is missing exact-image bindings"]
    for output_format, expected in candidate["native_outputs"].items():
        actual = bindings.get(output_format)
        if not isinstance(actual, dict):
            issues.append(f"slide {number} {output_format} QA binding is missing")
            continue
        for key in ("sha256", "width", "height"):
            if actual.get(key) != expected.get(key):
                issues.append(f"slide {number} {output_format} QA {key} is stale")
        if carousel_dir is not None and actual.get("path") not in (None, expected.get("path")):
            issues.append(f"slide {number} {output_format} QA path is stale")
    if issues:
        return issues

    # Fail fast in meaning-first order. Identity/style cannot rescue a picture
    # that does not visibly perform the intended action.
    for name in PIXEL_CHECKS:
        passed, issue = _check_pass(qa_record, name)
        if not passed:
            return [f"slide {number} {issue}"]

    exact = (qa_record.get("checks") or {}).get("exact_text", qa_record.get("exact_text"))
    if isinstance(exact, dict):
        expected_copy = str(candidate.get("copy") or "")
        if exact.get("expected") != expected_copy:
            return [f"slide {number} exact_text expected copy is stale"]
        observed = str(exact.get("observed") or "")
        if observed != expected_copy:
            return [f"slide {number} rendered copy is not exact"]
    return []


def validate_exact_image_visual_qa(
    visual_qa: dict[str, Any],
    quarantine_slides: list[dict[str, Any]],
    *,
    visual_plan: dict[str, Any] | None = None,
    carousel_dir: Path | None = None,
    **_: Any,
) -> list[str]:
    del visual_plan
    issues = validate_quarantine_integrity(
        quarantine_slides,
        carousel_dir=carousel_dir,
    )
    if issues:
        return issues
    if visual_qa.get("image_set_sha256") != image_set_sha256(quarantine_slides):
        return ["pixel QA image_set_sha256 is missing or stale"]
    qa_map = _qa_slide_map(visual_qa)
    for candidate in quarantine_slides:
        issues.extend(
            _qa_slide_issues(
                qa_map.get(int(candidate["slide"])),
                candidate,
                carousel_dir=carousel_dir,
            )
        )
    declared = str(visual_qa.get("status") or "").upper()
    if not issues and declared != PASS:
        issues.append("pixel QA status must be PASS when every slide check passes")
    return issues


def validate_creator_approval(
    approval: dict[str, Any],
    *,
    expected_image_set_sha256: str,
) -> list[str]:
    issues: list[str] = []
    if approval.get("approved") is not True or str(approval.get("status") or "").upper() != "APPROVED":
        issues.append("creator approval must be explicitly APPROVED")
    if approval.get("image_set_sha256") != expected_image_set_sha256:
        issues.append("creator approval is not bound to this proof image set")
    if not str(approval.get("approved_by") or "").strip():
        issues.append("creator approval must record approved_by")
    return issues


def visual_qa_issues_fingerprint(issues: list[str]) -> str:
    return _canonical_hash(issues)


def _copy_approved_candidate(
    carousel_dir: Path,
    candidate: dict[str, Any],
) -> dict[str, Any]:
    number = int(candidate["slide"])
    root = carousel_dir / APPROVED_CANDIDATE_FOLDER / f"slide-{number:02d}"
    remove_path_without_following(root)
    root.mkdir(parents=True)
    outputs: dict[str, Any] = {}
    for output_format, binding in candidate["native_outputs"].items():
        source = resolve_package_artifact_path(carousel_dir, binding["path"], "")
        target = root / f"{output_format}.png"
        shutil.copyfile(source, target)
        outputs[output_format] = {
            **binding,
            "path": package_relative_path(carousel_dir, target),
        }
    return {**candidate, "native_outputs": outputs}


def _qa_payload(path: Path) -> dict[str, Any] | None:
    return load_json(path) if path.is_file() else None


def _approval_payload(
    carousel_dir: Path,
    visual_qa: dict[str, Any],
    creator_approval_path: str | Path | None,
) -> dict[str, Any] | None:
    embedded = visual_qa.get("creator_approval")
    if isinstance(embedded, dict):
        return embedded
    if creator_approval_path is None:
        return None
    path = resolve_package_artifact_path(
        carousel_dir,
        creator_approval_path,
        "creator-proof-approval.json",
    )
    return _qa_payload(path)


def _finalize_complete_deck(
    carousel_dir: Path,
    *,
    approved: dict[str, Any],
    qa_records: dict[str, Any],
    state: dict[str, Any],
) -> dict[str, Any]:
    slides = _slides(carousel_dir)
    formats = list(locked_formats(carousel_dir))
    if set(approved) != {str(slide["slide"]) for slide in slides}:
        raise ValueError("Final manifest cannot be written before every slide has passed pixel QA.")

    staging = carousel_dir / PROMOTION_STAGING_FOLDER
    audit_root = carousel_dir / FINAL_AUDIT_CANDIDATE_FOLDER
    remove_path_without_following(staging)
    remove_path_without_following(audit_root)
    records: list[dict[str, Any]] = []
    prompt_handoff = state.get("compiled_prompt_handoff") or {}
    try:
        for slide in slides:
            number = int(slide["slide"])
            candidate = approved[str(number)]
            outputs: dict[str, Any] = {}
            for output_format in formats:
                source_binding = candidate["native_outputs"][output_format]
                source = resolve_package_artifact_path(carousel_dir, source_binding["path"], "")
                target = staging / str(format_spec(output_format)["folder"]) / f"slide-{number:02d}.png"
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(source, target)
                payload = target.read_bytes()
                dimensions = require_native_source_dimensions(
                    image_bytes=payload,
                    output_format=output_format,
                    slide_number=number,
                    path=target,
                )
                outputs[output_format] = {
                    "path": expected_output_path(carousel_dir, output_format, number).relative_to(
                        carousel_dir
                    ).as_posix(),
                    "sha256": sha256_binding(payload),
                    **dimensions,
                }
            records.append(
                {
                    "slide": number,
                    "copy": slide["copy"],
                    "native_outputs": outputs,
                    "qa": qa_records[str(number)],
                }
            )

        final_manifest = {
            "schema_version": "carousel-final-images/v2",
            "status": "PUBLISH_READY",
            "backend": BACKEND,
            "generation_mode": GENERATION_MODE,
            "slide_count": len(slides),
            "requested_formats": formats,
            "format_contract_sha256": locked_format_contract_fingerprint(carousel_dir),
            "prompt_handoff_sha256": prompt_handoff.get("fingerprint"),
            "identity_reference_bindings": state.get("identity_reference_bindings", []),
            "reference_bindings": state.get("reference_bindings", []),
            "slides": records,
        }
        final_qa = {
            "schema_version": "carousel-pixel-qa/v1",
            "scope": "final_deck",
            "status": PASS,
            "slides": [qa_records[str(slide["slide"])] for slide in slides],
        }

        # Audit a hidden, exact candidate package before any public final folder
        # or PUBLISH_READY manifest can exist.
        audit_root.mkdir(parents=True)
        for filename in (
            "creative-context.json",
            "format-contract.json",
            "slides.json",
            "prompt-pack.json",
        ):
            shutil.copyfile(carousel_dir / filename, audit_root / filename)
        for output_format in formats:
            folder = str(format_spec(output_format)["folder"])
            shutil.copytree(staging / folder, audit_root / folder)
        reference_root = carousel_dir / ".internal/references"
        if reference_root.is_dir():
            shutil.copytree(reference_root, audit_root / ".internal/references")
        write_json(audit_root / "final-images.json", final_manifest)
        write_json(audit_root / "visual-qa.json", final_qa)

        from pipeline.stages.carousel_quality import build_final_audit, write_final_audit

        audit = build_final_audit(audit_root, write=False)
        external_issues = []
        for output_format in SUPPORTED_NATIVE_FORMATS:
            if output_format in formats:
                continue
            folder = carousel_dir / str(format_spec(output_format)["folder"])
            if folder.is_dir() and any(folder.glob("*.png")):
                external_issues.append(f"unrequested format contains PNGs: {output_format}")
        if external_issues:
            audit = {
                **audit,
                "status": "FAIL",
                "pass": False,
                "issues": [*audit.get("issues", []), *external_issues],
            }
        if audit.get("pass") is not True:
            write_json(carousel_dir / "final-audit.json", audit)
            return _write_state(
                carousel_dir,
                {
                    **state,
                    "status": "generated_audit_failed",
                    "stage": "complete",
                    "selected_slides": [],
                    "approved_final_candidates": approved,
                    "qa_records": qa_records,
                    "final_audit_sha256": sha256_binding(
                        (carousel_dir / "final-audit.json").read_bytes()
                    ),
                    "next_action": "repair_final_audit",
                },
            )

        for output_format in formats:
            folder = str(format_spec(output_format)["folder"])
            final_dir = carousel_dir / folder
            remove_path_without_following(final_dir)
            (staging / folder).replace(final_dir)
        write_json(carousel_dir / "final-images.json", final_manifest)
        write_json(carousel_dir / "visual-qa.json", final_qa)
        audit = write_final_audit(carousel_dir)
        if audit.get("pass") is not True:
            for output_format in formats:
                remove_path_without_following(
                    carousel_dir / str(format_spec(output_format)["folder"])
                )
            remove_path_without_following(carousel_dir / "final-images.json")
            return _write_state(
                carousel_dir,
                {
                    **state,
                    "status": "generated_audit_failed",
                    "stage": "complete",
                    "selected_slides": [],
                    "approved_final_candidates": approved,
                    "qa_records": qa_records,
                    "final_audit_sha256": sha256_binding(
                        (carousel_dir / "final-audit.json").read_bytes()
                    ),
                    "next_action": "repair_final_audit",
                },
            )
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "publish_ready",
                "stage": "complete",
                "selected_slides": [],
                "approved_final_candidates": approved,
                "qa_records": qa_records,
                "final_images_sha256": sha256_binding(
                    (carousel_dir / "final-images.json").read_bytes()
                ),
                "final_audit_sha256": sha256_binding(
                    (carousel_dir / "final-audit.json").read_bytes()
                ),
                "next_action": "publish",
            },
        )
    finally:
        remove_path_without_following(staging)
        remove_path_without_following(audit_root)


def package_codex_builtin_outputs(
    carousel_dir: Path,
    generated_paths_by_format: dict[str, list[str | Path]] | None = None,
    *,
    refresh_quality: bool = True,
    visual_qa_path: str | Path | None = None,
    creator_approval_path: str | Path | None = None,
    proof_slide: int | None = None,
    promote_existing_quarantine: bool = False,
    **_: Any,
) -> dict[str, Any]:
    del refresh_quality
    carousel_dir = Path(carousel_dir).expanduser()
    state = _load_state(carousel_dir)
    formats = list(locked_formats(carousel_dir))
    selected = [int(value) for value in state.get("selected_slides") or []]
    stage = str(state.get("stage") or "proof")
    is_proof_scope = stage == "proof" or state.get("repair_scope") == "proof"
    attempts = {
        str(key): int(value)
        for key, value in (state.get("attempts_by_slide") or {}).items()
    }

    current_format_fingerprint = locked_format_contract_fingerprint(carousel_dir)
    if (
        state.get("proof_approved") is True
        and state.get("proof_format_contract_sha256") != current_format_fingerprint
    ):
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "blocked",
                "next_action": "regenerate_proof_for_format_change",
                "reason": "The locked format changed after proof approval.",
            },
        )
    handoff_issues = compiled_prompt_handoff_integrity_issues(carousel_dir, state=state)
    if handoff_issues:
        return _write_state(
            carousel_dir,
            {
                **state,
                "status": "blocked",
                "next_action": "recompile_prompt_handoff",
                "reason": "; ".join(handoff_issues),
            },
        )

    if promote_existing_quarantine:
        candidates = list(state.get("quarantine_candidates") or [])
        if not candidates:
            raise ValueError("No quarantined candidates exist to re-evaluate.")
    else:
        if state.get("status") != "handoff_ready":
            raise ValueError("Prepare the compiled prompt handoff before packaging images.")
        if proof_slide is not None and selected != [int(proof_slide)]:
            raise ValueError("proof_slide does not match the active compiled handoff.")
        supplied = generated_paths_by_format or {}
        if set(supplied) != set(formats):
            raise ValueError("Generated formats must match format-contract.json exactly.")
        if any(len(supplied[value]) != len(selected) for value in formats):
            raise ValueError("Each locked format needs one generated image per selected slide.")
        reject_non_codex_builtin_sources(carousel_dir, supplied)
        plan_by_number = {int(item["slide"]): item for item in _slides(carousel_dir)}
        candidates = quarantine_generated_sources(
            carousel_dir,
            slides=[plan_by_number[number] for number in selected],
            output_formats=formats,
            generated_paths_by_format=supplied,
            attempts_by_slide=attempts,
        )
        for candidate in candidates:
            attempts[str(candidate["slide"])] = int(candidate["attempt"])

    set_hash = image_set_sha256(candidates)
    qa_default = "proof-qa.json" if is_proof_scope else "visual-qa.json"
    qa_path = resolve_package_artifact_path(carousel_dir, visual_qa_path, qa_default)
    pending = {
        **state,
        "status": "generated_quarantined",
        "attempts_by_slide": attempts,
        "quarantine_candidates": candidates,
        "image_set_sha256": set_hash,
        "qa_path": package_relative_path(carousel_dir, qa_path),
        "next_action": "run_actual_pixel_qa",
    }
    # A freshly generated candidate must never consume a QA file left by a
    # previous attempt. Generation and review are deliberately separate calls;
    # only explicit quarantine promotion evaluates the now-current QA binding.
    if not promote_existing_quarantine:
        return _write_state(carousel_dir, pending)
    qa = _qa_payload(qa_path)
    if qa is None:
        return _write_state(carousel_dir, pending)

    qa_map = _qa_slide_map(qa)
    issues_by_slide: dict[str, list[str]] = {}
    for candidate in candidates:
        number = int(candidate["slide"])
        issues_by_slide[str(number)] = _qa_slide_issues(
            qa_map.get(number), candidate, carousel_dir=carousel_dir
        )
    top_binding_issue = (
        [] if qa.get("image_set_sha256") == set_hash else ["pixel QA image_set_sha256 is stale"]
    )
    if top_binding_issue:
        issues_by_slide[str(candidates[0]["slide"])].extend(top_binding_issue)

    failed = [int(number) for number, issues in issues_by_slide.items() if issues]
    qa_records = dict(state.get("qa_records") or {})
    approved = dict(state.get("approved_final_candidates") or {})
    for candidate in candidates:
        number = int(candidate["slide"])
        if number in failed:
            continue
        qa_records[str(number)] = qa_map[number]
        if not is_proof_scope:
            approved[str(number)] = _copy_approved_candidate(carousel_dir, candidate)

    if failed:
        exhausted = [number for number in failed if attempts[str(number)] >= MAX_SEMANTIC_ATTEMPTS]
        status = "blocked_visual_qa" if exhausted else "proof_failed"
        return _write_state(
            carousel_dir,
            {
                **pending,
                "status": status,
                "stage": "repair",
                "repair_scope": (
                    "proof" if is_proof_scope else "final"
                ),
                "repair_slides": failed,
                "visual_qa_issues": issues_by_slide,
                "qa_records": qa_records,
                "approved_final_candidates": approved,
                "next_action": (
                    "revise_copy_or_visual_premise" if exhausted else "repair_visual_premise"
                ),
            },
        )

    if str(qa.get("status") or "").upper() != PASS:
        return _write_state(
            carousel_dir,
            {
                **pending,
                "status": "proof_failed",
                "stage": "repair",
                "repair_slides": selected,
                "visual_qa_issues": {str(value): ["pixel QA status is not PASS"] for value in selected},
                "next_action": "repair_visual_premise",
            },
        )

    if is_proof_scope:
        approval = _approval_payload(carousel_dir, qa, creator_approval_path)
        if approval is None:
            return _write_state(
                carousel_dir,
                {
                    **pending,
                    "status": "qa_pass_candidate",
                    "proof_qa_sha256": sha256_binding(qa_path.read_bytes()),
                    "next_action": "creator_approve_proof",
                },
            )
        approval_issues = validate_creator_approval(
            approval,
            expected_image_set_sha256=set_hash,
        )
        if approval_issues:
            return _write_state(
                carousel_dir,
                {
                    **pending,
                    "status": "qa_pass_candidate",
                    "creator_approval_issues": approval_issues,
                    "next_action": "creator_approve_proof",
                },
            )
        return _write_state(
            carousel_dir,
            {
                **pending,
                "status": "BATCH_ALLOWED",
                "stage": "batch",
                "proof_approved": True,
                "proof_qa_sha256": sha256_binding(qa_path.read_bytes()),
                "proof_image_set_sha256": set_hash,
                "proof_format_contract_sha256": current_format_fingerprint,
                "creator_approval": approval,
                "repair_slides": [],
                "next_action": "prepare_remaining_slides",
            },
        )

    expected_numbers = {str(slide["slide"]) for slide in _slides(carousel_dir)}
    if set(approved) != expected_numbers:
        remaining = sorted(int(value) for value in expected_numbers - set(approved))
        return _write_state(
            carousel_dir,
            {
                **pending,
                "status": "BATCH_ALLOWED",
                "stage": "batch",
                "proof_approved": True,
                "approved_final_candidates": approved,
                "qa_records": qa_records,
                "selected_slides": [],
                "remaining_slides": remaining,
                "next_action": "prepare_remaining_slides",
            },
        )
    return _finalize_complete_deck(
        carousel_dir,
        approved=approved,
        qa_records=qa_records,
        state={**pending, "approved_final_candidates": approved, "qa_records": qa_records},
    )


def promote_quarantined_codex_builtin_outputs(
    carousel_dir: Path,
    *,
    refresh_quality: bool = True,
    visual_qa_path: str | Path | None = None,
    creator_approval_path: str | Path | None = None,
) -> dict[str, Any]:
    return package_codex_builtin_outputs(
        carousel_dir,
        refresh_quality=refresh_quality,
        visual_qa_path=visual_qa_path,
        creator_approval_path=creator_approval_path,
        promote_existing_quarantine=True,
    )


def recompile_failed_proof_handoff(carousel_dir: Path) -> dict[str, Any]:
    state = _load_state(carousel_dir)
    if state.get("status") != "proof_failed":
        raise ValueError("Only a QA-failed slide can be recompiled for repair.")
    return prepare_codex_builtin_image_generation(carousel_dir)


def accept_failed_proof_by_creator(*_: Any, **__: Any) -> dict[str, Any]:
    raise ValueError(
        "A failed proof cannot be accepted as production evidence. Repair the visual premise."
    )


def load_attempt_ledger(carousel_dir: Path) -> dict[str, Any]:
    state = _load_state(carousel_dir)
    return {
        "schema_version": "slide-attempts/v2",
        "attempts_by_slide": state.get("attempts_by_slide", {}),
        "attempts": [],
    }


def next_retry_count(
    carousel_dir: Path,
    proof_slide: int | None = None,
    **_: Any,
) -> int:
    state = _load_state(carousel_dir)
    number = proof_slide or next(iter(state.get("selected_slides") or [1]))
    return int((state.get("attempts_by_slide") or {}).get(str(number), 0))


def run_fail_closed_visual_worker(
    carousel_dir: Path,
    *,
    generate_attempt: Callable[[int, list[str]], dict[str, list[str | Path]]],
    review_attempt: Callable[[dict[str, Any]], dict[str, Any]],
    proof_slide: int | None = None,
    **_: Any,
) -> dict[str, Any]:
    repair_issues: list[str] = []
    for attempt in range(MAX_SEMANTIC_ATTEMPTS):
        prepare_codex_builtin_image_generation(carousel_dir, proof_slide=proof_slide)
        generated = generate_attempt(attempt, repair_issues)
        state = package_codex_builtin_outputs(
            carousel_dir,
            generated_paths_by_format=generated,
            proof_slide=proof_slide,
        )
        qa = review_attempt(state)
        qa_name = (
            "proof-qa.json"
            if state.get("stage") == "proof" or state.get("repair_scope") == "proof"
            else "visual-qa.json"
        )
        write_json(carousel_dir / qa_name, qa)
        state = promote_quarantined_codex_builtin_outputs(carousel_dir)
        if state.get("status") not in {"proof_failed", "blocked_visual_qa"}:
            return state
        repair_issues = [
            issue
            for issues in (state.get("visual_qa_issues") or {}).values()
            for issue in issues
        ]
    return _load_state(carousel_dir)


def write_blocked_status(carousel_dir: Path, reason: str) -> dict[str, Any]:
    state = _load_state(carousel_dir)
    return _write_state(
        carousel_dir,
        {**state, "status": "blocked", "reason": reason, "next_action": "repair_inputs"},
    )


def write_handoff_blocker(*_: Any, **__: Any) -> None:
    # The transient state is the blocker/next-action surface.
    return None


def existing_paths(raw_paths: list[Any]) -> list[Path]:
    return [Path(str(value)).expanduser() for value in raw_paths if Path(str(value)).expanduser().is_file()]


def slide_source_paths(slide: dict[str, Any]) -> list[Path]:
    return existing_paths(list(slide.get("source_images") or []))


def requested_native_output_formats(formats: list[str] | None) -> list[str]:
    return list(normalize_requested_formats(formats))


def expected_file_for_format(carousel_dir: Path, output_format: str, number: int) -> Path:
    return expected_output_path(carousel_dir, output_format, number)


def clean_packaged_output_files(carousel_dir: Path, slide_numbers: list[int]) -> None:
    for output_format in locked_formats(carousel_dir):
        for number in slide_numbers:
            path = expected_output_path(carousel_dir, output_format, number)
            if path.is_file() or path.is_symlink():
                path.unlink()


def infer_workspace_root_from_carousel_dir(carousel_dir: Path) -> Path:
    resolved = Path(carousel_dir).resolve()
    for parent in (resolved, *resolved.parents):
        if (parent / "AGENTS.md").is_file() and (parent / "pipeline").is_dir():
            return parent
    return Path(__file__).resolve().parents[2]


__all__ = [
    "BACKEND",
    "GENERATION_MODE",
    "MAX_SEMANTIC_ATTEMPTS",
    "accept_failed_proof_by_creator",
    "approved_proof_batch_handoff_attestation_issues",
    "build_compiled_prompt_handoff",
    "build_handoff_markdown",
    "compiled_prompt_handoff_integrity_issues",
    "creator_override_batch_handoff_integrity_issues",
    "generator_prompt_text",
    "image_set_sha256",
    "infer_workspace_root_from_carousel_dir",
    "load_attempt_ledger",
    "next_retry_count",
    "package_codex_builtin_outputs",
    "prepare_codex_builtin_image_generation",
    "promote_quarantined_codex_builtin_outputs",
    "recompile_failed_proof_handoff",
    "retry_prompt_handoff_attestation_issues",
    "run_fail_closed_visual_worker",
    "sha256_binding",
    "validate_exact_image_visual_qa",
    "validate_quarantine_integrity",
]
