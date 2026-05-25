"""
Pre-post analysis pipeline for @a.storyof.two.
Orchestrates five specialist agents to evaluate a planned Reel before posting.

Usage:
    python -m pipeline.stages.b1_prepost --concept "Description" [options]
    python scripts/analyze_prepost.py  (interactive mode)
"""

import anthropic
import json
import os
import sys
from datetime import datetime
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent.parent
SKILLS_DIR = BASE_DIR / "config" / "skills"
AGENTS_DIR = BASE_DIR / "agents"
OUTPUT_DIR = BASE_DIR / "output" / "prepost"
VOICE_FILE = BASE_DIR / "config" / "voice.md"
WORKING_MEMORY = BASE_DIR / "memory" / "working.md"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RELATED_SKILL_REFERENCES = {
    "romance-story-selling-engine": [
        BASE_DIR / "config" / "references" / "story-selling-canon" / "source-policy.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "a-story-of-two-adaptation.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "concept-process-cards.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "rubric.md",
        BASE_DIR / "config" / "references" / "story-selling-canon" / "story-selling-online.md",
    ],
}

PREPOST_AGENT_CONFIGS = [
    (
        "hook-analyzer",
        [
            "romance-story-selling-engine",
            "hook-and-edit-framework",
            "instagram-algorithm-2026",
            "indian-creator-intelligence",
        ],
    ),
    (
        "edit-auditor",
        [
            "romance-story-selling-engine",
            "hook-and-edit-framework",
            "instagram-algorithm-2026",
        ],
    ),
    (
        "algorithm-scorer",
        [
            "romance-story-selling-engine",
            "instagram-algorithm-2026",
            "hook-and-edit-framework",
        ],
    ),
    (
        "caption-advisor",
        [
            "romance-story-selling-engine",
            "indian-creator-intelligence",
            "instagram-algorithm-2026",
        ],
    ),
    (
        "cultural-resonance",
        [
            "romance-story-selling-engine",
            "indian-creator-intelligence",
        ],
    ),
]

ORCHESTRATOR_SKILLS = [
    "romance-story-selling-engine",
    "instagram-algorithm-2026",
    "hook-and-edit-framework",
    "indian-creator-intelligence",
]


def load_skill(name: str) -> str:
    path = SKILLS_DIR / f"{name}.md"
    if path.exists():
        body = path.read_text()
        reference_parts = []
        for reference_path in RELATED_SKILL_REFERENCES.get(name, []):
            if reference_path.exists():
                reference_parts.append(
                    f"# Required Reference: {reference_path.relative_to(BASE_DIR)}\n"
                    f"{reference_path.read_text()}"
                )
        if reference_parts:
            return body + "\n\n---\n\n" + "\n\n---\n\n".join(reference_parts)
        return body
    return f"[Skill file not found: {name}]"


def load_agent(name: str) -> str:
    path = AGENTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text()
    return f"[Agent file not found: {name}]"


def load_context() -> str:
    parts = []
    if VOICE_FILE.exists():
        parts.append(f"# Voice Guide\n{VOICE_FILE.read_text()}")
    if WORKING_MEMORY.exists():
        parts.append(f"# Working Memory\n{WORKING_MEMORY.read_text()}")
    return "\n\n---\n\n".join(parts)


def build_system_prompt(agent_name: str, skill_names: list[str]) -> str:
    agent_def = load_agent(agent_name)
    skills = "\n\n---\n\n".join([load_skill(s) for s in skill_names])
    context = load_context()

    return f"""You are a specialist content analysis agent for @a.storyof.two (Himanshu and Anchal's Instagram).
Follow the agent definition exactly. Be specific and actionable. Never be vague or generic.

# Agent Definition
{agent_def}

# Skill References
{skills}

# Channel Context
{context}
"""


def run_agent(client: anthropic.Anthropic, agent_name: str, skill_names: list[str], brief: dict) -> str:
    system = build_system_prompt(agent_name, skill_names)
    brief_text = "\n".join([f"{k}: {v}" for k, v in brief.items() if v])

    message = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=2000,
        system=system,
        messages=[
            {
                "role": "user",
                "content": f"Analyze this planned Reel and produce your full evaluation output:\n\n{brief_text}",
            }
        ],
    )
    return message.content[0].text


def run_orchestrator(client: anthropic.Anthropic, brief: dict, agent_outputs: dict) -> str:
    system = build_system_prompt(
        "prepost-orchestrator",
        ORCHESTRATOR_SKILLS,
    )

    agent_reports = "\n\n---\n\n".join(
        [f"## {name} Report\n{output}" for name, output in agent_outputs.items()]
    )

    brief_text = "\n".join([f"{k}: {v}" for k, v in brief.items() if v])

    message = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=4000,
        system=system,
        messages=[
            {
                "role": "user",
                "content": f"""Synthesize these specialist agent reports into a complete Pre-Post Brief.

# Planned Reel Brief
{brief_text}

# Specialist Agent Reports
{agent_reports}

Produce the full Pre-Post Analysis output per your agent definition.""",
            }
        ],
    )
    return message.content[0].text


def analyze_prepost(brief: dict, save: bool = True) -> str:
    """
    Run full pre-post analysis pipeline on a planned Reel.

    Args:
        brief: Dict with keys: concept, hook_plan, caption_draft, edit_plan, audio, cover_frame
        save: Whether to save output to output/prepost/

    Returns:
        Full pre-post analysis report as string
    """
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

    print("Running specialist agents...")

    agent_outputs = {}
    for agent_name, skills in PREPOST_AGENT_CONFIGS:
        print(f"  → {agent_name}...")
        agent_outputs[agent_name] = run_agent(client, agent_name, skills, brief)

    print("  → prepost-orchestrator (synthesis)...")
    final_report = run_orchestrator(client, brief, agent_outputs)

    if save:
        date_str = datetime.now().strftime("%Y-%m-%d")
        concept_slug = brief.get("concept", "reel")[:40].replace(" ", "-").lower()
        concept_slug = "".join(c for c in concept_slug if c.isalnum() or c == "-")
        filename = OUTPUT_DIR / f"{date_str}-{concept_slug}.md"
        filename.write_text(final_report)
        print(f"\nReport saved → {filename}")

    return final_report


def interactive_mode() -> dict:
    """Prompt user for Reel brief interactively."""
    print("\n=== Pre-Post Analysis — @a.storyof.two ===\n")
    print("Describe the planned Reel. Press Enter to skip optional fields.\n")

    brief = {}
    brief["concept"] = input("Concept (required): ").strip()
    if not brief["concept"]:
        print("Concept is required.")
        sys.exit(1)

    brief["hook_plan"] = input("Hook plan (first 3 seconds): ").strip() or None
    brief["caption_draft"] = input("Caption draft: ").strip() or None
    brief["edit_plan"] = input("Edit plan / scene structure: ").strip() or None
    brief["audio"] = input("Planned audio: ").strip() or None
    brief["cover_frame"] = input("Cover frame description: ").strip() or None

    return {k: v for k, v in brief.items() if v}


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Pre-post Reel analysis for @a.storyof.two")
    parser.add_argument("--concept", help="Video concept description")
    parser.add_argument("--hook", help="Hook plan (first 3 seconds)")
    parser.add_argument("--caption", help="Caption draft")
    parser.add_argument("--edit", help="Edit plan / scene structure")
    parser.add_argument("--audio", help="Planned audio")
    parser.add_argument("--cover", help="Cover frame description")
    parser.add_argument("--no-save", action="store_true", help="Don't save report to file")
    args = parser.parse_args()

    if args.concept:
        brief = {
            "concept": args.concept,
            "hook_plan": args.hook,
            "caption_draft": args.caption,
            "edit_plan": args.edit,
            "audio": args.audio,
            "cover_frame": args.cover,
        }
        brief = {k: v for k, v in brief.items() if v}
    else:
        brief = interactive_mode()

    report = analyze_prepost(brief, save=not args.no_save)
    print("\n" + "=" * 60)
    print(report)
