# Pixel Observation Checker Contract

The checker supports the four-gate carousel workflow. It has two modes, not two
review events:

- `pre`: verify locked copy, canvas, references, and one concrete physical
  action per slide before spending an image-generation call;
- `post`: validate observations that Codex authored after inspecting the exact
  decoded proof or final pixels with `view_image`, plus their file bindings.

The repo checker does not see an image, run OCR, call a vision backend, or infer
visual quality. It rejects structurally incomplete or stale observation claims;
it never reports that it personally inspected pixels. If Codex image viewing is
unavailable, no strict QA record can be written and the package remains at its
current handoff/review-required state.

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

## Strict pixel QA inputs

All new v3 packages use `carousel-pixel-qa/v2`. Archived v2 packages remain
read-only auditable through the legacy checker path; legacy QA is not a valid
new write.

Use `proof-qa.json` for the risky proof. It includes the one proof asset
inventory because no final manifest exists yet. Every binding is
package-relative, non-symlinked, decoded with Pillow, hash-bound, and checked
against the locked native dimensions.

Codex submits the `inspection`, per-format `reviews`, and check evidence. The
repo review command derives `asset_bindings` from the current ingested bytes;
it never trusts or requires Codex to calculate hashes or dimensions. If an
authored payload supplies conflicting inventory, review fails closed.

```json
{
  "schema_version": "carousel-pixel-qa/v2",
  "scope": "proof",
  "status": "PASS",
  "inspection": {
    "method": "codex_view_image",
    "decoded_pixels_observed": true
  },
  "selected_slides": [4],
  "slides": [
    {
      "slide": 4,
      "asset_bindings": {
        "instagram_post": {
          "path": ".internal/visual-quarantine/slide-04/attempt-01/instagram_post.png",
          "sha256": "sha256:...",
          "width": 1080,
          "height": 1440,
          "binding_sha256": "sha256:..."
        }
      },
      "reviews": {
        "instagram_post": {
          "checks": {
            "physical_action": {"status": "PASS", "evidence": "..."},
            "relationship_state": {"status": "PASS", "evidence": "..."},
            "entity_spatial_integrity": {"status": "PASS", "evidence": "..."},
            "identity_wardrobe_accessories": {
              "status": "PASS",
              "evidence": "...",
              "references": {
                "aachu": [".internal/references/identity/aachu.png"],
                "zuv": [".internal/references/identity/zuv.png"],
                "together": [".internal/references/identity/together.png"]
              }
            },
            "text_brandmark_style_dimensions": {
              "status": "PASS",
              "evidence": "...",
              "expected_text": "Exact locked copy.",
              "observed_text": "Exact locked copy.",
              "observed_brandmark": "@a.storyof.two",
              "style_references": [".internal/references/style/watercolor.png"]
            }
          }
        }
      }
    }
  ]
}
```

Use `visual-qa.json` for the complete deck. It deliberately contains no paths,
hashes, dimensions, or other asset inventory inside slide records. A hidden
prospective `carousel-final-images/v3` manifest owns that inventory until final
audit. `visual-qa.json` binds the exact manifest and each asset:

The repo review command derives `manifest_sha256` and
`asset_binding_hashes` from that hidden manifest. Conflicting caller-supplied
bindings are rejected.

```json
{
  "schema_version": "carousel-pixel-qa/v2",
  "scope": "final",
  "status": "PASS",
  "inspection": {
    "method": "codex_view_image",
    "decoded_pixels_observed": true
  },
  "selected_slides": [1, 2, 3, 4, 5, 6],
  "manifest_sha256": "sha256:...",
  "asset_binding_hashes": {
    "1:instagram_post": "sha256:...",
    "2:instagram_post": "sha256:..."
  },
  "slides": [
    {
      "slide": 1,
      "reviews": {
        "instagram_post": {
          "checks": {
            "physical_action": {"status": "PASS", "evidence": "..."},
            "relationship_state": {"status": "PASS", "evidence": "..."},
            "entity_spatial_integrity": {"status": "PASS", "evidence": "..."},
            "identity_wardrobe_accessories": {
              "status": "PASS",
              "evidence": "...",
              "references": {
                "aachu": [".internal/references/identity/aachu.png"],
                "zuv": [".internal/references/identity/zuv.png"],
                "together": [".internal/references/identity/together.png"]
              }
            },
            "text_brandmark_style_dimensions": {
              "status": "PASS",
              "evidence": "...",
              "expected_text": "Exact locked copy.",
              "observed_text": "Exact locked copy.",
              "observed_brandmark": "@a.storyof.two",
              "style_references": [".internal/references/style/watercolor.png"]
            }
          }
        }
      }
    }
  ]
}
```

Each separately generated native format receives its own review. One 3:4
observation cannot certify a separate 9:16 or square render.

Review in this fail-fast order:

1. `physical_action`: does the physical event read from the image alone?
2. `relationship_state`: is the intended between-them state or change visible?
3. `entity_spatial_integrity`: expected people/entities, whole silhouettes,
   limbs, hands, contact, depth, and object ownership are coherent.
4. `identity_wardrobe_accessories`: both people match the named attached
   Aachu, Zuv, and together references in face, hair, body proportions, height,
   posture, expression, reference-led wardrobe, and accessories.
5. `text_brandmark_style_dimensions`: exact text, tiny top-right
   `@a.storyof.two`, house style against named attached style references, and
   the locked native dimension pass.

If one check fails or is missing, later checks must not be marked PASS. A weak
identity or polished style cannot rescue an unreadable physical premise.

The checker rejects stale/tampered hashes, dimensions, binding fingerprints,
manifest fingerprints, path escapes, symlinks, unrequested formats, incomplete
slide/format coverage, non-exact observed text, unnamed identity references,
and missing decoded-pixel inspection declarations. A prompt, filename, reviewer
label, generator response, or prior QA record is not pixel evidence. The
declared method is a fail-closed workflow contract, not tool telemetry; the
skill must not author it when pixel viewing was unavailable.

If semantic action fails, set the package state to `proof_failed` and the next
action to `repair_visual_premise`. Do not continue the batch or regenerate an
unchanged semantic premise.

## Commands

```bash
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=pre
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=post
```

The command exits zero only when the requested phase passes. Its post-check key
is `bound_pixel_observation_qa`, which describes what the repo actually checked.
`post` also runs the package doctor, so any current identity-reference, format,
asset, QA, or final-audit blocker fails the command.
