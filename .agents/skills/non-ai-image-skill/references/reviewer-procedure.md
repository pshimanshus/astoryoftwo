# Independent pixel-review procedure

This procedure supplies review evidence to the existing four-gate workflow. It
does not add an approval gate, replace the creator, or claim that a repository
checker saw pixels.

## Select reviewers dynamically

Start every review with a **blind scene reader** who receives the decoded image
and format only. Add specialists only for actual risk:

| Detected risk | Specialist |
| --- | --- |
| Story-critical object, phone, screen, parcel, tool | object-geometry reviewer |
| Touch, carry, pull, or tightly cropped people | anatomy/contact reviewer |
| Door, wall, box, furniture, floor, threshold | spatial-topology reviewer |
| Multiple slides or changing wardrobe/props | continuity reviewer |
| Style complaint, complete deck, or final candidate | finish/text/format reviewer |

For parallel work, each specialist independently records observations, then a
synthesis reviewer compares them with the locked scene. Do not reveal the
intended answer to the blind reader until their silent read is recorded. Do not
call separate reviews “creator approvals”; the creator alone makes that
decision after the existing proof/final QA passes.

## Review one exact asset

1. Open the decoded current pixels at full frame and risk-specific crops. Record
   the path, SHA-256, dimensions, and requested format through the package
   workflow. If pixels cannot be viewed, report `NOT_RUN` or `data_gap` rather
   than writing a visual PASS.
2. **Silent read:** state who appears, what physically happens, what changes,
   and the relationship event visible with copy hidden. This record precedes
   the intended brief.
3. Compare silent read with the locked actor, action, target, consequence,
   chronology, eye-lines, copy, and object state. A semantic miss fails before
   finish review.
4. If human/object or architecture risk applies, trace the full silhouette,
   then each owner -> arm -> wrist -> hand -> target chain. Record allowed
   contact and depth/order at each risky boundary.
5. If identity/continuity risk applies, compare only visible facts with named
   actual references and adjacent images. Record a credible hidden/accessory
   reason instead of inferring an unseen item.
6. Check exact copy, tiny `@a.storyof.two` top-right signature, incidental
   lettering, current style board, and requested native dimensions. Re-review
   separately generated formats separately.
7. Synthesize a result only when every required observation is both current and
   consistent. A specialist conflict, ambiguous body/object boundary, or
   missing pixels is a failure or `data_gap`, never PASS_WITH_NOTES.

## Evidence quality

Good evidence names an observable relation: “Aachu’s right wrist continues from
her sleeve and her fingers wrap the parcel’s top edge; the parcel rests on the
floor mat.” “Looks natural” is not evidence. A reviewer may report that a
phone face is coherent; they must not assert a visual tool or a deterministic
checker independently recognized it.

On changed bytes, invalidate prior visual observations and run the relevant
review roles again. Keep raw specialist notes internal unless a package needs
them as its QA evidence; the stable package record remains hash-bound and uses
the repository's existing schemas.

## Calibration run

Use `regression-manifest.json` as a labeled, finite calibration set. Resolve a
fixture only when its repo-relative path exists and its SHA-256 matches. Mark a
missing or changed fixture unavailable; never silently substitute a lookalike.
Run frozen calibration after any generator, prompt, reference, rule, reviewer,
or procedure change. Then use new creator-labeled assets as fresh holdout.

Report, by family: known-defect misses, counterexample false rejections,
coverage, unavailable fixtures, and `data_gap` count. Calibration success is
evidence about that exact finite set, never proof that future images cannot
fail.
