# ASTO-018 Deep Spec - Copy-Visual Logic Contradiction

## Why This Task Exists

The repo has learned that beautiful art can still fail the story. The 2026-05-30
phone-prank correction is the cleanest example: the copy said "YOUR SOCKS ON
BEFORE YOUR PANTS" but the visual already showed Zuv wearing pants. The
`roti-bite-rights` storyboard has another: Zuv must look at his father, not at
Aachu, and Aachu is already eating the bite. These are not taste notes; they
are scene-logic failures that should block visual approval.

## Starting Fixture

Fixture direction: **regression**. The protected current implementation is
expected to reject the seeded failure, so a single-pass `evals/runner.py review`
records this fixture as `guarded`. That guard result alone cannot award agent
solve credit: an isolated benchmark run must first apply a hidden code mutation
or pre-fix revision that makes the guard fail, then evaluate the agent patch.

The visible fixture at `fixtures/output/evals/ASTO-018/visual-qa.json` contains
a visual QA artifact where status and `pass` claim success while the evidence
says Zuv is already wearing pants for copy that depends on socks coming before
pants. Example hidden contradictions should vary the failure: wrong gaze
target, missing object movement, cause/effect reversal, or symbolic prop
replacing literal scene evidence. The fail-to-pass state is that the slide can
proceed. The pass-to-pass state is that style-correct, identity-correct slides
still pass when their visible evidence proves the text.

## Failure Modes

- Agent changes approved copy to match the wrong image.
- Agent treats identity match as enough.
- Agent records "matches vibe" instead of explicit evidence.
- Agent catches one hard-coded socks/pants example but misses gaze/object
  contradictions.
- Agent lets final audit pass because visual QA is only Markdown checkboxes.

## Checker Design

The named deterministic checker is `copy_visual_logic_fixture`. It requires
each slide to declare a `copy_claim` and `visible_evidence` or equivalent
structured fields, then fails when QA simultaneously claims PASS and records a
visible contradiction. A hidden variant should use a different contradiction:
the person looks at the wrong character, the object is already moved before the
line says it moves, or a decorative symbol replaces literal proof.
Fail-to-pass flips when contradictions block proof/final approval.
Pass-to-pass preserves existing identity, style, text, and dimension gates.

## Anti-Gaming

Do not accept a generic checkbox saying "copy aligns with visual." Require
observable evidence in the visual plan or QA. Forbid agents from silently
rewriting approved copy to accommodate a failed image. The checker should treat
copy lock as authoritative unless creator metadata explicitly reopens copy.

## Severity Model

Critical: contradictory visual reaches proof/final approval, approved copy is
silently rewritten, or visual QA is weakened. Major: contradiction is blocked
but evidence fields are too vague. Minor: evidence wording is clunky but
specific enough to audit.
