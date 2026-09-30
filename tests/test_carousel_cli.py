from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.stages.carousel_lanes import discover_identity_images
from pipeline.stages.codex_builtin_image_generation import build_compiled_prompt_handoff
from tests.helpers.carousel_qa import cinematic_slide_fields, synthetic_route_story_plan


WORKSPACE = Path(__file__).resolve().parents[1]
SCRIPT = WORKSPACE / "scripts" / "carousel.py"


def _run(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )


def _write_reference(path: Path, payload: bytes = b"reference") -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)
    return path


def _write_brief(path: Path) -> Path:
    rows = (
        ("I was certain of you.", "Aachu places one house key in Zuv's open palm.", "certain of each other"),
        ("We are learning how.", "They turn one paper map and trace the same route together.", "committed and learning"),
        ("Some answers arrive slowly.", "Zuv holds the map flat while Aachu circles one shared stop.", "patient with uncertainty"),
        ("But we keep choosing the route together.", "They fold the map together and place it beside one house key.", "committed to the same life"),
    )
    path.write_text(
        json.dumps(
            {
                "story_plan": synthetic_route_story_plan(),
                "slides": [
                    {
                        **cinematic_slide_fields(index, len(rows)),
                        "copy": copy,
                        "physical_action": action,
                        "relationship_state": state,
                        "role": ("cover", "deepening", "turn", "payoff")[index - 1],
                        "copy_mode": "text",
                        "beat_delta": (
                            "The offered house key establishes a shared home.",
                            "They begin choosing a route through a shared map.",
                            "Aachu marks a stop while Zuv holds the route steady.",
                            "The folded map returns beside the key, joining commitment and practical choice.",
                        )[index - 1],
                        "copy_image_relation": {"kind": "completion", "proof": action},
                    }
                    for index, (copy, action, state) in enumerate(rows, start=1)
                ]
            }
        ),
        encoding="utf-8",
    )
    return path


def _tree_bytes(root: Path) -> dict[str, bytes]:
    return {
        path.relative_to(root).as_posix(): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_curated_identity_dossier_controls_auto_bundle(tmp_path: Path) -> None:
    relative = [
        Path("config/references/identity/aachu/a.jpg"),
        Path("config/references/identity/zuv/z.jpg"),
        Path("config/references/identity/together/t-face.jpg"),
        Path("config/references/identity/together/t-body.jpg"),
    ]
    for path in relative:
        _write_reference(tmp_path / path)
    dossier = tmp_path / "config/references/identity/_dossier/identity-dossier.json"
    dossier.parent.mkdir(parents=True)
    dossier.write_text(
        json.dumps({"selected_generation_bundle": [str(path) for path in relative]}),
        encoding="utf-8",
    )

    assert discover_identity_images(tmp_path) == [tmp_path / path for path in relative]


def test_curated_identity_dossier_rejects_missing_subject_role(tmp_path: Path) -> None:
    aachu = _write_reference(tmp_path / "config/references/identity/aachu/a.jpg")
    dossier = tmp_path / "config/references/identity/_dossier/identity-dossier.json"
    dossier.parent.mkdir(parents=True)
    dossier.write_text(
        json.dumps(
            {
                "selected_generation_bundle": [
                    str(aachu.relative_to(tmp_path)),
                ]
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ValueError, match="Aachu, Zuv, and together"):
        discover_identity_images(tmp_path)


def test_create_story_only_returns_truthful_draft_json(tmp_path: Path) -> None:
    result = _run(
        "create",
        "--story",
        "I was certain of you. We are still learning how.",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload == {
        "next_action": "lock_visible_actions",
        "package_dir": payload["package_dir"],
        "schema_version": "carousel-cli/v1",
        "selected_formats": ["instagram_post"],
        "selected_slides": [],
        "state": "draft",
    }
    package = Path(payload["package_dir"])
    assert (package / "generation-state.json").is_file()
    assert not (package / ".internal/compiled-prompts").exists()


def test_create_preserves_all_six_labeled_story_beats_by_default(tmp_path: Path) -> None:
    story = "\n".join(
        (
            "Cover: I was never unsure of you.",
            "Cold open: Choosing each other answered the easiest question.",
            "Deepening: Then life began asking harder ones.",
            "Conflict: Some days, love did not tell us what to do.",
            "Turn: Being lost together did not mean I had chosen wrong.",
            "Payoff: Commitment answered who. We are still learning how.",
        )
    )

    result = _run(
        "create",
        "--story",
        story,
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    slides = json.loads((Path(payload["package_dir"]) / "slides.json").read_text())
    assert [slide["role"] for slide in slides] == [
        "cover",
        "cold_open",
        "deepening",
        "conflict",
        "turn",
        "payoff",
    ]
    assert slides[-1]["copy"] == "Commitment answered who. We are still learning how."


def test_explicit_slide_cap_never_silently_discards_creator_copy(tmp_path: Path) -> None:
    story = "\n".join(
        (
            "Cover: One.",
            "Cold open: Two.",
            "Deepening: Three.",
            "Conflict: Four.",
            "Turn: Five.",
            "Payoff: Six.",
        )
    )

    result = _run(
        "create",
        "--story",
        story,
        "--slide-count",
        "5",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["state"] == "blocked"
    assert "refusing to discard creator copy" in payload["reason"]


def test_labeled_story_preserves_multiline_continuations(tmp_path: Path) -> None:
    story = "\n".join(
        (
            "Cover:",
            "I was never unsure of you.",
            "I was lost inside our life.",
            "Cold open: Choosing each other answered the easiest question.",
            "Deepening: Then life began asking harder ones.",
            "Conflict: Some days, love did not tell us what to do.",
            "Turn: Being lost together did not mean I had chosen wrong.",
            "Payoff:",
            "Commitment answered who.",
            "We are still learning how.",
        )
    )

    result = _run(
        "create",
        "--story",
        story,
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    slides = json.loads(
        (Path(json.loads(result.stdout)["package_dir"]) / "slides.json").read_text()
    )
    assert slides[0]["copy"] == (
        "I was never unsure of you.\nI was lost inside our life."
    )
    assert slides[-1]["copy"] == (
        "Commitment answered who.\nWe are still learning how."
    )


def test_creative_brief_and_explicit_slide_count_must_agree(tmp_path: Path) -> None:
    brief = tmp_path / "six-slide-brief.json"
    brief.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": f"Exact beat {number}.",
                        "physical_action": f"They move one shared object {number} together.",
                    }
                    for number in range(1, 7)
                ]
            }
        ),
        encoding="utf-8",
    )

    result = _run(
        "create",
        "--story",
        "Six protected beats.",
        "--creative-brief",
        str(brief),
        "--slide-count",
        "5",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["state"] == "blocked"
    assert "refusing to discard or invent creator beats" in payload["reason"]


def test_create_locked_brief_can_prepare_exactly_one_proof(tmp_path: Path) -> None:
    identities = [
        _write_reference(tmp_path / "identity/aachu/a.png", b"aachu"),
        _write_reference(tmp_path / "identity/zuv/z.png", b"zuv"),
        _write_reference(tmp_path / "identity/together/face.png", b"together-face"),
        _write_reference(tmp_path / "identity/together/body.png", b"together-body"),
    ]
    brief = _write_brief(tmp_path / "brief.json")
    command = [
        "create",
        "--story",
        "Certain of you, still learning us.",
        "--creative-brief",
        str(brief),
        "--prepare-proof",
        "--proof-slide",
        "2",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    ]
    for identity in identities:
        command.extend(("--identity-image", str(identity)))
    result = _run(*command)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] == "handoff_ready"
    assert payload["selected_slides"] == [2]
    assert payload["selected_formats"] == ["instagram_post"]
    package = Path(payload["package_dir"])
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    style_profile = prompt_pack["style_profile"]
    assert style_profile["id"] == "cinematic-observational-watercolor"
    assert style_profile["version"] == "1.0.0"
    assert (package / style_profile["reference"]["path"]).is_file()


def test_locked_visual_fields_survive_package_and_compiled_prompt(tmp_path: Path) -> None:
    brief = tmp_path / "brief.json"
    local_story_reference = _write_reference(tmp_path / "local-story.png", b"story")
    identities = [
        _write_reference(tmp_path / "identity/aachu/a.png", b"aachu"),
        _write_reference(tmp_path / "identity/zuv/z.png", b"zuv"),
        _write_reference(tmp_path / "identity/together/face.png", b"together-face"),
        _write_reference(tmp_path / "identity/together/body.png", b"together-body"),
    ]
    brief_payload = json.loads(_write_brief(brief).read_text(encoding="utf-8"))
    slides = brief_payload["slides"]
    slides[0].update(
        {
            "camera": {
                "shot_size": "low medium-wide doorway frame",
                "position": "eye-level at the doorway with the key centered between both hands",
                "negative_space": "clean upper-left wall protects the exact copy space",
            },
            "wardrobe": "Aachu black overshirt and blue jeans; Zuv white zip jacket",
            "props": "one unlettered brass house key and nothing else",
            "setting": {
                "place": "the uncluttered warm-ivory apartment doorway",
                "time": "late afternoon before moving",
                "motivated_light": "window light enters from frame left and catches the key",
                "depth_layers": {
                    "foreground": "a soft moving-box edge anchors the room",
                    "midground": "their hands exchange the key in the doorway",
                    "background": "the open hall reveals the next room",
                },
            },
            "emotion": "quiet certainty without posing",
            "continuity_lock": "same doorway and wardrobe across the sequence",
            "negative_prompt": "no spare keys or printed labels",
            "source_images": [local_story_reference.name],
        }
    )
    brief.write_text(json.dumps(brief_payload), encoding="utf-8")
    command = [
        "create",
        "--story",
        "The same home, learned together.",
        "--creative-brief",
        str(brief),
        "--prepare-proof",
        "--proof-slide",
        "1",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    ]
    for identity in identities:
        command.extend(("--identity-image", str(identity)))
    result = _run(*command)

    assert result.returncode == 0, result.stdout + result.stderr
    package = Path(json.loads(result.stdout)["package_dir"])
    packaged_slide = json.loads((package / "slides.json").read_text(encoding="utf-8"))[0]
    packaged_prompt = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    for key in (
        "camera",
        "wardrobe",
        "props",
        "setting",
        "emotion",
        "continuity_lock",
        "negative_prompt",
        "hand_map",
        "spatial_topology",
        "visual_richness",
    ):
        assert key in packaged_slide
        assert key not in packaged_prompt
    for retired in ("visual", "scene", "composition", "pose", "background"):
        assert retired not in packaged_slide
    assert len(packaged_slide["source_images"]) == 1
    assert (package / packaged_slide["source_images"][0]).read_bytes() == b"story"

    compiled = (
        package
        / ".internal/compiled-prompts/instagram-post/slide-01.prompt.txt"
    ).read_text(encoding="utf-8")
    for fragment in (
        "key centered between both hands",
        "Aachu black overshirt and blue jeans",
        "one unlettered brass house key",
        "uncluttered warm-ivory apartment doorway",
        "quiet certainty without posing",
        "no spare keys or printed labels",
        "LIMB AND HAND PLAN:",
        "owner -> arm -> wrist -> hand -> contacted object",
        "WHOLE-PERSON AND OBJECT TOPOLOGY:",
    ):
        assert fragment in compiled

    handoff = build_compiled_prompt_handoff(
        package,
        slide_numbers=[1],
        output_formats=["instagram_post"],
    )
    assert len(handoff["reference_bindings"]) == 5
    assert len(handoff["context_reference_bindings"]) == 1
    assert handoff["context_reference_bindings"][0]["roles"] == ["story"]


def test_default_prepared_handoff_uses_four_identity_roles_and_one_style_board(
    tmp_path: Path,
) -> None:
    identity_bundle = discover_identity_images(WORKSPACE)
    assert len(identity_bundle) == 4
    command = [
        "create",
        "--story",
        "Certain of you, still learning us.",
        "--creative-brief",
        str(_write_brief(tmp_path / "brief.json")),
        "--prepare-proof",
        "--proof-slide",
        "2",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    ]

    result = _run(*command)

    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] == "handoff_ready"
    package = Path(payload["package_dir"])
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    identities = prompt_pack["identity_reference_images"]
    style_profile = prompt_pack["style_profile"]
    styles = [style_profile["reference"]["path"]]
    assert len(identities) == 4
    assert len(styles) == 1
    assert len(identities) + len(styles) == 5
    style_board = (
        WORKSPACE
        / "config/references/style-lock/cinematic-observational-watercolor-v1/contact-sheet.png"
    )
    assert (package / styles[0]).read_bytes() == style_board.read_bytes()

    context = json.loads((package / "creative-context.json").read_text(encoding="utf-8"))
    assert [
        record["role"]
        for record in context["identity_reference_selection"]["selected_references"]
    ] == [
        "Aachu identity anchor",
        "Zuv identity anchor",
        "together face/scale anchor",
        "together body/posture anchor",
    ]
    handoff = build_compiled_prompt_handoff(
        package,
        slide_numbers=[2],
        output_formats=["instagram_post"],
    )
    attached = [
        binding
        for binding in handoff["reference_bindings"]
        if set(binding["roles"]) & {"identity", "style"}
    ]
    assert len(attached) == 5
    assert sum("identity" in binding["roles"] for binding in attached) == 4
    assert sum("style" in binding["roles"] for binding in attached) == 1
    assert {binding["role"] for binding in attached if binding["roles"] == ["identity"]} == {
        "Aachu identity anchor",
        "Zuv identity anchor",
        "together face/scale anchor",
        "together body/posture anchor",
    }
    assert handoff["files"][0]["prompt"] == (
        package / handoff["files"][0]["path"]
    ).read_text(encoding="utf-8")
    assert handoff["files"][0]["width"] == 1080
    assert handoff["files"][0]["height"] == 1440


def test_feedback_command_is_exact_idempotent_and_uses_existing_learning_loop(
    tmp_path: Path,
) -> None:
    created = _run(
        "create",
        "--story",
        "One truthful correction.",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    )
    assert created.returncode == 0, created.stdout + created.stderr
    package = Path(json.loads(created.stdout)["package_dir"])
    feedback_file = tmp_path / "feedback.txt"
    exact = "Keep her expression — but change the hand action.\nDo not rewrite this."
    feedback_file.write_text(exact, encoding="utf-8")
    command = (
        "feedback",
        str(package),
        "--text-file",
        str(feedback_file),
        "--kind",
        "correction",
        "--scope",
        "slide",
        "--slide",
        "1",
        "--must-change",
        "the hand action",
        "--must-preserve",
        "her expression",
    )

    first = _run(*command)
    second = _run(*command)

    assert first.returncode == second.returncode == 0
    first_payload = json.loads(first.stdout)
    second_payload = json.loads(second.stdout)
    assert first_payload["feedback_id"] == second_payload["feedback_id"]
    correction = json.loads((package / "creator-correction.json").read_text(encoding="utf-8"))
    assert correction["schema_version"] == "creator-correction/v3"
    assert len(correction["events"]) == 1
    assert correction["events"][0]["user_instruction_exact"] == exact
    events = list((tmp_path / "memory/agentic/learning-events").glob("*.json"))
    assert len(events) == 1
    event = json.loads(events[0].read_text(encoding="utf-8"))
    assert event["user_instruction_exact"] == exact
    assert event["eval_disposition"] == "background"


def test_feedback_on_archived_package_preserves_package_bytes(tmp_path: Path) -> None:
    package = tmp_path / "output/carousels/2026-09-04/archived"
    package.mkdir(parents=True)
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2",
                "status": "proof_ready_for_review",
            }
        ),
        encoding="utf-8",
    )
    (package / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v1",
                "creator_feedback": "historical correction",
            }
        ),
        encoding="utf-8",
    )
    before = _tree_bytes(package)

    result = _run(
        "feedback",
        str(package),
        "--text",
        "Save this new observation without migrating the package.",
        "--kind",
        "observation",
        "--scope",
        "package",
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert json.loads(result.stdout)["feedback_id"].startswith("fb-")
    assert _tree_bytes(package) == before
    assert len(list((tmp_path / "memory/agentic/learning-events").glob("*.json"))) == 1


def _write_archived_successor_source(tmp_path: Path) -> Path:
    package = tmp_path / "output/carousels/2026-09-04/archived-source"
    package.mkdir(parents=True)
    (package / "creative-context.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-creative-context/v2",
                "slug": "archived-source",
                "title": "Archived source",
                "source_story": "The original story stays archived.",
            }
        ),
        encoding="utf-8",
    )
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2",
                "status": "packaged",
                "slides": {"1": {"attempts": 2}},
            }
        ),
        encoding="utf-8",
    )
    (package / "prompt-pack.json").write_text(
        json.dumps({"schema_version": "carousel-prompt-pack/v2", "slides": []}),
        encoding="utf-8",
    )
    exact = "The hand is visually wrong — rebuild this scene."
    (package / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v3",
                "package_id": "output/carousels/2026-09-04/archived-source",
                "events": [
                    {
                        "feedback_id": "fb-old-live",
                        "captured_at": "2026-09-04T10:00:00+00:00",
                        "user_instruction_exact": exact,
                        "kind": "rejection",
                        "scope": "slide",
                        "slides": [2],
                        "primary_diagnosis": "scene_action",
                        "must_change": ["incorrect hand"],
                        "must_preserve": ["exact slide copy"],
                        "affected_artifacts": ["slides.json"],
                        "repair_operations": [
                            {
                                "artifact": "slides.json",
                                "json_pointer": "/1/physical_action",
                                "value": (
                                    "Zuv holds the map flat while Aachu traces one shared "
                                    "route with her right hand."
                                ),
                            }
                        ],
                        "action_taken": {"type": "legacy claim"},
                        "resolution_evidence": ["visual-qa.json"],
                        "learning_event_id": "event-feedback-fb-old-live",
                        "eval_task_ids": ["FEEDBACK-OLD-LIVE"],
                        "status": "evaluated",
                        "generation_effect": "slide_local",
                        "historical_only": False,
                    },
                    {
                        "feedback_id": "fb-learning-declined",
                        "captured_at": "2026-09-04T10:15:00+00:00",
                        "user_instruction_exact": "Keep this package fix even though the global rule was declined.",
                        "kind": "correction",
                        "scope": "slide",
                        "slides": [3],
                        "primary_diagnosis": "scene_action",
                        "must_change": ["repair slide three only"],
                        "must_preserve": ["do not turn this into a global rule"],
                        "affected_artifacts": ["slides.json"],
                        "repair_operations": [],
                        "action_taken": {"type": "legacy package repair"},
                        "resolution_evidence": ["slides.json"],
                        "learning_event_id": "event-feedback-fb-learning-declined",
                        "eval_task_ids": ["FEEDBACK-LEARNING-DECLINED"],
                        "status": "learning_declined",
                        "generation_effect": "slide_local",
                        "supersedes_feedback_id": "fb-old-live",
                        "historical_only": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    (package / "visual-qa.json").write_bytes(b"old-qa")
    (package / "generation-receipt.json").write_bytes(b"old-receipt")
    (package / "final").mkdir()
    (package / "final/slide-01.png").write_bytes(b"old-final")

    learning_dir = tmp_path / "memory/agentic/learning-events"
    learning_dir.mkdir(parents=True)
    (learning_dir / "event-feedback-fb-standalone.json").write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-feedback-fb-standalone",
                "source": "creator_feedback",
                "summary": "Use the approved umbrella interaction.",
                "evidence_paths": [],
                "user_instruction_exact": "yes — use the umbrella scene",
                "diagnosis": "scene_action",
                "scope": "slide",
                "package_path": "output/carousels/2026-09-04/archived-source",
                "feedback_status": "captured",
                "resolution_evidence": [],
                "eval_disposition": "background",
                "feedback_metadata": {
                    "feedback_id": "fb-standalone",
                    "kind": "approval",
                    "slides": [2],
                    "must_change": ["Use the approved umbrella action."],
                    "must_preserve": ["umbrella interaction"],
                    "generation_effect": "none",
                },
                "created_at": "2026-09-04T11:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )
    return package


def test_create_successor_adopts_lineage_and_unresolved_feedback_only(
    tmp_path: Path,
) -> None:
    source = _write_archived_successor_source(tmp_path)
    before = _tree_bytes(source)
    brief = _write_brief(tmp_path / "successor-brief.json")

    result = _run(
        "create",
        "--story",
        "The repaired story.",
        "--title",
        "Successor package",
        "--creative-brief",
        str(brief),
        "--successor-of",
        str(source),
        "--output-root",
        str(tmp_path / "output/carousels"),
    )

    assert result.returncode == 0, result.stdout + result.stderr
    successor = Path(json.loads(result.stdout)["package_dir"])
    assert successor != source
    assert _tree_bytes(source) == before

    context = json.loads((successor / "creative-context.json").read_text())
    assert context["lineage"]["relationship"] == "successor_of"
    assert context["lineage"]["source_package_path"] == (
        "output/carousels/2026-09-04/archived-source"
    )
    assert context["lineage"]["source_feedback_ids"] == [
        "fb-old-live",
        "fb-learning-declined",
        "fb-standalone",
    ]
    fresh_feedback_ids = context["lineage"]["carried_feedback_ids"]
    assert len(fresh_feedback_ids) == len(set(fresh_feedback_ids)) == 3
    assert not set(fresh_feedback_ids) & {
        "fb-old-live",
        "fb-learning-declined",
        "fb-standalone",
    }

    correction = json.loads((successor / "creator-correction.json").read_text())
    assert correction["schema_version"] == "creator-correction/v3"
    assert [item["feedback_id"] for item in correction["events"]] == fresh_feedback_ids
    assert [item["user_instruction_exact"] for item in correction["events"]] == [
        "The hand is visually wrong — rebuild this scene.",
        "Keep this package fix even though the global rule was declined.",
        "yes — use the umbrella scene",
    ]
    assert correction["events"][2]["must_change"] == [
        "Use the approved umbrella action."
    ]
    assert all(event["root_cause"] for event in correction["events"])
    assert all(event["desired_behavior"] for event in correction["events"])
    assert correction["events"][1]["learning_disposition"] == "declined"
    assert correction["events"][1]["supersedes_feedback_id"] == fresh_feedback_ids[0]
    assert (
        correction["events"][1]["adoption_provenance"][
            "source_supersedes_feedback_id"
        ]
        == "fb-old-live"
    )
    source_ids = [
        "fb-old-live",
        "fb-learning-declined",
        "fb-standalone",
    ]
    for event, source_feedback_id in zip(correction["events"], source_ids):
        assert event["status"] == "diagnosed"
        assert event["historical_only"] is False
        assert event["action_taken"] is None
        assert event["resolution_evidence"] == []
        assert len(event["eval_task_ids"]) == 1
        assert event["eval_task_ids"][0].startswith("FEEDBACK-")
        assert event["learning_event_id"] == f"event-feedback-{event['feedback_id']}"
        assert event["adoption_provenance"]["source_feedback_id"] == source_feedback_id
        assert event["adoption_provenance"]["source_user_instruction_sha256"] == (
            event["user_instruction_sha256"]
        )
        assert event["adoption_provenance"]["old_resolution_evidence_discarded"] is True

        case_path = (
            tmp_path / "evals/feedback-cases" / f"{event['eval_task_ids'][0]}.json"
        )
        learning_path = (
            tmp_path
            / "memory/agentic/learning-events"
            / f"{event['learning_event_id']}.json"
        )
        assert case_path.is_file()
        assert learning_path.is_file()
        case = json.loads(case_path.read_text())
        learning = json.loads(learning_path.read_text())
        assert case["feedback_id"] == event["feedback_id"]
        assert case["package_path"] == successor.relative_to(tmp_path).as_posix()
        assert learning["package_path"] == successor.relative_to(tmp_path).as_posix()
        assert learning["feedback_metadata"]["feedback_id"] == event["feedback_id"]
        assert learning["feedback_metadata"]["adoption_provenance"] == (
            event["adoption_provenance"]
        )

    revised = _run("revise", str(successor), "--feedback-id", fresh_feedback_ids[0])
    assert revised.returncode == 0, revised.stdout + revised.stderr
    revised_payload = json.loads(revised.stdout)
    assert revised_payload["feedback_evaluation"]["status"] == "passed"
    revised_document = json.loads((successor / "creator-correction.json").read_text())
    revised_event = next(
        event
        for event in revised_document["events"]
        if event["feedback_id"] == fresh_feedback_ids[0]
    )
    assert revised_event["adoption_provenance"] == correction["events"][0][
        "adoption_provenance"
    ]
    repaired_slides = json.loads((successor / "slides.json").read_text())
    assert repaired_slides[1]["physical_action"] == (
        "Zuv holds the map flat while Aachu traces one shared route with her right hand."
    )
    assert _tree_bytes(source) == before

    state = json.loads((successor / "generation-state.json").read_text())
    assert state["schema_version"] == "carousel-generation-state/v3"
    assert all(item["attempts"] == 0 for item in state["slides"].values())
    assert all(item["attempt_history"] == [] for item in state["slides"].values())
    for forbidden in (
        "visual-qa.json",
        "generation-receipt.json",
        "final",
        "proof-qa.json",
        "final-audit.json",
    ):
        assert not (successor / forbidden).exists()
    successor_bytes = _tree_bytes(successor).values()
    assert b"old-qa" not in successor_bytes
    assert b"old-receipt" not in successor_bytes
    assert b"old-final" not in successor_bytes


def test_each_successor_mints_noncolliding_feedback_event_and_eval_ids(
    tmp_path: Path,
) -> None:
    source = _write_archived_successor_source(tmp_path)
    before = _tree_bytes(source)
    brief = _write_brief(tmp_path / "successor-brief.json")

    created = [
        _run(
            "create",
            "--story",
            "The repaired story.",
            "--title",
            "Successor package",
            "--creative-brief",
            str(brief),
            "--successor-of",
            str(source),
            "--output-root",
            str(tmp_path / "output/carousels"),
        )
        for _ in range(2)
    ]

    assert all(result.returncode == 0 for result in created)
    packages = [Path(json.loads(result.stdout)["package_dir"]) for result in created]
    documents = [
        json.loads((package / "creator-correction.json").read_text())
        for package in packages
    ]
    feedback_ids = [
        {event["feedback_id"] for event in document["events"]}
        for document in documents
    ]
    event_ids = [
        {event["learning_event_id"] for event in document["events"]}
        for document in documents
    ]
    eval_ids = [
        {event["eval_task_ids"][0] for event in document["events"]}
        for document in documents
    ]
    assert feedback_ids[0].isdisjoint(feedback_ids[1])
    assert event_ids[0].isdisjoint(event_ids[1])
    assert eval_ids[0].isdisjoint(eval_ids[1])
    assert _tree_bytes(source) == before


def test_successor_rejects_corrupt_source_feedback_text_hash(
    tmp_path: Path,
) -> None:
    source = _write_archived_successor_source(tmp_path)
    correction_path = source / "creator-correction.json"
    correction = json.loads(correction_path.read_text())
    correction["events"][0]["user_instruction_sha256"] = "sha256:" + "0" * 64
    correction_path.write_text(json.dumps(correction), encoding="utf-8")
    before = _tree_bytes(source)

    result = _run(
        "create",
        "--story",
        "The repaired story.",
        "--creative-brief",
        str(_write_brief(tmp_path / "successor-brief.json")),
        "--successor-of",
        str(source),
        "--output-root",
        str(tmp_path / "output/carousels"),
    )

    assert result.returncode == 2
    assert "exact wording hash" in json.loads(result.stdout)["reason"]
    assert _tree_bytes(source) == before


@pytest.mark.parametrize("invalid_source", ["missing", "writable_v3"])
def test_create_successor_rejects_invalid_source(
    tmp_path: Path,
    invalid_source: str,
) -> None:
    source = tmp_path / "output/carousels/2026-09-04/source"
    if invalid_source == "writable_v3":
        source.mkdir(parents=True)
        (source / "creative-context.json").write_text("{}", encoding="utf-8")
        (source / "generation-state.json").write_text(
            json.dumps({"schema_version": "carousel-generation-state/v3"}),
            encoding="utf-8",
        )
        (source / "prompt-pack.json").write_text(
            json.dumps({"schema_version": "carousel-prompt-pack/v3"}),
            encoding="utf-8",
        )
    brief = _write_brief(tmp_path / "brief.json")

    result = _run(
        "create",
        "--story",
        "Do not create this successor.",
        "--creative-brief",
        str(brief),
        "--successor-of",
        str(source),
        "--output-root",
        str(tmp_path / "output/carousels"),
    )

    assert result.returncode == 2
    assert json.loads(result.stdout)["state"] == "blocked"


def test_create_successor_requires_nonempty_creative_brief(tmp_path: Path) -> None:
    source = _write_archived_successor_source(tmp_path)
    empty_brief = tmp_path / "empty-brief.json"
    empty_brief.write_text(json.dumps({"slides": []}), encoding="utf-8")

    missing = _run(
        "create",
        "--story",
        "No brief.",
        "--successor-of",
        str(source),
        "--output-root",
        str(tmp_path / "output/carousels"),
    )
    empty = _run(
        "create",
        "--story",
        "Empty brief.",
        "--creative-brief",
        str(empty_brief),
        "--successor-of",
        str(source),
        "--output-root",
        str(tmp_path / "output/carousels"),
    )

    assert missing.returncode == empty.returncode == 2
    assert "real --creative-brief" in json.loads(missing.stdout)["reason"]
    assert "real --creative-brief" in json.loads(empty.stdout)["reason"]


def test_blocked_cli_input_still_returns_versioned_json() -> None:
    result = _run("create", "--story", "")

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["schema_version"] == "carousel-cli/v1"
    assert payload["state"] == "blocked"
    assert payload["next_action"] == "repair_inputs"
    assert payload["selected_slides"] == []
    assert payload["selected_formats"] == []


def test_review_rejects_archived_v2_before_staging_any_file(tmp_path: Path) -> None:
    package = tmp_path / "archived-review"
    package.mkdir()
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2",
                "status": "proof_qa_required",
            }
        ),
        encoding="utf-8",
    )
    (package / "proof-qa.json").write_bytes(b"archived-proof-qa")
    qa = tmp_path / "new-qa.json"
    qa.write_text(json.dumps({"status": "PASS"}), encoding="utf-8")
    before = _tree_bytes(package)

    result = _run("review", str(package), "--qa", str(qa))

    assert result.returncode == 2
    assert "read-only" in json.loads(result.stdout)["reason"]
    assert _tree_bytes(package) == before


@pytest.mark.parametrize(
    ("legacy_status", "expected"),
    [
        ("proof_ready_for_review", "proof_qa_required"),
        ("creator_approved_proof", "batch_ready"),
        ("generated", "final_qa_required"),
        ("packaged", "final_qa_required"),
        ("publishable", "final_qa_failed"),
    ],
)
def test_archived_status_uses_one_read_only_public_mapping(
    tmp_path: Path,
    legacy_status: str,
    expected: str,
) -> None:
    package = tmp_path / legacy_status
    package.mkdir()
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2",
                "status": legacy_status,
            }
        ),
        encoding="utf-8",
    )
    before = _tree_bytes(package)

    result = _run("status", str(package))

    assert result.returncode == (2 if expected in {"proof_failed", "final_qa_failed"} else 0)
    assert json.loads(result.stdout)["state"] == expected
    assert _tree_bytes(package) == before


@pytest.mark.parametrize(
    "command",
    ("prepare", "ingest", "approve", "finalize", "revise", "review"),
)
@pytest.mark.parametrize("legacy_surface", ["state", "prompt-pack"])
def test_every_writing_cli_command_keeps_archived_v2_tree_unchanged(
    tmp_path: Path,
    command: str,
    legacy_surface: str,
) -> None:
    package = tmp_path / f"archived-{command}"
    package.mkdir()
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2" if legacy_surface == "state" else "carousel-generation-state/v3",
                "status": "proof_ready_for_review",
            }
        ),
        encoding="utf-8",
    )
    if legacy_surface == "prompt-pack":
        (package / "prompt-pack.json").write_text(
            json.dumps({"schema_version": "carousel-prompt-pack/v2", "slides": []}),
            encoding="utf-8",
        )
    external = _write_reference(tmp_path / "external.png", b"external")
    args = [command, str(package)]
    if command == "ingest":
        args.extend(("--instagram-post", str(external)))
    elif command == "approve":
        args.extend(("--proof-sha256", "sha256:" + "0" * 64))
    elif command == "prepare":
        args.extend(("--format", "reels_stories"))
    elif command == "revise":
        args.extend(("--feedback-id", "archived-feedback"))
    elif command == "review":
        args.extend(("--qa", str(external)))
    before = _tree_bytes(package)

    result = _run(*args)

    assert result.returncode == 2
    assert "read-only" in json.loads(result.stdout)["reason"]
    assert _tree_bytes(package) == before


def test_status_does_not_reconcile_historical_prompt_pack(tmp_path: Path) -> None:
    package = tmp_path / "archived-style"
    package.mkdir()
    (package / "generation-state.json").write_text(json.dumps({
        "schema_version": "carousel-generation-state/v3", "status": "publish_ready",
    }))
    (package / "prompt-pack.json").write_text(json.dumps({
        "schema_version": "carousel-prompt-pack/v2", "slides": [],
    }))
    (package / "final").mkdir()
    (package / "final/slide-01.png").write_bytes(b"historical-final")
    before = _tree_bytes(package)
    result = _run("status", str(package))
    assert result.returncode == 2
    assert "read-only" in json.loads(result.stdout)["reason"]
    assert _tree_bytes(package) == before


@pytest.mark.parametrize("command", ["status", "feedback-status"])
def test_observational_status_commands_report_drift_without_mutating_package(
    tmp_path: Path,
    command: str,
) -> None:
    identities = [
        _write_reference(tmp_path / "identity/aachu/a.png", b"aachu"),
        _write_reference(tmp_path / "identity/zuv/z.png", b"zuv"),
        _write_reference(tmp_path / "identity/together/face.png", b"together-face"),
        _write_reference(tmp_path / "identity/together/body.png", b"together-body"),
    ]
    create_args = [
        "create",
        "--story",
        "Certain of you, still learning us.",
        "--creative-brief",
        str(_write_brief(tmp_path / "brief.json")),
        "--prepare-proof",
        "--proof-slide",
        "2",
        "--output-root",
        str(tmp_path / "output" / "carousels"),
    ]
    for identity in identities:
        create_args.extend(("--identity-image", str(identity)))
    created = _run(*create_args)
    assert created.returncode == 0, created.stdout + created.stderr
    package = Path(json.loads(created.stdout)["package_dir"])

    if command == "feedback-status":
        state_path = package / "generation-state.json"
        state = json.loads(state_path.read_text(encoding="utf-8"))
        state.update(
            status="awaiting_creator_proof_approval",
            next_action="approve_proof",
        )
        state_path.write_text(json.dumps(state), encoding="utf-8")

    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    slides[1]["copy"] = "We are learning a completely different route now."
    slides_path.write_text(json.dumps(slides), encoding="utf-8")
    before = _tree_bytes(package)

    result = _run(command, str(package))

    assert result.returncode == 2, result.stdout + result.stderr
    payload = json.loads(result.stdout)
    assert payload["state"] == "blocked"
    assert payload["next_action"] == "reconcile_package_state"
    assert "stale" in payload["reason"]
    assert _tree_bytes(package) == before


def test_public_style_overrides_are_not_exposed(tmp_path: Path) -> None:
    style_one = _write_reference(tmp_path / "style-one.png", b"one")
    style_two = _write_reference(tmp_path / "style-two.png", b"two")

    result = _run(
        "create",
        "--story",
        "One truthful draft.",
        "--style-reference",
        str(style_one),
        "--style-reference",
        str(style_two),
        "--output-root",
        str(tmp_path / "output/carousels"),
    )

    assert result.returncode == 2
    payload = json.loads(result.stdout)
    assert payload["state"] == "blocked"
    assert "unrecognized arguments" in payload["reason"]

    help_result = _run("create", "--help")
    assert help_result.returncode == 0
    assert "--style-reference" not in help_result.stdout
    assert "--style-brief" not in help_result.stdout


def test_make_carousel_forwards_public_inputs_without_hidden_work() -> None:
    makefile = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    recipe = makefile.split("\nvisual-check:", 1)[0].split("\ncarousel:", 1)[1]

    assert "scripts/carousel.py create" in recipe
    for variable in (
        "STORY_FILE",
        "CREATIVE_BRIEF",
        "STORY_IMAGES",
        "IDENTITY_IMAGES",
        "FORMATS",
        "OUTPUT_ROOT",
        "PROOF_SLIDE",
    ):
        assert f"$({variable})" in recipe
    assert "STYLE_REFERENCE" not in recipe
    assert "pytest" not in recipe
    assert "agentic_os.py" not in recipe
    assert "wiki" not in recipe.lower()


def test_make_carousel_infers_beats_unless_creator_sets_slide_cap() -> None:
    default = subprocess.run(
        ["make", "-n", "carousel", "STORY=Cover: one. Payoff: two."],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
    )
    explicit = subprocess.run(
        ["make", "-n", "carousel", "STORY=Cover: one. Payoff: two.", "SLIDES=6"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
    )

    assert default.returncode == 0
    assert "--slide-count" not in default.stdout
    assert explicit.returncode == 0
    assert '--slide-count "6"' in explicit.stdout


def test_make_defaults_work_in_a_codex_worktree_and_scope_the_project_suite() -> None:
    result = subprocess.run(
        ["make", "-n", "test"],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "pytest --import-mode=importlib tests" in result.stdout
    assert "../../venv/bin/python" in result.stdout or "venv/bin/python" in result.stdout


def test_jam_uses_canonical_command_without_research_ceremony() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(WORKSPACE / "scripts/jam_today.py"),
            "--moment",
            "They turn one map around and trace one route together.",
        ],
        cwd=WORKSPACE,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    assert result.returncode == 0
    assert "scripts/carousel.py create" in result.stdout
    assert "--prepare-image-handoff" not in result.stdout
    assert "Research Challenge Gate" not in result.stdout
    assert "Research Partner Lens" not in result.stdout
