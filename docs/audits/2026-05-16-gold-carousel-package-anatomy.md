# Gold Carousel Package Anatomy

date: 2026-05-16
package: output/carousels/2026-05-09/he-didnt-marry-peace
purpose: understand why this package produced the strongest illustrations so far

## Core Correction

This package is not good because it says `he married` repeatedly. That wording
is incidental to this specific story.

The package is good because it gives the image generator a complete creative
map:

- who the characters are;
- what each person visually represents;
- what emotional job each slide performs;
- what one scene should be drawn on each slide;
- what objects and motifs should repeat;
- how the joke becomes tenderness;
- where the final output files should appear.

Future carousels should reuse this information architecture, not the literal
phrasing.

## Folder Structure

```text
he-didnt-marry-peace/
  concept.json
  copy.json
  final-approval.md
  image-generation.json
  manifest.json
  preview.md
  prompt-pack.json
  review.json
  slide-01.png
  slide-02.png
  slide-03.png
  slide-04.png
  slide-05.png
  slide-06.png
  slide-07.png
  slides.json
  source-generated/
    slide-01.png
    slide-02.png
    slide-03.png
    slide-04.png
    slide-05.png
    slide-06.png
    slide-07.png
  storyboard.md
```

The important structural choice is that the final carousel assets sit at the
root as `slide-XX.png`. Supporting files explain them, but do not bury them.

## `manifest.json`

The manifest is a light package index, not a creative essay.

What it does well:

- declares the title, channel, theme, status, and 4:5 Instagram format;
- fixes the slide count at 7;
- lists reference photos with specific roles;
- keeps the artifact map small.

The reference image roles are especially important:

- primary couple likeness and outfit reference;
- full-body pose, height contrast, garden, terracotta reference;
- seated couple pose, marigold and jasmine mood reference;
- Himanshu solo likeness and calm posture reference;
- Anchal solo likeness, outfit, jewelry, and bridal detail reference.

This tells the model what to extract from each reference. It is stronger than
only saying "use this for identity."

## `concept.json`

This is the creative operating system.

Important parts:

- `human_truth`: love lets the dramatic person stay fully themselves;
- `emotional_arc`: punchy joke -> specific chaos -> calm anchor -> soft truth;
- `visual_meaning`: Anchal is bright/expressive, Himanshu is steady/amused;
- `main_visual_metaphor`: spark beside a steady flame;
- character bible: wardrobe, hair, posture, jewelry, gesture, emotional role;
- `avoid`: anti-style and anti-tone constraints.

Why it works:

The file gives emotional and visual direction together. It does not separate
story from image. The model gets a consistent character system before it sees
individual slide prompts.

## `slides.json`

This file maps story to retention.

Each slide has five useful fields:

- `copy`: the exact slide line;
- `role`: the narrative job;
- `visual`: the image to draw;
- `emotion`: what the viewer should feel;
- `cta_intent`: why the slide earns the next swipe.

This is the real structure to reuse. The text can be completely different, but
each slide still needs a role, visual, emotion, and retention reason.

## `prompt-pack.json`

The prompt pack is strong because it speaks like an art-director brief.

Shared prompt:

- defines the illustration style;
- names likeness requirements;
- gives Anchal and Himanshu specific visual traits;
- names whitespace, paper background, line quality, muted palette;
- keeps brandmark and text rules simple.

Per-slide prompts:

- identify the slide number and canvas size;
- name the primary request;
- specify scene/backdrop;
- describe subject action and emotional posture;
- define composition/framing;
- give exact text;
- include brandmark;
- end with tight constraints.

The prompts do not carry large pipeline contracts. They are visual and compact.

## `copy.json`

The caption is short and native:

```text
he didn't marry peace. he married me.

and somehow, that became the love story.

which one are you: chaos or calm?
```

The caption does not over-explain the carousel. It gives viewers a way to
identify themselves and comment or send it.

The alt text is also useful because it paraphrases every slide visually. This
is a good secondary check: if the alt text is boring or vague, the slide brief
probably is too.

## `review.json`

The review gate measures creative success:

- theme alignment;
- character likeness prompting;
- visual simplicity;
- emotional payoff;
- Hinglish voice fit;
- first-slide hook strength;
- slide-to-slide story flow;
- absence of generic couple content.

The required changes are practical generation warnings:

- keep faces simple and stylized;
- keep slide 4 sparse;
- keep the final line readable.

This is much better than abstract audit checks because it protects the final
image quality.

## `final-approval.md`

This is a human creator checklist.

Before generation, it asks:

- does the slide copy feel like Aachu and Zuv?
- are the jokes affectionate?
- is the final emotional line true?
- are likeness rules acceptable?

After generation, it asks:

- do both faces feel inspired by references?
- does the deck avoid generic quote-card energy?
- is text readable on mobile?
- is slide 1 funny within one second?
- is slide 7 save/share-worthy?
- is the deck uncluttered?

This file is small but important. It checks taste.

## `storyboard.md`

The storyboard is the fastest approval view. It strips each slide down to:

- slide number;
- exact line;
- visual description.

This is useful because a human can quickly feel the rhythm without parsing
JSON. If the storyboard does not feel alive, the image prompts will not save it.

## `image-generation.json`

This is provenance for the output:

- status is generated;
- mode is Codex built-in image generation;
- source directory points to generated raw assets;
- workspace outputs list the root slide files;
- normalized size is `1080x1350`;
- raw copies are under `source-generated/`.

The strongest thing here is the separation between raw generation and final
normalized assets.

## `preview.md`

The preview file makes the folder creator-friendly. It shows:

```md
![Slide 1](slide-01.png)
...
![Slide 7](slide-07.png)
```

This is not decorative. It makes review friction low.

## Root Slides

The root slides are normalized `1080x1350` PNG files. This matters because the
folder immediately contains the actual deliverable, not just instructions.

The visual qualities that worked:

- large warm negative space;
- one readable line of text;
- small low-contrast brandmark;
- characters occupy a clear focal zone;
- wedding/desi wardrobe cues stay consistent;
- props are sparse and symbolic;
- face style is detailed enough to feel specific, not photorealistic.

## `source-generated/`

This folder preserves the raw generated images before normalization. The raw
sizes vary, while the root files are standardized. This is a good production
pattern because it keeps both provenance and publish-ready assets.

## Slide-By-Slide Visual Logic

### Slide 1

Job: hook and identity setup.

Why it works:

- one line at the top;
- Aachu's raised arm creates instant motion;
- Himanshu's body language is calm and amused;
- wardrobe and floral cues establish the desi/wedding world immediately.

### Slide 2

Job: specific emotional behavior.

Why it works:

- speech bubble makes the Hinglish line visual;
- one tear is enough;
- tissue and water tell us Himanshu knows the pattern;
- the joke stays affectionate.

### Slide 3

Job: strongest memeable chaos beat.

Why it works:

- barefoot exit is visually funny in one second;
- Himanshu holding the shoes is the calm-husband role in one prop;
- terracotta step line gives setting without clutter;
- the couple dynamic is readable without reading the text.

### Slide 4

Job: daily rhythm.

Why it works:

- multiple Aachu moods show pattern, not one incident;
- breakfast props make it domestic and relatable;
- Himanshu watches calmly with chai;
- this is the busiest slide, but still controlled.

### Slide 5

Job: reveal Himanshu as the emotional anchor.

Why it works:

- Himanshu is centered alone;
- chaos is represented by small props around him;
- his smile shifts the carousel from joke to affection;
- this slide gives him agency, not just reaction.

### Slide 6

Job: soft turn.

Why it works:

- the pose is quiet and intimate;
- terracotta steps and flowers continue the world;
- the copy opens emotional space without overexplaining;
- this slide slows the rhythm before the thesis.

### Slide 7

Job: save-worthy thesis.

Why it works:

- spark and diya make the relationship metaphor visible;
- the couple becomes soft background, not literal scene;
- final copy has enough whitespace to breathe;
- the image feels like closure, not another gag.

## Actual Reusable Lesson

Reusable:

- one idea per slide;
- each slide has a narrative job;
- visual proof before emotional thesis;
- character contrast is shown through posture and props;
- motifs repeat across the deck;
- joke turns into tenderness;
- final image assets are visible at the root.

Not reusable as a rule:

- the exact `he married` phrasing;
- the exact slide count for every possible story;
- wedding wardrobe for non-wedding stories;
- spark/diya metaphor for every topic.

## Next Package Standard

Any next carousel package should include:

- `manifest.json` with reference roles;
- `concept.json` with human truth, visual meaning, metaphor, character bible;
- `slides.json` with copy, role, visual, emotion, CTA intent;
- `prompt-pack.json` with compact art-direction prompts;
- `copy.json`, `review.json`, `final-approval.md`, `storyboard.md`;
- generated root `slide-XX.png` files;
- `source-generated/`;
- `preview.md`.

Audit files can exist, but they should not become the center of the creator
experience.
