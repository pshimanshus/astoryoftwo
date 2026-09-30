# ImageGen maintenance delivery — September 30, 2026

The shared skill upgrade is installed and the project implementation passes
focused offline verification. Live acceptance is **incomplete**: generation
accepted five references but failed pixel QA; editing was rejected because
the current tool accepts at most five local paths and the contract needs six.

## Delivered changes

- The shared ImageGen entrypoint is 102 lines, with selective repair/prompt/CLI
  references. Local paths are attached explicitly; creative intent is separated
  from CLI transport. Model changes and CLI fallback remain explicit choices.
- CLI preflight resolves original and derivative destinations before client
  construction, rejects collisions and image-bearing batch jobs, and preserves
  paid responses/originals in recovery storage before publication. Save failures
  do not repeat image generation. GPT Image 2 remains the default; transparent
  PNG/WebP is documented as preview support.
- Edit targets are snapshotted before reconciliation. Generation retains five
  references; edits add the target first. New ingestion requires exact prompt,
  ordered input and raw-return hashes. Receipts say `operator_recorded`, not
  server-attested. Historical receipt evidence is preserved.
- The discoverable `a-story-imagegen-maintenance` skill and
  `imagegen_maintenance` registry entry dispatch bounded helpers by affected
  subsystem. Ordinary carousel production still has four gates and no default
  helper agents. There is no new service, scheduler or production approval gate.

The reusable entrypoint is
`.agents/skills/a-story-imagegen-maintenance/SKILL.md`. Installation and rollback
instructions are in `tools/imagegen-skill-patch/README.md`. Only the existing
shared skill at `~/.codex/skills/.system/imagegen` was installed; the patch
package itself is not discoverable as a skill.

## Verification

- The original focused baseline reproduced **54 passing tests**.
- The integrated focused regression suite passed **306 tests** in 80.42 seconds,
  covering inputs/state, source normalization, CLI, lifecycle, prompt/compiler,
  registry, patch manager and fake-client CLI recovery. This includes **60**
  independently authored adversarial cases.
- A separate project-surface/workflow run passed **32 tests**, with two unrelated
  existing hook tests excluded. An earlier expanded run exposed the unchanged
  hook assertion about `scripts/agentic_os.py`; no whole-repository health claim
  is made.
- One fresh agent completed **nine held-out behavioral cases** without receiving
  implementation verdicts or expected answers. Three actual fake-tool calls
  preserved exact prompts and ordered inputs. Remaining cases stopped correctly
  or returned bounded maintenance routing. This is a small behavioral sample,
  not a reliability estimate. The reusable fixture set now has 14 scenarios.
- The synthetic benchmark completed one full proof-to-final lifecycle in
  **4.25 seconds**, with no budget violation. Its authored pixels/QA establish
  orchestration only.
- Shared installation hashes, rollback backups and both skill schemas were
  verified. Drift/idempotence/interrupted replacement/rollback were tested in
  temporary installations. No paid CLI call or credential change occurred.

Behavior results: `config/evals/imagegen-maintenance-behavior-report.json`.
Live results: the new `maintenance_upgrade` section in
`config/evals/carousel-live-smoke-report.json`. Historical sections are retained.

## Live evidence and limits

| Check | Request acceptance | Pixels | Creator approval |
| --- | --- | --- | --- |
| New proof, four identities plus style board | Accepted; returned image ingested | FAIL: no delivery interaction or OTP recipient; shoe–rug contact does not pass | Rejected by creator |
| Copied parcel proof, target plus same five references | Rejected before generation: `referenced_image_paths` must contain at most 5 paths | NOT_RUN | Not granted |

Generation returned 1086×1448; the existing allowed single proportional
downsample produced 1080×1440. Hash and normalization measurements remain valid.
The creator subsequently rejected the shoe–rug overlap and the phone shown to
the audience without an in-scene recipient. Earlier story and spatial PASS
claims are withdrawn. Missing bracelet, copy wrapping, label marks and
photographic rendering remain secondary issues. The candidate remains failed
and quarantined; original attempt evidence is retained alongside a corrective
QA artifact whose first failed check is `physical_action`.

The requested replacement is a delivery person handing the parcel to Aachu
while Zuv supplies the OTP to that person. An oblique view from inside the
doorway observes the handover: she reaches to receive the box, the courier still
supports it, and Zuv angles his phone toward the courier. The viewer sees its
back or edge; readable screen content is unnecessary. This replaces the event
and viewpoint. No new image has been generated or approved for this direction.

The review error came from equating prompt compliance and prop presence with
observed storytelling, then inferring shoe contact from a level floor. Review
guidance now requires copy-hidden event/recipient/consequence observation and
explicit shoe–rug–floor ordering. The checker reference also matches the six
runtime checks and v3 schema. No machine-vision detection capability was added.
A fresh reviewer, given the exact image and updated skill without prior QA or
grader answers, rejected physical action, relationship and cinematic meaning
and marked sneaker–mat contact as a data gap. This is a known-image regression,
separate from the original nine held-out behavior cases.

The edit retains all six required inputs and `handoff_ready`, with zero ingested
attempts. The rejected six-path call was not repeated, no reference was dropped,
and no fallback was used. Two built-in requests produced one image. The exposed
tool result did not identify a model or image-call ID, so neither was invented.

Exact call arguments, hashes, input snapshots, blind fake calls and authored QA
are preserved outside the repository at
`/Users/himanshusharma/.codex/tmp/imagegen-maintenance-2026-09-30/`.
New live-smoke output images and isolated input copies are not committed.
The pre-existing project identity/style reference assets are retained in the
separate dependency snapshot commits.

Six-input editing requires a runtime that accepts the full attachment list.
The failed generation requires the new delivery event and viewpoint before
another proof, followed by fresh pixel verification. No current evidence
establishes either capability as production-ready.

## Separation from existing work

Implementation is on `codex/imagegen-maintenance` in the existing task worktree.
Compare it against `1daf0789`. Its three predecessor baseline commits preserve
pre-existing source/evaluation dependencies and hash-bound calibration evidence;
they are not new ImageGen implementation. The baseline source snapshot is
`e49720b60b2518732cf6f42ad1f72b436ec12b73`.

At implementation closeout, all 156 inventoried original source files matched
their captured hashes. Other tasks have since continued work in that checkout;
publication preserves those subsequent changes as well.
The original checkout's uncommitted work and real carousel approval are
untouched. The worktree's local `venv` symlink is interpreter setup only and is
excluded from the implementation commit.

## Publication integration

Before publication, the task branch was merged with `origin/main` at
`ab14d9b0`. Its copy/taste review and non-AI scene contracts were retained
alongside ImageGen invocation and edit evidence. New QA stays on the current
schema even for older packages without an explicit scene contract; archived
legacy evidence remains readable. Scene plans and edit instructions share the
same compiler without changing legacy prompt bytes or raising prompt limits.

Known-negative evaluation metadata now lives only in the coordinator's grader
file, separate from evaluator prompts. The creator's rejected proof remains
failed; publishing this implementation grants no carousel approval.

Full-repository pytest was attempted and stopped during collection: the active
environment lacks FastAPI, backend test collection shadows the project
`tests.helpers` package, and the captured baseline includes a token-budget test
whose `build_stage_system_prompts` dependency is absent. These are separate
from the focused ImageGen/carousel integration checks.

Publication verification covered 417 focused regression cases. The combined run
passed 416 while one newly authored final-QA fixture was still being corrected
to use the actual hidden final-audit directory. After that fixture correction,
all 47 pixel-QA and visual-checker cases passed on the final files, including
the previously failing case. No production check was relaxed. Independent
review caught the new-QA schema downgrade before publication. Wiki health,
outgoing whitespace, scoped secret/risky-path checks, and installed patch
hashes also passed. The original dirty checkout was not staged or committed.
