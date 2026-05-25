from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("config") / "carousel_style_contract.json"


def load_style_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "north_star",
        "brandmark",
        "shared_style_prompt",
        "shared_negative_prompt",
        "typography",
        "characters",
        "content_lanes",
        "production_gate",
    ]
    missing = [key for key in required if not contract.get(key)]
    if missing:
        raise ValueError("Style contract missing required keys: " + ", ".join(missing))
    return contract


def build_character_bible(contract: dict[str, Any] | None = None) -> str:
    contract = contract or load_style_contract()
    aachu = contract["characters"]["aachu"]
    zuv = contract["characters"]["zuv"]
    aachu_cues = ", ".join(aachu["visual_cues"])
    zuv_cues = ", ".join(zuv["visual_cues"])
    return (
        f"Aachu/Anchal: {aachu_cues}; she is the {aachu['relationship_role']}. "
        f"Zuv/Himanshu: {zuv_cues}; he is the {zuv['relationship_role']}. "
        "Together: she is the spark, he is the steady flame; the humor must feel tender underneath."
    )
