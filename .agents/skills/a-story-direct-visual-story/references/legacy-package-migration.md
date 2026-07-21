# Legacy Visual-Story Package Migration

Use this only when a package predates the current two-event contract. A legacy
package may be inspected, diagnosed, or used as source material. It may not be
promoted, published, or treated as having passed Event A or Event B until fresh
evidence satisfies the current contract.

## Classify before touching evidence

Treat a package as legacy/unverified when any required element is absent or
cannot be reproduced from current files:

- exact copy or documented text-exception lock;
- request-derived format lock from `carousel_format_contract`;
- Event A `review_provenance` and raw pre-reveal critic evidence;
- current creator-correction and complete `prompt-pack.json` fingerprints;
- current `director_event_fingerprint` using `director-event/v2`;
- Event B binding to that complete director-event fingerprint;
- exact expected-asset paths, dimensions, and current image hashes;
- one image-first frame record for every slide/format pair in the lock.

An old `PASS`, `GO`, score, reviewer name, prose audit, or matching folder name
does not satisfy any missing item.

## Safe backfill sequence

1. Preserve the historical files. Do not rewrite their timestamps, reviewer
   claims, or prior result to look current.
2. Resolve the creator's current instruction and correction history. Write the
   locked format set with `write_format_contract`; if the current canvas is
   ambiguous, stop and ask rather than infer from folders.
3. Lock current exact copy (or the documented text exception), slide order,
   roles, and continuity. Mark any older downstream review stale.
4. Reconstruct or repair the observable board from current source facts as a
   new review attempt. Do not label old notes as a copy-hidden read.
5. Start a fresh orchestrated Event A. Persist the literal `blind_cards`, the
   critic's raw pre-reveal response inline or in one safe package-relative
   response artifact, and `review_provenance`. Bind the current correction
   state and complete generation payload. Compute the complete
   `director_event_fingerprint` only
   after the Event A record is final.
6. Resolve the exact expected asset for every locked slide/format pair with
   `expected_frame_bindings`. An existing historical image may continue only if
   that exact package-local file is decodable, its pixels have the expected
   dimensions, and its current hash is recorded; otherwise regenerate the
   requested native asset. Do not add a reviewer-declared dimensions field as a
   substitute for decoding the file.
7. Start a new orchestrated Event B with author, Event A, and Event B task/run
   provenance pairwise distinct. Give the critic the current expected assets
   image-first, preserve its raw pre-reveal response, and bind the result to
   `source_director_event_fingerprint` plus the exact input manifest.
8. Run the visual-story checker and every existing identity, text, anatomy,
   entity, dimensions, brandmark, and final-audit gate. Promotion begins only
   after the current package passes all of them.

## Invalidation rules

- A creator correction to copy, canvas, format set, slide order, role,
  continuity, or story intent invalidates Event A and every Event B result
  derived from it.
- A change to any Event A card, inference, ambiguity repair, staging decision,
  evidence ledger, status, issue, or provenance changes the complete
  `director_event_fingerprint` and invalidates Event B.
- A changed path, image byte, dimension, slide/format assignment, missing file,
  or extra file invalidates the affected Event B asset record. A changed format
  lock invalidates the complete Event B set.
- Moving legacy evidence into a new field without rerunning its semantic event
  does not make it current.

## Never synthesize PASS

Do not fabricate raw critic text, task/run IDs, fingerprints, timestamps, or
asset bindings. Do not split one reviewer into several string labels, infer
independence from names, reinterpret an old narrative note as a blind read, or
copy a previous PASS into the new schema. If orchestration evidence is missing,
rerun the event. If a current requested asset is missing, create and inspect it
before review. Unverifiable history remains `LEGACY_UNVERIFIED`, not PASS.
