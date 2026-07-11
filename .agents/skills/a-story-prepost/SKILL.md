---
name: a-story-prepost
description: Analyze a planned A Story of Two Reel, hook, edit, audio, cover, caption, or pre-post idea before publishing. Use for POST/REVISE/REWORK/KILL verdicts, Reel concept checks, hook repair, retention notes, caption advice, audio/cover review, or love-story prepost analysis; do not use for finished carousel packaging or article conversion.
---

# A Story Pre-Post

## Overview

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
- Preserve exact creator-provided hook, caption, audio, cover, edit notes, and
  concept language.

## Workflow

1. Preserve the planned Reel inputs exactly.
2. Load the `prepost_reel` system and run `scripts/analyze_prepost.py` when the
   request needs a full artifact.
3. For love or couple-story Reels, diagnose the emotional story before scoring
   mechanics.
4. Return a clear verdict with the smallest useful repair.
5. Save or reference the generated prepost artifact when the command creates
   one.

## Useful Commands

```bash
make prepost CONCEPT="planned Reel concept"
venv/bin/python scripts/analyze_prepost.py --concept "planned Reel concept"
venv/bin/python scripts/agentic_os.py skill-system prepost_reel
```
