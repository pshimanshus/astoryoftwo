# ImageGen maintenance implementation

Status: implementation installed and verified offline; live acceptance remains incomplete.

## Baseline and authority

- Original checkout: `/Users/himanshusharma/astoryoftwo-analysis`; do not edit it.
- Task worktree: `/Users/himanshusharma/.codex/worktrees/imagegen-project-review/astoryoftwo-analysis`.
- Baseline commit: `1daf0789` (parent source snapshot `e49720b60b2518732cf6f42ad1f72b436ec12b73`). The three baseline commits contain pre-existing review dependencies, not this task's implementation. Compare implementation against this commit.
- Original source inventory and hashes: `/tmp/asot-imagegen-implementation/baseline-files.json`.
- The user's approved plan is the specification. Preserve four creative gates, zero default carousel agents, exact copy and identity, quarantine, creator approval, retry accounting, normalization, and atomic promotion.
- CLI maintenance is authorized with fake clients only. No credential setup, live API calls, model migration, production publishing, or creator approval is part of this task.

## Frozen integration interfaces

1. An optional `slides.json` entry `image_operation` has `intent: edit` and `targets`, keyed by selected format. Each target has package-relative path, SHA-256, width and height. Missing operation or explicit targetless generate is canonical generation and preserves legacy hashes.
2. `prepare --operation-json PATH` accepts an array of `{slide, intent, targets}` records. Input `targets` map format names to source file paths. Validate all operations before changes; copy edit targets to `.internal/references/edit-targets/<content-hash>.png` before reconciling candidates. Each selected edit format requires exactly one target. Current proof selection/approval rules still apply.
3. Prepared handoff `files[]` entries include `intent`, optional `edit_target_binding`, and derived ordered `input_images`. Generate uses the five canonical reference bindings; edit uses the target first, followed by those same five. The references list remains exactly five; the tool attachment list may be six. No platform-wide image-limit claim.
4. Compiler reads the canonical operation. Add edit-specific instructions within current prompt caps without changing legacy generation prompt bytes. The target is the editable canvas, not identity/style authority. Existing canonical fields and feedback supply change/preserve instructions.
5. `ingest --invocation-json PATH` requires an array of records for ALL new calls: `{slide, format, intent, tool, sent_prompt_sha256, input_images, returned_source_sha256}`. Tool is `image_gen.imagegen`; optional `tool_call_id` and model are included only when exposed. Input records use role, path, SHA-256, and available dimensions from the handoff. Validate exact coverage, per-file prompt hash (not aggregate prompt fingerprint), ordered inputs, current target/reference bytes, and raw returned-image hash before reconciliation or ingestion mutations. Evidence is `operator_recorded`, never independent server attestation.
6. Store compact invocation data in existing attempt/candidate receipts and preserve it through state compaction and finalization. Legacy receipts remain readable and byte-stable without invented evidence. No flag can exempt a fresh return from invocation recording.
7. Target/operation changes affect normal slide input hashes but not the semantic premise fingerprint. They do not reset the two-attempt budget. Proof edits revoke approval; other edits retain unrelated hidden candidates.

## Ownership and dependencies

| Owner | Exclusive implementation scope | Interface dependency |
|---|---|---|
| Shared worker | `tools/imagegen-skill-patch/`, its new dedicated tests | Installed skill is read-only until root applies reviewed patch |
| Runtime worker | generation inputs/state/package writer/builtin runtime, carousel CLI, new operation tests | Canonical operation and handoff above |
| Workflow worker | prompt compiler, project instruction surfaces, maintenance skill, registry, prompt/registry tests | Reads operation field; does not edit runtime/CLI |
| Coordinator | existing ingestion fixtures, benchmark caller, integration, independent verification, live smoke/report, installation, final task report | Reviews all components before install |

Workers share the worktree. Do not revert another worker's edits; sequence shared-file changes through the coordinator. Use bounded helpers and no standing agent room or new production evidence ledger.

## Acceptance

- Offline patch-manager and CLI tests, focused runtime/QA/normalization/lifecycle tests, independent adversarial review, and blind routing/tool-boundary scenarios.
- Install one patched shared skill with drift checks, backup, and guarded rollback.
- At most three live built-in calls: one generation proof, one separate copied-parcel edit with six inputs, and one optional retry for that edit premise.
- Record request acceptance, actual-pixel validity, and creator approval independently. A failed live call or visual repair remains incomplete and must not be hidden by fixture tests.

## Progress

- Baseline: current-source planning checks passed 54 tests; worktree snapshot committed separately.
- Implementation: workers delivered; independent adversarial suite passed 60 cases with no remaining P1/P2 finding. Source, CLI and lifecycle integration tested separately from pre-existing baseline failures.
- Shared installation: patch applied and every allowlisted installed hash verified; backup and rollback receipt retained. Both shared and maintenance skill validators passed.
- Blind behavior: nine cases completed by a fresh agent; exact arguments verified for three fake calls. Six-input fake acceptance is explicitly not a live claim.
- Live generation: five reference inputs accepted, one fresh return ingested with operator-recorded invocation. Independent actual-pixel QA failed the required wrist-accessory check; bound failed QA retained, candidate quarantined, no promotion.
- Live edit: required six-path call rejected before generation: `referenced_image_paths` must contain at most 5 paths. Full inputs retained, no fallback or duplicate retry, no ingested edit attempt.
- Creator approvals: none granted; original production package unchanged.

- Creator correction: prior story/spatial PASS claims withdrawn. Copy-hidden event and shoe/rug contact checks now reject this known negative; the requested three-person delivery handover is captured as the replacement direction, with no new image generated.
