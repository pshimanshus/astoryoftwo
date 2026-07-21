# ASTO-011 Deep Spec - Small Brief Without Framework Dump

## Why This Task Exists

This is the core creative-agent eval. The creator may bring only a line,
feeling, or half-formed incident. A weak agent answers with framework names,
score tables, and architecture before giving the creator something alive. The
right behavior is small brief first: preserve the exact seed, choose a format,
show scene proof, and give a human-feeling route without exposing private
rubric machinery.

## Starting Fixture

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The fixture prompt is the seed: she says "main kar lungi" but the real love is
that he knows when not to believe her. The fixture includes a prior bad
creator-facing artifact at `output/evals/ASTO-011/creator-brief.md` with visible
terms like Story-Selling, Golden Theme, 28/30, selector verdict, a request for
the creator to bring the finished concept, and no scene. The fail-to-pass check
rejects creator-visible framework leakage, missing exact seed preservation,
missing format choice, missing visible object/reaction/payoff evidence, and
creator-solving handoff. The pass-to-pass check allows a separate private notes
artifact to contain rubric terms if it is clearly not creator-facing.

## Failure Modes

- Agent asks the creator to bring a finished concept.
- Agent turns the seed into generic caretaker romance.
- Agent exposes internal scores in public copy.
- Agent writes slide architecture without an alive human baseline.
- Agent picks carousel by default without explaining why the moment needs it.

## Checker Design

Deterministic checks scan the creator-facing artifact for banned framework
terms and required concepts: exact seed phrase, format choice, scene behavior,
and concrete couple object/action. Rubric review scores seed preservation,
scene proof, format judgment, creator-facing taste, and relationship motion.
The fail-to-pass case flips when the visible output becomes usable creative
briefing. The pass-to-pass case ensures internal analysis can still exist
separately. A hidden variant should use a different seed with Hinglish phrasing.

## Anti-Gaming

The checker should not accept a keyword-stuffed paragraph. Require observable
scene proof: who does what, what object moves, what reaction reveals love, and
why the format fits. Forbid touching production rules to make the creative
artifact easier to pass.

## Severity Model

Critical: framework dump remains, seed erased, or creator-facing copy includes
private scores. Major: no format choice or no scene proof. Minor: brief is a
little long but still useful and human.
