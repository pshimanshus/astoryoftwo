import json
from pathlib import Path

from scripts.start_agentic_session import build_session_takeover
from tests.test_agentic_workflow_integration import write_minimal_agentic_workspace


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
