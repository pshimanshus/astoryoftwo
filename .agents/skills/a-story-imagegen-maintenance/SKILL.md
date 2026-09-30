---
name: a-story-imagegen-maintenance
description: Diagnose, repair, test, and maintain the shared ImageGen skill and A Story of Two carousel generation/editing integration. Use for workflow bugs, skill drift, invocation evidence, and maintenance acceptance; ordinary carousel creation or a requested image edit stays in its production workflow.
---

# A Story ImageGen Maintenance

A separate maintenance workflow registered as `imagegen_maintenance` in
`config/skill-systems.json`. It does not run during an ordinary `carousel_jam`.

## Scope and dispatch

Normalize the reported behavior, affected system, evidence, and completion
condition. Start in the current task's dedicated worktree; inspect status and
preserve unrelated changes. Read the smallest relevant source and reproduce
the observed failure with offline clients or fixtures first.

Choose helpers from the affected system and observed failure. A coordinator
may run alone for a small repair or use up to four concurrent helpers for
independent work. Do not always assemble a full room. Read
[dispatch.md](references/dispatch.md) when delegating: assign explicit disjoint
file ownership, bounded inputs, output evidence, and dependency order. Reuse
the responsible agent for failures; use a fresh independent agent for blind
acceptance after fixes. The coordinator alone installs a global patch or makes
live image/API calls, and only within the user's actual authorization.

## Boundaries to preserve

- Canonical slide fields and feedback own scene, copy, and change/preserve
  instructions. `image_operation` adds intent and bound targets only.
- Generation keeps five canonical references; edit adds a separate target first
  then those same five. Send the exact compiled prompt and ordered handoff
  inputs. Keep legacy generation prompt bytes unchanged.
- Every new ingest requires invocation records, including generation. Evidence
  is `operator_recorded`, never independent server attestation. Preserve old
  receipts without inventing missing evidence. The detailed schema lives in
  `../astory/references/imagegen-contract.md`; read it only for that boundary.
- Preserve exact copy and identity, quarantine, normalization, hash-bound QA,
  creator approval, two-attempt semantic accounting, and atomic promotion.
- Ordinary carousel production keeps its four gates, empty `agents` list, and
  zero default agents. Add no SDK, scheduler, standing agent room, production
  gate, evidence ledger, or maintenance context to the production hot path.

## Implementation and acceptance

Patch only the surfaces supported by reproduced evidence. Shared skill changes
are carried in `tools/imagegen-skill-patch/`; helpers leave the installed global
skill untouched. The coordinator reviews the candidate patch and uses its
check/apply/guarded-rollback workflow after offline tests pass. Read the patch
tool's own help and contract for exact arguments; never hand-edit the installed
skill to bypass drift checks or a failed rollback guard.

Run focused contract and behavior tests for the changed boundary. Expand only
for unresolved adjacent risks. For substantial changes, read
[acceptance.md](references/acceptance.md) and forward-test realistic requests
with a fresh blind evaluator. Route actionable failures back to their owner,
then repeat affected checks and fresh acceptance; stop when evidence requires
user input, unavailable tooling, or authorization beyond the request.

Report the concrete change, tests and their limits, installation state, and any
remaining issue. Keep tool request acceptance, actual-pixel validity, and named
creator approval as separate claims. A rejected live request or visual failure
remains incomplete even when offline fixtures pass.
