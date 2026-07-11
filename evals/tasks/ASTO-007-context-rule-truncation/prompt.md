# Issue: Required Rule Text Can Be Truncated

## Context

The Agentic OS context packer expands `{{rule:...}}` includes from
`config/rules/`. If a required section is silently truncated after expansion,
hard-fail fragments such as palette, identity, text, or brandmark rules can
disappear.

## Task

Make required rule-include truncation fail loudly with useful evidence. Optional
sections may still truncate with a clear marker when that is safe.

## Acceptance Criteria

- Required rule-included sections are all-or-error.
- Error messages identify the section and referenced rules.
- Normal default context rendering still works.
- Context loader truncation tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not simply raise the production budget. Do not make
required rule sections optional.
