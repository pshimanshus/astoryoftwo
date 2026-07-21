# Engineering Workflow Preferences

research_partner_summary: thinking research partner; form explicit hypotheses;
challenge weak ideas; proposal-first durable updates; improve existing project
files before creating new files.

last_updated: 2026-07-04
confidence: 0.94
sources:
- direct creator instruction in Codex chat on 2026-05-25
- direct creator approval in Codex chat on 2026-05-28 to proceed with safe
  autopublish setup
- direct creator correction in Codex chat on 2026-05-28 that carousel image
  generation should use Codex's image tool, not an API key path
- direct creator correction in Codex chat on 2026-05-28 after stale carousel
  proof artifacts caused story drift
- direct creator correction in Codex chat on 2026-05-28 to avoid AI sprawl and
  prefer crisp, low-file, low-repetition code
- direct creator correction in Codex chat on 2026-07-01 from a simple prompt
  transcript: simple model freedom generated strong couple concepts, copy, and
  visual setup; engineering should perfect and guard the output, not own the
  initial idea
- direct creator correction in Codex chat on 2026-07-02 after a wrong long
  image/silent format snapback: never infer social format from repo defaults
  after the creator removes or rejects that format; lock the exact canvas first
- direct creator correction in Codex chat on 2026-07-02 finalizing the updated
  carousel format: Instagram post/carousel finals are exact `1080x1440` exports
  from `1440x1920` 3:4 source art
- direct creator instruction in Codex chat on 2026-07-04 asking the project to
  behave like a memory-backed thinking research partner
- direct creator correction in Codex chat on 2026-07-04 to stop adding parallel
  files/surfaces and optimize existing project files instead
- direct creator correction in Codex chat on 2026-07-12 after The Almosts Were
  Practicing images moved forward without structured face identity eval; the
  correct behavior is to stop instead of continuing

## Research Partner Operating Model

This project should make Codex act like a thinking research partner for
@a.storyof.two, not a passive command executor.

The partner behavior is:
- form explicit hypotheses about what will work before building;
- challenge weak, stale, or self-defeating directions with repo evidence and
  taste;
- preserve the creator's exact seed while improving the route when memory,
  rules, wiki, or evals point to a stronger move;
- turn repeated session learnings into proposal-first durable updates in
  `memory/semantic/`, `config/rules/`, `config/skills/`, `wiki/`, or tests;
- keep learning honest: no pretending the base model self-updates, no silent
  rule edits, and no generic "AI brain" theater;
- keep the implementation lightweight: improve existing project files before
  creating new files, commands, or parallel helper surfaces.
confidence: 0.92

fact: During carousel jams, broad theme seeds should be challenged before packaging. If a seed has abstract relationship language but no concrete couple scene or reader-recognition proof, block packaging with a REWORK verdict and ask for one visible action, object, room, line of dialogue, or private repeated pattern. Concrete couple moments should continue through the jam path.
confidence: 0.9

## Standing Preference

fact: Treat critical project infrastructure as a blocking concern, not an
optional suggestion. If git setup, repo hygiene, tests, memory health, or other
foundational project enhancements are required for safe progress, push hard,
name the blocker clearly, and do not drift into lower-priority work until the
blocker is handled or the creator explicitly accepts the risk.
confidence: 0.9

fact: When the creator tries to skip or ignore a required infrastructure step,
challenge the skip directly and explain the project risk in practical terms.
This should feel firm and protective, not performative.
confidence: 0.88

fact: Codex should own safe git publishing at the end of substantial repo
sessions so the creator does not need to manually push. The required approach is
the safe autopublish closeout gate, not blind background pushing: inspect scope,
block risky paths and secrets, run tests, run wiki health, commit, and push only
after every gate passes.
confidence: 0.92

fact: Blind auto-pushing, timer daemons, or file watchers are rejected for this
repo because they can publish broken work, secrets, sensitive identity media, or
half-finished creative artifacts. Automatic publishing is acceptable only when
it is gated by verification and clear scope.
confidence: 0.9

fact: For illustrated carousel image generation, do not route the creator into
an OpenAI API key or external image-client workflow. The expected path is Codex
native packaging plus Codex image tool generation in-session, followed by
packaging and visual QA.
confidence: 0.9

fact: For carousel ideation and packaging, model owns concept, copy, and visual
invention, and engineering is the guardrail layer: it checks for repeated ideas,
identity drift, weak or broken visuals, exact on-image text, brandmark,
dimensions, stale artifacts, and house guidance failures. Start with or
preserve the free creative pass first; scoring, memory, and QA should block hard
failures or repair issues without replacing the strongest alive route with a
safer template.
confidence: 1.0

fact: After the creator corrects a carousel story/proof, treat stale downstream
artifacts as a production bug. Rebuild every generation-facing artifact from
the corrected source of truth before calling image generation: `slides.json`,
`copy.json`, `post-copy-visual-room.json`, `visual-debate.json`,
`visual-plan-quality.json`, `identity-consistency-review.json`,
`prompt-pack.json`, `review.json`, `manifest.json`, `proof-review.json`, and
`image-generation.json`/`final-images.json`. Then run `rg` for old phrases and
block generation if stale copy remains.
confidence: 1.0

fact: For Codex-native carousel packaging, `prompt-pack.json` must contain a
complete `slides[]` array before handoff or packaging. A proof-only prompt pack
or old `prompt-pack-draft.json` is not enough. Handoff gates must pass
`identity-consistency-review.json` with `status: PASS` and
`visual-plan-quality.json` with `status: PASS` plus `can_generate: true`.
confidence: 0.99

fact: Do not call carousel proof images, old generated sources, or handoff
state "final images." For a normal post/carousel request, a carousel is final
after exact `1080x1440` post finals exist for every slide under `final/`, with
visual QA and final audit written. Native `1080x1920` Story/Reel images under
`final-reels-stories/` are required only when the creator explicitly requested
Story or Reel. Current post/carousel finals must be exact `1080x1440` exports
from `1440x1920` 3:4 source art unless the creator explicitly changes the
canvas again. Never create an automatic companion format.
confidence: 1.0

fact: Prefer crisp engineering with the smallest durable surface area: fewer
files, one clear route per workflow, one responsibility per module, and no
duplicated logic. If two lines solve the problem safely, do not write ten; if a
helper prevents repetition, use the helper instead of adding another parallel
path.
confidence: 0.95

fact: Before any illustration generation or export, run a Format Inference
Preflight. Lock the requested canvas from the current creator instruction,
current attached references, accepted prior screen, and immediate chat
corrections. If the creator removes, rejects, or corrects an aspect/format
decision, that correction overrides repo defaults for the current task. Never
snap back to 3:4, 9:16, feed, Story, Reel, square, or multi-format output from
workflow defaults. If the canvas is unclear after a correction, ask for the
exact canvas before generating.
confidence: 1.0

fact: For illustrated carousel proof generation, no identity eval means no next
slide. After a proof slide or any creator correction about likeness, stop before
batching the remaining images until a structured `identity-consistency-review.json`
or `visual-qa.json` records selected Aachu/Zuv reference IDs and specific
likeness notes. If real likeness comparison is unavailable, mark
`BLOCKED_FOR_IDENTITY_EVAL` or `IDENTITY_UNVERIFIED`, tell the creator, and do
not call the proof final or continue generating more slides.
confidence: 1.0
