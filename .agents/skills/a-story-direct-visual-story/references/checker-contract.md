# Visual Story Checker Contract

The skill uses existing lifecycle artifacts. Do not add a second storyboard or
QA source of truth.

## Contents

- [Contract invariants](#contract-invariants)
- [Event A: copy-hidden storyboard read](#event-a-visual-plan-qualityjson)
- [Event B: rendered-frame audit](#event-b-visual-qajson)
- [Legacy-package migration](#legacy-package-migration)
- [What code can and cannot prove](#what-code-can-and-cannot-prove)
- [Commands](#commands)

## Contract invariants

Event A is eligible to pass only after exact copy (or its documented text
exception) and the request-derived canvas set are locked. Event B is eligible
to pass only from direct inspection of the exact current assets named by that
lock. Neither event can inherit a result from a prompt, filename, generator
claim, older package, or arbitrary reviewer label.

Between Event A and first pixel quarantine, the executable handoff uses
`compiled-prompt-handoff/v1`: atomic staging plus package-relative path and hash
bindings for `prompt-pack.json`, `slides.json`, every compiled prompt/markdown
pair, the current format contract, and the complete prompt set. This does not
replace either review event; it prevents an approved plan from being packaged
through a different or partially compiled prompt set.

## Event A: `visual-plan-quality.json`

Add a root `director_storyboard` object. The full executable contract lives in
`pipeline/stages/carousel_visual_storytelling.py`; the fixture in
`tests/test_carousel_visual_storytelling.py` is the canonical complete example.

Required shape:

```json
{
  "status": "PASS",
  "can_generate": true,
  "director_storyboard": {
    "status": "PASS",
    "event": "copy_hidden_storyboard_read",
    "copy_locked": true,
    "copy_hidden": true,
    "intent_hidden": true,
    "copy_lock_evidence": "Exact copy or the documented text exception was locked before review.",
    "author_id": "route-author-00",
    "reviewer_id": "blind-director-01",
    "reviewer_evidence": "The reviewer received only observable staged visual cards and reported the inferred story before seeing copy or intent.",
    "requested_formats": ["instagram_post"],
    "format_contract_fingerprint": "sha256:...",
    "review_provenance": {
      "schema_version": "visual-review-provenance/v2",
      "author_task_id": "orchestrated-author-task-id",
      "author_run_id": "orchestrated-author-run-id",
      "reviewer_task_id": "orchestrated-event-a-task-id",
      "reviewer_run_id": "orchestrated-event-a-run-id",
      "input_fingerprint": "sha256:...",
      "raw_response": "Literal critic response recorded before copy or intent reveal.",
      "raw_response_fingerprint": "sha256:...",
      "output_fingerprint": "sha256:..."
    },
    "blind_cards": [
      {
        "slide": 1,
        "visible_people": ["person one", "person two"],
        "visible_setting": "...",
        "observable_action": "...",
        "hands_and_contact": "...",
        "gaze": "...",
        "body_blocking": "...",
        "object_state": "...",
        "camera_view": "...",
        "visible_continuity": "..."
      }
    ],
    "blind_input_fingerprint": "sha256:...",
    "source_fingerprint": "sha256:...",
    "creator_correction_fingerprint": "sha256:...",
    "generation_payload_fingerprint": "sha256:...",
    "director_event_fingerprint_version": "director-event/v2",
    "director_event_fingerprint": "sha256:...",
    "sequence_mode": "causal_sequence",
    "physical_event": "...",
    "emotional_arc": "...",
    "relationship_change": "...",
    "sequence_read": "...",
    "visual_variables": ["body distance", "object ownership"],
    "hero_receipt_slide": 3,
    "setup_payoff_ledger": [
      {"setup": "...", "payoff": "...", "changed_meaning": "..."}
    ],
    "object_motif_ledger": [
      {"object": "...", "initial_state": "...", "later_state": "...", "story_job": "..."}
    ],
    "slides": [
      {
        "slide": 1,
        "status": "PASS",
        "inference_match": true,
        "narrative_job": "...",
        "silent_read": "...",
        "change_from_previous": "...",
        "critic_evidence": "...",
        "staged_action": {
          "subject": "...",
          "action": "...",
          "target_or_object": "...",
          "reaction_or_consequence": "..."
        },
        "pov": {
          "owner": "...",
          "audience_knows": "...",
          "audience_feels": "..."
        },
        "shot": {
          "size": "...",
          "angle": "...",
          "camera_position": "...",
          "focal_subject": "...",
          "story_reason": "..."
        },
        "blocking": {
          "hands": "...",
          "gaze": "...",
          "body_distance": "...",
          "posture_or_feet": "..."
        },
        "setting": {
          "sub_location": "...",
          "time": "...",
          "motivated_light": "...",
          "story_trace": "..."
        },
        "story_evidence": [
          {"carrier": "...", "observable_state": "...", "narrative_job": "..."}
        ],
        "text_image_relationship": "interdependent",
        "continuity": {"incoming_state": "...", "outgoing_state": "..."},
        "entity_contract": {
          "expected_people": 2,
          "background_people": [],
          "reflections": [],
          "forbidden_entities": []
        },
        "unresolved_ambiguities": [],
        "resolved_ambiguities": [
          {
            "competing_read": "...",
            "repair": "...",
            "recheck_evidence": "..."
          }
        ]
      }
    ],
    "issues": []
  }
}
```

Allowed `sequence_mode` values:

- `causal_sequence`
- `montage_with_arc`
- `reel_sequence`
- `single_image`

Allowed `text_image_relationship` values:

- `additive`
- `counterpoint`
- `interdependent`

For a route with no meaningful recurring object, use an empty
`object_motif_ledger` plus a concrete `no_object_motif_reason`. Do not invent a
prop to satisfy the schema.

The source fingerprint covers slide number, exact copy, role, visual, emotion,
and continuity lock. `format_contract_fingerprint` binds the Event A result to
the request-derived canvas set. `creator_correction_fingerprint` binds all
current correction artifacts, including an empty state, and
`generation_payload_fingerprint` binds the complete parsed `prompt-pack.json`
that will feed generation. Obtain and verify all four from current package
state; any affected creator correction or prompt-pack mutation makes the old
review stale. Supported
format IDs are `instagram_post`, explicit `reels_stories`, and explicit
`square`. Never infer formats from existing folders.

`blind_cards` is the literal Event A payload. It may contain only observable
fields from the example—never copy, theme, narrative-job/POV labels, story
reasons, intended inference, or scores. Its fingerprint makes later mutation
visible. A provisional pre-copy board may guide drafting, but `copy_locked`
cannot be true and Event A cannot pass until exact copy or a text exception and
the request-derived format contract are locked, then the blind read is rerun.

`review_provenance.input_fingerprint` must equal `blind_input_fingerprint`.
Persist exactly one critic response source: literal `raw_response`, or a
package-relative `raw_response_artifact`. The latter must be a current readable
UTF-8 regular file inside the package with no traversal, absolute path, or
symlink component. `raw_response_fingerprint` must match the exact selected
source. Task/run IDs without verifiable response evidence cannot pass.
`output_fingerprint` binds the structured Event A review/reconciliation output.
Author and Event A reviewer task IDs must differ, and their run IDs must differ.
These orchestration fields provide auditable execution provenance, not
cryptographic proof of a person's identity; arbitrary string labels do not
establish independence.

Compute `director_event_fingerprint` only after the Event A object is complete.
`director-event/v2` fingerprints the entire `director_storyboard` object except
the fingerprint value itself, including locks, source/blind hashes, cards,
slides, staging, ledgers, critic output/provenance, issues, and final status.
Changing any of them invalidates Event B.

Record a competing interpretation when the critic reports it. After repairing
and rerunning the blind read, move a cleared interpretation into
`resolved_ambiguities` with recheck evidence. `unresolved_ambiguities` must be
empty for PASS.

## Event B: `visual-qa.json`

Add `checks.visual_story_readability`. Keep every existing QA check.

```json
{
  "status": "PASS",
  "checks": {
    "visual_story_readability": {
      "pass": true,
      "status": "PASS",
      "event": "rendered_frame_story_audit",
      "image_first": true,
      "reviewer_id": "rendered-editor-02",
      "reviewer_evidence": "A second critic inspected the current decoded frame pixels before receiving the board, copy, or director intent.",
      "review_provenance": {
        "schema_version": "visual-review-provenance/v2",
        "reviewer_task_id": "orchestrated-event-b-task-id",
        "reviewer_run_id": "orchestrated-event-b-run-id",
        "input_fingerprint": "sha256:...",
        "raw_response": "Literal image-first critic response before director intent or copy reveal.",
        "raw_response_fingerprint": "sha256:...",
        "output_fingerprint": "sha256:..."
      },
      "source_director_event_fingerprint": "sha256:...",
      "reviewed_native_formats": ["instagram_post"],
      "sequence_read": "...",
      "relationship_turn": "...",
      "setup_payoff_evidence": "...",
      "weakest_frame": "...",
      "repair_decision": "...",
      "frames": [
        {
          "slide": 1,
          "format": "instagram_post",
          "file": "final/slide-01.png",
          "status": "PASS",
          "expected_silent_read": "...",
          "observed_image_first_read": "...",
          "core_action_legible": true,
          "relationship_turn_legible": true,
          "focal_hierarchy": "...",
          "hands_gaze_prop_legible": true,
          "storyboard_match": true,
          "native_format_readability": true,
          "copy_visual_contradictions": [],
          "unexpected_story": [],
          "match_rationale": "...",
          "evidence": "Specific visible evidence from the rendered file.",
          "image_fingerprint": "sha256:..."
        }
      ],
      "issues": []
    }
  }
}
```

Create one frame record per slide per format in the current format contract.
The default is `instagram_post` only when the creator did not specify a canvas;
include `reels_stories` or `square` only when explicitly requested, and include
multiple formats only when each was locked. Resolve the set with
`locked_formats` and each canonical package-local file/dimension pair with
`expected_frame_bindings`. Do not discover intent from `final*` folders.

Each frame's `file`, format, slide number, and current `image_fingerprint` must
match its expected binding. Dimensions are decoded from the current pixels and
compared with the canonical format contract; they are not self-declared by the
reviewer. Reject external paths, path traversal, symlink escapes, duplicate
files, wrong extensions, undecodable images, missing files, and wrong
dimensions even when their names look right.
`review_provenance.input_fingerprint` must equal the computed image-first
manifest fingerprint. As in Event A, exactly one inline response or safe
package-relative response artifact is required and its current contents must
hash-match. `source_director_event_fingerprint` must equal the current complete
Event A fingerprint, whose correction and generation-payload bindings are also
compared with current package state. Event B reviewer task/run IDs must each be
pairwise distinct from the author and Event A reviewer provenance.

A passing proof review may be recorded separately as working notes, but do not
claim full Event B PASS until all locked slide/format assets exist and the
critic has inspected their decoded pixels. A prompt, filename, folder,
generator report, or prior review can never supply Event B evidence.

## Legacy-package migration

Read [legacy-package-migration.md](legacy-package-migration.md) before touching
an older package. Legacy records may support diagnosis but cannot inherit or be
translated into PASS. Lock current copy and formats, rerun Event A and Event B
with new provenance, and bind current expected assets; never synthesize missing
critic evidence.

## What code can and cannot prove

The checker blocks:

- absent or vague structured evidence;
- missing, duplicate, or unresolved slide records;
- one repeated narrative job or unmotivated shot-size repetition;
- missing setup/payoff logic;
- stale slide/copy, format-contract, director-event, review-input/output, raw
  response, or image fingerprints;
- absent orchestration provenance or non-distinct author/Event A/Event B
  task/run pairs (provenance is auditable evidence, not identity proof);
- absent or unrequested native-format records, including explicit square;
- any frame not bound to its exact package-local expected path, dimensions,
  decoded image, and current bytes;
- explicit contradictions, unexpected stories, or failed legibility flags;
- PASS status with unresolved issues.

The checker cannot prove that a frame is emotionally brilliant, culturally
specific, or genuinely legible. That is why Event A and Event B must be fresh
semantic review events with concrete evidence.

## Commands

```bash
# Before prompt handoff / generation
venv/bin/python .agents/skills/a-story-direct-visual-story/scripts/check_visual_story.py \
  --carousel-dir output/carousels/YYYY-MM-DD/slug --phase pre

# After all requested native finals and visual QA
venv/bin/python .agents/skills/a-story-direct-visual-story/scripts/check_visual_story.py \
  --carousel-dir output/carousels/YYYY-MM-DD/slug --phase post

# Final combined check
make visual-check CAROUSEL=output/carousels/YYYY-MM-DD/slug PHASE=all
```

Exit code `0` means the selected phase passed. Exit code `1` means it remains
blocked. The command prints JSON suitable for review or automation.
