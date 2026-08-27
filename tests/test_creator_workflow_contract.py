from __future__ import annotations

import json
from pathlib import Path

import pytest

from pipeline.agentic.context_loader import assemble_context_pack
from pipeline.stages.carousel_lanes import (
    discover_identity_images,
    select_identity_reference_bundle,
)


ROOT = Path(__file__).resolve().parents[1]

PUBLIC_STATES = [
    "draft",
    "blocked",
    "handoff_ready",
    "proof_qa_required",
    "proof_failed",
    "awaiting_creator_proof_approval",
    "batch_ready",
    "final_qa_required",
    "final_qa_failed",
    "publish_ready",
]


def _read(relative: str) -> str:
    return (ROOT / relative).read_text(encoding="utf-8")


def _flat(relative: str) -> str:
    return " ".join(_read(relative).split())


def test_default_carousel_system_is_exactly_four_gates_with_no_agents() -> None:
    carousel = json.loads(_read("config/skill-systems.json"))["systems"]["carousel_jam"]

    assert carousel["gates"] == [
        "concept_lock",
        "copy_format_lock",
        "proof_pixel_qa_creator_approval",
        "final_package_qa",
    ]
    assert carousel["agents"] == []
    assert carousel["default_agent_count"] == 0
    assert carousel["public_states"] == PUBLIC_STATES
    assert carousel["artifacts"] == [
        "creative-context.json",
        "format-contract.json",
        "slides.json",
        "prompt-pack.json",
        "proof-qa.json",
        "final-images.json",
        "visual-qa.json",
        "final-audit.json",
    ]


def test_style_contract_is_small_and_contains_no_retired_workflow_policy() -> None:
    path = ROOT / "config" / "carousel_style_contract.json"
    contract = json.loads(path.read_text(encoding="utf-8"))

    assert path.stat().st_size < 8_000
    assert contract["style_reference_attachment_limit"] == 1
    assert contract["style_references"] == [
        "config/references/style-lock/observational-intimacy-premium/contact-sheet.png"
    ]
    assert "concept_selection_policy" not in contract
    assert "stage_scene_policy" not in contract
    assert "golden_theme_contract" not in contract
    assert "model_native_master_prompt" not in contract
    assert contract["production_gate"]["approved_creation_path"].startswith(
        "scripts/carousel.py"
    )


def test_carousel_skill_keeps_the_creator_first_hot_path() -> None:
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "creator asks to jam from scratch",
        "strongest human draft",
        "quiet seasoning",
        "one sentence describing a visible physical event",
        "at most two total semantic attempts",
        "Do not generate the remaining deck before proof QA and creator approval",
        "one-command workflow",
    ):
        assert fragment in skill


def test_story_hook_preserves_change_receipt_and_creator_structure() -> None:
    hook = _flat(".agents/skills/a-story-storytelling-hook/SKILL.md")

    assert "before -> pressure or choice -> after" in hook
    assert "action, reaction, object state, gaze, distance, silence, or consequence" in hook
    assert "Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff" in hook
    assert "Deepening, Conflict, and Turn may each span multiple slides" in hook
    assert "$a-story-carousel-jam" in hook
    assert "$a-story-direct-visual-story" in hook


def test_story_hook_lifecycle_is_conversational_only() -> None:
    hook = _flat(".agents/skills/a-story-storytelling-hook/SKILL.md")

    for phase in ("Activate:", "Refresh:", "Resume:", "Close:"):
        assert phase in hook
    for forbidden in ("state file", "daemon", "agent room"):
        assert forbidden in hook


def test_compact_creator_pass_keeps_recognition_change_receipt_and_send() -> None:
    stack = _flat("config/skills/creator-skill-stack.md")

    for label in ("Stop:", "Mirror:", "Change:", "Receipt:", "Next:", "Send:"):
        assert label in stack
    assert "this is me" in stack
    assert "the creator already rejected the lane" in stack
    assert "$a-story-instagram-idea-loop" in stack


def test_identity_references_cover_the_whole_person_and_block_batching() -> None:
    surfaces = "\n".join(
        _flat(path)
        for path in (
            ".agents/skills/a-story-carousel-jam/SKILL.md",
            "config/skills/carousel-jam-runtime-context.md",
            "config/skills/carousel-jam-autopilot.md",
            "config/skills/illustration-carousel-framework.md",
        )
    )

    for fragment in (
        "actual Aachu/Zuv identity images",
        "face, hair, height",
        "proportions",
        "posture",
        "expression",
        "wardrobe",
        "No identity eval means no next slide",
    ):
        assert fragment in surfaces
    assert "Text-only identity descriptions are blocked" in surfaces


def test_generated_character_charts_never_replace_actual_photo_inputs() -> None:
    surfaces = "\n".join(
        _flat(path)
        for path in (
            "config/carousel_style_contract.json",
            "config/references/a-story-illustration-master-prompt.md",
            "memory/semantic/visual-director-intelligence.md",
        )
    ).lower()

    assert "actual photograph" in surfaces
    assert "generated character chart" in surfaces
    assert "supplemental" in surfaces
    assert "sole face source" in surfaces


def test_identity_attachment_bundle_rejects_generated_charts(tmp_path: Path) -> None:
    photo = tmp_path / "aachu" / "aachu-real-photo.jpg"
    chart = tmp_path / "character-models" / "aachu-face-turnaround.png"
    for path in (photo, chart):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")

    with pytest.raises(ValueError, match="cannot occupy"):
        select_identity_reference_bundle([photo, chart], explicit=True)


def test_auto_identity_discovery_uses_exact_four_actual_photos(tmp_path: Path) -> None:
    actual = [
        tmp_path / "config/references/identity/aachu/aachu.jpg",
        tmp_path / "config/references/identity/zuv/zuv.jpg",
        tmp_path / "config/references/identity/together/together-face.jpg",
        tmp_path / "config/references/identity/together/together-body.jpg",
    ]
    chart = tmp_path / "config/references/character-models/aachu-face-turnaround.png"
    for path in [*actual, chart]:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"image")
    dossier = tmp_path / "config/references/identity/_dossier/identity-dossier.json"
    dossier.parent.mkdir(parents=True, exist_ok=True)
    dossier.write_text(
        json.dumps(
            {
                "selected_generation_bundle": [
                    *(str(path.relative_to(tmp_path)) for path in actual),
                    str(chart.relative_to(tmp_path)),
                ]
            }
        ),
        encoding="utf-8",
    )

    assert discover_identity_images(tmp_path) == actual


def test_format_lock_defaults_to_post_and_never_manufactures_derivatives() -> None:
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    framework = _flat("config/skills/illustration-carousel-framework.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    for surface in (runtime, framework, skill):
        assert "1080x1440" in surface
        assert "1080x1920" in surface
        assert "1080x1080" in surface
        assert "explicit" in surface.lower()
    assert "downsample once" in runtime
    assert "1080x1440 through 1440x1920" in runtime
    for forbidden in ("crop", "pad", "stretch", "upscale", "wrong ratio", "second resample"):
        assert forbidden in runtime
    assert "add an unrequested format" in framework.lower()


def test_post_source_accommodation_keeps_exact_final_and_source_binding() -> None:
    dimensions = _flat("config/rules/image-dimensions.md")
    framework = _flat("config/skills/illustration-carousel-framework.md")

    for surface in (dimensions, framework):
        assert "1080x1440" in surface
        assert "1440x1920" in surface
        assert "exact 3:4" in surface
        assert "source" in surface.lower()
        assert "hash" in surface.lower() or "sha-256" in surface.lower()
        assert "downsample" in surface.lower()
        assert "upscale" in surface.lower()
    assert "width * 4 == height * 3" in dimensions
    assert "`reels_stories`" in framework
    assert "exact 1080x1920" in framework
    assert "approved normalized" in framework


def test_copy_brandmark_and_pixels_remain_hard_gates() -> None:
    framework = _flat("config/skills/illustration-carousel-framework.md")
    autopilot = _flat("config/skills/carousel-jam-autopilot.md")

    for surface in (framework, autopilot):
        assert "exact" in surface.lower()
        assert "@a.storyof.two" in surface
        assert "top-right" in surface
        assert "SHA-256" in surface
        assert "dimensions" in surface
    assert "Entity/anatomy/spatial integrity" in framework
    assert "Creator approval comes only after all checks pass" in framework


def test_default_path_rejects_review_ceremony_and_duplicate_ledgers() -> None:
    surfaces = "\n".join(
        _flat(path)
        for path in (
            ".agents/skills/a-story-carousel-jam/SKILL.md",
            "config/skills/carousel-jam-runtime-context.md",
            "config/skills/carousel-jam-autopilot.md",
            "config/skills/illustration-carousel-framework.md",
        )
    ).lower()

    for rejected in (
        "agent-room",
        "numeric score",
        "provenance graph",
        "run-ledger",
        "stage-review",
    ):
        assert rejected in surfaces
    assert "do not create separate ledgers" in surfaces


def test_deleted_carousel_room_and_review_loop_files_stay_deleted() -> None:
    retired = [
        "pipeline/stages/carousel_visual_rooms.py",
        "pipeline/agentic/carousel_review_loop.py",
        "pipeline/agentic/carousel_hil_checkpoints.py",
        "scripts/carousel_review_loop.py",
        "config/skills/continuous-carousel-agent-room.md",
        "config/skills/carousel-review-loop.md",
    ]

    assert all(not (ROOT / path).exists() for path in retired)


def test_parallel_helpers_are_dynamic_and_explicit_not_default() -> None:
    autopilot = _flat("config/skills/carousel-jam-autopilot.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    assert "one non-overlapping job" in autopilot
    assert "Do not create a standing room" in autopilot
    assert "only when the creator explicitly asks for parallel work" in skill


def test_make_carousel_is_production_only_not_repo_maintenance() -> None:
    makefile = _read("Makefile")
    recipe = makefile.split("carousel:", 1)[1].split("\n\n", 1)[0]

    assert "scripts/carousel.py" in recipe
    assert "pytest" not in recipe
    assert "agentic_os.py health" not in recipe
    assert "wiki_health" not in recipe


def test_codex_first_generation_boundary_is_explicit_and_truthful() -> None:
    system = json.loads(_read("config/skill-systems.json"))["systems"]["carousel_jam"]
    boundary = system["generation_boundary"]

    assert boundary["codex"] == [
        "read_compiled_prompt",
        "attach_four_curated_identity_references_and_one_style_board",
        "call_image_generation",
        "inspect_decoded_pixels_with_view_image",
        "submit_hash_and_dimension_bound_qa",
    ]
    assert boundary["repository"] == [
        "prepare",
        "ingest",
        "bind_review",
        "record_creator_approval",
        "atomic_promote",
    ]
    surfaces = "\n".join(
        _flat(path)
        for path in (
            ".agents/skills/a-story-carousel-jam/SKILL.md",
            "config/skills/carousel-jam-runtime-context.md",
            "config/skills/carousel-jam-autopilot.md",
            "config/skills/illustration-carousel-framework.md",
        )
    )
    assert "identity-dossier.json.selected_generation_bundle" in surfaces
    assert "four" in surfaces.lower()
    assert "exactly five" in surfaces.lower()
    assert "contact-sheet.png" in surfaces
    assert "not a claim" in surfaces.lower()
    assert "view_image" in surfaces
    assert "BLOCKED/NOT_RUN" in surfaces
    assert "remain `handoff_ready`" in surfaces or "retain `handoff_ready`" in surfaces


def test_public_state_vocabulary_is_identical_across_current_surfaces() -> None:
    for relative in (
        ".agents/skills/a-story-carousel-jam/SKILL.md",
        "config/skills/carousel-jam-runtime-context.md",
        "config/skills/carousel-jam-autopilot.md",
        "config/skills/illustration-carousel-framework.md",
        "docs/ai-ops-playbook.md",
        "docs/superpowers/plans/creative-os-master-plan.md",
    ):
        surface = _read(relative)
        for state in PUBLIC_STATES:
            assert f"`{state}`" in surface, f"{state} missing from {relative}"
        for retired in (
            "awaiting_concept_approval",
            "awaiting_copy_format_approval",
            "awaiting_creator_approval",
            "generating_remaining_slides",
            "final_package_ready",
        ):
            assert retired not in surface, f"retired {retired} remains in {relative}"


def test_ordinary_carousel_contract_has_no_maintenance_side_effects() -> None:
    runtime = _flat("config/skills/carousel-jam-runtime-context.md").lower()
    autopilot = _flat("config/skills/carousel-jam-autopilot.md").lower()

    for forbidden_side_effect in ("wiki", "memory", "rules", "tests", "diagnostics"):
        assert forbidden_side_effect in runtime
    assert "must not run" in autopilot
    assert "network calls" in autopilot


def test_context_loads_compact_creative_hooks_before_heavy_rules() -> None:
    pack = assemble_context_pack(ROOT, profile="a-story-of-two")
    sections = {section.id: section for section in pack.sections}
    order = [section.id for section in pack.sections]

    assert order.index("creator_skill_stack") < order.index("rule_palette")
    assert order.index("storytelling_change_hook") < order.index("rule_palette")
    assert not sections["creator_skill_stack"].truncated
    assert not sections["storytelling_change_hook"].truncated


def test_current_plans_are_small_and_point_to_the_hot_path() -> None:
    plans = sorted((ROOT / "docs" / "superpowers" / "plans").glob("*.md"))

    assert [path.name for path in plans] == [
        "2026-06-28-analysis-hot-path-repair.md",
        "THE-PLAN.md",
        "creative-os-master-plan.md",
    ]
    assert sum(len(path.read_text(encoding="utf-8").splitlines()) for path in plans) < 260
    assert "four locks" in _read("docs/superpowers/plans/creative-os-master-plan.md").lower()
