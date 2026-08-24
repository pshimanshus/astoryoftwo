"""Small fallback helpers for the Codex-native carousel builder.

Creative routing belongs in the storytelling skill and the creator/model
conversation.  This module deliberately does not contain a keyword classifier,
dozens of prewritten carousel lanes, or numeric concept scoring.  It only
preserves supplied copy when a CLI caller has not provided a creative brief and
keeps identity-reference selection bounded.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any


IDENTITY_IMAGE_DIRS = (
    Path("config/references/identity"),
    Path("identity_images"),
)
SUPPORTED_IDENTITY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IDENTITY_REFERENCE_BUNDLE = 4
IDENTITY_REFERENCE_RULE = (
    "Select a small story-specific identity bundle. Attach actual files to every "
    "generation call; filenames and prose are not identity evidence."
)
FALLBACK_COMPACT_STYLE_PROMPT = (
    "premium romantic watercolor-and-ink illustration on warm ivory paper, visible "
    "paper grain, fine pencil/ink linework, transparent washes, muted vintage palette"
)


def discover_identity_images(workspace_root: Path) -> list[Path]:
    candidates: list[Path] = []
    for relative in IDENTITY_IMAGE_DIRS:
        directory = workspace_root / relative
        if not directory.is_dir():
            continue
        candidates.extend(
            path
            for path in directory.rglob("*")
            if path.is_file()
            and path.suffix.lower() in SUPPORTED_IDENTITY_IMAGE_EXTENSIONS
            and "_dossier" not in path.parts
        )
    return sorted(dict.fromkeys(candidates))


def select_identity_reference_bundle(
    candidate_paths: list[Path], *, explicit: bool
) -> list[Path]:
    if explicit and not candidate_paths:
        raise ValueError(
            "Pass 1-4 actual Aachu/Zuv identity reference images, or omit the "
            "explicit identity argument to use the candidate library."
        )
    if explicit and len(candidate_paths) > MAX_IDENTITY_REFERENCE_BUNDLE:
        raise ValueError(
            f"Use at most {MAX_IDENTITY_REFERENCE_BUNDLE} identity references: "
            "face, body/posture, outfit/context, and emotion/detail anchors."
        )
    return candidate_paths[:MAX_IDENTITY_REFERENCE_BUNDLE]


def build_identity_reference_selection(
    *,
    candidate_paths: list[Path],
    selected_paths: list[Path],
    explicit: bool,
) -> dict[str, Any]:
    roles = (
        "face anchor",
        "body/posture anchor",
        "story-relevant outfit/context anchor",
        "emotion/detail anchor",
    )
    return {
        "mode": "explicit" if explicit else "auto_discovered",
        "rule": IDENTITY_REFERENCE_RULE,
        "candidate_count": len(candidate_paths),
        "selected_count": len(selected_paths),
        "selected_references": [
            {"path": str(path), "role": roles[index]}
            for index, path in enumerate(selected_paths)
        ],
    }


def infer_workspace_root(output_root: Path) -> Path:
    resolved = output_root.expanduser().resolve()
    if resolved.name == "carousels" and resolved.parent.name == "output":
        return resolved.parent.parent
    return resolved.parent


def infer_title(story: str, title: str | None) -> str:
    if title and title.strip():
        return title.strip()
    for line in story.splitlines():
        candidate = re.sub(
            r"^(cover|title|concept|cold open|deepening|conflict|turn|payoff)\s*:\s*",
            "",
            line.strip(),
            flags=re.IGNORECASE,
        )
        if candidate:
            words = candidate.rstrip(".!?").split()
            return " ".join(words[:8]).title()
    return "A Story Of Two"


def _source_groups(paths: list[Path], slide_count: int) -> list[list[str]]:
    if not paths:
        return [[] for _ in range(slide_count)]
    return [[str(paths[index % len(paths)])] for index in range(slide_count)]


def _story_beats(story: str) -> list[tuple[str, str]]:
    labeled: list[tuple[str, str]] = []
    for raw in story.splitlines():
        line = raw.strip()
        if not line:
            continue
        match = re.match(
            r"^(cover|cold\s*open|deepening|conflict|turn|payoff)\s*:\s*(.+)$",
            line,
            flags=re.IGNORECASE,
        )
        if match:
            labeled.append((match.group(1).lower().replace(" ", "_"), match.group(2).strip()))
    if labeled:
        return labeled

    sentences = [
        value.strip()
        for value in re.split(r"(?<=[.!?])\s+|\n+", story.strip())
        if value.strip()
    ]
    if not sentences:
        return []
    if len(sentences) == 1:
        return [("story_beat", sentences[0])]
    beats: list[tuple[str, str]] = []
    for index, sentence in enumerate(sentences):
        role = "cover" if index == 0 else "payoff" if index == len(sentences) - 1 else "deepening"
        beats.append((role, sentence))
    return beats


def build_slides(
    story: str,
    image_paths: list[Path],
    slide_count: int,
) -> list[dict[str, Any]]:
    """Build a conservative draft when no model-authored creative brief exists.

    Labeled creator copy is preserved exactly. If the source has fewer beats
    than requested, repeat no copy and invent no pseudo-specific story; instead
    stop at the available beats. A model-authored creative brief remains the
    preferred path because it can supply genuinely observable actions.
    """

    beats = _story_beats(story)
    if not beats:
        raise ValueError("Story must contain at least one non-empty beat.")
    if len(beats) > slide_count:
        beats = beats[:slide_count]
    sources = _source_groups(image_paths, len(beats))
    slides: list[dict[str, Any]] = []
    for index, ((role, copy), source_images) in enumerate(zip(beats, sources, strict=True), start=1):
        visual = (
            "Draft needed: choose one specific observable Aachu/Zuv physical action "
            f"from the creator's lived context that proves this {role} beat with copy hidden."
        )
        slides.append(
            {
                "slide": index,
                "role": role,
                "copy": copy,
                "visual": visual,
                "physical_action": visual,
                "relationship_state": "",
                "camera": "",
                "focal_hierarchy": "physical action first",
                "source_images": source_images,
                "needs_physical_action": True,
            }
        )
    return slides


__all__ = [
    "FALLBACK_COMPACT_STYLE_PROMPT",
    "MAX_IDENTITY_REFERENCE_BUNDLE",
    "build_identity_reference_selection",
    "build_slides",
    "discover_identity_images",
    "infer_title",
    "infer_workspace_root",
    "select_identity_reference_bundle",
]
