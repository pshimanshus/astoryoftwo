---
name: a-story-carousel-jam
description: Jam, choose, draft, route, plan visuals, generate prompts, or package A Story of Two illustrated posts, Reels, carousels, and multi-format carousel outputs. Use for fresh ideas, today's carousel, moment-to-post, copy approval, imagegen proof, visual planning, final carousel packages, or continuing carousel work; do not use for article-only, prepost-only, or wiki-health requests.
---

# A Story Carousel Jam

## Overview

Use this repo skill as the Codex-native entrypoint for the C-layer creator jam.
It wraps the existing Agentic OS system instead of duplicating the long workflow.

## Load First

1. `config/skill-systems.json` -> `carousel_jam`
2. `config/skills/creator-skill-stack.md`
3. `config/skills/carousel-jam-runtime-context.md`
4. `config/skills/carousel-jam-autopilot.md`
5. `config/skills/carousel-story-director-persona.md`
6. `config/skills/illustration-carousel-framework.md`

Use the compact runtime context first. Do not full-read
`wiki/insights/successful-carousel-standard.md`,
`memory/semantic/carousel-idea-preferences.md`,
`config/skills/romance-story-selling-engine.md`, and
`config/skills/golden-viral-carousel-theme.md` as a routine opening move; open
those source files only for targeted scoring, repair, conflict resolution,
memory updates, or final audit evidence.

Use `venv/bin/python scripts/agentic_os.py skill-system carousel_jam` for the
machine-readable workflow record.

## Operating Contract

- Small Brief First: preserve the creator's exact feeling, situation, line, or
  image premise when one exists. If the creator asks to jam from scratch, propose
  fresh concept seeds instead of demanding a finished concept.
- Format Inference Preflight: before generating or exporting images, lock the
  requested canvas from the current creator instruction, attached references,
  and immediate corrections. A current correction overrides repo defaults. Do
  not infer `3:4`, `9:16`, feed, Story, Reel, square, or multi-format output
  from repo defaults after the creator removes or rejects that format. If the
  current canvas is unclear after a correction, ask for the exact canvas instead
  of generating.
- Fresh Idea Standard: concept seeds should feel shareable on Instagram,
  partner-sendable, and rooted in couple love moments that make someone think
  "this is me", "this is her", or "this is us."
- Creator Skill Stack Hook: before creator-facing concept suggestions, define
  the scroll stop, recognition mirror, emotional contradiction, scene proof,
  retention ladder, payoff, format remix, audience mirror, volume path, taste
  gate, and DM Send Test from `config/skills/creator-skill-stack.md`.
- Format First: choose whether the idea is strongest as a post, Reel, carousel,
  or multi-format package before building assets.
- Free Creative Pass First: model owns concept, copy, and visual invention.
  Generate or preserve the alive baseline before private scoring, routing,
  debate, or package automation.
- Human Draft First: write the plain emotionally alive baseline before private
  scoring, routing, or agent debate.
- Context As Seasoning: use the runtime context, rules, winner patterns, and
  memory quietly to improve the baseline.
- Guardrail Second: engineering is the guardrail layer for repeated ideas,
  identity drift, visual issues, exact text, brandmark, dimensions, stale
  artifacts, and house guidance. It blocks hard failures; it does not own the
  first idea.
- No Visible Framework Language: do not expose internal rubric terms in public
  copy or creator-facing drafts unless the creator asks for analysis.
- The creator-visible locks are concept lock, copy lock, imagegen proof lock, and final package lock.
- Use subagents only for bounded reviews, output forensics, visual risk,
  reference extraction, or final skepticism.
- Before image generation, attach selected actual Aachu/Zuv identity images and
  style references. Text-only identity descriptions do not satisfy final art.
  Identity references must guide the whole illustrated person, not just a face
  patch. Wardrobe and couple styling must be chosen from attached
  identity/current-request photos first.
- Do not call the carousel final unless native 1080 x 1440 post finals,
  separate native 1080 x 1920 story/reel finals, tiny `@a.storyof.two`
  brandmark, visual QA, and final audit exist.
- Prefer one-command automation through Make/script workflows. If the one-command
  path is missing, name the missing automation link and plan it instead of doing
  scattered manual steps.

## Workflow

1. Normalize the seed into a small brief, or propose fresh concept seeds when
   the creator asks to jam from scratch.
2. Choose the strongest format before writing or generating assets.
3. Run or preserve the free creative pass first, then season with runtime
   context, rules, and winner memory.
4. Get concept lock and copy lock before visual handoff.
5. Prove the riskiest imagegen slide first when identity, text, canvas, or
   emotion can fail.
6. Finish only after native outputs, brandmark, visual QA, and final audit exist.

## Useful Commands

```bash
make jam MOMENT="one specific couple moment"
make carousel STORY="source story" TITLE="optional title"
venv/bin/python scripts/agentic_os.py recall "carousel moment"
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
```
