# Illustration Master Prompt Failure-State Diagnostics

date: 2026-06-30
scope: canonical-only repair evidence

## Decision

Do not mutate historical carousel/concept/output packages as part of this
repair. Old packages remain contradictory in places because they record the
rules that were active when those runs happened. Future agents must trust
`config/rules/`, the current master prompt, and fresh carousel-doctor checks
over stale package-local audits, prompts, visual QA, or memory snapshots.

Before trusting any package status, run:

```bash
venv/bin/python scripts/agentic_os.py carousel-doctor output/carousels/<date>/<slug>
```

## Current Audit Status Counts

Scanned `output/carousels/**/final-audit.json`: 61 files.

| Status | Count |
| --- | ---: |
| NEEDS_FIXES | 32 |
| PASS_WITH_NOTES | 15 |
| BLOCKED | 5 |
| BLOCKED_STYLE_PROOF_REQUIRED | 1 |
| PARTIAL_PROOF_GENERATED | 1 |
| BLOCKED_PROOF_REQUIRED | 1 |
| PARTIAL_PASS_SLIDE_05 | 1 |
| REPAIRED_PROOFS_READY_PENDING_NATIVE_FINALS | 1 |
| BLOCKED_PENDING_PROOF_APPROVAL | 1 |
| BLOCKED_PENDING_CREATOR_PROOF_REVIEW | 1 |
| PASS_VISUAL_QA | 1 |
| GO | 1 |

Scanned `output/carousels/**/final-images.json`: 71 files. Top statuses:
`generated` 16, `handoff_ready` 11, `READY_FOR_CODEX_BUILTIN_GENERATION` 8,
`BLOCKED` 5, `dry_run_generated` 4, `pending_generation` 3, `blocked` 3.

## Recent Stale Rule Examples

- `output/carousels/2026-06-27/one-sec-phone-moment/visual-qa.md` still records
  native `1080x1080` and a tiny bottom-corner brandmark as proof criteria.
- `output/carousels/2026-06-27/one-sec-phone-moment/image-generation-blocker.md`
  asks for a native `1080x1080` proof with the old brandmark placement.
- `output/carousels/2026-06-27/one-sec-phone-moment/final-audit.json` blocks on
  the stale native `1080x1080` proof dimension gate.
- `output/concepts/2026-06-14/roti-bite-rights-jam/rejection-note.md` and
  nearby scratch files preserve the old `1080x1080` proof requirement.
- `output/carousels/2026-06-13/capricorn-man-aries-woman-3/visual-qa.json`
  reports the old brandmark placement as a pass.

## Packages With Only One Native Output Family

Detected packages containing only `final/` or only `final-reels-stories/`, not
both native families:

- `output/carousels/2026-06-11/daily-betrayal-by-my-limbs`
- `output/carousels/2026-06-13/capricorn-man-aries-woman-3`
- `output/carousels/2026-06-13/do-life-with-you-clear-1080-proof`
- `output/carousels/2026-06-13/painful-truths-relationships`
- `output/carousels/2026-06-14/intimacy-he-stays`
- `output/carousels/2026-06-14/intimacy-he-stays-astory-v2`
- `output/carousels/2026-06-15/intimacy-he-stays-astory-final`
- `output/carousels/2026-06-15/intimacy-he-stays-astory-final-variety`
- `output/carousels/2026-06-24/zuv-one-word-direct-generated`
- `output/carousels/2026-06-27/one-sec-phone-moment`
- `output/carousels/2026-06-27/road-hi-galat-hai`

## Wrong-Dimension Publishable Slide Examples

Expected `final/slide-*.png`: `1080x1350`. Detected 9 wrong-dimension final
slides:

- `output/carousels/2026-06-13/capricorn-man-aries-woman-3/final/slide-01.png`
  is `1122x1402`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-01.png`
  is `1003x1568`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-02.png`
  is `1003x1568`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-03.png`
  is `1003x1568`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-04.png`
  is `953x1650`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-05.png`
  is `1004x1567`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-06.png`
  is `968x1625`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-07.png`
  is `1023x1537`.
- `output/carousels/2026-06-13/painful-truths-relationships/final/slide-08.png`
  is `941x1672`.

## Canonical Repair Target

Future generation must use the 2026-06-30 canon:

- default proof, concept, single-slide, and post/carousel output:
  native `1080x1350`;
- explicit Story/Reel companion output: native `1080x1920`;
- square only on explicit request;
- tiny top-right `@a.storyof.two`;
- exact on-image text from the first proof onward;
- no blank source-image/deferred-lettering workflow;
- `PAPER TONE LOCK`, `STAGE-SCENE / VISUAL RECEIPT`,
  `SHOT LADDER / VISUAL VARIETY`, `RELATIONSHIP MOTION`, and Aachu/Zuv
  two-inch height lock in compiled prompts.
