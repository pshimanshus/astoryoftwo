from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import FORMAT_CONTRACT_FILENAME
from tests.helpers.visual_story import (
    write_passing_director_storyboard,
    write_passing_story_readability,
)


SCRIPT = (
    Path(__file__).resolve().parents[1]
    / ".agents"
    / "skills"
    / "a-story-direct-visual-story"
    / "scripts"
    / "check_visual_story.py"
)


def _run_checker(package: Path, phase: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "--carousel-dir",
            str(package),
            "--phase",
            phase,
            "--compact",
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )


def test_pre_checker_requires_persisted_current_format_contract(
    tmp_path: Path,
) -> None:
    package = tmp_path / "missing-format-lock"
    package.mkdir()
    write_passing_director_storyboard(package)
    (package / FORMAT_CONTRACT_FILENAME).unlink()

    result = _run_checker(package, "pre")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["pass"] is False
    assert any("Missing required current-request format contract" in issue for issue in payload["issues"])


def test_post_checker_revalidates_event_a_after_slide_edit(tmp_path: Path) -> None:
    package = tmp_path / "stale-post-only"
    package.mkdir()
    write_passing_director_storyboard(package)
    final = package / "final" / "slide-01.png"
    final.parent.mkdir()
    Image.new("RGB", (1080, 1440), (241, 232, 217)).save(final)
    write_passing_story_readability(package)

    slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides[0]["copy"] = "Edited after Event A and Event B passed."
    (package / "slides.json").write_text(json.dumps(slides), encoding="utf-8")

    result = _run_checker(package, "post")
    payload = json.loads(result.stdout)

    assert result.returncode == 1
    assert payload["checks"]["pre_generation_director_storyboard"]["pass"] is False
    assert any("source_fingerprint is stale" in issue for issue in payload["issues"])
