"""Small shared contract for the @a.storyof.two carousel hot path.

The old module ran a sequential eleven-agent Anthropic room before it could
write a package.  That duplicated Codex-native creation, buried the creator's
idea under scores and debates, and made a production command depend on an API
key.  Carousel creation now has one implementation: ``create_codex_native_carousel``.

This module keeps the stable parsing and manifest helpers used by the CLI and
tests.  ``create_illustration_carousel`` remains as a compatibility alias; it
does not start a second orchestration system.
"""

from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_format_contract import (
    build_format_contract,
    format_spec,
    normalize_requested_formats,
)


BASE_DIR = Path(__file__).resolve().parents[2]
OUTPUT_ROOT = BASE_DIR / "output" / "carousels"
MIN_STORY_SLIDES = 4
MAX_STORY_SLIDES = 11
DEFAULT_SLIDE_COUNT = 5

# This is the package contract, not a record of internal deliberation.  Proof
# and final artifacts appear only when those stages have actually completed.
ARTIFACT_CONTRACT = {
    "creative_context": "creative-context.json",
    "format_contract": "format-contract.json",
    "slides": "slides.json",
    "prompt_pack": "prompt-pack.json",
    "compiled_prompts": ".internal/compiled-prompts/",
    "proof_image": ".internal/visual-quarantine/",
    "proof_qa": "proof-qa.json",
    "final_images": "final-images.json",
    "visual_qa": "visual-qa.json",
    "final_audit": "final-audit.json",
}

# Compatibility names for callers that imported the legacy orchestration
# constants.  Empty means no default agent room; the explicit idea-loop system
# remains registered separately in config/skill-systems.json.
SPECIALIST_AGENTS: tuple[()] = ()
ORCHESTRATOR_SKILLS: tuple[str, ...] = (
    "creator-skill-stack",
    "carousel-jam-runtime-context",
    "illustration-carousel-framework",
)


class CarouselPipelineError(RuntimeError):
    """Raised when a carousel package violates the small public contract."""


def slugify_title(value: str, fallback: str = "illustration-carousel") -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return re.sub(r"-{2,}", "-", slug).strip("-") or fallback


def validate_slide_count(slide_count: int) -> int:
    if not MIN_STORY_SLIDES <= slide_count <= MAX_STORY_SLIDES:
        raise ValueError(
            f"Slide count must be between {MIN_STORY_SLIDES} and "
            f"{MAX_STORY_SLIDES} for /story."
        )
    return slide_count


def parse_story_command(command: str) -> dict[str, Any]:
    text = command.strip()
    if not text.startswith("/story"):
        raise ValueError("Story command must start with /story.")

    title: str | None = None
    slide_count = DEFAULT_SLIDE_COUNT
    story_lines: list[str] = []
    for line in text[len("/story") :].strip().splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        key, separator, value = stripped.partition(":")
        normalized = key.strip().lower().replace("-", "_").replace(" ", "_")
        if separator and normalized in {"title", "working_title"}:
            title = value.strip() or None
        elif separator and normalized in {"slides", "slide_count"}:
            slide_count = validate_slide_count(int(value.strip()))
        else:
            story_lines.append(stripped)

    story = "\n".join(story_lines).strip()
    if not story:
        raise ValueError("Story command must include the story text.")
    return {"title": title, "story": story, "slide_count": slide_count}


def normalize_image_paths(image_paths: list[str | Path]) -> list[Path]:
    normalized = [Path(path).expanduser() for path in image_paths]
    missing = [str(path) for path in normalized if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing reference image(s): " + ", ".join(missing))
    return normalized


def load_context() -> str:
    """Render the canonical Agentic OS context without embedding agent prompts."""
    from pipeline.agentic.context_loader import assemble_context_pack, render_context_pack

    return render_context_pack(assemble_context_pack(BASE_DIR, profile="a-story-of-two"))


def build_manifest(
    *,
    title: str,
    slug: str,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path] | None = None,
    today: date | None = None,
    requested_formats: list[str] | tuple[str, ...] | None = None,
) -> dict[str, Any]:
    """Build the small public manifest used by compatibility callers."""
    format_contract = build_format_contract(
        requested_formats,
        source=("creator_request" if requested_formats is not None else "instagram_post_default"),
    )
    locked = normalize_requested_formats(format_contract["requested_formats"])
    return {
        "date": str(today or date.today()),
        "slug": slug,
        "title": title,
        "channel": "@a.storyof.two",
        "pipeline": "carousel_hot_path_v2",
        "status": "draft",
        "source_story": story,
        "requested_formats": list(locked),
        "format_contract": format_contract,
        "format": {
            "platform": "instagram",
            "type": "carousel",
            "native_outputs": {
                output_format: {
                    "aspect_ratio": format_spec(output_format)["aspect_ratio"],
                    "size": "x".join(
                        str(value) for value in format_spec(output_format)["target_size"]
                    ),
                    "directory": f"{format_spec(output_format)['folder']}/",
                }
                for output_format in locked
            },
        },
        "reference_images": [
            {"path": str(path), "role": "story reference"} for path in image_paths
        ],
        "identity_references": [
            {"path": str(path), "role": "Aachu/Zuv identity reference"}
            for path in (identity_image_paths or [])
        ],
        "artifacts": ARTIFACT_CONTRACT,
    }


def extract_json_object(text: str) -> dict[str, Any]:
    """Retained for old integrations that hand a package through JSON text."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidate = fenced.group(1) if fenced else text.strip()
    if not candidate.startswith("{"):
        start, end = candidate.find("{"), candidate.rfind("}")
        if start == -1 or end <= start:
            raise CarouselPipelineError("Response did not contain a JSON object.")
        candidate = candidate[start : end + 1]
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise CarouselPipelineError(f"Response JSON was invalid: {exc}") from exc
    if not isinstance(parsed, dict):
        raise CarouselPipelineError("Response JSON must be an object.")
    return parsed


def validate_package(package: dict[str, Any]) -> None:
    required = {"creative_context", "slides", "prompt_pack"}
    missing = sorted(required - set(package))
    if missing:
        raise CarouselPipelineError("Package missing keys: " + ", ".join(missing))
    slides = package["slides"]
    if not isinstance(slides, list) or not slides:
        raise CarouselPipelineError("Package must include at least one slide.")
    prompt_slides = package["prompt_pack"].get("slides", [])
    if len(prompt_slides) != len(slides):
        raise CarouselPipelineError("Prompt-pack slide count must match slides.json.")


def create_illustration_carousel(**options: Any) -> Path:
    """Compatibility alias for the single Codex-native implementation."""
    from pipeline.stages.codex_native_carousel import create_codex_native_carousel

    return create_codex_native_carousel(**options)


def interactive_mode() -> dict[str, Any]:
    print("\n=== Carousel Creator - @a.storyof.two ===\n")
    title = input("Working title (optional): ").strip() or None
    story = input("Story (required): ").strip()
    if not story:
        raise SystemExit("Story is required.")
    raw_images = input("Story-reference image paths (comma-separated): ").strip()
    images = [item.strip() for item in raw_images.split(",") if item.strip()]
    raw_identity = input("Aachu/Zuv identity images (comma-separated, required for art): ").strip()
    identity = [item.strip() for item in raw_identity.split(",") if item.strip()]
    raw_count = input(f"Slide count [{DEFAULT_SLIDE_COUNT}]: ").strip()
    style_brief = input("Style brief (optional): ").strip() or None
    return {
        "title": title,
        "story": story,
        "image_paths": images,
        "identity_image_paths": identity or None,
        "slide_count": validate_slide_count(int(raw_count)) if raw_count else DEFAULT_SLIDE_COUNT,
        "style_brief": style_brief,
    }


def _main() -> None:
    # The public entrypoint is scripts/create_illustration_carousel.py.  Keeping
    # this module executable avoids breaking old one-liners without restoring a
    # second workflow.
    options = interactive_mode()
    out_dir = create_illustration_carousel(**options, output_root=OUTPUT_ROOT)
    print(f"Carousel package saved -> {out_dir}")


if __name__ == "__main__":
    _main()
