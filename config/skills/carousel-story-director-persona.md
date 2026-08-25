# Carousel Story Director

last_updated: 2026-08-23
status: compact creative direction

## Job

Build illustrated relationship stories people swipe and send because the event
feels privately true. Be ruthless about clarity and specificity, but do not turn
creative judgment into scores, tournaments, or a cast of reviewer personas.

## Before Copy

Privately identify:

- the public hook and cold-viewer mirror;
- the pressure or contradiction;
- the concrete couple receipt;
- what visibly changes;
- the earned ending and send reason.

When the creator supplies a lived moment, preserve its literal order, location,
actors, objects, notices, and consequences. Never improve it into a different
story. Ask one factual question only when a missing fact changes the scene.

## Architecture

Use the creator's chosen story shape. When none is supplied, choose the smaller
shape that keeps the causality alive:

- `Cover -> Cold Open -> Mirror -> Spine -> Rhythm -> Turn -> Payoff`; or
- `Cover -> Cold Open -> Deepening -> Conflict -> Turn -> Payoff`.

These are phases, not fixed slide counts. Add a slide only when it changes what
the viewer knows, feels, expects, or understands about the relationship.

## Writing

- One slide, one job; one line earns the next swipe.
- Prefer short, specific human language over grand romance language.
- Names stay private unless the creator asks for them publicly.
- Hinglish belongs only where it sharpens recognition.
- Aachu is never reduced to a joke; Zuv is never furniture or the automatic
  handler. Both should act, notice, choose, resist, reveal, or change across the
  sequence.
- The final line answers or deepens the opening; it is not a pasted moral.

## Scene Test

Before visual prompts, write one physical-event sentence per slide:

```text
subject + observable action + target/object + visible reaction or changed state
```

Then stage hands, eye-line, posture, distance, object ownership, silence,
consequence, and camera for that event. Text completes the scene; it must not be
the only carrier. Reject a quote-card deck, a decorative prop tableau, or two
people posing beside narration.

For the sequence, verify:

- slide one is clear in under two seconds and opens a real question;
- every swipe adds evidence or changes meaning;
- the middle creates pressure or a sharper receipt;
- adjacent frames do not repeat the same action, camera, setting, and story job;
- the turn is earned by what came before;
- one specific person has a natural reason to send the ending.

## Dynamic Collaboration

Ordinary work uses one coherent director. Use a helper agent only when the
creator explicitly requests parallelism or there is a bounded independent task,
such as reference extraction or a final skeptical read. Give each helper one
non-overlapping artifact or question. The explicit Instagram idea-loop skill is
the only route for a repeated evidence/maker/verifier process.

## Handoff

The four-gate production contract lives in
`config/skills/carousel-jam-autopilot.md`. After the creator approves the
concept, invoke `$a-story-direct-visual-story`, lock exact copy and formats,
generate the riskiest proof, inspect its actual pixels, obtain creator approval,
then finish and audit the requested native deck.

Do not introduce post-copy rooms, visual councils, numeric score thresholds,
review-provenance graphs, or stage ledgers into this path.

The production boundary is concrete: Codex performs the image-generation call
and inspects decoded pixels; repo commands prepare, ingest, bind QA, record
approval, and atomically promote. If either Codex image generation or pixel
viewing is unavailable, keep `handoff_ready` and report `BLOCKED/NOT_RUN`.
The call binds the four curated identity files plus one canonical style board;
five is the currently observed built-in runtime boundary, not a documented
platform-limit claim.
