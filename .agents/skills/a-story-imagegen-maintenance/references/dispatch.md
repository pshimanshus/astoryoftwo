# Bounded maintenance dispatch

Read only when work benefits from delegation. Begin with the smallest affected
surface, not a fixed roster. Maximum concurrent team: coordinator plus four
helpers, including an acceptance reviewer. Sequence additional jobs through
existing helpers instead of exceeding that bound.

| Observed issue / affected surface | Suitable bounded owner | Dependency |
| --- | --- | --- |
| Installed ImageGen skill drift or incorrect tool routing | Shared-skill worker: `tools/imagegen-skill-patch/` and its dedicated tests | Capture current installed hashes read-only; implement a candidate before coordinator installation |
| Target bindings, input order, ingest evidence, retry/lifecycle regression | Runtime worker: generation inputs/state/package writer/builtin runtime, `scripts/carousel.py`, benchmark callers, shared ingestion fixtures/tests | Freeze canonical operation/handoff/receipt shape before compiler integration |
| Prompt conflict, instruction mismatch, maintenance routing | Workflow worker: compiler, project skills/docs, registry, prompt/workflow tests | Read runtime interface; preserve generation bytes and single scene/copy authority |
| Independent acceptance of completed change | Fresh read-only reviewer | Wait for integration and focused checks; receive raw scenario and necessary artifacts only |

These are ownership examples, not mandatory roles. A prompt-only bug can need
one owner and one fresh verifier; a docs-only correction may stay with the
coordinator. When a failure spans surfaces, update assignments explicitly
before edits. Tell each worker that others share the worktree, specify files
it may and may not edit, and require it to preserve other workers' changes.
Freeze interfaces before parallel consumers implement them. Sequence shared
files through one owner, and sequence tests after dependent interfaces land.

Workers return changed paths, reproduced behavior, commands/results, and open
interface questions. They do not commit, install globally, approve creator
art, publish, or make live image/API calls on the coordinator's behalf.
Installation and any authorized live call belong to the root coordinator only.
No new orchestration SDK or scheduler is needed: use available bounded agent
calls, messages, and follow-up tasks.

On failure, send the smallest reproducible artifact and failing check to the
existing owner. Do not restart a full room or multiply agents per retry. A
fresh acceptance reviewer must not be the implementer or receive the proposed
fix, suspected bug, prior verdict, or grader expectations. When the agent tool
supports history control, use a fresh context (`fork_turns: none`), not an
inherited implementation conversation. If the concurrency limit is full,
finish/release an implementation slot before fresh acceptance.
The coordinator remains accountable for integration and the final claims.
