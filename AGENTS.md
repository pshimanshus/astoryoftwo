# AGENTS.md - A Story of Two

This is the project contract for agents working in this repo.

The job is not to make the system look more agentic. The job is to help the
creator use this project to plan fresh concepts, develop sharper ideas, and
create illustrations for @a.storyof.two without losing the actual couple, the
actual voice, or the actual production gates.

Use this file as the router. Keep the deeper theory in the files it points to.

## What This Repo Is

`astoryoftwo-analysis` is the content intelligence and creative production repo
for @a.storyof.two: Instagram analysis, wiki/memory, carousel packages, image
handoffs, audits, and publishing closeout.

## What Matters Most

- Fresh ideas must feel shareable on Instagram: a couple moment, a love
  learning, or a tiny private recognition that makes someone think "this is me",
  "this is her", or "this is us" and send it to their partner.
- A good idea should be shapeable as a post, Reel, carousel, or multi-format
  package unless the creator asks for one exact format.
- The creator may bring a seed, or may ask the agent to jam and propose fresh
  concept ideas. Do not make the creator arrive with the concept already solved.
- At creative session start and jam start, use
  `config/skills/creator-skill-stack.md` as the hook for scroll stop,
  recognition, scene proof, retention, payoff, format remix, and DM-send
  thinking before showing concepts.
- Aachu and Zuv must both stay recognizable. Actual identity/reference images
  must guide the whole illustrated person, not just a face patch.
- Keep face, hair, body proportions, height, expression, posture, and clothing
  style consistent across the work. When current/couple photos are provided,
  clothing and couple styling come from those images first.
- Native formats and brandmark are production gates, not polish. The default
  post/carousel deliverable is only `1080x1440`. Generate Reel/story
  `1080x1920` or square `1080x1080` only when the creator explicitly requests
  that format. Never add an automatic multi-format derivative. Keep the tiny
  `@a.storyof.two` brandmark on every requested output.
- Prefer one-command workflows. If one command cannot create the brief/package,
  run checks, and produce the relevant post/Reel/carousel outputs, name the
  missing automation link and plan it instead of doing scattered manual work.
- Keep the workflow current. For Codex, OpenAI API, model, or agent behavior,
  check current official docs before making durable claims or workflow changes.
  For local behavior, use Agentic OS health, skill registry, wiki health, and
  focused tests.
- Important learnings must update the durable layer: `config/rules/`,
  `config/skills/`, `memory/semantic/`, tests, and any matching skill surface.
  Keep this file human, concise, and specific; no generic AI process fluff.
- When the creator asks to explore a product, startup, or tool idea, act like a
  rigorous AI PM before designing features: establish the user and buyer, the
  painful job, current alternatives, demand signals, urgency, budget, trust or
  switching barriers, wedge, and falsifiable tests. Do need and demand first;
  do not jump to UI, architecture, or feature lists until the market case is
  crisp.

The repo has failed in predictable ways:

- too much framework before the first human draft;
- too many always-on gates for small creative asks;
- root docs and tool-specific docs drifting apart;
- image outputs passing taste but failing exact text, identity, or dimensions;
- generated artifacts and human edits getting mixed in the same worktree.

Work against those failures.

## First Move

Before acting, silently normalize the user's request into:

- goal;
- context;
- constraints;
- done when.

If that brief is not clear enough to act safely, ask the smallest useful
question. Preserve exact user text, paths, commands, captions, IDs, and quoted
copy.

Check the current worktree before substantial edits. This repo often has mixed
human, generated, and previous-agent changes. Never revert changes you did not make.
If something looks unrelated, leave it alone.

## Instruction Precedence

Explicit user prompts in the current chat override repo docs, skills, memory,
and `config/rules/`.

If more `AGENTS.md` files are added later, the closest `AGENTS.md` to the file
being changed governs that subtree. Deeper files override this root router only
inside their own scope.

`config/rules/` is the canonical creative rule layer for this repo: it settles
conflicts among skills, memory, references, and old packages. It does not
override an explicit user request or a nearer `AGENTS.md`.

## Source Of Truth

Canonical rules live in `config/rules/`. If a skill, memory file, reference, or
old package disagrees with `config/rules/`, the rule file wins.

| Rule | File | Covers |
| --- | --- | --- |
| palette | `config/rules/palette.md` | warm ivory paper, watercolor-and-ink style, palette hard fails |
| identity | `config/rules/identity.md` | Aachu/Zuv identity, face preservation, height, wardrobe, pose |
| on-image-text | `config/rules/on-image-text.md` | exact slide text, typography, anti-invention |
| brandmark | `config/rules/brandmark.md` | tiny `@a.storyof.two` top-right signature |
| image-dimensions | `config/rules/image-dimensions.md` | default post/carousel output is only 1080x1440; 1080x1920 story/reel and 1080x1080 square are explicit-request-only |
| visual-variety | `config/rules/visual-variety.md` | shot ladder, setting/action variety, repeated-scene hard fails |
| relationship-motion | `config/rules/relationship-motion.md` | relationship proof without defaulting to Zuv-handler care |
| brand-zone | `config/rules/brand-zone.md` | sponsored brand/product legibility workflow |
| voice | `config/rules/voice.md` | @a.storyof.two voice, public naming, caption taste |
| golden-theme | `config/rules/golden-theme.md` | strongest repeatable love-theme spine and repair logic |
| story-selling | `config/rules/story-selling.md` | private story-selling diagnosis and quality caps |

The Agentic OS context loader expands these through
`config/agentic_context_manifest.json`. Workflow systems live in
`config/skill-systems.json`.

## Repo Map

- `AGENTS.md`: this router.
- `.agents/skills/`: repo-scoped Codex skills.
- `config/rules/`: canonical creative rules.
- `config/skills/`: workflow and creative operating references.
- `config/references/`: style, identity, and research references.
- `agents/`: specialist agent prompts.
- `pipeline/agentic/`: Agentic OS control plane.
- `pipeline/stages/`: deterministic pipeline modules.
- `scripts/`: CLI entrypoints and closeout tools.
- `memory/`: working, semantic, episodic, and indexed memory.
- `wiki/`: compiled knowledge pages.
- `output/`: generated reports, packages, diagnostics, and media.
- `tests/`: regression and contract tests.

## Agentic OS Control Plane

Use Agentic OS when context, memory, workflow registry, recall, package health,
learning proposals, or instruction drift matter.

```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "visual first carousel"
venv/bin/python scripts/agentic_os.py recall "kitchen comedy carousel"
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
venv/bin/python scripts/agentic_os.py health
```

Learning proposals are draft-only. Do not silently edit skills, rules, memory,
or context because a run "learned" something. Durable creator corrections belong
in `memory/semantic/` plus the relevant `config/rules/*.md`,
`config/skills/*.md`, or contract JSON. `memory/working.md` is pointer-only.
Keep this exact rule in mind: memory/working.md is pointer-only.

## Workflow Routing

Prefer repo-scoped skills when the task matches:

- `$a-story-carousel-jam`: idea, copy, visuals, prompts, or final carousel work.
- `$a-story-article`: carousel or love story into a Substack article package.
- `$a-story-prepost`: planned Reel analysis before publishing.
- `$a-story-wiki-health`: wiki, memory, context, and instruction health.
- `$a-story-closeout`: safe publish gate for substantial repo sessions.

The matching systems are in `config/skill-systems.json`:

- `carousel_jam`
- `story_article`
- `prepost_reel`
- `wiki_health`

## Carousel Hot Path

For normal carousel work, use the Idea -> Format -> Proof -> Package loop:

There are two valid starts. The creator may bring a seed: a feeling, situation,
photo, line, joke, reference, or half-formed thought. The creator may also ask
you to jam and propose fresh concept ideas. Do not require the creator to arrive
with the concept already formed.

1. Small Brief First: preserve the creator's seed when one exists, or create a
   small brief from channel memory, current constraints, and fresh idea lanes
   when the creator asks you to jam.
2. Format First: decide whether the idea is strongest as a post, Reel,
   carousel, or multi-format package before building assets.
3. Free Creative Pass First: model owns concept, copy, and visual invention;
   generate the alive baseline before private scoring, agent debate, or
   packaging. Preserve the free creative pass before private scoring whenever
   the creator or model has already produced a strong route.
4. Human Draft First: write or preserve the plain emotionally alive baseline
   before private scoring or agent debate.
5. Context As Seasoning: use runtime context, rules, memory, winners, and
   references quietly to improve the draft.
6. Guardrail Second: engineering is the guardrail layer for repeated ideas,
   identity drift, visual issues, exact text, brandmark, dimensions, stale
   artifacts, and guidance failures; it should block hard failures, not own the
   first idea.
7. Concept Lock: ask for creator approval only after the route feels alive.
8. Copy Lock: lock exact slide text before visual handoff.
9. Imagegen Proof Lock: prove the riskiest slide first when identity, text,
   style, canvas, or emotion could fail.
10. Final Package Lock: finish only after native outputs, visual QA, and final
   audit exist.

Use `config/skills/carousel-jam-runtime-context.md` as the compact first read.
Open the long sources only for targeted scoring, repair, conflict resolution,
memory updates, or final audit evidence:

- `wiki/insights/successful-carousel-standard.md`
- `memory/semantic/carousel-idea-preferences.md`
- `config/skills/romance-story-selling-engine.md`
- `config/skills/golden-viral-carousel-theme.md`

Do not answer a small creative brief with a framework report. Do not expose
internal terms in public copy or creator-facing drafts unless the creator asks
for analysis. The private intelligence should make the work sharper, not louder.

Use agents surgically. Subagents are useful for bounded audits, output
forensics, reference extraction, visual risk review, and final skepticism. They
are not the default creative runtime.

Before image generation, selected Aachu/Zuv identity images and style references
must be attached or explicitly unavailable. Text-only "same couple" prompts are
not enough for final art. Wardrobe should come from attached identity or
current-request photos before any static menu.

Do not call a carousel done until it has:

- native 1080x1440 post finals by default;
- native 1080x1920 story/reel finals only when the creator explicitly requested
  Story or Reel;
- native 1080x1080 square finals only when the creator explicitly requested
  square;
- exact on-image text or a documented text exception;
- identity/style-reference review;
- tiny `@a.storyof.two` brandmark;
- visual QA;
- final audit.

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

Useful direct commands:

```bash
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
venv/bin/python scripts/agentic_os.py health
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "short human-readable summary of what changed"
venv/bin/python scripts/autopublish.py \
  --session-note "short human-readable summary of what changed"
```

Use repeated `--include PATH` flags when the worktree contains unrelated human
changes. Do not stage a mixed worktree silently.

## Testing

Run the smallest relevant test first. For instruction-surface changes, start
with:

```bash
venv/bin/python -m pytest tests/test_creator_workflow_contract.py -q
venv/bin/python -m pytest tests/test_agentic_docs_contract.py tests/test_codex_project_surfaces.py -q
venv/bin/python scripts/agentic_os.py health
```

If the change touches rules, memory, context, skill registry, workflow docs, or
Agentic OS files, run wiki health before closeout:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "short human-readable summary of what changed"
```

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

## Review guidelines

When reviewing code or PRs, lead with serious findings:

- secret leaks, `.env` exposure, identity-reference leakage, or risky generated
  media under tracked paths;
- broken closeout gates, missing tests, or skipped wiki/memory health;
- duplicated rule authority outside `config/rules/`;
- prompt-compile drift that drops canonical rule fragments;
- carousel regressions that lose the human baseline, exact text, identity refs,
  native output sizes, visual QA, or final audit;
- changes that weaken `scripts/autopublish.py`, `scripts/wiki_health.py`, or
  the Agentic OS control plane.

## Do Not

- Do not delete `corpus/posts/`, `corpus/reels/`, or `memory/episodic/`.
- Do not commit `.env` or live-looking secrets.
- Do not modify raw corpus without rerunning the parse stage.
- Do not treat generated `output/` churn as source truth.
- Do not replace closeout with blind background pushing, timed daemons, or
  manual reminders.
- Do not recreate `CLAUDE.md` or let skills/memory become a second competing root contract.
- Do not edit `AGENTS.md` to resolve downstream mismatches. Treat this file as
  the source text and update dependent rules, prompts, skills, and tests to
  match it unless the creator explicitly asks to replace `AGENTS.md`.

## Done Criteria

For substantial repo sessions:

1. Inspect `git status --short` and separate unrelated human changes.
2. Run focused tests.
3. Run `venv/bin/python scripts/agentic_os.py health` when instruction,
   workflow, memory, context, or Agentic OS files changed.
4. Run wiki health when rules, skills, memory, context, or workflow docs changed.
5. Run the safe autopublish closeout gate unless the user explicitly keeps the
   work local.

## More Detail

Use these files instead of expanding this router:

- `docs/agentic-os-operating-manual.md`: preserved historical operating contract.
- `docs/superpowers/plans/creative-os-master-plan.md`: canonical creative OS plan.
- `docs/superpowers/plans/THE-PLAN.md`: ordered execution plan.
- `docs/superpowers/plans/2026-06-28-analysis-hot-path-repair.md`: current repair plan.
- `docs/ai-ops-playbook.md`: English command surface.
- `config/skill-systems.json`: workflow registry.
- `config/rules/*`: canonical rules.
- `config/skills/carousel-jam-runtime-context.md`: compact carousel runtime.
- `config/skills/carousel-jam-autopilot.md`: carousel execution workflow.
- `config/skills/illustration-carousel-framework.md`: image package framework.
- `config/skills/couple-substack-article-framework.md`: article workflow.
- `scripts/analyze_prepost.py`: Reel pre-post workflow.
- `scripts/autopublish.py`: verified closeout.
