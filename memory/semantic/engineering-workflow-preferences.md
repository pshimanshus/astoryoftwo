# Engineering Workflow Preferences

last_updated: 2026-05-28
confidence: 0.9
sources:
- direct creator instruction in Codex chat on 2026-05-25
- direct creator approval in Codex chat on 2026-05-28 to proceed with safe
  autopublish setup
- direct creator correction in Codex chat on 2026-05-28 that carousel image
  generation should use Codex's image tool, not an API key path
- direct creator correction in Codex chat on 2026-05-28 that illustrated
  carousel identity match comes before all other image checks
- direct creator correction in Codex chat on 2026-05-28 to avoid AI sprawl and
  prefer crisp, low-file, low-repetition code

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

fact: For illustrated @a.storyof.two carousel generation, identity match is
the first blocking gate, before story readability, house style, text accuracy,
or full-batch generation. A proof with generic faces, wrong Aachu/Zuv face
structure, wrong hair/beard/proportions, or only "close enough" resemblance is
REJECTED, not PASS_WITH_NOTES. Use the selected identity image(s) as actual
visual inputs before judging anything else.
confidence: 1.0

fact: Prefer crisp engineering with the smallest durable surface area: fewer
files, one clear route per workflow, one responsibility per module, and no
duplicated logic. If two lines solve the problem safely, do not write ten; if a
helper prevents repetition, use the helper instead of adding another parallel
path.
confidence: 0.95
