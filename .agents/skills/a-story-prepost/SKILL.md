---
name: a-story-prepost
description: Use when analyzing a planned Reel, hook, edit, audio, cover, caption, or pre-post idea before publishing.
---

# A Story Pre-Post

Use this repo skill for the B-layer planned Reel pre-post workflow. It wraps the
existing Agentic OS `prepost_reel` system and `scripts/analyze_prepost.py`.

## Load First

1. `config/skill-systems.json` -> `prepost_reel`
2. `scripts/analyze_prepost.py`
3. `config/skills/hook-and-edit-framework.md`
4. `config/skills/instagram-algorithm-2026.md`
5. `config/skills/indian-creator-intelligence.md`
6. `config/skills/romance-story-selling-engine.md` when the Reel is a love or
   couple story.

Use `venv/bin/python scripts/agentic_os.py skill-system prepost_reel` for the
machine-readable workflow record.

## Operating Contract

- Score the hook, retention/edit, algorithm send/save potential, caption, and
  cultural resonance.
- Return POST, REVISE, REWORK, or KILL.
- For love/couple stories, run Layer E before treating retention mechanics as
  the meaning of the Reel.
- Name the smallest repair that would improve the verdict.

## Useful Commands

```bash
make prepost CONCEPT="planned Reel concept"
venv/bin/python scripts/analyze_prepost.py --concept "planned Reel concept"
venv/bin/python scripts/agentic_os.py skill-system prepost_reel
```
