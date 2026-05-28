# AI Ops Playbook

last_updated: 2026-05-28
confidence: 0.82
sources:
- AGENTS.md
- memory/semantic/engineering-workflow-preferences.md
- memory/semantic/carousel-idea-preferences.md
- scripts/create_illustration_carousel.py
- scripts/analyze_prepost.py
- scripts/create_substack_article_package.py
- scripts/wiki_health.py
- scripts/autopublish.py

## Purpose

Use the terminal as an English-operated command surface for @a.storyof.two.
The goal is to reduce repeated manual work: Codex can inspect repo state,
choose the right existing workflow, run it, verify the result, and leave a
memory trail.

## Daily Loop

1. Run `make brief`.
2. Pick one lane: Reel pre-post, carousel jam, article package, or infra health.
3. Run the matching Make target.
4. Verify with `make health NOTE="short summary of what changed"`.
5. Check generated files before treating the work as done.

## Command Surface

`make brief`

Shows latest creative outputs, health status, memory files, and suggested next
commands.

`make jam MOMENT="one specific couple moment"`

Prepares the carousel jam context. It reminds the operator to use the golden
theme, idea-preference ledger, Layer E story-selling engine, and story-director
persona before packaging.

`make prepost CONCEPT="planned Reel concept"`

Runs the 5-agent pre-post analysis and returns POST / REVISE / REWORK / KILL.
Optional variables: `HOOK`, `CAPTION`, `EDIT`, `AUDIO`, `COVER`.

`make carousel STORY="source story" TITLE="optional title"`

Creates a C-layer carousel package using the existing local Codex-native
pipeline. Optional variables: `SLIDES`, `IMAGE`, `IDENTITY_IMAGE`.

`make article CAROUSEL=output/carousels/YYYY-MM-DD/slug TITLE="optional title"`

Creates a gated Substack article package from a carousel package.

`make health NOTE="what changed"`

Runs wiki/memory health with write and index repair enabled. This is the
session-close gate for substantial work.

`make publish NOTE="what changed" INCLUDE="path1 path2"`

Runs the safe closeout gate: inspect changed paths, block risky media/secrets,
run tests, run wiki health, commit, and push. Use `INCLUDE` when the worktree
contains changes outside the current session. Use `make publish-dry-run` first
when scope is unclear.

## Good English Prompts For Codex

Use these when you want the agent, not your memory, to drive the terminal.

```text
Run make brief, inspect the suggested next commands, and tell me what is most
important today.
```

```text
Take this Reel idea through pre-post analysis. If it is REVISE or worse, tell
me the smallest fix that would make it postable.
```

```text
Prepare a carousel jam from this moment. Read the idea-preference ledger first
and do not repeat cooled-down lanes.
```

```text
Create the article package for this carousel, then inspect editorial gates and
tell me what is still not publish-ready.
```

```text
Run health. If the wiki reports NEEDS_HEAL, treat that as a blocker and fix or
name the exact next-session repair.
```

## Operating Rules

- Prefer the Make target over remembering long script invocations.
- Do not bypass health when work touches memory, wiki, core scripts, or
  pipeline contracts.
- Do not publish a mixed worktree without either inspecting every changed path
  or passing explicit `INCLUDE` paths to the safe publish gate.
- Do not call a carousel done unless the package has final images, visual QA,
  final audit, and native 4:5 plus separate native 9:16 outputs.
- Do not use this layer to weaken the existing C-layer or D-layer gates. It is
  a command surface, not a replacement for the creative rules.
- Keep new automation boring and inspectable: small scripts, visible commands,
  no hidden network dependency.
