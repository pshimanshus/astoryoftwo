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
