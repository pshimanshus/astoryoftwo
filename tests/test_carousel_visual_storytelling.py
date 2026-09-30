from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_visual_storytelling import (
    ExpectedFrameAsset,
    active_feedback_constraints,
    creator_feedback_records,
    current_creator_correction_fingerprint,
    generation_payload_fingerprint,
    image_file_fingerprint,
    record_creator_feedback,
    storyboard_source_fingerprint,
    validate_director_storyboard,
    validate_frame_readability,
)


def write_png(path: Path, size: tuple[int, int] = (1080, 1440), color: str = "ivory") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def action_slides() -> dict:
    return {
        "slides": [
            {
                "slide": 1,
                "role": "recognition",
                "copy": "We both knew who.",
                "physical_action": "Aachu and Zuv pull the dining table toward opposite walls, stretching the tablecloth between them.",
                "relationship_state": "Both protect separate plans while noticing the strain between them.",
                "camera": {
                    "shot_size": "wide room geography frame",
                    "position": "doorway-height three-quarter view across the moving table",
                    "negative_space": "quiet upper-left wall above their opposing shoulders",
                },
                "focal_hierarchy": "Their opposing bodies read first, the stretched cloth second, and upper-left copy stays clear.",
                "setting": {
                    "place": "their narrow apartment dining room beside the balcony door",
                    "time": "late rainy afternoon",
                    "motivated_light": "cool balcony light crosses left-to-right over the stretched tablecloth",
                    "depth_layers": {
                        "foreground": "doorframe edge makes the moment feel privately witnessed",
                        "midground": "both bodies strain around the same dining table",
                        "background": "half-unpacked boxes reveal the unsettled shared home",
                    },
                },
                "visual_richness": {
                    "point_of_view": "Their shared uncertainty organizes the room around the table.",
                    "before_frame": "Each partner had silently chosen a different wall for dinner.",
                    "after_frame": "They pause long enough to notice the same tired expression.",
                    "continuation_pull": "Will either of them loosen their grip first?",
                    "story_evidence": [
                        {
                            "carrier": "the stretched cotton tablecloth",
                            "observable_state": "its center seam pulls taut between their hands",
                            "narrative_job": "proves the shared home is under visible tension",
                        },
                        {
                            "carrier": "the unopened moving boxes",
                            "observable_state": "different room labels face toward opposite walls",
                            "narrative_job": "proves two plans are competing inside one move",
                        },
                    ],
                    "posed_portrait_allowed": False,
                    "decorative_clutter_allowed": False,
                },
            },
            {
                "slide": 2,
                "role": "payoff",
                "copy": "We were still learning how.",
                "physical_action": "They stop, meet each other's eyes, and carry the same table together toward the window.",
                "relationship_state": "Their guarded effort releases into coordinated movement and relief.",
                "camera": {
                    "shot_size": "medium-wide lateral action frame",
                    "position": "window-height side view along the table edge",
                    "negative_space": "open upper-right curtain area above their joined direction",
                },
                "focal_hierarchy": "Their synchronized feet read first, shared grip second, and upper-right copy stays clear.",
                "setting": {
                    "place": "the same narrow apartment dining room beside the balcony door",
                    "time": "late rainy afternoon",
                    "motivated_light": "cool balcony light now falls evenly across both moving bodies",
                    "depth_layers": {
                        "foreground": "folded cloth edge leads toward their shared grip",
                        "midground": "both partners carry the table in one direction",
                        "background": "the cleared window wall opens their chosen destination",
                    },
                },
                "visual_richness": {
                    "point_of_view": "Their new coordination organizes the frame toward one destination.",
                    "before_frame": "They had just stopped pulling the table away from each other.",
                    "after_frame": "The table will settle beneath the window they both chose.",
                    "continuation_pull": "",
                    "story_evidence": [
                        {
                            "carrier": "their synchronized bare feet",
                            "observable_state": "both step toward the same window at once",
                            "narrative_job": "proves coordination replaced the earlier opposition",
                        },
                        {
                            "carrier": "the relaxed cotton tablecloth",
                            "observable_state": "its center seam hangs loose between their grips",
                            "narrative_job": "proves the physical tension has visibly released",
                        },
                    ],
                    "posed_portrait_allowed": False,
                    "decorative_clutter_allowed": False,
                },
            },
        ]
    }


def passing_frame(path: str, digest: str, *, slide: int = 1) -> dict:
    return {
        "slide": slide,
        "format": "instagram_post",
        "file": path,
        "status": "PASS",
        "core_action_legible": True,
        "relationship_turn_legible": True,
        "frame_reads_as_caught_event": True,
        "before_after_implied": True,
        "motivated_light_observed": {
            "source": "cool balcony window light",
            "direction": "crosses frame from left toward their active hands",
        },
        "depth_layers_observed": {
            "foreground": "doorframe edge places the viewer outside the private beat",
            "midground": "their hands and shared table carry the active event",
            "background": "moving boxes prove the unsettled domestic context",
        },
        "focal_action_clear": True,
        "story_evidence_observed": [
            "the stretched cloth records their opposing effort",
            "the labeled boxes prove the shared move",
        ],
        "posed_portrait": False,
        "decorative_clutter": False,
        "generic_ai_tells": [],
        "continuation_pull_observed": "Their unresolved grip asks who will release first.",
        "final_payoff_observed": "Their shared direction visibly resolves the earlier opposition.",
        "observed_image_first_read": "They pull one table in opposite directions and visibly disagree about where their shared life should go.",
        "evidence": "Both hands grip opposite table edges; the stretched cloth and diverging feet make the conflict readable.",
        "image_fingerprint": digest,
    }


def test_storyboard_fingerprint_tracks_copy_and_physical_action() -> None:
    slides = action_slides()
    first = storyboard_source_fingerprint(slides)
    slides["slides"][0]["physical_action"] = "They now carry the same table together."

    assert storyboard_source_fingerprint(slides) != first


def test_generation_payload_fingerprint_is_stable_for_key_order() -> None:
    assert generation_payload_fingerprint({"b": 2, "a": 1}) == generation_payload_fingerprint(
        {"a": 1, "b": 2}
    )


def test_empty_creator_correction_state_is_stable(tmp_path: Path) -> None:
    assert current_creator_correction_fingerprint(tmp_path) == current_creator_correction_fingerprint(
        tmp_path
    )


def test_legacy_creator_correction_is_normalized_without_rewriting(tmp_path: Path) -> None:
    path = tmp_path / "creator-correction.json"
    payload = {
        "schema_version": "creator-correction/v1",
        "status": "VISUAL_ROUTE_REJECTED_BY_CREATOR",
        "date": "2026-08-21",
        "creator_feedback": "keep this exact feedback",
        "diagnosis": ["The route invented a prop mechanism."],
        "rejected_route_phrases": ["power strip"],
    }
    path.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")
    before = path.read_bytes()

    records = creator_feedback_records(tmp_path)

    assert len(records) == 1
    assert records[0]["kind"] == "rejection"
    assert records[0]["user_instruction_exact"] == "keep this exact feedback"
    assert records[0]["root_cause"] == "The route invented a prop mechanism."
    assert records[0]["must_change"] == ["power strip"]
    assert records[0]["historical_only"] is True
    assert path.read_bytes() == before


def test_active_feedback_constraints_are_scoped_superseded_and_stable(
    tmp_path: Path,
) -> None:
    (tmp_path / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v2",
                "feedback": [
                    {
                        "feedback_id": "fb-old",
                        "slides": [1],
                        "must_change": ["old action"],
                        "must_preserve": ["copy"],
                        "generation_effect": "slide_local",
                        "historical_only": False,
                    },
                    {
                        "feedback_id": "fb-shared",
                        "slides": [],
                        "must_change": ["grey palette"],
                        "must_preserve": ["identity"],
                        "generation_effect": "shared",
                        "historical_only": False,
                    },
                    {
                        "feedback_id": "fb-new",
                        "slides": [1],
                        "must_change": ["new action"],
                        "must_preserve": ["copy"],
                        "generation_effect": "slide_local",
                        "supersedes_feedback_id": "fb-old",
                        "historical_only": False,
                    },
                    {
                        "feedback_id": "fb-history",
                        "slides": [2],
                        "must_change": ["archived route"],
                        "must_preserve": [],
                        "generation_effect": "slide_local",
                        "historical_only": True,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )

    assert active_feedback_constraints(tmp_path, 1) == [
        {
            "feedback_id": "fb-new",
            "must_change": ["new action"],
            "must_preserve": ["copy"],
        },
        {
            "feedback_id": "fb-shared",
            "must_change": ["grey palette"],
            "must_preserve": ["identity"],
        },
    ]
    assert active_feedback_constraints(tmp_path, 2) == [
        {
            "feedback_id": "fb-shared",
            "must_change": ["grey palette"],
            "must_preserve": ["identity"],
        }
    ]


def test_untriaged_feedback_is_saved_without_churning_generation_inputs(
    tmp_path: Path,
) -> None:
    (tmp_path / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v2",
                "feedback": [
                    {
                        "feedback_id": "fb-needs-triage",
                        "user_instruction_exact": "Something still feels off.",
                        "kind": "correction",
                        "scope": "slide",
                        "slides": [1],
                        "must_change": [],
                        "must_preserve": [],
                        "generation_effect": "slide_local",
                        "historical_only": False,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )

    assert active_feedback_constraints(tmp_path, 1) == []


def test_record_creator_feedback_is_idempotent_and_preserves_exact_text(
    tmp_path: Path,
    monkeypatch,
) -> None:
    package = tmp_path / "output" / "carousels" / "2026-09-04" / "example"
    package.mkdir(parents=True)
    (package / "slides.json").write_text("[]", encoding="utf-8")
    (package / "generation-state.json").write_text(
        json.dumps({"schema_version": "carousel-generation-state/v3"}),
        encoding="utf-8",
    )
    calls: list[dict] = []

    def fake_capture_learning_event(root: Path, **kwargs):
        calls.append({"root": root, **kwargs})

    monkeypatch.setattr(
        "pipeline.agentic.learning_loop.capture_learning_event",
        fake_capture_learning_event,
    )
    exact = "Do not normalize this.\r\nKeep punctuation — exactly!"
    kwargs = {
        "workspace_root": tmp_path,
        "user_instruction_exact": exact,
        "kind": "correction",
        "scope": "slide",
        "slide_numbers": [2],
        "diagnosis": "scene_action",
        "root_cause": "The visible action contradicts the copy.",
        "must_change": ["physical action"],
        "must_preserve": ["exact copy"],
    }

    first = record_creator_feedback(package, **kwargs)
    second = record_creator_feedback(package, **kwargs)
    payload = json.loads((package / "creator-correction.json").read_text(encoding="utf-8"))

    assert first == second
    assert payload["schema_version"] == "creator-correction/v3"
    assert len(payload["events"]) == 1
    assert payload["events"][0]["user_instruction_exact"] == exact
    assert payload["events"][0]["learning_event_id"] == calls[0]["event_id"]
    assert calls[0]["event_id"] == calls[1]["event_id"]
    assert active_feedback_constraints(package, 2)[0]["feedback_id"] == first["feedback_id"]


def test_preflight_accepts_concrete_actions_without_event_a_provenance() -> None:
    slides = action_slides()
    direction = {**slides, "requested_formats": ["instagram_post"]}

    issues = validate_director_storyboard(
        direction,
        slide_count=2,
        expected_slides=slides,
        expected_formats=["instagram_post"],
    )

    assert issues == []


def test_preflight_rejects_mood_instead_of_physical_action() -> None:
    issues = validate_director_storyboard(
        {"slides": [{"slide": 1, "physical_action": "dreamy romantic room"}]},
        slide_count=1,
    )

    assert any("concrete physical action" in issue for issue in issues)


def test_preflight_rejects_format_drift() -> None:
    issues = validate_director_storyboard(
        {
            "requested_formats": ["square"],
            "slides": [
                {
                    "slide": 1,
                    "physical_action": "They pull the dining table toward opposite walls while the dinner plates slide apart.",
                }
            ],
        },
        slide_count=1,
        expected_formats=["instagram_post"],
    )

    assert any("format lock" in issue for issue in issues)


def test_preflight_rejects_generic_light_and_incomplete_story_evidence() -> None:
    direction = action_slides()
    direction["slides"][0]["setting"]["motivated_light"] = "nice lighting"
    direction["slides"][0]["visual_richness"]["story_evidence"] = [
        {
            "carrier": "some props",
            "observable_state": "warm scene",
            "narrative_job": "couple moment",
        }
    ]

    issues = validate_director_storyboard(direction, slide_count=2)

    assert any("setting.motivated_light" in issue for issue in issues)
    assert any("story_evidence must contain two to four" in issue for issue in issues)


def test_preflight_rejects_repeated_shot_and_story_job_without_reason() -> None:
    direction = action_slides()
    direction["slides"][1]["role"] = direction["slides"][0]["role"]
    direction["slides"][1]["camera"]["shot_size"] = direction["slides"][0]["camera"][
        "shot_size"
    ]

    issues = validate_director_storyboard(direction, slide_count=2)

    assert any("repeats one narrative job" in issue for issue in issues)


def test_preflight_rejects_duplicate_normalized_story_evidence_carriers() -> None:
    direction = action_slides()
    evidence = direction["slides"][0]["visual_richness"]["story_evidence"]
    evidence[1] = {
        **evidence[0],
        "carrier": "  " + evidence[0]["carrier"].upper().replace(" ", "   ") + ". ",
    }

    issues = validate_director_storyboard(direction, slide_count=2)

    assert any("two to four distinct normalized carriers" in issue for issue in issues)
    assert any("repeated normalized carriers" in issue for issue in issues)


def test_preflight_accepts_specific_short_camera_place_and_carrier_values() -> None:
    direction = action_slides()
    first = direction["slides"][0]
    first["camera"]["shot_size"] = "medium-wide"
    first["setting"]["place"] = "kitchen table"
    first["setting"]["time"] = "dusk"
    first["visual_richness"]["story_evidence"][0]["carrier"] = "face-down phone"

    issues = validate_director_storyboard(direction, slide_count=2)

    assert issues == []


def test_pixel_read_passes_without_event_a_or_reviewer_provenance(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    check = {
        "status": "PASS",
        "pass": True,
        "image_first": True,
        "frames": [passing_frame("final/slide-01.png", image_file_fingerprint(image))],
        "issues": [],
    }

    issues = validate_frame_readability(
        check,
        slide_count=1,
        required_formats=["instagram_post"],
        expected_frame_bindings={
            (1, "instagram_post"): ExpectedFrameAsset(
                "final/slide-01.png", (1080, 1440)
            )
        },
        package_dir=tmp_path,
        require_files=True,
    )

    assert issues == []


def test_pixel_read_fails_fast_on_unreadable_action(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    frame = passing_frame("final/slide-01.png", image_file_fingerprint(image))
    frame["core_action_legible"] = False
    frame["relationship_turn_legible"] = False

    issues = validate_frame_readability(
        {"status": "FAIL", "pass": False, "frames": [frame]},
        slide_count=1,
        required_formats=["instagram_post"],
    )

    assert issues == [
        "semantic_action failed on rendered slide 1 (core_action_legible)."
    ]


def test_pixel_read_rejects_stale_image_hash(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    frame = passing_frame("final/slide-01.png", "sha256:" + "0" * 64)

    issues = validate_frame_readability(
        {"status": "PASS", "pass": True, "frames": [frame]},
        slide_count=1,
        required_formats=["instagram_post"],
        expected_frame_bindings={
            (1, "instagram_post"): ExpectedFrameAsset(
                "final/slide-01.png", (1080, 1440)
            )
        },
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("image_fingerprint is missing or stale" in issue for issue in issues)


def test_pixel_read_rejects_wrong_dimensions(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image, (1080, 1080))

    issues = validate_frame_readability(
        {
            "status": "PASS",
            "pass": True,
            "frames": [passing_frame("final/slide-01.png", image_file_fingerprint(image))],
        },
        slide_count=1,
        required_formats=["instagram_post"],
        expected_frame_bindings={
            (1, "instagram_post"): ExpectedFrameAsset(
                "final/slide-01.png", (1080, 1440)
            )
        },
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("dimensions are 1080x1080" in issue for issue in issues)


def test_pixel_read_rejects_path_escape(tmp_path: Path) -> None:
    outside = tmp_path.parent / "outside.png"
    write_png(outside)
    frame = passing_frame("../outside.png", image_file_fingerprint(outside))

    issues = validate_frame_readability(
        {"status": "PASS", "pass": True, "frames": [frame]},
        slide_count=1,
        required_formats=["instagram_post"],
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("must not escape" in issue for issue in issues)


def test_pixel_read_requires_every_locked_frame(tmp_path: Path) -> None:
    image = tmp_path / "final" / "slide-01.png"
    write_png(image)
    issues = validate_frame_readability(
        {
            "status": "PASS",
            "pass": True,
            "frames": [passing_frame("final/slide-01.png", image_file_fingerprint(image))],
        },
        slide_count=2,
        required_formats=["instagram_post"],
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("2:instagram_post" in issue for issue in issues)
