"""Small shared contract for the @a.storyof.two carousel hot path.

The old module ran a sequential eleven-agent Anthropic room before it could
write a package.  That duplicated Codex-native creation, buried the creator's
idea under scores and debates, and made a production command depend on an API
key.  Carousel creation now has one implementation: ``create_codex_native_carousel``.

This module keeps only path, slug, and slide-count validation shared by the
canonical builder. It is not a second executable creation surface.
"""

from __future__ import annotations

import re
from pathlib import Path


MIN_STORY_SLIDES = 4
MAX_STORY_SLIDES = 11


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


def normalize_image_paths(image_paths: list[str | Path]) -> list[Path]:
    normalized = [Path(path).expanduser() for path in image_paths]
    missing = [str(path) for path in normalized if not path.exists()]
    if missing:
        raise FileNotFoundError("Missing reference image(s): " + ", ".join(missing))
    return normalized
