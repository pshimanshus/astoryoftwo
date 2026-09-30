import json
from pathlib import Path

import pytest

from pipeline.agentic import memory_index
from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.agentic.recall import build_recall_bundle, render_recall_bundle


def test_memory_index_finds_semantic_memory_by_meaningful_terms(tmp_path: Path):
    root = tmp_path
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- test\n\nfact: Use visual-first kitchen comedy and tiny thought bubbles.\n",
        encoding="utf-8",
    )

    index_path = build_memory_index(root)
    hits = search_memory(index_path, "kitchen thought bubble", limit=3)

    assert hits
    assert hits[0].path == "memory/semantic/prefs.md"
    assert "kitchen" in hits[0].snippet.lower()


def test_memory_index_includes_learning_events_and_historical_creator_corrections(tmp_path: Path):
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    correction_dir = tmp_path / "output" / "carousels" / "2026-07-30" / "door-check"
    event_dir.mkdir(parents=True)
    correction_dir.mkdir(parents=True)
    (event_dir / "feedback-door-check-v1.json").write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "feedback-door-check-v1",
                "source": "creator_feedback",
                "summary": "The scene must show a forceful palm press, not a casual touch.",
                "user_instruction_exact": "The palm needs visible pressure ticks.",
            }
        ),
        encoding="utf-8",
    )
    (correction_dir / "creator-correction.json").write_text(
        json.dumps(
            {
                "status": "CORRECTED_BY_CREATOR",
                "corrections": ["The umbrella clips to the tote hands-free."],
                "rejected_route_phrases": ["spare hand holding umbrella"],
            }
        ),
        encoding="utf-8",
    )

    index_path = build_memory_index(tmp_path)
    event_hits = search_memory(index_path, "pressure ticks", limit=3)
    correction_hits = search_memory(index_path, "umbrella tote hands-free", limit=3)

    assert any(hit.kind == "learning_event" for hit in event_hits)
    assert any(hit.path.endswith("creator-correction.json") for hit in correction_hits)
    assert any(hit.kind == "creator_correction" for hit in correction_hits)


def test_memory_index_failed_rebuild_preserves_last_good_index(tmp_path: Path, monkeypatch):
    semantic_dir = tmp_path / "memory" / "semantic"
    semantic_dir.mkdir(parents=True)
    (semantic_dir / "prefs.md").write_text(
        "# Preferences\n\nKeep the kitchen recognition beat.\n",
        encoding="utf-8",
    )
    index_path = build_memory_index(tmp_path)
    before = index_path.read_bytes()

    def fail_collection(_root: Path):
        raise RuntimeError("simulated index build failure")

    monkeypatch.setattr(memory_index, "collect_indexable_files", fail_collection)
    with pytest.raises(RuntimeError, match="simulated index build failure"):
        build_memory_index(tmp_path)

    assert index_path.read_bytes() == before
    assert search_memory(index_path, "kitchen recognition")
    assert not list(index_path.parent.glob(f".{index_path.name}.*.tmp"))


def test_memory_index_filters_superseded_feedback_before_result_limit(tmp_path: Path):
    package = tmp_path / "output" / "carousels" / "2026-09-05" / "current-package"
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    package.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    events = []
    for number in range(10):
        old_id = f"fb-old-{number}"
        events.extend(
            [
                {
                    "feedback_id": old_id,
                    "captured_at": "2026-09-01T00:00:00+00:00",
                    "user_instruction_exact": "obsolete vermilion gesture",
                    "scope": "slide",
                    "status": "evaluated",
                },
                {
                    "feedback_id": f"fb-replacement-{number}",
                    "captured_at": "2026-09-02T00:00:00+00:00",
                    "user_instruction_exact": "use the replacement gesture",
                    "scope": "slide",
                    "status": "captured",
                    "supersedes_feedback_id": old_id,
                },
            ]
        )
    events.append(
        {
            "feedback_id": "fb-current",
            "captured_at": "2026-09-05T00:00:00+00:00",
            "user_instruction_exact": "vermilion gesture is current for this beat",
            "scope": "slide",
            "status": "captured",
        }
    )
    (package / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v3",
                "package_id": "output/carousels/2026-09-05/current-package",
                "events": events,
            }
        ),
        encoding="utf-8",
    )
    (event_dir / "event-feedback-fb-old-0.json").write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-feedback-fb-old-0",
                "source": "creator_feedback",
                "user_instruction_exact": "obsolete vermilion gesture",
                "package_path": "output/carousels/2026-09-05/current-package",
                "scope": "slide",
                "feedback_metadata": {"feedback_id": "fb-old-0"},
                "created_at": "2026-09-01T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    hits = search_memory(build_memory_index(tmp_path), "vermilion gesture", limit=1)

    assert len(hits) == 1
    assert hits[0].path.endswith("creator-correction.json#fb-current")
    assert "obsolete" not in hits[0].snippet


def test_memory_index_package_filter_excludes_other_package_feedback(tmp_path: Path):
    for slug, action in (("flight-story", "window shade"), ("train-story", "platform clock")):
        package = tmp_path / "output" / "carousels" / "2026-09-05" / slug
        package.mkdir(parents=True)
        (package / "creator-correction.json").write_text(
            json.dumps(
                {
                    "schema_version": "creator-correction/v3",
                    "package_id": f"output/carousels/2026-09-05/{slug}",
                    "events": [
                        {
                            "feedback_id": f"fb-{slug}",
                            "captured_at": "2026-09-05T00:00:00+00:00",
                            "user_instruction_exact": f"Make the shared travel action show the {action}.",
                            "scope": "package",
                            "status": "captured",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
    semantic_dir = tmp_path / "memory" / "semantic"
    semantic_dir.mkdir(parents=True)
    (semantic_dir / "travel.md").write_text(
        "# Travel\n\nShared travel actions should remain legible.\n",
        encoding="utf-8",
    )
    index_path = build_memory_index(tmp_path)

    hits = search_memory(
        index_path,
        "package:output/carousels/2026-09-05/flight-story shared travel action",
        limit=8,
    )
    package_only_hits = search_memory(
        index_path,
        "package:output/carousels/2026-09-05/flight-story",
        limit=8,
    )

    assert hits[0].path.endswith("flight-story/creator-correction.json#fb-flight-story")
    assert all("flight-story" in hit.path for hit in hits)
    assert package_only_hits
    assert all("flight-story" in hit.path for hit in package_only_hits)


def test_memory_index_deduplicates_linked_event_and_prefers_canonical_correction(tmp_path: Path):
    package = tmp_path / "output" / "carousels" / "2026-09-05" / "umbrella-story"
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    package.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    correction = {
        "feedback_id": "fb-umbrella",
        "captured_at": "2026-09-05T00:00:00+00:00",
        "user_instruction_exact": "Angle the umbrella to cover both people.",
        "scope": "slide",
        "status": "captured",
    }
    (package / "creator-correction.json").write_text(
        json.dumps(
            {
                "schema_version": "creator-correction/v3",
                "package_id": "output/carousels/2026-09-05/umbrella-story",
                "events": [correction],
            }
        ),
        encoding="utf-8",
    )
    (event_dir / "event-feedback-fb-umbrella.json").write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-feedback-fb-umbrella",
                "source": "creator_feedback",
                "user_instruction_exact": correction["user_instruction_exact"],
                "scope": "slide",
                "package_path": "output/carousels/2026-09-05/umbrella-story",
                "feedback_metadata": {"feedback_id": "fb-umbrella"},
                "created_at": correction["captured_at"],
            }
        ),
        encoding="utf-8",
    )

    hits = search_memory(build_memory_index(tmp_path), "umbrella cover", limit=8)
    feedback_hits = [hit for hit in hits if "fb-umbrella" in hit.path]

    assert len(feedback_hits) == 1
    assert feedback_hits[0].kind == "creator_correction"


def test_memory_index_scope_and_recency_rank_learning_event_only_guidance(tmp_path: Path):
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    event_dir.mkdir(parents=True)
    for name, scope, created_at in (
        ("old-workflow", "workflow", "2025-09-05T00:00:00+00:00"),
        ("recent-slide", "slide", "2026-09-05T00:00:00+00:00"),
    ):
        (event_dir / f"{name}.json").write_text(
            json.dumps(
                {
                    "schema_version": "learning-event/v1",
                    "event_id": name,
                    "source": "creator_feedback",
                    "summary": "Keep the commitment action observable.",
                    "scope": scope,
                    "created_at": created_at,
                }
            ),
            encoding="utf-8",
        )

    hits = search_memory(
        build_memory_index(tmp_path),
        "scope:slide commitment observable",
        limit=2,
    )

    assert len(hits) == 2
    assert hits[0].path == "memory/agentic/learning-events/recent-slide.json"


@pytest.mark.parametrize(
    ("source", "eval_disposition"),
    (
        ("langfuse_annotation_candidate", "candidate_only"),
        ("langfuse_annotation_candidate", "reviewed_locally"),
        ("code_review", "candidate_only"),
    ),
)
def test_memory_index_excludes_unpromoted_annotation_candidates_from_active_recall(
    tmp_path: Path,
    source: str,
    eval_disposition: str,
) -> None:
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    event_dir.mkdir(parents=True)
    (event_dir / "annotation.json").write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-langfuse-annotation",
                "source": source,
                "summary": "Unreviewed heliotrope annotation candidate.",
                "eval_disposition": eval_disposition,
                "created_at": "2026-09-05T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    hits = search_memory(build_memory_index(tmp_path), "heliotrope annotation", limit=8)

    assert hits == []


def test_memory_index_includes_separately_captured_local_learning_after_review(
    tmp_path: Path,
) -> None:
    event_dir = tmp_path / "memory" / "agentic" / "learning-events"
    event_dir.mkdir(parents=True)
    (event_dir / "local-learning.json").write_text(
        json.dumps(
            {
                "schema_version": "learning-event/v1",
                "event_id": "event-local-learning",
                "source": "creator_feedback",
                "summary": "Locally reviewed heliotrope identity correction.",
                "eval_disposition": "passed",
                "created_at": "2026-09-05T00:00:00+00:00",
            }
        ),
        encoding="utf-8",
    )

    hits = search_memory(build_memory_index(tmp_path), "heliotrope identity", limit=8)

    assert len(hits) == 1
    assert hits[0].path.endswith("local-learning.json")


def test_memory_index_retires_only_explicit_carried_events_from_mixed_package(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from pipeline.stages import carousel_visual_storytelling

    package_path = "output/carousels/2026-09-12/duplicate-successor"
    correction_dir = tmp_path / package_path
    event_dir = tmp_path / "memory/agentic/learning-events"
    correction_dir.mkdir(parents=True)
    event_dir.mkdir(parents=True)
    (correction_dir / "creator-correction.json").write_text(
        json.dumps(
            {
                "package_id": package_path,
                "successor_retirement": {"schema_version": "v2"},
                "events": [
                    {
                        "feedback_id": "fb-carried-duplicate",
                        "status": "diagnosed",
                        "user_instruction_exact": "retired heliotrope duplicate",
                    },
                    {
                        "feedback_id": "fb-unrelated-local",
                        "status": "evaluated",
                        "historical_only": True,
                        "user_instruction_exact": "preserved cerulean local history",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    learning_events = [
        (
            "event-retired-exact",
            "fb-carried-duplicate",
            "retired ochre learning duplicate",
        ),
        (
            "event-other-but-linked-retired",
            "fb-carried-duplicate",
            "retired magenta linked duplicate",
        ),
        (
            "event-preserved-history",
            "fb-unrelated-local",
            "preserved indigo historical learning",
        ),
    ]
    for event_id, feedback_id, summary in learning_events:
        (event_dir / f"{event_id}.json").write_text(
            json.dumps(
                {
                    "event_id": event_id,
                    "source": "creator_feedback",
                    "package_path": package_path,
                    "summary": summary,
                    "feedback_metadata": {"feedback_id": feedback_id},
                }
            ),
            encoding="utf-8",
        )

    monkeypatch.setattr(
        carousel_visual_storytelling,
        "successor_feedback_retirement_status",
        lambda *_args, **_kwargs: {
            "retired": True,
            "package_path": package_path,
            "retired_feedback_ids": ["fb-carried-duplicate"],
            "retired_learning_event_ids": ["event-retired-exact"],
        },
    )

    index = build_memory_index(tmp_path)

    assert not search_memory(index, "heliotrope", limit=10)
    assert not search_memory(index, "ochre", limit=10)
    assert not search_memory(index, "magenta", limit=10)
    assert search_memory(index, "cerulean", limit=10)
    assert search_memory(index, "indigo", limit=10)


def test_recall_bundle_combines_context_and_ranked_hits(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "voice.md").write_text("Warm couple voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Current kitchen carousel draft.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- test\n\nfact: Build visual-first carousels.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        """{
          "schema_version": "1.0",
          "default_profile": "a-story-of-two",
          "profiles": {
            "a-story-of-two": {
              "budget_tokens": 400,
              "sections": [
                {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": true},
                {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": true}
              ]
            }
          }
        }""",
        encoding="utf-8",
    )

    bundle = build_recall_bundle(root, query="visual carousel", profile="a-story-of-two")

    assert bundle.query == "visual carousel"
    assert bundle.context.profile == "a-story-of-two"
    assert bundle.hits


def test_render_recall_bundle_includes_context_and_ranked_citations(tmp_path: Path):
    root = tmp_path
    (root / "config").mkdir()
    (root / "memory" / "semantic").mkdir(parents=True)
    (root / "memory").mkdir(exist_ok=True)
    (root / "config" / "voice.md").write_text("Warm couple voice.", encoding="utf-8")
    (root / "memory" / "working.md").write_text("Current kitchen carousel draft.", encoding="utf-8")
    (root / "memory" / "semantic" / "prefs.md").write_text(
        "# Preferences\n\nconfidence: 0.9\nsources:\n- test\n\nfact: Build visual-first carousels.\n",
        encoding="utf-8",
    )
    (root / "config" / "agentic_context_manifest.json").write_text(
        """{
          "schema_version": "1.0",
          "default_profile": "a-story-of-two",
          "profiles": {
            "a-story-of-two": {
              "budget_tokens": 400,
              "sections": [
                {"id": "voice", "path": "config/voice.md", "kind": "brand_voice", "required": true},
                {"id": "working", "path": "memory/working.md", "kind": "working_memory", "required": true}
              ]
            }
          }
        }""",
        encoding="utf-8",
    )

    rendered = render_recall_bundle(
        build_recall_bundle(root, query="visual carousel", profile="a-story-of-two")
    )

    assert "# Recall Bundle" in rendered
    assert "# Agentic Context Pack" in rendered
    assert "memory/semantic/prefs.md" in rendered
    assert "Build visual-first carousels" in rendered
