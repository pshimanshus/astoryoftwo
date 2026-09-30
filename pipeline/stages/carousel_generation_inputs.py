"""Canonical, slide-local fingerprints for the carousel generation hot path.

The state machine stores these digests instead of serializing creative inputs.
JSON formatting and object-key order therefore cannot invalidate generated
work, while a real semantic, prompt, reference, format, or brand change does.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    locked_format_contract_fingerprint,
    locked_formats,
)
from pipeline.stages.carousel_contract import (
    load_active_illustration_style_profile,
    resolve_style_profile_reference_path,
    style_profile_contract_sha256,
)
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt
from pipeline.stages.carousel_visual_storytelling import active_feedback_constraints


INPUT_SCHEMA_VERSION = "carousel-generation-inputs/v3"
REFERENCE_BINDING_SCHEMA_VERSION = "carousel-reference-bindings/v2-style-profile"
PROMPT_COMPILER_VERSION = "carousel-prompt-compiler/v5-cinematic-profile"
BRAND_CONTRACT_VERSION = "a-story-brand/v1"
VISUAL_PREMISE_SCHEMA_VERSION = "carousel-visual-premise/v1"

SLIDE_SOURCE_FIELDS = (
    "slide",
    "role",
    "copy",
    "copy_mode",
    "beat_delta",
    "copy_image_relation",
    "physical_action",
    "relationship_state",
    "camera",
    "focal_hierarchy",
    "setting",
    "wardrobe",
    "props",
    "emotion",
    "continuity_lock",
    "negative_prompt",
    "hand_map",
    "spatial_topology",
    "visual_richness",
)


def canonical_json_bytes(value: Any) -> bytes:
    """Encode JSON semantics, independent of whitespace and key order."""

    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_binding(payload: bytes) -> str:
    return "sha256:" + hashlib.sha256(payload).hexdigest()


def canonical_fingerprint(value: Any) -> str:
    return sha256_binding(canonical_json_bytes(value))


def _read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def _package_file(package_dir: Path, raw_path: Any, *, role: str) -> Path:
    package_path = Path(package_dir).expanduser()
    if package_path.is_symlink():
        raise ValueError("carousel package path cannot itself be a symlink")
    supplied_root = Path(os.path.abspath(package_path))
    root = package_path.resolve(strict=True)
    path = Path(str(raw_path)).expanduser()
    if not path.is_absolute():
        path = supplied_root / path
    path = Path(os.path.abspath(path))
    lexical_relative: Path | None = None
    for candidate_root in (supplied_root, root):
        try:
            lexical_relative = path.relative_to(candidate_root)
            break
        except ValueError:
            continue
    if lexical_relative is not None:
        cursor = root
        for part in lexical_relative.parts:
            cursor /= part
            if cursor.is_symlink():
                raise ValueError(
                    f"{role} reference cannot contain package-local symlink components: {raw_path}"
                )
    try:
        resolved = path.resolve(strict=True)
        resolved.relative_to(root)
    except (FileNotFoundError, OSError, ValueError) as exc:
        raise ValueError(
            f"{role} reference is missing or outside the carousel package: {raw_path}"
        ) from exc
    if not resolved.is_file():
        raise ValueError(f"{role} reference is not a regular file: {raw_path}")
    return resolved


def _reference_bindings(
    package_dir: Path,
    values: list[Any],
    *,
    role: str,
) -> list[dict[str, str]]:
    by_role_and_path: dict[tuple[str, str], dict[str, str]] = {}
    root = package_dir.resolve(strict=True)
    for raw_path in values:
        path = _package_file(package_dir, raw_path, role=role)
        relative = path.relative_to(root).as_posix()
        binding = {
            "role": role,
            "path": relative,
            "sha256": sha256_binding(path.read_bytes()),
        }
        by_role_and_path[(role, relative)] = binding
    return [
        by_role_and_path[key]
        for key in sorted(by_role_and_path)
    ]


def _shared_reference_bindings(
    package_dir: Path,
    prompt_pack: dict[str, Any],
    creative_context: dict[str, Any],
    *,
    require_complete_identity_bundle: bool = False,
) -> list[dict[str, str]]:
    """Return canonical identity/style bindings from the real prompt-pack keys.

    Prompt-pack lists are the generation attachment authority after selected
    references have been localized into the package. The list order is not
    semantic; the binding role, package-relative path, and exact file bytes
    are. Keeping those three values in one sorted structure makes reference
    drift explicit in every slide fingerprint.
    """

    root = package_dir.resolve(strict=True)
    selection = creative_context.get("identity_reference_selection")
    selected = selection.get("selected_references") if isinstance(selection, dict) else []
    role_by_path: dict[str, str] = {}
    for record in selected if isinstance(selected, list) else []:
        if not isinstance(record, dict) or not record.get("path"):
            continue
        path = _package_file(package_dir, record["path"], role="identity selection")
        role_by_path[path.relative_to(root).as_posix()] = str(
            record.get("role") or "unassigned identity role"
        )

    identity_paths = prompt_pack.get("identity_reference_images")
    if not isinstance(identity_paths, list):
        raise ValueError("prompt-pack.json identity_reference_images must be a list.")
    if require_complete_identity_bundle:
        if len(identity_paths) != 4:
            raise ValueError("prompt-pack.json must bind exactly four identity photographs.")
        if len({str(value) for value in identity_paths}) != 4:
            raise ValueError("prompt-pack.json identity photographs must be four distinct files.")

    identity_bindings: list[dict[str, str]] = []
    for raw_path in identity_paths:
        path = _package_file(package_dir, raw_path, role="identity")
        relative = path.relative_to(root).as_posix()
        identity_bindings.append(
            {
                "role": f"identity:{role_by_path.get(relative, 'unassigned identity role')}",
                "path": relative,
                "sha256": sha256_binding(path.read_bytes()),
            }
        )

    profile = prompt_pack.get("style_profile")
    reference = profile.get("reference") if isinstance(profile, dict) else None
    style_path = reference.get("path") if isinstance(reference, dict) else None
    style_role = (
        f"style:{profile.get('id')}@{profile.get('version')}"
        if isinstance(profile, dict)
        else "style"
    )
    bindings = [
        *identity_bindings,
        *_reference_bindings(
            package_dir,
            [style_path] if str(style_path or "").strip() else [],
            role=style_role,
        ),
    ]
    return sorted(
        bindings,
        key=lambda binding: (
            binding["role"],
            binding["path"],
            binding["sha256"],
        ),
    )


def _validated_style_profile_snapshot(
    package_dir: Path,
    prompt_pack: dict[str, Any],
) -> dict[str, Any]:
    schema = str(prompt_pack.get("schema_version") or "")
    if schema == "carousel-prompt-pack/v2":
        raise ValueError(
            "carousel-prompt-pack/v2 is historical and read-only; rebuild this package before generation."
        )
    if schema != "carousel-prompt-pack/v3":
        raise ValueError("prompt-pack.json must use carousel-prompt-pack/v3.")
    retired_keys = {
        "identity_dossier_reference_images",
        "slides",
        "style_prompt",
        "shared_style_prompt",
        "shared_negative_prompt",
        "negative_prompt",
        "style_reference_images",
    }
    present = sorted(retired_keys & set(prompt_pack))
    if present:
        raise ValueError(
            "carousel-prompt-pack/v3 contains retired duplicate fields: " + ", ".join(present)
        )
    snapshot = prompt_pack.get("style_profile")
    if not isinstance(snapshot, dict):
        raise ValueError("prompt-pack.json must contain one style_profile object.")
    reference = snapshot.get("reference")
    if not isinstance(reference, dict):
        raise ValueError("prompt-pack.json style_profile must contain one reference object.")
    localized = _package_file(package_dir, reference.get("path"), role="style")

    active = load_active_illustration_style_profile()
    active_reference_path = resolve_style_profile_reference_path(active)
    active_reference_digest = str(active["reference"]["sha256"]).removeprefix("sha256:")
    expected_local_reference_path = (
        Path(".internal")
        / "references"
        / "style"
        / f"{active_reference_digest[:20]}{active_reference_path.suffix.lower()}"
    ).as_posix()
    expected = {
        "id": active["id"],
        "version": active["version"],
        "contract_sha256": style_profile_contract_sha256(active),
        "generation_prompt": active["generation_prompt"],
        "negative_prompt": active["negative_prompt"],
        "reference_path": expected_local_reference_path,
        "reference_sha256": active["reference"]["sha256"],
        "attachment_count": active["reference"]["attachment_count"],
    }
    observed = {
        "id": snapshot.get("id"),
        "version": snapshot.get("version"),
        "contract_sha256": snapshot.get("contract_sha256"),
        "generation_prompt": snapshot.get("generation_prompt"),
        "negative_prompt": snapshot.get("negative_prompt"),
        "reference_path": reference.get("path"),
        "reference_sha256": reference.get("sha256"),
        "attachment_count": reference.get("attachment_count"),
    }
    if observed != expected:
        changed = sorted(key for key in expected if observed.get(key) != expected[key])
        raise ValueError("style_profile_stale: " + ", ".join(changed))

    actual_sha256 = sha256_binding(localized.read_bytes())
    if actual_sha256 != expected["reference_sha256"]:
        raise ValueError("style_profile_stale: reference bytes do not match the active profile")
    return snapshot


def build_shared_reference_bindings(package_dir: Path) -> list[dict[str, str]]:
    """Return the canonical named identity/style attachment bindings.

    This is the single public adapter for generation handoffs that need the
    exact same role, path, and byte bindings used by slide fingerprints.
    """

    package_dir = Path(package_dir).expanduser()
    prompt_pack = _read_json(package_dir / "prompt-pack.json")
    creative_context = _read_json(package_dir / "creative-context.json")
    if not isinstance(prompt_pack, dict):
        raise ValueError("prompt-pack.json must contain a JSON object.")
    if not isinstance(creative_context, dict):
        raise ValueError("creative-context.json must contain a JSON object.")
    _validated_style_profile_snapshot(package_dir, prompt_pack)
    return _shared_reference_bindings(
        package_dir,
        prompt_pack,
        creative_context,
        require_complete_identity_bundle=True,
    )


def _slide_source(slide: dict[str, Any]) -> dict[str, Any]:
    return {
        key: slide[key]
        for key in SLIDE_SOURCE_FIELDS
        if key in slide and slide[key] not in (None, "", [])
    }


def visual_premise_fingerprint(slide: dict[str, Any]) -> str:
    """Fingerprint the staged event, not prompt polish around that event.

    The hand and topology contracts both carry the same scene-action binding
    when a slide has completed visual direction.  That shared binding is a
    more stable premise anchor than camera, wardrobe, copy, or hand-detail
    wording.  Draft/legacy slides fall back to their physical action.  When
    the structured bindings disagree, keep the first non-empty binding rather
    than granting a fresh retry for an ambiguous prompt-only edit.
    """

    bindings: list[str] = []
    for field in ("hand_map", "spatial_topology"):
        value = slide.get(field)
        if not isinstance(value, dict):
            continue
        binding = " ".join(str(value.get("scene_action_binding") or "").split())
        if binding and binding not in bindings:
            bindings.append(binding)
    fallback = " ".join(
        str(
            slide.get("physical_action")
            or slide.get("visual")
            or slide.get("scene")
            or ""
        ).split()
    )
    staged_action = bindings[0] if bindings else fallback
    return canonical_fingerprint(
        {
            "schema_version": VISUAL_PREMISE_SCHEMA_VERSION,
            "staged_action": staged_action,
        }
    )


def effective_slide_prompt_fields(
    slide: dict[str, Any],
    *,
    shared_negative: str,
) -> dict[str, Any]:
    """Return the slide-authoritative generator fields for new v3 packages.

    ``slides.json`` is the only per-slide authority. ``prompt-pack.json`` owns
    only the immutable shared profile and reference snapshot.
    """

    scene = str(
        slide.get("physical_action")
        or slide.get("visual")
        or slide.get("scene")
        or ""
    )
    return {
        "scene": scene,
        "camera": slide.get("camera"),
        "focal_hierarchy": str(slide.get("focal_hierarchy") or ""),
        "setting": slide.get("setting"),
        "wardrobe": str(slide.get("wardrobe") or ""),
        "props": str(slide.get("props") or ""),
        "relationship_state": str(
            slide.get("relationship_state") or slide.get("emotion") or ""
        ),
        "emotion": str(slide.get("emotion") or ""),
        "continuity_lock": str(slide.get("continuity_lock") or ""),
        "negative_prompt": " ".join(
            value
            for value in (
                str(shared_negative).strip(),
                str(slide.get("negative_prompt") or "").strip(),
            )
            if value
        ),
        "hand_map": slide.get("hand_map"),
        "spatial_topology": slide.get("spatial_topology"),
        "visual_richness": slide.get("visual_richness"),
        **{key: slide[key] for key in ("copy_mode", "beat_delta", "copy_image_relation") if key in slide},
    }


def _compiled_prompt_fingerprint(
    *,
    slide: dict[str, Any],
    slide_count: int,
    formats: tuple[str, ...],
    style: str,
    negative: str,
    feedback_constraints: list[dict[str, Any]] | None = None,
) -> str:
    effective = effective_slide_prompt_fields(
        slide,
        shared_negative=negative,
    )
    prompt_bytes: list[dict[str, str]] = []
    for output_format in formats:
        try:
            compiled = compile_image_prompt(
                slide_number=int(slide["slide"]),
                slide_count=slide_count,
                slide_copy=str(slide.get("copy") or ""),
                copy_mode=effective.get("copy_mode", "text"),
                beat_delta=effective.get("beat_delta"),
                copy_image_relation=effective.get("copy_image_relation"),
                visual=effective["scene"],
                format_key=output_format,
                style=style,
                negative=effective["negative_prompt"],
                camera=effective["camera"],
                focal_hierarchy=effective["focal_hierarchy"],
                setting=effective["setting"],
                wardrobe=effective["wardrobe"],
                props=effective["props"],
                relationship_state=effective["relationship_state"],
                emotion=effective["emotion"],
                continuity_lock=effective["continuity_lock"],
                hand_map=effective["hand_map"],
                spatial_topology=effective["spatial_topology"],
                visual_richness=effective["visual_richness"],
                feedback_constraints=feedback_constraints,
            ).encode("utf-8")
        except ValueError as exc:
            # Draft packages must remain serializable before visual direction is
            # complete. The typed blocked reason is fingerprinted; the single
            # pre-generation gate still refuses to create a handoff.
            prompt_bytes.append(
                {
                    "format": output_format,
                    "blocked_sha256": canonical_fingerprint(
                        {
                            "reason": str(exc),
                            "effective_fields": effective,
                            "feedback_constraints": feedback_constraints or [],
                        }
                    ),
                }
            )
        else:
            prompt_bytes.append(
                {
                    "format": output_format,
                    "sha256": sha256_binding(compiled),
                }
            )
    return canonical_fingerprint(
        {
            "compiler_version": PROMPT_COMPILER_VERSION,
            "compiled_prompts": prompt_bytes,
        }
    )


def build_generation_inputs(package_dir: Path) -> dict[str, Any]:
    """Build the canonical current input snapshot for every slide."""

    package_dir = Path(package_dir).expanduser()
    slides_payload = _read_json(package_dir / "slides.json")
    prompt_pack = _read_json(package_dir / "prompt-pack.json")
    creative_context = _read_json(package_dir / "creative-context.json")
    if not isinstance(slides_payload, list) or not slides_payload:
        raise ValueError("slides.json must contain at least one slide.")
    if not isinstance(prompt_pack, dict):
        raise ValueError("prompt-pack.json must contain a JSON object.")
    if not isinstance(creative_context, dict):
        raise ValueError("creative-context.json must contain a JSON object.")
    style_profile = _validated_style_profile_snapshot(package_dir, prompt_pack)

    slides = [item for item in slides_payload if isinstance(item, dict)]
    numbers = [int(item.get("slide", 0) or 0) for item in slides]
    if numbers != list(range(1, len(slides) + 1)):
        raise ValueError("slides.json slide numbers must be unique and sequential from 1.")
    formats = tuple(locked_formats(package_dir))
    format_sha256 = locked_format_contract_fingerprint(package_dir)
    shared_reference_bindings = _shared_reference_bindings(
        package_dir,
        prompt_pack,
        creative_context,
    )
    shared = {
        "compiler_version": PROMPT_COMPILER_VERSION,
        "brand_contract_version": BRAND_CONTRACT_VERSION,
        "brandmark": str(prompt_pack.get("brandmark") or "@a.storyof.two"),
        "brandmark_placement": "top-right",
        "style_profile": style_profile,
        "reference_binding_schema_version": REFERENCE_BINDING_SCHEMA_VERSION,
        "shared_references": shared_reference_bindings,
        "formats": list(formats),
        "format_sha256": format_sha256,
        "slide_order": numbers,
    }
    shared_sha256 = canonical_fingerprint(shared)
    result_slides: dict[str, dict[str, str]] = {}
    style = str(style_profile["generation_prompt"])
    negative = str(style_profile["negative_prompt"])
    for slide in slides:
        number = int(slide["slide"])
        source = _slide_source(slide)
        feedback_constraints = active_feedback_constraints(package_dir, number)
        # Keep legacy/no-feedback source bytes and fingerprints exactly stable.
        # Active v2 feedback is slide-local generation input only when present.
        if feedback_constraints:
            source["feedback_constraints"] = feedback_constraints
        source_sha256 = canonical_fingerprint(source)
        prompt_sha256 = _compiled_prompt_fingerprint(
            slide=slide,
            slide_count=len(slides),
            formats=formats,
            style=style,
            negative=negative,
            feedback_constraints=feedback_constraints,
        )
        story_bindings = _reference_bindings(
            package_dir,
            list(slide.get("source_images") or []),
            role="story",
        )
        references_sha256 = canonical_fingerprint(
            {
                "schema_version": REFERENCE_BINDING_SCHEMA_VERSION,
                "shared": shared_reference_bindings,
                "story": story_bindings,
            }
        )
        input_sha256 = canonical_fingerprint(
            {
                "source_sha256": source_sha256,
                "prompt_sha256": prompt_sha256,
                "references_sha256": references_sha256,
                "shared_sha256": shared_sha256,
            }
        )
        result_slides[str(number)] = {
            "premise_sha256": visual_premise_fingerprint(slide),
            "source_sha256": source_sha256,
            "prompt_sha256": prompt_sha256,
            "references_sha256": references_sha256,
            "input_sha256": input_sha256,
        }

    return {
        "schema_version": INPUT_SCHEMA_VERSION,
        "selected_formats": list(formats),
        "format_sha256": format_sha256,
        "shared_sha256": shared_sha256,
        "slides": result_slides,
    }


__all__ = [
    "BRAND_CONTRACT_VERSION",
    "INPUT_SCHEMA_VERSION",
    "PROMPT_COMPILER_VERSION",
    "VISUAL_PREMISE_SCHEMA_VERSION",
    "build_generation_inputs",
    "build_shared_reference_bindings",
    "canonical_fingerprint",
    "canonical_json_bytes",
    "sha256_binding",
    "visual_premise_fingerprint",
]
