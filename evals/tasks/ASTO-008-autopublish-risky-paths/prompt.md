# Issue: Autopublish Could Stage Risky Local Files

## Context

The repo often has mixed human changes, generated outputs, logs, local secrets,
identity references, and cache files. A closeout gate must not stage everything
just because tests passed.

## Task

Repair autopublish safety so risky files and live-looking secrets are blocked,
while scoped includes still allow legitimate source changes and required
wiki-health closeout artifacts.

## Acceptance Criteria

- `.env*`, identity media, generated finals, logs, caches, and raw risky paths
  are blocked.
- Secret scanning catches live-looking tokens but ignores placeholders.
- Scoped includes preserve closeout artifacts.
- Autopublish tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not turn autopublish into a no-op. Do not remove
the readable session handoff requirement.
