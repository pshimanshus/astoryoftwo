# A Story of Two — Instagram Content Analysis Platform

## What this is
Content intelligence platform for **@a.storyof.two**
(https://www.instagram.com/a.storyof.two/) — Anchal's Instagram channel about
the story of Himanshu and Anchal Sharma.

Analyses: post corpus → content themes → engagement patterns → creative insights → strategy.
Knowledge layer: LLM-compiled wiki (Karpathy pattern) + memory lifecycle (Rohit v2).

## Reading order
1. `AGENTS.md`            — Platform schema: all operations, agent contracts, memory model
2. `config/agentic_context_manifest.json` — Agentic OS context-pack manifest
3. `config/skill-systems.json` — Agentic OS workflow system registry
4. `config/channel.py`    — Instagram channel config, hashtags, content pillars
5. `config/voice.md`      — @a.storyof.two tone and aesthetic guide
6. `wiki/index.md`        — Current wiki state
7. `memory/working.md`    — Current live analysis context

## Agentic OS Control Plane

Use `pipeline/agentic/` and `scripts/agentic_os.py` before substantial
workflow work when context, memory recall, skill composition, learning
proposals, or auditability matter.

Core commands:

```bash
venv/bin/python scripts/agentic_os.py context --render
venv/bin/python scripts/agentic_os.py skill-system carousel_jam
venv/bin/python scripts/agentic_os.py index-memory
venv/bin/python scripts/agentic_os.py search "visual first carousel"
venv/bin/python scripts/agentic_os.py recall "kitchen comedy carousel"
venv/bin/python scripts/agentic_os.py health
```

The control plane is grounded by `config/agentic_context_manifest.json` and
`config/skill-systems.json`, with the full technical contract in
`docs/superpowers/specs/agentic-os-control-plane.md`. It does not auto-apply
learning. Learning events become draft proposals and must pass eval gates
before any skill/context file is changed.

## Canonical Rules — `config/rules/`

Every constraint that drives generation lives in exactly one file under
`config/rules/`. These are the load-bearing source — `config/references/`,
`config/skills/`, and `memory/semantic/` reference them, they do not
re-state them.

**Known migration gap (Task 9 of the activation sprint):** existing
`config/skills/*.md` files still inline rule text. Until the skill-dedup
task lands, rules ARE canonical at the manifest level (every session
loads `config/rules/*` via `config/agentic_context_manifest.json`) but
skill files still carry their own copies. Treat `config/rules/` as
authoritative when there is any disagreement.

| Rule | Source of truth | What it covers |
|---|---|---|
| palette | `config/rules/palette.md` | Warm-ivory paper, watercolor-and-ink style, hard fails (yellow/mustard/sepia/parchment/tan/beige), accent palette, deterministic acceptance thresholds |
| identity | `config/rules/identity.md` | Aachu/Zuv hierarchy, identity reference rule, face preservation, heights (5'6"/5'8"), wardrobe continuity, anatomy/pose rules |
| on-image-text | `config/rules/on-image-text.md` | Source-of-truth contract, placement, handwritten typography, anti-text-invention default |
| brandmark | `config/rules/brandmark.md` | Tiny `@a.storyof.two` bottom-right always |
| brand-zone | `config/rules/brand-zone.md` | Brand-integration legibility, brand-label workflow |
| voice | `config/rules/voice.md` | @a.storyof.two voice, aesthetic, content pillars, caption style, story-feel test, public-naming rule |
| golden-theme | `config/rules/golden-theme.md` | Calm Enough For Your Chaos 5-layer stack, 28/30 rubric, repair playbook |
| story-selling | `config/rules/story-selling.md` | Layer E 30-point rubric, decision rules, hard fails |

Skill files, prompt templates, and context sections compose rules via the
`{{rule:NAME}}` include syntax — `pipeline/agentic/rule_includes.py` expands
them against `config/rules/`. The context loader (`pipeline/agentic/
context_loader.py`) expands includes before token-estimating each section.

## Deterministic Gates — `pipeline/agentic/checks/`

These are the runtime checks the workflow runner uses to PASS / FAIL slides
on measurement instead of LLM opinion. Each returns a typed `WorkflowGate`.

| Check | When to call | What it measures |
|---|---|---|
| `check_palette` | after every image generation | Paper-region warm-ivory tolerance + yellow-band fraction. Calibrated against approved style-lock slides on 2026-05-31. |
| `check_ocr_text` | after every image generation | OCR vs. expected `slides.md` text. Degrades to STOP (soft skip) when easyocr is not installed. |
| `check_image_size` | after every image generation | Native 4:5 / 9:16 aspect within ±0.01 + min dimensions 1080×1350 / 1080×1920. Catches "one image resized into both formats". |
| `check_prompt_constraints` | after every prompt compile | Compiled prompt contains 8 canonical fragments (warm ivory, HARD FAIL: yellow, ON-IMAGE TEXT, @a.storyof.two, identity reference, bottom-right, Aachu, Zuv). Catches prompt-compile drift before generation. |

Active sprint: `docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md`.

## Channel identity
- Handle: @a.storyof.two
- URL: https://www.instagram.com/a.storyof.two/
- Creator: Anchal Sharma
- Subject: Himanshu + Anchal — their life, love, travel, and shared story
- Content: Photos, reels, captions, stories about their journey together

## Working rules
- Always check `memory/working.md` before any analysis run
- Wiki pages are ground truth. Raw scraped data in `corpus/raw/` is ephemeral.
- Every analysis must identify the emotional core of the content — not just metrics
- Voice guide is critical: Anchal's aesthetic is warm, intimate, visual-first
- All agents use `claude-sonnet-4-6` for analysis; `claude-opus-4-6` for creative strategy
- Instagram data fetched via Apify MCP (apify/instagram-scraper actor)

## Illustrated carousel hard gates
- Default to the Codex-native/local carousel path; do not route normal carousel image work through API image generation.
- Creator-approved illustration style lock: use the Observational Intimacy
  Premium reference bundle for future @a.storyof.two illustrations by default:
  `config/references/style-lock/observational-intimacy-premium/`. The look is
  premium hand-drawn romantic watercolor-and-ink with identity-first Aachu/Zuv
  faces, warm ivory paper, visible paper grain, fine ink/pencil linework,
  transparent watercolor blooms, tactile wardrobe/props, lower/middle-lower
  couple placement, clean upper-middle negative space for exact integrated
  handwritten ON-IMAGE TEXT, tiny bottom-right `@a.storyof.two` brandmark, and
  A Story of Two style even when outside references are used for essence.
  Product labels are allowed only when the creator explicitly requests a
  brand-integration test, and the brand/product name must be legible at
  phone-screen size.
- For every carousel, use multiple agents or parallel reviewers for concept, visual plan, identity, prompt, and QA.
- Before carousel ideation or writing, load `wiki/insights/successful-carousel-standard.md` and define audience success, creative success, brand success, and production success; if that definition is missing, Layer E has not actually run.
- Preserve the Calm Enough For Your Chaos golden-theme machine: universal relationship truth -> Aachu/Zuv proof -> Zuv active care -> tender thesis.
- Before writing hooks, slide copy, captions, visual direction, prompts, or image handoff instructions, load `config/skills/carousel-story-director-persona.md` after the existing memory/golden-theme gates. Keep it active through final native image sets and QA.
- Before any image generation, `visual-debate.json`, `visual-plan-quality.json`, and `identity-consistency-review.json` must pass.
- `visual-plan-quality.json` is per-slide. If any screen has copy-visual drift, weak relationship proof, losing-option leakage, isolated-partner metaphor, uncertain identity continuity, or unresolved doubt, mark REPAIR/BLOCKED and do not generate.

## Corpus
The `corpus/` directory contains all scraped Instagram content:
- `corpus/posts/`    — Individual post data (caption, likes, comments, hashtags)
- `corpus/reels/`    — Reel metadata and transcripts where available
- `corpus/captions/` — Extracted captions for NLP analysis
- `corpus/raw/`      — Raw Apify JSON output (ephemeral — do not depend on)

## Environment variables needed
```
APIFY_API_KEY=...
APIFY_USER_ID=...
INSTAGRAM_HANDLE=a.storyof.two
```

## Running the platform
```bash
# Analyze a planned Reel before posting (pre-post pipeline)
python scripts/analyze_prepost.py
python scripts/analyze_prepost.py --concept "Anchal tries wazwan for the first time"

# Full analysis pipeline (post-corpus)
python -m pipeline.runner

# Wiki/memory health closeout
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "short human-readable summary of what changed"

# Safe verified publish closeout
venv/bin/python scripts/autopublish.py \
  --session-note "short human-readable summary of what changed"

# Individual stages
python -m pipeline.stages.ingest      # Scrape Instagram via Apify → corpus/raw/
python -m pipeline.stages.parse       # Raw JSON → structured corpus/posts/
python -m pipeline.stages.analyze     # Posts → themes + patterns
python -m pipeline.stages.wiki_build  # Compile wiki pages from corpus
python -m pipeline.stages.report      # Generate analysis report

# Scrape fresh data
python scripts/scrape_instagram.py --handle a.storyof.two --limit 50
```

## Do not
- Delete `corpus/posts/` or `corpus/reels/` — historical content corpus
- Delete `memory/episodic/` — permanent analysis record
- Commit `.env` — secrets stay local
- Modify raw corpus without re-running parse stage
- End a substantial session without running
  `scripts/autopublish.py --session-note "short summary"` after the relevant
  checks pass
- Treat `scripts/wiki_health.py --write --fix-index` as sufficient closeout by
  itself; wiki health records memory state, but autopublish is what commits and
  pushes verified session state
