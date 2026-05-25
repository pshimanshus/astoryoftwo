# Chaotic Wife Calm Husband Carousel Design

## Status

Approved by user on 2026-05-09.

## Goal

Create a carousel-generation setup for @a.storyof.two that turns the channel's
core dynamic, "Chaotic Wife, Calm Husband," into warm illustrated Instagram
carousels that look like Anchal and Himanshu while borrowing the minimalist
Product Unshipped illustration aesthetic.

## Channel Understanding

@a.storyof.two is Anchal's warm, funny, emotionally specific love diary. The
page is not a generic couple page, travel page, or wedding aesthetic page. Its
strongest identity is the contrast between Anchal's expressive, chaotic, loving
energy and Himanshu's calm, smiling, grounded presence.

The carousel system must not create generic quote cards. A successful carousel
should feel like a tiny illustrated love story: funny in the first swipe,
emotionally true by the end, and visibly rooted in the real Aachu and Zuv.

## Core Theme

**Chaotic Wife, Calm Husband**

The recurring emotional thesis:

> She brings drama, feeling, hunger, overthinking, and comedy. He brings calm,
> snacks, patience, and the kind of love that does not make her feel too much.

## First Carousel

Title: **He Didn't Marry Peace**

Slide flow:

1. He didn't marry peace.
2. He married "mujhe kuch nahi hua" while clearly crying.
3. He married "I'm leaving" with no shoes on.
4. He married 10 moods before breakfast.
5. And somehow, he still smiles like this is normal.
6. Maybe love is not finding calm.
7. Maybe it's finding someone calm enough for your chaos.

## Visual Direction

Borrow from Product Unshipped:

- soft hand-drawn flat vector illustration
- imperfect black outlines
- slightly uneven strokes
- childlike simplicity with adult emotional meaning
- minimal composition
- large whitespace
- muted warm colors
- one clear emotional idea per slide
- tiny low-contrast handwritten brandmark

Adapt for A Story of Two:

- warmer, more romantic, more desi
- recurring illustrated versions of Anchal and Himanshu
- garden, marigold, jasmine, mehendi, terracotta, fairy-light motifs
- Kashmiri/newlywed details when relevant
- brandmark should be `@a.storyof.two`

Avoid:

- generic Indian couple stock characters
- Canva quote cards
- corporate/startup illustration
- photorealism
- glossy 3D AI look
- overly detailed faces
- complex backgrounds
- too many props in one slide
- moralizing self-help language
- captions that explain the joke too much

## Character Reference Rules

All human figures should be based on the provided reference photos unless a
specific carousel concept says otherwise.

Anchal / Aachu:

- expressive, playful, warm smile
- soft curls and bridal styling
- pink, coral, orange, and red lehenga energy
- jewelry, mehendi, jasmine, and bridal detail cues
- dramatic body language, but affectionate rather than harsh

Himanshu / Zuv:

- calm, warm smile
- dark wavy hair
- ivory sherwani with soft pastel embroidery
- taller, grounded posture
- patient-husband energy

Together:

- she is the spark
- he is the steady flame
- the relationship should read as tender underneath the comedy

## Carousel Artifact Contract

Each generated carousel package should contain:

- `manifest.json`: date, slug, theme, status, input references
- `concept.json`: carousel title, human truth, emotional arc, slide summaries
- `slides.json`: ordered slide copy, visual prompt, notes, and CTA intent
- `prompt-pack.json`: image-generation prompts and shared negative prompt
- `copy.json`: Instagram caption, alt text, hashtags, and posting notes
- `review.json`: scorecard output before approval
- `final-approval.md`: human review checklist

## Review Criteria

Score each carousel from 0 to 5 on:

- theme alignment
- Anchal/Himanshu character likeness
- visual simplicity
- emotional payoff
- Hinglish voice fit
- first-slide hook strength
- slide-to-slide story flow
- absence of generic couple content

Pass threshold: 32 out of 40, with no zero in theme alignment, character
likeness, or generic-content absence.

## CLI Shape

The setup should eventually support:

```bash
python scripts/create_carousel.py --theme chaotic-wife-calm-husband
python scripts/create_carousel.py --title "He Didn't Marry Peace"
python scripts/create_carousel.py --idea "wife threatens to leave but asks if he ate"
```

Default output path:

```text
output/carousels/YYYY-MM-DD/<slug>/
```

## Open Constraints

This workspace is not currently a Git repository, so the design cannot be
committed from here. The implementation should still keep all generated specs,
plans, and artifacts in the local project tree.
