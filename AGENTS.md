# AGENTS.md - A Story of Two Content Analysis Platform

This file is the Codex router for the repo. The canonical creative OS plan is
`docs/superpowers/plans/creative-os-master-plan.md`; the ordered execution plan
is `docs/superpowers/plans/THE-PLAN.md`; the full historical operating contract
was moved to `docs/agentic-os-operating-manual.md`. Use this file to find the
right source of truth quickly without crowding Codex project guidance.

## Source Of Truth

Canonical creative rules live in `config/rules/`. If any reference, skill, or
memory disagrees with these files, `config/rules/` wins.


| Rule          | File                            | Covers                                                                        |
| ------------- | ------------------------------- | ----------------------------------------------------------------------------- |
| palette       | `config/rules/palette.md`       | warm ivory paper, watercolor-and-ink style, hard fails, acceptance thresholds |
| identity      | `config/rules/identity.md`      | Aachu/Zuv identity, face preservation, height, wardrobe, pose                 |
| on-image-text | `config/rules/on-image-text.md` | exact slide text, placement, typography, anti-invention                       |
| brandmark     | `config/rules/brandmark.md`     | tiny `@a.storyof.two` bottom-right signature                                  |
| brand-zone    | `config/rules/brand-zone.md`    | sponsored brand/product legibility workflow                                   |
| voice         | `config/rules/voice.md`         | @a.storyof.two voice, public naming, caption taste                            |
| golden-theme  | `config/rules/golden-theme.md`  | Calm Enough For Your Chaos stack and 28/30 threshold                          |
| story-selling | `config/rules/story-selling.md` | Layer E story-selling rubric and hard fails                                   |


The Agentic OS context loader expands these rules through
`config/agentic_context_manifest.json`. Skill systems are registered in
`config/skill-systems.json`.

## Repo Layout

- `AGENTS.md` - lean Codex router and standing repo rules.
- `docs/superpowers/plans/creative-os-master-plan.md` - canonical creative OS plan.
- `docs/superpowers/plans/THE-PLAN.md` - ordered execution plan.
- `docs/agentic-os-operating-manual.md` - preserved full operating contract.
- `docs/ai-ops-playbook.md` - English command surface for common workflows.
- `.agents/skills/` - repo-scoped Codex Skill wrappers.
- `.codex/` - project Codex config, hooks, and command rules.
- `config/rules/` - canonical creative rules.
- `config/skills/` - project workflow references used by the Agentic OS.
- `agents/` - role prompts for carousel, article, pre-post, and story-selling rooms.
- `pipeline/agentic/` - Agentic OS control plane.
- `pipeline/stages/` - deterministic pipeline and carousel package modules.
- `scripts/` - CLI entrypoints and closeout tools.
- `memory/` - working, episodic, semantic, and indexed memory.
- `wiki/` - compiled knowledge pages.
- `output/` - generated reports, packages, diagnostics, and non-source artifacts.
- `tests/` - regression and contract tests.

## Agentic OS Control Plane

Use the executable Agentic OS before packaging creative work when context,
memory, skill systems, recall, learning proposals, or health matter.

Key files:

- `config/agentic_context_manifest.json`
- `config/skill-systems.json`
- `scripts/agentic_os.py`
- `pipeline/agentic/`
- `docs/superpowers/specs/agentic-os-control-plane.md`

Default commands:

```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "visual first carousel"
venv/bin/python scripts/agentic_os.py recall "kitchen comedy carousel"
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
venv/bin/python scripts/agentic_os.py health
```



Learning proposals are draft-only. The Agentic OS may create learning proposals,
but it must not silently edit skills, rules, memory, or context without
deterministic checks and explicit approval. `memory/working.md is pointer-only`:
creator corrections must propagate to `memory/semantic/` plus the relevant
`config/skills/*.md`, `config/rules/*.md`, or contract JSON when behavior
changes. Keep `memory/working.md` to current-session pointers, not durable law.

## Workflow Routing

Prefer the repo-scoped Codex Skills in `.agents/skills/` when the task matches:

- `$a-story-carousel-jam` - creator jam to final illustrated carousel package.
- `$a-story-article` - carousel or love story to Substack article package.
- `$a-story-prepost` - planned Reel analysis before posting.
- `$a-story-wiki-health` - wiki, memory, context, and instruction health.
- `$a-story-closeout` - safe publish gate for substantial repo sessions.

The matching project systems live in `config/skill-systems.json`:

- `carousel_jam`
- `story_article`
- `prepost_reel`
- `wiki_health`

## Hard Creative Rules

For carousel work, never bypass the gold creative spine:

1. Read `memory/semantic/carousel-idea-preferences.md` before pitching or
  packaging an idea.
2. Read `wiki/insights/successful-carousel-standard.md` and define audience success,
  creative success, brand success, and production success before writing.
3. Run Layer E first: `config/skills/romance-story-selling-engine.md`.
  Think like an author before thinking like a packager: find the emotional
   obstacle, choose one concept-process card, prove the truth through Aachu/Zuv
   behavior, score with Story-Selling, then write.
4. Run the golden-theme variant tournament against
  `wiki/themes/calm-enough-for-chaos.md` and
   `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`.
   Do not package or generate unless the selected route scores 28/30 or higher.
5. Run the Stage-Scene Gate before hooks, slide copy, captions, visual
  direction, prompts, or image handoff. The carousel must stage visible action,
   reaction, eye-line, hands, distance, object movement, silence, consequence,
   reversal, and payoff. text completes the scene; text must not carry the scene.
6. Load `config/skills/carousel-story-director-persona.md` before writing hooks,
  slide copy, captions, visual directions, prompts, or image handoff text.
7. After copy approval, run the Visual Debate Gate before image generation:
  the Post-Copy Visual Creative Room, then three visual agents, then
   `visual-debate.json`, then `visual-plan-quality.json`.
8. Do not call a carousel done until separate native 4:5 finals, separate
  native 9:16 finals, visual QA, and final audit exist.

Creator Jam Response Contract: when the creator asks to jam, brainstorm, pick
today's carousel, or turn one idea into a post: Do not offer the generic visual companion,
browser mockup, or design-doc approval flow. Run the carousel jam room
automatically and keep the creator in the loop at explicit checkpoints:
concept lock, copy lock, visual-plan lock, proof approval, and final approval.
Handoff is not final, partial final is not publishable, and proof/final approval
must pause for creator confirmation before the package advances.

Visual Debate Gate: after final copy confirmation, compare three or more visual
systems, record rejected motifs, repair the winner, and return GO / REPAIR /
STOP before image generation. The three visual agents are
`agents/carousel-visual-evidence-planner.md`,
`agents/carousel-romance-scene-planner.md`, and
`agents/carousel-visual-continuity-judge.md`.

## Commands

Prefer Make targets for routine workflows:

```bash
make brief
make jam MOMENT="one specific couple moment"
make prepost CONCEPT="planned Reel concept"
make carousel STORY="source story" TITLE="optional title"
make article CAROUSEL=output/carousels/YYYY-MM-DD/slug
make health NOTE="short summary"
make publish-dry-run NOTE="short summary" INCLUDE="path1 path2"
make publish NOTE="short summary" INCLUDE="path1 path2"
make test
```

Direct commands that future sessions may need:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "short human-readable summary of what changed"

venv/bin/python scripts/autopublish.py \
  --session-note "short human-readable summary of what changed"
```

Use repeated `--include PATH` flags when the worktree contains unrelated human
changes. Do not stage a mixed worktree silently.

## Codex Workflow Defaults

- Use Codex Worktrees for parallel sprint tasks and mixed worktrees. If falling
back to manual git worktrees, use `.worktrees/`, which is ignored by git.
- Use Browser for visual QA of local previews, rendered HTML, generated
diagrams, and carousel preview pages when a route can be opened without
authentication.
- Use `/review` for local PR-quality review loops before publishing meaningful
code or contract changes.
- Use GitHub `@codex review` on pull requests when cloud review is available.
- Use Automations for daily `make brief`, wiki-health drift checks, and
AGENTS/skill drift audits. Keep automation prompts scoped, boring, and
reviewable.
- Use Goal mode for long-running carousel/image pipeline repairs with a clear
definition of done.

## Review guidelines

When reviewing code or PRs, prioritize:

- secret leaks, `.env` exposure, risky generated media, identity-reference
leakage, and accidental commits under ignored output paths;
- broken closeout gates, missing tests, or skipped wiki/memory health;
- carousel regressions that bypass Layer E, golden-theme scoring, Stage-Scene
Gate, Visual Debate Gate, identity review, final native formats, visual QA, or
final audit;
- prompt-compile drift that loses canonical rule fragments;
- duplicated rule authority outside `config/rules/`;
- changes that weaken `scripts/autopublish.py`, `scripts/wiki_health.py`, or the
Agentic OS control plane.

Treat serious repo-hygiene, safety, and contract regressions as P1 review
findings. Typos in user-facing docs may be noted when they obscure commands or
workflow contracts.

## Done Criteria

For substantial repo sessions:

1. Inspect git status and separate unrelated human changes.
2. Run relevant focused tests.
3. Run `venv/bin/python scripts/agentic_os.py health` when the change touches
  skills, rules, memory, context, workflow docs, or Agentic OS files.
4. Run wiki health:
  ```bash
   venv/bin/python scripts/wiki_health.py --write --fix-index \
     --session-note "short human-readable summary of what changed"
  ```
5. Run the safe autopublish closeout gate unless the user explicitly keeps the
  work local:

The closeout gate must block risky paths, live-looking secrets, failing tests,
wiki-health failures, and unclear mixed-worktree scope. Do not replace it with
blind background pushing, timed daemons, or manual "remember to push" reminders.

## More Detail

Use these files instead of expanding AGENTS.md again:

- Full operating contract: `docs/agentic-os-operating-manual.md`
- Canonical creative OS plan: `docs/superpowers/plans/creative-os-master-plan.md`
- Ordered execution plan: `docs/superpowers/plans/THE-PLAN.md`
- Command playbook: `docs/ai-ops-playbook.md`
- Workflow systems: `config/skill-systems.json`
- Canonical rules: `config/rules/*`
- Carousel workflows: `config/skills/carousel-jam-autopilot.md`,
`config/skills/illustration-carousel-framework.md`,
`config/skills/golden-viral-carousel-theme.md`,
`config/skills/romance-story-selling-engine.md`
- Article workflow: `config/skills/couple-substack-article-framework.md`
- Pre-post workflow: `scripts/analyze_prepost.py`
- Closeout workflow: `scripts/autopublish.py`
