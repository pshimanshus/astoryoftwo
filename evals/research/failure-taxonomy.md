# Project Failure Taxonomy

last_updated: 2026-07-04
confidence: 0.82
sources:
- AGENTS.md
- evals/research/sources.json
- pipeline/agentic/workflow_doctor.py
- scripts/autopublish.py
- scripts/wiki_health.py

## Purpose

This taxonomy maps recurring @a.storyof.two agent failures to eval task
families. It separates mechanical contract failures from creative contract
failures so a subjective taste score never hides a broken production gate.

## Mechanical Contract Failures

- Root-contract damage: editing `AGENTS.md` to resolve downstream drift.
- Rule-authority drift: copying stale rule fragments instead of using
  `config/rules/` as canonical source.
- Unsafe closeout: staging `.env`, identity media, generated finals, logs,
  caches, or unrelated mixed-worktree files.
- False finality: claiming publishable images without native assets, visual QA,
  final audit, exact text, identity references, or brandmark evidence.
- Context mutilation: truncating required rule text or dropping hard-fail
  fragments from assembled context or prompts.
- Memory corruption: turning `memory/working.md` into durable memory, omitting
  semantic confidence scores, or deleting episodic records.

## Creative Contract Failures

- Framework-first response: showing rubric terms, score tables, or process
  language before an alive human route.
- Seed erasure: replacing the creator's actual feeling, line, photo, or moment
  with a generic couple trope.
- Text-driven poster spine: visuals become interchangeable if slide copy is
  hidden.
- Relationship-motion collapse: every route becomes "Aachu is chaos, Zuv is
  caretaker" even when the moment needs mutuality, Aachu agency, or no heroic
  actor.
- Visual repetition: same medium two-shot, same room, same posture, same action
  across slides.
- Identity/style drift: text says "same couple" but no actual identity/style
  references guide the whole illustrated person.

## Eval Mapping

Mechanical failures should have deterministic fail-to-pass checkers and
pass-to-pass regression coverage.

Creative failures may need rubric review, but every rubric must name observable
evidence: scene behavior, concrete props, exact seed preservation, format
choice, relationship motion, or visible absence of internal framework language.
