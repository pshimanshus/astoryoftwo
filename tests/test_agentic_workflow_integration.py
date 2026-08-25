import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages import codex_native_carousel
from pipeline.stages.b1_prepost import build_agentic_os_brief, load_context as load_prepost_context
from scripts.create_substack_article_package import create_article_package
from tests.helpers.agentic_workspace import write_minimal_agentic_workspace
from tests.helpers.images import write_jpeg


def test_carousel_registry_uses_small_agentless_contract():
    systems = json.loads(
        (Path(__file__).resolve().parents[1] / "config" / "skill-systems.json").read_text()
    )
    carousel = systems["systems"]["carousel_jam"]

    assert carousel["agents"] == []
    assert carousel["gates"] == [
        "concept_lock",
        "copy_format_lock",
        "proof_pixel_qa_creator_approval",
        "final_package_qa",
    ]


def test_codex_native_manifest_is_small_creative_context():
    manifest = codex_native_carousel.build_manifest(
        title="Agentic Native",
        slug="agentic-native",
        story="A small proof story.",
        image_paths=[],
        identity_image_paths=[],
        identity_reference_selection={},
        identity_dossier={},
        slide_count=5,
        today=date(2026, 5, 28),
    )

    assert manifest["schema_version"] == "carousel-creative-context/v2"
    assert manifest["status"] == "copy_and_format_locked"
    assert manifest["artifacts"] == [
        "creative-context.json",
        "format-contract.json",
        "slides.json",
        "prompt-pack.json",
    ]
    assert "agentic_os" not in manifest


def test_codex_native_workflow_rejects_empty_explicit_identity_refs(tmp_path: Path):
    story_image = tmp_path / "story.jpg"
    write_jpeg(story_image)

    try:
        codex_native_carousel.create_codex_native_carousel(
            story="A small proof story with Aachu and Zuv.",
            image_paths=[story_image],
            identity_image_paths=[],
            title="Empty Identity",
            output_root=tmp_path / "output" / "carousels",
            today=date(2026, 5, 28),
        )
    except ValueError as exc:
        assert "identity reference" in str(exc).lower()
    else:
        raise AssertionError("empty explicit identity refs should not create a publishable workflow package")


def test_prepost_context_and_brief_use_agentic_os():
    rendered_context = load_prepost_context()
    agentic_brief = build_agentic_os_brief({"concept": "A visual-first kitchen proof"})

    assert "# Agentic Context Pack" in rendered_context
    assert "prepost_reel" in agentic_brief
    assert "# Recall Bundle" in agentic_brief


def test_article_package_writes_agentic_recall_brief():
    with tempfile.TemporaryDirectory() as tmpdir:
        workspace = Path(tmpdir)
        write_minimal_agentic_workspace(workspace)
        carousel = workspace / "output" / "carousels" / "2026-05-28" / "proof-story"
        carousel.mkdir(parents=True)
        (carousel / "concept.json").write_text(
            json.dumps({"title": "Proof Story", "human_truth": "Love becomes visible in proof."}),
            encoding="utf-8",
        )
        (carousel / "storyboard.md").write_text("# Storyboard", encoding="utf-8")
        (carousel / "slides.json").write_text("[]", encoding="utf-8")
        (carousel / "copy.json").write_text("{}", encoding="utf-8")

        out_dir = create_article_package(
            carousel_dir=carousel,
            title="Proof Story",
            output_root=workspace / "output" / "articles",
            today=date(2026, 5, 28),
        )

        manifest = json.loads((out_dir / "source-manifest.json").read_text(encoding="utf-8"))
        memory_brief = (out_dir / "source-memory-brief.md").read_text(encoding="utf-8")

    assert manifest["agentic_os"]["skill_system"]["name"] == "story_article"
    assert manifest["agentic_os"]["recall_brief"] == "source-memory-brief.md"
    assert "# Recall Bundle" in memory_brief
    assert "memory/semantic/prefs.md" in memory_brief


def test_agentic_os_cli_plan_aliases(tmp_path: Path):
    write_minimal_agentic_workspace(tmp_path)
    repo_root = Path(__file__).resolve().parents[1]

    skill_system = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(tmp_path),
            "skill-system",
            "carousel_jam",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )
    index_memory = subprocess.run(
        [
            sys.executable,
            "scripts/agentic_os.py",
            "--workspace-root",
            str(tmp_path),
            "index-memory",
        ],
        cwd=repo_root,
        text=True,
        capture_output=True,
        check=False,
        timeout=30,
    )

    assert skill_system.returncode == 0, skill_system.stderr
    assert '"name": "carousel_jam"' in skill_system.stdout
    assert index_memory.returncode == 0, index_memory.stderr
    assert "memory.sqlite3" in index_memory.stdout


def test_layer_e_artifacts_are_not_in_default_carousel_jam():
    systems = json.loads((Path(__file__).resolve().parents[1] / "config" / "skill-systems.json").read_text())

    assert not any(
        "layer-e" in artifact
        for artifact in systems["systems"]["carousel_jam"].get("artifacts", [])
    )
    for name in ("story_article", "prepost_reel"):
        system = systems["systems"][name]
        artifacts = system.get("artifacts", [])
        assert "layer-e-story-selling.json" in artifacts
        assert "layer-e-story-selling.md" in artifacts
