import json
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "build_story_source_register.py"
REGISTER = ROOT / "config" / "references" / "story-selling-canon" / "source-register.json"


def write_register(path: Path, source: dict) -> None:
    path.write_text(json.dumps({"sources": [source]}, indent=2), encoding="utf-8")


def valid_source(**overrides: object) -> dict:
    source = {
        "id": "Gutenberg Pride And Prejudice",
        "type": "book",
        "title": "Pride and Prejudice",
        "creator": "Jane Austen",
        "source_url": "https://www.gutenberg.org/ebooks/1342",
        "license_status": "public_domain_us",
        "allowed_use": ["full_text_analysis", "short_quotes", "derived_patterns"],
        "ingestion_mode": "robot_harvest_or_manual_seed",
        "priority": 1,
        "confidence": 0.95,
        "scraped_at": "2026-05-18",
    }
    source.update(overrides)
    return source


def run_validator(path: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), "--source-register", str(path), *extra_args],
        cwd=ROOT,
        text=True,
        capture_output=True,
        check=False,
    )


def test_seed_register_is_valid_and_has_expected_source_mix():
    result = run_validator(REGISTER)

    assert result.returncode == 0, result.stderr
    assert "validated" in result.stdout

    register = json.loads(REGISTER.read_text(encoding="utf-8"))
    sources = register["sources"]
    assert 40 <= len(sources) <= 60
    assert {"book", "film", "craft_article", "story_selling_framework"} <= {
        source["type"] for source in sources
    }


def test_validator_reports_missing_required_safety_fields(tmp_path):
    for field in ("license_status", "allowed_use", "source_url", "confidence"):
        path = tmp_path / f"missing-{field}.json"
        source = valid_source()
        source.pop(field)
        write_register(path, source)

        result = run_validator(path)

        assert result.returncode == 1
        assert field in result.stderr


def test_validator_rejects_invalid_confidence_and_empty_allowed_use(tmp_path):
    path = tmp_path / "bad-values.json"
    source = valid_source(confidence=1.2, allowed_use=[])
    write_register(path, source)

    result = run_validator(path)

    assert result.returncode == 1
    assert "confidence" in result.stderr
    assert "allowed_use" in result.stderr


def test_validator_rejects_unknown_allowed_use_and_review_gated_full_text(tmp_path):
    path = tmp_path / "unsafe-use.json"
    source = valid_source(
        license_status="public_domain_us_review_before_bulk_use",
        allowed_use=["full_text_analysis", "mirror_full_article"],
    )
    write_register(path, source)

    result = run_validator(path)

    assert result.returncode == 1
    assert "full_text_analysis" in result.stderr
    assert "mirror_full_article" in result.stderr


def test_validator_normalizes_ids_when_write_is_enabled(tmp_path):
    path = tmp_path / "source-register.json"
    write_register(path, valid_source(id="Gutenberg: Pride & Prejudice!"))

    result = run_validator(path, "--write")

    assert result.returncode == 0, result.stderr
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["sources"][0]["id"] == "gutenberg-pride-prejudice"
