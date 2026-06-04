# Paper Tone Rejection

Status: HARD FAILURE

Creator correction:

The generated proof is still too yellow. The approved premium reference is
clean off-white/neutral ivory paper with visible grain. It is not amber,
golden, tea-stained, sepia, beige, tan, parchment, or restaurant-light washed.

## Cause

The prompt allowed Pizza Bakery warmth, wooden table, and lamp glow to bleed
into the whole page. That made the negative space read yellow, even though the
story blocking improved.

## New Rule

Separate paper from scene warmth.

- Paper / negative space: clean neutral off-white ivory.
- Linework: charcoal, pencil, muted blue-grey/brown ink.
- Scene warmth: only inside wood, coffee, pizza, skin, lamp objects.
- No global golden overlay.
- No sepia watercolor wash.
- No beige/tan background.

## Correct Reference

Use the creator-attached premium reference as the tone standard:

- off-white paper first;
- soft texture;
- gentle grey-blue shadows;
- muted browns only in objects;
- black/charcoal readable handwritten text;
- no restaurant-light color cast over the whole illustration.

## Regeneration Instruction

Before generating again, include:

```text
PAPER TONE LOCK:
The entire negative-space paper must be clean neutral off-white ivory, close to
white, with subtle visible grain. Do not tint the page yellow, amber, golden,
sepia, beige, tan, parchment, coffee-stained, or heavy cream. Warm restaurant
colors may appear only inside the illustrated wood, glass, and small props; they
must not wash over the background paper.
```
