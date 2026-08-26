from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import write_format_contract


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def write_base_package(path: Path, *, status: str) -> None:
    path.mkdir()
    write_format_contract(path, ["instagram_post"], source="test")
    identity = path / "refs" / "couple.png"
    identity.parent.mkdir(parents=True)
    Image.new("RGB", (64, 64), "ivory").save(identity)
    write_json(path / "slides.json", {"slides": [{"slide": 1, "copy": "Exact copy."}]})
    write_json(
        path / "prompt-pack.json",
        {
            "identity_reference_images": ["refs/couple.png"],
            "slides": [{"slide": 1, "text": "Exact copy."}],
        },
    )
    write_json(
        path / "generation-state.json",
        {"status": status, "requested_formats": ["instagram_post"]},
    )


def test_carousel_doctor_cli_outputs_json(tmp_path: Path) -> None:
    package = tmp_path / "handoff"
    write_base_package(package, status="HANDOFF_READY")

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
    write_base_package(package, status="BATCH_ALLOWED")

    result = subprocess.run(
        [sys.executable, "scripts/carousel_doctor.py", str(package), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )

    payload = json.loads(result.stdout)
    assert result.returncode == 2
    # Archived v2 BATCH_ALLOWED maps read-only to the canonical batch_ready
    # lifecycle state. The doctor reports the missing approval as a blocker; it
    # does not rewrite the package's public state merely because evidence is
    # incomplete.
    assert payload["state"]["name"] == "batch_ready"
    assert payload["state"]["blocked"] is True
    assert payload["state"]["publishable"] is False
    assert payload["highest_severity"] == "blocker"
    assert any(issue["code"] == "batch_without_approved_proof" for issue in payload["issues"])


def test_archived_publishable_claim_without_final_evidence_fails_closed(
    tmp_path: Path,
) -> None:
    package = tmp_path / "empty-publishable-claim"
    package.mkdir()
    write_json(
        package / "generation-state.json",
        {
            "schema_version": "carousel-generation-state/v2",
            "status": "publishable",
        },
    )
    before = {
        path.relative_to(package): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    }

    doctor = subprocess.run(
        [sys.executable, "scripts/carousel_doctor.py", str(package), "--json"],
        capture_output=True,
        text=True,
        timeout=30,
    )
    status = subprocess.run(
        [sys.executable, "scripts/carousel.py", "status", str(package)],
        capture_output=True,
        text=True,
        timeout=30,
    )

    doctor_payload = json.loads(doctor.stdout)
    status_payload = json.loads(status.stdout)
    assert doctor.returncode == 2
    assert doctor_payload["highest_severity"] == "blocker"
    assert doctor_payload["state"]["name"] == "final_qa_failed"
    assert status.returncode == 2
    assert status_payload["state"] == "final_qa_failed"
    assert status_payload["next_action"] == "lock_current_request_formats"
    assert {
        path.relative_to(package): path.read_bytes()
        for path in package.rglob("*")
        if path.is_file()
    } == before
