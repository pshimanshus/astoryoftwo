# Final Carousel Illustrations With Text Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the final `He Did Not Marry A Morning Person` carousel as storybook illustrations with visible handwritten copy and brandmark, matching the attached reference style.

**Architecture:** Treat image-model output as clean art only and never as the publishable final. The publishable carousel is `final-with-text/slide-XX.png`, created by applying exact deterministic typography to approved generated art. The audit must pass only when generated-art provenance, text-bearing final images, and structured visual QA all pass.

**Tech Stack:** `image_gen` built-in image generation, `scripts/package_generated_carousel.py`, `scripts/render_carousel_text_overlays.py`, `pipeline/stages/carousel_quality.py`, `venv/bin/python -m unittest`.

---

## File Structure

- Existing carousel package: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/`
- Style references: `/Users/himanshusharma/Downloads/Generated image 2.png` through `/Users/himanshusharma/Downloads/Generated image 7.png`
- Identity reference: `identity_images/aachu_zuv.png`
- Generated clean-art staging folder: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/`
- Clean intermediate art: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/final/slide-XX.png`
- Publishable final art with text: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/final-with-text/slide-XX.png`
- Structured QA gate: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/visual-qa.json`
- Human QA worksheet: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/visual-qa.md`

## Non-Negotiable Rules

- Do not create local OpenCV/vector placeholder illustrations.
- If `image_gen` fails or produces unusable art, stop and report the blocker.
- Do not mark QA pass from markdown checkboxes alone.
- Do not call clean textless images final for Instagram.
- Final shareable carousel means `final-with-text/slide-XX.png`.
- Text must be exact from `slides.json`; no model-generated spelling.
- The attached examples are layout/style references: warm paper, soft figure rendering, handwritten black text, bottom-right `@a.storyof.two`, generous whitespace.

### Task 1: Freeze The Final Slide Copy And Layout

**Files:**
- Read: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/slides.json`
- Read: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/prompt-pack.json`

- [ ] **Step 1: Confirm the exact five copy lines**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
slides = json.loads(Path("output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/slides.json").read_text())
for slide in slides:
    print(f"{slide['slide']}: {slide['copy']}")
PY
```

Expected output:

```text
1: He didn't marry a morning person.
2: He married "5 more minutes" said 11 times.
3: He married angry, hungry, and suddenly cute.
4: So he learned: chai first, questions later.
5: Maybe love is knowing when not to talk.
```

- [ ] **Step 2: Confirm `text_layout` supports reference-style placement**

Run:

```bash
venv/bin/python - <<'PY'
import json
from pathlib import Path
slides = json.loads(Path("output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/slides.json").read_text())
for slide in slides:
    print(slide["slide"], slide.get("text_layout", {}))
PY
```

Expected: slide 2 includes `speech_bubble: "5 more\nminutes"` and all slides have a clear primary text position.

### Task 2: Generate Only Approved Clean Art

**Files:**
- Read: `identity_images/aachu_zuv.png`
- Read: `/Users/himanshusharma/Downloads/Generated image 2.png` through `/Users/himanshusharma/Downloads/Generated image 7.png`
- Create: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-XX.png`

- [ ] **Step 1: Generate slide 1 with image model**

Use `image_gen` with `identity_images/aachu_zuv.png` as identity reference and the downloaded examples as style/layout references.

Prompt requirements:

```text
Create clean illustration art for slide 1. Do not draw the main caption text or brandmark. Match the attached reference carousel style: warm off-white paper, soft storybook characters, expressive Aachu/Zuv likeness, generous whitespace where handwritten copy will be overlaid. Scene: Aachu wrapped in a blanket refusing morning light while Zuv gently opens the curtain. No text, no watermark.
```

Acceptance before continuing: the image has Aachu/Zuv likeness, no text, enough empty copy space, and does not look like stock art.

- [ ] **Step 2: Generate slides 2-5 the same way**

Use the current `prompt-pack.json` scenes, but keep these copy areas:

```text
Slide 2: room for top caption and speech bubble.
Slide 3: room for top caption.
Slide 4: room for top caption.
Slide 5: room for top caption.
```

Acceptance before continuing: all five images look like one coherent carousel set.

- [ ] **Step 3: Copy approved generated images into staging**

Immediately after each approved `image_gen` result, run the matching copy command. These commands preserve the original generated files and copy the newest generated PNG into the project staging folder.

```bash
mkdir -p output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model
src="$(find /Users/himanshusharma/.codex/generated_images -type f -name '*.png' -mmin -10 | sort | tail -1)"
test -n "$src" && cp "$src" output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-01.png
src="$(find /Users/himanshusharma/.codex/generated_images -type f -name '*.png' -mmin -10 | sort | tail -1)"
test -n "$src" && cp "$src" output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-02.png
src="$(find /Users/himanshusharma/.codex/generated_images -type f -name '*.png' -mmin -10 | sort | tail -1)"
test -n "$src" && cp "$src" output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-03.png
src="$(find /Users/himanshusharma/.codex/generated_images -type f -name '*.png' -mmin -10 | sort | tail -1)"
test -n "$src" && cp "$src" output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-04.png
src="$(find /Users/himanshusharma/.codex/generated_images -type f -name '*.png' -mmin -10 | sort | tail -1)"
test -n "$src" && cp "$src" output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-05.png
```

Expected: five staged PNGs exist under `source-generated-image-model/`.

### Task 3: Package Clean Art With Approved Provenance

**Files:**
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/final/slide-XX.png`
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/final-images.json`

- [ ] **Step 1: Package staged image-model files**

Run:

```bash
venv/bin/python scripts/package_generated_carousel.py \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3 \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-01.png \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-02.png \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-03.png \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-04.png \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/source-generated-image-model/slide-05.png
```

Expected: `final-images.json` records sources from `source-generated-image-model`, not `source-generated-local`.

### Task 4: Render The Publishable Text-Bearing Carousel

**Files:**
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/final-with-text/slide-XX.png`
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/text-overlay.json`

- [ ] **Step 1: Run deterministic text overlay**

Run:

```bash
venv/bin/python -m scripts.render_carousel_text_overlays \
  output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3
```

Expected: five `final-with-text/slide-XX.png` files exist with exact copy and bottom-right brandmark.

- [ ] **Step 2: Create contact sheet for review**

Run:

```bash
venv/bin/python - <<'PY'
from pathlib import Path
import cv2, numpy as np
base = Path("output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3")
imgs = []
for i in range(1, 6):
    img = cv2.imread(str(base / "final-with-text" / f"slide-{i:02d}.png"))
    if img is None:
        raise RuntimeError(f"missing slide {i}")
    imgs.append(cv2.resize(img, (324, 405), interpolation=cv2.INTER_AREA))
sheet = np.full((405, 324 * 5, 3), (248, 244, 235), np.uint8)
for idx, img in enumerate(imgs):
    sheet[:, idx * 324 : (idx + 1) * 324] = img
cv2.imwrite(str(base / "final-with-text" / "contact-sheet.png"), sheet)
print(base / "final-with-text" / "contact-sheet.png")
PY
```

Expected: contact sheet shows text visible on every slide.

### Task 5: Write Structured Visual QA

**Files:**
- Create: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/visual-qa.json`
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/visual-qa.md`

- [ ] **Step 1: Review final-with-text contact sheet**

Check each final slide against these gates:

```text
storyboard: each visual matches the planned scene.
aachu_face: Aachu is recognizably based on identity reference.
zuv_face: Zuv is recognizably based on identity reference.
style: matches attached storybook reference style.
typography: exact copy is visible, natural, and not misspelled.
final_files: all final and final-with-text files exist.
```

- [ ] **Step 2: Write `visual-qa.json` only if every gate passes**

Create:

```json
{
  "schema_version": "1.0",
  "status": "PASS",
  "reviewed_artifact": "final-with-text/contact-sheet.png",
  "checks": {
    "storyboard": {"pass": true, "evidence": "All five final-with-text slides match slides.json scenes."},
    "aachu_face": {"pass": true, "evidence": "Aachu keeps long dark hair, expressive face, and reference-inspired styling."},
    "zuv_face": {"pass": true, "evidence": "Zuv keeps dark wavy hair, beard/stubble, warm smile, and calm posture."},
    "style": {"pass": true, "evidence": "Warm paper, hand-drawn storybook texture, imperfect black linework, muted color."},
    "typography": {"pass": true, "evidence": "All slide copy is exact and readable in final-with-text exports."},
    "final_files": {"pass": true, "evidence": "final/ and final-with-text/ contain slide-01.png through slide-05.png."}
  }
}
```

If any item fails, do not write a passing `visual-qa.json`; stop and report the failed check.

### Task 6: Refresh Audit And Verify

**Files:**
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/final-audit.json`
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/run-ledger.json`
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/stage-reviews.json`
- Modify: `output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3/wiki-update.md`

- [ ] **Step 1: Rebuild audit from current artifacts**

Run the existing audit refresh helper pattern:

```bash
venv/bin/python - <<'PY'
from __future__ import annotations
from datetime import date
from pathlib import Path
import json
from pipeline.stages.carousel_quality import QualityContext, build_run_ledger, build_stage_reviews, build_final_audit, build_wiki_update, update_wiki_memory

out_dir = Path("output/carousels/2026-05-16/he-did-not-marry-a-morning-person-3")
manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
package = {
    "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
    "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
    "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
    "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
    "review": json.loads((out_dir / "review.json").read_text(encoding="utf-8")),
}
render_result = json.loads((out_dir / "image-generation.json").read_text(encoding="utf-8"))
context = QualityContext(
    story=manifest["source_story"],
    title=manifest["title"],
    slug=manifest["slug"],
    today=date.fromisoformat(manifest["date"]),
    out_dir=out_dir,
    image_paths=[Path(record["path"]) for record in manifest.get("reference_images", [])],
    slide_count=manifest["format"]["slide_count"],
    package=package,
    manifest=manifest,
    render_result=render_result,
    workspace_root=Path("."),
)
ledger = build_run_ledger(context)
stage_reviews = build_stage_reviews(context, ledger)
final_audit = build_final_audit(context, ledger, stage_reviews)
ledger["stage_statuses"]["final_contract"] = final_audit["status"]
ledger["final_gate"] = {"status": final_audit["status"], "pass": final_audit["pass"], "notes": final_audit["notes"]}
(out_dir / "run-ledger.json").write_text(json.dumps(ledger, indent=2), encoding="utf-8")
(out_dir / "stage-reviews.json").write_text(json.dumps(stage_reviews, indent=2), encoding="utf-8")
(out_dir / "final-audit.json").write_text(json.dumps(final_audit, indent=2), encoding="utf-8")
(out_dir / "wiki-update.md").write_text(build_wiki_update(context, final_audit), encoding="utf-8")
update_wiki_memory(context, final_audit)
print(json.dumps({"status": final_audit["status"], "pass": final_audit["pass"], "issues": final_audit["issues"]}, indent=2))
PY
```

Expected only after all gates pass:

```json
{
  "status": "PASS",
  "pass": true,
  "issues": []
}
```

- [ ] **Step 2: Run tests**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel
```

Expected:

```text
Ran 30 tests
OK
```

## Self-Review

- Spec coverage: The plan covers image generation, exact text rendering, provenance, structured QA, audit refresh, and tests.
- Placeholder scan: The plan contains no deferred filename placeholders for generated outputs; execution copies the newest generated PNG immediately after each approved image.
- Gate behavior: The final audit cannot pass from checked markdown alone because `visual-qa.json` is required.
- Block behavior: If generation or QA fails, the plan stops and reports the blocker instead of creating substitute art.
