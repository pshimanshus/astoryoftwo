# A Story of Two Research Source Inventory

What real, repo-local evidence the taste benchmark is built from. Discovered by
filesystem search on 2026-06-30. Used to replace the prior synthetic
charger/pillow/hoodie/umbrella benchmark with source-backed patterns.

> Honesty note on signal quality: A Story's **own** carousels have real
> reach/share/save metrics, but several taste-corpus reads are caption-only and
> interpretive (lower confidence). The **external** winner bank has likes/comments
> only — saves/shares are not public, so those are proxies. Each source below is
> tagged with its evidence strength.

## 1. Winner bank / source-winning posts (external, for permissioned remix)

| Path | Type | Why relevant | Contains | Permission | Use for |
| --- | --- | --- | --- | --- | --- |
| `references/text-style/winner-bank/winner_bank.json` | JSON, 170 records | Full local scrape of selected external winners | exact caption, mechanicTags, likes/comments, winnerScore, commentSend/Tag proxies | permissioned_source_preserve_then_astory_wrapper | copy + carousel structure (mechanics) |
| `references/text-style/winner-bank-index-2026-06-14.json` | JSON, 170 ranked | Clean ranked index | rank, account, format, slide_count, mechanic_tags, caption_preview, remix_mode/notes | same | shortlist + structure |
| `references/text-style/winner-bank/posts_merged.json` | JSON, 715 | Full merged scrape (superset) | same fields | research only | mining new mechanics |
| `references/text-style/winner-bank/winner_contact_sheet.jpg` | image | visual contact sheet | thumbnails | research only | visual scan |
| `references/text-style/instagram-winner-mechanics-2026-06-14.md` | MD | **Distilled 20 winning mechanics + carousel wrapper formula + slop-trap checklist** | mechanics → A Story wrappers | n/a | copy + visual + structure |
| `references/text-style/illusion-of-novelty-storytelling-2026-06-18.md` | MD | novelty model (old feeling, new angle) | hook/novelty diagnostics | n/a | concept/hook framing |
| `references/text-style/permissioned-winner-remix-workflow-2026-06-14.md` | MD | how to remix a permissioned winner | workflow | n/a | remix discipline |
| `references/text-style/astory-wrapper-seed-bank-2026-06-14.md` | MD | seed wrappers | seeds | n/a | idea seeds (caution: not winners) |

Evidence note: external metric signal = likes/comments/winnerScore + comment-to-like
ratio + tag/send proxies. Saves/shares are **not** public for these.

## 2. Performance and outcome attribution (A Story's OWN posts — hard metrics)

| Path | Type | Why relevant | Contains | Use for |
| --- | --- | --- | --- | --- |
| `references/brain/pages/outcome-attribution.md` | MD (brain page) | Canonical win/flop ranking | shares/1k, saves/1k, follows/1k, reach for own carousels | engagement scoring truth |
| `references/brain/reports/outcome_attribution.json` | JSON (derived) | machine outcome report | winners/flops/ranking/thresholds | scoring |
| `data/instagram/account_inventory.json` | JSON | account post inventory + metrics | reach/shares/saved per post | metric source for taste-corpus |

Ranking rule (from these): **shares/1k reach and save behavior, not likes.** Own
winners ≈ 25–40 shares/1k; flops ≈ 4–6 shares/1k.

## 3. Carousel exports (A Story's OWN slides + insights)

| Path | Type | Contains | Use for |
| --- | --- | --- | --- |
| `data/instagram/carousel_posts/<shortcode>/carousel_export.json` (12 posts) | JSON | account, children (slides), caption, comments, **insights** (reach/shares/saves/likes/comments), child_count | verbatim structure + real per-post engagement |

Present shortcodes: DYJpjt9CQYY, DZNl2zxiRD4, DY4tGrQCXRA, DZSfrNaCS4Y,
DYaCIwAiYX9, DZjf5OxCR4Z, DY_t4Dek0pq, DY9SfANiXWc, DYoEl5jicte, DZINgGKCU94,
DYxCm58CaOM (weak), DYkEsrfiRRw (anti).

## 4. Engagement evals and run reports (per-run idea scores)

| Path | Type | Note |
| --- | --- | --- |
| `runs/*/evals/idea_engagement_eval.json` / `idea_engagement_report.md` (~15 runs) | JSON/MD | per-run idea-room engagement *scores* — predictive, not outcomes |
| `runs/2026-06-18_21-21_winner-bank-brainstorm/planning/source_winner_remix_contract.json`, `.../winner_landing_comparison.md` | JSON/MD | real source-winner remix worked example |
| `runs/2026-06-19_21-09_ghar-line/planning/{source_winner_remix_contract,source_winner_novelty_model,winner_landing_comparison}` + `evals/source_winner_alignment_eval.json` | JSON/MD | full source-winner remix run |
| `runs/2026-06-15_23-25_silence-house-walks/evals/{source_winner_alignment_eval,final_winner_landing_check}.json` | JSON | alignment/landing checks |

## 5. Brain lessons (cited, durable)

| Path | Note |
| --- | --- |
| `references/brain/pages/run-lessons.md` | visual-text logic, evil-eye continuity, creative-failure postmortem, taste-layer install |
| `references/brain/pages/prompt-patterns.md` | prompt-pack rules |
| `references/brain/pages/characters/{aachu,zuv,together}.md` | identity anchors |

## 6. Visual / style / identity references

| Path | Note |
| --- | --- |
| `references/style/best-illustration/` | canonical watercolor-and-ink style lock |
| `references/identity/{aachu,zuv,together}/` | raw face anchors |
| `references/failures/visual-inconsistencies/` | named visual failure modes |

## 7. Other compiled research (A Story's own craft brain)

| Path | Type | Note |
| --- | --- | --- |
| `references/craft/taste-corpus.json` | JSON, 87 cards | **Primary A Story-specific source**: own posts read as stories — `on_image_copy`, `engine`, `unsaid_feeling`, `craft_move`, `send_job`, `verdict`, `metrics`. 18 are the illustrated-story (soul) lane. Hard fields (caption/metrics) are real; interpretive fields are authored reads. |
| `references/craft/craft-brain.md`, `story-craft.md`, `taste-library.md` | MD | craft theory (use as support, not as winner evidence) |

## Evidence gaps (do not paper over)

- External winner saves/shares are not public → proxies only.
- Several own taste-corpus cards are `caption-only` / interpretive reads → lower
  confidence than `verbatim_slides_read_2026-06-24` cards.
- Some verbatim cards have unread slides (`[slide N not yet read]`).
- `references/viral-research.md` (root) does **not** exist; the real one is
  `.agents/skills/anti-ai-slop-human-copy-filter/references/viral-research.md`.

Corpus status: **FOUND** (not `WINNING_RESEARCH_CORPUS_NOT_FOUND`). Patterns are
extracted into `source_backed_winner_patterns.md`.
