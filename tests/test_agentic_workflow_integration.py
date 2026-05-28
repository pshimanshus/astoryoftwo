import json
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages import codex_native_carousel
from pipeline.stages.c1_illustration_carousel import build_manifest as build_anthropic_manifest
from pipeline.stages.c1_illustration_carousel import load_context as load_anthropic_context
from pipeline.stages.b1_prepost import build_agentic_os_brief, load_context as load_prepost_context
from scripts.create_substack_article_package import create_article_package


def write_minimal_agentic_workspace(root: Path) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "memory" / "semantic").mkdir(parents=True, exist_ok=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "voice.md").write_text("Warm A Story of Two voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Current visual-first carousel work.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\n\nfact: Use visual-first proof for couple stories.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "default_profile": "a-story-of-two",
                "profiles": {
                    "a-story-of-two": {
                        "budget_tokens": 500,
                        "sections": [
                            {
                                "id": "voice",
                                "path": "config/voice.md",
                                "kind": "brand_voice",
                                "required": True,
                            },
                            {
                                "id": "working",
                                "path": "memory/working.md",
                                "kind": "working_memory",
                                "required": True,
                            },
                        ],
                    },
                    "article": {
                        "budget_tokens": 500,
                        "sections": [
                            {
                                "id": "voice",
                                "path": "config/voice.md",
                                "kind": "brand_voice",
                                "required": True,
                            },
                            {
                                "id": "working",
                                "path": "memory/working.md",
                                "kind": "working_memory",
                                "required": True,
                            },
                        ],
                    },
                },
            }
        ),
        encoding="utf-8",
    )
    (root / "config" / "skill-systems.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0",
                "systems": {
                    "carousel_jam": {
                        "components": ["config/skills/carousel-jam-autopilot.md"],
                        "agents": [],
                        "gates": ["visual_debate_go"],
                    },
                    "story_article": {
                        "components": ["config/skills/couple-substack-article-framework.md"],
                        "agents": [],
                        "gates": ["final_approval"],
                    },
                    "prepost_reel": {
                        "components": ["config/skills/hook-and-edit-framework.md"],
                        "agents": [],
                        "gates": ["verdict"],
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def test_anthropic_context_and_manifest_use_agentic_os():
    rendered_context = load_anthropic_context()
    manifest = build_anthropic_manifest(
        title="Agentic Provenance",
        slug="agentic-provenance",
        story="A small proof story.",
        image_paths=[],
        today=date(2026, 5, 28),
    )

    assert "# Agentic Context Pack" in rendered_context
    assert "config/agentic_context_manifest.json" in manifest["agentic_os"]["context_manifest"]
    assert manifest["agentic_os"]["skill_system"] == "carousel_jam"


def test_codex_native_manifest_records_agentic_os_contract():
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

    assert manifest["agentic_os"]["skill_system"] == "carousel_jam"
    assert manifest["agentic_os"]["context_manifest"] == "config/agentic_context_manifest.json"
    assert manifest["agentic_os"]["skill_systems"] == "config/skill-systems.json"


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
    )

    assert skill_system.returncode == 0, skill_system.stderr
    assert '"name": "carousel_jam"' in skill_system.stdout
    assert index_memory.returncode == 0, index_memory.stderr
    assert "memory.sqlite3" in index_memory.stdout
