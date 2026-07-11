# ASTO-007 Deep Spec - Context Rule Truncation

## Why This Task Exists

Context assembly can create silent failures if required rule text is truncated
after expansion. Dropping a phrase like "HARD FAIL: yellow" or exact text rules
can make a later prompt look compliant while missing the actual constraint. This
task evaluates context safety: the loader should fail loudly rather than
mutilate required rule-included content.

## Starting Fixture

The fixture should build a temporary manifest with a small token budget and a
required section containing `{{rule:palette}}` or another canonical rule include
near the budget boundary. The fail-to-pass behavior is a silent truncated
section, or a rendered context pack that contains a partial rule without an
error. The pass-to-pass behavior is that ordinary context packs still render
with provenance and optional non-rule sections can be truncated with a visible
marker.

## Failure Modes

- Agent simply increases the production budget.
- Agent marks required rule sections optional.
- Agent disables rule include expansion to avoid truncation.
- Agent throws on all truncation, including safe optional sections.
- Agent lets required rules truncate without naming the affected section.

## Checker Design

Use synthetic manifests in tests. The fail-to-pass case expects a specific
exception or validation failure when a required rule-include section would be
cut. The pass-to-pass case covers normal context rendering and optional
truncation behavior. A hidden variant should use a different rule include and
put it after a large preceding section so order and remaining budget matter.

## Anti-Gaming

Forbid production manifest changes that only hide the issue. The checker should
assert rule names appear in the error message, making the failure actionable.
It should also verify that expanded required rules are all-or-nothing, not
half-preserved.

## Severity Model

Critical: required rule content is silently truncated, rule expansion disabled,
or hard-fail fragments disappear. Major: error exists but lacks enough evidence
to repair manifest order or budget. Minor: conservative token estimate noise.
