from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCENARIOS = ROOT / "config/evals/carousel-live-smoke-scenarios.json"
REPORT = ROOT / "config/evals/carousel-live-smoke-report.json"


def test_live_smoke_is_explicit_untracked_and_tool_truthful() -> None:
    contract = json.loads(SCENARIOS.read_text(encoding="utf-8"))

    assert contract["schema_version"] == "carousel-live-smoke/v1"
    assert contract["opt_in_only"] is True
    assert contract["asset_policy"] == {
        "output_location": "untracked temporary directory outside output/carousels",
        "commit_generated_assets": False,
        "commit_identity_images": False,
        "unavailable_tool_result": "BLOCKED/NOT_RUN",
    }
    assert contract["attempt_policy"] == {
        "maximum_attempts_per_visual_premise": 2,
        "minimum_first_attempt_passes": 2,
        "all_scenarios_must_pass_hard_gates": True,
    }
    assert contract["attachment_contract"] == {
        "observed_runtime_boundary": 5,
        "boundary_source": "current built-in Codex image-generation runtime smoke; not a published platform limit",
        "identity_attachments": 4,
        "identity_source": "config/references/identity/_dossier/identity-dossier.json.selected_generation_bundle",
        "style_board_attachments": 1,
        "style_board_source": "config/references/style-lock/observational-intimacy-premium/contact-sheet.png",
        "forbid_individual_style_slides_in_addition": True,
        "forbid_silent_identity_omission": True,
    }
    assert contract["source_size_contract"] == {
        "boundary_source": "current built-in Codex image-generation runtime smoke; not a published platform guarantee",
        "prompt_target": "1080x1440; native 3:4",
        "instagram_post": {
            "accepted_exact_ratio": "3:4",
            "minimum_source": [1080, 1440],
            "maximum_source": [1440, 1920],
            "final": [1080, 1440],
            "transform": "at most one proportional downsample",
        },
        "reels_stories_source": [1080, 1920],
        "square_source": [1080, 1080],
        "forbidden": [
            "crop",
            "pad",
            "stretch",
            "upscale",
            "wrong_ratio",
            "second_resample",
        ],
        "binding": "retain untouched source hash/dimensions and reuse approved normalized proof bytes",
    }


def test_live_smoke_has_three_distinct_non_duvet_risks_and_corrupt_controls() -> None:
    contract = json.loads(SCENARIOS.read_text(encoding="utf-8"))
    scenarios = contract["scenarios"]

    assert len(scenarios) == 3
    assert len({scenario["id"] for scenario in scenarios}) == 3
    joined = " ".join(json.dumps(scenario).casefold() for scenario in scenarios)
    assert "duvet" not in joined
    for phrase in (
        "shared-object hands",
        "asymmetric action",
        "occlusion",
        "multiline exact text",
    ):
        assert phrase in joined
    assert contract["corrupted_controls"] == [
        "sha256_mismatch",
        "exact_text_mismatch",
        "native_dimension_mismatch",
    ]
    assert all(scenario["format"] == "instagram_post" for scenario in scenarios)
    assert all(scenario["exact_text"] for scenario in scenarios)
    assert all(scenario["physical_action"] for scenario in scenarios)


def test_live_smoke_report_is_complete_truthful_and_asset_free() -> None:
    report = json.loads(REPORT.read_text(encoding="utf-8"))

    assert report["schema_version"] == "carousel-live-smoke-report/v1"
    assert report["scenario_contract"] == SCENARIOS.relative_to(ROOT).as_posix()
    assert report["summary"] == {
        "result": "PASS",
        "scenario_passes": 3,
        "first_attempt_passes": 2,
        "false_passes_in_corruption_controls": 0,
    }
    scenarios = report["scenarios"]
    assert [scenario["id"] for scenario in scenarios] == [
        "shared-plain-frame-hold",
        "box-seal-key-glance",
        "rug-through-doorway",
    ]
    assert all(scenario["result"] == "PASS" for scenario in scenarios)
    assert sum(scenario["first_attempt_pass"] for scenario in scenarios) >= 2
    assert all(1 <= scenario["attempts"] <= 2 for scenario in scenarios)
    assert all(scenario["attachments"] == {"identity": 4, "style_board": 1} for scenario in scenarios)
    assert all(scenario["normalized_dimensions"] == [1080, 1440] for scenario in scenarios)
    assert all(scenario["raw_dimensions"] == [1086, 1448] for scenario in scenarios)
    for scenario in scenarios:
        for key in ("raw_sha256", "normalized_sha256", "references_sha256"):
            value = scenario[key].removeprefix("sha256:")
            assert len(value) == 64
            assert set(value) <= set("0123456789abcdef")
    assert report["corruption_controls"]["result"] == "PASS"
    assert report["corruption_controls"]["false_passes"] == 0
    assert {control["id"] for control in report["corruption_controls"]["controls"]} == {
        "sha256_mismatch",
        "exact_text_mismatch",
        "native_dimension_mismatch",
    }
    assert all(control["result"] == "REJECTED" for control in report["corruption_controls"]["controls"])
    serialized = json.dumps(report).casefold()
    assert "/private/tmp/" not in serialized
    assert "/users/" not in serialized
    assert "identity-dossier" not in serialized
    assert ".png" not in serialized
