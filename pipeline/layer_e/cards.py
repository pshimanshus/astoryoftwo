from __future__ import annotations

import json
import re
from pathlib import Path

from pipeline.layer_e.contracts import ConceptProcessCard


def _inline_value(chunk: str, key: str) -> str:
    match = re.search(rf"^- {re.escape(key)}:\s*(.+)$", chunk, flags=re.MULTILINE)
    return re.sub(r"\s+", " ", match.group(1)).strip() if match else ""


def _cards_from_bank(path: Path) -> list[ConceptProcessCard]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    cards = payload.get("processes", []) if isinstance(payload, dict) else []
    return [
        ConceptProcessCard(
            id=str(item.get("id", "")),
            title=str(item.get("title", "")),
            best_for=[str(value) for value in item.get("best_for", [])],
            source_patterns=[str(value) for value in item.get("source_patterns", [])],
            confidence=float(item.get("confidence", 0.5)),
            process=[str(value) for value in item.get("process", [])],
            a_story_of_two_filter=str(item.get("a_story_of_two_filter", "")),
        )
        for item in cards
        if item.get("id") and item.get("title")
    ]


def _cards_from_markdown(path: Path) -> list[ConceptProcessCard]:
    text = path.read_text(encoding="utf-8")
    cards: list[ConceptProcessCard] = []
    for chunk in re.split(r"(?=^## Card \d+ - )", text, flags=re.MULTILINE):
        heading = re.search(r"^## Card (\d+) - (.+)$", chunk, flags=re.MULTILINE)
        if not heading:
            continue
        source_section = chunk.split("- confidence:", 1)[0]
        confidence_match = re.search(r"^- confidence:\s*([0-9.]+)\s*$", chunk, flags=re.MULTILINE)
        cards.append(
            ConceptProcessCard(
                id=f"card-{int(heading.group(1)):02d}",
                title=heading.group(2).strip(),
                best_for=[item.strip() for item in _inline_value(chunk, "best_for").split(",") if item.strip()],
                source_patterns=re.findall(r"`([^`]+)`", source_section),
                confidence=float(confidence_match.group(1)) if confidence_match else 0.5,
                process=re.findall(r"^\s+\d+\.\s+(.+?)\s*$", chunk, flags=re.MULTILINE),
                a_story_of_two_filter=_inline_value(chunk, "a_story_of_two_filter"),
            )
        )
    return cards


def load_concept_process_cards(root: Path, concept_process_bank: Path | None = None) -> list[ConceptProcessCard]:
    if concept_process_bank and concept_process_bank.exists():
        cards = _cards_from_bank(concept_process_bank)
        if cards:
            return cards
    path = root / "config" / "references" / "story-selling-canon" / "concept-process-cards.md"
    return _cards_from_markdown(path)
