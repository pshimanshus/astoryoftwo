from __future__ import annotations

import json
import os
from pathlib import Path

_REPO = Path(__file__).resolve().parents[2]
_WINNER_BANK = _REPO / "references/text-style/winner-bank/winner_bank.json"
_CONTRACTS = _REPO / ".agents/skills/astory/references"


def load_winner_bank(path: Path | None = None) -> list[dict]:
    return json.loads(Path(path or _WINNER_BANK).read_text())


def bank_summary(records: list[dict], limit: int = 40) -> list[dict]:
    out = []
    for r in records[:limit]:
        out.append({
            "caption": (r.get("caption") or "")[:600],
            "slide_count": r.get("childCount") or len(r.get("childTypes") or []),
            "comments": r.get("commentsCount") or 0,
            "send_proxy": r.get("commentSendProxy") or 0,
        })
    return out


def load_contract(name: str) -> str:
    return (_CONTRACTS / f"{name}.md").read_text()


def house_style_ref_paths() -> list[Path]:
    # Configurable via ASTORY_STYLE_REFS (os.pathsep-separated). Empty + non-raising by default.
    raw = os.environ.get("ASTORY_STYLE_REFS", "").strip()
    if not raw:
        return []
    return [Path(p) for p in raw.split(os.pathsep) if Path(p).exists()]
