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


def test_filter_included_paths_limits_mixed_worktree_scope():
    paths = [
        "AGENTS.md",
        "scripts/autopublish.py",
        "scripts/jam_today.py",
        "tests/test_autopublish.py",
        "tests/test_ai_command_center.py",
        "docs/superpowers/specs/2026-05-28-autopublish-closeout-gate-design.md",
    ]

    assert autopublish.filter_included_paths(
        paths,
        [
            "scripts/autopublish.py",
            "tests/test_autopublish.py",
            "docs/superpowers/specs/2026-05-28-autopublish-closeout-gate-design.md",
        ],
    ) == [
        "scripts/autopublish.py",
        "tests/test_autopublish.py",
        "docs/superpowers/specs/2026-05-28-autopublish-closeout-gate-design.md",
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
