# Autopublish Closeout Gate Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a safe autopublish closeout gate so Codex sessions can commit and push verified repo changes without manual user pushing.

**Architecture:** Add a focused Python CLI in `scripts/autopublish.py` with pure helper functions for path parsing, risk classification, secret scanning, command planning, and commit message generation. The CLI runs validation gates before staging, committing, and pushing the current branch.

**Tech Stack:** Python standard library, pytest, git CLI, existing wiki health script.

---

### Task 1: Autopublish Safety Tests

**Files:**
- Create: `tests/test_autopublish.py`

- [ ] **Step 1: Write failing tests**

```python
from pathlib import Path

from scripts import autopublish


def test_parse_changed_paths_handles_modified_untracked_deleted_and_renames():
    status = "\n".join(
        [
            " M AGENTS.md",
            "?? scripts/autopublish.py",
            " D old-file.md",
            "R  docs/old.md -> docs/new.md",
        ]
    )

    assert autopublish.parse_changed_paths(status) == [
        "AGENTS.md",
        "scripts/autopublish.py",
        "old-file.md",
        "docs/new.md",
    ]


def test_risky_paths_block_secrets_media_caches_and_logs():
    paths = [
        ".env",
        ".env.local",
        "identity_images/aachu.png",
        "draft_videos/reel.mp4",
        "corpus/raw/2026-05-28.json",
        "output/carousels/2026-05-28/demo/final/slide-01.png",
        "output/carousels/2026-05-28/demo/final-reels-stories/slide-01.png",
        "venv/lib/site.py",
        "tests/__pycache__/x.pyc",
        "logs/2026-05-28-wiki-health.log",
        "scripts/autopublish.py",
    ]

    blocked = autopublish.find_risky_paths(paths)
    blocked_paths = {item.path for item in blocked}

    assert ".env" in blocked_paths
    assert ".env.local" in blocked_paths
    assert "identity_images/aachu.png" in blocked_paths
    assert "draft_videos/reel.mp4" in blocked_paths
    assert "corpus/raw/2026-05-28.json" in blocked_paths
    assert "output/carousels/2026-05-28/demo/final/slide-01.png" in blocked_paths
    assert "output/carousels/2026-05-28/demo/final-reels-stories/slide-01.png" in blocked_paths
    assert "venv/lib/site.py" in blocked_paths
    assert "tests/__pycache__/x.pyc" in blocked_paths
    assert "logs/2026-05-28-wiki-health.log" in blocked_paths
    assert "scripts/autopublish.py" not in blocked_paths


def test_secret_scan_detects_live_tokens_and_ignores_placeholders(tmp_path):
    safe = tmp_path / "safe.env.example"
    unsafe = tmp_path / "unsafe.py"
    safe.write_text(
        "OPENAI_API_KEY=your_openai_key_here\nAPIFY_API_KEY=...\n",
        encoding="utf-8",
    )
    unsafe.write_text(
        "OPENAI_API_KEY = 'sk-" + "abcdefghijklmnopqrstuvwxyz123456'\n"
        "APIFY_API_KEY=apify_api_" + "abcdefghijklmnopqrstuvwxyz123456\n",
        encoding="utf-8",
    )

    findings = autopublish.scan_secret_text(tmp_path, ["safe.env.example", "unsafe.py"])

    assert [finding.path for finding in findings] == ["unsafe.py", "unsafe.py"]
    assert {finding.kind for finding in findings} == {"openai_key", "apify_key"}


def test_validation_commands_include_tests_and_wiki_health():
    commands = autopublish.build_validation_commands("autopublish gate test")

    assert commands == [
        ["venv/bin/python", "-m", "pytest", "-q"],
        [
            "venv/bin/python",
            "scripts/wiki_health.py",
            "--write",
            "--fix-index",
            "--session-note",
            "autopublish gate test",
        ],
    ]


def test_generate_commit_message_prefers_autopublish_scope():
    assert (
        autopublish.generate_commit_message(
            [
                "scripts/autopublish.py",
                "tests/test_autopublish.py",
                "AGENTS.md",
            ]
        )
        == "chore: add safe autopublish closeout"
    )
    assert autopublish.generate_commit_message(["docs/example.md"]) == "docs: update project docs"
```

- [ ] **Step 2: Run tests to verify RED**

Run: `venv/bin/python -m pytest tests/test_autopublish.py -q`

Expected: FAIL because `scripts.autopublish` cannot be imported.

### Task 2: Autopublish CLI

**Files:**
- Create: `scripts/autopublish.py`

- [ ] **Step 1: Implement helper functions**

Implement:

```python
parse_changed_paths(status_text: str) -> list[str]
find_risky_paths(paths: Sequence[str]) -> list[PathBlock]
filter_included_paths(paths: Sequence[str], includes: Sequence[str]) -> list[str]
scan_secret_text(root: Path, paths: Sequence[str]) -> list[SecretFinding]
build_validation_commands(session_note: str) -> list[list[str]]
generate_commit_message(paths: Sequence[str]) -> str
```

- [ ] **Step 2: Run unit tests**

Run: `venv/bin/python -m pytest tests/test_autopublish.py -q`

Expected: PASS.

- [ ] **Step 3: Add CLI orchestration**

Add argument parsing, git status inspection, safety gates, validation commands,
`git add -A`, `git commit`, `git push`, and local log writing.

- [ ] **Step 4: Run dry-run**

Run: `venv/bin/python scripts/autopublish.py --dry-run --session-note "autopublish gate dry run"`

Expected: safety and validation plan printed; no commit or push.

### Task 3: Repo Instructions And Memory

**Files:**
- Modify: `AGENTS.md`
- Modify: `memory/semantic/engineering-workflow-preferences.md`

- [ ] **Step 1: Add AGENTS closeout policy**

Add a section requiring future sessions to run:

```bash
venv/bin/python scripts/autopublish.py --session-note "short summary"
```

at the end of substantial repo work, with explicit block conditions.

- [ ] **Step 2: Update semantic memory**

Record the creator preference that Codex should own safe autopublishing after
verification and should refuse blind pushing.

### Task 4: Verification And Publish

**Files:**
- All files touched by Tasks 1-3.

- [ ] **Step 1: Run targeted tests**

Run: `venv/bin/python -m pytest tests/test_autopublish.py -q`

Expected: PASS.

- [ ] **Step 2: Run full tests**

Run: `venv/bin/python -m pytest -q`

Expected: PASS.

- [ ] **Step 3: Run wiki health**

Run: `venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "Added safe autopublish closeout gate."`

Expected: PASS.

- [ ] **Step 4: Secret scan staged/tracked changes**

Run the repository secret scan before committing.

Expected: no findings.

- [ ] **Step 5: Commit and push**

Commit message:

```bash
chore: add safe autopublish closeout
```

Push to `origin/main`.
