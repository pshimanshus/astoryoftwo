# Carousel Generation Loop Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make `/story` produce storyboard, prompts, final generated carousel images, packaging, and audit results from one locked Aachu/Zuv style and story contract.

**Architecture:** Add a canonical visual identity contract, replace generic local story inference with explicit story-lane planning, make storyboard/prompt/final-image manifests derive from the same slide records, and fail the final audit unless generated images are copied into the carousel package and reviewed against the storyboard. Generated art should be text-free or text-light; final typography should be applied locally with one fixed overlay renderer so font and spacing stay consistent.

**Tech Stack:** Python 3.13, `unittest`, existing C-layer modules in `pipeline/stages/`, local filesystem artifacts, OpenCV/Pillow-style post-processing for deterministic text overlays, Codex built-in image generation for final art when available.

---

## Verified Gaps

1. **Style contract drift:** `config/skills/illustration-carousel-framework.md` still says generic “desi storybook / photo-rooted” and does not encode the Product Unshipped-like soft flat vector style, typography, negative prompt, or Aachu/Zuv character bible the user supplied.
2. **No identity bible:** The pipeline has no persistent face/reference contract for Aachu and Zuv. It accepts arbitrary images as “story references” but never marks the new face photo as required identity input.
3. **Storyboard and final images can diverge:** `slides.json`, `prompt-pack.json`, and image-generation calls are separate editable artifacts. Manual edits after rendering created mismatch risk.
4. **Generated images were not packaged:** Built-in image generation saved files under `$CODEX_HOME/generated_images/...`, but the carousel package did not copy them into `output/carousels/.../final/`.
5. **Local previews were mislabeled as success:** `image-generation.json` said `rendered` for OpenCV stylized previews, while no final AI-generated illustration slides existed in the project output.
6. **Audit is too shallow:** `pipeline/stages/carousel_quality.py` checks prompt text and reference-image presence, but not final slide files, dimensions, final-image count, prompt/storyboard consistency, typography, or face-reference use.
7. **Story lane failure:** `pipeline/stages/codex_native_carousel.py` infers generic first-date/travel arcs. It does not use the North Star: “A soft illustrated archive of Aachu and Zuv’s love, chaos, culture, and tiny rituals.”
8. **Typography is uncontrolled:** Text was asked of the image model and also drawn by OpenCV with a different look. This guarantees inconsistent font, spacing, and readability.
9. **No human approval checkpoint for faces:** The process does not stop for identity review before declaring final images ready. Exact face preservation is not something a prompt can honestly guarantee; the system needs an explicit face-consistency gate.

## File Structure

- Create: `config/carousel_style_contract.json`
  - Owns the canonical shared style prompt, negative prompt, typography rules, North Star, content lanes, and Aachu/Zuv character bible.
- Create: `pipeline/stages/carousel_contract.py`
  - Loads and validates the style contract. Builds shared style text and per-run identity/reference context.
- Modify: `pipeline/stages/codex_native_carousel.py`
  - Removes generic first-date/trip fallback for `/story`. Adds story-lane classification, style-contract injection, and a final-image packaging status.
- Modify: `pipeline/stages/carousel_quality.py`
  - Adds hard requirements for identity reference, final generated image files, dimensions, storyboard/prompt consistency, and text overlay policy.
- Create: `scripts/package_generated_carousel.py`
  - Copies generated images from `$CODEX_HOME/generated_images/...` into a carousel output folder, maps them to slide numbers, records source paths, and creates `final/slide-01.png` through `final/slide-05.png`.
- Create: `scripts/render_carousel_text_overlays.py`
  - Applies fixed local typography and brandmark to clean generated art so font and spacing are deterministic.
- Modify: `tests/test_illustration_carousel.py`
  - Adds regression tests for the style contract, identity reference requirement, final image gate, and storyboard/prompt consistency.

---

### Task 1: Add Canonical Aachu/Zuv Style Contract

**Files:**
- Create: `config/carousel_style_contract.json`
- Test: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write the failing test**

Add this test to `tests/test_illustration_carousel.py`:

```python
    def test_carousel_style_contract_contains_aachu_zuv_north_star(self):
        from pipeline.stages.carousel_contract import load_style_contract

        contract = load_style_contract()

        self.assertIn("Aachu and Zuv", contract["north_star"])
        self.assertIn("Product Unshipped", contract["shared_style_prompt"])
        self.assertIn("soft hand-drawn flat vector", contract["shared_style_prompt"])
        self.assertIn("No photorealism", contract["shared_negative_prompt"])
        self.assertEqual(contract["brandmark"], "@a.storyof.two")
        self.assertEqual(contract["typography"]["strategy"], "local_overlay")
        self.assertIn("spark", contract["characters"]["aachu"]["relationship_role"])
        self.assertIn("steady flame", contract["characters"]["zuv"]["relationship_role"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_carousel_style_contract_contains_aachu_zuv_north_star -v`

Expected: FAIL with `ModuleNotFoundError: No module named 'pipeline.stages.carousel_contract'`.

- [ ] **Step 3: Create the contract file**

Create `config/carousel_style_contract.json`:

```json
{
  "schema_version": "1.0",
  "north_star": "A soft illustrated archive of Aachu and Zuv's love, chaos, culture, and tiny rituals.",
  "brandmark": "@a.storyof.two",
  "shared_style_prompt": "Create an Instagram carousel slide in a soft hand-drawn flat vector illustration style. Use the provided reference photos to create recurring illustrated versions of Aachu/Anchal and Zuv/Himanshu, not generic stock characters. Keep the illustration minimal, warm, romantic, and desi. Use imperfect black outlines, slightly uneven strokes, matte muted colors, large whitespace, off-white or very light warm background, and one clear visual idea only. Add tiny low-contrast handwritten brandmark '@a.storyof.two' at bottom-right. Product Unshipped-like simplicity adapted for a desi love story.",
  "shared_negative_prompt": "No photorealism, no 3D rendering, no glossy AI look, no corporate/startup illustration, no stock Indian couple style, no Canva quote-card design, no complex background, no overcrowded props, no dramatic shadows, no gradients, no isometric style, no anime, no Pixar/Disney style, no hyper-detailed faces, no perfect vector geometry, no large logo, no extra decorative clutter, no mean-spirited humor, no generic self-help poster energy.",
  "typography": {
    "strategy": "local_overlay",
    "text_color": "#2a2621",
    "background": "#fbf4e8",
    "max_lines": 3,
    "placement": "generous whitespace",
    "brandmark_placement": "bottom-right"
  },
  "characters": {
    "aachu": {
      "names": ["Aachu", "Anchal"],
      "visual_cues": ["expressive warm smile", "soft dramatic energy", "playful body language", "Kashmiri bridal details when story-relevant", "pink/coral/orange/red lehenga energy when wedding-relevant", "mehendi", "jasmine", "jewelry"],
      "relationship_role": "spark"
    },
    "zuv": {
      "names": ["Zuv", "Himanshu"],
      "visual_cues": ["dark wavy hair", "calm warm smile", "grounded patient posture", "taller presence", "ivory sherwani with subtle pastel embroidery when wedding-relevant"],
      "relationship_role": "steady flame"
    }
  },
  "content_lanes": [
    "Wedding Origin Story",
    "Kashmiri Wife x Non-Kashmiri Husband",
    "Chaotic Wife, Calm Husband",
    "Soft Love Notes",
    "Tiny Rituals",
    "Himanshu POV",
    "Aachu POV"
  ]
}
```

- [ ] **Step 4: Add the loader**

Create `pipeline/stages/carousel_contract.py`:

```python
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


CONTRACT_PATH = Path("config") / "carousel_style_contract.json"


def load_style_contract(path: Path = CONTRACT_PATH) -> dict[str, Any]:
    contract = json.loads(path.read_text(encoding="utf-8"))
    required = [
        "north_star",
        "brandmark",
        "shared_style_prompt",
        "shared_negative_prompt",
        "typography",
        "characters",
        "content_lanes",
    ]
    missing = [key for key in required if not contract.get(key)]
    if missing:
        raise ValueError("Style contract missing required keys: " + ", ".join(missing))
    return contract
```

- [ ] **Step 5: Run test to verify it passes**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_carousel_style_contract_contains_aachu_zuv_north_star -v`

Expected: PASS.

---

### Task 2: Require Identity Reference Images

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write the failing test**

Add this test:

```python
    def test_codex_native_manifest_records_identity_reference(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            story_image = workspace / "anklet.jpg"
            identity_image = workspace / "aachu-zuv.jpg"
            story_image.write_bytes(b"story-image")
            identity_image.write_bytes(b"identity-image")

            out_dir = create_codex_native_carousel(
                story="He tied the anklet before proposing; after marriage he still ties her sandals.",
                image_paths=[story_image],
                identity_image_paths=[identity_image],
                title="Same Posture",
                output_root=workspace / "output" / "carousels",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

        selfEqual = self.assertEqual
        selfEqual(manifest["identity_references"], [{"path": str(identity_image), "role": "Aachu/Zuv face consistency reference"}])
        self.assertIn(str(identity_image), prompt_pack["identity_reference_images"])
        self.assertIn("Aachu", prompt_pack["character_bible"])
        self.assertIn("Zuv", prompt_pack["character_bible"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_codex_native_manifest_records_identity_reference -v`

Expected: FAIL with `TypeError: create_codex_native_carousel() got an unexpected keyword argument 'identity_image_paths'`.

- [ ] **Step 3: Update function signature and manifest**

Modify `create_codex_native_carousel(...)` to accept:

```python
identity_image_paths: list[str | Path] | None = None,
```

Normalize them with:

```python
identity_paths = normalize_paths(identity_image_paths or [])
```

Add `identity_image_paths=identity_paths` to `build_package(...)` and `build_manifest(...)`.

Add to `build_manifest(...)`:

```python
"identity_references": [
    {"path": str(path), "role": "Aachu/Zuv face consistency reference"}
    for path in identity_image_paths
],
```

- [ ] **Step 4: Add identity context to prompt pack**

In `build_package(...)`, load the contract and add:

```python
contract = load_style_contract()
character_bible = (
    "Aachu/Anchal: expressive warm smile, playful dramatic energy, soft curls or real current hair from identity reference, "
    "Kashmiri/desi jewelry cues when relevant; she is the spark. "
    "Zuv/Himanshu: dark wavy hair, calm warm smile, grounded patient posture, taller presence; he is the steady flame."
)
```

Then include these keys in `prompt_pack`:

```python
"identity_reference_images": [str(path) for path in identity_image_paths],
"character_bible": character_bible,
```

Prepend every slide prompt with:

```python
f"Identity reference images: {[str(path) for path in identity_image_paths]}. "
f"Character bible: {character_bible}. "
```

- [ ] **Step 5: Run test to verify it passes**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_codex_native_manifest_records_identity_reference -v`

Expected: PASS.

---

### Task 3: Replace Generic Story Inference With Story Lane Planner

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write the failing test**

Add this test:

```python
    def test_tiny_ritual_story_uses_aachu_zuv_theme_not_travel_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her shoes and sandals.",
                image_paths=[image],
                title="Same Posture",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))

        joined = " ".join(slide["copy"] + " " + slide["visual"] for slide in slides).lower()
        self.assertEqual(concept["content_lane"], "Tiny Rituals")
        self.assertIn("anklet", joined)
        self.assertIn("sandals", joined)
        self.assertNotIn("date became a trip", joined)
        self.assertNotIn("story feel huge", joined)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_tiny_ritual_story_uses_aachu_zuv_theme_not_travel_template -v`

Expected: FAIL because current builder emits first-date/trip copy.

- [ ] **Step 3: Implement lane classification**

Add to `pipeline/stages/codex_native_carousel.py`:

```python
def classify_content_lane(story: str) -> str:
    lower = story.lower()
    if any(token in lower for token in ["anklet", "shoe", "shoes", "sandal", "sandals", "chai", "gossip", "feeds me"]):
        return "Tiny Rituals"
    if any(token in lower for token in ["kashmir", "kashmiri", "noon chai", "wazwan"]):
        return "Kashmiri Wife x Non-Kashmiri Husband"
    if any(token in lower for token in ["chaos", "dramatic", "mood", "leaving", "peace"]):
        return "Chaotic Wife, Calm Husband"
    if any(token in lower for token in ["proposal", "shaadi", "wedding", "married"]):
        return "Wedding Origin Story"
    return "Soft Love Notes"
```

- [ ] **Step 4: Add Tiny Rituals anklet planner**

Add:

```python
def build_tiny_ritual_anklet_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "Before the ring, there was an anklet.",
        "He thought he was tying jewellery.",
        "Maybe love had already bent down.",
        "Now it's shoes. Sandals. Same boy.",
        "Some promises don't need new words.",
    ][:slide_count]
    visuals = [
        "Aachu sits in the mountain-window room while Zuv kneels and ties the anklet before proposing.",
        "Close-up of Zuv's hands tying the anklet around Aachu's foot, warm off-white background.",
        "Then-and-now visual rhyme: anklet before proposal, sandal after marriage, same kneeling posture.",
        "Aachu laughs on the balcony while Zuv fastens her golden sandal; playful married-life care.",
        "Minimal close-up of anklet and fastened sandal strap, with Zuv's hand leaving the frame.",
    ][:slide_count]
    source_groups = distribute_sources(image_paths, slide_count)
    return [
        {
            "slide": index,
            "copy": copy,
            "role": ["hook", "meaning reveal", "turn", "married-life proof", "payoff"][index - 1],
            "visual": visuals[index - 1],
            "emotion": ["private", "tender", "realizing", "playful", "settled"][index - 1],
            "cta_intent": "make couples send this as a tiny-ritual love-language moment",
            "source_images": source_groups[index - 1],
        }
        for index, copy in enumerate(copies, start=1)
    ]
```

- [ ] **Step 5: Route `build_slides` through lane planner**

At the start of `build_slides(...)`:

```python
lane = classify_content_lane(story)
if lane == "Tiny Rituals" and any(token in story.lower() for token in ["anklet", "shoe", "shoes", "sandal", "sandals"]):
    return build_tiny_ritual_anklet_slides(image_paths, slide_count)
```

- [ ] **Step 6: Run test to verify it passes**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_tiny_ritual_story_uses_aachu_zuv_theme_not_travel_template -v`

Expected: PASS.

---

### Task 4: Make Storyboard, Prompt Pack, and Final Images Use One Slide Manifest

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write the failing test**

Add this test:

```python
    def test_storyboard_prompt_pack_and_text_plan_match_slides(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                title="Same Posture",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))
            prompts = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))
            storyboard = (out_dir / "storyboard.md").read_text(encoding="utf-8")

        slide_copy = [slide["copy"] for slide in slides]
        self.assertEqual(prompts["text_overlay_plan"]["slide_copy"], slide_copy)
        self.assertEqual([prompt["text"] for prompt in prompts["slides"]], slide_copy)
        for copy in slide_copy:
            self.assertIn(copy, storyboard)
```

- [ ] **Step 2: Run test to verify current behavior**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_storyboard_prompt_pack_and_text_plan_match_slides -v`

Expected: PASS after Task 3 if all artifacts are generated from `slides`; FAIL if manual post-edits or disconnected generation remain.

- [ ] **Step 3: Make `write_storyboard` consume only package slides**

Ensure `write_storyboard(...)` never recomputes copy. It should use:

```python
for slide in package["slides"]:
    lines.append(f"- {slide['slide']}: {slide['copy']} - {slide['visual']}")
```

- [ ] **Step 4: Add a generated image manifest skeleton**

In `write_package(...)`, create `final-images.json` with pending records:

```python
write_json(
    out_dir / "final-images.json",
    {
        "status": "pending_generation",
        "slides": [
            {
                "slide": slide["slide"],
                "copy": slide["copy"],
                "expected_file": f"final/slide-{slide['slide']:02d}.png",
                "source_prompt_slide": slide["slide"],
            }
            for slide in package["slides"]
        ],
    },
)
```

- [ ] **Step 5: Run full carousel tests**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel -v`

Expected: PASS.

---

### Task 5: Package Real Generated Images Into Carousel Output

**Files:**
- Create: `scripts/package_generated_carousel.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write the failing packaging test**

Add this test:

```python
    def test_package_generated_carousel_copies_final_images(self):
        from scripts.package_generated_carousel import package_generated_images

        with tempfile.TemporaryDirectory() as tmpdir:
            workspace = Path(tmpdir)
            out_dir = workspace / "output" / "carousels" / "2026-05-16" / "same-posture"
            source_dir = workspace / "generated"
            out_dir.mkdir(parents=True)
            source_dir.mkdir()
            slides = [{"slide": number, "copy": f"Slide {number}"} for number in range(1, 6)]
            (out_dir / "slides.json").write_text(json.dumps(slides), encoding="utf-8")
            for number in range(1, 6):
                (source_dir / f"source-{number}.png").write_bytes(b"png-data")

            manifest = package_generated_images(
                carousel_dir=out_dir,
                generated_paths=[source_dir / f"source-{number}.png" for number in range(1, 6)],
            )

        self.assertEqual(manifest["status"], "packaged")
        self.assertEqual(len(manifest["slides"]), 5)
        self.assertTrue((out_dir / "final" / "slide-01.png").exists())
        self.assertTrue((out_dir / "final" / "slide-05.png").exists())
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_package_generated_carousel_copies_final_images -v`

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement packager**

Create `scripts/package_generated_carousel.py`:

```python
from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any


def package_generated_images(carousel_dir: Path, generated_paths: list[Path]) -> dict[str, Any]:
    slides_path = carousel_dir / "slides.json"
    slides = json.loads(slides_path.read_text(encoding="utf-8"))
    if len(generated_paths) != len(slides):
        raise ValueError(f"Expected {len(slides)} generated images, got {len(generated_paths)}.")

    final_dir = carousel_dir / "final"
    final_dir.mkdir(parents=True, exist_ok=True)
    records = []
    for slide, source_path in zip(slides, generated_paths, strict=True):
        number = int(slide["slide"])
        target = final_dir / f"slide-{number:02d}.png"
        shutil.copy2(source_path, target)
        records.append(
            {
                "slide": number,
                "copy": slide["copy"],
                "source": str(source_path),
                "file": str(target),
            }
        )

    manifest = {"status": "packaged", "slides": records}
    (carousel_dir / "final-images.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
```

- [ ] **Step 4: Run test to verify it passes**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_package_generated_carousel_copies_final_images -v`

Expected: PASS.

---

### Task 6: Deterministic Typography Overlay

**Files:**
- Create: `scripts/render_carousel_text_overlays.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write the failing overlay test**

Add this test:

```python
    def test_overlay_manifest_preserves_slide_copy(self):
        from scripts.render_carousel_text_overlays import build_overlay_manifest

        slides = [
            {"slide": 1, "copy": "Before the ring, there was an anklet."},
            {"slide": 2, "copy": "He thought he was tying jewellery."},
        ]

        manifest = build_overlay_manifest(slides)

        self.assertEqual(manifest["typography"]["strategy"], "local_overlay")
        self.assertEqual(manifest["slides"][0]["text"], "Before the ring, there was an anklet.")
        self.assertEqual(manifest["slides"][1]["brandmark"], "@a.storyof.two")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_overlay_manifest_preserves_slide_copy -v`

Expected: FAIL with `ModuleNotFoundError`.

- [ ] **Step 3: Implement overlay manifest builder**

Create `scripts/render_carousel_text_overlays.py`:

```python
from __future__ import annotations

from typing import Any

from pipeline.stages.carousel_contract import load_style_contract


def build_overlay_manifest(slides: list[dict[str, Any]]) -> dict[str, Any]:
    contract = load_style_contract()
    return {
        "typography": contract["typography"],
        "slides": [
            {
                "slide": int(slide["slide"]),
                "text": slide["copy"],
                "brandmark": contract["brandmark"],
                "placement": contract["typography"]["placement"],
            }
            for slide in slides
        ],
    }
```

- [ ] **Step 4: Add actual renderer after manifest test passes**

Add a `render_overlays(carousel_dir: Path) -> dict[str, Any]` function that reads `final/slide-XX.png`, writes `final-with-text/slide-XX.png`, and writes `text-overlay.json`. Use one local font, one text color, one max-width, one brandmark placement. If the selected font file is missing, raise `FileNotFoundError` instead of silently switching fonts.

- [ ] **Step 5: Run overlay tests**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_overlay_manifest_preserves_slide_copy -v`

Expected: PASS.

---

### Task 7: Strengthen Final Audit Gates

**Files:**
- Modify: `pipeline/stages/carousel_quality.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Write failing audit test**

Add:

```python
    def test_final_audit_fails_when_final_images_are_missing(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            image.write_bytes(b"story-image")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                title="Same Posture",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            final_audit = json.loads((out_dir / "final-audit.json").read_text(encoding="utf-8"))

        self.assertEqual(final_audit["status"], "NEEDS_FIXES")
        self.assertIn("REQ-FINAL-IMAGES-001", final_audit["requirements"])
        self.assertFalse(final_audit["requirements"]["REQ-FINAL-IMAGES-001"]["pass"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_final_audit_fails_when_final_images_are_missing -v`

Expected: FAIL because current audit permits missing final images.

- [ ] **Step 3: Add final-image requirement**

In `build_requirements(...)`, add:

```python
{
    "id": "REQ-FINAL-IMAGES-001",
    "label": "Final generated carousel images are packaged as final/slide-XX.png and match slide count",
    "source": "user final-output requirement",
    "expected": context.slide_count,
    "critical": True,
}
```

- [ ] **Step 4: Evaluate final-image requirement**

In `evaluate_requirements(...)`, add:

```python
final_files = [context.out_dir / "final" / f"slide-{number:02d}.png" for number in range(1, context.slide_count + 1)]
results["REQ-FINAL-IMAGES-001"] = {
    "pass": all(path.exists() for path in final_files),
    "evidence": [str(path) for path in final_files if path.exists()],
}
```

- [ ] **Step 5: Add identity-reference requirement**

Add requirement:

```python
{
    "id": "REQ-IDENTITY-001",
    "label": "Aachu/Zuv identity reference is present in manifest and prompt pack",
    "source": "user face-consistency requirement",
    "critical": True,
}
```

Evaluate:

```python
identity_refs = context.manifest.get("identity_references", [])
identity_prompt_refs = prompt_pack(context).get("identity_reference_images", [])
results["REQ-IDENTITY-001"] = {
    "pass": bool(identity_refs) and bool(identity_prompt_refs),
    "evidence": {"manifest": identity_refs, "prompt_pack": identity_prompt_refs},
}
```

- [ ] **Step 6: Run final audit tests**

Run: `venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_final_audit_fails_when_final_images_are_missing -v`

Expected: PASS.

---

### Task 8: Add Manual Visual QA Checklist for Faces and Storyboard Match

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `pipeline/stages/carousel_quality.py`

- [ ] **Step 1: Update final approval checklist**

Modify `write_approval(...)` to include:

```python
"- [ ] Final images exist in `final/` or `final-with-text/`.",
"- [ ] Aachu and Zuv faces are checked against the identity reference image.",
"- [ ] Each final image matches its storyboard slide.",
"- [ ] Text uses the local overlay style, not random model typography.",
"- [ ] Any failed identity or storyboard check marks the run NEEDS_FIXES.",
```

- [ ] **Step 2: Add visual QA artifact**

Write `visual-qa.md` in `write_quality_artifacts(...)` with this checklist:

```markdown
# Visual QA

- [ ] Slide 1 final image matches slide 1 storyboard.
- [ ] Slide 2 final image matches slide 2 storyboard.
- [ ] Slide 3 final image matches slide 3 storyboard.
- [ ] Slide 4 final image matches slide 4 storyboard.
- [ ] Slide 5 final image matches slide 5 storyboard.
- [ ] Aachu face is recognizably based on the identity reference.
- [ ] Zuv face is recognizably based on the identity reference.
- [ ] Illustration style matches soft hand-drawn flat vector / Product Unshipped-like simplicity.
- [ ] Typography is consistent and readable.
```

- [ ] **Step 3: Final audit rule**

If `visual-qa.md` exists but any line begins `- [x] FAIL`, final audit becomes `NEEDS_FIXES`. If `visual-qa.md` is absent, final audit includes a note only when final images are also absent; once final images exist, missing visual QA is a critical issue.

---

### Task 9: Repair the Existing `love-kept-the-same-posture` Package

**Files:**
- Modify generated package under `output/carousels/2026-05-16/love-kept-the-same-posture/`

- [ ] **Step 1: Add the new identity reference to manifest**

Record `/Users/himanshusharma/Downloads/WhatsApp Image 2026-05-16 at 10.16.37 (1).jpeg` as:

```json
{"path": "/Users/himanshusharma/Downloads/WhatsApp Image 2026-05-16 at 10.16.37 (1).jpeg", "role": "Aachu/Zuv face consistency reference"}
```

- [ ] **Step 2: Rewrite prompt-pack with canonical style**

Use `config/carousel_style_contract.json` for `shared_style_prompt`, `shared_negative_prompt`, `character_bible`, `identity_reference_images`, and `text_overlay_plan`.

- [ ] **Step 3: Regenerate clean art**

Generate one image per slide, without model-rendered text, using:

```text
Create ONE standalone final Instagram carousel illustration, slide N of 5, vertical 4:5. No text inside the artwork. Use identity reference image for Aachu/Zuv faces and the story reference images for scene/posture. Style must follow config/carousel_style_contract.json exactly.
```

After generation, copy the selected five clean art files into this staging folder with stable names:

```text
/Users/himanshusharma/astoryoftwo-analysis/tmp/final-art/love-kept-the-same-posture/slide-01.png
/Users/himanshusharma/astoryoftwo-analysis/tmp/final-art/love-kept-the-same-posture/slide-02.png
/Users/himanshusharma/astoryoftwo-analysis/tmp/final-art/love-kept-the-same-posture/slide-03.png
/Users/himanshusharma/astoryoftwo-analysis/tmp/final-art/love-kept-the-same-posture/slide-04.png
/Users/himanshusharma/astoryoftwo-analysis/tmp/final-art/love-kept-the-same-posture/slide-05.png
```

- [ ] **Step 4: Package generated art**

Run:

```bash
venv/bin/python scripts/package_generated_carousel.py \
  output/carousels/2026-05-16/love-kept-the-same-posture \
  tmp/final-art/love-kept-the-same-posture/slide-01.png \
  tmp/final-art/love-kept-the-same-posture/slide-02.png \
  tmp/final-art/love-kept-the-same-posture/slide-03.png \
  tmp/final-art/love-kept-the-same-posture/slide-04.png \
  tmp/final-art/love-kept-the-same-posture/slide-05.png
```

- [ ] **Step 5: Apply local text overlay**

Run:

```bash
venv/bin/python scripts/render_carousel_text_overlays.py output/carousels/2026-05-16/love-kept-the-same-posture
```

Expected outputs:

```text
output/carousels/2026-05-16/love-kept-the-same-posture/final/slide-01.png
output/carousels/2026-05-16/love-kept-the-same-posture/final-with-text/slide-01.png
output/carousels/2026-05-16/love-kept-the-same-posture/text-overlay.json
output/carousels/2026-05-16/love-kept-the-same-posture/visual-qa.md
```

- [ ] **Step 6: Run tests and audit**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

Final audit expected after images and visual QA pass: `PASS_WITH_NOTES` if manual face review is still pending; `PASS` only after face/storyboard QA is checked.

---

## Execution Notes

- Do not delete anything under `/Users/himanshusharma/.codex/generated_images/`; copy generated files into the carousel package.
- Do not claim “final carousel images” unless `final/slide-01.png` through `final/slide-05.png` exist in the package.
- Do not rely on image-model typography for final posts. Generate art clean, then add text locally.
- Exact face preservation cannot be honestly guaranteed through prompting alone. The gate should be: use the identity reference every time, reject obvious face drift, and require human visual approval before `PASS`.
- This workspace is not a git repository, so skip commit steps unless the project is later moved into a git repo.

## Self-Review

- Spec coverage: Covers style contract, character bible, identity reference, storyboard/prompt consistency, final image packaging, deterministic text, final audit, and existing package repair.
- Placeholder scan: No unfinished placeholder markers remain. Generated images are staged into stable `tmp/final-art/.../slide-XX.png` paths before packaging.
- Type consistency: New functions use `Path`, `dict[str, Any]`, existing `create_codex_native_carousel(...)`, and existing `unittest` structure.
