#!/usr/bin/env python3
"""CLI wrapper for repo-wide wiki/memory health diagnostics."""

from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from pipeline.stages.wiki_health import main  # noqa: E402


if __name__ == "__main__":
    raise SystemExit(main())
