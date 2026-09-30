# ImageGen maintenance patch

This package contains a reviewed unified diff, pinned SHA-256 manifest, patch
manager, and the original CLI test fixture. It is not a discoverable skill and
does not contain `SKILL.md`.

Run from this repository's root with Python 3:

```bash
python3 tools/imagegen-skill-patch/manage.py check
python3 tools/imagegen-skill-patch/manage.py apply
python3 tools/imagegen-skill-patch/manage.py rollback
```

The default installed target is
`/Users/himanshusharma/.codex/skills/.system/imagegen` for this account. To make
the target and backup root explicit, use the same options with each action:

```bash
python3 tools/imagegen-skill-patch/manage.py check \
  --target /Users/himanshusharma/.codex/skills/.system/imagegen \
  --backup-root /Users/himanshusharma/.codex/skill-maintenance-backups/imagegen
```

`check` writes nothing. `apply` verifies the diff, source and target hashes, and
maintenance marker. Only the eight manifest-listed skill files and the managed
`.imagegen-maintenance.json` marker can change. Drift, symlink targets, and
unexpected markers fail closed. An already-applied patch is a no-op. Do not edit
hashes to bypass a baseline mismatch; inspect and rebase the reviewed patch.

Backups live outside skill discovery under
`~/.codex/skill-maintenance-backups/imagegen/imagegen-2026-09-30-v1/<target-hash>/`.
Files use `.before` suffixes; `receipt.json` records the bound target and observed
state. If replacement stops partway through, inspect `check` and the receipt,
then use `rollback`. Guarded rollback validates backups and accepts only the
exact original or patched bytes. It refuses subsequent user edits. Applying and
rolling back preserve unrelated installed files. Individual replacements are
atomic; the whole installation is not a single filesystem transaction.

Offline validation:

```bash
/Users/himanshusharma/astoryoftwo-analysis/venv/bin/python -m pytest -q \
  tests/test_imagegen_skill_patch.py tests/test_imagegen_cli.py
```

These tests reconstruct scratch installations and use fake API clients. They do
not configure credentials, call ImageGen/API services, prove provider acceptance,
assess generated pixels, or grant creator approval. The shared skill's default
CLI model stays `gpt-image-2`; its PNG/WebP transparency is documented as preview
in the [official reference](https://developers.openai.com/api/reference/cli/resources/images/methods/generate),
checked 2026-09-30.

The patched CLI validates all job outputs and derivatives before client creation.
`--dry-run` writes nothing. Live returned responses and originals are saved under
`tmp/imagegen/recovery/response-*` (or `--recovery-dir`) before final promotion.
Local promotion failures retain this folder and do not retry generation. Use
`recovery.json` to see confirmed promotions and whether the complete response was
saved; recover originals locally. If even recovery storage fails, the error says
the complete response could not be saved. Promotion is atomic per file, so some
outputs may already exist when another fails.
