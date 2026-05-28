# AGENTS.md — A Story of Two Content Analysis Platform
# "The schema file is the real product." — Rohit Ghumare, LLM Wiki v2
# Karpathy wiki pattern + Rohit v2 memory lifecycle

## Identity
- Channel: **@a.storyof.two**
- Creator: Anchal Sharma
- Platform: Instagram
- Focus: Himanshu + Anchal's shared story — life, love, travel, moments
- Analysis goal: Understand what content resonates, what themes emerge,
  what the creative arc of this channel looks like

---

## Architecture (Seven Layers)

```
┌─────────────────────────────────────────────────────────────┐
│  LAYER E - ROMANCE STORY SELLING CANON (new)                │
│  Love-story sources + craft + online selling -> concept lens│
│  Entry skill: config/skills/romance-story-selling-engine.md │
│  References: config/references/story-selling-canon/         │
│  Gates: source legality / story-selling score / golden      │
│         theme remains mandatory for carousel work           │
└───────────────────────┬─────────────────────────────────────┘
                        │ strengthens concepts before C/D
┌───────────────────────▼─────────────────────────────────────┐
│  LAYER D — SUBSTACK LOVE ARTICLE (new)                      │
│  Carousel/podcast/story → gated love essay publish package  │
│  Entry: scripts/create_substack_article_package.py          │
│  Gates: source · love theme · image refs · structure        │
│         voice/taste · growth package · final approval       │
└───────────────────────┬─────────────────────────────────────┘
                        │ expands story packages into essays
┌─────────────────────────────────────────────────────────────┐
│  LAYER C — ILLUSTRATED CAROUSEL (new)                       │
│  Photos + story → Codex-native C1–C6 → carousel pack        │
│  Entry: scripts/create_illustration_carousel.py             │
│  Agents: C1-Story C2-Arc C3-Visual C3.5-Identity C4-Prompt │
│          C5-Copy C6-Review                                  │
└───────────────────────┬─────────────────────────────────────┘
                        │ creates reusable story packages
┌───────────────────────▼─────────────────────────────────────┐
│  LAYER 0 — PRE-POST (new)                                   │
│  Planned Reel → 5-agent analysis → POST/REVISE/REWORK/KILL  │
│  Entry: scripts/analyze_prepost.py                          │
│  Agents: B1-Hook B2-Edit B3-Algo B4-Caption B5-Culture      │
└───────────────────────┬─────────────────────────────────────┘
                        │ feeds learnings back to wiki
┌───────────────────────▼─────────────────────────────────────┐
│  LAYER 1 — SOURCES                                          │
│  Instagram posts · Reels · Captions · Hashtags · Comments  │
│  Scraped via Apify (apify/instagram-scraper)                │
└───────────────────────┬─────────────────────────────────────┘
                        │ ingest
┌───────────────────────▼─────────────────────────────────────┐
│  LAYER 2 — WIKI (Karpathy pattern)                          │
│  LLM-compiled pages: posts/ themes/ people/ insights/       │
│  Memory lifecycle: working.md · episodic/ · graph.json      │
│  (Rohit v2: confidence scoring, supersession, forgetting)   │
└───────────────────────┬─────────────────────────────────────┘
                        │ pipeline
┌───────────────────────▼─────────────────────────────────────┐
│  LAYER 3 — PIPELINE (6 stages)                              │
│  A0 → A1 → A2 → A3 → A4 → A5                               │
│                   ↑                                          │
│            human review gate                                 │
└─────────────────────────────────────────────────────────────┘
```

---

## Romance Story Selling Canon (E-Layer) - New

Entry point for making @a.storyof.two love stories feel more cinematic,
novelistic, emotionally specific, and strong enough to sell online without
becoming generic relationship advice.

Layer E is a pre-concept and repair layer. Use it before C-layer carousel
concepting or D-layer article angle work when the creator asks to make a story
more cinematic, novelistic, romantic, emotionally compelling, or better at
selling online.

Layer E is additive. It does not replace the golden viral carousel theme. For
carousel work, the golden theme remains mandatory and the selected concept must
pass both the Story-Selling rubric and the Golden Theme tournament before
packaging or image generation.

### E-Layer Skill Files

| Skill | File | Contents |
|---|---|---|
| romance-story-selling-engine | config/skills/romance-story-selling-engine.md | Lightweight operating skill for story-canon use, process-card selection, and C/D adaptation |
| source policy | config/references/story-selling-canon/source-policy.md | Legal/use safety policy, allowed use values, and source traceability rules |
| story-selling adaptation | config/references/story-selling-canon/a-story-of-two-adaptation.md | Aachu/Zuv adaptation rules, reader mirror, obstacle, proof, reversal, payoff |
| concept-process cards | config/references/story-selling-canon/concept-process-cards.md | 20 reusable concept processes derived from legal source patterns |
| story-selling rubric | config/references/story-selling-canon/rubric.md | 30-point rubric, 28/30 threshold, and hard fails |

### E-Layer Agents

| Agent | File | Role |
|---|---|---|
| E0 | agents/story-canon-orchestrator.md | Synthesizes E1-E5 into a scored concept direction |
| E1 | agents/story-source-curator.md | Verifies source legality, allowed use, quality, and diversity |
| E2 | agents/romance-arc-miner.md | Extracts emotional arcs from public-domain or licensed romance books |
| E3 | agents/film-scene-miner.md | Extracts visual scene patterns from public-domain films and metadata |
| E4 | agents/online-story-selling-miner.md | Extracts reader, proof, transformation, and CTA processes from craft/marketing sources |
| E5 | agents/story-skill-reviewer.md | Scores the concept and rejects generic or unsafe story advice |

### E-Layer Command Guidance

When the user asks to "make this more cinematic", "make this more novelistic",
"make this more romantic", "why does this love story feel flat", "make this
sell online", "find a stronger article angle", or similar, use:

- `config/skills/romance-story-selling-engine.md`
- `config/references/story-selling-canon/source-policy.md`
- `config/references/story-selling-canon/a-story-of-two-adaptation.md`
- `config/references/story-selling-canon/concept-process-cards.md`
- `config/references/story-selling-canon/rubric.md`

Default process:

1. Check source memory and legality if source-canon material is involved.
2. Choose one concept-process card.
3. Score with the 30-point Story-Selling rubric.
4. Require 28/30 or repair and rescore.
5. For carousel work, run the golden-theme variant tournament too.
6. Only then adapt the winner to the C-layer or D-layer artifact contract.

### E-Layer Hard Fails

Reject or repair before C-layer or D-layer work if:

- no emotional obstacle;
- only a pretty moment;
- generic couple dynamic;
- Zuv has no active emotional role;
- ending is a quote, not an earned payoff;
- copyrighted source text is copied into artifacts.

---

## Pipeline Stages

### A0 — Validator
Fail-fast checks: ANTHROPIC_API_KEY + APIFY_API_KEY set, all paths exist.

### A1 — Ingest  (`pipeline/stages/a1_ingest.py`)
Scrape @a.storyof.two via Apify instagram-scraper actor.
Fetch: posts, reels, captions, hashtags, like counts, comment counts, timestamps.
Output: `corpus/raw/YYYY-MM-DD.json` + structured files in `corpus/posts/`

```python
# Apify actor: apify/instagram-profile-scraper
# Input: { "usernames": ["a.storyof.two"] }
```

### A2 — Parser  (`pipeline/stages/a2_parser.py`)
Convert raw Apify JSON → normalized Post objects.
Extract: caption text, hashtags, mentions, post type (photo/reel/carousel), engagement.
Output: `corpus/posts/YYYY-MM-DD-posts.json`

### A3 — Analyzer  (`pipeline/stages/a3_analyzer.py`)
LLM analysis of post corpus. Identifies:
- Content themes (travel, food, couple moments, milestones, daily life)
- Emotional tone per post (warm/nostalgic/playful/celebratory/intimate)
- Hashtag strategy and reach signals
- Posting frequency and cadence patterns
- Top-performing vs low-performing content patterns
Output: `output/reports/YYYY-MM-DD-analysis.md`
Uses: claude-sonnet-4-6

### A4 — Wiki Builder  (`pipeline/stages/a4_wiki.py`)
Compile wiki pages from analysis. Updates:
- `wiki/themes/` — recurring content themes with confidence scores
- `wiki/insights/` — distilled strategic insights
- `wiki/posts/` — notable post entries
- `memory/working.md` — latest analysis state
Uses: claude-sonnet-4-6

### A5 — Report  (`pipeline/stages/a5_report.py`)
Generate human-readable content strategy report.
Output: `output/reports/strategy-YYYY-MM-DD.md`
⊡ Human review gate: review report before taking any action.
Uses: claude-opus-4-6

---

## Running the Pipeline

```bash
# Full analysis run
python -m pipeline.runner

# Resume from a specific stage
python -m pipeline.runner --from a3

# Single stage
python -m pipeline.runner --stage a1

# Fresh scrape only
python scripts/scrape_instagram.py
```

---

## Autopublish Closeout Gate

At the end of every substantial Codex session that changes repo files, run the
safe autopublish gate so the creator does not need to push manually:

```bash
venv/bin/python scripts/autopublish.py \
  --session-note "short human-readable summary of what changed"
```

This gate is mandatory repo infrastructure. Do not replace it with blind
background pushing, timed daemons, or manual "remember to push" reminders. The
script must block publishing if any gate fails:

- risky paths appear in git status, including `.env`, `.env.*`,
  `identity_images/`, `draft_videos/`, `corpus/raw/`, virtual environments,
  caches, logs, or generated carousel image/video outputs;
- changed text files contain live-looking secrets or populated secret
  assignments;
- `venv/bin/python -m pytest -q` fails;
- `venv/bin/python scripts/wiki_health.py --write --fix-index` fails;
- git cannot commit or push the current branch.

If the worktree contains unrelated human changes or unclear scope, do not stage
silently. Name the blocker, protect the work, and ask only for the minimum
decision needed to separate or publish the changes. Use repeated
`--include PATH` flags to publish only the paths owned by the current session
when a mixed worktree is unavoidable. If the creator tries to skip this gate
after substantial work, push back firmly: repo hygiene, memory health, tests,
and git publication are blocking concerns for this project.

Use `--dry-run` only for rehearsal or debugging. A real closeout should commit
and push after all gates pass.

---

## Illustrated Carousel Pipeline (C-Layer) — New

Entry point for turning supplied pictures and a story into an illustrated
Instagram carousel package.

Default runtime: **Codex-native/local**. The carousel entry script must not
require `ANTHROPIC_API_KEY` for normal `/story` work. It writes the complete
C-layer artifact contract, requires or discovers Aachu/Zuv identity references,
prepares model-native publishable image-generation prompts, packages two native
final outputs per slide, and fails the final audit until both model-native
formats and visual QA exist. The default final generation flow must create a
separate 4:5 Instagram post image and a separate 9:16 Reels/Stories image for
each slide; never create one image and resize, crop, or pad it into the other
format. The final output agents/workers are: Instagram Post Output, Reels/Stories
Output, and Identity/Visual QA. Each generated slide includes the illustration,
exact copy, brandmark, faces, outfits, and composition together.
`final-with-text/` is legacy local-overlay fallback only. The
Anthropic-backed C1-C6 runner is optional legacy mode: use `--mode anthropic`
only when an external Anthropic API run is explicitly desired.
For illustrated carousel work, never use a single-pass reviewer path. Use
multiple agents or parallel reviewers for concept, visual plan, identity,
prompt, and final QA. Preserve the golden-theme learnings as hard creative
memory. Before generation, write `visual-plan-quality.json` with per-slide
GO / REPAIR / STOP checks for golden-theme proof, copy-visual alignment,
photo/identity evidence, composition, outfit/face continuity, text placement,
and doubt flags. If any slide is doubtful, mark the package REPAIR/BLOCKED and
fix it before generating. Do not generate "maybe okay" screens.

Carousel jam autopilot is mandatory when the creator wants to jam on one idea
or turn one idea into a post. Use `config/skills/carousel-jam-autopilot.md`.
Do not ask whether to run parallel agents; run the room automatically, keep the
creator in the loop for idea/copy/proof/final approval, and continue past
prompt-pack handoff into final image generation whenever the session has an
available image-generation path. A carousel is not "done" until native 4:5
slides, separate native 9:16 slides, visual QA, and final audit exist. If final
generation is unavailable, write the blocker inside the carousel package and
ask only for the missing input or approval.

### `/story` Command

When the user starts a message with `/story`, treat it as a creator command for
this C-layer pipeline:

```text
/story
title: optional title
slides: 4 or 5
<story text>
```

Use any attached pictures or supplied local image paths as references. Default
to 5 slides, allow only 4 or 5 slides, and follow the @a.storyof.two voice,
`config/carousel_style_contract.json`, the golden viral theme skill, and visual
memory from this folder. Before submitting or recommending any new carousel
idea, first read and use `wiki/themes/calm-enough-for-chaos.md` and
`output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md` as the
first-principles source for why the gold carousel worked. The golden theme is
mandatory: start from a universal relationship truth, then prove it with
Aachu/Zuv specifics. Photos, places, outfits, and objects are evidence, not the
premise. Use `--identity-image` or `identity_images/` for face/character
consistency. The expected result is a ready carousel package plus final
generated carousel slides. Do not treat local stylized previews as final
illustrations.

Before any carousel ideation, also read
`memory/semantic/carousel-idea-preferences.md`. This file is the persistent
creator preference ledger for recommended, rejected, packaged, and cooled-down
carousel ideas. Do not pitch a concept or emotional lane listed there as a fresh
idea unless the creator explicitly asks to revisit it. When the creator rejects,
accepts, or cools down a concept, update that ledger immediately with the
concept, lane, status, reason, and confidence score. Then update
`memory/working.md` only with a short pointer if the workflow changed.

For any new carousel concept, story repair, caption angle, article angle, or
creator jam where we are deciding what the love story *means*, run Layer E
first: `config/skills/romance-story-selling-engine.md`. Think like an author before thinking like a packager:
find the emotional obstacle, choose one concept-process card, prove the truth
through Aachu/Zuv behavior, score with the Story-Selling rubric, then write.
Layer E must not bypass the golden theme;
it supplies a stronger story lens before the mandatory golden-theme tournament.

After the memory, Layer E, and golden-theme gates are loaded, always load
`config/skills/carousel-story-director-persona.md` before writing hooks, slide
copy, captions, visual directions, prompts, or image-generation handoff text.
The persona persists until final native 4:5 and 9:16 image sets, visual QA,
and approval artifacts exist. It must block any direction that lacks a hook,
setup, proof, escalation, bridge, active Zuv role, earned ending, or
send/save reason.

Before finalizing any next carousel idea or theme, run the golden-theme variant
tournament: create 5-10 distinct concept options, score each on the 30-point
Golden Theme rubric, and let a final selector choose the highest-rated option.
Every option must be judged against the Calm Enough For Your Chaos theme file
and the full viral-theme analysis, not only against the current prompt. Do not
proceed to carousel packaging or image generation unless the selected concept
scores 28/30 or higher. If no option reaches the threshold, repair the top
candidates and rescore before choosing.

### Visual Debate Gate

After a 28/30+ Golden Theme winner is selected and the creator confirms the
final copy/copies, the flow must enter a mandatory Post-Copy Visual Creative
Room before image generation, visual plan finalization, prompt finalization, or
carousel packaging. Listen for creator confirmation language such as "copy is
final", "copies are closed", "perfect", "I like it", "go ahead", "proceed",
"approved", "now visuals", "make prompts", or "generate." When that happens,
lock the approved copy and write `post-copy-visual-room.json` before any final
visual handoff.

The Post-Copy Visual Creative Room uses:

- `agents/carousel-post-copy-visual-room-orchestrator.md`

It must run a Visual Format Anthropologist, Scene Evidence Director, Romance
Blocking Director, Typography And Aspect Director, Generation Prompt Director,
and Harsh Visual Selector. The room must compare three or more visual systems,
record rejected motifs, repair the winner, and return GO / REPAIR / STOP.
Any REPAIR or STOP blocks visual debate, prompt pack, and image generation.

After `post-copy-visual-room.json` returns GO, run three visual agents as a
short council and write `visual-debate.json`.

The required agents are:

- `agents/carousel-visual-evidence-planner.md` — finds photo-rooted,
  non-repetitive exterior/interior scene evidence and prevents prop-first
  thinking.
- `agents/carousel-romance-scene-planner.md` — turns the emotional machine into
  drawable romance scene beats with obstacle, reversal, and payoff.
- `agents/carousel-visual-continuity-judge.md` — debates the options, blocks
  repeated motifs and one-setting defaults, and returns GO / REPAIR / STOP.

The council must record three or more visual options, rejected visual patterns,
the selector verdict, the winner, and the final slide-by-slide visual plan. It
must preserve the selected post-copy visual system unless it records an explicit
repair. If the creator rejects a visual motif, do not repeat it across every
illustration; use it only as occasional evidence when the story truly needs it.
The Visual Debate Gate must be followed by `visual-plan-quality.json`, a
per-slide pre-generation screen review. Each slide must receive GO / REPAIR /
STOP for visual evidence, emotional proof, identity continuity, typography
safety, and aspect-specific composition. Any REPAIR or STOP slide blocks image
generation for the whole carousel until repaired and rescored.

### Creator Jam Response Contract

When the creator asks to "jam", "brainstorm", "ideate", "pick today's
carousel", "what should we do next", or otherwise discuss a next illustrated
carousel idea, treat it as C-layer creator ideation even if the message does
not literally start with `/story`.

Do not offer the generic visual companion, browser mockup, design-doc flow, or
Superpowers-style spec approval gate for this kind of creator jam. Those steps
interrupt the creative loop. The correct response shape is:

1. Acknowledge the jam in one short line.
2. Load `config/skills/carousel-jam-autopilot.md`.
3. Read/use the Calm Enough For Your Chaos theme, full viral-theme analysis,
   and `memory/semantic/carousel-idea-preferences.md`.
4. Exclude recently recommended, rejected, packaged, or cooled-down lanes from
   the tournament unless the creator explicitly asks to revisit them.
5. If there is no supplied moment, photo, or constraint, ask one practical
   context question at most.
6. Otherwise run the golden-theme variant tournament and parallel agent room:
   5-10 distinct options, cross-agent debate, repairs, 30-point scores,
   selector verdict, and GO / REPAIR / STOP decision.
7. Record the recommendation, rejection, acceptance, or cooldown in
   `memory/semantic/carousel-idea-preferences.md`.
8. After a 28/30+ winner is selected, package the carousel and continue through
   post-copy visual room, visual debate, visual-plan-quality, identity review,
   prompt pack, image generation, packaging, and visual QA.
9. If image generation is possible in the session, do not stop at
   `READY_FOR_CODEX_BUILTIN_GENERATION`; generate proof images, get creator
   proof approval when needed, then generate and package the full native 4:5
   and native 9:16 sets.

This contract intentionally overrides generic creative brainstorming habits for
carousel ideation. The product is the strongest creator-facing idea first, then
final packaged images after creator checkpoints, not a process explanation.

```bash
# Interactive mode, no external credentials required
venv/bin/python scripts/create_illustration_carousel.py

# One-liner mode, no external credentials required
venv/bin/python scripts/create_illustration_carousel.py \
  --story "I proposed to Anchal under the stars" \
  --image /path/to/photo-1.jpg \
  --image /path/to/photo-2.jpg

# Full brief
venv/bin/python scripts/create_illustration_carousel.py \
  --title "Anchal Under The Stars" \
  --story-file story.txt \
  --image /path/to/photo-1.jpg \
  --image /path/to/photo-2.jpg \
  --identity-image /path/to/aachu-zuv-reference.jpg \
  --slide-count 5 \
  --style-brief "soft hand-drawn desi storybook illustration"

# Prepare local Codex built-in image generation handoff files
venv/bin/python scripts/create_illustration_carousel.py \
  --title "Anchal Under The Stars" \
  --story-file story.txt \
  --image /path/to/photo-1.jpg \
  --identity-image /path/to/aachu-zuv-reference.jpg \
  --slide-count 5 \
  --generate-images

# Optional legacy API-backed agent run
venv/bin/python scripts/create_illustration_carousel.py \
  --mode anthropic \
  --story-file story.txt \
  --image /path/to/photo-1.jpg
```

### C-Layer Agents

| Agent | File | Role |
|---|---|---|
| C0 | agents/illustration-carousel-orchestrator.md | Master orchestrator; synthesizes C1-C6 |
| C0.25 | agents/carousel-story-director.md | Preloads the content-director persona; locks hook, story, bridge, ending, retention, and send/save spine before C1-C6 |
| C1 | agents/carousel-story-miner.md | Extracts human truth, facts, motifs, risks |
| C2 | agents/carousel-arc-builder.md | Builds the 4-5 slide narrative arc |
| C3 | agents/carousel-visual-director.md | Defines likeness, palette, motifs, continuity |
| C3A | agents/carousel-visual-evidence-planner.md | Runs the Visual Debate Gate evidence pass before image generation |
| C3B | agents/carousel-romance-scene-planner.md | Runs the Visual Debate Gate romance-scene pass before image generation |
| C3C | agents/carousel-visual-continuity-judge.md | Runs the Visual Debate Gate selector/judge pass before image generation |
| C3D | visual-plan-quality.json | Per-slide pre-generation screen; blocks generation on copy-visual drift, losing-option leakage, weak golden proof, or doubtful screens |
| C3.5 | agents/carousel-identity-consistency-reviewer.md | Blocks generation unless face structure, expressions, clothes, and cross-slide identity continuity are locked from the selected identity bundle |
| C4 | agents/carousel-prompt-engineer.md | Creates image-generation prompt pack |
| C5 | agents/carousel-copy-packager.md | Writes caption, alt text, hashtags, notes |
| C5.5 | agents/carousel-post-copy-visual-room-orchestrator.md | Mandatory creative visual room entered after creator confirms copy; compares visual systems before visual debate, prompts, or generation |
| C6 | agents/carousel-reviewer.md | Scores package before image generation |

### Visual Debate Gate

Before image generation, the C-layer must write `visual-debate.json` from the
three visual agents: C3A evidence planner, C3B romance scene planner, and C3C
continuity judge. If the creator has confirmed copy, the C-layer must first
write `post-copy-visual-room.json` from C5.5 and receive GO. The visual debate
gate decides whether the visuals prove the relationship truth or have drifted
into repeated props, one-setting defaults, or generic couple poses. Do not
package or generate final images until both gates record a GO / PASS decision.
This gate is per-slide, not package-only. The judge must block generation if
even one slide has unclear story evidence, weak golden-theme proof, generic
couple posing, risky text placement, uncertain identity continuity, or visual
motifs borrowed from a losing/risky visual option.

### C-Layer Skill Files

| Skill | File | Contents |
|---|---|---|
| carousel-story-director-persona | config/skills/carousel-story-director-persona.md | World-class content director persona for hook, story, bridge, ending, retention, and send/save checks before carousel writing/design |
| illustration-carousel-framework | config/skills/illustration-carousel-framework.md | Artifact contract, visual rules, story arcs, review rubric |
| carousel-jam-autopilot | config/skills/carousel-jam-autopilot.md | Automatic jam → parallel agents → creator checkpoints → final image generation workflow |
| golden-viral-carousel-theme | config/skills/golden-viral-carousel-theme.md | Mandatory universal-theme guardrail, caption formula, hard fails |
| golden viral theme reference | config/references/golden-viral-carousel-theme-reference.md | Detailed gold-theme anatomy, examples, repair playbook |

### C-Layer Output

Default output path:

```text
output/carousels/YYYY-MM-DD/<slug>/
```

Each package contains:

- `manifest.json` — run metadata and source images
- `concept.json` — title, human truth, emotional arc, story-director persona gate
- `post-copy-visual-room.json` — mandatory visual creative-room output after creator-confirmed copy, with visual system candidates, debate, selector verdict, typography/aspect plan, and generation brief
- `visual-debate.json` — three-agent visual council, rejected motifs, selector verdict, and final visual plan
- `visual-plan-quality.json` — per-slide pre-generation GO / REPAIR / STOP screen that blocks doubtful visuals
- `slides.json` — slide copy and visual plan
- `prompt-pack.json` — generation-ready image prompts
- `identity-consistency-review.json` — C3.5 pre-generation identity gate for face structure, expressions, clothing, and cross-slide consistency
- `copy.json` — caption, alt text, hashtags, posting notes
- `review.json` — scorecard and required fixes
- `storyboard.md` — readable slide flow
- `final-approval.md` — human review checklist
- `agent-reports.md` — raw C-layer agent outputs
- `final-images.json` — final generated image source mapping, with separate native provenance for 4:5 and 9:16 outputs
- `visual-qa.md` — storyboard, face, dress continuity, style, model-native text, and final-output checks
- `final/slide-XX.png` — native 4:5 Instagram post output, not derived from another aspect ratio
- `final-reels-stories/slide-XX.png` — native 9:16 Reels/Stories output, not derived from the Instagram post output
- `final-with-text/slide-XX.png` — legacy local text-overlay exports only

---

## Substack Love Article Pipeline (D-Layer) — New

Entry point for turning a carousel, podcast, or love-story package into a
Substack-ready article for the couple/love theme.

Default article stance: **love and couple dynamics first**. Do not turn
@a.storyof.two articles into tool/process teardowns unless explicitly asked.
Use the generated carousel images as emotional evidence and story anchors.

### `/article` Command

When the user asks to write, plan, draft, or publish a Substack article, treat
it as this D-layer workflow. If a carousel package is supplied or obvious, start
by creating a gated article package:

```bash
venv/bin/python scripts/create_substack_article_package.py \
  --carousel-dir output/carousels/YYYY-MM-DD/<slug> \
  --title "Working Article Title"
```

Then follow:

- `config/skills/romance-story-selling-engine.md` before choosing the article
  hook, thesis, proof beats, reversal, or payoff
- `config/skills/couple-substack-article-framework.md`
- `config/references/couple-substack-growth-reference.md`
- `config/voice.md`
- source carousel `concept.json`, `storyboard.md`, `slides.json`, `copy.json`

### D-Layer Output

Default output path:

```text
output/articles/YYYY-MM-DD/<slug>/
```

Each package contains:

- `source-manifest.json` — source carousel, image inventory, artifact contract
- `article-brief.md` — theme, audience, angle, emotional thesis
- `image-reference-review.md` — slide image placement, story job, alt text
- `title-growth-pack.md` — subject lines, preview text, slug, prompt, Notes
- `outline.md` — structure before drafting
- `draft.md` — working article
- `editorial-gates.md` — source, theme, image, structure, voice, growth, final checks
- `publish-package.md` — final Substack-ready article
- `notes-promo.md` — Substack Notes/social excerpts
- `final-approval.md` — human approval checklist

Do not present an article as final until `publish-package.md` exists and every
gate in `editorial-gates.md` is `PASS` or `PASS_WITH_NOTES`.

### D-Layer Gates

1. Source Integrity — carousel files and images reviewed.
2. Love Theme Fit — article stays on love/couple dynamics.
3. Image Reference Fit — images have placement, emotional job, and alt text.
4. Article Structure — strong hook, proof, turn, payoff.
5. Voice And Taste — warm, intimate, affectionate, not mean or generic.
6. Substack Growth Package — subject lines, preview, slug, comment prompt, Notes.
7. Final Publish Approval — clean publish package assembled.

---

## Memory Model (Rohit v2 LLM Wiki)

```
memory/working.md     Current analysis session. Reset on new full run.
memory/episodic/      Permanent per-run records. Never deleted.
memory/semantic/      Distilled facts about the channel with confidence scores (0.0–1.0).
memory/graph.json     Entities (posts, themes, hashtags) + relationships.
```

Persistent creator preferences that should survive future sessions live under
`memory/semantic/`. For carousel ideation, the required ledger is
`memory/semantic/carousel-idea-preferences.md`; read it before pitching ideas
and update it whenever the creator rejects, accepts, or cools down a lane.

Confidence lifecycle: new=0.4 → confirmed×2=0.7 → confirmed×3=0.9 → contradicted=↓ → stale=decay

### Wiki Health And Session Close

The wiki/memory layer is not healthy unless it can diagnose itself. At the end
of any substantial project session, run:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "short human-readable summary of what changed"
```

This writes:

- `output/diagnostics/wiki-health-YYYY-MM-DD.md` — current wiki/memory lint and
  drift report
- `memory/heal/proposals/YYYY-MM-DD-wiki-health.md` — HEAL proposal for failed
  or warning checks
- `memory/episodic/YYYY-MM-DD-session-health.md` — permanent session record
- `logs/YYYY-MM-DD-wiki-health.log` — compact machine-readable run log

The health gate checks that:

- advertised pipeline files in `AGENTS.md` / `CLAUDE.md` exist;
- `wiki/index.md` page counts are current;
- wiki pages carry `last_updated`, `confidence`, and `sources`;
- semantic memory files carry confidence scores;
- episodic memory and logs are being written.

If the script returns `NEEDS_HEAL`, do not pretend the wiki layer is current.
Either repair the failing checks immediately or leave the generated HEAL
proposal as the next-session starting point.

---

## Wiki Structure

```
wiki/
  index.md             Catalog of all compiled pages
  posts/               Notable individual post analyses
  themes/              Recurring content themes (travel, love, daily life...)
  people/              Anchal, Himanshu — voice, aesthetic, recurring motifs
  insights/            Distilled strategic insights about the channel
```

---

## Apify Integration

Primary scraper: `apify/instagram-profile-scraper`
Fallback scraper: `apify/instagram-scraper`

```python
# pipeline/sources/apify.py
APIFY_ACTORS = {
    "profile": "apify/instagram-profile-scraper",
    "posts":   "apify/instagram-scraper",
}
INSTAGRAM_HANDLE = "a.storyof.two"
```

The Apify MCP server is configured globally at `https://mcp.apify.com?token=...`
and can be called directly from Claude Code sessions.

---

---

## Pre-Post Pipeline (B-Layer) — New

Entry point for analyzing videos **before they are posted**.

B-layer also uses Layer E before hook, edit, caption, cultural, algorithm, and
orchestrator judgment whenever the planned Reel is a love/couple story. The
pre-post agents should think like an author before thinking like a retention
machine: name the romantic obstacle, proof beat, reversal, and payoff, then
score whether the Reel can sell the story online.

```bash
# Interactive mode
python scripts/analyze_prepost.py

# One-liner mode
python scripts/analyze_prepost.py --concept "Anchal tries wazwan for the first time"

# Full brief
python scripts/analyze_prepost.py \
  --concept "..." \
  --hook "Opens on Anchal holding a suitcase" \
  --caption "me threatening to leave (again)" \
  --audio "trending Hinglish beat" \
  --cover "Anchal deadpan face with suitcase"
```

### B-Layer Agents

| Agent | File | Role | Max Score |
|---|---|---|---|
| B0 | agents/prepost-orchestrator.md | Master orchestrator; runs B1–B5 and synthesizes | — |
| B1 | agents/hook-analyzer.md | Hook strength, type, killers, rewrites | 10 |
| B2 | agents/edit-auditor.md | Retention architecture, loop design, audio | 35 |
| B3 | agents/algorithm-scorer.md | DM sends, saves, skip risk, distribution prediction | 70 |
| B4 | agents/caption-advisor.md | Voice 1/2, keywords, CTA, caption rewrites | 35 |
| B5 | agents/cultural-resonance.md | Theme match, Indian authenticity, Kashmiri signal | 50 |

**Total composite score: 200 points**

### B-Layer Skill Files

| Skill | File | Contents |
|---|---|---|
| instagram-algorithm-2026 | config/skills/instagram-algorithm-2026.md | 2026 algorithm signals, audition system, scoring reference |
| hook-and-edit-framework | config/skills/hook-and-edit-framework.md | Hook taxonomy, MrBeast principles, retention editing, loop mechanics |
| indian-creator-intelligence | config/skills/indian-creator-intelligence.md | Indian couple creator landscape, Hinglish patterns, Kashmiri niche |

### Verdict Tiers

| Score | Verdict | Action |
|---|---|---|
| 160–200 | POST | High-confidence. Minor optimizations then post. |
| 120–159 | REVISE | Fix 2–3 highest-impact gaps first. |
| 80–119 | REWORK | Significant structural issues. At minimum fix hook + algo gaps. |
| 0–79 | KILL | Rebuild from scratch. |

### Hard Override Rules (regardless of composite score)
- Hook score < 5 → Automatic REWORK
- DM Send Potential < 10/25 → Automatic REVISE minimum
- Cultural Authenticity < 5/10 → Automatic REVISE minimum
- Audio plan missing → Subtract 10 from composite before applying tier

---

## Lint Rules
- Wiki pages must have: last_updated, confidence (0–1), sources[]
- memory/semantic/ facts must carry confidence score
- Never commit .env
- corpus/raw/ is ephemeral — always re-parseable from Apify
