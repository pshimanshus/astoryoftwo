# AI Ops Playbook

last_updated: 2026-08-24
confidence: 0.95
sources:
- AGENTS.md
- memory/semantic/engineering-workflow-preferences.md
- memory/semantic/carousel-idea-preferences.md
- scripts/carousel.py
- scripts/analyze_prepost.py
- scripts/create_substack_article_package.py
- scripts/wiki_health.py
- scripts/autopublish.py

## Purpose

Use the terminal as an English-operated command surface for @a.storyof.two.
The goal is to reduce repeated manual work: Codex can inspect repo state,
choose the right existing workflow, run it, verify the result, and leave a
reviewable package state.

## Daily Loop

1. Run `make brief`.
2. Pick one lane: Reel pre-post, carousel jam, article package, or infra health.
3. Run the matching Make target.
4. Check current package state and actual generated pixels before treating the
   work as done.

`make health` is a repository-maintenance/closeout command. An ordinary
carousel run never invokes it and never writes wiki, memory, rules, tests, or
diagnostics.

## Command Surface

`make brief`

Shows latest creative outputs, health status, memory files, and suggested next
commands.

`make jam MOMENT="one specific couple moment"`

Prepares a small carousel jam from the supplied moment. Deep research and the
multi-agent Instagram idea loop are explicit opt-ins, never default preflight.

`make prepost CONCEPT="planned Reel concept"`

Runs the 5-agent pre-post analysis and returns POST / REVISE / REWORK / KILL.
Optional variables: `HOOK`, `CAPTION`, `EDIT`, `AUDIO`, `COVER`.

`make carousel STORY="source story" CREATIVE_BRIEF="locked-brief.json" TITLE="optional title"`

Creates the minimal v3 package and, when the creative brief contains locked
physical actions, prepares the selected risky proof. Story-only input remains
`draft` and makes no generation call. Optional variables include `STORY_FILE`,
`STORY_IMAGES`, `IDENTITY_IMAGES`, `STYLE_REFERENCES`, `FORMATS`, `OUTPUT_ROOT`,
and `PROOF_SLIDE`.

The canonical lifecycle is:

```bash
python scripts/carousel.py create ... --prepare-proof --proof-slide 3
python scripts/carousel.py ingest PACKAGE --instagram-post returned-proof.png --proof-slide 3
python scripts/carousel.py review PACKAGE --qa authored-proof-qa.json
python scripts/carousel.py approve PACKAGE --proof-sha256 sha256:<bound-proof-hash>
python scripts/carousel.py prepare PACKAGE
python scripts/carousel.py ingest PACKAGE --instagram-post slide-01.png --instagram-post slide-02.png  # repeat in selected-slide order
python scripts/carousel.py review PACKAGE --qa authored-final-qa.json
python scripts/carousel.py finalize PACKAGE
python scripts/carousel.py status PACKAGE
```

Every command returns versioned JSON with `package_dir`, `state`,
`next_action`, selected slides, and selected formats. Invalid/blocked input is
nonzero; `awaiting_creator_proof_approval` is a successful pause.

At `handoff_ready`, Codex reads the selected compiled prompt, attaches the
identity dossier's exact four-file Aachu/Zuv/together bundle plus the single
package-bound canonical style contact sheet,
calls image generation only for selected slides, ingests each returned file,
opens the decoded pixels with `view_image`, and submits hash/dimension-bound
QA. If generation or pixel viewing is unavailable, report
`handoff_ready: BLOCKED/NOT_RUN`; never claim a PASS.

That five-file attachment set is the boundary observed in the current built-in
Codex runtime smoke, not a claim about a documented platform limit. Do not add
the three individual style slides on top of the style board or silently omit an
identity file.

Prompts still request exact `1080x1440; native 3:4` for posts. As an observed
built-in-runtime accommodation, repo ingest may quarantine an untouched exact
3:4 post source from 1080x1440 through 1440x1920 inclusive, retain its source
hash/dimensions, and downsample once proportionally to exact 1080x1440. Crop,
pad, stretch, upscale, wrong-ratio input, and a second resample are blocked;
Story/Reel and square remain exact-source only. Approved normalized proof bytes
are reused as the final candidate.

For repository validation—not an ordinary carousel run—use
`python scripts/benchmark_carousel.py --runs 3 --json`. It exercises the public
CLI with temporary synthetic images and reports timing, RSS, and package
overhead; it explicitly does not claim the images passed real vision review.

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
- Do not call a carousel done unless state is `publish_ready`, the requested
  native files have passed actual-pixel QA, and final manifest/audit bindings
  match. Default output is only 1080x1440; Story/Reel and square exist only when
  explicitly requested.
- Do not use this layer to weaken the existing C-layer or D-layer gates. It is
  a command surface, not a replacement for the creative rules.
- Keep new automation boring and inspectable: small scripts, visible commands,
  no hidden network dependency.
- Use only `draft`, `blocked`, `handoff_ready`, `proof_qa_required`,
  `proof_failed`, `awaiting_creator_proof_approval`, `batch_ready`,
  `final_qa_required`, `final_qa_failed`, and `publish_ready` for public
  carousel state.
