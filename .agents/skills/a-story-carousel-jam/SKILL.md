---
name: a-story-carousel-jam
description: Use when the creator wants to jam on a carousel idea, choose today's carousel, turn a moment into an illustrated post, approve copy, plan visuals, generate prompts, or continue toward final A Story of Two carousel outputs.
---

# A Story Carousel Jam

Use this repo skill as the Codex-native entrypoint for the C-layer creator jam.
It wraps the existing Agentic OS system instead of duplicating the long workflow.

## Load First

1. `config/skill-systems.json` -> `carousel_jam`
2. `config/skills/carousel-jam-autopilot.md`
3. `wiki/insights/successful-carousel-standard.md`
4. `memory/semantic/carousel-idea-preferences.md`
5. `config/skills/romance-story-selling-engine.md`
6. `config/skills/golden-viral-carousel-theme.md`
7. `config/skills/carousel-story-director-persona.md`
8. `config/skills/illustration-carousel-framework.md`

Use `venv/bin/python scripts/agentic_os.py skill-system carousel_jam` for the
machine-readable workflow record.

## Operating Contract

- Define audience success, creative success, brand success, and production
  success before writing.
- Run Layer E before concept selection.
- Run the golden-theme variant tournament and require 28/30 or repair.
- Run the Stage-Scene Gate before hooks, copy, captions, visuals, prompts, or
  image handoff.
- After copy approval, run the Post-Copy Visual Creative Room and Visual Debate
  Gate before image generation.
- Do not call the carousel final unless native 4:5 finals, separate native 9:16
  finals, visual QA, and final audit exist.

## Useful Commands

```bash
make jam MOMENT="one specific couple moment"
venv/bin/python scripts/agentic_os.py recall "carousel moment"
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
```
