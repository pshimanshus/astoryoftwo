#!/usr/bin/env python3
"""Analyze story-canon source cards into reusable story-selling patterns.

The analyzer is intentionally deterministic: it reads source-register metadata
plus optional parsed source cards, then emits abstracted pattern summaries. It
does not preserve long source quotations or scraped copyrighted bodies.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import UTC, date, datetime
from pathlib import Path
from typing import Any

try:
    from scripts.story_canon_policy import source_should_generate_patterns
except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
    from story_canon_policy import source_should_generate_patterns


DEFAULT_PARSED_DIR = Path("corpus/story-canon/parsed")
DEFAULT_OUTPUT_ROOT = Path("output/story-canon")
REFERENCE_DIR = Path("config/references/story-selling-canon")

REFERENCE_FILES = {
    "romance-novel-canon": REFERENCE_DIR / "romance-novel-canon.md",
    "romance-film-canon": REFERENCE_DIR / "romance-film-canon.md",
    "screenplay-patterns": REFERENCE_DIR / "screenplay-patterns.md",
    "story-selling-online": REFERENCE_DIR / "story-selling-online.md",
}

ROMANCE_ARC_STEPS = [
    "meet",
    "attraction",
    "misread",
    "intimacy",
    "rupture",
    "proof",
    "choice",
    "payoff",
]

SCENE_ENGINE_STEPS = [
    "want",
    "obstacle",
    "hidden_feeling",
    "reversal",
    "visible_behavior",
]

SELL_ONLINE_STEPS = [
    "reader_identity",
    "desire",
    "tension",
    "proof",
    "transformation",
    "cta",
]

CAROUSEL_ADAPTER_STEPS = [
    "universal_hook",
    "aachu_spark",
    "proof_beat",
    "zuv_active_care",
    "tender_thesis",
]


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "untitled"


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def parse_date(value: str | None) -> date:
    if not value:
        return date.today()
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError as exc:
        raise SystemExit("--date must use YYYY-MM-DD") from exc


def normalize_string_list(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str):
        return [part.strip() for part in re.split(r"[,;|]", value) if part.strip()]
    return [str(value).strip()] if str(value).strip() else []


def clamp_confidence(value: Any, default: float = 0.65) -> float:
    try:
        confidence = float(value)
    except (TypeError, ValueError):
        confidence = default
    confidence = max(0.0, min(1.0, confidence))
    return round(confidence, 2)


def concise_text(value: Any, max_chars: int = 260) -> str:
    if value is None:
        return ""
    if isinstance(value, list):
        text = " ".join(str(item) for item in value)
    elif isinstance(value, dict):
        text = " ".join(str(item) for item in value.values())
    else:
        text = str(value)
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 3].rstrip() + "..."


def load_source_register(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise SystemExit(f"Missing source register: {path}")
    data = read_json(path)
    sources = data.get("sources")
    if not isinstance(sources, list):
        raise SystemExit("source register must contain a top-level sources list")
    normalized = []
    for index, source in enumerate(sources, start=1):
        if not isinstance(source, dict):
            raise SystemExit(f"source #{index} must be an object")
        source_id = str(source.get("id", "")).strip()
        if not source_id:
            raise SystemExit(f"source #{index} is missing id")
        normalized.append(source)
    return normalized


def parse_markdown_card(path: Path) -> dict[str, Any]:
    lines = path.read_text(encoding="utf-8").splitlines()
    card: dict[str, Any] = {"card_path": str(path)}
    body: list[str] = []
    for line in lines:
        match = re.match(r"^\s*[-*]?\s*([A-Za-z_ -]{2,40})\s*:\s*(.+?)\s*$", line)
        if match:
            key = match.group(1).strip().lower().replace(" ", "_").replace("-", "_")
            card[key] = match.group(2).strip()
        elif line.strip() and not line.lstrip().startswith("#"):
            body.append(line.strip())
    if body:
        card["notes"] = concise_text(" ".join(body), 800)
    return card


def load_parsed_cards(parsed_dir: Path) -> dict[str, dict[str, Any]]:
    cards: dict[str, dict[str, Any]] = {}
    if not parsed_dir.exists():
        return cards

    for path in sorted(parsed_dir.rglob("*")):
        if not path.is_file():
            continue
        card: dict[str, Any] | None = None
        if path.suffix.lower() == ".json":
            data = read_json(path)
            if isinstance(data, dict):
                card = data
        elif path.suffix.lower() in {".md", ".markdown"}:
            card = parse_markdown_card(path)
        if not card:
            continue

        source_id = (
            card.get("source_id")
            or card.get("id")
            or card.get("source")
            or path.stem
        )
        source_id = str(source_id).strip()
        if source_id:
            cards[source_id] = card
    return cards


def merge_source_with_card(source: dict[str, Any], card: dict[str, Any] | None) -> dict[str, Any]:
    merged = dict(source)
    if card:
        for key, value in card.items():
            if key not in {"id", "source_id"} and value not in (None, "", []):
                merged[f"parsed_{key}"] = value
        if card.get("confidence") is not None:
            source_confidence = clamp_confidence(source.get("confidence"))
            parsed_confidence = clamp_confidence(card.get("confidence"), source_confidence)
            merged["confidence"] = round((source_confidence + parsed_confidence) / 2, 2)
    return merged


def source_kind(source: dict[str, Any]) -> str:
    source_type = str(source.get("type", "")).strip().lower()
    if source_type == "story_selling_framework":
        return "article"
    if source_type == "craft_article":
        return "article"
    if source_type == "article":
        return "article"
    if source_type == "film":
        return "film"
    if source_type == "book":
        return "book"

    raw = " ".join(
        [
            source_type,
            " ".join(normalize_string_list(source.get("subjects"))),
            " ".join(normalize_string_list(source.get("tags"))),
            " ".join(normalize_string_list(source.get("framework_tags"))),
        ]
    ).lower()
    if "screenplay" in raw or "script" in raw or "beat" in raw:
        return "screenplay"
    if "film" in raw or "movie" in raw or "cinema" in raw:
        return "film"
    if "article" in raw or "marketing" in raw or "craft" in raw or "online" in raw:
        return "article"
    return "book"


def source_citation(source: dict[str, Any]) -> str:
    return str(source.get("id", "")).strip()


def source_title(source: dict[str, Any]) -> str:
    return str(source.get("title") or source.get("parsed_title") or source.get("id") or "Untitled")


def source_creator(source: dict[str, Any]) -> str:
    return str(source.get("creator") or source.get("author") or source.get("parsed_author") or "").strip()


def source_signals(source: dict[str, Any]) -> list[str]:
    phrase_candidates: list[str] = []
    for key in [
        "subjects",
        "tags",
        "framework_tags",
        "parsed_process_tags",
        "parsed_framework_tags",
    ]:
        for item in normalize_string_list(source.get(key)):
            phrase = re.sub(r"[^A-Za-z0-9 -]+", "", item).strip().lower()
            phrase = re.sub(r"\s+", " ", phrase)
            if phrase and phrase not in phrase_candidates:
                phrase_candidates.append(phrase)
            if len(phrase_candidates) >= 4:
                break
        if len(phrase_candidates) >= 4:
            break

    priority_fields = [
        source.get("subjects"),
        source.get("tags"),
        source.get("framework_tags"),
        source.get("parsed_summary"),
        source.get("parsed_notes"),
        source.get("parsed_extraction_notes"),
        source.get("parsed_process_tags"),
        source.get("allowed_use"),
    ]
    fallback_fields = [source.get("title")]
    text = " ".join(concise_text(field, 500) for field in priority_fields if field)
    if not text.strip():
        text = " ".join(concise_text(field, 500) for field in fallback_fields if field)
    words = re.findall(r"[a-z][a-z-]{3,}", text.lower())
    stopwords = {
        "about",
        "allowed",
        "analysis",
        "article",
        "book",
        "craft",
        "derived",
        "film",
        "from",
        "full",
        "genre",
        "grid",
        "metadata",
        "public",
        "source",
        "story",
        "text",
        "that",
        "this",
        "with",
    }
    ranked: list[str] = []
    for phrase in phrase_candidates:
        ranked.append(phrase)
    for word in words:
        if word not in stopwords and word not in ranked:
            ranked.append(word)
        if len(ranked) >= 8:
            break
    return ranked or ["romance", "conflict", "proof"]


def pattern_id(prefix: str, source: dict[str, Any]) -> str:
    return f"{prefix}-{slugify(source_citation(source))}"


def build_romance_arc(source: dict[str, Any]) -> dict[str, Any]:
    title = source_title(source)
    signals = source_signals(source)
    confidence = clamp_confidence(source.get("confidence"))
    steps = {
        "meet": f"Open with the social situation or promise that makes {title} legible.",
        "attraction": f"Let attraction appear as attention, friction, or curiosity around {signals[0]}.",
        "misread": f"Make the first emotional error concrete: pride, fear, duty, distance, or status masks the truth.",
        "intimacy": "Use a small private exchange where the couple sees what public behavior hides.",
        "rupture": f"Force the pair to confront the cost of wanting each other through {signals[1] if len(signals) > 1 else 'a real obstacle'}.",
        "proof": "Show love through action, restraint, sacrifice, or repair before any thesis line.",
        "choice": "Make the final choice active for both people, not a reward handed to one side.",
        "payoff": "Land the ending as earned emotional clarity: the obstacle changes because the people changed.",
    }
    return {
        "id": pattern_id("romance-arc", source),
        "schema": "romance_arc",
        "title": f"{title}: romance arc",
        "summary": "A derived romance structure that turns attraction into earned proof, with no copied source prose.",
        "steps": steps,
        "confidence": confidence,
        "source_ids": [source_citation(source)],
    }


def build_scene_engine(source: dict[str, Any]) -> dict[str, Any]:
    title = source_title(source)
    kind = source_kind(source)
    signals = source_signals(source)
    confidence = clamp_confidence(source.get("confidence"))
    steps = {
        "want": f"Give the lead a visible want tied to {signals[0]}.",
        "obstacle": f"Block the want with an emotional or social pressure, not only logistics.",
        "hidden_feeling": "Keep the vulnerable feeling slightly unsaid so behavior has to carry it.",
        "reversal": f"Turn the scene when a small action reveals the opposite of what was assumed.",
        "visible_behavior": "End on something an audience can see: a pause, a choice, a returned object, a changed distance.",
    }
    return {
        "id": pattern_id("scene-engine", source),
        "schema": "scene_engine",
        "title": f"{title}: {kind} scene engine",
        "summary": "A scene pattern for converting internal romance pressure into visible behavior.",
        "steps": steps,
        "confidence": confidence,
        "source_ids": [source_citation(source)],
    }


def build_sell_online_engine(source: dict[str, Any]) -> dict[str, Any]:
    title = source_title(source)
    signals = source_signals(source)
    confidence = clamp_confidence(source.get("confidence"))
    steps = {
        "reader_identity": f"Name the person who already recognizes the {signals[0]} tension.",
        "desire": "Surface what they want to believe about love, safety, attention, or being chosen.",
        "tension": f"State the obstacle as a felt contradiction around {signals[1] if len(signals) > 1 else 'the relationship dynamic'}.",
        "proof": "Use specific scenes, objects, gestures, or screenshots as evidence before advice.",
        "transformation": "Show the reader how the story changes their self-understanding.",
        "cta": "Invite a reply, save, share, or next read that continues the emotional problem.",
    }
    return {
        "id": pattern_id("sell-online", source),
        "schema": "sell_online_engine",
        "title": f"{title}: online story-selling engine",
        "summary": "A derived online storytelling process that sells through reader identity, proof, and transformation.",
        "steps": steps,
        "confidence": confidence,
        "source_ids": [source_citation(source)],
    }


def build_carousel_adapter(source: dict[str, Any]) -> dict[str, Any]:
    title = source_title(source)
    signals = source_signals(source)
    confidence = clamp_confidence(source.get("confidence"))
    steps = {
        "universal_hook": f"Start from a relationship truth about {signals[0]}, not from a pretty location.",
        "aachu_spark": "Give Aachu the expressive pressure: the feeling, demand, joke, chaos, or brave ask.",
        "proof_beat": "Use one concrete photo/place/object/outfit detail as evidence for the truth.",
        "zuv_active_care": "Give Zuv a visible active choice: steady, notice, protect, repair, or choose.",
        "tender_thesis": "End with a line that feels earned by the proof beat, not pasted on as a quote.",
    }
    return {
        "id": pattern_id("carousel-adapter", source),
        "schema": "carousel_adapter",
        "title": f"{title}: A Story of Two adapter",
        "summary": "A carousel adaptation pattern for turning canon structure into Aachu/Zuv-specific proof.",
        "steps": steps,
        "confidence": confidence,
        "source_ids": [source_citation(source)],
    }


def build_pattern_map(sources: list[dict[str, Any]], parsed_cards: dict[str, dict[str, Any]]) -> dict[str, Any]:
    merged_sources = [merge_source_with_card(source, parsed_cards.get(source_citation(source))) for source in sources]
    pattern_sources = [source for source in merged_sources if source_should_generate_patterns(source)]
    pattern_map: dict[str, Any] = {
        "generated_at": datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z"),
        "source_count": len(merged_sources),
        "pattern_source_count": len(pattern_sources),
        "excluded_source_ids": [
            source_citation(source)
            for source in merged_sources
            if not source_should_generate_patterns(source)
        ],
        "schemas": {
            "romance_arc": ROMANCE_ARC_STEPS,
            "scene_engine": SCENE_ENGINE_STEPS,
            "sell_online_engine": SELL_ONLINE_STEPS,
            "carousel_adapter": CAROUSEL_ADAPTER_STEPS,
        },
        "romance_arc": [],
        "scene_engine": [],
        "sell_online_engine": [],
        "carousel_adapter": [],
    }

    for source in pattern_sources:
        kind = source_kind(source)
        if kind == "book":
            pattern_map["romance_arc"].append(build_romance_arc(source))
            pattern_map["scene_engine"].append(build_scene_engine(source))
            pattern_map["carousel_adapter"].append(build_carousel_adapter(source))
        elif kind in {"film", "screenplay"}:
            pattern_map["scene_engine"].append(build_scene_engine(source))
            pattern_map["carousel_adapter"].append(build_carousel_adapter(source))
            if kind == "screenplay":
                pattern_map["romance_arc"].append(build_romance_arc(source))
        else:
            pattern_map["sell_online_engine"].append(build_sell_online_engine(source))
            pattern_map["carousel_adapter"].append(build_carousel_adapter(source))

    return pattern_map


def validate_patterns(pattern_map: dict[str, Any]) -> None:
    for schema in ["romance_arc", "scene_engine", "sell_online_engine", "carousel_adapter"]:
        patterns = pattern_map.get(schema)
        if not isinstance(patterns, list):
            raise SystemExit(f"pattern-map schema {schema} must be a list")
        for pattern in patterns:
            if pattern.get("confidence") is None:
                raise SystemExit(f"pattern {pattern.get('id')} is missing confidence")
            if not pattern.get("source_ids"):
                raise SystemExit(f"pattern {pattern.get('id')} is missing source_ids")
            for step in pattern_map["schemas"][schema]:
                if step not in pattern.get("steps", {}):
                    raise SystemExit(f"pattern {pattern.get('id')} is missing step {step}")


def pattern_bullets(patterns: list[dict[str, Any]], limit: int = 12) -> str:
    if not patterns:
        return "- No source-backed patterns generated yet.\n"
    lines: list[str] = []
    for pattern in patterns[:limit]:
        source_refs = ", ".join(f"`{source_id}`" for source_id in pattern["source_ids"])
        lines.append(f"## {pattern['title']}")
        lines.append("")
        lines.append(f"- Confidence: {pattern['confidence']}")
        lines.append(f"- Sources: {source_refs}")
        lines.append(f"- Use: {pattern['summary']}")
        for step, value in pattern["steps"].items():
            label = "CTA" if step == "cta" else step.replace("_", " ").title()
            lines.append(f"- {label}: {value}")
        lines.append("")
    remaining = len(patterns) - limit
    if remaining > 0:
        lines.append(f"_Plus {remaining} additional source-backed patterns in `pattern-map.json`._")
        lines.append("")
    return "\n".join(lines)


def write_reference_markdown(pattern_map: dict[str, Any], output_dir: Path) -> None:
    REFERENCE_DIR.mkdir(parents=True, exist_ok=True)
    header = (
        "<!-- Generated by scripts/analyze_story_canon.py. Edit sources, not this summary. -->\n\n"
    )

    novel_patterns = pattern_map["romance_arc"]
    film_patterns = [
        pattern
        for pattern in pattern_map["scene_engine"]
        if "film" in pattern["title"].lower() or "screenplay" in pattern["title"].lower()
    ]
    screenplay_patterns = [
        pattern
        for pattern in pattern_map["scene_engine"]
        if "screenplay" in pattern["title"].lower()
    ] or pattern_map["scene_engine"]
    online_patterns = pattern_map["sell_online_engine"]

    docs = {
        "romance-novel-canon": (
            "# Romance Novel Canon\n\n"
            "Derived romance-arc patterns from legally allowed source metadata and parsed cards. "
            "Use these as structural memory, not as quoted prose.\n\n"
            + pattern_bullets(novel_patterns)
        ),
        "romance-film-canon": (
            "# Romance Film Canon\n\n"
            "Derived visual-scene patterns for romantic film and cinema references. "
            "Use these to make love visible through action, staging, and reversal.\n\n"
            + pattern_bullets(film_patterns)
        ),
        "screenplay-patterns": (
            "# Screenplay Patterns\n\n"
            "Scene engines abstracted for beats, wants, obstacles, reversals, and visible behavior. "
            "No screenplay text is stored here.\n\n"
            + pattern_bullets(screenplay_patterns)
        ),
        "story-selling-online": (
            "# Story Selling Online\n\n"
            "Online story-selling patterns for turning romantic truth into reader identity, proof, "
            "transformation, and a clean CTA.\n\n"
            + pattern_bullets(online_patterns)
        ),
    }

    for key, content in docs.items():
        REFERENCE_FILES[key].write_text(header + content, encoding="utf-8")

    index = output_dir / "reference-files.json"
    write_json(index, {key: str(path) for key, path in REFERENCE_FILES.items()})


def analyze_story_canon(source_register: Path, parsed_dir: Path, output_root: Path, run_date: date) -> Path:
    sources = load_source_register(source_register)
    parsed_cards = load_parsed_cards(parsed_dir)
    pattern_map = build_pattern_map(sources, parsed_cards)
    validate_patterns(pattern_map)

    output_dir = output_root / run_date.isoformat()
    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "pattern-map.json", pattern_map)
    write_reference_markdown(pattern_map, output_dir)
    return output_dir


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Analyze story-canon source cards into pattern-map JSON and reference markdown."
    )
    parser.add_argument("--source-register", type=Path, required=True, help="Path to source-register.json.")
    parser.add_argument(
        "--parsed-dir",
        type=Path,
        default=DEFAULT_PARSED_DIR,
        help="Directory containing parsed JSON or Markdown source cards.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Output root or dated output directory. Default: output/story-canon/YYYY-MM-DD.",
    )
    parser.add_argument("--date", help="Run date in YYYY-MM-DD format. Defaults to today.")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    run_date = parse_date(args.date)
    output_root = args.output_dir or DEFAULT_OUTPUT_ROOT
    if output_root.name == run_date.isoformat():
        dated_root = output_root.parent
    else:
        dated_root = output_root
    out_dir = analyze_story_canon(args.source_register, args.parsed_dir, dated_root, run_date)
    print(f"Story-canon analysis written -> {out_dir}")
    print(f"Pattern map -> {out_dir / 'pattern-map.json'}")
    for path in REFERENCE_FILES.values():
        print(f"Reference -> {path}")


if __name__ == "__main__":
    main()
