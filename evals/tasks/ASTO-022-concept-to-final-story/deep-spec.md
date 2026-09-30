# Concept approval to final story

## Why This Task Exists

A creator liked the emotional premise, then rejected the delivered final draft
for failing storytelling format. The assistant mistook concept approval for
completion, dropped the proposed cover, and compressed story development into
an exchange. The regular creative rubric can reward clean, concrete scenes
without separately establishing architecture, development, or earned closure.

## Starting Fixture

Fixture direction: **solution**. The initial state must remain unresolved.

The solution fixture preserves the exact rejected output as input. It does not
seed a repaired `creator-brief.md`; the missing requested result makes the
mechanical fixture review unresolved. Once a result exists, mechanical success
alone still leaves semantic judgment PENDING. The original negative example
is assessed with the story-completion rubric, not a phrase blacklist.

Fail-to-pass requires a developed replacement and an independent review.
Pass-to-pass preserves complete short or reflective stories without forcing
one phase per slide.

## Failure Modes

- Treating "nice" as approval of unwritten copy or shortened structure.
- Omitting the cover/promise or replacing selected phases with a quick exchange.
- Giving a recognition montage without developed pressure or a caused turn.
- Ending at the proposed solution when its consequence remains unwritten.
- Calling an unrun eval a pass; validating only a synopsis or earlier draft.
- Repairing by adding filler, phase labels, or a moral rather than story.

## Checker Design

Existing copy and diff checks verify a bounded creator-facing artifact.
The new story_completion rubric separately evaluates surviving locks,
functional architecture, causal development, payoff, and voice. The evaluator
requires an independent reviewer and current artifact hash. Architecture,
development, and payoff each have minimum scores, so a good total cannot hide
an incomplete ending. These checks enforce review integrity, not semantic
truth; an evidence-bearing independent read remains necessary.

## Anti-Gaming

Do not hardcode the five-slide count or the line "Kaisa tha aaj?" as failures.
Both can work in a different story. Phase labels cannot substitute for actual
causality. A wordless answer can be sufficient; a new spoken question can close
a story only if asking it answers that story's need. Evaluate the precise
opening-to-ending relationship. Do not silently impose this narrative rubric
on a creator-selected joke, observation, or catalogue. A hidden variant should
use a different premise with an incomplete ending, and keep reviewer guidance
separate from solver output.

## Severity Model

Critical: discarded creator lock or fabricated review/approval. Major: omitted
functional phase, undeveloped pressure, unearned ending, stale review, or
review of another artifact. Minor: a line needs polish while the story works.
