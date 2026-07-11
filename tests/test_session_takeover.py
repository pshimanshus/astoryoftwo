import json
from pathlib import Path

from scripts.start_agentic_session import build_session_takeover
from tests.helpers.agentic_workspace import write_minimal_agentic_workspace


def test_session_takeover_loads_context_recall_git_health_and_writes_intent(tmp_path: Path):
    write_minimal_agentic_workspace(tmp_path)

    result = build_session_takeover(
        tmp_path,
        skill_system_name="carousel_jam",
        intent="Layer E continuation",
        profile="a-story-of-two",
    )

    assert result["intent"] == "Layer E continuation"
    assert result["skill_system"]["name"] == "carousel_jam"
    assert result["context"]["status"] == "loaded"
    assert result["recall"]["status"] in {"loaded", "unavailable"}
    assert "status" in result["dirty_git_state"]
    assert result["wiki_health"]["status"] == "NEEDS_HEAL"
    assert result["creative_work_blocked"] is True

    intent_path = tmp_path / result["session_intent_path"]
    assert intent_path.exists()
    intent_payload = json.loads(intent_path.read_text(encoding="utf-8"))
    assert intent_payload["intent"] == "Layer E continuation"
    assert intent_payload["creative_work_blocked"] is True


def test_session_takeover_surfaces_research_partner_lens(tmp_path: Path):
    write_minimal_agentic_workspace(tmp_path)
    research_memory = tmp_path / "memory" / "semantic" / "engineering-workflow-preferences.md"
    research_memory.write_text(
        "\n".join(
            [
                "# Engineering Workflow Preferences",
                "",
                "## Research Partner Operating Model",
                "",
                "The partner behavior is:",
                "- form explicit hypotheses about what will work before building;",
                "- challenge weak, stale, or self-defeating directions with repo evidence;",
                "- turn repeated session learnings into proposal-first durable updates.",
            ]
        ),
        encoding="utf-8",
    )

    result = build_session_takeover(
        tmp_path,
        skill_system_name="carousel_jam",
        intent="build a stronger idea system",
        profile="a-story-of-two",
    )

    lens = result["research_partner"]
    assert lens["status"] == "loaded"
    assert lens["path"] == "memory/semantic/engineering-workflow-preferences.md"
    assert "What hypothesis are we testing next?" in lens["session_questions"]
    assert "challenge weak" in " ".join(lens["operating_rules"]).lower()
    assert "proposal-first durable updates" in " ".join(lens["operating_rules"])

    intent_path = tmp_path / result["session_intent_path"]
    intent_payload = json.loads(intent_path.read_text(encoding="utf-8"))
    assert intent_payload["research_partner"] == lens
