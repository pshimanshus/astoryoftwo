from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_format_contract import (
    locked_format_contract_fingerprint,
    write_format_contract,
)
from pipeline.stages.carousel_pixel_qa import (
    LEGACY_PIXEL_QA_SCHEMA_VERSIONS,
    PIXEL_QA_SCHEMA_VERSION,
    asset_binding_fingerprint,
    bind_final_qa,
    bind_proof_qa,
    manifest_fingerprint,
    scene_contract_fingerprint,
    validate_final_qa,
    validate_proof_qa,
)


COPY = "We knew who. We were learning how."


def _write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def _write_png(path: Path, size: tuple[int, int] = (1080, 1440)) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, "ivory").save(path)


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
        [{"slide": 1, "copy": COPY, "physical_action": "They pull one map in opposite directions while its fold tears."}],
    )
    _write_json(
        package / "prompt-pack.json",
        {
            "identity_reference_images": list(refs.values()),
            "style_reference_images": [style_ref],
            "slides": [{"slide": 1}],
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


def _binding(package: Path, *, path: str = ".internal/visual-quarantine/slide-01/attempt-01/instagram_post.png") -> dict:
    image = package / path
    _write_png(image)
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
        "entity_spatial_integrity": {
            "status": "PASS",
            "evidence": "Two whole silhouettes, four coherent hands, and one shared map have clear ownership and contact.",
        },
        "identity_wardrobe_accessories": {
            "status": "PASS",
            "evidence": "Aachu and Zuv retain their referenced faces, hair, proportions, clothing, and watches.",
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


def _scene_contract() -> dict:
    """A planned scene contract; fixtures test record validation, not vision."""

    return {
        "continuity": [
            {
                "id": "shared-map",
                "planned_state": "being pulled in opposite directions",
                "planned_job": "make disagreement visible",
                "planned_owner": "Aachu and Zuv",
            }
        ],
        "object_integrity": [
            {
                "id": "shared-map",
                "object": "folded paper map",
                "planned_orientation": {"held_edge": "horizontal"},
                "planned_use": {
                    "actor": "Aachu and Zuv",
                    "action": "pull",
                    "target": "shared-map",
                },
            }
        ],
        "action_critical_hands": [
            {
                "id": "aachu-right-map",
                "owner": "Aachu",
                "side": "right",
                "planned_action": "pull shared-map",
                "planned_contact_target": {"object": "shared-map", "region": "left edge"},
            }
        ],
        "scale": [
            {
                "id": "aachu-scale",
                "subject": "Aachu",
                "planned_scale": "adult proportion",
                "planned_support": "floor",
            }
        ],
        "accessory_visibility": [
            {
                "id": "aachu-bracelet",
                "subject": "Aachu",
                "item": "evil-eye bracelet",
                "side": "right",
                "planned_visibility": "visible",
                "planned_location": "right wrist",
            }
        ],
    }


def _observations() -> dict:
    """Authored observations matching _scene_contract; no fixture claims pixels prove them."""

    return {
        "continuity": [
            {
                "id": "shared-map",
                "observed_state": "being pulled in opposite directions",
                "observed_job": "make disagreement visible",
                "observed_owner": "Aachu and Zuv",
                "evidence": "The same folded map is between both people as they pull it apart.",
            }
        ],
        "object_integrity": [
            {
                "id": "shared-map",
                "observed_orientation": {"held_edge": "horizontal"},
                "observed_use": {
                    "actor": "Aachu and Zuv",
                    "action": "pull",
                    "target": "shared-map",
                },
                "evidence": "The map has one horizontal held edge and both people use it to pull.",
            }
        ],
        "action_critical_hands": [
            {
                "id": "aachu-right-map",
                "observed_action": "pull shared-map",
                "observed_contact_target": {"object": "shared-map", "region": "left edge"},
                "evidence": "Aachu's right hand grips the map's left edge while pulling outward.",
            }
        ],
        "scale": [
            {
                "id": "aachu-scale",
                "observed_scale": "adult proportion",
                "observed_support": "floor",
                "evidence": "Aachu has adult proportions and both feet are supported by the floor.",
            }
        ],
        "accessory_visibility": [
            {
                "id": "aachu-bracelet",
                "observed_visibility": "visible",
                "observed_location": "right wrist",
                "evidence": "The evil-eye bracelet is visible on Aachu's right wrist.",
            }
        ],
        "incidental_lettering": [],
    }


def _proof_qa(package: Path, binding: dict) -> dict:
    scene_contract = _scene_contract()
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
                "scene_contract": scene_contract,
                "scene_contract_sha256": scene_contract_fingerprint(scene_contract),
                "asset_bindings": {"instagram_post": copy.deepcopy(binding)},
                "reviews": {
                    "instagram_post": {
                        "checks": _checks(package),
                        "observations": _observations(),
                    }
                },
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
    scene_contract = _scene_contract()
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
                "scene_contract": scene_contract,
                "scene_contract_sha256": scene_contract_fingerprint(scene_contract),
                "reviews": {
                    "instagram_post": {
                        "checks": _checks(package),
                        "observations": _observations(),
                    }
                },
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

    issues = validate_proof_qa(
        package,
        qa,
        expected_scene_contracts={1: _scene_contract()},
    )

    assert issues == [
        "slide 1 instagram_post: identity references.zuv does not match its selected role"
    ]


def test_v3_requires_observed_contact_target_not_just_coherent_hand_count(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    qa = _proof_qa(package, _binding(package))
    hand = qa["slides"][0]["reviews"]["instagram_post"]["observations"][
        "action_critical_hands"
    ][0]
    hand["observed_contact_target"]["region"] = "upper sleeve"

    issues = validate_proof_qa(
        package,
        qa,
        expected_scene_contracts={1: _scene_contract()},
    )

    assert issues == [
        "slide 1 instagram_post: observations.action_critical_hands[aachu-right-map] "
        "observed_contact_target does not match planned_contact_target"
    ]


def test_v3_rejects_contradictory_carrier_state_and_object_use(tmp_path: Path) -> None:
    package = _package(tmp_path)
    qa = _proof_qa(package, _binding(package))
    observations = qa["slides"][0]["reviews"]["instagram_post"]["observations"]
    observations["continuity"][0]["observed_state"] = "already folded away"
    observations["object_integrity"][0]["observed_use"]["action"] = "read"

    issues = validate_proof_qa(
        package,
        qa,
        expected_scene_contracts={1: _scene_contract()},
    )

    assert "slide 1 instagram_post: observations.continuity[shared-map] observed_state does not match planned_state" in issues
    assert "slide 1 instagram_post: observations.object_integrity[shared-map] observed_use does not match planned_use" in issues


def test_v3_requires_conditional_scale_accessory_and_lettering_inventory(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    qa = _proof_qa(package, _binding(package))
    observations = qa["slides"][0]["reviews"]["instagram_post"]["observations"]
    observations["scale"] = []
    observations["accessory_visibility"] = []
    del observations["incidental_lettering"]

    issues = validate_proof_qa(
        package,
        qa,
        expected_scene_contracts={1: _scene_contract()},
    )

    assert "slide 1 instagram_post: observations.scale is missing planned ids: aachu-scale" in issues
    assert "slide 1 instagram_post: observations.accessory_visibility is missing planned ids: aachu-bracelet" in issues
    assert "slide 1 instagram_post: observations are missing incidental_lettering" in issues
    assert "slide 1 instagram_post: observations.incidental_lettering must be a list" in issues


def test_v3_blocks_inventory_that_reports_unexpected_incidental_lettering(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    qa = _proof_qa(package, _binding(package))
    qa["slides"][0]["reviews"]["instagram_post"]["observations"][
        "incidental_lettering"
    ] = [
        {
            "location": "parcel side",
            "text": "RANDOM LABEL",
            "allowed": False,
            "evidence": "Random label lettering appears on the side of the parcel.",
        }
    ]

    assert validate_proof_qa(
        package,
        qa,
        expected_scene_contracts={1: _scene_contract()},
    ) == [
        "slide 1 instagram_post: observations.incidental_lettering[1] reports unexpected incidental lettering"
    ]


def test_legacy_v2_is_preserved_but_rejected_by_explicit_v3_scene_workflow(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    qa = bind_proof_qa(
        package,
        _proof_qa(package, binding),
        [{"slide": 1, "native_outputs": {"instagram_post": binding}}],
    )

    assert qa["schema_version"] == LEGACY_PIXEL_QA_SCHEMA_VERSIONS[0]
    assert validate_proof_qa(package, qa) == []
    assert validate_proof_qa(
        package,
        qa,
        expected_scene_contracts={1: _scene_contract()},
    ) == [
        f"schema_version must be {PIXEL_QA_SCHEMA_VERSION}"
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
        expected_scene_contracts={1: _scene_contract()},
    )

    assert bound["schema_version"] == PIXEL_QA_SCHEMA_VERSION
    assert bound["slides"][0]["asset_bindings"]["instagram_post"] == binding
    assert validate_proof_qa(
        package,
        bound,
        expected_scene_contracts={1: _scene_contract()},
    ) == []


def test_canonical_scene_contract_is_attached_and_hash_bound_at_review_time(
    tmp_path: Path,
) -> None:
    package = _package(tmp_path)
    binding = _binding(package)
    authored = _proof_qa(package, binding)
    record = authored["slides"][0]
    del record["scene_contract"]
    del record["scene_contract_sha256"]
    canonical_contract = _scene_contract()

    bound = bind_proof_qa(
        package,
        authored,
        [{"slide": 1, "native_outputs": {"instagram_post": binding}}],
        expected_scene_contracts={1: canonical_contract},
    )

    record = bound["slides"][0]
    assert record["scene_contract"] == canonical_contract
    assert record["scene_contract_sha256"] == scene_contract_fingerprint(canonical_contract)
    assert validate_proof_qa(
        package,
        bound,
        expected_scene_contracts={1: canonical_contract},
    ) == []

    forged = copy.deepcopy(bound)
    forged["slides"][0]["scene_contract"]["continuity"][0][
        "planned_state"
    ] = "already folded away"
    forged["slides"][0]["scene_contract_sha256"] = scene_contract_fingerprint(
        forged["slides"][0]["scene_contract"]
    )

    assert "slide 1: scene_contract does not match the canonical pre-generation contract" in validate_proof_qa(
        package,
        forged,
        expected_scene_contracts={1: canonical_contract},
    )


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
        "slide 1 instagram_post: physical_action is FAIL; downstream PASS is invalid for relationship_state, entity_spatial_integrity, identity_wardrobe_accessories, text_brandmark_style_dimensions"
    ]


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

    bound = bind_final_qa(
        authored,
        manifest,
        expected_scene_contracts={1: _scene_contract()},
    )

    assert bound["manifest_sha256"] == manifest_fingerprint(manifest)
    assert bound["asset_binding_hashes"] == {
        "1:instagram_post": asset_binding_fingerprint(1, "instagram_post", binding)
    }
    assert validate_final_qa(
        package,
        bound,
        manifest,
        expected_scene_contracts={1: _scene_contract()},
    ) == []


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


def test_final_qa_rejects_corrupted_observed_text(tmp_path: Path) -> None:
    package = _package(tmp_path)
    binding = _binding(package, path=".internal/final-candidate/final/slide-01.png")
    manifest = _manifest(package, binding)
    qa = _final_qa(package, manifest)
    qa["slides"][0]["reviews"]["instagram_post"]["checks"][
        "text_brandmark_style_dimensions"
    ]["observed_text"] = "Nearly the same."

    assert "slide 1 instagram_post: rendered text is not exact" in validate_final_qa(
        package, qa, manifest
    )
