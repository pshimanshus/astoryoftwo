# HEAL Proposal - Wiki Health

last_updated: 2026-07-21
confidence: 0.78
sources:
- output/diagnostics/wiki-health report
- AGENTS.md architecture contract
- repository filesystem scan

## Hypothesis

Repeated project setup failures are happening because the repo has C-layer carousel quality checks but no repo-wide session-close gate for wiki health, episodic memory, stale index metadata, advertised pipeline drift, or repair proposals.

## Evidence

- No failing checks in the latest run.

## Action

- Keep running the health check at session close.

## Learning

A session should not be considered closed until diagnostics, a HEAL proposal when needed, an episodic record, and a log entry exist.
