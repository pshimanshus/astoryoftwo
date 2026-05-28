# Engineering Workflow Preferences

last_updated: 2026-05-28
confidence: 0.9
sources:
- direct creator instruction in Codex chat on 2026-05-25
- direct creator approval in Codex chat on 2026-05-28 to proceed with safe
  autopublish setup

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
