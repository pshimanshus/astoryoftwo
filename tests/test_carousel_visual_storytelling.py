import json
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import (
    format_contract_fingerprint,
    write_format_contract,
)
from pipeline.stages.carousel_visual_storytelling import (
    DIRECTOR_EVENT_FINGERPRINT_VERSION,
    EMPTY_CREATOR_CORRECTION_FINGERPRINT,
    REVIEW_PROVENANCE_VERSION,
    blind_cards_fingerprint,
    current_creator_correction_fingerprint,
    director_event_fingerprint,
    director_review_output_fingerprint,
    frame_review_input_fingerprint,
    frame_review_output_fingerprint,
    generation_payload_fingerprint,
    image_file_fingerprint,
    requested_story_formats,
    review_response_fingerprint,
    storyboard_source_fingerprint,
    validate_director_storyboard,
    validate_frame_readability,
)


TEST_FORMATS = ("instagram_post", "reels_stories")
FORMAT_CONTRACT_FINGERPRINT = format_contract_fingerprint(TEST_FORMATS)
TEST_DIMENSIONS = {
    "instagram_post": (108, 144),
    "reels_stories": (108, 192),
    "square": (108, 108),
}


def _slides() -> list[dict]:
    return [
        {
            "slide": 1,
            "copy": "He didn't marry peace.",
            "role": "establisher",
            "visual": "A wide wedding-corridor frame establishes Aachu moving ahead and Zuv noticing.",
            "emotion": "playful friction",
            "continuity_lock": "same wedding and wardrobe",
        },
        {
            "slide": 2,
            "copy": "He married ‘I'm leaving’ with no shoes on.",
            "role": "peak",
            "visual": "Aachu points toward the exit barefoot while Zuv calmly holds both of her juttis.",
            "emotion": "comic familiarity",
            "continuity_lock": "same wedding and wardrobe",
        },
        {
            "slide": 3,
            "copy": "And stayed for every version of it.",
            "role": "release",
            "visual": "A close reaction frame reconnects their eye-lines as he offers the shoes back.",
            "emotion": "earned tenderness",
            "continuity_lock": "same wedding and wardrobe",
        },
    ]


def _director_slide(number: int) -> dict:
    is_hero = number == 2
    return {
        "slide": number,
        "status": "PASS",
        "inference_match": True,
        "narrative_job": ["establish wedding geography", "peak comic proof", "release into tenderness"][number - 1],
        "silent_read": (
            "She is making an impulsive barefoot exit while he already knows to carry both shoes."
            if is_hero
            else "The couple's changing distance and eye-line make the wedding disagreement soften."
        ),
        "change_from_previous": (
            "Establishes the wedding corridor and their opposite movement."
            if number == 1
            else "Changes the object state, body distance, and emotional pressure from the prior frame."
        ),
        "critic_evidence": "The blind critic cited feet, hands, gaze, distance, and the shoe state.",
        "staged_action": {
            "subject": "Aachu",
            "action": "points toward the exit while walking barefoot" if is_hero else "changes her distance from Zuv",
            "target_or_object": "the exit and her juttis" if is_hero else "Zuv and the wedding corridor",
            "reaction_or_consequence": "Zuv holds both shoes with familiar calm" if is_hero else "their eye-lines reconnect",
        },
        "pov": {
            "owner": "the couple's shared comic point of view",
            "audience_knows": "this disagreement is a familiar ritual rather than a breakup",
            "audience_feels": "recognition first and tenderness underneath",
        },
        "shot": {
            "size": ["wide shot", "medium full-body shot", "close reaction shot"][number - 1],
            "angle": "eye-level three-quarter angle",
            "camera_position": "inside the wedding corridor facing their crossing paths",
            "focal_subject": "bare feet and the shoes in Zuv's hands" if is_hero else "the changing couple distance",
            "story_reason": "The view keeps action, object ownership, and reaction readable together.",
        },
        "blocking": {
            "hands": "Her hand points away while both of his hands hold the shoes.",
            "gaze": "She looks toward the exit while he watches her with recognition.",
            "body_distance": "Several feet of comic disagreement remain between them.",
            "posture_or_feet": "Her bare feet move away while his stance stays grounded.",
        },
        "setting": {
            "sub_location": "wedding venue corridor",
            "time": "late wedding evening",
            "motivated_light": "warm spill from the occupied wedding hall",
            "story_trace": "scattered petals and her missing shoes show what just happened",
        },
        "story_evidence": [
            {
                "carrier": "the pair of juttis",
                "observable_state": "both shoes are in Zuv's hands while Aachu is barefoot",
                "narrative_job": "compress her exit bravado, his familiarity, and practical care",
            }
        ],
        "text_image_relationship": "interdependent",
        "continuity": {
            "incoming_state": "the same wedding, clothes, corridor, and disagreement",
            "outgoing_state": "the shoes and eye-line move toward an offered return",
        },
        "entity_contract": {
            "expected_people": 2,
            "background_people": [],
            "reflections": [],
            "forbidden_entities": ["duplicate couple", "invented wedding guest in foreground"],
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [],
    }


def _blind_card(number: int) -> dict:
    return {
        "slide": number,
        "visible_people": ["Aachu", "Zuv"],
        "visible_setting": "A wedding venue corridor with warm hall light and scattered petals.",
        "observable_action": "Aachu changes distance while Zuv responds through a visible shoe action.",
        "hands_and_contact": "Her pointing hand and his hands holding or returning both shoes remain visible.",
        "gaze": "Their eye-lines move from different destinations back toward each other.",
        "body_blocking": "Her moving posture contrasts with his grounded stance in the shared corridor.",
        "object_state": "The same pair of juttis changes from left behind to held and offered back.",
        "camera_view": ["wide corridor view", "medium full-body view", "close reaction view"][number - 1],
        "visible_continuity": "Wedding clothes, corridor, couple identity, and shoe ownership stay traceable.",
    }


def _passing_plan(
    slides: list[dict] | None = None,
    *,
    prompt_pack: dict | None = None,
    creator_correction_fingerprint: str = EMPTY_CREATOR_CORRECTION_FINGERPRINT,
) -> dict:
    slides = slides or _slides()
    prompt_pack = {} if prompt_pack is None else prompt_pack
    blind_cards = [_blind_card(number) for number in range(1, 4)]
    raw_response = (
        "The critic read a wedding disagreement, a familiar barefoot exit ritual, "
        "and a shoe-return reconciliation from the observable cards alone."
    )
    plan = {
        "status": "PASS",
        "can_generate": True,
        "issues": [],
        "director_storyboard": {
            "status": "PASS",
            "event": "copy_hidden_storyboard_read",
            "copy_locked": True,
            "copy_hidden": True,
            "intent_hidden": True,
            "copy_lock_evidence": "The exact three slide lines were locked before this review payload was created.",
            "author_id": "route-author-00",
            "reviewer_id": "blind-director-01",
            "reviewer_evidence": "The reviewer received only staged visual cards and reported the inferred story before seeing copy.",
            "requested_formats": ["instagram_post", "reels_stories"],
            "format_contract_fingerprint": FORMAT_CONTRACT_FINGERPRINT,
            "creator_correction_fingerprint": creator_correction_fingerprint,
            "generation_payload_fingerprint": generation_payload_fingerprint(
                prompt_pack
            ),
            "blind_cards": blind_cards,
            "blind_input_fingerprint": blind_cards_fingerprint(blind_cards),
            "source_fingerprint": storyboard_source_fingerprint(slides),
            "sequence_mode": "causal_sequence",
            "physical_event": "A wedding disagreement turns into a barefoot exit ritual and a quiet shoe return.",
            "emotional_arc": "public comic friction becomes private proof that he knows her patterns.",
            "relationship_change": "They move from opposite directions back into a shared eye-line and practical care.",
            "sequence_read": "The corridor establishes distance, the juttis reveal history, and the return releases tension.",
            "visual_variables": ["body distance", "object ownership"],
            "hero_receipt_slide": 2,
            "setup_payoff_ledger": [
                {
                    "setup": "Aachu moves ahead without stopping for her shoes.",
                    "payoff": "Zuv is already carrying both shoes and later offers them back.",
                    "changed_meaning": "The shoes change from missing item to evidence that he knows the ritual.",
                }
            ],
            "object_motif_ledger": [
                {
                    "object": "Aachu's juttis",
                    "initial_state": "left behind while she walks barefoot",
                    "later_state": "held and returned by Zuv",
                    "story_job": "make familiarity and care physically visible",
                }
            ],
            "slides": [_director_slide(number) for number in range(1, 4)],
            "issues": [],
            "director_event_fingerprint_version": DIRECTOR_EVENT_FINGERPRINT_VERSION,
            "review_provenance": {
                "schema_version": REVIEW_PROVENANCE_VERSION,
                "author_task_id": "route-author-00",
                "author_run_id": "route-author-run-00",
                "reviewer_task_id": "blind-director-01",
                "reviewer_run_id": "blind-director-run-01",
                "input_fingerprint": blind_cards_fingerprint(blind_cards),
                "raw_response": raw_response,
                "raw_response_fingerprint": review_response_fingerprint(raw_response),
                "output_fingerprint": "",
            },
        },
    }
    director = plan["director_storyboard"]
    director["review_provenance"]["output_fingerprint"] = (
        director_review_output_fingerprint(director)
    )
    director["director_event_fingerprint"] = director_event_fingerprint(director)
    return plan


def _passing_readability(
    tmp_path: Path,
    plan: dict,
    formats: tuple[str, ...] = TEST_FORMATS,
) -> dict:
    frames = []
    folders = {
        "instagram_post": "final",
        "reels_stories": "final-reels-stories",
        "square": "final-square",
    }
    for number in range(1, 4):
        for output_format in formats:
            folder = folders[output_format]
            path = tmp_path / folder / f"slide-{number:02d}.png"
            path.parent.mkdir(parents=True, exist_ok=True)
            format_offset = 0 if output_format == "instagram_post" else 40
            Image.new(
                "RGB",
                TEST_DIMENSIONS[output_format],
                (220 + number, 205 + format_offset + number, 180 + number),
            ).save(path)
            frames.append(
                {
                    "slide": number,
                    "format": output_format,
                    "file": str(path.relative_to(tmp_path)),
                    "status": "PASS",
                    "expected_silent_read": _director_slide(number)["silent_read"],
                    "observed_image_first_read": "The rendered frame shows the intended action, reaction, and changing relationship distance.",
                    "core_action_legible": True,
                    "relationship_turn_legible": True,
                    "focal_hierarchy": "The eye reaches the acting bodies and shoe evidence before decorative wedding detail.",
                    "hands_gaze_prop_legible": True,
                    "storyboard_match": True,
                    "native_format_readability": True,
                    "copy_visual_contradictions": [],
                    "unexpected_story": [],
                    "match_rationale": "Observed hands, feet, gaze, and object ownership match the locked director card.",
                    "evidence": "The reviewer inspected this native file image-first and cited visible pixels, not prompt intent.",
                    "image_fingerprint": image_file_fingerprint(path),
                }
            )
    director = plan["director_storyboard"]
    raw_response = (
        "The image-first critic saw the intended physical actions, object transfers, "
        "and relationship turn in every current native frame."
    )
    check = {
        "pass": True,
        "status": "PASS",
        "event": "rendered_frame_story_audit",
        "image_first": True,
        "reviewer_id": "rendered-editor-02",
        "reviewer_evidence": "A second critic inspected current rendered pixels before receiving the board or exact copy.",
        "source_director_event_fingerprint": director["director_event_fingerprint"],
        "reviewed_native_formats": list(formats),
        "sequence_read": "The rendered sequence preserves the move from distance through comic proof to reconnection.",
        "relationship_turn": "Zuv's calm shoe-holding reframes her exit as a known ritual with emotional safety.",
        "setup_payoff_evidence": "The missing shoes set up their visible return and changed meaning in the final beat.",
        "weakest_frame": "Slide one is the least compressed frame but its geography remains necessary and readable.",
        "repair_decision": "No repair required after both native formats matched the directed story.",
        "frames": frames,
        "issues": [],
        "review_provenance": {
            "schema_version": REVIEW_PROVENANCE_VERSION,
            "reviewer_task_id": "rendered-editor-02",
            "reviewer_run_id": "rendered-editor-run-02",
            "input_fingerprint": frame_review_input_fingerprint(frames),
            "raw_response": raw_response,
            "raw_response_fingerprint": review_response_fingerprint(raw_response),
            "output_fingerprint": "",
        },
    }
    check["review_provenance"]["output_fingerprint"] = frame_review_output_fingerprint(check)
    return check


def _expected_frame_bindings(
    formats: tuple[str, ...] = ("instagram_post", "reels_stories"),
) -> dict[tuple[int, str], dict[str, object]]:
    folders = {
        "instagram_post": "final",
        "reels_stories": "final-reels-stories",
        "square": "final-square",
    }
    return {
        (number, output_format): {
            "relative_path": f"{folders[output_format]}/slide-{number:02d}.png",
            "dimensions": TEST_DIMENSIONS[output_format],
        }
        for number in range(1, 4)
        for output_format in formats
    }


def _validate_passing_readability(
    tmp_path: Path,
    plan: dict,
    check: dict,
    *,
    formats: tuple[str, ...] = ("instagram_post", "reels_stories"),
    expected_generation_fingerprint: str | None = None,
) -> list[str]:
    director = plan["director_storyboard"]
    return validate_frame_readability(
        check,
        slide_count=3,
        required_formats=formats,
        expected_director_event_fingerprint=director_event_fingerprint(plan),
        event_a_review_provenance=director["review_provenance"],
        event_a_creator_correction_fingerprint=director[
            "creator_correction_fingerprint"
        ],
        expected_creator_correction_fingerprint=(
            current_creator_correction_fingerprint(tmp_path)
        ),
        event_a_generation_payload_fingerprint=director[
            "generation_payload_fingerprint"
        ],
        expected_generation_payload_fingerprint=(
            expected_generation_fingerprint
            or director["generation_payload_fingerprint"]
        ),
        expected_frame_bindings=_expected_frame_bindings(formats),
        director_author_id="route-author-00",
        director_reviewer_id="blind-director-01",
        package_dir=tmp_path,
        provenance_package_dir=tmp_path,
        require_files=True,
    )


def _refresh_event_a_fingerprints(plan: dict) -> None:
    director = plan["director_storyboard"]
    director["review_provenance"]["output_fingerprint"] = (
        director_review_output_fingerprint(director)
    )
    director["director_event_fingerprint"] = director_event_fingerprint(director)


def _refresh_event_b_fingerprints(check: dict) -> None:
    provenance = check["review_provenance"]
    provenance["input_fingerprint"] = frame_review_input_fingerprint(check["frames"])
    provenance["output_fingerprint"] = frame_review_output_fingerprint(check)


def _validate_event_a(
    plan: dict,
    *,
    package_dir: Path | None = None,
    expected_generation_fingerprint: str | None = None,
) -> list[str]:
    director = plan["director_storyboard"]
    return validate_director_storyboard(
        plan,
        slide_count=3,
        expected_slides=_slides(),
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=(
            current_creator_correction_fingerprint(package_dir)
            if package_dir is not None
            else EMPTY_CREATOR_CORRECTION_FINGERPRINT
        ),
        expected_generation_payload_fingerprint=(
            expected_generation_fingerprint
            or director["generation_payload_fingerprint"]
        ),
        provenance_package_dir=package_dir,
    )


def test_juttis_style_director_storyboard_passes() -> None:
    slides = _slides()
    issues = validate_director_storyboard(
        _passing_plan(slides),
        slide_count=len(slides),
        expected_slides=slides,
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
    )
    assert issues == []


def test_generic_cozy_room_cannot_pass_as_director_evidence() -> None:
    plan = _passing_plan()
    hero = plan["director_storyboard"]["slides"][1]
    hero["silent_read"] = "cozy room"
    hero["story_evidence"] = [
        {"carrier": "some props", "observable_state": "warm scene", "narrative_job": "couple moment"}
    ]

    issues = validate_director_storyboard(
        plan,
        slide_count=3,
        expected_slides=_slides(),
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
    )

    joined = " ".join(issues)
    assert "silent_read" in joined
    assert "story_evidence" in joined


def test_copy_or_visual_change_invalidates_director_fingerprint() -> None:
    plan = _passing_plan()
    changed = _slides()
    changed[1]["copy"] = "A changed locked line"

    issues = validate_director_storyboard(
        plan,
        slide_count=3,
        expected_slides=changed,
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
    )

    assert any("stale" in issue for issue in issues)


def test_pre_copy_or_self_review_cannot_unlock_generation() -> None:
    plan = _passing_plan()
    plan["director_storyboard"]["copy_locked"] = False
    plan["director_storyboard"]["reviewer_id"] = "route-author-00"

    issues = validate_director_storyboard(
        plan,
        slide_count=3,
        expected_slides=_slides(),
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
    )

    joined = " ".join(issues)
    assert "pre-copy direction is advisory" in joined
    assert "independent from the route author" in joined


def test_blind_payload_rejects_intended_story_fields() -> None:
    plan = _passing_plan()
    plan["director_storyboard"]["blind_cards"][0]["narrative_job"] = "establisher"
    plan["director_storyboard"]["blind_cards"][0]["observable_action"] = (
        "The observable action was changed after the blind review."
    )

    issues = validate_director_storyboard(
        plan,
        slide_count=3,
        expected_slides=_slides(),
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
    )

    assert any("not allowed in the blind payload" in issue for issue in issues)
    assert any("blind_input_fingerprint is stale" in issue for issue in issues)


def test_requested_story_formats_follow_locked_generation_metadata(tmp_path: Path) -> None:
    (tmp_path / "image-generation.json").write_text(
        json.dumps({"requested_formats": ["instagram_post"]}),
        encoding="utf-8",
    )
    (tmp_path / "final-reels-stories").mkdir()
    (tmp_path / "final-reels-stories" / "slide-01.png").write_bytes(b"stale-extra")

    assert requested_story_formats(tmp_path) == ("instagram_post",)


def test_rendered_frame_audit_requires_both_native_formats(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    check["frames"] = [
        frame for frame in check["frames"] if frame["format"] == "instagram_post"
    ]

    issues = validate_frame_readability(
        check,
        slide_count=3,
        required_formats=("instagram_post", "reels_stories"),
        expected_director_event_fingerprint=director_event_fingerprint(plan),
        event_a_review_provenance=plan["director_storyboard"]["review_provenance"],
        event_a_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        event_a_generation_payload_fingerprint=generation_payload_fingerprint({}),
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
        expected_frame_bindings=_expected_frame_bindings(),
        director_author_id="route-author-00",
        director_reviewer_id="blind-director-01",
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("reels_stories" in issue for issue in issues)


def test_rendered_frame_audit_detects_contradiction_and_stale_image(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    failed = check["frames"][2]
    failed["copy_visual_contradictions"] = ["Aachu is shown wearing the shoes already."]
    failed_path = tmp_path / failed["file"]
    failed_path.write_bytes(b"changed-after-review")

    issues = _validate_passing_readability(tmp_path, plan, check)

    joined = " ".join(issues)
    assert "copy_visual_contradictions" in joined
    assert "image_fingerprint is stale" in joined


def test_rendered_frame_audit_passes_current_independent_review(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert issues == []


def test_rendered_frame_audit_passes_full_square_contract(tmp_path: Path) -> None:
    formats = ("square",)
    plan = _passing_plan()
    director = plan["director_storyboard"]
    director["requested_formats"] = list(formats)
    director["format_contract_fingerprint"] = format_contract_fingerprint(formats)
    _refresh_event_a_fingerprints(plan)
    check = _passing_readability(tmp_path, plan, formats)

    issues = _validate_passing_readability(
        tmp_path,
        plan,
        check,
        formats=formats,
    )

    assert issues == []


def test_rendered_frame_reviewer_cannot_be_route_author(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    check["reviewer_id"] = "route-author-00"

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("independent from the route author" in issue for issue in issues)


def test_external_file_cannot_substitute_for_canonical_package_asset(
    tmp_path: Path,
) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    external = tmp_path.parent / "unrelated-approved-looking-frame.png"
    Image.new("RGB", TEST_DIMENSIONS["instagram_post"], "ivory").save(external)
    frame = check["frames"][0]
    frame["file"] = str(external)
    frame["image_fingerprint"] = image_file_fingerprint(external)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    joined = " ".join(issues)
    assert "never absolute" in joined
    assert "canonical package asset final/slide-01.png" in joined


def test_event_b_is_invalid_after_director_restaging(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    approved_event = check["source_director_event_fingerprint"]
    plan["director_storyboard"]["slides"][1]["blocking"]["hands"] = (
        "Her hands now hold both shoes while his hands point toward the exit."
    )
    _refresh_event_a_fingerprints(plan)

    assert director_event_fingerprint(plan) != approved_event
    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("stale for the complete current director Event A" in issue for issue in issues)


def test_duplicate_frame_path_reuse_is_rejected(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    first_path = tmp_path / check["frames"][0]["file"]
    duplicate = check["frames"][1]
    duplicate["file"] = check["frames"][0]["file"]
    duplicate["image_fingerprint"] = image_file_fingerprint(first_path)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("reuses the asset already bound" in issue for issue in issues)


def test_traversal_path_is_rejected_even_when_target_exists(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    outside = tmp_path.parent / "traversal-frame.png"
    Image.new("RGB", TEST_DIMENSIONS["instagram_post"], "ivory").save(outside)
    frame = check["frames"][0]
    frame["file"] = f"../{outside.name}"
    frame["image_fingerprint"] = image_file_fingerprint(outside)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("must not contain traversal" in issue for issue in issues)


def test_non_image_bytes_at_canonical_path_are_rejected(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    frame = check["frames"][0]
    path = tmp_path / frame["file"]
    path.write_bytes(b"not an image despite the png extension")
    frame["image_fingerprint"] = image_file_fingerprint(path)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("is not a decodable image" in issue for issue in issues)


def test_wrong_native_dimensions_are_rejected(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    frame = check["frames"][0]
    path = tmp_path / frame["file"]
    Image.new("RGB", (107, 144), "ivory").save(path)
    frame["image_fingerprint"] = image_file_fingerprint(path)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("dimensions are 107x144, expected 108x144" in issue for issue in issues)


def test_event_b_provenance_must_bind_input_output_and_independent_run(
    tmp_path: Path,
) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    provenance = check["review_provenance"]
    provenance["reviewer_run_id"] = "route-author-run-00"
    provenance["input_fingerprint"] = "sha256:" + "2" * 64
    provenance["raw_response"] = "A different response added after the recorded hash."
    provenance["output_fingerprint"] = frame_review_output_fingerprint(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    joined = " ".join(issues)
    assert "input_fingerprint is stale" in joined
    assert "raw_response_fingerprint is stale" in joined
    assert "reviewer run ID must differ" in joined


def test_event_a_provenance_cannot_self_certify_with_changed_ids() -> None:
    plan = _passing_plan()
    director = plan["director_storyboard"]
    director["review_provenance"]["reviewer_run_id"] = "route-author-run-00"
    _refresh_event_a_fingerprints(plan)

    issues = validate_director_storyboard(
        plan,
        slide_count=3,
        expected_slides=_slides(),
        expected_formats=("instagram_post", "reels_stories"),
        expected_format_contract_fingerprint=FORMAT_CONTRACT_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
    )

    assert any("author and reviewer run IDs must differ" in issue for issue in issues)


def test_event_a_hash_only_provenance_cannot_pass() -> None:
    plan = _passing_plan()
    plan["director_storyboard"]["review_provenance"].pop("raw_response")
    _refresh_event_a_fingerprints(plan)

    issues = _validate_event_a(plan)

    assert any("exactly one critic response source" in issue for issue in issues)


def test_event_b_hash_only_provenance_cannot_pass(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    check["review_provenance"].pop("raw_response")
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("exactly one critic response source" in issue for issue in issues)


def test_package_local_event_a_raw_response_artifact_passes(tmp_path: Path) -> None:
    plan = _passing_plan()
    provenance = plan["director_storyboard"]["review_provenance"]
    response = provenance.pop("raw_response")
    artifact = tmp_path / "reviews" / "event-a-critic.txt"
    artifact.parent.mkdir()
    artifact.write_text(response, encoding="utf-8")
    provenance["raw_response_artifact"] = "reviews/event-a-critic.txt"
    _refresh_event_a_fingerprints(plan)

    assert _validate_event_a(plan, package_dir=tmp_path) == []


def test_package_local_event_b_raw_response_artifact_passes(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    provenance = check["review_provenance"]
    response = provenance.pop("raw_response")
    artifact = tmp_path / "reviews" / "event-b-critic.txt"
    artifact.parent.mkdir()
    artifact.write_text(response, encoding="utf-8")
    provenance["raw_response_artifact"] = "reviews/event-b-critic.txt"
    _refresh_event_b_fingerprints(check)

    assert _validate_passing_readability(tmp_path, plan, check) == []


def test_external_raw_response_artifact_is_rejected(tmp_path: Path) -> None:
    plan = _passing_plan()
    provenance = plan["director_storyboard"]["review_provenance"]
    response = provenance.pop("raw_response")
    external = tmp_path.parent / "external-critic-evidence.txt"
    external.write_text(response, encoding="utf-8")
    provenance["raw_response_artifact"] = str(external)
    _refresh_event_a_fingerprints(plan)

    issues = _validate_event_a(plan, package_dir=tmp_path)

    assert any("never absolute" in issue for issue in issues)


def test_traversal_raw_response_artifact_is_rejected(tmp_path: Path) -> None:
    plan = _passing_plan()
    provenance = plan["director_storyboard"]["review_provenance"]
    response = provenance.pop("raw_response")
    external = tmp_path.parent / "traversal-critic-evidence.txt"
    external.write_text(response, encoding="utf-8")
    provenance["raw_response_artifact"] = f"../{external.name}"
    _refresh_event_a_fingerprints(plan)

    issues = _validate_event_a(plan, package_dir=tmp_path)

    assert any("must not contain traversal" in issue for issue in issues)


def test_symlinked_raw_response_artifact_is_rejected(tmp_path: Path) -> None:
    plan = _passing_plan()
    provenance = plan["director_storyboard"]["review_provenance"]
    response = provenance.pop("raw_response")
    reviews = tmp_path / "reviews"
    reviews.mkdir()
    target = reviews / "critic-target.txt"
    target.write_text(response, encoding="utf-8")
    link = reviews / "critic-link.txt"
    link.symlink_to(target)
    provenance["raw_response_artifact"] = "reviews/critic-link.txt"
    _refresh_event_a_fingerprints(plan)

    issues = _validate_event_a(plan, package_dir=tmp_path)

    assert any("not a symlink" in issue for issue in issues)


def test_changed_raw_response_artifact_invalidates_hash(tmp_path: Path) -> None:
    plan = _passing_plan()
    provenance = plan["director_storyboard"]["review_provenance"]
    response = provenance.pop("raw_response")
    artifact = tmp_path / "reviews" / "event-a-critic.txt"
    artifact.parent.mkdir()
    artifact.write_text(response, encoding="utf-8")
    provenance["raw_response_artifact"] = "reviews/event-a-critic.txt"
    _refresh_event_a_fingerprints(plan)
    artifact.write_text("The critic evidence changed after approval was recorded.", encoding="utf-8")

    issues = _validate_event_a(plan, package_dir=tmp_path)

    assert any("stale for raw_response_artifact" in issue for issue in issues)


def test_new_creator_correction_revision_invalidates_event_a_and_b(
    tmp_path: Path,
) -> None:
    plan = _passing_plan(
        creator_correction_fingerprint=current_creator_correction_fingerprint(tmp_path)
    )
    check = _passing_readability(tmp_path, plan)
    (tmp_path / "creator-correction.json").write_text(
        json.dumps({"status": "REVISE", "revision": 1}),
        encoding="utf-8",
    )

    event_a_issues = _validate_event_a(plan, package_dir=tmp_path)
    event_b_issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("creator_correction_fingerprint is stale" in issue for issue in event_a_issues)
    assert any("does not bind the current creator-correction" in issue for issue in event_b_issues)


def test_hardlinked_frame_cannot_satisfy_two_expected_assets(tmp_path: Path) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    first = tmp_path / check["frames"][0]["file"]
    second_frame = check["frames"][2]
    second = tmp_path / second_frame["file"]
    second.unlink()
    second.hardlink_to(first)
    second_frame["image_fingerprint"] = image_file_fingerprint(second)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("same hardlinked asset" in issue for issue in issues)


def test_copied_duplicate_pixels_cannot_satisfy_two_expected_assets(
    tmp_path: Path,
) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)
    first = tmp_path / check["frames"][0]["file"]
    second_frame = check["frames"][2]
    second = tmp_path / second_frame["file"]
    second.write_bytes(first.read_bytes())
    second_frame["image_fingerprint"] = image_file_fingerprint(second)
    _refresh_event_b_fingerprints(check)

    issues = _validate_passing_readability(tmp_path, plan, check)

    assert any("duplicates the exact rendered bytes" in issue for issue in issues)


def test_final_audit_fails_closed_without_expected_asset_bindings(
    tmp_path: Path,
) -> None:
    plan = _passing_plan()
    check = _passing_readability(tmp_path, plan)

    issues = validate_frame_readability(
        check,
        slide_count=3,
        required_formats=("instagram_post", "reels_stories"),
        expected_director_event_fingerprint=director_event_fingerprint(plan),
        event_a_review_provenance=plan["director_storyboard"]["review_provenance"],
        event_a_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        expected_creator_correction_fingerprint=EMPTY_CREATOR_CORRECTION_FINGERPRINT,
        event_a_generation_payload_fingerprint=generation_payload_fingerprint({}),
        expected_generation_payload_fingerprint=generation_payload_fingerprint({}),
        package_dir=tmp_path,
        require_files=True,
    )

    assert any("requires caller-resolved expected_frame_bindings" in issue for issue in issues)


def test_fixture_is_json_serializable() -> None:
    json.dumps(_passing_plan(), ensure_ascii=False)


def test_generation_boundary_rejects_bare_pass_flags(tmp_path: Path) -> None:
    from pipeline.stages.codex_builtin_image_generation import (
        visual_plan_quality_gate_reason,
    )

    (tmp_path / "slides.json").write_text(json.dumps(_slides()), encoding="utf-8")
    (tmp_path / "prompt-pack.json").write_text(
        json.dumps({"slides": [{"slide": 1, "text": "test"}]}),
        encoding="utf-8",
    )
    (tmp_path / "visual-plan-quality.json").write_text(
        json.dumps({"status": "PASS", "can_generate": True, "issues": []}),
        encoding="utf-8",
    )

    reason = visual_plan_quality_gate_reason(tmp_path)

    assert reason is not None
    assert "director_storyboard" in reason


def test_generation_boundary_accepts_current_director_event(tmp_path: Path) -> None:
    from pipeline.stages.codex_builtin_image_generation import (
        visual_plan_quality_gate_reason,
    )

    slides = _slides()
    prompt_pack = {"slides": [{"slide": 1, "text": "locked generation payload"}]}
    write_format_contract(tmp_path, TEST_FORMATS, source="test")
    (tmp_path / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
    (tmp_path / "prompt-pack.json").write_text(
        json.dumps(prompt_pack), encoding="utf-8"
    )
    (tmp_path / "visual-plan-quality.json").write_text(
        json.dumps(_passing_plan(slides, prompt_pack=prompt_pack)),
        encoding="utf-8",
    )

    assert visual_plan_quality_gate_reason(tmp_path) is None


def test_generation_boundary_rejects_prompt_pack_edit_after_event_a(
    tmp_path: Path,
) -> None:
    from pipeline.stages.codex_builtin_image_generation import (
        visual_plan_quality_gate_reason,
    )

    slides = _slides()
    prompt_pack = {
        "slides": [
            {
                "slide": 1,
                "text": slides[0]["copy"],
                "visual": slides[0]["visual"],
                "pose": "Aachu moves ahead while Zuv turns toward her.",
                "props": "Both juttis remain visibly in Zuv's hands.",
                "background": "The locked wedding corridor remains readable.",
            }
        ]
    }
    write_format_contract(tmp_path, TEST_FORMATS, source="test")
    (tmp_path / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
    (tmp_path / "prompt-pack.json").write_text(
        json.dumps(prompt_pack), encoding="utf-8"
    )
    (tmp_path / "visual-plan-quality.json").write_text(
        json.dumps(_passing_plan(slides, prompt_pack=prompt_pack)),
        encoding="utf-8",
    )
    assert visual_plan_quality_gate_reason(tmp_path) is None

    prompt_pack["slides"][0]["pose"] = (
        "Both partners now face away and the shoe action is removed."
    )
    (tmp_path / "prompt-pack.json").write_text(
        json.dumps(prompt_pack), encoding="utf-8"
    )

    reason = visual_plan_quality_gate_reason(tmp_path)

    assert reason is not None
    assert "generation_payload_fingerprint is stale" in reason
