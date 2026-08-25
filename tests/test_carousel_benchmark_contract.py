from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/benchmark_carousel.py"


def test_benchmark_help_and_budgets_are_public() -> None:
    text = SCRIPT.read_text(encoding="utf-8")

    for value in ("3.0", "10.0", "256.0", "1.0"):
        assert value in text
    assert "synthetic_orchestration_only" in text
    assert "TemporaryDirectory" in text


def test_benchmark_runs_one_disk_safe_synthetic_lifecycle() -> None:
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--runs", "1", "--json"],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads(result.stdout)
    assert report["schema_version"] == "carousel-benchmark/v1"
    assert report["status"] == "PASS"
    assert report["synthetic_orchestration_only"] is True
    assert report["issues"] == []
