from __future__ import annotations

import copy
import hashlib
import json
import pytest
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import (
    locked_format_contract_fingerprint,
    write_format_contract,
)
from pipeline.stages.carousel_pixel_qa import (
    PIXEL_QA_SCHEMA_VERSION,
    asset_binding_fingerprint,
    bind_final_qa,
    bind_proof_qa,
    manifest_fingerprint,
    validate_final_qa,
    validate_proof_qa,
)
from tests.helpers.carousel_qa import cinematic_slide_fields, passing_cinematic_story_frame


COPY = "We knew who. We were learning how."


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_png(
    path: Path,
    size: tuple[int, int] = (1080, 1440),
    color: str | tuple[int, int, int] = "ivory",
) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path)


def _package(tmp_path: Path) -> Path:
    package = tmp_path / "carousel"
    package.mkdir()
    write_format_contract(package, ["instagram_post"], source="test")
    refs = {
        "aachu": "refs/aachu/face.png",
        "zuv": "refs/zuv/face.png",
        "together_face": "refs/together/face.png",
        "together_body": "refs/together/body.png",
    }
    for path in refs.values():
        _write_png(package / path, (32, 32))
    style_ref = "refs/style/watercolor.png"
    _write_png(package / style_ref, (32, 32))
    _write_json(
        package / "slides.json",
        [
            {
                "slide": 1,
                "copy": COPY,
                "physical_action": "They pull one map in opposite directions while its fold tears.",
                **cinematic_slide_fields(1, 1),
            }
        ],
    )
    style_hash = "sha256:" + hashlib.sha256((package / style_ref).read_bytes()).hexdigest()
    _write_json(
        package / "prompt-pack.json",
        {
            "identity_reference_images": list(refs.values()),
            "style_profile": {
                "id": "cinematic-observational-watercolor",
                "version": "1.0.0",
                "reference": {
                    "path": style_ref,
                    "sha256": style_hash,
                    "attachment_count": 1,
                },
            },
        },
    )
    _write_json(
        package / "creative-context.json",
        {
            "identity_reference_selection": {
                "selected_references": [
                    {"path": refs["aachu"], "role": "Aachu identity anchor"},
                    {"path": refs["zuv"], "role": "Zuv identity anchor"},
                    {"path": refs["together_face"], "role": "together face/scale anchor"},
                    {"path": refs["together_body"], "role": "together body/posture anchor"},
                ]
            }
        },
    )
    return package


def _binding(
    package: Path,
    *,
    path: str = ".internal/visual-quarantine/slide-01/attempt-01/instagram_post.png",
    color: str | tuple[int, int, int] = "ivory",
) -> dict:
    image = package / path
    _write_png(image, color=color)
    binding = {
        "path": path,
        "sha256": "sha256:" + hashlib.sha256(image.read_bytes()).hexdigest(),
        "width": 1080,
        "height": 1440,
    }
    binding["binding_sha256"] = asset_binding_fingerprint(1, "instagram_post", binding)
    return binding


def _checks(package: Path) -> dict:
    refs = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))[
        "identity_reference_images"
    ]
    return {
        "physical_action": {
            "status": "PASS",
            "evidence": "Both people visibly pull the same map in opposite directions.",
        },
        "relationship_state": {
            "status": "PASS",
            "evidence": "Their opposing pull shows disagreement while the shared map keeps them connected.",
        },
        "cinematic_story_frame": passing_cinematic_story_frame(package, 1),
        "entity_spatial_integrity": {
            "status": "PASS",
            "evidence": "Two whole silhouettes and the two focal hands have clear ownership and contact.",
            "expected_people": 2,
            "observed_people": 2,
            "observed_people_names": ["Aachu", "Zuv"],
            "unexpected_entities": [],
            "unexpected_limbs": [],
            "duplicated_limbs": [],
            "ambiguous_contacts": [],
            "silhouette_evidence": "Both bodies remain continuously separated from the table and room planes.",
            "visible_hands": [
                {
                    "owner": "Aachu",
                    "side": "right",
                    "story_required": True,
                    "attachment_traceable": True,
                    "contact_geometry_pass": True,
                    "solid_object_intersection": False,
                    "malformed_or_extra_fingers": False,
                    "contact": "right palm grips the left map edge",
                    "evidence": "Her right forearm and wrist continue cleanly into the gripping hand.",
                },
                {
                    "owner": "Zuv",
                    "side": "left",
                    "story_required": True,
                    "attachment_traceable": True,
                    "contact_geometry_pass": True,
                    "solid_object_intersection": False,
                    "malformed_or_extra_fingers": False,
                    "contact": "left palm grips the right map edge",
                    "evidence": "His left forearm and wrist continue cleanly into the gripping hand.",
                },
            ],
        },
        "identity_wardrobe_accessories": {
            "status": "PASS",
            "evidence": (
                "Aachu retains long dense very dark mostly-straight hair with soft bends, "
                "large expressive dark round-almond eyes and full mostly-straight brows with a low soft arch, "
                "and warm medium-brown skin tone. Zuv retains thick dark curly hair with visible top and side volume, "
                "thick dark brows, and warm brown skin tone; their referenced proportions and clothing also match."
            ),
            "references": {
                "aachu": [refs[0]],
                "zuv": [refs[1]],
                "together": refs[2:],
            },
        },
        "text_brandmark_style_dimensions": {
            "status": "PASS",
            "evidence": "Exact copy and tiny top-right brandmark are visible on the 1080 by 1440 watercolor frame.",
            "expected_text": COPY,
            "observed_text": COPY,
            "observed_brandmark": "@a.storyof.two",
            "style_references": ["refs/style/watercolor.png"],
        },
    }


def _proof_qa(package: Path, binding: dict) -> dict:
    return {
        "schema_version": PIXEL_QA_SCHEMA_VERSION,
        "scope": "proof",
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": [1],
        "slides": [
            {
                "slide": 1,
                "asset_bindings": {"instagram_post": copy.deepcopy(binding)},
                "reviews": {"instagram_post": {"checks": _checks(package)}},
            }
        ],
    }


def _manifest(package: Path, binding: dict) -> dict:
    return {
        "schema_version": "carousel-final-images/v3",
        "selected_formats": ["instagram_post"],
        "format_sha256": locked_format_contract_fingerprint(package),
        "slides": [
            {
                "slide": 1,
                "input_sha256": "sha256:" + "2" * 64,
                "native_outputs": {"instagram_post": copy.deepcopy(binding)},
            }
        ],
    }


def _final_qa(package: Path, manifest: dict) -> dict:
    binding = manifest["slides"][0]["native_outputs"]["instagram_post"]
    return {
        "schema_version": PIXEL_QA_SCHEMA_VERSION,
        "scope": "final",
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": [1],
        "manifest_sha256": manifest_fingerprint(manifest),
        "asset_binding_hashes": {
            "1:instagram_post": asset_binding_fingerprint(1, "instagram_post", binding)
        },
        "slides": [
            {
                "slide": 1,
                "reviews": {"instagram_post": {"checks": _checks(package)}},
            }
        ],
    }


def test_proof_qa_is_bound_to_decoded_pixels_and_current_candidate(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)

    assert validate_proof_qa(
        package,
        qa,
        expected_asset_bindings={
            (1, "instagram_post"): binding,
        },
    ) == []


def test_identity_qa_must_name_references_for_each_selected_role(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    references = qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "identity_wardrobe_accessories"
    ]["references"]
    references["zuv"] = list(references["aachu"])

    issues = validate_proof_qa(package, qa)

    assert issues == [
        "slide 1 instagram_post: identity references.zuv does not match its selected role"
    ]


def test_repo_derives_proof_bindings_from_current_bytes(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    authored = _proof_qa(package, binding)
    del authored["schema_version"]
    del authored["scope"]
    del authored["slides"][0]["asset_bindings"]

    bound = bind_proof_qa(
        package,
        authored,
        [{"slide": 1, "native_outputs": {"instagram_post": binding}}],
    )

    assert bound["schema_version"] == PIXEL_QA_SCHEMA_VERSION
    assert bound["slides"][0]["asset_bindings"]["instagram_post"] == binding
    assert validate_proof_qa(package, bound) == []


def test_repo_rejects_conflicting_authored_proof_inventory(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    authored = _proof_qa(package, binding)
    authored["slides"][0]["asset_bindings"]["instagram_post"]["sha256"] = (
        "sha256:" + "0" * 64
    )

    try:
        bind_proof_qa(
            package,
            authored,
            [{"slide": 1, "native_outputs": {"instagram_post": binding}}],
        )
    except ValueError as exc:
        assert "conflicts with current bytes" in str(exc)
    else:
        raise AssertionError("conflicting authored inventory must fail closed")


def test_semantic_failure_rejects_downstream_passes(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    qa["status"] = "FAIL"
    qa["slides"][0]["reviews"]["instagram_post"]["checks"]["physical_action"] = {
        "status": "FAIL",
        "evidence": "The intended shared-map action is not visible.",
    }

    issues = validate_proof_qa(package, qa)

    assert issues == [
        "slide 1 instagram_post: physical_action is FAIL; downstream PASS is invalid for relationship_state, cinematic_story_frame, entity_spatial_integrity, identity_wardrobe_accessories, text_brandmark_style_dimensions"
    ]


def test_cinematic_gate_rejects_a_staged_non_temporal_frame(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    cinematic = qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "cinematic_story_frame"
    ]
    cinematic["frame_reads_as_caught_event"] = False
    cinematic["before_after_implied"] = False
    cinematic["posed_portrait"] = True

    issues = validate_proof_qa(package, qa)

    assert any("must read as a caught event" in issue for issue in issues)
    assert any("must visibly imply before/after time" in issue for issue in issues)
    assert any("posed portrait framing is not allowed" in issue for issue in issues)


def test_palette_drift_on_exact_reviewed_pixels_blocks_pass(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, color=(242, 198, 45))
    qa = _proof_qa(package, binding)

    issues = validate_proof_qa(package, qa)

    assert any("palette check failed" in issue for issue in issues)


def test_cinematic_gate_rejects_duplicate_observed_evidence(tmp_path: Path) -> None:
    package = _package(tmp_path)
    qa = _proof_qa(package, _binding(package))
    cinematic = qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "cinematic_story_frame"
    ]
    # Coverage still includes every planned carrier; a repeated third record
    # must not be disguised by the set comparison used for plan matching.
    duplicate = dict(cinematic["story_evidence"][0])
    duplicate["carrier"] = "  " + duplicate["carrier"].upper().replace(" ", "  ") + ". "
    cinematic["story_evidence"].append(duplicate)

    issues = validate_proof_qa(package, qa)

    assert any("cinematic review story_evidence contains repeated normalized carriers" in issue for issue in issues)


def test_cinematic_gate_rejects_duplicate_planned_evidence(tmp_path: Path) -> None:
    package = _package(tmp_path)
    slides_path = package / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    evidence = slides[0]["visual_richness"]["story_evidence"]
    evidence[1] = dict(evidence[0])
    _write_json(slides_path, slides)
    qa = _proof_qa(package, _binding(package))

    issues = validate_proof_qa(package, qa)

    assert any("slide plan story_evidence contains repeated normalized carriers" in issue for issue in issues)


def test_cinematic_carrier_matching_normalizes_observations(tmp_path: Path) -> None:
    package = _package(tmp_path)
    qa = _proof_qa(package, _binding(package))
    cinematic = qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "cinematic_story_frame"
    ]
    for evidence in cinematic["story_evidence"]:
        evidence["carrier"] = "  " + evidence["carrier"].upper().replace(" ", "  ") + ". "

    assert validate_proof_qa(package, qa) == []


def test_style_profile_must_bind_exactly_one_board_attachment(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    prompt_path = package / "prompt-pack.json"
    prompt_pack = json.loads(prompt_path.read_text(encoding="utf-8"))
    prompt_pack["style_profile"]["reference"]["attachment_count"] = 2
    prompt_path.write_text(json.dumps(prompt_pack), encoding="utf-8")

    issues = validate_proof_qa(package, qa)

    assert any("exactly one attachment" in issue for issue in issues)


def test_placeholder_qa_cannot_claim_pixel_inspection_or_gate_evidence(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    qa["inspection"] = {
        "method": "prompt_review",
        "decoded_pixels_observed": False,
    }
    qa["slides"][0]["reviews"]["instagram_post"]["checks"]["physical_action"] = {
        "status": "PASS",
        "evidence": "PASS",
    }

    issues = validate_proof_qa(package, qa)

    assert "inspection.method must be codex_view_image" in issues
    assert "inspection.decoded_pixels_observed must be true" in issues
    assert any("physical_action needs concrete observed pixel evidence" in issue for issue in issues)


def test_vague_anatomy_sentence_cannot_pass_entity_integrity(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    qa["slides"][0]["reviews"]["instagram_post"]["checks"]["entity_spatial_integrity"] = {
        "status": "PASS",
        "evidence": "The hands look coherent.",
    }

    issues = validate_proof_qa(package, qa)

    assert any("must inventory every visible hand" in issue for issue in issues)
    assert any("observed people count does not match" in issue for issue in issues)


def test_any_hand_object_intersection_blocks_approval(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    hand = qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "entity_spatial_integrity"
    ]["visible_hands"][0]
    hand["solid_object_intersection"] = True

    issues = validate_proof_qa(package, qa)

    assert any("visible hand 1 may intersect a solid object" in issue for issue in issues)


def test_proof_qa_rejects_tampered_hash_dimensions_and_binding(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    actual = package / binding["path"]
    _write_png(actual, (1080, 1080))

    issues = validate_proof_qa(package, qa)

    assert any("SHA-256 is stale" in issue for issue in issues)
    assert any("recorded dimensions are stale" in issue for issue in issues)
    assert any("expected 1080x1440" in issue for issue in issues)


def test_proof_qa_rejects_path_escape_and_symlink(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = _proof_qa(package, binding)
    escaped = copy.deepcopy(qa)
    escaped["slides"][0]["asset_bindings"]["instagram_post"]["path"] = "../outside.png"

    assert any("must not escape" in issue for issue in validate_proof_qa(package, escaped))

    link = package / ".internal" / "visual-quarantine" / "linked.png"
    link.parent.mkdir(parents=True, exist_ok=True)
    link.symlink_to(package / binding["path"])
    linked = copy.deepcopy(qa)
    linked_binding = linked["slides"][0]["asset_bindings"]["instagram_post"]
    linked_binding["path"] = str(link.relative_to(package))
    linked_binding["binding_sha256"] = asset_binding_fingerprint(1, "instagram_post", linked_binding)
    assert any("symlink" in issue for issue in validate_proof_qa(package, linked))


def test_proof_qa_rejects_third_attempt_for_same_visual_premise(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(
        package,
        path=".internal/visual-quarantine/slide-01/attempt-03/instagram_post.png",
    )
    qa = _proof_qa(package, binding)

    assert any("exceeds two attempts" in issue for issue in validate_proof_qa(package, qa))


def test_final_qa_binds_manifest_without_duplicating_inventory(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)

    assert validate_final_qa(package, qa, manifest) == []
    assert "native_outputs" not in qa["slides"][0]
    assert "asset_bindings" not in qa["slides"][0]


def test_repo_derives_final_manifest_bindings(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    authored = _final_qa(package, manifest)
    del authored["schema_version"]
    del authored["scope"]
    del authored["manifest_sha256"]
    del authored["asset_binding_hashes"]

    bound = bind_final_qa(authored, manifest)

    assert bound["manifest_sha256"] == manifest_fingerprint(manifest)
    assert bound["asset_binding_hashes"] == {
        "1:instagram_post": asset_binding_fingerprint(1, "instagram_post", binding)
    }
    assert validate_final_qa(package, bound, manifest) == []


def test_final_qa_rejects_stale_manifest_and_asset_bindings(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)
    manifest["slides"][0]["input_sha256"] = "sha256:" + "9" * 64

    issues = validate_final_qa(package, qa, manifest)

    assert "visual QA manifest_sha256 is missing or stale" in issues


def test_final_qa_rejects_inventory_duplication_and_incomplete_reviews(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)
    qa["slides"][0]["native_outputs"] = copy.deepcopy(
        manifest["slides"][0]["native_outputs"]
    )
    qa["slides"][0]["reviews"] = {}

    issues = validate_final_qa(package, qa, manifest)

    assert any("duplicates manifest inventory" in issue for issue in issues)
    assert any("reviews must match locked formats" in issue for issue in issues)


def test_final_qa_rejects_inventory_hidden_inside_review(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)
    qa["slides"][0]["reviews"]["instagram_post"]["sha256"] = binding["sha256"]

    assert any(
        "reviews duplicate manifest inventory fields" in issue
        for issue in validate_final_qa(package, qa, manifest)
    )


@pytest.mark.parametrize("observed", ["Nearly the same.", "We knew who.",
                                     COPY + " Forever.", "We knew how. We were learning who."])
def test_final_qa_rejects_corrupted_observed_text(tmp_path: Path, observed: str) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)
    qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "text_brandmark_style_dimensions"
    ]["observed_text"] = observed

    assert "slide 1 instagram_post: rendered text is not exact" in validate_final_qa(
        package, qa, manifest
    )


@pytest.mark.parametrize("unexpected", [["LOVE on the mug"], "", None, False])
def test_final_qa_rejects_extra_lettering_inventory(tmp_path: Path, unexpected) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)
    finish = qa["slides"][0]["reviews"]["instagram_post"]["checks"]["text_brandmark_style_dimensions"]
    finish["unexpected_visible_text"] = unexpected
    assert "slide 1 instagram_post: unexpected visible text must be absent" in validate_final_qa(
        package, qa, manifest
    )
    finish["unexpected_visible_text"] = []
    assert not validate_final_qa(package, qa, manifest)
