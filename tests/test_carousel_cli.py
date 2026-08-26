from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from pipeline.stages.carousel_lanes import discover_identity_images
from pipeline.stages.codex_builtin_image_generation import build_compiled_prompt_handoff


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
    path.write_text(
        json.dumps(
            {
                "slides": [
                    {
                        "copy": "I was certain of you.",
                        "physical_action": "Aachu places one house key in Zuv's open palm.",
                        "relationship_state": "certain of each other",
                    },
                    {
                        "copy": "We are learning how.",
                        "physical_action": "They turn one paper map and trace the same route together.",
                        "relationship_state": "committed and learning",
                    },
                    {
                        "copy": "Some answers arrive slowly.",
                        "physical_action": "Zuv holds the map flat while Aachu circles one shared stop.",
                        "relationship_state": "patient with uncertainty",
                    },
                    {
                        "copy": "But we keep choosing the route together.",
                        "physical_action": "They fold the map together and place it beside one house key.",
                        "relationship_state": "committed to the same life",
                    },
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
    style = _write_reference(tmp_path / "style.png", b"style")
    brief = _write_brief(tmp_path / "brief.json")
    command = [
        "create",
        "--story",
        "Certain of you, still learning us.",
        "--creative-brief",
        str(brief),
        "--style-reference",
        str(style),
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
    assert len(prompt_pack["style_reference_images"]) == 1
    assert (package / prompt_pack["style_reference_images"][0]).read_bytes() == b"style"


def test_locked_visual_fields_survive_package_and_compiled_prompt(tmp_path: Path) -> None:
    brief = tmp_path / "brief.json"
    local_story_reference = _write_reference(tmp_path / "local-story.png", b"story")
    identities = [
        _write_reference(tmp_path / "identity/aachu/a.png", b"aachu"),
        _write_reference(tmp_path / "identity/zuv/z.png", b"zuv"),
        _write_reference(tmp_path / "identity/together/face.png", b"together-face"),
        _write_reference(tmp_path / "identity/together/body.png", b"together-body"),
    ]
    style = _write_reference(tmp_path / "style.png", b"style")
    slides = json.loads(_write_brief(brief).read_text(encoding="utf-8"))["slides"]
    slides[0].update(
        {
            "composition": "low eye-level doorway frame, key centered between both hands",
            "wardrobe": "Aachu black overshirt and blue jeans; Zuv white zip jacket",
            "pose": "Aachu extends her right hand; Zuv receives with his left palm",
            "props": "one unlettered brass house key and nothing else",
            "background": "uncluttered warm-ivory apartment doorway",
            "emotion": "quiet certainty without posing",
            "continuity_lock": "same doorway and wardrobe across the sequence",
            "negative_prompt": "no spare keys or printed labels",
            "source_images": [local_story_reference.name],
        }
    )
    brief.write_text(json.dumps({"slides": slides}), encoding="utf-8")
    command = [
        "create",
        "--story",
        "The same home, learned together.",
        "--creative-brief",
        str(brief),
        "--style-reference",
        str(style),
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
    packaged_prompt = json.loads(
        (package / "prompt-pack.json").read_text(encoding="utf-8")
    )["slides"][0]
    for key in (
        "composition",
        "wardrobe",
        "pose",
        "props",
        "background",
        "emotion",
        "continuity_lock",
        "negative_prompt",
    ):
        assert key in packaged_slide
        assert key not in packaged_prompt
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
    styles = prompt_pack["style_reference_images"]
    assert len(identities) == 4
    assert len(styles) == 1
    assert len(identities) + len(styles) == 5
    style_board = (
        WORKSPACE
        / "config/references/style-lock/observational-intimacy-premium/contact-sheet.png"
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
    ("prepare", "ingest", "approve", "finalize"),
)
def test_every_writing_cli_command_keeps_archived_v2_tree_unchanged(
    tmp_path: Path,
    command: str,
) -> None:
    package = tmp_path / f"archived-{command}"
    package.mkdir()
    (package / "generation-state.json").write_text(
        json.dumps(
            {
                "schema_version": "carousel-generation-state/v2",
                "status": "proof_ready_for_review",
            }
        ),
        encoding="utf-8",
    )
    external = _write_reference(tmp_path / "external.png", b"external")
    args = [command, str(package)]
    if command == "ingest":
        args.extend(("--instagram-post", str(external)))
    elif command == "approve":
        args.extend(("--proof-sha256", "sha256:" + "0" * 64))
    before = _tree_bytes(package)

    result = _run(*args)

    assert result.returncode == 2
    assert "read-only" in json.loads(result.stdout)["reason"]
    assert _tree_bytes(package) == before


def test_explicit_style_overflow_blocks_instead_of_silently_slicing(tmp_path: Path) -> None:
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
    assert "Pass exactly 1 explicit style board" in payload["reason"]


def test_make_carousel_forwards_public_inputs_without_hidden_work() -> None:
    makefile = (WORKSPACE / "Makefile").read_text(encoding="utf-8")
    recipe = makefile.split("\nvisual-check:", 1)[0].split("\ncarousel:", 1)[1]

    assert "scripts/carousel.py create" in recipe
    for variable in (
        "STORY_FILE",
        "CREATIVE_BRIEF",
        "STORY_IMAGES",
        "IDENTITY_IMAGES",
        "STYLE_REFERENCES",
        "FORMATS",
        "OUTPUT_ROOT",
        "PROOF_SLIDE",
    ):
        assert f"$({variable})" in recipe
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
