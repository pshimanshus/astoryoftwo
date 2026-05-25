from __future__ import annotations

import json
import re
import shutil
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt, extract_scene_summary
from pipeline.stages.carousel_style_consistency import house_style_consistency_gate_reason
from pipeline.stages.model_native_image_generation import (
    FINAL_UPLOAD_SIZE,
    INSTAGRAM_POST_FORMAT,
    NATIVE_OUTPUT_CONTRACT,
    NATIVE_OUTPUT_FORMATS,
    REELS_STORIES_FORMAT,
    REELS_STORIES_SIZE,
    contain_on_paper,
    decode_png,
    existing_reference_paths,
    normalize_native_output,
    prompt_for_native_format,
)


BACKEND = "codex_builtin"
GENERATION_MODE = "model_native_publishable"


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def identity_consistency_gate_reason(carousel_dir: Path) -> str | None:
    review_path = carousel_dir / "identity-consistency-review.json"
    if not review_path.exists():
        return "identity-consistency-review.json is required before Codex built-in image generation."
    review = load_json(review_path)
    if review.get("status") != "PASS":
        issues = review.get("issues") or ["identity consistency review did not pass"]
        return "identity-consistency-review.json did not pass: " + "; ".join(str(issue) for issue in issues)
    return None


def visual_plan_quality_gate_reason(carousel_dir: Path) -> str | None:
    review_path = carousel_dir / "visual-plan-quality.json"
    if not review_path.exists():
        return "visual-plan-quality.json is required as the per-slide pre-generation visual screen before Codex built-in image generation."
    review = load_json(review_path)
    if review.get("status") != "PASS" or not review.get("can_generate"):
        issues = review.get("issues") or ["pre-generation visual screen did not pass"]
        return "visual-plan-quality.json did not pass: " + "; ".join(str(issue) for issue in issues)
    return None


def existing_paths(raw_paths: list[Any]) -> list[Path]:
    paths: list[Path] = []
    seen: set[str] = set()
    for raw in raw_paths:
        path = Path(str(raw)).expanduser()
        marker = str(path)
        if marker not in seen and path.exists():
            paths.append(path)
            seen.add(marker)
    return paths


def slide_source_paths(slide: dict[str, Any]) -> list[Path]:
    return existing_paths(slide.get("source_images", []))


def generator_prompt_text(slide_prompt: dict[str, Any], output_format: str) -> str:
    visual = slide_prompt.get("visual") or slide_prompt.get("scene")
    if not visual:
        visual = extract_scene_summary(str(slide_prompt["prompt"]))
    return compile_image_prompt(
        int(slide_prompt["slide"]),
        int(slide_prompt.get("slide_count") or 0) or 1,
        str(slide_prompt["text"]),
        str(visual),
        output_format,
        str(slide_prompt.get("style") or "warm hand-drawn desi storybook illustration"),
        str(slide_prompt.get("negative_prompt") or "No photorealism, no 3D, no stock couple, no quote card."),
    )


def reject_non_codex_builtin_sources(carousel_dir: Path, generated_paths_by_format: dict[str, list[str | Path]]) -> None:
    carousel_root = carousel_dir.expanduser().resolve()
    forbidden_markers = {
        "tmp-generated/local-native",
        "tmp-generated\\local-native",
        "source-generated-local",
    }
    rejected: list[str] = []
    for paths in generated_paths_by_format.values():
        for raw_path in paths:
            path = Path(raw_path).expanduser()
            marker = str(path)
            resolved_marker = str(path.resolve()) if path.exists() else marker
            normalized = marker.replace("\\", "/")
            normalized_resolved = resolved_marker.replace("\\", "/")
            inside_carousel = False
            try:
                path.resolve().relative_to(carousel_root)
                inside_carousel = True
            except (FileNotFoundError, ValueError):
                inside_carousel = False
            if any(token in normalized or token in normalized_resolved for token in forbidden_markers):
                rejected.append(marker)
            elif inside_carousel and "model-native-source" not in normalized_resolved:
                rejected.append(marker)
    if rejected:
        raise ValueError(
            "Codex built-in packaging requires real external/generated model sources, not local placeholder "
            "or renderer outputs. Rejected source path(s): "
            + ", ".join(rejected)
        )


def write_blocked_status(carousel_dir: Path, reason: str) -> dict[str, Any]:
    return write_generation_state(
        carousel_dir,
        status=GenerationStatus.BLOCKED,
        backend=BACKEND,
        generation_mode=GENERATION_MODE,
        slide_count=infer_slide_count(carousel_dir),
        reason=reason,
    )


def infer_slide_count(carousel_dir: Path) -> int:
    for filename in ("slides.json", "prompt-pack.json"):
        path = carousel_dir / filename
        if not path.exists():
            continue
        try:
            payload = load_json(path)
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, list):
            return len(payload)
        slides = payload.get("slides")
        if isinstance(slides, list):
            return len(slides)
    return 0


def proof_slide_from_gate(proof_gate: str | None, slides: list[dict[str, Any]]) -> int:
    if proof_gate:
        match = re.search(r"\bslide\s+0*(\d+)\b", proof_gate, flags=re.IGNORECASE)
        if match:
            requested = int(match.group(1))
            if any(int(slide.get("slide", 0) or 0) == requested for slide in slides):
                return requested
    if slides:
        return int(slides[min(3, len(slides) - 1)].get("slide", 1))
    return 1


def write_handoff_blocker(carousel_dir: Path, result: dict[str, Any], proof_gate: str | None = None) -> None:
    slides = result.get("slides", [])
    requested_formats = result.get("requested_formats") or list(NATIVE_OUTPUT_CONTRACT["formats"])
    proof_slide = result.get("requested_proof_slide") or proof_slide_from_gate(proof_gate, slides)
    slide_count = int(result.get("slide_count") or len(slides))
    proof_copy = ""
    proof_generator_prompt = ""
    for slide in slides:
        if int(slide.get("slide", 0) or 0) == proof_slide:
            proof_copy = str(slide.get("copy", ""))
            generator_prompt_files = slide.get("generator_prompt_files") or {}
            for output_format in requested_formats:
                if generator_prompt_files.get(output_format):
                    proof_generator_prompt = str(generator_prompt_files[output_format])
                    break
            if not proof_generator_prompt and generator_prompt_files:
                proof_generator_prompt = str(next(iter(generator_prompt_files.values())))
            break
    prompt_handoff_lines = []
    for output_format in requested_formats:
        output_spec = NATIVE_OUTPUT_FORMATS[output_format]
        prompt_path = carousel_dir / "codex-image-prompts" / format_prompt_dir_name(output_format)
        prompt_handoff_lines.append(f"- {output_spec['label']} prompts: `{prompt_path}`")
    blocker = [
        "# Image Generation Blocker",
        "",
        "status: HANDOFF_READY_IMAGES_PENDING",
        "",
        "No final PNGs were generated by this step.",
        "",
        "This package is ready for Codex built-in image generation, but the CLI can only",
        "prepare prompt files and provenance expectations. It cannot call the interactive",
        "built-in image generator or produce identity-referenced final artwork by itself.",
        "",
        "Prompt handoff:",
        "",
        *prompt_handoff_lines,
        f"- Paste-ready generator prompts: `.prompt.txt` files beside each `.md` handoff file.",
        "",
        "Final images still required:",
        "",
        f"- `final/slide-01.png` through `slide-{slide_count:02d}.png`",
        f"- `final-reels-stories/slide-01.png` through `slide-{slide_count:02d}.png`",
        "",
        "Rules:",
        "",
        "- generate separate native 4:5 and native 9:16 images;",
        "- do not derive one aspect ratio from the other;",
        "- use identity references as actual image inputs;",
        "- preserve exact slide copy and `@a.storyof.two` inside the generated image;",
        "- package generated sources with `scripts/package_generated_carousel.py`.",
    ]
    if proof_copy:
        blocker.extend(
            [
                "",
                "Proof-first recommendation:",
                "",
                f"- slide {proof_slide:02d}: `{proof_copy}`",
            ]
        )
        if proof_generator_prompt:
            blocker.append(f"- paste only this proof prompt after attaching references: `{proof_generator_prompt}`")
    (carousel_dir / "image-generation-blocker.md").write_text("\n".join(blocker) + "\n", encoding="utf-8")


def requested_native_output_formats(formats: list[str] | None) -> list[str]:
    contract_formats = list(NATIVE_OUTPUT_CONTRACT["formats"])
    if formats is None:
        return contract_formats
    unsupported = sorted(set(formats) - set(contract_formats))
    if unsupported:
        raise ValueError("Unsupported Codex built-in output format(s): " + ", ".join(unsupported))
    if not formats:
        raise ValueError("At least one Codex built-in output format is required.")
    requested = set(formats)
    return [output_format for output_format in contract_formats if output_format in requested]


def expected_file_for_format(carousel_dir: Path, output_format: str, number: int) -> Path:
    output_folder = "final" if output_format == INSTAGRAM_POST_FORMAT else "final-reels-stories"
    return carousel_dir / output_folder / f"slide-{number:02d}.png"


def clean_packaged_output_files(carousel_dir: Path, slide_numbers: list[int]) -> None:
    for folder_name in ["final", "final-reels-stories"]:
        folder = carousel_dir / folder_name
        folder.mkdir(parents=True, exist_ok=True)
        for path in folder.glob("slide-*.png"):
            path.unlink()

    source_dir = carousel_dir / "final" / "model-native-source"
    source_dir.mkdir(parents=True, exist_ok=True)
    for number in slide_numbers:
        for prefix in ["instagram-post", "reels-stories"]:
            source_path = source_dir / f"{prefix}-slide-{number:02d}.png"
            if source_path.exists():
                source_path.unlink()


def format_prompt_dir_name(output_format: str) -> str:
    return "instagram-post" if output_format == INSTAGRAM_POST_FORMAT else "reels-stories"


def image_dimensions(image_bytes: bytes) -> dict[str, Any]:
    source = decode_png(image_bytes)
    source_height, source_width = source.shape[:2]
    return {
        "width": source_width,
        "height": source_height,
        "aspect": round(source_width / source_height, 4),
    }


def normalize_for_upload(image_bytes: bytes, width: int, height: int) -> tuple[bytes, dict[str, Any], str, str | None]:
    dimensions = image_dimensions(image_bytes)
    try:
        return (
            normalize_native_output(image_bytes, width, height),
            dimensions,
            "resized same-aspect generated source to upload size",
            None,
        )
    except RuntimeError as error:
        return (
            contain_on_paper(image_bytes, width, height),
            dimensions,
            "contained on warm paper to preserve full generated artwork",
            str(error),
        )


def infer_workspace_root_from_carousel_dir(carousel_dir: Path) -> Path:
    resolved = carousel_dir.expanduser().resolve()
    for candidate in [resolved, *resolved.parents]:
        if (candidate / "AGENTS.md").exists() or (candidate / "config" / "carousel_style_contract.json").exists():
            return candidate

    for parent in resolved.parents:
        if parent.name == "out":
            return parent.parent
        if parent.name == "carousels" and parent.parent.name == "output":
            return parent.parent.parent

    if resolved.parent != resolved:
        return resolved.parent
    return resolved


def prompt_file_text(
    *,
    carousel_dir: Path,
    slide_prompt: dict[str, Any],
    output_format: str,
    generator_prompt_path: Path,
    dossier_paths: list[Path],
    identity_dossier_path: str | None,
    identity_preflight_path: str | None,
    identity_paths: list[Path],
    source_paths: list[Path],
    style_paths: list[Path],
) -> str:
    number = int(slide_prompt["slide"])
    text = slide_prompt["text"]
    output_spec = NATIVE_OUTPUT_FORMATS[output_format]
    output_folder = "final" if output_format == INSTAGRAM_POST_FORMAT else "final-reels-stories"
    expected_file = carousel_dir / output_folder / f"slide-{number:02d}.png"
    generated_source = (
        carousel_dir
        / "final"
        / "model-native-source"
        / f"{'instagram-post' if output_format == INSTAGRAM_POST_FORMAT else 'reels-stories'}-slide-{number:02d}.png"
    )
    lines = [
        f"# Codex Built-In Image Prompt - Slide {number:02d} - {output_spec['label']}",
        "",
        "Use the Codex built-in image generator. Do not use external API keys or external image API clients.",
        "",
        "## How To Use This File",
        "",
        "- This markdown file is the Codex handoff/checklist, not the exact text to paste into the image model.",
        f"- Attach/view the image references below, then paste only `{generator_prompt_path}` into the image generator.",
        "- After generation, package the returned image with `scripts/package_generated_carousel.py` or the proof-specific workflow.",
        "",
        "## Native Output Contract",
        "",
        f"- Native output format: {output_spec['label']}",
        f"- Required aspect ratio: {output_spec['aspect_ratio']}",
        f"- Required final file: `{expected_file}`",
        f"- {NATIVE_OUTPUT_CONTRACT['rule']}",
        "- Generate this format as its own artwork. Do not create it by resizing another generated slide.",
        "",
        "## Hard Gate",
        "",
        "- Before any slide generation, read `identity-generation-preflight.md` and load/view `identity-face-contact-sheet.jpg`.",
        "- Preserve the carousel story-director spine embedded in `prompt-pack.json`: hook, setup, proof, bridge, active Zuv role, earned ending, and send/save reason.",
        "- Before calling image generation, load/view every identity reference listed below so they are actual image inputs in the Codex context.",
        "- Use the selected identity images as face, hair, expression, body proportion, posture, and relationship-energy references.",
        "- Do not accept generic Aachu/Zuv faces.",
        "- Keep the exact slide copy and tiny `@a.storyof.two` brandmark inside the generated image.",
        "",
        "## Identity Dossier",
        "",
        f"- Dossier: {identity_dossier_path or 'missing'}",
        f"- Preflight: {identity_preflight_path or 'missing'}",
        "",
        "## Actual Image Inputs",
        "",
        "Identity dossier references:",
        *[f"- {path}" for path in dossier_paths],
        "",
        "Identity references:",
        *[f"- {path}" for path in identity_paths],
        "",
        "Story/source references:",
        *[f"- {path}" for path in source_paths],
        "",
        "Style references:",
        *[f"- {path}" for path in style_paths],
        "",
        "## Exact Slide Copy",
        "",
        text,
        "",
        "## Prompt",
        "",
        prompt_for_native_format(slide_prompt["prompt"], output_format),
        "",
        "## Expected Output",
        "",
        f"- Save packaged final to `{expected_file}`.",
        f"- Source provenance should point to the Codex generated image copied into `{generated_source}`.",
    ]
    return "\n".join(lines) + "\n"


def prepare_codex_builtin_image_generation(
    carousel_dir: Path,
    *,
    proof_slide: int | None = None,
    formats: list[str] | None = None,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    prompt_dir = carousel_dir / "codex-image-prompts"
    if prompt_dir.exists():
        shutil.rmtree(prompt_dir)
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    slides = prompt_pack.get("slides", [])
    if not slides:
        raise ValueError("prompt-pack.json does not include slide prompts.")
    total_prompt_pack_slide_count = len(slides)
    output_formats = requested_native_output_formats(formats)
    if proof_slide is not None:
        slides = [slide for slide in slides if int(slide.get("slide", 0) or 0) == proof_slide]
        if not slides:
            raise ValueError(f"proof_slide {proof_slide} is not present in prompt-pack.json.")

    visual_quality_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_quality_reason:
        return write_blocked_status(carousel_dir, visual_quality_reason)

    identity_reason = identity_consistency_gate_reason(carousel_dir)
    if identity_reason:
        return write_blocked_status(carousel_dir, identity_reason)

    style_consistency_reason = house_style_consistency_gate_reason(prompt_pack)
    if style_consistency_reason:
        return write_blocked_status(carousel_dir, style_consistency_reason)

    dossier_paths = existing_paths(prompt_pack.get("identity_dossier_reference_images", []))
    identity_paths = existing_paths(prompt_pack.get("identity_reference_images", []))
    if not dossier_paths:
        return write_blocked_status(
            carousel_dir,
            "Codex built-in image generation requires identity-face-contact-sheet.jpg as an actual image input.",
        )
    if not identity_paths:
        return write_blocked_status(
            carousel_dir,
            "Codex built-in image generation requires selected identity images as actual image inputs.",
        )

    style_paths = [
        path
        for path in existing_reference_paths({"style_reference_images": prompt_pack.get("style_reference_images", [])})
        if path not in identity_paths
    ]
    prompt_dir.mkdir(parents=True, exist_ok=True)

    records = []
    slide_plans = load_json(carousel_dir / "slides.json")
    for slide_prompt in slides:
        number = int(slide_prompt["slide"])
        slide_plan = next(
            (
                item
                for item in slide_plans
                if int(item.get("slide", 0) or 0) == number
            ),
            {},
        )
        source_paths = slide_source_paths(slide_plan)
        prompt_files = {}
        for output_format in output_formats:
            format_dir = format_prompt_dir_name(output_format)
            prompt_files[output_format] = prompt_dir / format_dir / f"slide-{number:02d}.md"
        for output_format, prompt_path in prompt_files.items():
            prompt_path.parent.mkdir(parents=True, exist_ok=True)
            generator_prompt_path = prompt_path.with_suffix(".prompt.txt")
            generator_prompt_path.write_text(
                generator_prompt_text(slide_prompt, output_format),
                encoding="utf-8",
            )
            prompt_path.write_text(
                prompt_file_text(
                    carousel_dir=carousel_dir,
                    slide_prompt=slide_prompt,
                    output_format=output_format,
                    generator_prompt_path=generator_prompt_path,
                    dossier_paths=dossier_paths,
                    identity_dossier_path=prompt_pack.get("identity_dossier_path"),
                    identity_preflight_path=prompt_pack.get("identity_generation_preflight_path"),
                    identity_paths=identity_paths,
                    source_paths=source_paths,
                    style_paths=style_paths,
                ),
                encoding="utf-8",
            )
        first_output_format = output_formats[0]
        first_prompt_path = prompt_files[first_output_format]
        records.append(
            {
                "slide": number,
                "copy": slide_prompt["text"],
                "status": "awaiting_codex_builtin_image",
                "generation_mode": GENERATION_MODE,
                "backend": BACKEND,
                "prompt_file": str(first_prompt_path),
                "prompt_files": {key: str(path) for key, path in prompt_files.items()},
                "generator_prompt_files": {
                    key: str(path.with_suffix(".prompt.txt")) for key, path in prompt_files.items()
                },
                "expected_file": str(expected_file_for_format(carousel_dir, first_output_format, number)),
                "expected_files": {
                    output_format: str(expected_file_for_format(carousel_dir, output_format, number))
                    for output_format in output_formats
                },
                "identity_dossier_reference_images": [str(path) for path in dossier_paths],
                "identity_reference_images": [str(path) for path in identity_paths],
                "story_reference_images": [str(path) for path in source_paths],
                "style_reference_images": [str(path) for path in style_paths],
            }
        )

    result = write_generation_state(
        carousel_dir,
        status=GenerationStatus.HANDOFF_READY,
        backend=BACKEND,
        generation_mode=GENERATION_MODE,
        slide_count=total_prompt_pack_slide_count,
        reason="Prompt files are ready; final PNGs still require Codex built-in image generation.",
        slides=records,
        extra={
            "proof_gate": prompt_pack.get("proof_gate"),
            "requested_proof_slide": proof_slide,
            "requested_formats": output_formats,
            "native_output_contract": NATIVE_OUTPUT_CONTRACT,
            "prompt_dir": str(prompt_dir),
            "identity_reference_requirement": (
                "Load/view identity-face-contact-sheet.jpg and selected identity images before every "
                "Codex image generation call; the final art must preserve Aachu/Zuv face structure."
            ),
        },
    )
    write_handoff_blocker(carousel_dir, result, prompt_pack.get("proof_gate"))
    return result


def package_codex_builtin_outputs(
    carousel_dir: Path,
    *,
    generated_paths: list[str | Path] | None = None,
    generated_paths_by_format: dict[str, list[str | Path]] | None = None,
    refresh_quality: bool = False,
) -> dict[str, Any]:
    carousel_dir = carousel_dir.expanduser()
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    slides = prompt_pack.get("slides", [])
    if generated_paths is not None:
        raise ValueError(
            "Codex built-in packaging requires generated_paths_by_format with both "
            "instagram_post and reels_stories outputs."
        )
    if not generated_paths_by_format:
        raise ValueError("generated_paths_by_format is required.")
    expected_formats = set(NATIVE_OUTPUT_CONTRACT["formats"])
    supplied_formats = set(generated_paths_by_format)
    if supplied_formats != expected_formats:
        raise ValueError(
            "generated_paths_by_format must contain exactly: "
            + ", ".join(NATIVE_OUTPUT_CONTRACT["formats"])
        )
    for format_key, paths in generated_paths_by_format.items():
        if len(paths) != len(slides):
            raise ValueError(f"Expected {len(slides)} {format_key} image paths, got {len(paths)}.")
    reject_non_codex_builtin_sources(carousel_dir, generated_paths_by_format)

    visual_quality_reason = visual_plan_quality_gate_reason(carousel_dir)
    if visual_quality_reason:
        return write_blocked_status(carousel_dir, visual_quality_reason)

    identity_reason = identity_consistency_gate_reason(carousel_dir)
    if identity_reason:
        return write_blocked_status(carousel_dir, identity_reason)

    slide_numbers = [int(slide.get("slide", 0) or 0) for slide in slides]
    clean_packaged_output_files(carousel_dir, slide_numbers)

    final_dir = carousel_dir / "final"
    source_dir = final_dir / "model-native-source"
    reels_stories_dir = carousel_dir / "final-reels-stories"
    for folder in [final_dir, source_dir, reels_stories_dir]:
        folder.mkdir(parents=True, exist_ok=True)

    prompt_refs = [str(path) for path in existing_reference_paths(prompt_pack)]
    slide_plans = load_json(carousel_dir / "slides.json")
    records = []
    normalization_notes: list[str] = []
    for index, slide_prompt in enumerate(slides):
        number = int(slide_prompt["slide"])
        instagram_source_path = Path(generated_paths_by_format["instagram_post"][index]).expanduser()
        reels_stories_source_path = Path(generated_paths_by_format["reels_stories"][index]).expanduser()
        if not instagram_source_path.exists():
            raise FileNotFoundError(f"Missing Codex generated image: {instagram_source_path}")
        if not reels_stories_source_path.exists():
            raise FileNotFoundError(f"Missing Codex generated image: {reels_stories_source_path}")
        instagram_bytes = instagram_source_path.read_bytes()
        reels_stories_bytes = reels_stories_source_path.read_bytes()
        instagram_source_target = source_dir / f"instagram-post-slide-{number:02d}.png"
        shutil.copyfile(instagram_source_path, instagram_source_target)
        reels_stories_source_target = source_dir / f"reels-stories-slide-{number:02d}.png"
        shutil.copyfile(reels_stories_source_path, reels_stories_source_target)
        target = final_dir / f"slide-{number:02d}.png"
        instagram_output, instagram_dimensions, instagram_normalization, instagram_warning = normalize_for_upload(
            instagram_bytes, *FINAL_UPLOAD_SIZE
        )
        target.write_bytes(instagram_output)
        reels_stories_target = reels_stories_dir / f"slide-{number:02d}.png"
        (
            reels_stories_output,
            reels_stories_dimensions,
            reels_stories_normalization,
            reels_stories_warning,
        ) = normalize_for_upload(reels_stories_bytes, *REELS_STORIES_SIZE)
        reels_stories_target.write_bytes(reels_stories_output)
        if instagram_warning:
            normalization_notes.append(f"Slide {number} Instagram post: {instagram_warning}")
        if reels_stories_warning:
            normalization_notes.append(f"Slide {number} Reels/Stories: {reels_stories_warning}")
        slide_plan = next(
            (
                item
                for item in slide_plans
                if int(item.get("slide", 0) or 0) == number
            ),
            {},
        )
        reference_images = [
            *prompt_refs,
            *[str(path) for path in slide_source_paths(slide_plan)],
        ]
        records.append(
            {
                "slide": number,
                "copy": slide_prompt["text"],
                "generation_mode": GENERATION_MODE,
                "backend": BACKEND,
                "prompt": slide_prompt["prompt"],
                "reference_images": reference_images,
                "source": str(instagram_source_target),
                "codex_generated_source": str(instagram_source_path),
                "file": str(target),
                "reels_stories_source": str(reels_stories_source_target),
                "reels_stories_file": str(reels_stories_target),
                "native_outputs": {
                    INSTAGRAM_POST_FORMAT: {
                        "label": NATIVE_OUTPUT_FORMATS[INSTAGRAM_POST_FORMAT]["label"],
                        "aspect_ratio": NATIVE_OUTPUT_FORMATS[INSTAGRAM_POST_FORMAT]["aspect_ratio"],
                        "source": str(instagram_source_target),
                        "codex_generated_source": str(instagram_source_path),
                        "source_dimensions": instagram_dimensions,
                        "file": str(target),
                        "upload_size": f"{FINAL_UPLOAD_SIZE[0]}x{FINAL_UPLOAD_SIZE[1]}",
                        "normalization": instagram_normalization,
                    },
                    REELS_STORIES_FORMAT: {
                        "label": NATIVE_OUTPUT_FORMATS[REELS_STORIES_FORMAT]["label"],
                        "aspect_ratio": NATIVE_OUTPUT_FORMATS[REELS_STORIES_FORMAT]["aspect_ratio"],
                        "source": str(reels_stories_source_target),
                        "codex_generated_source": str(reels_stories_source_path),
                        "source_dimensions": reels_stories_dimensions,
                        "file": str(reels_stories_target),
                        "upload_size": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
                        "normalization": reels_stories_normalization,
                    },
                },
            }
        )

    normalization_text = (
        "Each surface is generated from its own source. Final files are upload-size normalizations; "
        "non-target source aspects are contained on warm paper to preserve the complete generated artwork."
        if normalization_notes
        else "Each surface is generated from its own native source; final files are same-aspect upload-size normalizations only."
    )
    generation_extra = {
        "native_output_contract": NATIVE_OUTPUT_CONTRACT,
        "instagram_upload_size": f"{FINAL_UPLOAD_SIZE[0]}x{FINAL_UPLOAD_SIZE[1]}",
        "reels_stories_size": f"{REELS_STORIES_SIZE[0]}x{REELS_STORIES_SIZE[1]}",
        "normalization": normalization_text,
        "notes": normalization_notes,
    }
    result = write_generation_state(
        carousel_dir,
        status=GenerationStatus.GENERATED,
        backend=BACKEND,
        generation_mode=GENERATION_MODE,
        slide_count=len(slides),
        slides=records,
        extra=generation_extra,
    )
    if refresh_quality:
        from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts

        manifest = load_json(carousel_dir / "manifest.json")
        package = {
            "concept": load_json(carousel_dir / "concept.json"),
            "slides": load_json(carousel_dir / "slides.json"),
            "visual_plan_quality": load_json(carousel_dir / "visual-plan-quality.json"),
            "prompt_pack": prompt_pack,
            "copy": load_json(carousel_dir / "copy.json"),
        }
        final_audit = write_quality_artifacts(
            QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date.fromisoformat(manifest["date"]),
                out_dir=carousel_dir,
                image_paths=[
                    Path(item["path"])
                    for item in manifest.get("reference_images", [])
                    if isinstance(item, dict) and item.get("path")
                ],
                slide_count=len(slides),
                package=package,
                manifest=manifest,
                render_result=result,
                workspace_root=infer_workspace_root_from_carousel_dir(carousel_dir),
            )
        )
        audit_extra = {
            **generation_extra,
            "final_audit_status": final_audit["status"],
            "final_audit_pass": bool(final_audit["pass"]),
            "final_audit_path": str(carousel_dir / "final-audit.json"),
        }
        if not final_audit["pass"]:
            result = write_generation_state(
                carousel_dir,
                status=GenerationStatus.GENERATED_AUDIT_FAILED,
                backend=BACKEND,
                generation_mode=GENERATION_MODE,
                slide_count=len(slides),
                reason="Generated files were packaged, but final-audit.json did not pass.",
                slides=records,
                extra=audit_extra,
            )
        else:
            result = write_generation_state(
                carousel_dir,
                status=GenerationStatus.GENERATED,
                backend=BACKEND,
                generation_mode=GENERATION_MODE,
                slide_count=len(slides),
                slides=records,
                extra=audit_extra,
            )
    return result
