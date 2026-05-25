from pipeline.stages.b1_prepost import ORCHESTRATOR_SKILLS, PREPOST_AGENT_CONFIGS, load_skill


def test_prepost_flow_loads_story_selling_authorial_spine_for_every_agent():
    for _, skill_names in PREPOST_AGENT_CONFIGS:
        assert "romance-story-selling-engine" in skill_names
    assert "romance-story-selling-engine" in ORCHESTRATOR_SKILLS

    loaded = load_skill("romance-story-selling-engine")

    assert "Story-Selling" in loaded
    assert "Concept Process Cards" in loaded
    assert "Story-Selling Rubric" in loaded
    assert "Story Selling Canon Source Policy" in loaded
