import json
from pathlib import Path

from pipeline.agentic.context_loader import assemble_context_pack


WORKSPACE = Path(__file__).resolve().parents[1]


def _read(path: str) -> str:
    return (WORKSPACE / path).read_text(encoding="utf-8")


def _flat(path: str) -> str:
    return " ".join(_read(path).split())


def test_agents_md_is_human_first_router_not_creative_os_dump():
    agents = _read("AGENTS.md")

    assert "This is the project contract for agents working in this repo." in agents
    assert "What Matters Most" in agents
    assert "Small Brief First" in agents
    assert "Human Draft First" in agents
    assert "Context As Seasoning" in agents
    assert "Do not answer a small creative brief with a framework report" in agents
    assert "Use agents surgically" in agents

    assert "## Hard Creative Rules" not in agents
    assert "golden-theme variant tournament" not in agents
    assert "Visual Debate Gate" not in agents
    assert "Stage-Scene Gate" not in agents
    assert "28/30" not in agents


def test_agents_md_protects_shareable_instagram_love_ideas():
    agents = _flat("AGENTS.md")

    for fragment in (
        "Fresh ideas must feel shareable on Instagram",
        "couple moment",
        "love learning",
        "this is me",
        "this is her",
        "this is us",
        "send it to their partner",
    ):
        assert fragment in agents


def test_carousel_hot_path_allows_creator_seed_or_agent_jam():
    agents = _read("AGENTS.md")
    skill = _read(".agents/skills/a-story-carousel-jam/SKILL.md")

    assert "There are two valid starts" in agents
    assert "The creator may bring a seed" in agents
    assert "jam and propose fresh concept ideas" in agents
    assert "concept already formed" in agents
    assert "creator asks to jam from scratch" in skill
    assert "fresh concept seeds" in skill


def test_agents_md_requires_format_choice_and_transformability():
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    assert "post, Reel, carousel, or multi-format package" in agents
    assert "Idea -> Format -> Proof -> Package" in agents
    assert "Format First" in agents
    assert "post, Reel, carousel" in skill


def test_agents_md_protects_identity_wardrobe_dimensions_and_brandmark():
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Aachu and Zuv must both stay recognizable",
        "whole illustrated person, not just a face patch",
        "face, hair, body proportions, height, expression, posture, and clothing",
        "clothing and couple styling come from those images first",
        "1080x1440",
        "1080x1920",
        "square `1080x1080` only when",
        "tiny `@a.storyof.two`",
    ):
        assert fragment in agents

    assert "whole illustrated person, not just a face patch" in skill
    assert "Wardrobe and couple styling" in skill
    assert "tiny `@a.storyof.two`" in skill


def test_identity_eval_stop_gate_blocks_batching_without_structured_review():
    surfaces = {
        "identity rule": _flat("config/rules/identity.md"),
        "carousel skill": _flat(".agents/skills/a-story-carousel-jam/SKILL.md"),
        "runtime context": _flat("config/skills/carousel-jam-runtime-context.md"),
        "autopilot": _flat("config/skills/carousel-jam-autopilot.md"),
        "illustration framework": _flat("config/skills/illustration-carousel-framework.md"),
        "engineering memory": _flat("memory/semantic/engineering-workflow-preferences.md"),
    }

    for name, text in surfaces.items():
        lowered = text.lower()

        assert "no identity eval" in lowered, name
        assert "no next slide" in lowered, name
        assert "identity-consistency-review.json" in text, name
        assert "visual-qa.json" in text, name
        assert "reference IDs" in text or "reference ids" in lowered, name
        assert "specific likeness notes" in lowered, name
        assert "BLOCKED_FOR_IDENTITY_EVAL" in text, name
        assert "IDENTITY_UNVERIFIED" in text, name
        assert "do not call" in lowered or "instead of calling it final" in lowered, name


def test_signature_evil_eye_accessories_are_durable_identity_locks():
    identity = _flat("config/rules/identity.md")
    master_prompt = _flat("config/references/a-story-illustration-master-prompt.md")
    director_memory = _flat("memory/semantic/visual-director-intelligence.md")
    style_contract = json.loads(_read("config/carousel_style_contract.json"))

    for name, text in {
        "identity rule": identity,
        "master prompt": master_prompt,
        "visual director memory": director_memory,
    }.items():
        lowered = text.lower()
        assert "evil-eye locket" in lowered, name
        assert "silver chain" in lowered, name
        assert "evil-eye bracelet" in lowered, name
        assert "right wrist" in lowered, name
        assert "always worn" in lowered, name

    assert "evil-eye bracelet" in style_contract["characters"]["aachu"]["signature_accessory"].lower()
    assert "right wrist" in style_contract["characters"]["aachu"]["signature_accessory"].lower()
    assert "evil-eye locket" in style_contract["characters"]["zuv"]["signature_accessory"].lower()
    assert "silver chain" in style_contract["characters"]["zuv"]["signature_accessory"].lower()


def test_scene_entity_integrity_is_a_loaded_hard_gate():
    manifest = json.loads((WORKSPACE / "config/agentic_context_manifest.json").read_text(encoding="utf-8"))
    sections = manifest["profiles"][manifest["default_profile"]]["sections"]
    paths = {section["path"] for section in sections}

    assert "config/rules/scene-entity-integrity.md" in paths
    rule = _flat("config/rules/scene-entity-integrity.md").lower()
    assert "expected_people" in rule
    assert "observed_people" in rule
    assert "unexpected_entities" in rule
    assert "unintended second aachu/zuv pair" in rule


def test_directed_visual_story_runs_two_independent_lifecycle_events():
    surfaces = {
        "carousel skill": _flat(".agents/skills/a-story-carousel-jam/SKILL.md"),
        "runtime context": _flat("config/skills/carousel-jam-runtime-context.md"),
        "autopilot": _flat("config/skills/carousel-jam-autopilot.md"),
        "illustration framework": _flat("config/skills/illustration-carousel-framework.md"),
    }

    for name, text in surfaces.items():
        assert "$a-story-direct-visual-story" in text, name
        assert "director_storyboard" in text, name
        assert "visual_story_readability" in text, name
        assert "visual-plan-quality.json" in text, name
        assert "visual-qa.json" in text, name

    makefile = _read("Makefile")
    assert "visual-check:" in makefile
    assert "check_visual_story.py" in makefile


def test_directed_visual_story_requires_provenance_and_exact_asset_binding():
    surfaces = {
        "carousel skill": _flat(".agents/skills/a-story-carousel-jam/SKILL.md"),
        "runtime context": _flat("config/skills/carousel-jam-runtime-context.md"),
        "autopilot": _flat("config/skills/carousel-jam-autopilot.md"),
        "illustration framework": _flat("config/skills/illustration-carousel-framework.md"),
    }

    for name, text in surfaces.items():
        lowered = text.lower()
        assert "Event A cannot pass" in text, name
        assert "review_provenance" in text, name
        assert "director_event_fingerprint" in text, name
        assert "source_director_event_fingerprint" in text, name
        assert "expected_frame_bindings" in text, name
        assert "square" in lowered, name
        for untrusted_source in ("prompt", "filename", "generator"):
            assert untrusted_source in lowered, (name, untrusted_source)

    contract = _flat(
        ".agents/skills/a-story-direct-visual-story/references/checker-contract.md"
    )
    for field in (
        "visual-review-provenance/v2",
        "author_task_id",
        "author_run_id",
        "reviewer_task_id",
        "reviewer_run_id",
        "raw_response_fingerprint",
        "director-event/v2",
        "format_contract_fingerprint",
        "creator_correction_fingerprint",
        "generation_payload_fingerprint",
        "raw_response_artifact",
        "compiled-prompt-handoff/v1",
    ):
        assert field in contract
    assert "not cryptographic proof" in contract
    assert "Dimensions are decoded from the current pixels" in contract


def test_visual_story_legacy_packages_cannot_inherit_pass():
    skill = _read(".agents/skills/a-story-direct-visual-story/SKILL.md")
    contract = _read(
        ".agents/skills/a-story-direct-visual-story/references/checker-contract.md"
    )
    migration_path = (
        ".agents/skills/a-story-direct-visual-story/references/"
        "legacy-package-migration.md"
    )
    migration = _flat(migration_path)

    assert "references/legacy-package-migration.md" in skill
    assert "legacy-package-migration.md" in contract
    assert "may not be promoted" in migration
    assert "Never synthesize PASS" in migration
    assert "Do not fabricate" in migration
    assert "LEGACY_UNVERIFIED" in migration
    assert "rerun the event" in migration


def test_long_visual_story_references_have_compact_navigation():
    reference_dir = (
        WORKSPACE / ".agents" / "skills" / "a-story-direct-visual-story" / "references"
    )

    for path in reference_dir.glob("*.md"):
        lines = path.read_text(encoding="utf-8").splitlines()
        if len(lines) > 100:
            assert "## Contents" in lines[:30], path.name


def test_agents_md_requires_one_command_currentness_and_learning_updates():
    agents = _flat("AGENTS.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Prefer one-command workflows",
        "name the missing automation link and plan it",
        "check current official docs",
        "Agentic OS health, skill registry, wiki health, and focused tests",
        "Important learnings must update the durable layer",
        "no generic AI process fluff",
    ):
        assert fragment in agents

    assert "Prefer one-command automation" in skill
    assert "missing automation link" in skill


def test_agents_md_preserves_project_specific_sources_and_commands():
    agents = _read("AGENTS.md")

    for fragment in (
        "config/rules/",
        "config/agentic_context_manifest.json",
        "config/skill-systems.json",
        "config/skills/carousel-jam-runtime-context.md",
        "docs/superpowers/plans/2026-06-28-analysis-hot-path-repair.md",
        "docs/ai-ops-playbook.md",
        "scripts/agentic_os.py carousel-doctor",
        "memory/working.md` is pointer-only",
        "Learning proposals are draft-only",
        "make carousel STORY=",
        "scripts/autopublish.py",
    ):
        assert fragment in agents


def test_agents_md_uses_native_output_dimensions_not_square_default():
    agents = _flat("AGENTS.md")

    assert "default post/carousel deliverable is only `1080x1440`" in agents
    assert "Reel/story `1080x1920`" in agents
    assert "only when the creator explicitly requests" in agents
    assert "Never add an automatic multi-format derivative" in agents
    assert "native 1080x1920 story/reel finals;" not in agents
    assert "1080x1080 proof/concept/single-slide generation gate" not in agents


def test_root_and_runtime_default_to_post_only_and_keep_reels_explicit():
    agents = _flat("AGENTS.md")
    dimensions = _flat("config/rules/image-dimensions.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    format_contract = _read("pipeline/stages/carousel_format_contract.py")

    assert "post/carousel deliverable is only `1080x1440`" in agents
    assert "story/reel finals only when the creator explicitly requested" in agents
    assert "If the creator explicitly asks for Story, Stories, Reel, or Reels, use `1080x1920`" in dimensions
    assert "The no-canvas default is 3:4 only; 9:16 and 1:1 remain explicit-only" in runtime
    assert 'DEFAULT_NATIVE_FORMATS = (INSTAGRAM_POST_FORMAT,)' in format_contract


def test_format_inference_preflight_blocks_repo_default_snapback():
    rule = _flat("config/rules/image-dimensions.md")
    skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    framework = _flat("config/skills/illustration-carousel-framework.md")
    master = _flat("config/references/a-story-illustration-master-prompt.md")
    memory = _flat("memory/semantic/engineering-workflow-preferences.md")

    for text in (rule, skill, runtime, framework, master, memory):
        assert "format inference preflight" in text.lower()
        assert "current creator instruction" in text
        assert "correction overrides" in text or "correction, that correction overrides" in text
        assert "repo defaults" in text
        assert "ask for the exact canvas" in text

    assert "Do not silently snap back to `3:4`, `9:16`, feed, Story, Reel, square" in _read(
        "config/rules/image-dimensions.md"
    )
    assert "Generating an unrequested Story/Reel/long variant" in _read(
        "config/rules/image-dimensions.md"
    )


def test_carousel_jam_skill_matches_hot_path_contract():
    skill = _read(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Small Brief First",
        "Free Creative Pass First",
        "Human Draft First",
        "Context As Seasoning",
        "engineering is the guardrail layer",
        "No Visible Framework Language",
        "concept lock, copy lock, imagegen proof lock, and final package lock",
        "Use subagents only for bounded reviews",
    ):
        assert fragment in skill

    assert "Run Layer E before concept selection" not in skill
    assert "golden-theme variant tournament" not in skill
    assert "Run a nested debate room" not in skill
    assert "Stage-Scene Gate" not in skill
    assert "Visual Debate" not in skill


def test_creator_skill_stack_hook_loads_on_session_start_and_jam():
    skill_stack = _read("config/skills/creator-skill-stack.md")
    skill_systems = _read("config/skill-systems.json")
    context_manifest = _read("config/agentic_context_manifest.json")
    jam_today = _read("scripts/jam_today.py")
    runtime = _read("config/skills/carousel-jam-runtime-context.md")
    autopilot = _read("config/skills/carousel-jam-autopilot.md")
    carousel_skill = _read(".agents/skills/a-story-carousel-jam/SKILL.md")

    for fragment in (
        "Session Start Hook",
        "Jam Hook",
        "Scroll-Stop Skill",
        "Recognition Skill",
        "Story Change Skill",
        "Emotional Contradiction Skill",
        "Scene-Proof Skill",
        "Retention Ladder Skill",
        "Payoff Skill",
        "Format Remix Skill",
        "Audience Mirror Skill",
        "Volume Skill",
        "Taste Gate Skill",
        "DM Send Test",
        "Mandatory Storytelling Change Hook",
    ):
        assert fragment in skill_stack

    assert "Do not copy the story engine into this file" in _flat(
        "config/skills/creator-skill-stack.md"
    )

    for surface in (skill_systems, context_manifest, jam_today, runtime, autopilot):
        assert "config/skills/creator-skill-stack.md" in surface

    for surface in (skill_systems, context_manifest, jam_today, runtime, carousel_skill):
        assert ".agents/skills/a-story-storytelling-hook/SKILL.md" in surface


def test_storytelling_change_hook_is_loaded_untruncated_before_heavy_rules():
    pack = assemble_context_pack(WORKSPACE, profile="a-story-of-two")
    sections = {section.id: section for section in pack.sections}
    order = [section.id for section in pack.sections]

    assert order.index("creator_skill_stack") < order.index("rule_palette")
    assert order.index("storytelling_change_hook") < order.index("rule_palette")

    for section_id in ("creator_skill_stack", "storytelling_change_hook"):
        assert not sections[section_id].truncated

    assert "That skill owns the Story" in sections["creator_skill_stack"].content
    assert "Story State Card" in sections["storytelling_change_hook"].content
    assert "before -> pressure/choice -> after" in sections["storytelling_change_hook"].content
    assert "ERCRT" in sections["storytelling_change_hook"].content
    assert "WHW" in sections["storytelling_change_hook"].content


def test_storytelling_hook_bundles_learning_and_exact_source_reference():
    skill = _read(".agents/skills/a-story-storytelling-hook/SKILL.md")
    engine = _read(".agents/skills/a-story-storytelling-hook/references/story-engine.md")
    transcript = _read(
        ".agents/skills/a-story-storytelling-hook/references/source-transcript.txt"
    )

    for fragment in (
        "Story State Card",
        "before -> pressure/choice -> after",
        "Emotion cycle",
        "Climax hint",
        "Reason to continue",
        "Twisting patterns",
        "Why",
        "How",
        "What",
    ):
        assert fragment in skill or fragment in engine

    assert "Ownership And Conflict Rules" in engine
    assert "Current creator instruction and correction" in engine
    assert not (
        WORKSPACE
        / ".agents/skills/a-story-storytelling-hook/references/repo-storytelling-source-map.md"
    ).exists()
    assert "Everything is incomplete" in transcript
    assert "ERCRT" in transcript
    assert "WHW" in transcript
    assert "PARADOLIA" in transcript


def test_storytelling_surfaces_point_to_one_canonical_engine_without_repeating_it():
    skill = _read(".agents/skills/a-story-storytelling-hook/SKILL.md")
    engine = _read(".agents/skills/a-story-storytelling-hook/references/story-engine.md")
    creator_stack = _read("config/skills/creator-skill-stack.md")
    runtime = _read("config/skills/carousel-jam-runtime-context.md")
    memory = _read("memory/semantic/storytelling-change-engine.md")

    assert engine.count("## ERCRT Translation") == 1
    assert engine.count("## WHW Translation") == 1
    assert "Emotion cycle: vary emotional intensity with cause" not in skill
    assert "Do not copy the story engine into this file" in " ".join(creator_stack.split())
    assert "Do not duplicate the story engine here" in " ".join(runtime.split())
    assert "canonical_method: `.agents/skills/a-story-storytelling-hook/references/story-engine.md`" in memory


def test_reflective_six_beat_storytelling_architecture_is_named_and_protected():
    skill = _flat(".agents/skills/a-story-storytelling-hook/SKILL.md")
    engine = _read(".agents/skills/a-story-storytelling-hook/references/story-engine.md")
    carousel_skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    director = _flat("config/skills/carousel-story-director-persona.md")
    framework = _flat("config/skills/illustration-carousel-framework.md")
    memory = _flat("memory/semantic/storytelling-change-engine.md")
    six_beat = "Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff"

    for surface in (skill, carousel_skill, director, memory):
        assert six_beat in surface

    for surface in (runtime, framework):
        for role in ("Cover", "Cold Open", "Deepening", "Conflict", "Turn", "Payoff"):
            assert role in surface
        assert "first-class" in surface or "creator-approved" in surface

    for exact_line in (
        "Cover: I was never unsure of you. I was lost inside our life.",
        "Cold open: Choosing each other had answered the easiest question.",
        "Deepening: Then life began asking harder ones.",
        "Conflict: Some days, love did not tell us what to do.",
        "Turn: Being lost together did not mean I had chosen wrong.",
        "Payoff: Commitment answered who. We are still learning how.",
    ):
        assert exact_line in engine

    assert "default seven-beat" in skill
    assert "Do not treat the six-beat route as a compressed or inferior seven-beat deck" in engine
    assert "do not pad or relabel" in carousel_skill.lower()


def test_reflective_story_phases_can_expand_across_multiple_slides():
    skill = _flat(".agents/skills/a-story-storytelling-hook/SKILL.md")
    engine = _flat(".agents/skills/a-story-storytelling-hook/references/story-engine.md")
    carousel_skill = _flat(".agents/skills/a-story-carousel-jam/SKILL.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    director = _flat("config/skills/carousel-story-director-persona.md")
    framework = _flat("config/skills/illustration-carousel-framework.md")
    memory = _flat("memory/semantic/storytelling-change-engine.md")

    for surface in (skill, engine, carousel_skill, runtime, director, framework, memory):
        assert "Deepening, Conflict, and Turn may each span multiple slides" in surface

    assert "These names describe causal story phases, not a six-slide limit" in engine
    assert "Question, Conflict, Character, And Answer Engine" in engine
    assert "at least two active story characters" in engine
    assert "Each slide must repay the previous swipe promise" in engine
    assert "generic \"swipe for more\" bait" in engine
    assert "a cold viewer must be able to explain" in engine
    assert "without relying on the caption or private creator context" in engine
    assert "one clean deepening beat and one clean conflict beat" not in engine


def test_storytelling_hook_is_always_on_for_ideation_discussion_and_rejection():
    manifest = json.loads(_read("config/agentic_context_manifest.json"))
    systems = json.loads(_read("config/skill-systems.json"))["systems"]
    skill = _flat(".agents/skills/a-story-storytelling-hook/SKILL.md")
    engine = _flat(".agents/skills/a-story-storytelling-hook/references/story-engine.md")
    metadata = _flat(".agents/skills/a-story-storytelling-hook/agents/openai.yaml")
    creator_stack = _flat("config/skills/creator-skill-stack.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    memory = _flat("memory/semantic/storytelling-change-engine.md")

    sections = manifest["profiles"]["a-story-of-two"]["sections"]
    first_two = sections[:2]
    assert [section["id"] for section in first_two] == [
        "creator_skill_stack",
        "storytelling_change_hook",
    ]
    assert all(section["required"] is True for section in first_two)

    hook_path = ".agents/skills/a-story-storytelling-hook/SKILL.md"
    assert hook_path in systems["carousel_jam"]["components"]
    assert hook_path in systems["instagram_idea_loop"]["components"]
    assert "allow_implicit_invocation: true" in metadata

    for trigger in (
        "brainstorms",
        "generates",
        "compares",
        "discusses",
        "rejects",
        "revises",
        "continues",
    ):
        assert trigger in skill

    assert "Rejection And Discussion Protocol" in engine
    assert "rejection_reasons:" in engine
    assert "reopen_conditions:" in engine
    assert "Do not return the same premise with cosmetic wording" in engine
    assert "At the start of future ideation, query Agentic OS recall/search" in engine
    assert "This is mandatory during brainstorming" in creator_stack
    assert "keep it active across brainstorming" in runtime
    assert "Never polish or rename a closed route as fresh" in memory


def test_hot_path_makes_model_first_creative_authority_durable():
    agents = _flat("AGENTS.md")
    runtime = _flat("config/skills/carousel-jam-runtime-context.md")
    prefs = _flat("memory/semantic/engineering-workflow-preferences.md")

    for text in (agents, runtime, prefs):
        assert "model owns concept, copy, and visual invention" in text
        assert "engineering is the guardrail layer" in text

    assert "free creative pass before private scoring" in agents
    assert "free creative pass before scoring" in runtime


def test_research_partner_memory_is_loaded_by_agentic_context():
    manifest = json.loads(_read("config/agentic_context_manifest.json"))
    sections = manifest["profiles"]["a-story-of-two"]["sections"]
    memory = _flat("memory/semantic/engineering-workflow-preferences.md")
    section_paths = [section["path"] for section in sections]

    assert not any(section["path"] == "memory/semantic/research-partner-operating-model.md" for section in sections)
    assert any(section["path"] == "memory/semantic/engineering-workflow-preferences.md" for section in sections)
    assert section_paths.index("memory/semantic/engineering-workflow-preferences.md") < section_paths.index(
        "memory/working.md"
    )

    for fragment in (
        "thinking research partner",
        "form explicit hypotheses",
        "challenge weak",
        "proposal-first durable updates",
        "no pretending the base model self-updates",
        "improve existing project files before",
    ):
        assert fragment in memory


def test_instruction_contract_protects_actual_project_failures():
    agents = _flat("AGENTS.md")

    for fragment in (
        "too much framework before the first human draft",
        "root docs and tool-specific docs drifting apart",
        "image outputs passing taste but failing exact text, identity, or dimensions",
        "Never revert changes you did not make",
        "Do not stage a mixed worktree silently",
        "Do not recreate `CLAUDE.md` or let skills/memory become a second competing root contract",
        "Do not edit `AGENTS.md` to resolve downstream mismatches",
        "update dependent rules, prompts, skills, and tests to match it",
    ):
        assert fragment in agents
