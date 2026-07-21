# Prevent Public Aachu/Zuv Name Leakage

## Context

The package correctly uses Aachu and Zuv inside identity prompts, visual
direction, and QA. But the public-facing slide copy also says their names. The
creator did not ask for public names.

The repo memory says names may appear in internal notes, visual direction,
identity prompts, and QA artifacts, but public slide copy should usually use
"she", "he", "we", "us", relational language, or universal phrasing unless
the creator explicitly asks otherwise.

## Task

Repair the workflow and tests so public-facing carousel copy does not leak
internal Aachu/Zuv names by default, while preserving internal identity use.

## Acceptance Criteria

- Public slide copy and creator-facing brief avoid Aachu/Zuv unless explicitly
  requested.
- Internal identity prompts and QA still use Aachu/Zuv where needed.
- The checker distinguishes public copy fields from internal production fields.
- Focused creator workflow tests pass.

## Constraints

Do not edit `AGENTS.md`. Do not weaken identity prompting. Do not remove the
actual couple from internal planning. The fix is about public/private boundary,
not making the project generic.
