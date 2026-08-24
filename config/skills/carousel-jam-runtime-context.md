# Carousel Jam Runtime Context

last_updated: 2026-08-23
status: minimal default runtime

## Purpose

This is the compact context for ordinary @a.storyof.two carousel work. It keeps
the default run fast and readable. Canonical `config/rules/` files win on
palette, identity, text, brandmark, dimensions, variety, relationship motion,
and scene/entity integrity.

Do not load the long theme, scoring, memory, agent-room, or review-loop sources
at startup. Search the relevant section only when a creator correction, rejected
lane, or failed check needs it. Use `$a-story-instagram-idea-loop` only on an
explicit request for the deep idea loop.

## Default Flow

```text
small brief
-> Gate 1: concept lock
-> Gate 2: exact copy + requested format lock
-> one physical event per slide
-> compact prompt compile
-> riskiest proof
-> Gate 3: actual-pixel QA + creator approval
-> remaining native slides
-> Gate 4: final package QA
```

These are the only gates. A deterministic check may support a gate but must not
create another approval state or duplicate artifact.

## Creative Context

- Preserve the creator's literal sequence, objects, corrections, approved
  language, and rejected scope.
- Write the alive draft before using rules. The rules block hard failures; they
  do not invent the first idea.
- Make the relationship legible to a cold viewer through action and consequence,
  not explanation alone.
- Use `config/skills/creator-skill-stack.md` as the six-question taste pass.
- Keep public copy free of internal framework and score language.
- The last beat must reframe or answer the opening, not soften into a generic
  moral.
- Preserve a creator-supplied architecture, including
  `Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff`.
- Treat that reflective structure as first-class. Deepening, Conflict, and Turn
  may each span multiple slides when each new scene changes the story.

## Format Lock

Resolve format from the current request and corrections before prompts:

- `instagram_post`: default only when no canvas is specified; 1080x1440.
- `reels_stories`: 1080x1920; explicit request only.
- `square`: 1080x1080; explicit request only.

Persist only the requested set in `format-contract.json`. Generate each natively;
never crop, stretch, pad, or infer intent from old folders. A current creator
correction overrides defaults and stale assets.

## Scene Lock

For every slide, `slides.json` must contain exact on-image text and one concise
physical event:

```text
subject + observable action + target/object + visible reaction or changed state
```

Also capture the few generation-critical facts: camera/focal hierarchy, hands,
gaze, body distance, object ownership, expected people, wardrobe reference, and
text-safe space. Vary story job, action, shot, or setting between adjacent
slides. Text completes the scene; it must not be the only story carrier.

## Generation Lock

- Attach a small selected bundle of actual Aachu/Zuv identity images plus style
  references to every call. Text-only identity descriptions are blocked.
- Wardrobe comes from the attached identity/current-request images first.
- Preserve both whole people: face, hair, height, proportions, expression,
  posture, and clothing.
- Integrate exact approved text and tiny `@a.storyof.two` at top-right.
- Generate one risky proof first. Do not batch until its current pixels pass and
  the creator approves.
- No identity eval means no next slide.
- Allow two total semantic attempts for one visual premise. Replace the premise
  after the second miss.

## Pixel QA

Inspect the decoded file, in order:

1. visible physical action and relationship state;
2. expected people/entities, continuous silhouettes, body/solid-object depth,
   and owner-to-hand-to-object contact;
3. Aachu/Zuv likeness and wardrobe against attached reference IDs;
4. exact text, brandmark, house style, and native dimensions.

Bind QA to the current package-relative path, SHA-256, and dimensions. A prompt,
filename, agent label, or generation report cannot pass pixel QA. Failed
candidates stay quarantined and set the next action to a concrete repair.

## Minimal Artifacts

Before proof: `creative-context.json`, `format-contract.json`, `slides.json`,
`prompt-pack.json`, and compiled prompt files. After proof: quarantined PNG and
`proof-qa.json`. After final: requested native PNGs, `final-images.json`,
`visual-qa.json`, and `final-audit.json`.

The ordinary run does not create debate rooms, numeric scorecards, provenance
graphs, ledgers, stage reviews, or wiki-update artifacts.
