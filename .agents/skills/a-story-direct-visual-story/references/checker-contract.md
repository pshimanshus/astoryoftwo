# Visual Story Checker Contract

The checker supports the four-gate carousel workflow. It has two modes, not two
review events:

- `pre`: verify locked copy, canvas, references, and one concrete physical
  action per slide before spending an image-generation call;
- `post`: inspect the exact current proof or final pixels and verify their file
  bindings.

Neither mode requires agent-room transcripts, blind-response artifacts,
reviewer task IDs, run IDs, provenance graphs, or Event A fingerprints.

## Preflight inputs

The package must contain:

- `slides.json` with exact slide copy and a physical action sentence;
- `format-contract.json` with only the formats requested now;
- `prompt-pack.json` with one matching slide record and selected real Aachu/Zuv
  identity-reference paths.

Each physical action sentence must visibly name or imply:

1. the person or subject;
2. the action;
3. the person, object, or space acted upon;
4. a visible reaction, consequence, or changed state.

Mood is not an action. “Dreamy couple in a warm room” fails. “They pull the
same dining table toward opposite walls while the plates slide apart” passes.

The preflight output uses one check key:

```json
{
  "phase": "pre",
  "checks": {
    "copy_format_action_preflight": {
      "pass": true,
      "issues": []
    }
  },
  "pass": true,
  "issues": []
}
```

## Pixel QA inputs

Use `proof-qa.json` for the risky proof and `visual-qa.json` for the complete
deck. A passing QA record must be bound to current package-local image bytes.

```json
{
  "status": "PASS",
  "image_set_sha256": "sha256:...",
  "checks": {
    "semantic_action": {"pass": true, "evidence": "..."},
    "relationship_state": {"pass": true, "evidence": "..."},
    "entity_anatomy_spatial": {"pass": true, "evidence": "..."},
    "identity": {"pass": true, "evidence": "..."},
    "text_style_dimensions": {"pass": true, "evidence": "..."}
  },
  "slides": [
    {
      "slide": 1,
      "native_outputs": {
        "instagram_post": {
          "path": ".internal/visual-quarantine/slide-01/attempt-01/instagram-post.png",
          "sha256": "...",
          "width": 1080,
          "height": 1440
        }
      }
    }
  ]
}
```

Review in this order and stop at the first failure:

1. `semantic_action`: does the physical event read from the image alone?
2. `relationship_state`: is the intended between-them state or change visible?
3. `entity_anatomy_spatial`: expected people/entities, whole silhouettes,
   limbs, hands, contact, depth, and object ownership are coherent.
4. `identity`: both people match attached references in face, hair, body
   proportions, height, posture, expression, and reference-led wardrobe.
5. `text_style_dimensions`: exact text, tiny top-right `@a.storyof.two`, house
   style, and each locked native dimension pass.

The checker verifies that every `path` is package-relative, exists, is not a
symlink, decodes as an image, matches its recorded SHA-256, and has the locked
dimensions. A prompt, filename, reviewer label, generator response, or prior QA
record is not pixel evidence.

If semantic action fails, set the package state to `proof_failed` and the next
action to `repair_visual_premise`. Do not continue the batch or regenerate an
unchanged semantic premise.

## Commands

```bash
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=pre
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=post
```

The command exits zero only when the requested phase passes. `post` also runs
the package doctor, so any current identity-reference, format, asset, QA, or
final-audit blocker fails the command.
