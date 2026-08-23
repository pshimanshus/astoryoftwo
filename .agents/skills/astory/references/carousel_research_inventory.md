# ASOT Carousel Research Inventory

What real, repo-local evidence the ASOT carousel craft layer is built from.
Discovered by filesystem search on 2026-07-01. Corpus status: **FOUND** (not
`CAROUSEL_RESEARCH_CORPUS_NOT_FOUND`).

> Discipline: the pasted chat summary is **not** treated as canonical. Every
> carousel mechanic that becomes canonical must cite a repo path below. Where the
> pasted summary goes beyond what the repo proves, it is quarantined in
> `asot_carousel_mechanics.md` → "Needs source confirmation."

## Searches performed (Phase 2)

- `rg -l -i` across the repo for: `carousel`, `slide 2`/`slide two`, `hook`,
  `swipe`, `swipe reason`, `screenshot`, `save-worthy`/`saveable`, `caption`,
  `CTA`, `second post`, `brand asset`, `brand dna`, `first frame`, `payoff`,
  `retention`, `send/save/comment trigger`, format-family names.
- `find runs -type f` for existing carousel-craft artifacts
  (`format_decision*`, `carousel_architecture*`, `slide2_proof*`,
  `save_worthy*`, `carousel_craft*`, `caption_second_post*`) → **none exist yet**
  (this layer is new). Existing upstream artifacts DO exist widely:
  `slide_count_decision.md`, `slide_beat_map.json`, `scene_landing_preview.md`,
  `winner_landing_comparison.md`, `novelty_candidate_ledger.json`.
- Inspected roots: `references/text-style/` (+ `winner-bank/`, `content-dump/`),
  `references/craft/`, `references/brain/pages|reports/`,
  `data/instagram/carousel_posts/`, `.agents/skills/astory/{references,templates,personas}/`.

## Existing coverage (do not duplicate; extend)

- **Story Room already decides slide architecture.** `SKILL.md` + the Story Room
  packet (`templates/agents/story_room_agent_prompt.md`) + personas
  (`story-director`, `pacing-editor`, `swipe-retention-critic`) already produce
  `slide_count_decision.md`, `slide_beat_map.json`, a tension ladder, and a
  retention pass. The new layer adds an **upstream `format_decision.md` gate** and
  **carousel-specific craft checks**, and feeds the Story Room — it does not
  replace it.
- **SKILL.md already contains a "Carousel Wrapper Formula"** and a scene-landing
  preview gate. The new layer makes those source-backed and gate-enforced.
- **Slide-count is not the same as carousel craft.** The gap this layer fills:
  format decision (hero vs carousel), slide-2 hook-proof, screenshot survival,
  the save-worthy slide, and caption-as-second-post.

## Sources

| Path | Type | ASOT-own / external / compiled | Confidence | Why relevant | Contains | Should influence |
| --- | --- | --- | --- | --- | --- | --- |
| `references/text-style/instagram-winner-mechanics-2026-06-14.md` | MD, distilled | external winner-bank + own | **high** | THE carousel-craft doc: 20 winning mechanics + **Carousel Wrapper Formula** (slide1 hook→slide2 first receipt→slide3 second receipt→slide4 unsaid obvious→slide5 payoff→opt 6-8) + **Static/Reel Wrapper** ("if it needs an explanation, it wants to be a carousel") + **Slop Trap Checklist**. Format mix among winners: 115 carousels / 40 static / 15 reels; caption median 39 words. Case study DZNl2zxiRD4 (1.19M views, 14,094 shares, 10,913 saves, 6 slides). | structure, hooks, slide-2, save/share/comment, caption, visual, metrics | format · hook · slide2 · sequence · save-worthy · caption · CTA · brand DNA |
| `references/craft/story-craft.md` | MD, derived craft (ASOT voice) | compiled (own) | **high** | "Two shapes": single illustration vs multi (2–10); **the swipe is the engine**; slide1=hook, middle=escalating fresh receipts (no repeats), final=turn home; length chosen by count of *true receipts*; hook craft; visual storytelling; **anti-templating guardrail** ("if you can describe it as 'the X format,' you're templating"). | structure, hooks, slide sequence, visual | format · hook · sequence · visual direction |
| `.agents/skills/astory/references/source_backed_winner_patterns.md` | MD, extracted | own + external | **high** | 10 cited winner patterns; Pattern 1 escalation (carousel), Pattern 3 saves engine, Pattern 8 receipt, Pattern 9 send/save split, Pattern 10 anti-patterns. | structure, hooks, save/send, payoff, metrics | format · hook · sequence · save-worthy · CTA |
| `.agents/skills/astory/references/taste_benchmark.md` | MD | own + external | **high** | Winner-mechanics library (first-frame stop / swipe reason / payoff / send-save-comment triggers); Level ladder. | hook · slide2 · save-worthy · caption |
| `references/brain/pages/outcome-attribution.md` | MD (brain) | ASOT-own (hard metrics) | **high** | Own carousels ranked by **shares/1k + saves, not likes**; winners 25–40 shares/1k (DYJpjt9CQYY 40.15, DY_t4Dek0pq saves 16.99/1k); slide counts. | save/share mechanics, metrics | format · save-worthy · CTA |
| `data/instagram/carousel_posts/<shortcode>/carousel_export.json` (12) | JSON | ASOT-own | **high** | Verbatim per-slide text + per-post insights (reach/shares/saves/likes/comments), child_count. | structure, slide sequence, metrics | sequence · slide2 · save-worthy |
| `references/craft/taste-corpus.json` | JSON, 87 cards | ASOT-own | **high** | Own posts read as stories: `on_image_copy`, `engine`, `send_job`, `verdict`, `metrics`; 18 illustrated-story soul lane. | structure, hooks, save/send, caption | format · hook · sequence · save-worthy · caption |
| `references/text-style/illusion-of-novelty-storytelling-2026-06-18.md` | MD | compiled | **med-high** | Novelty model: old feeling / new reveal / viewer outcome / contrast / urgency / bullseye / what-not-to-explain. | hook, slide1, payoff | hook · slide1 · brand DNA |
| `references/text-style/winner-bank-index-2026-06-14.json` + `winner-bank/` | JSON, 170 ranked | external | **high** (structure) / med (saves are proxies) | rank, format, slide_count, mechanic_tags, remix_mode. | structure, format mix, mechanics | format · sequence |
| `references/text-style/permissioned-winner-remix-workflow-2026-06-14.md` | MD | compiled | **med** | How to preserve a source winner's copy/premise/slide structure + add the ASOT wrapper. | structure, caption | format · sequence · caption |
| `references/craft/craft-brain.md`, `taste-library.md` | MD | compiled theory | **med** | Craft theory (support, not winner evidence). | structure, visual | visual direction · sequence |
| `.agents/skills/astory/templates/planning/{slide_count_decision.md,slide_beat_map.json,scene_landing_preview.md,winner_landing_comparison.md,novelty_candidate_ledger.json}` + `runs/*/planning/*` | templates + worked examples | own | **med-high** | The existing slide-architecture artifacts + real filled examples. | structure, sequence | format · sequence |
| `.agents/skills/astory/references/creative_taste_bible.md`, `visual_direction_bible.md`, `copy_voice_bible.md` | MD | own | **high** | Core "same people, same world, new moment" (brand-asset/world), single-hero default, visual-proof, copy voice. | brand DNA, format, visual, caption | format · visual · caption · brand DNA |

## Evidence gaps (not papered over)

- The pasted-summary phrasings **"every slide survives as a screenshot," "caption
  is the second post," "carousel is a brand asset,"** and the ASOT **format-family
  names** (tiny love proof / Hinglish contradiction / relationship receipt deck /
  couple ritual montage / soft micro-essay) are **operational syntheses** — the
  repo backs the underlying *mechanics* (save/screenshot/message-native behavior,
  caption structure, page-identity, the named engines), but not those exact
  formulations as measured findings. They are marked accordingly in
  `asot_carousel_mechanics.md` and quarantined in its "Needs source confirmation"
  section where they exceed the evidence.
- External winner **saves/shares are proxies** (not public); rank by ASOT-own
  shares/1k first.
- No live web/Instagram research this pass (repo-first; connectors not required).
