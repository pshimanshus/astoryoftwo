# Carousel Autopilot Spine Sprint Implementation Plan

> **⚠️ SUPERSEDED on 2026-05-31** by
> `docs/superpowers/plans/2026-05-31-agentic-os-activation-sprint.md`.
>
> Do not execute this plan as a fresh sprint. Its five P0 items are absorbed
> as sub-goals of the activation plan:
>
> - Workflow Doctor → activation Task 4 (Runner) + Task 10 (Audit)
> - Canonical Prompt Source → activation Task 1 (Rule Consolidation)
>   (✅ landed in commit `33de1f9`, hardened in `ebb3fbf` and `95ffef4`)
> - Handoff Prompt Cleanup → activation Task 5 (Handlers)
> - Final State Contract → activation Task 2 (Typed Contracts)
>   (✅ landed in commit `a96eb56`)
> - 80/20 Final QA → activation Task 3 (Deterministic Gates)
>   (✅ landed in commit `584a968`, hardened in `95ffef4` and `a29fbc2`)
>
> This document is retained for context only. The activation plan is the
> live executable sprint.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the carousel system stop pretending partial handoff states are finished, use one canonical prompt source, and enforce enough executable gates that today’s carousel work becomes reliably smarter, faster, and harder to derail.

**Architecture:** Build the 80/20 spine first: a workflow doctor, a canonical prompt compiler, a single package-state contract, and final-output QA gates. Do not attempt to fully automate image generation in this sprint; instead, make generation state honest and make every downstream artifact derive from verifiable package state. The deeper Agentic OS runner and real agent rooms come after the system can reliably tell draft, blocked, handoff, proof, partial, and publishable states apart.

**Tech Stack:** Python 3, pytest, existing `pipeline/stages/` modules, existing `pipeline/agentic/` package, JSON artifacts, Markdown plans, optional Pillow image inspection if available.

---

## Sprint North Star

The current failure mode is not lack of taste. The repo already knows the desired taste:

- Observational Intimacy Premium watercolor-and-ink style.
- Exact readable on-image text when copy is approved.
- Tiny bottom-right `@a.storyof.two` brandmark.
- Real Aachu/Zuv identity references.
- No yellow/parchment/sepia/heavy cream drift.
- Separate native 4:5 and native 9:16 final outputs.
- Stage-scene proof before quote/poster design.
- Final audit only after real visual QA.

The failure mode is orchestration honesty. The code can still produce `GO`, `PASS`, or `handoff_ready` artifacts while the carousel is actually stale, partial, rejected, or unpublishable.

The fastest valuable sprint is therefore:

1. Detect contradictions.
2. Stop contradictory states from passing.
3. Make prompt generation use exactly one canonical source.
4. Make final QA inspect actual output files, not just metadata.
5. Give parallel sessions narrow tasks so the work can land today.

---

## Pareto Scope

### Must Finish Today

These five items produce roughly 80 percent of the reliability gain:

1. **Workflow Doctor:** scan carousel packages for stale, contradictory, or fake-pass states.
2. **Canonical Prompt Source:** load `config/references/a-story-illustration-master-prompt.md` from disk and compile from that, not a duplicate Python template.
3. **Handoff Prompt Cleanup:** make `.md` handoff files point to the same prompt as `.prompt.txt`; remove competing legacy prompt bodies.
4. **Final State Contract:** derive one canonical package state: `draft`, `blocked`, `copy_locked`, `handoff_ready`, `proof_ready`, `partial_final`, `publishable`.
5. **80/20 Final QA:** verify image count, native dimensions/aspect, stale blocker contradictions, exact expected text recorded, visual QA present, and final audit agreement.

### Should Finish After Must Finish

6. Wire the doctor into `scripts/create_illustration_carousel.py` and `scripts/agentic_os.py`.
7. Add a `carousel doctor` command that can be run before generation and before closeout.
8. Repair status on recent packages using the doctor’s findings.

### Deeper Hardening

9. Real Agentic OS state-machine runner driven by `config/skill-systems.json`.
10. Real multi-agent/council execution or honest deterministic substitute naming.
11. OCR/brandmark/paper-tone/identity visual scoring.
12. Integrated image generation bridge when the environment exposes a callable generator.

---

## Sprint Board

| Lane | Owner Session | Priority | Status | Outcome |
|---|---:|---:|---|---|
| A. Workflow Doctor | Session A | P0 | Ready | Contradictions are detected before anyone trusts artifacts |
| B. Canonical Prompt Source | Session B | P0 | Ready | Prompt compiler uses the real master prompt file |
| C. Handoff Prompt Cleanup | Session B | P0 | Ready | `.md` and `.prompt.txt` cannot disagree |
| D. Final State Contract | Session C | P0 | Ready | One package status replaces scattered stale statuses |
| E. 80/20 Final QA | Session C | P0 | Ready | Partial/non-native/stale packages fail loudly |
| F. CLI Wiring | Session D | P1 | Ready | Doctor can run from command line and Agentic OS |
| G. Recent Package Triage | Session E | P1 | Ready | May 30/31 packages get honest status reports |
| H. Real Runner Design | Session F | P2 | Ready | Next sprint has executable state-machine plan |

---

## File Map

### Create

- `pipeline/agentic/workflow_doctor.py`  
  Scans a carousel package and returns structured issues with severity, code, evidence, and recommended next action.

- `pipeline/agentic/carousel_state.py`  
  Derives one canonical package state from artifacts and doctor issues.

- `scripts/carousel_doctor.py`  
  CLI for inspecting one carousel directory or all recent carousel directories.

- `tests/test_carousel_workflow_doctor.py`  
  Regression tests for contradictory package states.

- `tests/test_carousel_state_contract.py`  
  Regression tests for derived package state.

### Modify

- `pipeline/stages/carousel_master_prompt.py`  
  Replace duplicate hardcoded master template with disk-backed canonical prompt loading.

- `pipeline/stages/carousel_prompt_compiler.py`  
  Compile from the disk-backed prompt and fix path scrubber corruption.

- `pipeline/stages/codex_builtin_image_generation.py`  
  Stop writing a second competing prompt inside `.md` handoff files.

- `pipeline/stages/carousel_quality.py`  
  Consume `carousel_state.py` and fail final audit on state contradictions.

- `scripts/create_illustration_carousel.py`  
  Print honest next action after package creation and handoff preparation.

- `scripts/agentic_os.py`  
  Add a `doctor` or `carousel-doctor` command if the CLI structure supports it cleanly.

### Existing Source Files To Read Before Editing

- `config/references/a-story-illustration-master-prompt.md`
- `config/carousel_style_contract.json`
- `pipeline/stages/carousel_master_prompt.py`
- `pipeline/stages/carousel_prompt_compiler.py`
- `pipeline/stages/codex_builtin_image_generation.py`
- `pipeline/stages/carousel_quality.py`
- `pipeline/stages/carousel_visual_rooms.py`
- `scripts/create_illustration_carousel.py`
- `output/carousels/2026-05-31/private-captions-fresh-a-story/manifest.json`
- `output/carousels/2026-05-30/one-brain-cell-at-home/raw-scene-row.md`

---

## Task 1: Workflow Doctor

**Purpose:** Build a read-only package inspector that catches the contradictions causing most frustration.

**Files:**

- Create: `pipeline/agentic/workflow_doctor.py`
- Create: `tests/test_carousel_workflow_doctor.py`

- [ ] **Step 1: Write failing tests for known contradictions**

Create `tests/test_carousel_workflow_doctor.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.workflow_doctor import inspect_carousel_package


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def issue_codes(report) -> set[str]:
    return {issue.code for issue in report.issues}


def test_flags_raw_scene_rejected_but_generation_allowed(tmp_path: Path) -> None:
    package = tmp_path / "one-brain-cell-at-home"
    package.mkdir()
    (package / "raw-scene-row.md").write_text(
        "STATUS: REJECTED\nGeneration must stop until creator-approved storyboard exists.\n",
        encoding="utf-8",
    )
    write_json(package / "visual-plan-quality.json", {"status": "PASS", "can_generate": True})

    report = inspect_carousel_package(package)

    assert "raw_scene_rejected_but_generation_allowed" in issue_codes(report)
    assert report.highest_severity == "blocker"


def test_flags_handoff_ready_with_final_images_claim(tmp_path: Path) -> None:
    package = tmp_path / "handoff-with-fake-final"
    package.mkdir()
    write_json(package / "image-generation.json", {"status": "handoff_ready"})
    write_json(package / "final-images.json", {"status": "generated", "done": True, "publishable": True})
    (package / "image-generation-blocker.md").write_text(
        "No final PNGs were generated by this CLI run.\n",
        encoding="utf-8",
    )

    report = inspect_carousel_package(package)

    assert "stale_blocker_with_generated_finals" in issue_codes(report)
    assert report.highest_severity == "blocker"


def test_flags_missing_required_c_layer_artifacts_for_fresh_generation(tmp_path: Path) -> None:
    package = tmp_path / "private-captions-fresh-a-story"
    package.mkdir()
    write_json(package / "manifest.json", {"status": "fresh_generation_in_progress"})
    write_json(package / "slides.json", {"slides": [{"slide": 1, "copy": "dumber"}]})
    write_json(package / "visual-plan-quality.json", {"status": "GO"})
    (package / "final-clean").mkdir()

    report = inspect_carousel_package(package)

    assert "missing_prompt_pack" in issue_codes(report)
    assert "missing_visual_debate" in issue_codes(report)
    assert "missing_post_copy_visual_room" in issue_codes(report)
    assert "missing_final_audit" in issue_codes(report)
    assert report.highest_severity == "blocker"


def test_clean_handoff_package_reports_actionable_non_publishable_state(tmp_path: Path) -> None:
    package = tmp_path / "i-have-no-car-i-ll-walk"
    package.mkdir()
    write_json(package / "manifest.json", {"status": "READY_FOR_CODEX_BUILTIN_GENERATION"})
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1, "prompt": "scene"}]})
    write_json(package / "visual-debate.json", {"decision": "GO"})
    write_json(package / "post-copy-visual-room.json", {"decision": "GO"})
    write_json(package / "visual-plan-quality.json", {"status": "PASS", "can_generate": True})
    write_json(package / "image-generation.json", {"status": "handoff_ready"})
    write_json(package / "final-images.json", {"status": "handoff_ready", "done": False, "publishable": False})

    report = inspect_carousel_package(package)

    assert report.highest_severity == "warning"
    assert "handoff_ready_not_publishable" in issue_codes(report)
    assert "missing_prompt_pack" not in issue_codes(report)
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py -q
```

Expected:

```text
ModuleNotFoundError: No module named 'pipeline.agentic.workflow_doctor'
```

- [ ] **Step 3: Implement `workflow_doctor.py`**

Create `pipeline/agentic/workflow_doctor.py`:

```python
from __future__ import annotations

from dataclasses import dataclass, field
import json
from pathlib import Path
from typing import Any


SEVERITY_ORDER = {"info": 0, "warning": 1, "blocker": 2}


@dataclass(frozen=True)
class WorkflowIssue:
    code: str
    severity: str
    message: str
    evidence_path: str
    next_action: str


@dataclass(frozen=True)
class WorkflowDoctorReport:
    package_dir: str
    issues: list[WorkflowIssue] = field(default_factory=list)

    @property
    def highest_severity(self) -> str:
        if not self.issues:
            return "info"
        return max(self.issues, key=lambda issue: SEVERITY_ORDER[issue.severity]).severity

    @property
    def has_blockers(self) -> bool:
        return any(issue.severity == "blocker" for issue in self.issues)

    def to_dict(self) -> dict[str, Any]:
        return {
            "package_dir": self.package_dir,
            "highest_severity": self.highest_severity,
            "has_blockers": self.has_blockers,
            "issues": [issue.__dict__ for issue in self.issues],
        }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {"_invalid_json": True}
    return data if isinstance(data, dict) else {"_non_object_json": True}


def _read_text(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")


def _add(
    issues: list[WorkflowIssue],
    code: str,
    severity: str,
    message: str,
    evidence_path: Path,
    next_action: str,
) -> None:
    issues.append(
        WorkflowIssue(
            code=code,
            severity=severity,
            message=message,
            evidence_path=str(evidence_path),
            next_action=next_action,
        )
    )


def inspect_carousel_package(package_dir: Path) -> WorkflowDoctorReport:
    package_dir = Path(package_dir)
    issues: list[WorkflowIssue] = []

    manifest = _read_json(package_dir / "manifest.json")
    image_generation = _read_json(package_dir / "image-generation.json")
    final_images = _read_json(package_dir / "final-images.json")
    visual_plan_quality = _read_json(package_dir / "visual-plan-quality.json")
    raw_scene = _read_text(package_dir / "raw-scene-row.md").lower()
    blocker = _read_text(package_dir / "image-generation-blocker.md").lower()

    if "rejected" in raw_scene and (
        visual_plan_quality.get("can_generate") is True
        or str(visual_plan_quality.get("status", "")).upper() in {"GO", "PASS"}
    ):
        _add(
            issues,
            "raw_scene_rejected_but_generation_allowed",
            "blocker",
            "Raw scene is marked rejected but visual-plan-quality still allows generation.",
            package_dir / "raw-scene-row.md",
            "Set visual-plan-quality to STOP/BLOCKED and repair storyboard before prompts or generation.",
        )

    if "no final pngs were generated" in blocker and (
        final_images.get("done") is True
        or final_images.get("publishable") is True
        or str(final_images.get("status", "")).lower() in {"generated", "done", "publishable"}
    ):
        _add(
            issues,
            "stale_blocker_with_generated_finals",
            "blocker",
            "A blocker file says no final PNGs exist, but final-images claims generated/publishable output.",
            package_dir / "image-generation-blocker.md",
            "Refresh image-generation and final-images state from actual files, then remove or supersede stale blocker evidence.",
        )

    status = str(manifest.get("status") or image_generation.get("status") or final_images.get("status") or "").lower()
    needs_full_contract = status in {
        "fresh_generation_in_progress",
        "ready_for_codex_builtin_generation",
        "handoff_ready",
        "generated",
        "publishable",
    }

    required_artifacts = {
        "prompt-pack.json": "missing_prompt_pack",
        "visual-debate.json": "missing_visual_debate",
        "post-copy-visual-room.json": "missing_post_copy_visual_room",
        "final-audit.json": "missing_final_audit",
    }
    if needs_full_contract:
        for filename, code in required_artifacts.items():
            path = package_dir / filename
            if not path.exists():
                _add(
                    issues,
                    code,
                    "blocker",
                    f"Package state requires {filename}, but it is missing.",
                    path,
                    f"Create {filename} from the canonical C-layer flow or downgrade this package to manual draft.",
                )

    if image_generation.get("status") == "handoff_ready" or final_images.get("status") == "handoff_ready":
        if final_images.get("publishable") is not True:
            _add(
                issues,
                "handoff_ready_not_publishable",
                "warning",
                "Prompt handoff exists, but final native images are not publishable.",
                package_dir / "final-images.json",
                "Generate/package native 4:5 and native 9:16 images, then run final QA.",
            )

    return WorkflowDoctorReport(package_dir=str(package_dir), issues=issues)
```

- [ ] **Step 4: Run tests and verify pass**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py -q
```

Expected:

```text
4 passed
```

---

## Task 2: Canonical Prompt Source

**Purpose:** Stop the system from having a “final prompt” in docs while code quietly uses another prompt.

**Files:**

- Modify: `pipeline/stages/carousel_master_prompt.py`
- Modify: `pipeline/stages/carousel_prompt_compiler.py`
- Test: `tests/test_carousel_prompt_compiler.py`

- [ ] **Step 1: Add failing tests for disk-backed master prompt**

Append to `tests/test_carousel_prompt_compiler.py`:

```python
from pathlib import Path


def test_compile_image_prompt_preserves_canonical_master_prompt_fragments():
    prompt = compile_image_prompt(
        slide={
            "slide": 1,
            "copy": "dumber",
            "visual": "Aachu at a kitchen doorway, Zuv smiling from inside.",
            "on_image_text": "dumber",
        },
        format_name="instagram_post",
        identity_paths=["identity_images/aachu-zuv-reference.jpg"],
        style_reference_paths=["config/references/style-lock/observational-intimacy-premium/reference.png"],
    )

    canonical = Path("config/references/a-story-illustration-master-prompt.md").read_text(encoding="utf-8")
    required_fragments = [
        "Do not make the paper yellow",
        "Do not use mustard, sepia, tan, parchment",
        "ON-IMAGE TEXT",
        "tiny low-contrast handwritten @a.storyof.two brandmark",
    ]

    for fragment in required_fragments:
        assert fragment in canonical
        assert fragment in prompt


def test_compile_image_prompt_does_not_corrupt_slash_separated_wardrobe_text():
    prompt = compile_image_prompt(
        slide={
            "slide": 5,
            "copy": "she noticed",
            "visual": "Aachu in muted denim/red scarf stands near Zuv in cream/blue layers.",
            "on_image_text": "she noticed",
        },
        format_name="instagram_post",
        identity_paths=["identity_images/aachu-zuv-reference.jpg"],
        style_reference_paths=[],
    )

    assert "muted denim/red scarf" in prompt
    assert "cream/blue layers" in prompt
    assert "denimattached reference image" not in prompt
    assert "scarfattached reference image" not in prompt
```

- [ ] **Step 2: Run tests and verify failure**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -q
```

Expected:

```text
FAIL test_compile_image_prompt_preserves_canonical_master_prompt_fragments
FAIL test_compile_image_prompt_does_not_corrupt_slash_separated_wardrobe_text
```

- [ ] **Step 3: Replace hardcoded master prompt with disk-backed loader**

In `pipeline/stages/carousel_master_prompt.py`, add a loader like this and route prompt construction through it:

```python
from functools import lru_cache
from pathlib import Path


CANONICAL_MASTER_PROMPT_PATH = Path("config/references/a-story-illustration-master-prompt.md")


@lru_cache(maxsize=1)
def load_canonical_master_prompt() -> str:
    prompt = CANONICAL_MASTER_PROMPT_PATH.read_text(encoding="utf-8")
    required = [
        "ON-IMAGE TEXT",
        "@a.storyof.two",
        "Do not make the paper yellow",
        "Do not use mustard, sepia, tan, parchment",
    ]
    missing = [fragment for fragment in required if fragment not in prompt]
    if missing:
        raise ValueError(
            "Canonical master prompt is missing required fragments: "
            + ", ".join(missing)
        )
    return prompt
```

Then update the existing prompt-builder function so its final prompt starts with `load_canonical_master_prompt()` and appends only slide-specific fields:

```python
def build_generation_master_prompt(...):
    master = load_canonical_master_prompt()
    slide_contract = f"""

SLIDE-SPECIFIC CONTRACT
FORMAT: {format_name}
SLIDE NUMBER: {slide_number}
ON-IMAGE TEXT:
{on_image_text}

SCENE:
{scene_summary}

IDENTITY REFERENCES:
{identity_reference_summary}

STYLE REFERENCES:
{style_reference_summary}
"""
    return compact_prompt(master + slide_contract)
```

Use the actual existing parameter names in `build_generation_master_prompt`; do not introduce a second public function unless the current signature makes that unavoidable.

- [ ] **Step 4: Fix path scrubber so it does not corrupt slash-separated prose**

In `pipeline/stages/carousel_prompt_compiler.py`, update path scrubbing so it only removes strings that look like actual file paths:

```python
PATH_MARKERS = (
    "/Users/",
    "output/carousels/",
    "identity_images/",
    "config/references/",
    ".json",
    ".md",
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
)


def looks_like_path_token(token: str) -> bool:
    token = token.strip().strip(".,;:()[]{}")
    return any(marker in token for marker in PATH_MARKERS)
```

Only remove tokens when `looks_like_path_token(token)` is true. Preserve prose such as `muted denim/red scarf`.

- [ ] **Step 5: Run prompt tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -q
```

Expected:

```text
all tests passed
```

---

## Task 3: Handoff Prompt Cleanup

**Purpose:** Prevent `.md` handoff files from showing a different prompt than `.prompt.txt`.

**Files:**

- Modify: `pipeline/stages/codex_builtin_image_generation.py`
- Test: `tests/test_carousel_prompt_compiler.py`

- [ ] **Step 1: Add failing test that handoff markdown does not embed legacy prompt**

Add a test that calls the existing handoff writer or the smallest public function that returns the markdown content. If there is no public function, extract one called `build_handoff_markdown`.

Expected assertions:

```python
def test_handoff_markdown_points_to_prompt_txt_without_second_prompt_body(tmp_path: Path):
    prompt_text = "MASTER PROMPT VERSION\nON-IMAGE TEXT:\ndumber\n"
    markdown = build_handoff_markdown(
        slide_number=1,
        format_name="instagram_post",
        prompt_filename="slide-01.prompt.txt",
        prompt_text=prompt_text,
        reference_paths=["identity_images/aachu-zuv-reference.jpg"],
    )

    assert "Paste the full prompt from `slide-01.prompt.txt`" in markdown
    assert "## Prompt" not in markdown
    assert "ON-IMAGE TEXT:\ndumber" not in markdown
```

- [ ] **Step 2: Implement markdown cleanup**

In `pipeline/stages/codex_builtin_image_generation.py`, make the markdown file contain:

```markdown
## Prompt Source

Paste the full prompt from `slide-01.prompt.txt`. This markdown file intentionally does not duplicate the prompt body, so `.prompt.txt` remains the only generation prompt source.
```

Do not include the older one-paragraph prompt under `## Prompt`.

- [ ] **Step 3: Run prompt and handoff tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -q
```

Expected:

```text
all tests passed
```

---

## Task 4: Canonical Carousel State Contract

**Purpose:** Replace scattered and contradictory package states with one derived state.

**Files:**

- Create: `pipeline/agentic/carousel_state.py`
- Create: `tests/test_carousel_state_contract.py`
- Modify: `pipeline/stages/carousel_quality.py`

- [ ] **Step 1: Write state contract tests**

Create `tests/test_carousel_state_contract.py`:

```python
from __future__ import annotations

import json
from pathlib import Path

from pipeline.agentic.carousel_state import derive_carousel_state


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def test_state_draft_for_missing_core_artifacts(tmp_path: Path) -> None:
    package = tmp_path / "draft"
    package.mkdir()
    write_json(package / "manifest.json", {"status": "fresh_generation_in_progress"})

    state = derive_carousel_state(package)

    assert state.name == "draft"
    assert state.publishable is False
    assert "missing_prompt_pack" in state.issue_codes


def test_state_handoff_ready_for_prompt_package_without_final_images(tmp_path: Path) -> None:
    package = tmp_path / "handoff"
    package.mkdir()
    write_json(package / "manifest.json", {"status": "READY_FOR_CODEX_BUILTIN_GENERATION"})
    write_json(package / "prompt-pack.json", {"slides": [{"slide": 1}]})
    write_json(package / "visual-debate.json", {"decision": "GO"})
    write_json(package / "post-copy-visual-room.json", {"decision": "GO"})
    write_json(package / "visual-plan-quality.json", {"status": "PASS", "can_generate": True})
    write_json(package / "image-generation.json", {"status": "handoff_ready"})
    write_json(package / "final-images.json", {"status": "handoff_ready", "done": False, "publishable": False})

    state = derive_carousel_state(package)

    assert state.name == "handoff_ready"
    assert state.publishable is False


def test_state_blocked_when_doctor_has_blockers(tmp_path: Path) -> None:
    package = tmp_path / "blocked"
    package.mkdir()
    (package / "raw-scene-row.md").write_text("STATUS: REJECTED\n", encoding="utf-8")
    write_json(package / "visual-plan-quality.json", {"status": "PASS", "can_generate": True})

    state = derive_carousel_state(package)

    assert state.name == "blocked"
    assert state.publishable is False
    assert "raw_scene_rejected_but_generation_allowed" in state.issue_codes
```

- [ ] **Step 2: Implement `carousel_state.py`**

Create:

```python
from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path
from typing import Any

from pipeline.agentic.workflow_doctor import inspect_carousel_package


@dataclass(frozen=True)
class CarouselState:
    name: str
    publishable: bool
    issue_codes: list[str]
    next_action: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "publishable": self.publishable,
            "issue_codes": self.issue_codes,
            "next_action": self.next_action,
        }


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return data if isinstance(data, dict) else {}


def derive_carousel_state(package_dir: Path) -> CarouselState:
    package_dir = Path(package_dir)
    doctor = inspect_carousel_package(package_dir)
    issue_codes = [issue.code for issue in doctor.issues]

    if doctor.has_blockers:
        return CarouselState(
            name="blocked",
            publishable=False,
            issue_codes=issue_codes,
            next_action="Resolve workflow doctor blockers before copy, prompt, generation, or closeout.",
        )

    prompt_pack_exists = (package_dir / "prompt-pack.json").exists()
    final_audit = _read_json(package_dir / "final-audit.json")
    final_images = _read_json(package_dir / "final-images.json")
    visual_qa_json = _read_json(package_dir / "visual-qa.json")
    image_generation = _read_json(package_dir / "image-generation.json")

    if final_images.get("publishable") is True and str(final_audit.get("status", "")).upper() in {
        "PASS",
        "PASS_WITH_NOTES",
    }:
        if visual_qa_json or (package_dir / "visual-qa.md").exists():
            return CarouselState(
                name="publishable",
                publishable=True,
                issue_codes=issue_codes,
                next_action="Ready for closeout gate.",
            )

    if final_images.get("status") in {"generated", "partial_final"} or (
        (package_dir / "final").exists() or (package_dir / "final-reels-stories").exists()
    ):
        return CarouselState(
            name="partial_final",
            publishable=False,
            issue_codes=issue_codes,
            next_action="Complete both native formats and run visual QA plus final audit.",
        )

    if image_generation.get("status") == "handoff_ready" or final_images.get("status") == "handoff_ready":
        return CarouselState(
            name="handoff_ready",
            publishable=False,
            issue_codes=issue_codes,
            next_action="Run proof/final generation, package outputs, then run final QA.",
        )

    if prompt_pack_exists:
        return CarouselState(
            name="copy_locked",
            publishable=False,
            issue_codes=issue_codes,
            next_action="Prepare image handoff or generation proof.",
        )

    return CarouselState(
        name="draft",
        publishable=False,
        issue_codes=issue_codes,
        next_action="Create missing C-layer artifacts before generation.",
    )
```

- [ ] **Step 3: Run state tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_state_contract.py tests/test_carousel_workflow_doctor.py -q
```

Expected:

```text
all tests passed
```

- [ ] **Step 4: Wire final audit to fail on blocked state**

In `pipeline/stages/carousel_quality.py`, import `derive_carousel_state` and add a final-audit requirement:

```python
from pipeline.agentic.carousel_state import derive_carousel_state
```

Where final audit requirements are assembled, add:

```python
state = derive_carousel_state(out_dir)
if state.name == "blocked":
    requirements.append(
        {
            "name": "workflow_doctor",
            "passed": False,
            "reason": "Workflow doctor blockers: " + ", ".join(state.issue_codes),
            "next_action": state.next_action,
        }
    )
```

Use the local variable name for the package directory already present in that function.

---

## Task 5: 80/20 Final QA Gate

**Purpose:** Catch the practical issues that caused recent rework: wrong aspect, partial final folders, stale blockers, missing visual QA, and final audit disagreement.

**Files:**

- Create or extend: `pipeline/agentic/workflow_doctor.py`
- Create or extend: `tests/test_carousel_workflow_doctor.py`

- [ ] **Step 1: Add tests for native final completeness**

Append tests:

```python
def test_flags_final_folder_without_reels_folder(tmp_path: Path) -> None:
    package = tmp_path / "partial-final"
    package.mkdir()
    (package / "final").mkdir()
    write_json(package / "final-images.json", {"status": "generated", "done": False, "publishable": False})

    report = inspect_carousel_package(package)

    assert "missing_reels_stories_final_folder" in issue_codes(report)


def test_flags_publishable_without_visual_qa(tmp_path: Path) -> None:
    package = tmp_path / "fake-publishable"
    package.mkdir()
    write_json(package / "final-images.json", {"status": "generated", "done": True, "publishable": True})
    write_json(package / "final-audit.json", {"status": "PASS"})

    report = inspect_carousel_package(package)

    assert "publishable_without_visual_qa" in issue_codes(report)
```

- [ ] **Step 2: Implement completeness checks**

Add to `inspect_carousel_package`:

```python
if (package_dir / "final").exists() and not (package_dir / "final-reels-stories").exists():
    _add(
        issues,
        "missing_reels_stories_final_folder",
        "blocker",
        "Instagram final folder exists but native 9:16 final folder is missing.",
        package_dir / "final-reels-stories",
        "Generate/package separate native 9:16 Reels/Stories images.",
    )

if final_images.get("publishable") is True and not (
    (package_dir / "visual-qa.json").exists() or (package_dir / "visual-qa.md").exists()
):
    _add(
        issues,
        "publishable_without_visual_qa",
        "blocker",
        "Package claims publishable final images without visual QA evidence.",
        package_dir / "visual-qa.json",
        "Run structured visual QA before final audit can pass.",
    )
```

- [ ] **Step 3: Run doctor tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py -q
```

Expected:

```text
all tests passed
```

---

## Task 6: CLI Doctor

**Purpose:** Let every session run one command before trusting a package.

**Files:**

- Create: `scripts/carousel_doctor.py`
- Test: `tests/test_carousel_workflow_doctor.py` or new `tests/test_carousel_doctor_cli.py`

- [ ] **Step 1: Add CLI test**

Create `tests/test_carousel_doctor_cli.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
import subprocess
import sys


def test_carousel_doctor_cli_outputs_json(tmp_path: Path) -> None:
    package = tmp_path / "pkg"
    package.mkdir()
    (package / "raw-scene-row.md").write_text("STATUS: REJECTED\n", encoding="utf-8")
    (package / "visual-plan-quality.json").write_text(
        json.dumps({"status": "PASS", "can_generate": True}),
        encoding="utf-8",
    )

    result = subprocess.run(
        [sys.executable, "scripts/carousel_doctor.py", str(package), "--json"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 2
    data = json.loads(result.stdout)
    assert data["highest_severity"] == "blocker"
    assert data["has_blockers"] is True
```

- [ ] **Step 2: Implement CLI**

Create `scripts/carousel_doctor.py`:

```python
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

from pipeline.agentic.workflow_doctor import inspect_carousel_package


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Inspect A Story of Two carousel package state.")
    parser.add_argument("package_dir", help="Path to one output/carousels package directory.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable report.")
    args = parser.parse_args(argv)

    report = inspect_carousel_package(Path(args.package_dir))
    data = report.to_dict()

    if args.json:
        print(json.dumps(data, indent=2))
    else:
        print(f"Package: {data['package_dir']}")
        print(f"Severity: {data['highest_severity']}")
        for issue in report.issues:
            print(f"- [{issue.severity}] {issue.code}: {issue.message}")
            print(f"  next: {issue.next_action}")

    return 2 if report.has_blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Run CLI tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_doctor_cli.py tests/test_carousel_workflow_doctor.py -q
```

Expected:

```text
all tests passed
```

---

## Task 7: Recent Package Triage

**Purpose:** Produce an honest board for recent carousels so sessions stop treating drafts as finals.

**Files:**

- Create: `output/reports/2026-05-31-carousel-package-triage.md`
- Use: `scripts/carousel_doctor.py`

- [ ] **Step 1: Run doctor on recent packages**

Run:

```bash
venv/bin/python scripts/carousel_doctor.py output/carousels/2026-05-31/private-captions-fresh-a-story --json
venv/bin/python scripts/carousel_doctor.py output/carousels/2026-05-30/one-brain-cell-at-home --json
venv/bin/python scripts/carousel_doctor.py output/carousels/2026-05-30/i-have-no-car-i-ll-walk --json
venv/bin/python scripts/carousel_doctor.py output/carousels/2026-05-30/the-hand-that-stays --json
```

Expected:

- `private-captions-fresh-a-story`: blocker, missing full C-layer/final artifacts.
- `one-brain-cell-at-home`: blocker, rejected raw scene but generation allowed.
- `i-have-no-car-i-ll-walk`: warning or blocker depending missing final audit requirements, not publishable.
- `the-hand-that-stays`: no blocker or only stale-note warning.

- [ ] **Step 2: Write triage report**

Create `output/reports/2026-05-31-carousel-package-triage.md` with:

```markdown
# 2026-05-31 Carousel Package Triage

## Summary

This report was generated after adding the workflow doctor. It separates publishable packages from handoff, partial, draft, blocked, and manual proof packages.

## Package Board

| Package | State | Publishable | Blockers | Next Action |
|---|---|---:|---|---|
| private-captions-fresh-a-story | blocked/draft | no | missing prompt pack, visual debate, final audit | promote through C-layer or keep as manual draft |
| one-brain-cell-at-home | blocked | no | raw scene rejected but generation allowed | repair storyboard and regenerate artifacts |
| i-have-no-car-i-ll-walk | handoff_ready | no | final native sets missing | generate/package final 4:5 and 9:16 |
| the-hand-that-stays | publishable | yes | none or stale note only | closeout-ready |

## Rules Going Forward

- No package can be called final if `derive_carousel_state(...).publishable` is false.
- No image-generation blocker may coexist with generated/publishable final state unless marked superseded.
- No `raw-scene-row.md` rejection can coexist with `visual-plan-quality.can_generate = true`.
- No `fresh_generation_in_progress` folder is a C-layer package until it has the required artifact contract.
```

Update the rows with the exact doctor output after implementation.

---

## Task 8: Agentic OS Runner Design Spike

**Purpose:** Prepare the next sprint without blocking today’s 80/20 fixes.

**Files:**

- Create: `docs/superpowers/specs/carousel-agentic-runner-v2.md`
- Read: `config/skill-systems.json`
- Read: `scripts/agentic_os.py`
- Read: `pipeline/agentic/`

- [ ] **Step 1: Write executable runner spec**

Create `docs/superpowers/specs/carousel-agentic-runner-v2.md`:

```markdown
# Carousel Agentic Runner v2 Spec

## Goal

Turn `config/skill-systems.json` from a registry into an executable state machine for carousel work.

## Required States

1. `session_started`
2. `memory_recalled`
3. `raw_scene_locked`
4. `layer_e_selected`
5. `golden_theme_selected`
6. `stage_scene_passed`
7. `copy_locked`
8. `post_copy_visual_room_passed`
9. `visual_debate_passed`
10. `visual_plan_quality_passed`
11. `identity_review_passed`
12. `prompt_pack_ready`
13. `handoff_ready`
14. `proof_ready`
15. `proof_approved`
16. `native_4x5_generated`
17. `native_9x16_generated`
18. `visual_qa_passed`
19. `final_audit_passed`
20. `publishable`

## State Rules

- A state can only advance when its required artifact exists and its gate returns PASS/GO.
- A later state is invalid if an earlier artifact is edited after it without a recorded rerun.
- Rejection artifacts force state `blocked`.
- Handoff is not generation.
- Partial final output is not publishable.

## First Implementation Slice

The first runner should not call image generation. It should orchestrate all pre-generation gates and stop honestly at `handoff_ready`.
```

- [ ] **Step 2: Do not implement runner in this sprint**

This is intentionally a spec-only track during today’s 80/20 sprint. It prevents scope creep.

---

## Parallel Session Prompts

Use one prompt per fresh Codex session. Each session should create its own worktree or branch before editing. Keep sessions narrow; merge after tests pass.

### Session A Prompt: Workflow Doctor

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 1 and Task 6 from docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md.

Goal:
Create the workflow doctor and CLI that catch contradictory carousel package states.

Scope:
- Create pipeline/agentic/workflow_doctor.py
- Create scripts/carousel_doctor.py
- Create tests/test_carousel_workflow_doctor.py
- Create tests/test_carousel_doctor_cli.py

Do not modify prompt compiler, image generation, memory files, carousel outputs, or existing package artifacts.

Run:
venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py tests/test_carousel_doctor_cli.py -q

Return:
- files changed
- test output
- examples of issues detected for private-captions-fresh-a-story and one-brain-cell-at-home
```

### Session B Prompt: Canonical Prompt Source

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 2 and Task 3 from docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md.

Goal:
Make config/references/a-story-illustration-master-prompt.md the single source of truth for model-native generation prompts, and remove competing prompt text from markdown handoff files.

Scope:
- Modify pipeline/stages/carousel_master_prompt.py
- Modify pipeline/stages/carousel_prompt_compiler.py
- Modify pipeline/stages/codex_builtin_image_generation.py
- Modify tests/test_carousel_prompt_compiler.py

Do not touch carousel outputs, Agentic OS runner code, memory, wiki, or package writer unless a test proves it is required.

Run:
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -q

Return:
- proof the compiled prompt contains canonical yellow/parchment hard-fail language
- proof slash-separated wardrobe text is preserved
- proof handoff markdown has no second legacy prompt body
```

### Session C Prompt: State Contract and Final QA

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Work only on Task 4 and Task 5 from docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md.

Goal:
Create one canonical carousel state contract and make final audit fail when workflow doctor blockers exist.

Scope:
- Create pipeline/agentic/carousel_state.py
- Create tests/test_carousel_state_contract.py
- Extend pipeline/agentic/workflow_doctor.py if Session A has landed; otherwise add a minimal compatible implementation and note the integration point.
- Modify pipeline/stages/carousel_quality.py only where final audit requirements are assembled.

Do not edit prompt compiler, handoff prompt markdown, carousel outputs, memory, or wiki.

Run:
venv/bin/python -m pytest tests/test_carousel_state_contract.py tests/test_carousel_workflow_doctor.py -q

Return:
- state names produced for draft, blocked, handoff_ready, partial_final, publishable
- exact final-audit requirement added
- test output
```

### Session D Prompt: CLI Wiring and Current Flow Messaging

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Wait until Session A has produced scripts/carousel_doctor.py and pipeline/agentic/workflow_doctor.py.

Goal:
Wire honest doctor/state messaging into the creator flow without changing generation behavior.

Scope:
- Modify scripts/create_illustration_carousel.py to print the derived package state after package creation and after handoff prep.
- Modify scripts/agentic_os.py only if its command structure makes a carousel doctor subcommand straightforward.
- Add or update tests around CLI output if existing tests cover create_illustration_carousel CLI behavior.

Do not implement image generation.
Do not call external APIs.
Do not edit output/carousels packages.

Run:
venv/bin/python -m pytest tests/test_agentic_workflow_integration.py tests/test_carousel_workflow_doctor.py -q

Return:
- sample CLI output for a handoff_ready package
- sample CLI output for a blocked package
- test output
```

### Session E Prompt: Recent Package Triage

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:executing-plans.

Wait until Session A has produced scripts/carousel_doctor.py.

Work only on Task 7 from docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md.

Goal:
Create an honest triage report for recent carousel packages so we stop treating drafts, handoffs, and partial finals as complete.

Scope:
- Create output/reports/2026-05-31-carousel-package-triage.md
- Run carousel_doctor.py on:
  - output/carousels/2026-05-31/private-captions-fresh-a-story
  - output/carousels/2026-05-30/one-brain-cell-at-home
  - output/carousels/2026-05-30/i-have-no-car-i-ll-walk
  - output/carousels/2026-05-30/the-hand-that-stays
  - output/carousels/2026-05-30/before-us-timing-found-us

Do not modify any carousel package files.
Do not delete stale blockers.
This is report-only.

Return:
- package board
- exact blockers per package
- next action per package
```

### Session F Prompt: Runner v2 Spec

```text
You are in /Users/himanshusharma/astoryoftwo-analysis.

Use superpowers:using-git-worktrees and superpowers:writing-plans.

Work only on Task 8 from docs/superpowers/plans/2026-05-31-carousel-autopilot-sprint.md.

Goal:
Write a crisp runner-v2 spec for turning config/skill-systems.json into an executable carousel workflow state machine.

Scope:
- Create docs/superpowers/specs/carousel-agentic-runner-v2.md
- Read config/skill-systems.json
- Read scripts/agentic_os.py
- Read pipeline/agentic/

Do not implement runner code.
Do not modify carousel outputs.
Do not modify prompts.

Return:
- spec path
- list of required states
- list of gate invariants
- smallest next implementation slice
```

---

## Recommended Execution Order

### Fastest Today Path

1. Start Session A and Session B immediately in parallel.
2. Start Session C after Session A lands or after it shares the `workflow_doctor.py` interface.
3. Start Session E after Session A lands.
4. Start Session D only after A and C land.
5. Start Session F whenever there is spare capacity; it must not block P0.

### Merge Order

1. Merge Session A first because other tasks depend on doctor interfaces.
2. Merge Session B second because it is isolated and high value.
3. Merge Session C third because it consumes doctor state.
4. Merge Session D fourth because it wires the user-facing CLI.
5. Merge Session E fifth because it is report-only.
6. Keep Session F as a design artifact for the next sprint.

---

## Definition of Done

Today’s sprint is done when:

- `venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py tests/test_carousel_doctor_cli.py tests/test_carousel_state_contract.py tests/test_carousel_prompt_compiler.py -q` passes.
- `scripts/carousel_doctor.py` flags `private-captions-fresh-a-story` as not publishable.
- `scripts/carousel_doctor.py` flags `one-brain-cell-at-home` as blocked if raw scene rejection coexists with generation allowed.
- Prompt compiler preserves canonical master prompt fragments from `config/references/a-story-illustration-master-prompt.md`.
- Handoff markdown no longer embeds a second competing prompt body.
- Final audit cannot pass when `derive_carousel_state(package).name == "blocked"`.
- There is a triage report separating publishable, handoff, partial, draft, and blocked packages.

---

## Anti-Scope-Creep Rules

- Do not build a full image generator in this sprint.
- Do not rewrite all carousel lanes.
- Do not change creative taste or copy standards.
- Do not delete old outputs as a shortcut.
- Do not mark manual proof folders as C-layer packages.
- Do not allow docs-only gates to count as executable gates.
- Do not allow `PASS`, `GO`, or `publishable` unless the state contract agrees.

---

## Closeout

At the end of implementation, run:

```bash
venv/bin/python -m pytest tests/test_carousel_workflow_doctor.py tests/test_carousel_doctor_cli.py tests/test_carousel_state_contract.py tests/test_carousel_prompt_compiler.py -q
venv/bin/python scripts/wiki_health.py --write --fix-index
venv/bin/python scripts/autopublish.py --session-note "Add carousel autopilot workflow doctor, canonical prompt source, state contract, and triage gates"
```

If the worktree contains unrelated carousel outputs, use repeated `--include` flags with `scripts/autopublish.py` for only the files changed by the sprint.
