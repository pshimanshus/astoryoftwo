# Couple Substack Article Framework

## Purpose

Use this before planning, drafting, reviewing, or publishing any Substack-style
article for @a.storyof.two, especially when the article is based on a carousel
or illustrated love-story package.

The article is not a tool/process teardown unless the user explicitly asks for
that. Default to love, marriage, couple dynamics, emotional safety, memories,
and the Aachu/Zuv rhythm.

Read the growth reference before drafting:

`config/references/couple-substack-growth-reference.md`

Also read:

- `config/voice.md`
- `config/skills/golden-viral-carousel-theme.md`
- `config/skills/romance-story-selling-engine.md`
- `config/references/story-selling-canon/concept-process-cards.md`
- `config/references/story-selling-canon/rubric.md`
- `config/references/story-selling-canon/story-selling-online.md`
- source carousel `concept.json`, `storyboard.md`, `slides.json`, and `copy.json`

## Output Contract

Default output path:

```text
output/articles/YYYY-MM-DD/<slug>/
```

Create the package with:

```bash
venv/bin/python scripts/create_substack_article_package.py \
  --carousel-dir output/carousels/YYYY-MM-DD/<slug> \
  --title "Working Article Title"
```

Every article package must contain:

- `source-manifest.json` - source carousel, image inventory, artifact list
- `article-brief.md` - theme, audience, angle, emotional thesis
- `image-reference-review.md` - image inventory, placement, alt text checks
- `title-growth-pack.md` - subject lines, preview text, slug, comment prompt, Notes promo
- `outline.md` - article structure before drafting
- `draft.md` - working article
- `editorial-gates.md` - gate status and required fixes
- `publish-package.md` - final clean Substack-ready article
- `notes-promo.md` - Substack Notes/social excerpts
- `final-approval.md` - human approval checklist

Do not give the final article as complete until `publish-package.md` exists and
every gate is `PASS` or `PASS_WITH_NOTES`.

## Article Shape

Use this default structure for love/couple essays:

1. **Hook:** one line that feels like a relationship truth, not a topic label.
2. **Recognition:** name the familiar couple feeling in plain language.
3. **Specific proof:** use carousel scenes and images as evidence.
4. **Deeper turn:** explain what the funny detail reveals about love.
5. **Couple rhythm:** show what she brings and what he brings.
6. **Payoff:** land on a line worth saving, sending, or commenting on.

For carousel-based articles, place images intentionally:

- Hero: the strongest first-slide or thesis image.
- Middle: 2-3 scene-proof images after the relevant section.
- Ending: the final emotional-payoff image.

Images must carry emotional evidence, not decoration. Every image needs alt
text and a reason for placement.

## Gates

### Gate 1 - Source Integrity

Pass only if the carousel folder exists, source JSON/Markdown files were read,
and generated slide images were discovered or explicitly supplied.

### Gate 2 - Love Theme Fit

Pass only if the article is about love/couple dynamics. Reject drafts that drift
into "how this content was made" unless the user explicitly requested craft
analysis.

### Gate 3 - Image Reference Fit

Pass only if image placement is planned, every image has a story job, and alt
text exists.

### Gate 4 - Article Structure

Pass only if the article has an inbox-strong opening, section rhythm, concrete
scenes, and a save/share-worthy close.

### Gate 5 - Voice And Taste

Pass only if the draft matches @a.storyof.two: warm, intimate, emotionally
honest, affectionate, and never mean.

### Gate 6 - Substack Growth Package

Pass only if the package includes subject lines, preview text, slug, reader
prompt, and Notes/social promo.

### Gate 7 - Final Publish Approval

Pass only after `publish-package.md` is assembled and limitations are stated.

### Gate 8 - Story Selling Fit

Pass only if `romance-story-selling-engine` was used before drafting, one
concept-process card shaped the hook/proof/reversal/payoff, the angle would
score 28/30 or higher on the Story-Selling rubric when Layer E is invoked, and
no copyrighted source text is copied into the article.

## Hard Fails

Rewrite before final if:

- The article explains the carousel instead of telling a love story.
- The article makes Anchal/Aachu sound like a burden.
- Himanshu/Zuv is reduced to a passive saint.
- Images are dumped into the article without narrative purpose.
- The title is poetic but unclear in an inbox.
- There is no reader prompt or shareable final line.
- Layer E was invoked but no Story-Selling score, process card, or source-safety
  check is recorded.
