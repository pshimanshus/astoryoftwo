from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from pipeline.agentic.checks.prompt_constraints import REQUIRED_FRAGMENTS
from pipeline.agentic.workflow_doctor import inspect_carousel_package
from pipeline.stages.carousel_format_contract import write_format_contract
from pipeline.stages.codex_builtin_image_generation import (
    RETRY_GATE_INPUT_FILES,
    RETRY_HANDOFF_SCHEMA_VERSION,
    build_compiled_prompt_handoff,
    image_set_sha256,
    sha256_binding,
)


def write_json(path: Path, payload: dict) -> None:
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def issue_codes(package: Path) -> set[str]:
    return {issue.code for issue in inspect_carousel_package(package).issues}


def _canonical_fingerprint(payload: dict) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return sha256_binding(encoded)


def _file_binding(package: Path, relative_path: str) -> dict[str, str]:
    return {
        "relative_path": relative_path,
        "sha256": sha256_binding((package / relative_path).read_bytes()),
    }


def write_retry_ready_failed_proof(
    package: Path,
    *,
    attempt_count: int = 1,
) -> dict:
    package.mkdir()
    write_format_contract(package, ["instagram_post"], source="test")
    write_json(
        package / "prompt-pack.json",
        {"slides": [{"slide": 1, "text": "Proof", "prompt": "Repair prompt."}]},
    )
    write_json(
        package / "slides.json",
        {"slides": [{"slide": 1, "copy": "Proof", "visual": "Repair proof."}]},
    )
    for filename in RETRY_GATE_INPUT_FILES:
        path = package / filename
        if not path.exists():
            write_json(path, {})

    prompt_dir = package / "codex-image-prompts" / "instagram-post"
    prompt_dir.mkdir(parents=True)
    (prompt_dir / "slide-01.prompt.txt").write_text(
        "\n".join((*REQUIRED_FRAGMENTS, "Proof")),
        encoding="utf-8",
    )
    (prompt_dir / "slide-01.md").write_text("Proof handoff.", encoding="utf-8")
    compiled_handoff = build_compiled_prompt_handoff(
        package,
        slide_numbers=[1],
        output_formats=["instagram_post"],
    )

    backup_dir = (
        package
        / ".internal"
        / "codex-image-prompts-previous"
        / "attempt-01"
        / "instagram-post"
    )
    backup_dir.mkdir(parents=True)
    (backup_dir / "slide-01.prompt.txt").write_text(
        "Prior proof prompt.",
        encoding="utf-8",
    )
    (backup_dir / "slide-01.md").write_text("Prior proof handoff.", encoding="utf-8")
    write_json(package / "visual-qa.json", {"schema_version": "1.0", "status": "FAIL"})

    image_set_hash = "sha256:" + ("a" * 64)
    attempts = [
        {
            "attempt": index + 1,
            "retry_count": index,
            "image_set_sha256": image_set_hash,
            "status": "QA_FAILED",
            "qa_issues": ["anatomy failure"],
        }
        for index in range(attempt_count)
    ]
    ledger_path = package / ".internal" / "visual-qa-attempts.json"
    ledger_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(
        ledger_path,
        {
            "schema_version": "1.0",
            "max_retries": 2,
            "attempts": attempts,
        },
    )

    backup_root = ".internal/codex-image-prompts-previous/attempt-01"
    attestation = {
        "schema_version": RETRY_HANDOFF_SCHEMA_VERSION,
        "source_status": "GENERATED_QUARANTINED",
        "proof_slide": 1,
        "requested_formats": ["instagram_post"],
        "failed_image_set_sha256": image_set_hash,
        "failed_attempt": attempts[-1],
        "visual_qa_binding": _file_binding(package, "visual-qa.json"),
        "attempt_ledger_binding": _file_binding(
            package,
            ".internal/visual-qa-attempts.json",
        ),
        "gate_input_bindings": [
            _file_binding(package, relative_path)
            for relative_path in RETRY_GATE_INPUT_FILES
        ],
        "previous_handoff_set_fingerprint": "sha256:" + ("b" * 64),
        "replacement_handoff_set_fingerprint": compiled_handoff[
            "handoff_set_fingerprint"
        ],
        "previous_prompt_backup_dir": backup_root,
        "previous_prompt_files": [
            _file_binding(
                package,
                f"{backup_root}/instagram-post/slide-01.prompt.txt",
            ),
            _file_binding(
                package,
                f"{backup_root}/instagram-post/slide-01.md",
            ),
        ],
        "next_retry_count": attempt_count,
    }
    attestation["attestation_fingerprint"] = _canonical_fingerprint(attestation)
    state = {
        "status": "GENERATED_QUARANTINED",
        "proof_state": "GENERATED_QUARANTINED",
        "proof_only": True,
        "requested_proof_slide": 1,
        "requested_formats": ["instagram_post"],
        "slide_count": 1,
        "retry_count": attempt_count - 1,
        "image_set_sha256": image_set_hash,
        "visual_qa_issues": ["anatomy failure"],
        "slides": [{"slide": 1}],
        "compiled_prompt_handoff": compiled_handoff,
        "retry_prompt_handoff_attestation": attestation,
    }
    write_json(package / "image-generation.json", state)
    write_json(package / "final-images.json", state)
    return state


def write_v2_qa(
    package: Path,
    *,
    proof_state: str,
    creator_approved: bool = False,
    reviews_pass: bool = True,
    continue_batch: bool = False,
    retry_count: int | None = None,
) -> Path:
    asset = (
        package
        / ".internal"
        / "visual-quarantine"
        / "attempt-01"
        / "final"
        / "slide-01.png"
    )
    asset.parent.mkdir(parents=True)
    Image.new("RGB", (1080, 1440), "ivory").save(asset)
    import hashlib

    digest = hashlib.sha256(asset.read_bytes()).hexdigest()
    native_outputs = {
        "instagram_post": {
            "path": ".internal/visual-quarantine/attempt-01/final/slide-01.png",
            "sha256": digest,
            "width": 1080,
            "height": 1440,
        }
    }
    set_hash = image_set_sha256(
        [{"slide": 1, "native_outputs": native_outputs}]
    )
    visible_hands = [
        {
            "owner": owner,
            "side": side,
            "action": "rests naturally beside the body",
            "story_required": True,
            "attachment_visible": True,
            "attachment_evidence": "wrist continues visibly into the matching sleeve",
            "contact_object": None,
            "contact_geometry_pass": True,
            "occlusion_evidence": "open air clearly separates the hand from nearby objects",
            "solid_object_intersection": False,
            "edge_entry_unexplained": False,
        }
        for owner, side in (("Aachu", "left"), ("Aachu", "right"), ("Zuv", "left"), ("Zuv", "right"))
    ]
    qa = {
        "schema_version": "2.1",
        "status": "PASS" if reviews_pass else "FAIL",
        "proof_state": proof_state,
        "image_set_sha256": set_hash,
        "continue_batch": continue_batch,
        "reviews": {
            "anatomy_entity_spatial_identity": {
                "reviewer_id": "anatomy-reviewer",
                "pass": reviews_pass,
                "evidence": ["Every visible hand is owned and attached."],
            },
            "storytelling_richness_text_style": {
                "reviewer_id": "story-reviewer",
                "pass": reviews_pass,
                "evidence": ["Foreground, midground, background, and causal detail are readable."],
            },
        },
        "slides": [{"slide": 1, "native_outputs": native_outputs}],
        "checks": {
            "anatomy_inventory": {
                "slides": [
                    {
                        "slide": 1,
                        "formats": {
                            "instagram_post": {
                                "source_asset": native_outputs["instagram_post"],
                                "expected_arms": 4,
                                "observed_arms": 4,
                                "expected_hands": 4,
                                "observed_hands": 4,
                                "visible_hands": visible_hands,
                                "unexpected_limbs": [],
                                "duplicated_limbs": [],
                                "malformed_fingers": False,
                            }
                        },
                    }
                ]
            },
            "scene_entity_integrity": {
                "slides": [
                    {
                        "slide": 1,
                        "formats": {
                            "instagram_post": {
                                "source_asset": native_outputs["instagram_post"],
                                "expected_people": 2,
                                "observed_people": 2,
                                "expected_arms": 4,
                                "observed_arms": 4,
                                "expected_hands": 4,
                                "observed_hands": 4,
                                "unexpected_entities": [],
                                "unexpected_limbs": [],
                                "duplicated_limbs": [],
                                "evidence": "Only Aachu and Zuv are visible, with four attributable arms and hands.",
                            }
                        },
                    }
                ]
            },
            "spatial_topology": {
                "slides": [
                    {
                        "slide": 1,
                        "observed_people": 2,
                        "evidence_views": {
                            "full_frame": "Both silhouettes remain distinct.",
                            "person_object_crop": "Body and door boundaries remain separate.",
                            "focal_detail": "Hands and nearby objects have clear overlap."
                        },
                        "environment_planes": [{"object": "door", "depth_order": "behind both people", "boundary_continuous": True}],
                        "people": [
                            {
                                "person": "Aachu",
                                "silhouette_traceable": True,
                                "ambiguous_regions": [],
                                "body_regions": [
                                    {
                                        "region": "head neck shoulders and torso",
                                        "near_object": "interior wall",
                                        "expected_relation": "in_front_of",
                                        "observed_relation": "in_front_of",
                                        "boundary_continuous": True,
                                        "occlusion_order_clear": True,
                                        "solid_object_intersection": False,
                                        "morph_or_merge": False,
                                        "evidence": "Aachu's full silhouette remains separate from the interior wall."
                                    }
                                ]
                            },
                            {
                                "person": "Zuv",
                                "silhouette_traceable": True,
                                "ambiguous_regions": [],
                                "body_regions": [
                                    {
                                        "region": "head neck shoulders back and torso",
                                        "near_object": "door",
                                        "expected_relation": "in_front_of",
                                        "observed_relation": "in_front_of",
                                        "boundary_continuous": True,
                                        "occlusion_order_clear": True,
                                        "solid_object_intersection": False,
                                        "morph_or_merge": False,
                                        "evidence": "Zuv's shirt contour remains continuous and separate in front of the door."
                                    }
                                ]
                            }
                        ],
                        "ambiguous_regions": [],
                        "unresolved_intersections": []
                    }
                ]
            },
            "visual_richness": {
                "slides": [
                    {
                        "slide": 1,
                        "formats": {
                            "instagram_post": {
                                "source_asset": native_outputs["instagram_post"],
                                "foreground": "The door lock anchors the foreground evidence.",
                                "midground": "The couple's repair action is fully readable.",
                                "background": "The lived-in landing establishes location and consequence.",
                                "focal_action": "They inspect the repaired lock together.",
                                "story_details": ["repair kit", "snapped key half"],
                                "cause_effect": "The broken key caused the repair now visible.",
                                "posed_portrait": False,
                                "decorative_clutter": False,
                            }
                        },
                    }
                ]
            },
        },
    }
    if retry_count is not None:
        qa["retry_policy"] = {"retry_count": retry_count, "max_auto_retries": 2}
    write_json(package / "visual-qa.json", qa)
    if creator_approved:
        write_json(
            package / "creator-proof-approval.json",
            {
                "status": "APPROVED",
                "approved": True,
                "image_set_sha256": set_hash,
                "approved_by": "creator",
                "evidence": "Creator approved the exact QA-passed proof.",
            },
        )
    return asset


def test_generated_proof_without_schema_v2_qa_is_blocked(tmp_path: Path) -> None:
    package = tmp_path / "missing-qa"
    package.mkdir()
    write_json(package / "image-generation.json", {"proof_state": "GENERATED_QUARANTINED"})

    assert "generated_proof_without_structured_qa_v2" in issue_codes(package)


def test_quarantined_proof_cannot_claim_batch_continuation(tmp_path: Path) -> None:
    package = tmp_path / "quarantine-batch"
    package.mkdir()
    write_v2_qa(package, proof_state="GENERATED_QUARANTINED", continue_batch=True)

    codes = issue_codes(package)
    assert "quarantined_proof_claims_continuation" in codes
    assert "batch_allowed_without_correct_state" in codes


def test_qa_pass_candidate_requires_creator_approval(tmp_path: Path) -> None:
    package = tmp_path / "qa-pass"
    package.mkdir()
    write_v2_qa(package, proof_state="QA_PASS_CANDIDATE")

    assert "qa_pass_without_creator_approval" in issue_codes(package)


def test_batch_flag_requires_batch_allowed_state(tmp_path: Path) -> None:
    package = tmp_path / "wrong-batch-state"
    package.mkdir()
    write_v2_qa(
        package,
        proof_state="CREATOR_APPROVED_PROOF",
        creator_approved=True,
        continue_batch=True,
    )

    assert "batch_allowed_without_correct_state" in issue_codes(package)


def test_batch_allowed_state_passes_lifecycle_gates(tmp_path: Path) -> None:
    package = tmp_path / "batch-allowed"
    package.mkdir()
    write_v2_qa(
        package,
        proof_state="BATCH_ALLOWED",
        creator_approved=True,
        continue_batch=True,
    )

    codes = issue_codes(package)
    assert "batch_allowed_without_correct_state" not in codes
    assert "batch_state_without_required_gates" not in codes
    assert "qa_pass_without_creator_approval" not in codes


def test_changed_proof_invalidates_recorded_qa_hash(tmp_path: Path) -> None:
    package = tmp_path / "stale-hash"
    package.mkdir()
    asset = write_v2_qa(package, proof_state="QA_PASS_CANDIDATE")
    asset.write_bytes(b"edited-after-review")

    assert "visual_qa_asset_hash_mismatch" in issue_codes(package)


def test_doctor_rejects_unowned_unattached_door_hand(tmp_path: Path) -> None:
    package = tmp_path / "door-hand"
    package.mkdir()
    write_v2_qa(package, proof_state="QA_PASS_CANDIDATE")
    qa_path = package / "visual-qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    anatomy = qa["checks"]["anatomy_inventory"]["slides"][0]["formats"]["instagram_post"]
    anatomy["observed_hands"] = 5
    anatomy["visible_hands"].append(
        {
            "owner": "",
            "side": "right",
            "action": "appears on the door edge",
            "story_required": False,
            "attachment_visible": False,
            "attachment_evidence": "",
            "contact_object": "door",
            "contact_geometry_pass": False,
            "occlusion_evidence": "",
            "solid_object_intersection": True,
            "edge_entry_unexplained": True,
        }
    )
    write_json(qa_path, qa)

    assert "generated_proof_without_structured_qa_v2" in issue_codes(package)


def test_doctor_rejects_sparse_posed_portrait(tmp_path: Path) -> None:
    package = tmp_path / "sparse-proof"
    package.mkdir()
    write_v2_qa(package, proof_state="QA_PASS_CANDIDATE")
    qa_path = package / "visual-qa.json"
    qa = json.loads(qa_path.read_text(encoding="utf-8"))
    richness = qa["checks"]["visual_richness"]["slides"][0]["formats"]["instagram_post"]
    richness["story_details"] = []
    richness["posed_portrait"] = True
    richness["cause_effect"] = ""
    write_json(qa_path, qa)

    assert "generated_proof_without_structured_qa_v2" in issue_codes(package)


def test_doctor_rejects_missing_reviewed_asset(tmp_path: Path) -> None:
    package = tmp_path / "missing-reviewed-asset"
    package.mkdir()
    asset = write_v2_qa(package, proof_state="QA_PASS_CANDIDATE")
    asset.unlink()

    assert "visual_qa_asset_hash_mismatch" in issue_codes(package)


def test_copied_creator_approval_is_rejected_after_image_set_changes(tmp_path: Path) -> None:
    package = tmp_path / "stale-creator-approval"
    package.mkdir()
    write_v2_qa(
        package,
        proof_state="BATCH_ALLOWED",
        creator_approved=True,
        continue_batch=True,
    )
    approval_path = package / "creator-proof-approval.json"
    approval = json.loads(approval_path.read_text(encoding="utf-8"))
    approval["image_set_sha256"] = "0" * 64
    write_json(approval_path, approval)

    codes = issue_codes(package)
    assert "creator_approval_asset_hash_mismatch" in codes
    assert "batch_state_without_required_gates" in codes


def test_blocked_visual_qa_is_terminal_after_two_retries(tmp_path: Path) -> None:
    package = tmp_path / "retry-exhausted"
    package.mkdir()
    write_v2_qa(
        package,
        proof_state="BLOCKED_VISUAL_QA",
        reviews_pass=False,
        retry_count=2,
    )

    codes = issue_codes(package)
    assert "blocked_visual_qa_terminal" in codes
    assert "blocked_visual_qa_retry_metadata_invalid" not in codes
    assert "blocked_visual_qa_claims_publishable" not in codes


def test_blocked_visual_qa_cannot_claim_publishable(tmp_path: Path) -> None:
    package = tmp_path / "blocked-but-publishable"
    package.mkdir()
    write_v2_qa(
        package,
        proof_state="BLOCKED_VISUAL_QA",
        reviews_pass=False,
        retry_count=2,
    )
    write_json(package / "final-images.json", {"publishable": True})

    assert "blocked_visual_qa_claims_publishable" in issue_codes(package)


def test_ordinary_failed_proof_without_retry_attestation_remains_blocked(
    tmp_path: Path,
) -> None:
    package = tmp_path / "ordinary-failed-proof"
    state = write_retry_ready_failed_proof(package)
    state.pop("retry_prompt_handoff_attestation")
    write_json(package / "image-generation.json", state)
    write_json(package / "final-images.json", state)

    assert "generated_proof_without_structured_qa_v2" in issue_codes(package)


def test_attested_retry_ready_failed_proof_clears_only_qa_v2_blocker(
    tmp_path: Path,
) -> None:
    package = tmp_path / "retry-ready-failed-proof"
    write_retry_ready_failed_proof(package)

    assert "generated_proof_without_structured_qa_v2" not in issue_codes(package)


@pytest.mark.parametrize("tamper", ["attestation", "handoff"])
def test_tampered_retry_ready_evidence_remains_blocked(
    tmp_path: Path,
    tamper: str,
) -> None:
    package = tmp_path / f"tampered-{tamper}"
    state = write_retry_ready_failed_proof(package)
    if tamper == "attestation":
        state["retry_prompt_handoff_attestation"]["proof_slide"] = 2
        write_json(package / "image-generation.json", state)
        write_json(package / "final-images.json", state)
    else:
        prompt = (
            package
            / "codex-image-prompts"
            / "instagram-post"
            / "slide-01.prompt.txt"
        )
        prompt.write_text(prompt.read_text(encoding="utf-8") + "\ntampered", encoding="utf-8")

    assert "generated_proof_without_structured_qa_v2" in issue_codes(package)


def test_attested_failed_proof_with_exhausted_retries_remains_blocked(
    tmp_path: Path,
) -> None:
    package = tmp_path / "retry-exhausted-failed-proof"
    write_retry_ready_failed_proof(package, attempt_count=3)

    assert "generated_proof_without_structured_qa_v2" in issue_codes(package)
