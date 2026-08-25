# End-To-End Project Sequence

last_updated: 2026-07-11

This is the factual end-to-end execution sequence for this repo, including the
eval harness. It is a single sequence diagram. It does not describe every helper
function; it shows the repo-level control flow, gates, artifacts, and closeout.

```mermaid
sequenceDiagram
    autonumber
    actor User as Creator / Checker
    participant Codex as Codex Agent
    participant Normalizer as Prompt Normalizer<br/>~/.codex/prompting/codex_prompt_normalizer.md
    participant Router as AGENTS.md<br/>repo router
    participant Git as Git Worktree
    participant Rules as config/rules/*
    participant Skills as config/skill-systems.json<br/>config/skills/*<br/>.agents/skills/*
    participant AgenticOS as scripts/agentic_os.py<br/>pipeline/agentic/*
    participant Make as Makefile / CLI
    participant Pipeline as scripts/* workflow entrypoints<br/>pipeline/stages/*
    participant Tests as tests/*<br/>pytest
    participant Artifacts as output/*
    participant MemoryWiki as memory/*<br/>wiki/*
    participant WikiHealth as scripts/wiki_health.py<br/>pipeline/stages/wiki_health.py
    participant Autopublish as scripts/autopublish.py
    participant Evals as evals/runner.py
    participant EvalTasks as evals/registry.json<br/>evals/tasks/*
    participant EvalCheckers as evals/checkers/*
    participant Report as JSON / diagnostics / commit gate

    User->>Codex: Send repo task, creative request, closeout request, or eval request
    Codex->>Normalizer: Normalize prompt into goal, context, constraints, done_when
    Normalizer-->>Codex: Internal task brief
    Codex->>Router: Read project contract and routing rules
    Router-->>Codex: Source truth, precedence, forbidden actions, done criteria
    Codex->>Git: git status --short before substantial edits
    Git-->>Codex: Mixed worktree state and changed paths

    alt Normal repo work
        Codex->>Rules: Load canonical rule layer when behavior touches creative contract
        Rules-->>Codex: palette, identity, text, brandmark, dimensions, voice, memory rules
        Codex->>Skills: Select workflow system by task type
        Skills-->>Codex: carousel_jam, story_article, prepost_reel, or wiki_health components
        Codex->>AgenticOS: Load context, skill system, health, recall, or package doctor when needed
        AgenticOS-->>Codex: Context sections, skill registry, memory search, doctor results, health status

        alt Daily brief
            Codex->>Make: make brief
            Make->>Pipeline: scripts/daily_creator_brief.py
            Pipeline->>MemoryWiki: Read memory, wiki, references, diagnostics
            Pipeline-->>Codex: Creator/engineering brief
            Codex-->>User: Brief result
        else Carousel jam or package
            Codex->>Make: make jam or make carousel
            Make->>Pipeline: scripts/jam_today.py or scripts/carousel.py create
            Pipeline->>Skills: Use carousel_jam components and source references
            Pipeline->>Rules: Enforce identity, on-image text, dimensions, brandmark, visual variety, voice
            Pipeline->>Artifacts: Write minimal v3 package and selected compiled prompt
            Artifacts-->>Pipeline: draft, blocked, or handoff_ready
            alt handoff_ready and Codex image tools available
                Codex->>Artifacts: Read prompt plus four identity bindings and one canonical style-board binding
                Codex->>Codex: Attach those five actual files and call image generation for selected slides
                Codex->>Pipeline: Ingest untouched source; bind source hash and dimensions
                opt exact-3:4 post source is larger than 1080x1440 and at most 1440x1920
                    Pipeline->>Artifacts: Proportionally downsample once to exact 1080x1440
                end
                Codex->>Artifacts: Open decoded normalized candidate pixels with view_image
                Codex->>Pipeline: scripts/carousel.py review with hash/dimension-bound observations
                Pipeline->>Artifacts: proof_qa_required, proof_failed, awaiting_creator_proof_approval, batch_ready, final_qa_required, or final_qa_failed
                Codex->>Pipeline: scripts/carousel.py approve / finalize when eligible
                Pipeline->>Artifacts: Atomically promote a complete audited deck
                Artifacts-->>Codex: publish_ready
            else image generation or pixel viewer unavailable
                Codex-->>User: handoff_ready with BLOCKED/NOT_RUN; no generated or QA claim
            end
            Codex->>AgenticOS: workflow_doctor and carousel_state read-only checks when needed
            AgenticOS-->>Codex: Canonical package state and one next action
            Codex-->>User: Package state, blocker, or publish-ready summary
        else Pre-post Reel analysis
            Codex->>Make: make prepost
            Make->>Pipeline: scripts/analyze_prepost.py
            Pipeline->>Skills: prepost_reel system and romance story-selling engine
            Pipeline->>Rules: voice, story-selling, cultural/taste constraints
            Pipeline->>Artifacts: Write prepost analysis artifacts
            Pipeline->>Tests: tests/test_prepost_story_selling.py when changed
            Tests-->>Codex: pass/fail
            Codex-->>User: POST, REVISE, REWORK, or KILL style result
        else Substack article package
            Codex->>Make: make article CAROUSEL=output/carousels/...
            Make->>Pipeline: scripts/create_substack_article_package.py
            Pipeline->>Skills: story_article system
            Pipeline->>Rules: voice and source-integrity constraints
            Pipeline->>Artifacts: Write article brief, outline, editorial gates, publish package
            Pipeline->>Tests: tests/test_substack_article_package.py when changed
            Tests-->>Codex: pass/fail
            Codex-->>User: Article package status
        else Memory, wiki, or instruction health
            Codex->>Make: make health or direct wiki health command
            Make->>WikiHealth: scripts/run_content_health.py or scripts/wiki_health.py --write --fix-index
            WikiHealth->>MemoryWiki: Read/write wiki index, episodic handoff, diagnostics, heal proposal
            WikiHealth-->>Codex: PASS/FAIL plus diagnostics paths
            Codex->>AgenticOS: scripts/agentic_os.py health when instruction/workflow/context changed
            AgenticOS-->>Codex: health JSON
            Codex-->>User: Health status and changed artifacts
        end

        opt Substantial session closeout
            Codex->>Tests: Run focused pytest commands for touched surfaces
            Tests-->>Codex: pass/fail
            Codex->>AgenticOS: scripts/agentic_os.py health for instruction/workflow/memory/context changes
            AgenticOS-->>Codex: health JSON
            Codex->>WikiHealth: scripts/wiki_health.py --write --fix-index --session-note ...
            WikiHealth->>MemoryWiki: Write diagnostics and session handoff
            WikiHealth-->>Codex: wiki health PASS/FAIL
            Codex->>Autopublish: make publish-dry-run or scripts/autopublish.py --dry-run --include ...
            Autopublish->>Git: git status --porcelain
            Git-->>Autopublish: changed paths
            Autopublish->>Autopublish: filter includes, preserve closeout artifacts, block risky paths
            Autopublish->>Autopublish: scan secrets and require readable session handoff
            Autopublish-->>Codex: dry-run plan or BLOCKED
            opt User or process explicitly publishes
                Codex->>Autopublish: make publish NOTE=... INCLUDE=...
                Autopublish->>Tests: full pytest and wiki health validation commands
                Tests-->>Autopublish: pass/fail
                Autopublish->>Git: git add selected paths, commit, optional push
                Git-->>Autopublish: commit/push result
                Autopublish-->>Report: closeout log under logs/*
            end
        end
    else Eval suite operation
        User->>Evals: Validate, list, prepare, or check SWE-bench-style tasks
        Evals->>EvalTasks: Load registry and task metadata
        EvalTasks-->>Evals: task.json, prompt.md, deep-spec.md, fixtures, suites
        alt Validate suite
            Evals->>EvalTasks: Validate schema_version, prompts, deep-spec headings, suites
            Evals->>EvalTasks: Validate fail_to_pass, pass_to_pass, fixture paths, checker names
            Evals-->>Report: PASS/FAIL task_count and issues JSON
        else Prepare fixture-backed task
            Evals->>EvalTasks: Select task by id
            Evals->>EvalCheckers: Use evals/fixtures.py safety checks for fixture overlay paths
            EvalCheckers-->>Evals: Reject absolute paths or .. escapes, else materialize overlay
            Evals->>Git: Apply fixture overlay to isolated repo checkout or scratch directory
            Git-->>Evals: Prepared starting state and .eval/<task>-prompt.md
        else Agent attempts eval task
            Evals-->>Codex: Issue-like prompt from evals/tasks/<task>/prompt.md
            Codex->>Router: Follow AGENTS.md and current task prompt
            Codex->>Rules: Preserve config/rules authority
            Codex->>Pipeline: Make scoped source/test/docs changes required by task
            Pipeline->>Artifacts: May update allowed task artifacts only
            Codex->>Tests: Run task required commands or focused tests
            Tests-->>Codex: pass/fail
        else Check attempted task
            Evals->>EvalCheckers: prompt_exists
            Evals->>Git: changed_paths from git status or injected --changed-path
            Git-->>Evals: changed path list
            Evals->>EvalCheckers: diff_guard against allowed_paths and forbidden_paths
            Evals->>EvalCheckers: run named deterministic checkers from task.json
            EvalCheckers->>Rules: brandmark_top_right_rule checks config/rules/brandmark.md
            EvalCheckers->>AgenticOS: carousel_doctor_fixture uses workflow_doctor and carousel_state
            EvalCheckers->>Autopublish: autopublish_safety_fixture uses risky path and secret scanners
            EvalCheckers->>Artifacts: creator_visible_copy checks output/evals/.../creator-brief.md
            EvalCheckers-->>Evals: CheckResult list with status, severity, evidence
            Evals->>Tests: Run required_commands unless --skip-commands
            Tests-->>Evals: command result evidence
            Evals->>Report: score_checks applies pass_criteria
            Report-->>User: resolved true/false, score, summary, checks JSON
        end
    end

    Codex-->>User: Final answer with changed files, validations run, skipped validations, and remaining risk
```

## Source Map

| Flow Area | Repo Surface |
| --- | --- |
| Prompt normalization and repo contract | `AGENTS.md`, `~/.codex/prompting/codex_prompt_normalizer.md` |
| Routine commands | `Makefile` |
| Canonical creative rules | `config/rules/*` |
| Workflow registry | `config/skill-systems.json` |
| Carousel work | `scripts/jam_today.py`, `scripts/carousel.py`, `pipeline/agentic/workflow_doctor.py`, `pipeline/agentic/carousel_state.py` |
| Pre-post Reel work | `scripts/analyze_prepost.py` |
| Article package work | `scripts/create_substack_article_package.py` |
| Agentic OS health/context | `scripts/agentic_os.py`, `pipeline/agentic/*` |
| Wiki and memory health | `scripts/wiki_health.py`, `pipeline/stages/wiki_health.py`, `memory/*`, `wiki/*` |
| Safe closeout | `scripts/autopublish.py` |
| Eval harness | `evals/runner.py`, `evals/schemas.py`, `evals/fixtures.py`, `evals/checkers/*`, `evals/tasks/*` |
| Regression tests | `tests/*` |

## Hard Gates Represented

- `AGENTS.md` is the root router; normal downstream fixes should not edit it.
- `config/rules/*` is the canonical creative rule layer.
- Carousel packages require only explicitly requested native outputs, exact
  text, identity/style review, actual-pixel QA, and final audit before
  `publish_ready`. Default is 1080x1440 only.
- Ordinary `make carousel` runs no tests, health checks, network calls, wiki
  writes, memory writes, rule edits, test edits, or diagnostics writes.
- New generation calls attach four curated identity files plus one canonical
  style board. Five is the current built-in runtime's observed smoke boundary,
  not a published-platform limit claim.
- Prompts still request exact targets. Only post ingest may accept an untouched
  exact-3:4 source from 1080x1440 through 1440x1920 and downsample once to exact
  1080x1440. Source bindings remain recorded; Story/Reel and square are
  exact-only; crop, pad, stretch, upscale, wrong ratio, and repeated resampling
  are blocked.
- `memory/working.md` stays pointer-only; durable learning belongs in semantic
  memory and matching rule/skill/test surfaces.
- `scripts/autopublish.py` blocks `.env*`, live-looking secrets, identity media,
  generated final media, logs, caches, and mixed unscoped paths.
- Evals separate mechanical deterministic checks from rubric checks.
- Eval task metadata must include `fail_to_pass`, `pass_to_pass`,
  `allowed_paths`, `forbidden_paths`, required commands, and registered checker
  names.
