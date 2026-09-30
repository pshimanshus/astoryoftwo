# Maintenance acceptance

Use focused offline tests first. For shared skill changes, test drift rejection,
backup and guarded rollback against a temporary fake installation. For runtime
changes, cover current target/reference bytes, ordered inputs, per-file prompt
hashes, raw returned bytes, strict all-new-call coverage, legacy receipt
preservation, retry accounting, proof invalidation, and atomic promotion where
affected. Compiler edits must preserve generation bytes and stay within the
existing 8,000-character / 1,050-word caps without dropping locked content.

For blind forward testing, the coordinator may select realistic prompts from
`tests/fixtures/imagegen_maintenance_forward_prompts.json`. Give a fresh agent
only the selected prompt, the relevant skill, and minimum raw fixture/artifact
paths. Run in an isolated temporary workspace with explicit permitted side
effects. Do not supply grader expectations, suspected defects, proposed fixes,
previous verdicts, or the implementer's interpretation. The separately stored
`tests/fixtures/imagegen_maintenance_forward_expectations.json` is for the
coordinator after the evaluator has returned its actual decisions and artifacts.
The evaluator must not open that file. A routing exercise can return a plan;
a tool-boundary exercise should use a fake tool/fixture and record actual args
when available, rather than merely state that the correct call would be made.

Choose scenarios that exercise the changed behavior. Include ordinary creation
as a negative routing control when maintenance discovery changes; include a
bound edit, stale bytes or input-order failure, and missing invocation record
when the edit/ingest boundary changes. Add a narrow new case only for a real
uncovered risk. Static wording checks alone do not establish behavior.

Root-only installation follows the reviewed patch tool's check, apply, and
rollback guards. Keep its receipt/backup and verify installed bytes. Install
only within existing authorization; an upstream drift failure needs a refreshed
reviewed patch, not force-overwrite. Avoid an approval request until all already
authorized preparation has produced a concrete reviewable patch.

Live calls are separate, scoped acceptance only when authorized. Use the exact
compiled prompt and ordered handoff inputs, inspect edit targets before edits,
and inspect actual returned pixels. Record exposed tool metadata and unexposed
fields honestly. Report request acceptance, visual QA, and creator approval
independently. A runtime attachment rejection stays `handoff_ready` with
`BLOCKED/NOT_RUN`; it does not justify silently dropping an identity reference,
changing the model, using an SDK fallback, or claiming the edit passed.
