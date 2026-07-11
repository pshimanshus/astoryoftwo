from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_carousel_doctor_cli_outputs_json(tmp_path: Path) -> None:
    package = tmp_path / "handoff"
    package.mkdir()
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1}]})
    write_json(package / "image-generation.json", {"status": "handoff_ready"})
    write_json(package / "final-images.json", {"status": "handoff_ready", "publishable": False})

    result = subprocess.run(
        [sys.executable, "scripts/carousel_doctor.py", str(package), "--json"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    )

    payload = json.loads(result.stdout)
    assert payload["state"]["name"] == "handoff_ready"
    assert payload["highest_severity"] == "warning"
    assert payload["issues"][0]["code"] == "handoff_ready_not_publishable"


def test_carousel_doctor_cli_returns_nonzero_for_blocker(tmp_path: Path) -> None:
    package = tmp_path / "blocked"
    package.mkdir()
    (package / "raw-scene-row.md").write_text("STATUS: REJECTED\n", encoding="utf-8")
    write_json(package / "visual-plan-quality.json", {"status": "PASS", "can_generate": True})

    result = subprocess.run(
        [sys.executable, "scripts/carousel_doctor.py", str(package), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    assert payload["state"]["name"] == "blocked"
    assert payload["highest_severity"] == "blocker"
