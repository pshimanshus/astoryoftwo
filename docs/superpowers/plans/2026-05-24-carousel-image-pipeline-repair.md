# Carousel Image Pipeline Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the carousel pipeline truthfully move from package creation to image handoff, proof generation, packaging, QA refresh, and publish-ready status without pretending handoff files are final images.

**Architecture:** Split the current mixed workflow into three clear units: state tracking, prompt compilation, and output packaging. Package creation remains deterministic and no-API by default; image generation is either a Codex built-in handoff or an explicit local dry-run backend for tests/previews, with real final status granted only after generated images are packaged and QA is refreshed.

**Tech Stack:** Python 3.13, pytest, pathlib/json dataclass-style helpers, existing C-layer scripts under `scripts/` and `pipeline/stages/`.

---

## File Structure

- Create: `pipeline/stages/carousel_generation_state.py`
  - Owns generation statuses and one helper for writing `image-generation.json` / `final-images.json` without ad hoc strings.
- Create: `pipeline/stages/carousel_prompt_compiler.py`
  - Converts verbose slide metadata into compact paste-ready image prompts and enforces reference/prompt budgets.
- Create: `pipeline/stages/local_dry_run_image_backend.py`
  - Produces deterministic non-photoreal PNGs for tests and flow verification only. It must mark provenance as local dry-run, not Codex built-in final art.
- Modify: `pipeline/stages/codex_native_carousel.py`
  - Stop writing ambiguous `pending_generation` final manifests directly; use the state helper.
  - Keep local preview render state separate from image generation state.
  - Cap style references before prompt pack creation.
- Modify: `pipeline/stages/codex_builtin_image_generation.py`
  - Use compact prompt compiler for `.prompt.txt`.
  - Add slide/format filtering for proof-first generation handoff.
  - Refresh quality artifacts after packaging generated outputs.
- Modify: `scripts/create_illustration_carousel.py`
  - Rename behavior: `--prepare-image-handoff` is the honest path.
  - Keep `--generate-images` as a deprecated alias that prints a warning and behaves like handoff.
  - Add `--proof-slide` and `--proof-format`.
- Modify: `scripts/package_generated_carousel.py`
  - Refresh final audit by default after packaging.
- Move or deprecate: `scripts/render_local_carousel.py`, `scripts/render_carousel_preview.py`, `scripts/render_illustrated_carousel_draft.py`
  - Either move to `scripts/legacy/` or rename so they do not match `*carousel*.py` as active creation paths.
- Modify tests:
  - `tests/test_illustration_carousel.py`
  - Add `tests/test_carousel_generation_state.py`
  - Add `tests/test_carousel_prompt_compiler.py`

Current workspace note: this directory is not a git repository. If implementation happens inside a git/worktree, commit after each task. If not, treat each task boundary as a manual checkpoint.

---

### Task 1: Add Explicit Generation State

**Files:**
- Create: `pipeline/stages/carousel_generation_state.py`
- Test: `tests/test_carousel_generation_state.py`
- Modify: `pipeline/stages/codex_native_carousel.py`

- [ ] **Step 1: Write failing tests for allowed states**

Create `tests/test_carousel_generation_state.py`:

```python
import json
from pathlib import Path

from pipeline.stages.carousel_generation_state import (
    GenerationStatus,
    write_generation_state,
)


def test_write_handoff_ready_state_writes_both_manifests(tmp_path: Path):
    result = write_generation_state(
        tmp_path,
        status=GenerationStatus.HANDOFF_READY,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=2,
        reason="Prompt files are ready; images still pending.",
        extra={"prompt_dir": "codex-image-prompts"},
    )

    assert result["status"] == "handoff_ready"
    assert result["done"] is False
    assert result["requires_human_generation"] is True
    assert json.loads((tmp_path / "image-generation.json").read_text()) == result
    assert json.loads((tmp_path / "final-images.json").read_text()) == result


def test_generated_state_requires_slide_records(tmp_path: Path):
    result = write_generation_state(
        tmp_path,
        status=GenerationStatus.GENERATED,
        backend="codex_builtin",
        generation_mode="model_native_publishable",
        slide_count=1,
        slides=[{"slide": 1, "file": "final/slide-01.png"}],
    )

    assert result["status"] == "generated"
    assert result["done"] is True
    assert result["slides"][0]["file"] == "final/slide-01.png"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_generation_state.py -v
```

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.stages.carousel_generation_state'`.

- [ ] **Step 3: Implement the state helper**

Create `pipeline/stages/carousel_generation_state.py`:

```python
from __future__ import annotations

import json
from enum import StrEnum
from pathlib import Path
from typing import Any


class GenerationStatus(StrEnum):
    DRAFT = "draft"
    HANDOFF_READY = "handoff_ready"
    BLOCKED = "blocked"
    PROOF_READY_FOR_REVIEW = "proof_ready_for_review"
    GENERATED = "generated"
    QA_PASSED = "qa_passed"
    PUBLISH_READY = "publish_ready"


DONE_STATUSES = {
    GenerationStatus.GENERATED,
    GenerationStatus.QA_PASSED,
    GenerationStatus.PUBLISH_READY,
}

HUMAN_GENERATION_STATUSES = {
    GenerationStatus.HANDOFF_READY,
    GenerationStatus.PROOF_READY_FOR_REVIEW,
}


def write_json(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_generation_state(
    carousel_dir: Path,
    *,
    status: GenerationStatus,
    backend: str,
    generation_mode: str,
    slide_count: int,
    reason: str | None = None,
    slides: list[dict[str, Any]] | None = None,
    extra: dict[str, Any] | None = None,
) -> dict[str, Any]:
    carousel_dir.mkdir(parents=True, exist_ok=True)
    result: dict[str, Any] = {
        "status": status.value,
        "backend": backend,
        "generation_mode": generation_mode,
        "slide_count": slide_count,
        "done": status in DONE_STATUSES,
        "requires_human_generation": status in HUMAN_GENERATION_STATUSES,
        "slides": slides or [],
    }
    if reason:
        result["reason"] = reason
    if extra:
        result.update(extra)
    write_json(carousel_dir / "image-generation.json", result)
    write_json(carousel_dir / "final-images.json", result)
    return result
```

- [ ] **Step 4: Run test to verify it passes**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_generation_state.py -v
```

Expected: PASS.

- [ ] **Step 5: Replace initial `pending_generation` writes**

In `pipeline/stages/codex_native_carousel.py`, import:

```python
from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state
```

Replace the `write_json(out_dir / "final-images.json", {"status": "pending_generation", ...})` block inside `write_package(...)` with:

```python
write_generation_state(
    out_dir,
    status=GenerationStatus.DRAFT,
    backend="none",
    generation_mode="not_generated",
    slide_count=len(package["slides"]),
    reason="Carousel package exists, but image handoff has not been prepared.",
    slides=[
        {
            "slide": slide["slide"],
            "copy": slide["copy"],
            "expected_files": {
                "instagram_post": f"final/slide-{slide['slide']:02d}.png",
                "reels_stories": f"final-reels-stories/slide-{slide['slide']:02d}.png",
            },
            "source_prompt_slide": slide["slide"],
        }
        for slide in package["slides"]
    ],
)
```

- [ ] **Step 6: Stop overwriting generation state with preview render state**

In `create_codex_native_carousel(...)`, replace:

```python
write_json(out_dir / "image-generation.json", render_result)
```

with:

```python
write_json(out_dir / "local-preview-render.json", render_result)
```

Keep `render_result` passed into `QualityContext` unchanged for now.

- [ ] **Step 7: Run focused tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_generation_state.py tests/test_illustration_carousel.py::IllustrationCarouselTests::test_codex_native_builder_creates_package_without_anthropic_key -v
```

Expected: PASS.

---

### Task 2: Compile Small Image Prompts

**Files:**
- Create: `pipeline/stages/carousel_prompt_compiler.py`
- Modify: `pipeline/stages/codex_builtin_image_generation.py`
- Test: `tests/test_carousel_prompt_compiler.py`

- [ ] **Step 1: Write failing prompt compiler tests**

Create `tests/test_carousel_prompt_compiler.py`:

```python
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt


def test_compile_image_prompt_removes_file_paths_and_contract_noise():
    prompt = compile_image_prompt(
        slide_number=4,
        slide_count=6,
        slide_copy="He saw. He pretended to sleep.",
        visual="Zuv notices the wallet audit, smiles, and points toward the backup pocket.",
        format_key="instagram_post",
        style="warm hand-drawn desi storybook illustration",
        negative="No photorealism, no 3D, no stock couple.",
    )

    assert "final-images.json" not in prompt
    assert "identity-dossier.json" not in prompt
    assert "/Users/" not in prompt
    assert "He saw. He pretended to sleep." in prompt
    assert "4:5" in prompt
    assert len(prompt) <= 1800


def test_compile_image_prompt_uses_native_format_lock():
    post = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="Some wives don't ask. They audit wallets.",
        visual="Aachu mock-officially opens the wallet while Zuv watches amused.",
        format_key="instagram_post",
        style="warm hand-drawn desi storybook illustration",
        negative="No photorealism.",
    )
    story = compile_image_prompt(
        slide_number=1,
        slide_count=5,
        slide_copy="Some wives don't ask. They audit wallets.",
        visual="Aachu mock-officially opens the wallet while Zuv watches amused.",
        format_key="reels_stories",
        style="warm hand-drawn desi storybook illustration",
        negative="No photorealism.",
    )

    assert "exact 4:5" in post
    assert "exact 9:16" in story
    assert "do not resize from another format" in post.lower()
    assert "do not resize from another format" in story.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement compact prompt compiler**

Create `pipeline/stages/carousel_prompt_compiler.py`:

```python
from __future__ import annotations

import re


FORMAT_COPY = {
    "instagram_post": "Create an exact 4:5 Instagram carousel slide, 1080x1350 if size is available.",
    "reels_stories": "Create an exact 9:16 Reels/Stories slide, 1080x1920 if size is available.",
}


def clean_text(value: str) -> str:
    value = re.sub(r"/(?:[^,\]\n'\"`]+/)+[^,\]\n'\"`]+", "attached reference image", value)
    value = re.sub(r"\b(?:output|config|identity_images)/[^,\]\n'\"`]+", "attached reference image", value)
    value = re.sub(r"\s+", " ", value)
    return value.strip()


def compile_image_prompt(
    *,
    slide_number: int,
    slide_count: int,
    slide_copy: str,
    visual: str,
    format_key: str,
    style: str,
    negative: str,
) -> str:
    if format_key not in FORMAT_COPY:
        raise ValueError(f"Unsupported format_key: {format_key}")

    lines = [
        f"Slide {slide_number:02d} of {slide_count:02d}.",
        FORMAT_COPY[format_key],
        "Use the attached identity and style references as visual inputs.",
        "Do not resize from another format. Generate this canvas natively.",
        "Draw one soft @a.storyof.two scene where Aachu and Zuv behavior carries the joke.",
        f"Scene: {clean_text(visual)}",
        f"Style: {clean_text(style)}",
        "Keep warm off-white paper, imperfect black linework, matte muted colors, expressive recurring faces, and generous negative space.",
        f"Render this exact handwritten text inside the artwork: {slide_copy!r}.",
        "Add the tiny low-contrast handwritten brandmark '@a.storyof.two' at bottom-right.",
        f"Negative: {clean_text(negative)}",
    ]
    prompt = "\n".join(lines).strip() + "\n"
    if len(prompt) > 1800:
        raise ValueError(f"Compiled image prompt is too long: {len(prompt)} characters.")
    return prompt
```

- [ ] **Step 4: Use compiler for `.prompt.txt` generation**

In `pipeline/stages/codex_builtin_image_generation.py`, import:

```python
from pipeline.stages.carousel_prompt_compiler import compile_image_prompt
```

Change `generator_prompt_text(...)` so it loads only the compact fields:

```python
def generator_prompt_text(slide_prompt: dict[str, Any], output_format: str) -> str:
    return compile_image_prompt(
        slide_number=int(slide_prompt["slide"]),
        slide_count=int(slide_prompt.get("slide_count") or 0) or 1,
        slide_copy=str(slide_prompt["text"]),
        visual=str(slide_prompt.get("visual") or slide_prompt.get("scene") or slide_prompt["prompt"]),
        format_key=output_format,
        style=str(slide_prompt.get("style") or "warm hand-drawn desi storybook illustration"),
        negative=str(slide_prompt.get("negative_prompt") or "No photorealism, no 3D, no stock couple, no quote card."),
    )
```

If `slide_count` is not present in existing prompt packs, set it during Task 3.

- [ ] **Step 5: Run prompt tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py -v
```

Expected: PASS.

---

### Task 3: Add Prompt Pack Fields and Reference Budgets

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `config/carousel_style_contract.json`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Add failing test for prompt budget**

Add to `tests/test_illustration_carousel.py`:

```python
def test_codex_native_prompt_pack_has_compact_generation_fields(self):
    with tempfile.TemporaryDirectory() as tmpdir:
        identity = Path(tmpdir) / "identity.jpg"
        identity.write_bytes(b"identity")
        out_dir = create_codex_native_carousel(
            story="She said bas 500. He kept extra there by morning.",
            image_paths=[],
            identity_image_paths=[identity],
            title="Wallet Audit Tiny Test",
            output_root=Path(tmpdir) / "out",
            render_assets=False,
            today=date(2026, 5, 24),
        )

        prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

    assert len(prompt_pack["style_reference_images"]) <= 3
    for slide in prompt_pack["slides"]:
        assert slide["slide_count"] == 5
        assert slide["visual"]
        assert slide["style"]
        assert slide["negative_prompt"]
        assert len(slide["prompt"]) <= 9500
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_codex_native_prompt_pack_has_compact_generation_fields -v
```

Expected: FAIL because `slide_count`, `visual`, `style`, or `negative_prompt` is missing.

- [ ] **Step 3: Cap style references in config**

In `config/carousel_style_contract.json`, reduce `style_references` to the three canonical in-repo references:

```json
"style_references": [
  "output/carousels/2026-05-19/main-kar-lungi/final/slide-01.png",
  "output/carousels/2026-05-19/love-carries-the-heavier-half/final/slide-03.png",
  "output/carousels/2026-05-16/he-learned-her-subtitles/final/slide-02.png"
]
```

Remove `/Users/himanshusharma/Downloads/Generated image *.png` entries from the default style contract. If those files are useful, move them to a curated `style_reference_library/` later, but do not attach them by default.

- [ ] **Step 4: Add compact fields in prompt pack slides**

In `pipeline/stages/codex_native_carousel.py`, inside the `prompt_slides` dict around the existing `slide`, `text`, `generation_mode`, add:

```python
"slide_count": slide_count,
"visual": slide["visual"],
"style": style,
"negative_prompt": contract["shared_negative_prompt"],
```

Also change:

```python
style_reference_paths = contract.get("style_references", [])
```

to:

```python
style_reference_paths = contract.get("style_references", [])[:3]
```

- [ ] **Step 5: Run test to verify it passes**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_codex_native_prompt_pack_has_compact_generation_fields -v
```

Expected: PASS.

---

### Task 4: Make Handoff Explicit and Proof-First

**Files:**
- Modify: `scripts/create_illustration_carousel.py`
- Modify: `pipeline/stages/codex_builtin_image_generation.py`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Add failing test for proof-only handoff**

Add to `tests/test_illustration_carousel.py`:

```python
def test_prepare_codex_handoff_can_write_single_proof_prompt(self):
    from pipeline.stages.codex_builtin_image_generation import prepare_codex_builtin_image_generation

    with tempfile.TemporaryDirectory() as tmpdir:
        identity = Path(tmpdir) / "identity.jpg"
        identity.write_bytes(b"identity")
        out_dir = create_codex_native_carousel(
            story="She said bas 500. He kept extra there.",
            image_paths=[],
            identity_image_paths=[identity],
            title="Proof Only Handoff",
            output_root=Path(tmpdir) / "out",
            render_assets=False,
            today=date(2026, 5, 24),
        )

        result = prepare_codex_builtin_image_generation(
            out_dir,
            proof_slide=4,
            formats=["instagram_post"],
        )

    assert result["status"] == "handoff_ready"
    assert len(result["slides"]) == 1
    assert result["slides"][0]["slide"] == 4
    assert "instagram_post" in result["slides"][0]["prompt_files"]
    assert "reels_stories" not in result["slides"][0]["prompt_files"]
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_prepare_codex_handoff_can_write_single_proof_prompt -v
```

Expected: FAIL because the function does not accept `proof_slide` or `formats`.

- [ ] **Step 3: Extend handoff function signature**

Change function signature in `pipeline/stages/codex_builtin_image_generation.py`:

```python
def prepare_codex_builtin_image_generation(
    carousel_dir: Path,
    *,
    proof_slide: int | None = None,
    formats: list[str] | None = None,
) -> dict[str, Any]:
```

After loading `slides`, filter:

```python
requested_formats = formats or NATIVE_OUTPUT_CONTRACT["formats"]
invalid_formats = sorted(set(requested_formats) - set(NATIVE_OUTPUT_CONTRACT["formats"]))
if invalid_formats:
    raise ValueError("Unsupported output format(s): " + ", ".join(invalid_formats))

if proof_slide is not None:
    slides = [slide for slide in slides if int(slide["slide"]) == proof_slide]
    if not slides:
        raise ValueError(f"Proof slide {proof_slide} is not present in prompt-pack.json.")
```

Change prompt file creation loop to build only `requested_formats`.

- [ ] **Step 4: Use generation state helper in handoff**

At the end of `prepare_codex_builtin_image_generation(...)`, replace direct `write_json(...)` calls with:

```python
result = write_generation_state(
    carousel_dir,
    status=GenerationStatus.HANDOFF_READY,
    backend=BACKEND,
    generation_mode=GENERATION_MODE,
    slide_count=len(load_json(carousel_dir / "prompt-pack.json").get("slides", [])),
    reason="Prompt files are ready; final PNGs still require Codex built-in image generation.",
    slides=records,
    extra={
        "proof_gate": prompt_pack.get("proof_gate"),
        "native_output_contract": NATIVE_OUTPUT_CONTRACT,
        "prompt_dir": str(prompt_dir),
        "identity_reference_requirement": (
            "Load/view identity-face-contact-sheet.jpg and selected identity images before every "
            "Codex image generation call; the final art must preserve Aachu/Zuv face structure."
        ),
    },
)
```

Import `GenerationStatus` and `write_generation_state`.

- [ ] **Step 5: Update CLI flags**

In `scripts/create_illustration_carousel.py`:

Add:

```python
parser.add_argument(
    "--prepare-image-handoff",
    action="store_true",
    help="Prepare Codex built-in prompt handoff files. Does not generate final PNGs.",
)
parser.add_argument(
    "--proof-slide",
    type=int,
    help="Prepare handoff only for one proof slide.",
)
parser.add_argument(
    "--proof-format",
    choices=["instagram_post", "reels_stories"],
    action="append",
    help="Limit proof handoff to one native format. Repeat to include both.",
)
```

Change the existing `--generate-images` help to:

```python
help="Deprecated alias for --prepare-image-handoff. Does not generate final PNGs.",
```

Change the execution condition:

```python
if args.generate_images or args.prepare_image_handoff:
    if args.generate_images:
        print("WARNING: --generate-images is deprecated; preparing handoff only.")
    result = prepare_codex_builtin_image_generation(
        out_dir,
        proof_slide=args.proof_slide,
        formats=args.proof_format,
    )
```

- [ ] **Step 6: Run proof-only handoff test**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_prepare_codex_handoff_can_write_single_proof_prompt -v
```

Expected: PASS.

---

### Task 5: Refresh Final Audit After Packaging

**Files:**
- Modify: `pipeline/stages/codex_builtin_image_generation.py`
- Modify: `scripts/package_generated_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Add failing test for audit refresh**

Add to `tests/test_illustration_carousel.py`:

```python
def test_package_generated_outputs_refreshes_final_audit(self):
    from pipeline.stages.codex_builtin_image_generation import package_codex_builtin_outputs

    with tempfile.TemporaryDirectory() as tmpdir:
        identity = Path(tmpdir) / "identity.jpg"
        identity.write_bytes(b"identity")
        source_root = Path(tmpdir) / "sources"
        source_root.mkdir()
        out_dir = create_codex_native_carousel(
            story="She said bas 500. He kept extra there.",
            image_paths=[],
            identity_image_paths=[identity],
            title="Audit Refresh",
            output_root=Path(tmpdir) / "out",
            render_assets=False,
            today=date(2026, 5, 24),
        )

        instagram = []
        reels = []
        for number in range(1, 6):
            post_path = source_root / f"post-{number}.png"
            reels_path = source_root / f"reels-{number}.png"
            post_path.write_bytes(self.png_bytes(1080, 1350))
            reels_path.write_bytes(self.png_bytes(1080, 1920))
            instagram.append(post_path)
            reels.append(reels_path)

        result = package_codex_builtin_outputs(
            out_dir,
            generated_paths_by_format={
                "instagram_post": instagram,
                "reels_stories": reels,
            },
            refresh_quality=True,
        )

        audit = json.loads((out_dir / "final-audit.json").read_text(encoding="utf-8"))

    assert result["status"] == "generated"
    assert audit["status"] in {"PASS", "PASS_WITH_NOTES"}
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_package_generated_outputs_refreshes_final_audit -v
```

Expected: FAIL because `package_codex_builtin_outputs` does not accept `refresh_quality`.

- [ ] **Step 3: Add quality refresh option**

In `pipeline/stages/codex_builtin_image_generation.py`, change signature:

```python
def package_codex_builtin_outputs(
    carousel_dir: Path,
    *,
    generated_paths: list[str | Path] | None = None,
    generated_paths_by_format: dict[str, list[str | Path]] | None = None,
    refresh_quality: bool = False,
) -> dict[str, Any]:
```

After writing `final-images.json` and `image-generation.json`, add:

```python
if refresh_quality:
    from datetime import date

    from pipeline.stages.carousel_quality import QualityContext, write_quality_artifacts

    manifest = load_json(carousel_dir / "manifest.json")
    package = {
        "concept": load_json(carousel_dir / "concept.json"),
        "slides": load_json(carousel_dir / "slides.json"),
        "visual_plan_quality": load_json(carousel_dir / "visual-plan-quality.json"),
        "prompt_pack": prompt_pack,
        "copy": load_json(carousel_dir / "copy.json"),
    }
    write_quality_artifacts(
        QualityContext(
            story=manifest["source_story"],
            title=manifest["title"],
            slug=manifest["slug"],
            today=date.fromisoformat(manifest["date"]),
            out_dir=carousel_dir,
            image_paths=[Path(item["path"]) for item in manifest.get("reference_images", [])],
            slide_count=len(slides),
            package=package,
            manifest=manifest,
            render_result=result,
            workspace_root=Path.cwd(),
        )
    )
```

- [ ] **Step 4: Make script refresh by default**

In `scripts/package_generated_carousel.py`, add:

```python
parser.add_argument(
    "--no-quality-refresh",
    action="store_true",
    help="Package image files only; do not rerun final audit.",
)
```

Pass:

```python
refresh_quality=not args.no_quality_refresh,
```

through `package_generated_images(...)` to `package_codex_builtin_outputs(...)`.

- [ ] **Step 5: Run audit refresh test**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_package_generated_outputs_refreshes_final_audit -v
```

Expected: PASS.

---

### Task 6: Fix Existing Failing Tests

**Files:**
- Modify: `tests/test_illustration_carousel.py`
- Modify: `pipeline/stages/c1_illustration_carousel.py`
- Modify or move: one-off renderer scripts

- [ ] **Step 1: Fix validation-order test**

Current failure expects `story_selling_score` but package validation fails first on missing `post_copy_visual_room`. Update the test fixture, not the validator, by adding:

```python
"post_copy_visual_room": {"status": "GO", "selected_visual_system": "Tiny Ritual Evidence"},
```

to the package in `test_anthropic_package_validation_requires_story_selling_gate`.

- [ ] **Step 2: Fix final audit acceptance test**

Inspect actual audit issues:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_final_audit_accepts_identity_only_generated_carousel -v
```

If the only failure is missing `backend`, update the test manifest records to include:

```python
"backend": "codex_builtin",
```

on each slide record. This aligns the test with `carousel_quality.py`, which requires approved final-art backends.

- [ ] **Step 3: Move preview-only renderers out of active script glob**

Create:

```bash
mkdir -p scripts/legacy
```

Move:

```bash
mv scripts/render_local_carousel.py scripts/legacy/render_local_carousel.py
mv scripts/render_carousel_preview.py scripts/legacy/render_carousel_preview.py
mv scripts/render_illustrated_carousel_draft.py scripts/legacy/render_illustrated_carousel_draft.py
```

If any tests/imports rely on these files, update imports to point at `pipeline/stages/local_carousel_renderer.py` or `scripts/legacy/...`.

- [ ] **Step 4: Run current failing tests**

Run:

```bash
venv/bin/python -m pytest \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_anthropic_package_validation_requires_story_selling_gate \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_final_audit_accepts_identity_only_generated_carousel \
  tests/test_illustration_carousel.py::IllustrationCarouselTests::test_no_uncontracted_one_off_carousel_generator_scripts \
  -v
```

Expected: PASS.

---

### Task 7: Add a Local Dry-Run Backend for Fast End-to-End Flow Tests

**Files:**
- Create: `pipeline/stages/local_dry_run_image_backend.py`
- Modify: `scripts/create_illustration_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Add failing dry-run test**

Add to `tests/test_illustration_carousel.py`:

```python
def test_local_dry_run_backend_creates_both_native_formats(self):
    from pipeline.stages.local_dry_run_image_backend import generate_local_dry_run_images

    with tempfile.TemporaryDirectory() as tmpdir:
        identity = Path(tmpdir) / "identity.jpg"
        identity.write_bytes(b"identity")
        out_dir = create_codex_native_carousel(
            story="She said bas 500. He kept extra there.",
            image_paths=[],
            identity_image_paths=[identity],
            title="Dry Run Images",
            output_root=Path(tmpdir) / "out",
            render_assets=False,
            today=date(2026, 5, 24),
        )

        result = generate_local_dry_run_images(out_dir)

    assert result["status"] == "generated"
    assert (out_dir / "final" / "slide-01.png").exists()
    assert (out_dir / "final-reels-stories" / "slide-01.png").exists()
    assert result["backend"] == "local_dry_run"
```

- [ ] **Step 2: Run test to verify it fails**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_local_dry_run_backend_creates_both_native_formats -v
```

Expected: FAIL with missing module.

- [ ] **Step 3: Implement deterministic dry-run backend**

Create `pipeline/stages/local_dry_run_image_backend.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import cv2
import numpy as np


INK = (42, 38, 33)
PAPER = (232, 244, 251)


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_png(path: Path, width: int, height: int, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    canvas = np.empty((height, width, 3), dtype=np.uint8)
    canvas[:, :] = PAPER
    cv2.putText(canvas, text[:36], (80, 160), cv2.FONT_HERSHEY_SIMPLEX, 1.2, INK, 3, cv2.LINE_AA)
    cv2.putText(canvas, "@a.storyof.two", (width - 360, height - 80), cv2.FONT_HERSHEY_SIMPLEX, 0.7, INK, 2, cv2.LINE_AA)
    ok, data = cv2.imencode(".png", canvas, [cv2.IMWRITE_PNG_COMPRESSION, 3])
    if not ok:
        raise RuntimeError(f"Could not encode {path}")
    path.write_bytes(data.tobytes())


def generate_local_dry_run_images(carousel_dir: Path) -> dict[str, Any]:
    prompt_pack = load_json(carousel_dir / "prompt-pack.json")
    records: list[dict[str, Any]] = []
    for slide in prompt_pack["slides"]:
        number = int(slide["slide"])
        post = carousel_dir / "final" / f"slide-{number:02d}.png"
        reels = carousel_dir / "final-reels-stories" / f"slide-{number:02d}.png"
        write_png(post, 1080, 1350, slide["text"])
        write_png(reels, 1080, 1920, slide["text"])
        records.append(
            {
                "slide": number,
                "copy": slide["text"],
                "backend": "local_dry_run",
                "generation_mode": "local_dry_run_not_publishable",
                "file": str(post),
                "reels_stories_file": str(reels),
            }
        )
    result = {
        "status": "generated",
        "backend": "local_dry_run",
        "generation_mode": "local_dry_run_not_publishable",
        "slides": records,
    }
    (carousel_dir / "image-generation.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    (carousel_dir / "final-images.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return result
```

Important: this backend is for fast flow tests/previews. It must not satisfy publish-ready final-art gates unless product explicitly chooses to allow local renders as final.

- [ ] **Step 4: Add CLI option**

In `scripts/create_illustration_carousel.py`, change `--image-backend` choices to:

```python
choices=["codex-built-in", "local-dry-run"],
```

After package creation, add:

```python
if args.image_backend == "local-dry-run":
    from pipeline.stages.local_dry_run_image_backend import generate_local_dry_run_images

    result = generate_local_dry_run_images(out_dir)
    print(f"Local dry-run images -> {result['status']}")
```

- [ ] **Step 5: Run dry-run test**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_local_dry_run_backend_creates_both_native_formats -v
```

Expected: PASS.

---

### Task 8: Full Verification

**Files:**
- No new files unless prior tasks reveal missing imports.

- [ ] **Step 1: Run focused carousel suite**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py tests/test_creator_workflow_contract.py tests/test_identity_dossier.py tests/test_carousel_generation_state.py tests/test_carousel_prompt_compiler.py -v
```

Expected: PASS.

- [ ] **Step 2: Run a real handoff smoke test**

Run:

```bash
venv/bin/python scripts/create_illustration_carousel.py \
  --title "Pipeline Repair Smoke Test" \
  --story "She said bas 500. He kept extra there by morning." \
  --identity-image identity_images/aachu_zuv.png \
  --slide-count 5 \
  --prepare-image-handoff \
  --proof-slide 4 \
  --proof-format instagram_post
```

Expected:
- Command prints `handoff_ready`.
- It does not claim final PNGs were generated.
- New package contains one proof `.md` and one proof `.prompt.txt`.
- `final-images.json` status is `handoff_ready`.

- [ ] **Step 3: Run local dry-run smoke test**

Run:

```bash
venv/bin/python scripts/create_illustration_carousel.py \
  --title "Pipeline Dry Run Smoke Test" \
  --story "She said bas 500. He kept extra there by morning." \
  --identity-image identity_images/aachu_zuv.png \
  --slide-count 5 \
  --image-backend local-dry-run
```

Expected:
- `final/slide-01.png` through `final/slide-05.png` exist.
- `final-reels-stories/slide-01.png` through `final-reels-stories/slide-05.png` exist.
- `final-images.json` says `backend=local_dry_run`.
- Final audit should not call this publish-ready unless the quality gate is intentionally relaxed.

- [ ] **Step 4: Run wiki health**

Run:

```bash
venv/bin/python scripts/wiki_health.py --write --fix-index \
  --session-note "Repaired carousel image-generation state machine, compact prompt compiler, proof-first handoff, packaging audit refresh, and local dry-run backend."
```

Expected: `wiki health: PASS`.

---

## Self-Review

Spec coverage:
- Honest image state: Task 1 and Task 4.
- Faster image flow: Task 2, Task 3, Task 4, and Task 7.
- Fewer failures from ambiguous paths: Task 5 and Task 6.
- Existing failing tests: Task 6.
- End-to-end verification: Task 8.

Placeholder scan:
- No `TBD`, `TODO`, or vague "add tests" steps remain.
- Each code task includes concrete test or implementation snippets.

Type consistency:
- Status values use lowercase strings through `GenerationStatus`.
- `proof_slide` and `formats` are defined in Task 4 and used only after that task.
- `refresh_quality` is introduced in Task 5 and passed through the script in the same task.

