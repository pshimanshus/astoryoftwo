from pipeline.stages.b1_prepost import ORCHESTRATOR_SKILLS, PREPOST_AGENT_CONFIGS, build_agentic_os_brief, load_skill


def test_prepost_flow_loads_story_selling_authorial_spine_for_every_agent():
    for _, skill_names in PREPOST_AGENT_CONFIGS:
        assert "romance-story-selling-engine" in skill_names
    assert "romance-story-selling-engine" in ORCHESTRATOR_SKILLS

    loaded = load_skill("romance-story-selling-engine")

    assert "Story-Selling" in loaded
    assert "Concept Process Cards" in loaded
    assert "Story-Selling Rubric" in loaded
    assert "Story Selling Canon Source Policy" in loaded


def test_prepost_agentic_brief_includes_layer_e_room_decision():
    brief = build_agentic_os_brief({"concept": "Aachu stacks the plates and says dono rakh do."})

    assert "## Layer E Story-Selling" in brief
    assert "layer-e-story-selling.json" in brief
    assert "selected_story_lens" in brief
    assert "rooms" in brief
