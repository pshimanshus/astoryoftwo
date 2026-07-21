# ASTO-017 Deep Spec - Public Name Leakage

## Why This Task Exists

The repo needs two truths at once: the work is about the actual recurring
couple, and public copy should usually read as a universal relationship mirror.
Semantic memory says "Aachu" and "Zuv" belong in internal notes, visual
direction, identity prompts, and QA artifacts, but not public-facing carousel
copy unless the creator explicitly asks for names. This eval prevents agents
from solving identity specificity by leaking internal names into slides.

## Starting Fixture

Fixture direction: **solution**. A single-pass `evals/runner.py review` must
observe the materialized starter as `unresolved`. The task becomes resolved
only after the agent repairs the fixture-backed repository state and the named
checker passes.

The visible fixture at `fixtures/output/evals/ASTO-017/public-copy.json`
contains public slide copy that names Aachu and Zuv without an explicit
creator-request flag, plus an internal identity prompt where those names are
valid and necessary. The fail-to-pass state is public leakage. The pass-to-pass
state is internal identity prompts, reference IDs, and QA language still using
names to preserve the real people.

## Failure Modes

- Agent globally removes Aachu/Zuv, weakening identity prompts.
- Agent allows names in public copy because the package is about them.
- Agent checks only the creator brief and misses slide text.
- Agent makes all copy generic and loses the actual couple's behavior.
- Agent edits `AGENTS.md` instead of downstream voice/rule/tests.

## Checker Design

The named deterministic checker is `public_name_boundary_fixture`. It
classifies fields by audience. Public fields include on-image text,
creator-facing brief, published caption, and public slide copy. Internal fields
include visual direction, prompt identity lock, reference review, and QA.
Fail-to-pass flips when unrequested public names are removed or replaced with
natural pronouns/relationship language. Pass-to-pass coverage ensures internal
identity evidence remains. A hidden variant should put the names in a caption
and a slide label, not only `copy.json`.

## Anti-Gaming

Do not accept deleting identity references or replacing names with vague
"person one/person two" language. Require the public copy to remain warm and
specific through behavior. The checker should allow public names only when
metadata records the creator explicitly requested names for that artifact.

## Severity Model

Critical: public slide/caption names leak without permission, or internal
identity names are removed from prompts/QA. Major: one public field is missed.
Minor: phrasing becomes slightly generic but still preserves the scene.
