---
name: a-story-carousel-jam
description: Jam, choose, draft, direct, generate, or package an @a.storyof.two post, Reel, or carousel. Use for fresh ideas, copy, visual planning, image proofs, and final carousel work; do not use for article-only, prepost-only, or wiki-health requests.
---

# A Story Carousel Jam

Compact router for the `carousel_jam` system in `config/skill-systems.json`.
Use `config/skills/carousel-jam-runtime-context.md`,
`config/skills/carousel-jam-autopilot.md`, and, after concept lock,
`.agents/skills/a-story-direct-visual-story/SKILL.md` only when their exact
detail is needed.

## Hot Path

When the creator asks to jam from scratch, invent a fresh route. Start with the
strongest human draft; use memory and rules as quiet seasoning. Each slide needs
one sentence describing a visible physical event. If a premise misses
semantically, allow at most two total semantic attempts, then replace it.

Four gates only: concept lock; copy + format lock; proof QA + creator approval;
final package QA. Do not generate the remaining deck before proof QA and creator
approval. Prefer the one-command workflow; if automation is missing, name the
missing link.

A request for a final draft after concept approval enters the copy part of
Gate 2, including in chat-only work. Apply the storytelling hook's final-draft
review before delivery: preserve the selected architecture and approved
premise, and check the actual middle, turn, and payoff. A shorter restatement
of the pitch is not automatically a completed story. Keep this review private;
it adds no artifact, numerical score, or creator approval step.

Default post/carousel output is `1080x1440`. Generate `1080x1920` or `1080x1080`
only by explicit request. Put exact approved text in-image and the tiny
`@a.storyof.two` top-right signature.

## Generation Boundary

Use actual Aachu/Zuv identity images for face, hair, height, proportions,
posture, expression, and wardrobe. Text-only identity descriptions are blocked.
No identity eval means no next slide.

For new packages, attach exactly five files: the four actual files from
`identity-dossier.json.selected_generation_bundle` plus the active
`contact-sheet.png` style board. This is not a claim about a published platform
limit. If the runtime rejects the bound files, remain `handoff_ready` and report
`BLOCKED/NOT_RUN`.

Codex directly invokes ImageGen: read the compiled prompt, attach the files, call image generation,
inspect decoded pixels with `view_image`, and submit hash/dimension-bound QA.
Repository commands prepare, ingest, bind review, record approval, and promote.

## Feedback And Helpers

When the creator gives feedback, save exact words with `scripts/carousel.py
feedback`, repair the same package, and inspect `feedback-status` before saying
it is resolved.

Use helper agents only when the creator explicitly asks for parallel work or a
bounded independent audit is necessary. Do not create standing agent-room,
numeric score, provenance graph, run-ledger, or stage-review artifacts. Do not
create separate ledgers.

## Public States

`draft`, `blocked`, `handoff_ready`, `proof_qa_required`, `proof_failed`,
`awaiting_creator_proof_approval`, `batch_ready`, `final_qa_required`,
`final_qa_failed`, `publish_ready`.

## Commands

```bash
make jam MOMENT="one specific couple moment"
make carousel STORY="source story" CREATIVE_BRIEF="locked-brief.json" TITLE="optional title"
python scripts/carousel.py status output/carousels/YYYY-MM-DD/slug
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=pre
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=post
```
