from __future__ import annotations

import json

from app.data_refs import bank_summary
from app.models import MatchResult
from app.providers.base import LLMProvider

_SYSTEM = (
    "You are the Story Director for A Story of Two, a hand-drawn romantic illustration brand. "
    "Given a couple's story and a bank of high-performing carousel patterns, pick the single "
    "pattern that best fits this story and design the slide beats. Respond ONLY as JSON: "
    '{"pattern_id": str, "slide_count": int, "beats": [str, ...]} where beats has exactly '
    "slide_count entries, each a one-line description of that slide's emotional beat."
)


def match_winner(story: str, creator: str, partner: str, relationship: str,
                 bank: list[dict], llm: LLMProvider, min_slides: int = 3,
                 max_slides: int = 5) -> MatchResult:
    summary = bank_summary(bank, limit=40)
    prompt = (
        f"Couple: {creator} & {partner} ({relationship}).\n"
        f"Their story: {story}\n\n"
        f"Winning patterns (JSON):\n{json.dumps(summary)}\n\n"
        f"Choose slide_count between {min_slides} and {max_slides}."
    )
    data = llm.reason_json(_SYSTEM, prompt)
    count = max(min_slides, min(max_slides, int(data.get("slide_count", min_slides))))
    beats = list(data.get("beats", []))[:count]
    beats += [""] * (count - len(beats))
    return MatchResult(pattern_id=str(data.get("pattern_id", "unknown")),
                       slide_count=count, beats=beats)
