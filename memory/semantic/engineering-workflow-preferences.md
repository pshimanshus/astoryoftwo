# Engineering Workflow Preferences

last_updated: 2026-07-01
confidence: 0.92
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
state "final images." A carousel is final only after separate native 4:5 and
separate native 9:16 images exist for every slide, packaged under `final/` and
`final-reels-stories/`, with visual QA and final audit written.
confidence: 1.0

fact: Prefer crisp engineering with the smallest durable surface area: fewer
files, one clear route per workflow, one responsibility per module, and no
duplicated logic. If two lines solve the problem safely, do not write ten; if a
helper prevents repetition, use the helper instead of adding another parallel
path.
confidence: 0.95
