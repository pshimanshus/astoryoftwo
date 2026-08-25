---
name: a-story-carousel-jam
description: Jam, choose, draft, direct, generate, or package an @a.storyof.two post, Reel, or carousel. Use for fresh ideas, copy, visual planning, image proofs, and final carousel work; do not use for article-only, prepost-only, or wiki-health requests.
---

# A Story Carousel Jam

Build one alive, image-led relationship story without making the creator operate
the repo. Codex owns the visual generation call and the actual-pixel read. Repo
commands own deterministic package preparation, ingestion, binding, approval,
and promotion. The default path is deliberately small:

```text
brief -> concept lock -> copy + format lock -> one physical action per slide
-> compact prompts -> riskiest proof -> pixel QA + creator approval
-> remaining slides -> final package QA
```

## Load

Read, in order:

1. `config/skill-systems.json` -> `carousel_jam`
2. `.agents/skills/a-story-storytelling-hook/SKILL.md`
3. `config/skills/carousel-jam-runtime-context.md`
4. `config/skills/carousel-jam-autopilot.md`
5. after concept lock, `.agents/skills/a-story-direct-visual-story/SKILL.md`

Open longer memory or theory only to resolve a specific rejection, conflict, or
failed check. The explicit `$a-story-instagram-idea-loop` remains available for
deep evidence-heavy ideation; never start it during an ordinary jam.

## Four Gates

There are exactly four creator/production gates:

1. **Concept:** one recognizable relationship truth and a concrete change.
2. **Copy + format:** exact slide text and only the requested native canvases.
3. **Proof:** the riskiest generated slide passes actual-pixel story, identity,
   anatomy, spatial, text, style, and dimension QA; the creator approves it.
4. **Final package:** every locked native slide passes the same checks and the
   final manifest/audit matches the files.

Internal checks may report why a gate failed. They must not become more approval
ledgers, numeric taste gates, agent rooms, or lifecycle ceremonies.

## Operating Rules

- Preserve the creator's exact seed, facts, copy, corrections, and approved
  locks. A rejected route stays rejected unless the creator reopens it.
- When the creator asks to jam from scratch, invent a fresh route instead of
  asking them to arrive with the concept solved.
- Start with the strongest human draft. Use memory and rules as quiet seasoning,
  not as a visible framework or a tournament the creator must review.
- Infer the best format early. Default carousel/post output is only 1080x1440.
  Generate 1080x1920 Story/Reel or 1080x1080 square only when explicitly asked.
  Never crop or resize one requested format into another.
- Keep the `instagram_post` prompt requesting exact `1080x1440; native 3:4`.
  As an observed built-in-runtime accommodation, repo ingest may quarantine an
  untouched exact-3:4 source from 1080x1440 through 1440x1920 inclusive, bind
  its hash/dimensions, and proportionally downsample it once to 1080x1440.
  Never crop, pad, stretch, upscale, accept a wrong ratio, or use this source
  accommodation for Story/Reel or square. Reuse an approved normalized proof
  as its final candidate.
- Every slide gets one sentence describing a visible physical event: who acts,
  what they act on, and what visibly changes or reacts. Atmosphere, symbolism,
  and copy alone are not an event.
- Use the creator's approved story architecture. Preserve
  `Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff` when supplied;
  never pad it into another structure.
- For new packages, attach exactly five files to every generated slide: the
  four actual Aachu/Zuv identity images in
  `identity-dossier.json.selected_generation_bundle`, then the
  single canonical style board
  `config/references/style-lock/observational-intimacy-premium/contact-sheet.png`.
  Use the identity files for the whole person—face, hair, height, proportions,
  posture, expression, and wardrobe—not as a face patch.
- Treat supplied story images as slide-local creative evidence: inspect them
  before copy/visual lock and encode every relevant wardrobe, object, setting,
  and continuity fact in `slides.json`. The compiled handoff lists them under
  `context_reference_bindings`, not the five image-generation attachments;
  never exceed the observed boundary or pretend an unattached image guided the
  pixels. Their byte bindings remain slide-local invalidation inputs.
- Put exact approved text inside the image and tiny `@a.storyof.two` at top-right.
  No invented text and no unrequested derivative.
- Generated files enter quarantine. Inspect decoded current pixels, never the
  prompt, filename, reviewer name, or generator claim.
- At `handoff_ready`, read the selected compiled `.prompt.txt`, attach those
  four identity files plus that one style-board file, and call Codex image
  generation only for the selected proof or batch slides. Ingest each returned
  file immediately. If post ingest normalizes an accepted larger source, inspect
  the normalized candidate with `view_image`; otherwise inspect the unchanged
  target-size candidate. Submit QA bound to those exact reviewed bytes while
  retaining the untouched source hash and dimensions.
- Five is the boundary observed in the current built-in Codex image-generation
  runtime smoke, not a claim about a published platform limit. Do not add the
  three individual style slides on top of the board. If the runtime rejects
  the five bound files, remain truthful and blocked rather than dropping an
  identity role silently.
- If image generation or `view_image` is unavailable, leave the package at
  `handoff_ready` and report `BLOCKED/NOT_RUN`. Never invent a generated asset,
  visual observation, or PASS result.
- In pixel QA, check in this order: visible story action and relationship state;
  people/entities, whole-person spatial integrity and hands; identity; exact
  text, brandmark, style, and dimensions.
- A semantic miss repairs the physical premise or staging before adjectives.
  Allow at most two total semantic attempts for the same visual premise. If it
  still fails, stop and replace the premise.
- Do not generate the remaining deck before proof QA and creator approval.
- Use helper agents only when the creator explicitly asks for parallel work or a
  bounded independent audit is genuinely needed. Keep ownership non-overlapping.
- Prefer the one-command workflow. If a required automation link is missing,
  name that link instead of replacing it with scattered manual ceremony.

## Minimal Package

Before proof: `creative-context.json`, `format-contract.json`, `slides.json`,
`prompt-pack.json`, `generation-state.json`, and compiled `.prompt.txt` files.

After proof: the quarantined proof PNG and `proof-qa.json`.

After audited finalization: requested native PNGs, `final-images.json`,
`visual-qa.json`, and `final-audit.json`.

Do not create agent-room, debate, score tournament, provenance, run-ledger,
stage-review, or wiki-update artifacts on the default path.

## Commands

```bash
make jam MOMENT="one specific couple moment"
make carousel STORY="source story" CREATIVE_BRIEF="locked-brief.json" TITLE="optional title"
python scripts/carousel.py status output/carousels/YYYY-MM-DD/slug
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=pre
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=post
```

`make carousel` creates a truthful package and, when the supplied brief has
locked physical actions, prepares one risky proof. Story-only input stays
`draft` and spends no generation call.

Use only these public states: `draft`, `blocked`, `handoff_ready`,
`proof_qa_required`, `proof_failed`,
`awaiting_creator_proof_approval`, `batch_ready`, `final_qa_required`,
`final_qa_failed`, and `publish_ready`. Call the work final only at
`publish_ready`; otherwise report the state and its one next action.
