"""Small fallback helpers for the Codex-native carousel builder.

Creative routing belongs in the storytelling skill and the creator/model
conversation.  This module deliberately does not contain a keyword classifier,
dozens of prewritten carousel lanes, or numeric concept scoring.  It only
preserves supplied copy when a CLI caller has not provided a creative brief and
keeps identity-reference selection bounded.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


SUPPORTED_IDENTITY_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
MAX_IDENTITY_REFERENCE_BUNDLE = 4
IDENTITY_DOSSIER_PATH = Path(
    "config/references/identity/_dossier/identity-dossier.json"
)
IDENTITY_REFERENCE_RULE = (
    "Select a small story-specific identity bundle. Attach actual files to every "
    "generation call; filenames and prose are not identity evidence."
)
FALLBACK_COMPACT_STYLE_PROMPT = (
    "premium romantic watercolor-and-ink illustration on warm ivory paper, visible "
    "paper grain, fine pencil/ink linework, transparent washes, muted vintage palette"
)


def discover_identity_images(workspace_root: Path) -> list[Path]:
    """Return the curated generation bundle, never a filename-sorted sample.

    The identity dossier is the creator-owned selection surface. Falling back
    to the first files in the library made the people vary with directory
    order and could omit either Aachu, Zuv, or a together/body anchor.
    """

    dossier_path = workspace_root / IDENTITY_DOSSIER_PATH
    if not dossier_path.is_file():
        return []
    payload = json.loads(dossier_path.read_text(encoding="utf-8"))
    raw_bundle = payload.get("selected_generation_bundle")
    if not isinstance(raw_bundle, list):
        raise ValueError(
            f"{IDENTITY_DOSSIER_PATH} needs selected_generation_bundle."
        )
    selected: list[Path] = []
    for raw_path in raw_bundle:
        path = Path(str(raw_path)).expanduser()
        if not path.is_absolute():
            path = workspace_root / path
        if not path.is_file():
            raise FileNotFoundError(f"Missing curated identity reference: {path}")
        if path.suffix.lower() not in SUPPORTED_IDENTITY_IMAGE_EXTENSIONS:
            raise ValueError(f"Unsupported curated identity reference: {path}")
        selected.append(path)
    selected = list(dict.fromkeys(selected))
    if len(selected) > MAX_IDENTITY_REFERENCE_BUNDLE:
        raise ValueError(
            f"Curated identity dossier exceeds the {MAX_IDENTITY_REFERENCE_BUNDLE}-image limit."
        )
    subjects = {_identity_subject(path) for path in selected}
    missing = {"aachu", "zuv", "together"} - subjects
    if missing:
        raise ValueError(
            "Curated identity dossier must include Aachu, Zuv, and together references; "
            f"missing: {', '.join(sorted(missing))}."
        )
    return selected


def _identity_subject(path: Path) -> str:
    lowered = {part.lower() for part in path.parts}
    for subject in ("aachu", "zuv", "together"):
        if subject in lowered:
            return subject
    return "identity"


def select_identity_reference_bundle(
    candidate_paths: list[Path], *, explicit: bool
) -> list[Path]:
    if explicit and not candidate_paths:
        raise ValueError(
            "Pass 1-4 actual Aachu/Zuv identity reference images, or omit the "
            "explicit identity argument to use the curated dossier."
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
    subject_counts: dict[str, int] = {}
    selected_references: list[dict[str, str]] = []
    for path in selected_paths:
        subject = _identity_subject(path)
        subject_counts[subject] = subject_counts.get(subject, 0) + 1
        role = {
            "aachu": "Aachu identity anchor",
            "zuv": "Zuv identity anchor",
            "together": (
                "together face/scale anchor"
                if subject_counts[subject] == 1
                else "together body/posture anchor"
            ),
        }.get(subject, "creator-selected identity anchor")
        selected_references.append({"path": str(path), "role": role})
    return {
        "mode": "explicit" if explicit else "curated_identity_dossier",
        "rule": IDENTITY_REFERENCE_RULE,
        "candidate_count": len(candidate_paths),
        "selected_count": len(selected_paths),
        "selected_references": selected_references,
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
    current_role: str | None = None
    current_lines: list[str] = []
    unlabeled_before_first: list[str] = []

    def flush_current() -> None:
        nonlocal current_role, current_lines
        if current_role is None:
            return
        copy = "\n".join(current_lines).strip()
        if not copy:
            raise ValueError(f"{current_role.replace('_', ' ').title()} needs copy.")
        labeled.append((current_role, copy))
        current_role = None
        current_lines = []

    for raw in story.splitlines():
        match = re.match(
            r"^\s*(cover|cold\s*open|deepening|conflict|turn|payoff)\s*:\s?(.*)$",
            raw,
            flags=re.IGNORECASE,
        )
        if match:
            flush_current()
            current_role = match.group(1).lower().replace(" ", "_")
            current_lines = [match.group(2).rstrip()]
        elif current_role is not None:
            current_lines.append(raw.rstrip())
        elif raw.strip():
            unlabeled_before_first.append(raw.strip())
    flush_current()
    if labeled:
        if unlabeled_before_first:
            raise ValueError(
                "Unlabeled copy appears before the first story beat; refusing to discard it."
            )
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
    slide_count: int | None,
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
    if len(beats) > 11:
        raise ValueError(
            "Story contains more than 11 beats; reduce or explicitly combine beats before packaging."
        )
    if slide_count is not None and len(beats) > slide_count:
        raise ValueError(
            f"Story contains {len(beats)} beats but --slide-count is {slide_count}; "
            "refusing to discard creator copy."
        )
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
    "IDENTITY_DOSSIER_PATH",
    "MAX_IDENTITY_REFERENCE_BUNDLE",
    "build_identity_reference_selection",
    "build_slides",
    "discover_identity_images",
    "infer_title",
    "infer_workspace_root",
    "select_identity_reference_bundle",
]
