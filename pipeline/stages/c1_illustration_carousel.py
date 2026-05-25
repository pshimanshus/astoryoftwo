"""
Illustrated carousel pipeline for @a.storyof.two.

Turns user-supplied photos plus a short story into a complete carousel package:
concept, slide arc, image-generation prompt pack, captions, review, and
approval checklist.

Usage:
    python -m pipeline.stages.c1_illustration_carousel --story "..." --image photo.jpg
    python scripts/create_illustration_carousel.py
    /story title: Optional title
    <story text>
"""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import re
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Any

import anthropic


BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "config" / "skills"
AGENTS_DIR = BASE_DIR / "agents"
OUTPUT_ROOT = BASE_DIR / "output" / "carousels"
VOICE_FILE = BASE_DIR / "config" / "voice.md"
WORKING_MEMORY = BASE_DIR / "memory" / "working.md"
MIN_STORY_SLIDES = 4
MAX_STORY_SLIDES = 10
DEFAULT_SLIDE_COUNT = 5
STORY_SELLING_MIN_SCORE = 28

RELATED_SKILL_REFERENCES = {
    "romance-story-selling-engine": [
        BASE_DIR / "config" / "references" / "story-selling-canon" / "source-policy.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "a-story-of-two-adaptation.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "concept-process-cards.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "rubric.md",
        BASE_DIR / "config" / "references" / "golden-viral-carousel-theme-reference.md",
    ],
}

ARTIFACT_CONTRACT = {
    "concept": "concept.json",
    "post_copy_visual_room": "post-copy-visual-room.json",
    "visual_debate": "visual-debate.json",
    "visual_plan_quality": "visual-plan-quality.json",
    "slides": "slides.json",
    "prompt_pack": "prompt-pack.json",
    "identity_dossier": "identity-dossier.json",
    "identity_generation_preflight": "identity-generation-preflight.md",
    "identity_face_contact_sheet": "identity-face-contact-sheet.jpg",
    "identity_consistency_review": "identity-consistency-review.json",
    "copy": "copy.json",
    "review": "review.json",
    "approval": "final-approval.md",
    "storyboard": "storyboard.md",
    "agent_reports": "agent-reports.md",
}

SPECIALIST_AGENTS = [
    (
        "carousel-story-director",
        [
            "carousel-story-director-persona",
            "golden-viral-carousel-theme",
            "romance-story-selling-engine",
            "hook-and-edit-framework",
            "instagram-algorithm-2026",
        ],
    ),
    (
        "carousel-story-miner",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
        ],
    ),
    (
        "carousel-arc-builder",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "hook-and-edit-framework",
        ],
    ),
    (
        "carousel-visual-director",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "indian-creator-intelligence",
        ],
    ),
    (
        "carousel-visual-evidence-planner",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "indian-creator-intelligence",
        ],
    ),
    (
        "carousel-romance-scene-planner",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "indian-creator-intelligence",
        ],
    ),
    (
        "carousel-visual-continuity-judge",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "indian-creator-intelligence",
        ],
    ),
    (
        "carousel-prompt-engineer",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
        ],
    ),
    (
        "carousel-copy-packager",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "instagram-algorithm-2026",
            "indian-creator-intelligence",
        ],
    ),
    (
        "carousel-post-copy-visual-room-orchestrator",
        [
            "illustration-carousel-framework",
            "continuous-carousel-agent-room",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
            "indian-creator-intelligence",
        ],
    ),
    (
        "carousel-reviewer",
        [
            "illustration-carousel-framework",
            "golden-viral-carousel-theme",
            "carousel-story-director-persona",
            "romance-story-selling-engine",
        ],
    ),
]

ORCHESTRATOR_AGENT = "illustration-carousel-orchestrator"
ORCHESTRATOR_SKILLS = [
    "illustration-carousel-framework",
    "continuous-carousel-agent-room",
    "golden-viral-carousel-theme",
    "carousel-story-director-persona",
    "romance-story-selling-engine",
    "indian-creator-intelligence",
]


class CarouselPipelineError(RuntimeError):
    """Raised when the carousel pipeline cannot produce a valid package."""


def slugify_title(value: str, fallback: str = "illustration-carousel") -> str:
    slug = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or fallback


def validate_slide_count(slide_count: int) -> int:
    if slide_count < MIN_STORY_SLIDES or slide_count > MAX_STORY_SLIDES:
        raise ValueError(
            f"Slide count must be between {MIN_STORY_SLIDES} and {MAX_STORY_SLIDES} for /story."
        )
    return slide_count


def parse_story_command(command: str) -> dict[str, Any]:
    """Parse a chat-style /story command into carousel options."""
    text = command.strip()
    if not text.startswith("/story"):
        raise ValueError("Story command must start with /story.")

    body = text[len("/story") :].strip()
    title = None
    slide_count = DEFAULT_SLIDE_COUNT
    story_lines: list[str] = []

    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        key, separator, value = stripped.partition(":")
        normalized_key = key.strip().lower().replace("-", "_").replace(" ", "_")
        if separator and normalized_key in {"title", "working_title"}:
            title = value.strip() or None
        elif separator and normalized_key in {"slides", "slide_count"}:
            slide_count = validate_slide_count(int(value.strip()))
        else:
            story_lines.append(stripped)

    story = "\n".join(story_lines).strip()
    if not story:
        raise ValueError("Story command must include the story text.")

    return {
        "title": title,
        "story": story,
        "slide_count": slide_count,
    }


def extract_json_object(text: str) -> dict[str, Any]:
    """Extract the first JSON object from an agent response."""
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL)
    candidate = fenced.group(1) if fenced else text.strip()

    if not candidate.startswith("{"):
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise CarouselPipelineError("Agent response did not contain a JSON object.")
        candidate = candidate[start : end + 1]

    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise CarouselPipelineError(f"Agent response JSON was invalid: {exc}") from exc

    if not isinstance(parsed, dict):
        raise CarouselPipelineError("Agent response JSON must be an object.")
    return parsed


def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    if path.exists():
        body = path.read_text(encoding="utf-8")
        reference_parts = []
        for reference_path in RELATED_SKILL_REFERENCES.get(name, []):
            if reference_path.exists():
                reference_parts.append(
                    f"# Required Reference: {reference_path.relative_to(BASE_DIR)}\n"
                    f"{reference_path.read_text(encoding='utf-8')}"
                )
        if reference_parts:
            return body + "\n\n---\n\n" + "\n\n---\n\n".join(reference_parts)
        return body
    return f"[Skill file not found: {name}]"


def load_agent(name: str) -> str:
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text(encoding="utf-8")
    return f"[Agent file not found: {name}]"


def load_context() -> str:
    parts = []
    if VOICE_FILE.exists():
        parts.append(f"# Voice Guide\n{VOICE_FILE.read_text(encoding='utf-8')}")
    if WORKING_MEMORY.exists():
        parts.append(f"# Working Memory\n{WORKING_MEMORY.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(parts)


def build_system_prompt(agent_name: str, skill_names: list[str]) -> str:
    agent_def = load_agent(agent_name)
    skills = "\n\n---\n\n".join(load_skill(name) for name in skill_names)
    context = load_context()

    return f"""You are a specialist illustrated-carousel agent for @a.storyof.two.
Follow the agent definition exactly. Be specific, visual, and non-generic.

# Agent Definition
{agent_def}

# Skill References
{skills}

# Channel Context
{context}
"""


def normalize_image_paths(image_paths: list[str | Path]) -> list[Path]:
    normalized = [Path(path).expanduser() for path in image_paths]
    missing = [str(path) for path in normalized if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing reference image(s): " + ", ".join(missing))
    return normalized


def image_content_block(path: Path) -> dict[str, Any]:
    media_type = mimetypes.guess_type(path.name)[0] or "image/jpeg"
    allowed = {"image/jpeg", "image/png", "image/gif", "image/webp"}
    if media_type not in allowed:
        raise CarouselPipelineError(f"Unsupported image type for {path}: {media_type}")

    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": encoded,
        },
    }


def build_brief_text(
    *,
    story: str,
    title: str | None,
    slide_count: int,
    style_brief: str | None,
    image_paths: list[Path],
    identity_image_paths: list[Path] | None = None,
    prior_outputs: dict[str, str] | None = None,
) -> str:
    lines = [
        f"Title: {title or '[choose the strongest title]'}",
        f"Story: {story}",
        f"Slide count: {slide_count}",
        f"Style brief: {style_brief or '[use the channel illustration framework]'}",
        "Reference images:",
    ]
    lines.extend(f"- {path}" for path in image_paths)
    if identity_image_paths:
        lines.append("")
        lines.append("Identity reference images for Aachu/Zuv face consistency:")
        lines.extend(f"- {path}" for path in identity_image_paths)

    if prior_outputs:
        lines.append("")
        lines.append("# Previous Specialist Outputs")
        for name, output in prior_outputs.items():
            lines.append(f"\n## {name}\n{output}")

    return "\n".join(lines)


def build_user_content(
    *,
    story: str,
    title: str | None,
    slide_count: int,
    style_brief: str | None,
    image_paths: list[Path],
    identity_image_paths: list[Path] | None = None,
    prior_outputs: dict[str, str] | None = None,
) -> list[dict[str, Any]]:
    content: list[dict[str, Any]] = []
    for path in identity_image_paths or []:
        content.append({"type": "text", "text": f"Identity reference image for Aachu/Zuv: {path.name}"})
        content.append(image_content_block(path))

    for path in image_paths:
        content.append({"type": "text", "text": f"Reference image: {path.name}"})
        content.append(image_content_block(path))

    content.append(
        {
            "type": "text",
            "text": build_brief_text(
                story=story,
                title=title,
                slide_count=slide_count,
                style_brief=style_brief,
                image_paths=image_paths,
                identity_image_paths=identity_image_paths,
                prior_outputs=prior_outputs,
            ),
        }
    )
    return content


def run_agent(
    client: anthropic.Anthropic,
    *,
    agent_name: str,
    skill_names: list[str],
    story: str,
    title: str | None,
    slide_count: int,
    style_brief: str | None,
    image_paths: list[Path],
    identity_image_paths: list[Path] | None = None,
    prior_outputs: dict[str, str] | None = None,
    model: str = "claude-sonnet-4-6",
    max_tokens: int = 2500,
) -> str:
    system = build_system_prompt(agent_name, skill_names)
    content = build_user_content(
        story=story,
        title=title,
        slide_count=slide_count,
        style_brief=style_brief,
        image_paths=image_paths,
        identity_image_paths=identity_image_paths,
        prior_outputs=prior_outputs,
    )

    message = client.messages.create(
        model=model,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": content}],
    )
    return message.content[0].text


def build_manifest(
    *,
    title: str,
    slug: str,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path] | None = None,
    today: date | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    return {
        "date": str(today),
        "slug": slug,
        "title": title,
        "channel": "@a.storyof.two",
        "pipeline": "C-layer illustrated carousel",
        "status": "draft_for_human_review",
        "source_story": story,
        "format": {
            "platform": "instagram",
            "type": "carousel",
            "native_outputs": {
                "instagram_post": {
                    "aspect_ratio": "4:5",
                    "size": "1080x1350",
                    "directory": "final/",
                },
                "reels_stories": {
                    "aspect_ratio": "9:16",
                    "size": "1080x1920",
                    "directory": "final-reels-stories/",
                },
            },
            "native_output_rule": "Generate both formats separately. Never resize, crop, pad, or extend one output into the other.",
        },
        "reference_images": [
            {"path": str(path), "role": "user supplied story reference"}
            for path in image_paths
        ],
        "identity_references": [
            {"path": str(path), "role": "Aachu/Zuv face consistency reference"}
            for path in (identity_image_paths or [])
        ],
        "artifacts": ARTIFACT_CONTRACT,
    }


def validate_package(package: dict[str, Any]) -> None:
    required = {
        "concept",
        "post_copy_visual_room",
        "visual_debate",
        "slides",
        "prompt_pack",
        "copy",
        "review",
    }
    missing = sorted(required - set(package))
    if missing:
        raise CarouselPipelineError("Orchestrator package missing keys: " + ", ".join(missing))

    slides = package["slides"]
    if not isinstance(slides, list) or not slides:
        raise CarouselPipelineError("Orchestrator package must include at least one slide.")

    prompt_slides = package["prompt_pack"].get("slides", [])
    if len(prompt_slides) != len(slides):
        raise CarouselPipelineError("Prompt pack slide count must match slides.json.")

    if not isinstance(package["review"], dict):
        raise CarouselPipelineError("Orchestrator review must be an object.")
    validate_story_selling_review(package["review"])


def validate_story_selling_review(review: dict[str, Any]) -> None:
    story_selling_score = review.get("story_selling_score")
    if not isinstance(story_selling_score, dict):
        raise CarouselPipelineError("Review must include story_selling_score.")

    total = story_selling_score.get("total")
    try:
        total_score = float(total)
    except (TypeError, ValueError) as exc:
        raise CarouselPipelineError("Review story_selling_score.total must be numeric.") from exc
    if total_score < STORY_SELLING_MIN_SCORE:
        raise CarouselPipelineError(
            f"Story-Selling score must be at least {STORY_SELLING_MIN_SCORE}/30."
        )

    hard_fails = review.get("story_selling_hard_fails", [])
    if not isinstance(hard_fails, list):
        raise CarouselPipelineError("Review story_selling_hard_fails must be a list.")
    if hard_fails:
        raise CarouselPipelineError("Story-Selling hard fails must be repaired before packaging.")

    gate = review.get("story_selling_gate")
    if not isinstance(gate, dict):
        raise CarouselPipelineError("Review must include story_selling_gate.")
    if gate.get("status") not in {"PASS", "PASS_WITH_NOTES", "GO"}:
        raise CarouselPipelineError("Review story_selling_gate.status must pass before packaging.")
    if not gate.get("selected_concept_process_card"):
        raise CarouselPipelineError("Review must record the selected Story-Selling concept-process card.")

    story_director_gate = review.get("story_director_gate")
    if story_director_gate is not None:
        if not isinstance(story_director_gate, dict):
            raise CarouselPipelineError("Review story_director_gate must be an object when present.")
        if story_director_gate.get("status") not in {"PASS", "GO", "PASS_WITH_NOTES"}:
            raise CarouselPipelineError("Review story_director_gate.status must pass before packaging.")


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_storyboard(out_dir: Path, package: dict[str, Any]) -> None:
    concept = package["concept"]
    copy = package["copy"]
    lines = [
        f"# {concept.get('title', 'Illustrated Carousel')}",
        "",
        concept.get("human_truth", ""),
        "",
        "## Emotional Arc",
        "",
        concept.get("emotional_arc", ""),
        "",
        "## Slide Flow",
        "",
    ]

    for slide in package["slides"]:
        lines.append(
            f"- {slide.get('slide')}: {slide.get('copy')} - {slide.get('visual')}"
        )

    lines.extend(
        [
            "",
            "## Recommended Caption",
            "",
            copy.get("caption_recommended", ""),
            "",
            "## Generation Notes",
            "",
            "- Use `prompt-pack.json` for image generation.",
            "- Review `final-approval.md` before posting.",
        ]
    )
    (out_dir / "storyboard.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_approval_checklist(out_dir: Path, package: dict[str, Any]) -> None:
    review = package["review"]
    story_selling_score = review.get("story_selling_score", {})
    story_selling_gate = review.get("story_selling_gate", {})
    lines = [
        "# Final Approval Checklist",
        "",
        f"Status: {review.get('status', 'draft_review')}",
        f"Score: {review.get('total', 0)} / {review.get('max', 40)}",
        f"Story-Selling: {story_selling_score.get('total', 0)} / 30",
        f"Story-Selling Gate: {story_selling_gate.get('status', 'PENDING')}",
        f"Pass: {review.get('pass', False)}",
        "",
        "## Before Image Generation",
        "",
        "- [ ] Slide copy is final.",
        "- [ ] `post-copy-visual-room.json` is GO after copy confirmation.",
        "- [ ] The prompts preserve the supplied photos and story.",
        "- [ ] The package does not feel like generic couple content.",
        "- [ ] Text is short enough for both 1080x1350 post slides and 1080x1920 Reels/Stories slides.",
        "- [ ] Final generation will create separate native 4:5 and 9:16 outputs, not a resized duplicate.",
        "- [ ] Brandmark is tiny and low contrast.",
        "",
        "## Required Changes",
        "",
    ]
    changes = review.get("required_changes_before_image_generation") or []
    if changes:
        lines.extend(f"- [ ] {change}" for change in changes)
    else:
        lines.append("- [ ] No required changes listed by reviewer.")

    (out_dir / "final-approval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_agent_reports(out_dir: Path, outputs: dict[str, str]) -> None:
    lines = ["# C-Layer Agent Reports", ""]
    for name, output in outputs.items():
        lines.extend([f"## {name}", "", output, ""])
    (out_dir / "agent-reports.md").write_text("\n".join(lines), encoding="utf-8")


def write_package(
    *,
    out_dir: Path,
    manifest: dict[str, Any],
    package: dict[str, Any],
    agent_outputs: dict[str, str],
) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "concept.json", package["concept"])
    write_json(out_dir / "post-copy-visual-room.json", package["post_copy_visual_room"])
    write_json(out_dir / "visual-debate.json", package["visual_debate"])
    write_json(out_dir / "slides.json", package["slides"])
    write_json(out_dir / "prompt-pack.json", package["prompt_pack"])
    write_json(out_dir / "copy.json", package["copy"])
    write_json(out_dir / "review.json", package["review"])
    write_storyboard(out_dir, package)
    write_approval_checklist(out_dir, package)
    write_agent_reports(out_dir, agent_outputs)


def create_illustration_carousel(
    *,
    story: str,
    image_paths: list[str | Path],
    identity_image_paths: list[str | Path] | None = None,
    title: str | None = None,
    slide_count: int = DEFAULT_SLIDE_COUNT,
    style_brief: str | None = None,
    output_root: Path = OUTPUT_ROOT,
) -> Path:
    if not story.strip():
        raise ValueError("Story is required.")
    validate_slide_count(slide_count)

    normalized_images = normalize_image_paths(image_paths)
    normalized_identity_images = normalize_image_paths(identity_image_paths or [])
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print("Running C-layer illustrated carousel agents...")
    agent_outputs: dict[str, str] = {}
    for agent_name, skills in SPECIALIST_AGENTS:
        print(f"  -> {agent_name}...")
        agent_outputs[agent_name] = run_agent(
            client,
            agent_name=agent_name,
            skill_names=skills,
            story=story,
            title=title,
            slide_count=slide_count,
            style_brief=style_brief,
            image_paths=normalized_images,
            identity_image_paths=normalized_identity_images,
            prior_outputs=agent_outputs,
        )

    print("  -> illustration-carousel-orchestrator...")
    orchestrator_output = run_agent(
        client,
        agent_name=ORCHESTRATOR_AGENT,
        skill_names=ORCHESTRATOR_SKILLS,
        story=story,
        title=title,
        slide_count=slide_count,
        style_brief=style_brief,
        image_paths=normalized_images,
        identity_image_paths=normalized_identity_images,
        prior_outputs=agent_outputs,
        model="claude-opus-4-6",
        max_tokens=5000,
    )
    agent_outputs[ORCHESTRATOR_AGENT] = orchestrator_output

    package = extract_json_object(orchestrator_output)
    validate_package(package)

    concept = package["concept"]
    final_title = title or concept.get("title") or "Illustration Carousel"
    slug = slugify_title(final_title)
    dated_root = output_root / datetime.now().strftime("%Y-%m-%d")
    out_dir = dated_root / slug
    suffix = 2
    while out_dir.exists():
        out_dir = dated_root / f"{slug}-{suffix}"
        suffix += 1

    manifest = build_manifest(
        title=final_title,
        slug=out_dir.name,
        story=story,
        image_paths=normalized_images,
        identity_image_paths=normalized_identity_images,
    )
    write_package(
        out_dir=out_dir,
        manifest=manifest,
        package=package,
        agent_outputs=agent_outputs,
    )
    print(f"\nCarousel package saved -> {out_dir}")
    return out_dir


def interactive_mode() -> dict[str, Any]:
    print("\n=== Illustrated Carousel Automation - @a.storyof.two ===\n")
    print("Share the story and reference pictures. Press Enter to skip optional fields.\n")

    title = input("Working title (optional): ").strip() or None
    story = input("Story (required): ").strip()
    if not story:
        print("Story is required.")
        sys.exit(1)

    raw_images = input("Image paths (comma-separated, required): ").strip()
    if not raw_images:
        print("At least one image path is required.")
        sys.exit(1)
    image_paths = [item.strip() for item in raw_images.split(",") if item.strip()]
    raw_identity_images = input("Identity image paths for Aachu/Zuv (comma-separated, optional): ").strip()
    identity_image_paths = (
        [item.strip() for item in raw_identity_images.split(",") if item.strip()]
        if raw_identity_images
        else None
    )

    slide_count_raw = input(
        f"Slide count [{DEFAULT_SLIDE_COUNT}, choose {MIN_STORY_SLIDES}-{MAX_STORY_SLIDES}]: "
    ).strip()
    slide_count = validate_slide_count(int(slide_count_raw)) if slide_count_raw else DEFAULT_SLIDE_COUNT
    style_brief = input("Style brief (optional): ").strip() or None

    return {
        "title": title,
        "story": story,
        "image_paths": image_paths,
        "identity_image_paths": identity_image_paths,
        "slide_count": slide_count,
        "style_brief": style_brief,
    }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Create an illustrated carousel package.")
    parser.add_argument("--story", help="Story or memory behind the pictures")
    parser.add_argument("--story-file", help="Read story from a text file")
    parser.add_argument("--title", help="Optional working title")
    parser.add_argument(
        "--image",
        dest="images",
        action="append",
        default=[],
        help="Reference image path. Repeat for multiple images.",
    )
    parser.add_argument(
        "--identity-image",
        dest="identity_images",
        action="append",
        default=None,
        help="Aachu/Zuv identity or clothing reference image. Repeat for multiple references.",
    )
    parser.add_argument(
        "--slide-count",
        type=int,
        default=DEFAULT_SLIDE_COUNT,
        help=f"Slide count, {MIN_STORY_SLIDES}-{MAX_STORY_SLIDES}",
    )
    parser.add_argument("--style-brief", help="Optional illustration/style direction")
    args = parser.parse_args()

    if args.story_file:
        story_text = Path(args.story_file).expanduser().read_text(encoding="utf-8")
    else:
        story_text = args.story

    if story_text and args.images:
        options = {
            "story": story_text,
            "image_paths": args.images,
            "identity_image_paths": args.identity_images,
            "title": args.title,
            "slide_count": args.slide_count,
            "style_brief": args.style_brief,
        }
    else:
        options = interactive_mode()

    create_illustration_carousel(**options)
