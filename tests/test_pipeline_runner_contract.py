import importlib
import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def test_pipeline_runner_resolves_stage_selection():
    from pipeline.runner import resolve_stages

    assert [stage.name for stage in resolve_stages(stage="a3")] == ["a3"]
    assert [stage.name for stage in resolve_stages(from_stage="a3")] == ["a3", "a4", "a5"]


def test_advertised_stage_modules_expose_run_and_main():
    for module_name in (
        "pipeline.stages.a1_ingest",
        "pipeline.stages.a2_parser",
        "pipeline.stages.a3_analyzer",
        "pipeline.stages.a4_wiki",
        "pipeline.stages.a5_report",
    ):
        module = importlib.import_module(module_name)
        assert callable(module.run)
        assert callable(module.main)


def test_a2_parser_normalizes_apify_posts(tmp_path):
    from pipeline.stages.a2_parser import parse_raw_posts

    raw_path = tmp_path / "corpus" / "raw" / "2026-05-19-raw.json"
    raw_path.parent.mkdir(parents=True)
    raw_path.write_text(
        json.dumps(
            [
                {
                    "id": "abc123",
                    "shortCode": "DYJpjt9CQYY",
                    "caption": "me threatening to leave #marriedlife #kashmir",
                    "type": "Video",
                    "likesCount": 140730,
                    "commentsCount": 294,
                    "timestamp": "2026-05-04T12:00:00.000Z",
                    "url": "https://www.instagram.com/p/DYJpjt9CQYY/",
                    "videoViewCount": 1350000,
                }
            ]
        ),
        encoding="utf-8",
    )

    out_path = parse_raw_posts(raw_path, output_dir=tmp_path / "corpus" / "posts")
    posts = json.loads(out_path.read_text(encoding="utf-8"))

    assert out_path.name == "2026-05-19-posts.json"
    assert posts[0]["id"] == "abc123"
    assert posts[0]["shortcode"] == "DYJpjt9CQYY"
    assert posts[0]["post_type"] == "video"
    assert posts[0]["hashtags"] == ["marriedlife", "kashmir"]
    assert posts[0]["engagement"]["likes"] == 140730


def test_runner_dry_run_lists_requested_stage_without_executing():
    result = subprocess.run(
        [sys.executable, "-m", "pipeline.runner", "--stage", "a1", "--dry-run"],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0
    assert "a1 pipeline.stages.a1_ingest" in result.stdout
