# Carousel Generation Loop Remaining Fixes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the `/story` carousel loop so Aachu/Zuv style, identity references, clean art generation, local typography, final packaging, and final audit are enforced end to end.

**Architecture:** Treat `config/carousel_style_contract.json` as the canonical style source, pass identity references through every runtime, derive storyboard/prompts/overlay/final manifests from `slides.json`, and make the final audit fail until clean generated images, local text overlays, and visual QA exist. Existing generated packages must be re-audited under the stricter contract because older `PASS_WITH_NOTES` audits were produced before the final-image and identity gates existed.

**Tech Stack:** Python 3.13, `unittest`, existing C-layer modules in `pipeline/stages/`, OpenCV for deterministic text overlays and optional dimension checks, local filesystem artifacts under `output/carousels/`.

---

## Current Audit Snapshot

- `venv/bin/python -m unittest tests.test_illustration_carousel -v` currently runs 21 tests successfully.
- `scripts/create_illustration_carousel.py` now accepts `--identity-image` and passes identity references through Codex-native and Anthropic legacy modes.
- Source security scan no longer finds committed Apify token literals in `AGENTS.md`, `CLAUDE.md`, `config`, `pipeline`, `scripts`, `docs`, `tests`, `memory`, `wiki`, or `.claude`.
- The fresh identity-aware package is `output/carousels/2026-05-16/love-kept-the-same-posture-2/` and is intentionally marked `NEEDS_FIXES`: it has identity references, but still has no final generated images, no local text overlays, and unchecked face/storyboard QA.
- The older `output/carousels/2026-05-16/love-kept-the-same-posture/` package remains a stale pre-identity run and should not be treated as final.
- The old package audit no longer says `PASS_WITH_NOTES`; it was re-audited under `REQ-IDENTITY-001` and `REQ-FINAL-IMAGES-001`.

## File Structure

- Modify: `scripts/create_illustration_carousel.py`
  - Adds `--identity-image` and passes identity refs into the Codex-native builder.
- Modify: `pipeline/stages/c1_illustration_carousel.py`
  - Makes optional Anthropic legacy mode identity-aware instead of silently dropping face references.
- Modify: `pipeline/stages/codex_native_carousel.py`
  - Removes model-typography wording from image prompts, renames local CV2 outputs as previews, and broadens story-lane planning.
- Modify: `pipeline/stages/carousel_quality.py`
  - Adds hard gates for identity refs, final images, local text overlays, visual QA, and dimensions.
- Modify: `scripts/render_carousel_text_overlays.py`
  - Uses the style contract colors and checks all expected final images before rendering overlays.
- Modify: `config/skills/illustration-carousel-framework.md`
  - Aligns the skill text with the canonical Aachu/Zuv style contract.
- Modify: `tests/test_illustration_carousel.py`
  - Adds regression coverage for CLI identity refs, no generated typography, overlay artifacts, stale audits, and broader content lanes.
- Re-audit generated files: `output/carousels/2026-05-16/love-kept-the-same-posture/`
  - Marks the stale package as `NEEDS_FIXES` until identity references, real final art, local overlays, and visual QA are completed.

---

### Task 1: Fix CLI Identity Reference Wiring

**Files:**
- Modify: `scripts/create_illustration_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Run the existing failing test**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_cli_accepts_identity_image_for_codex_native_runs -v
```

Expected: FAIL with `unrecognized arguments: --identity-image`.

- [x] **Step 2: Add the CLI argument**

In `scripts/create_illustration_carousel.py`, after the `--image` argument, add:

```python
    parser.add_argument(
        "--identity-image",
        dest="identity_images",
        action="append",
        default=None,
        help="Aachu/Zuv identity or clothing reference image. Repeat for multiple references.",
    )
```

- [x] **Step 3: Pass identity refs into options**

Replace the `options = { ... }` block in `scripts/create_illustration_carousel.py` with:

```python
        options = {
            "story": story,
            "image_paths": args.images,
            "identity_image_paths": args.identity_images,
            "title": args.title,
            "slide_count": args.slide_count,
            "style_brief": args.style_brief,
        }
```

- [x] **Step 4: Keep Anthropic legacy mode from crashing**

Until Task 2 lands, strip `identity_image_paths` before calling legacy mode:

```python
    if args.mode == "anthropic":
        options.pop("identity_image_paths", None)
        out_dir = create_illustration_carousel(
            **options,
            output_root=args.output_root,
        )
```

- [x] **Step 5: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_cli_accepts_identity_image_for_codex_native_runs -v
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: both commands PASS.

---

### Task 2: Make Anthropic Legacy Mode Identity-Aware

**Files:**
- Modify: `pipeline/stages/c1_illustration_carousel.py`
- Modify: `scripts/create_illustration_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Add a unit test for manifest identity refs in legacy helpers**

Add this test:

```python
    def test_anthropic_manifest_can_record_identity_references(self):
        from pipeline.stages.c1_illustration_carousel import build_manifest

        with tempfile.TemporaryDirectory() as tmpdir:
            story_image = Path(tmpdir) / "story.jpg"
            identity_image = Path(tmpdir) / "identity.jpg"
            story_image.write_bytes(b"story")
            identity_image.write_bytes(b"identity")

            manifest = build_manifest(
                title="Legacy Identity",
                slug="legacy-identity",
                story="A tiny ritual story.",
                image_paths=[story_image],
                identity_image_paths=[identity_image],
                today=date(2026, 5, 16),
            )

        self.assertEqual(
            manifest["identity_references"],
            [{"path": str(identity_image), "role": "Aachu/Zuv face consistency reference"}],
        )
```

- [x] **Step 2: Extend the legacy manifest signature**

Change `build_manifest(...)` in `pipeline/stages/c1_illustration_carousel.py` to accept:

```python
    identity_image_paths: list[Path] | None = None,
```

Then add:

```python
        "identity_references": [
            {"path": str(path), "role": "Aachu/Zuv face consistency reference"}
            for path in (identity_image_paths or [])
        ],
```

- [x] **Step 3: Extend legacy brief content**

Update `build_brief_text(...)` to accept `identity_image_paths: list[Path] | None = None` and include:

```python
    if identity_image_paths:
        lines.append("Identity reference images for Aachu/Zuv face consistency:")
        lines.extend(f"- {path}" for path in identity_image_paths)
```

- [x] **Step 4: Include identity image blocks before story references**

Update `build_user_content(...)` to accept `identity_image_paths` and add:

```python
    for path in identity_image_paths or []:
        content.append({"type": "text", "text": f"Identity reference image for Aachu/Zuv: {path.name}"})
        content.append(image_content_block(path))
```

- [x] **Step 5: Pass identity refs through `run_agent(...)` and `create_illustration_carousel(...)`**

Add `identity_image_paths: list[Path] | None = None` to `run_agent(...)` and `create_illustration_carousel(...)`. Normalize in `create_illustration_carousel(...)`:

```python
    normalized_identity_images = normalize_image_paths(identity_image_paths or [])
```

Pass `identity_image_paths=normalized_identity_images` into every `run_agent(...)` and `build_manifest(...)` call.

- [x] **Step 6: Remove the temporary strip in the CLI**

After legacy mode accepts identity refs, replace `legacy_options` with direct `options` again:

```python
        out_dir = create_illustration_carousel(
            **options,
            output_root=args.output_root,
        )
```

- [x] **Step 7: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

---

### Task 3: Stop Asking Image Models To Render Typography

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Add a failing prompt test**

Add this test:

```python
    def test_prompts_request_clean_art_without_model_typography(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            identity = Path(tmpdir) / "identity.jpg"
            image.write_bytes(b"story")
            identity.write_bytes(b"identity")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                identity_image_paths=[identity],
                title="Clean Typography",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )

            prompt_pack = json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8"))

        joined = "\n".join(slide["prompt"] for slide in prompt_pack["slides"])
        self.assertIn("No text inside the artwork", joined)
        self.assertNotIn("Text overlay verbatim", joined)
```

- [x] **Step 2: Change prompt generation**

In `build_package(...)`, replace:

```python
f"Style: {style}. Text overlay verbatim: '{slide['copy']}'. "
"Preserve the supplied reference image cues and avoid generic couple content. "
"If final typography is applied locally, leave clean whitespace for the text."
```

with:

```python
f"Style: {style}. No text inside the artwork. No rendered captions, no quote text, no fake typography. "
"Reserve clean whitespace for a later local text overlay. "
"Preserve the supplied reference image cues and avoid generic couple content. "
```

- [x] **Step 3: Keep slide text only in structured fields**

Confirm each prompt slide keeps:

```python
"text": slide["copy"]
```

and that `prompt_pack["text_overlay_plan"]["slide_copy"]` remains the source for local typography.

- [x] **Step 4: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_prompts_request_clean_art_without_model_typography -v
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

---

### Task 4: Rename Local CV2 Renders As Previews, Not Final Generation

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Modify: `pipeline/stages/carousel_quality.py`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Add an assertion that local previews are not final images**

Add this to `test_codex_native_builder_creates_package_without_anthropic_key`:

```python
        self.assertNotEqual(review["status"], "final_ready")
```

Add a new test:

```python
    def test_local_cv2_render_is_recorded_as_preview_not_final_generation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "invalid.jpg"
            image.write_bytes(b"not-real-image-data")

            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                title="Preview Only",
                output_root=Path(tmpdir) / "out",
                render_assets=True,
                today=date(2026, 5, 16),
            )

            image_generation = json.loads((out_dir / "image-generation.json").read_text(encoding="utf-8"))

        self.assertIn(image_generation["status"], {"preview_partial", "preview_rendered", "skipped"})
```

- [x] **Step 2: Rename statuses in `try_render_assets(...)`**

Replace return values:

```python
return {"status": "partial", "reason": str(exc), "slides": rendered}
return {"status": "rendered", "mode": "local_cv2_stylized_render", "slides": rendered}
```

with:

```python
return {"status": "preview_partial", "reason": str(exc), "slides": rendered}
return {"status": "preview_rendered", "mode": "local_cv2_stylized_preview", "slides": rendered}
```

- [x] **Step 3: Update quality accepted statuses**

In `build_stage_reviews(...)`, replace:

```python
elif render_status not in {"rendered", "partial"}:
```

with:

```python
elif render_status not in {"preview_rendered", "preview_partial"}:
```

- [x] **Step 4: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

---

### Task 5: Enforce Local Text Overlay And Visual QA Gates

**Files:**
- Modify: `pipeline/stages/carousel_quality.py`
- Modify: `scripts/render_carousel_text_overlays.py`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Add final overlay requirement**

In `build_requirements(...)`, add:

```python
{
    "id": "REQ-TEXT-OVERLAY-001",
    "label": "Final text overlays are rendered locally into final-with-text/slide-XX.png",
    "source": "user typography consistency requirement",
    "expected": context.slide_count,
    "critical": True,
},
{
    "id": "REQ-VISUAL-QA-001",
    "label": "Face and storyboard visual QA exists and has no failed checks",
    "source": "user face/storyboard QA requirement",
    "critical": True,
},
```

- [x] **Step 2: Evaluate overlay files**

In `evaluate_requirements(...)`, add:

```python
overlay_files = [
    context.out_dir / "final-with-text" / f"slide-{number:02d}.png"
    for number in range(1, context.slide_count + 1)
]
results["REQ-TEXT-OVERLAY-001"] = {
    "pass": all(path.exists() for path in overlay_files) and (context.out_dir / "text-overlay.json").exists(),
    "evidence": [str(path) for path in overlay_files if path.exists()],
}
```

- [x] **Step 3: Evaluate visual QA**

In `evaluate_requirements(...)`, add:

```python
visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
if visual_qa_path.exists():
    visual_qa_text = visual_qa_path.read_text(encoding="utf-8")
    failed = [line for line in visual_qa_text.splitlines() if line.strip().startswith("- [x] FAIL")]
    unchecked_face_items = [
        line for line in visual_qa_text.splitlines()
        if line.strip().startswith("- [ ]") and ("face" in line.lower() or "storyboard" in line.lower())
    ]
else:
    failed = ["visual-qa.md is missing"]
    unchecked_face_items = []

results["REQ-VISUAL-QA-001"] = {
    "pass": visual_qa_path.exists() and not failed and not unchecked_face_items,
    "evidence": {
        "visual_qa": str(visual_qa_path),
        "failed": failed,
        "unchecked_face_or_storyboard_items": unchecked_face_items,
    },
}
```

- [x] **Step 4: Make overlay renderer fail early when final art is missing**

In `render_overlays(...)`, before rendering, add:

```python
    missing = [
        final_dir / f"slide-{int(record['slide']):02d}.png"
        for record in manifest["slides"]
        if not (final_dir / f"slide-{int(record['slide']):02d}.png").exists()
    ]
    if missing:
        raise FileNotFoundError("Missing final images for overlay: " + ", ".join(str(path) for path in missing))
```

- [x] **Step 5: Add a test that final images alone are not enough**

Add:

```python
    def test_final_audit_fails_without_local_overlays_and_checked_visual_qa(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "anklet.jpg"
            identity = Path(tmpdir) / "identity.jpg"
            image.write_bytes(b"story")
            identity.write_bytes(b"identity")
            out_dir = create_codex_native_carousel(
                story="Before proposing I tied her anklet. After marriage I still tie her sandals.",
                image_paths=[image],
                identity_image_paths=[identity],
                title="Needs Overlay QA",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            final_dir = out_dir / "final"
            final_dir.mkdir()
            for number in range(1, 6):
                (final_dir / f"slide-{number:02d}.png").write_bytes(b"fake-png")

            from pipeline.stages.carousel_quality import build_final_audit, build_run_ledger, build_stage_reviews, QualityContext
            manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
            package = {
                "concept": json.loads((out_dir / "concept.json").read_text(encoding="utf-8")),
                "slides": json.loads((out_dir / "slides.json").read_text(encoding="utf-8")),
                "prompt_pack": json.loads((out_dir / "prompt-pack.json").read_text(encoding="utf-8")),
                "copy": json.loads((out_dir / "copy.json").read_text(encoding="utf-8")),
            }
            context = QualityContext(
                story=manifest["source_story"],
                title=manifest["title"],
                slug=manifest["slug"],
                today=date(2026, 5, 16),
                out_dir=out_dir,
                image_paths=[image],
                slide_count=5,
                package=package,
                manifest=manifest,
                render_result={"status": "skipped", "reason": "test"},
                workspace_root=Path(tmpdir),
            )
            ledger = build_run_ledger(context)
            stage_reviews = build_stage_reviews(context, ledger)
            audit = build_final_audit(context, ledger, stage_reviews)

        self.assertFalse(audit["requirements"]["REQ-TEXT-OVERLAY-001"]["pass"])
        self.assertFalse(audit["requirements"]["REQ-VISUAL-QA-001"]["pass"])
        self.assertEqual(audit["status"], "NEEDS_FIXES")
```

- [x] **Step 6: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

---

### Task 6: Align Framework Skill With Canonical Contract

**Files:**
- Modify: `config/skills/illustration-carousel-framework.md`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Add a skill-contract regression test**

Add:

```python
    def test_illustration_framework_mentions_canonical_aachu_zuv_contract(self):
        framework = Path("config/skills/illustration-carousel-framework.md").read_text(encoding="utf-8")

        self.assertIn("A soft illustrated archive of Aachu and Zuv", framework)
        self.assertIn("Product Unshipped", framework)
        self.assertIn("identity reference", framework.lower())
        self.assertIn("local text overlay", framework.lower())
```

- [x] **Step 2: Update the Visual Direction section**

Replace lines describing only “desi storybook / photo-rooted” with:

```markdown
Use `config/carousel_style_contract.json` as the canonical style contract.
The North Star is: “A soft illustrated archive of Aachu and Zuv's love,
chaos, culture, and tiny rituals.”

The visual style must be Product Unshipped-like softness adapted for a desi
love story: soft hand-drawn flat vector illustration, imperfect black outlines,
slightly uneven strokes, matte muted colors, large whitespace, off-white or
very light warm background, one clear visual idea per slide, and tiny
low-contrast `@a.storyof.two` brandmark.

Every run must use story reference images for scene/posture and identity
reference images for Aachu/Zuv face consistency. Generate clean art first:
no model-rendered captions, no random typography, no fake text. Apply final
copy with the local text overlay renderer.
```

- [x] **Step 3: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel.IllustrationCarouselTests.test_illustration_framework_mentions_canonical_aachu_zuv_contract -v
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

---

### Task 7: Broaden Story Lane Planner Beyond The Anklet Case

**Files:**
- Modify: `pipeline/stages/codex_native_carousel.py`
- Test: `tests/test_illustration_carousel.py`

- [x] **Step 1: Add lane regression tests**

Add:

```python
    def test_kashmiri_wife_story_avoids_generic_travel_template(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "noon-chai.jpg"
            image.write_bytes(b"story")
            out_dir = create_codex_native_carousel(
                story="Things my non-Kashmiri husband had to learn: noon chai, wazwan, and my strong opinions.",
                image_paths=[image],
                title="Kashmiri Wife Lessons",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))

        joined = " ".join(slide["copy"] + " " + slide["visual"] for slide in slides).lower()
        self.assertEqual(concept["content_lane"], "Kashmiri Wife x Non-Kashmiri Husband")
        self.assertIn("noon chai", joined)
        self.assertIn("wazwan", joined)
        self.assertNotIn("date became a trip", joined)
```

Add:

```python
    def test_chaotic_wife_story_uses_calm_husband_arc(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            image = Path(tmpdir) / "chaos.jpg"
            image.write_bytes(b"story")
            out_dir = create_codex_native_carousel(
                story="He didn't marry peace. He married me saying I'm leaving with no shoes on.",
                image_paths=[image],
                title="He Didn't Marry Peace",
                output_root=Path(tmpdir) / "out",
                render_assets=False,
                today=date(2026, 5, 16),
            )
            concept = json.loads((out_dir / "concept.json").read_text(encoding="utf-8"))
            slides = json.loads((out_dir / "slides.json").read_text(encoding="utf-8"))

        joined = " ".join(slide["copy"] + " " + slide["visual"] for slide in slides).lower()
        self.assertEqual(concept["content_lane"], "Chaotic Wife, Calm Husband")
        self.assertIn("peace", joined)
        self.assertIn("shoes", joined)
        self.assertIn("calm", concept["human_truth"].lower())
```

- [x] **Step 2: Add lane-specific slide builders**

Add functions:

```python
def build_kashmiri_lessons_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "He married me. Then Kashmir arrived.",
        "First lesson: noon chai is serious.",
        "Second lesson: wazwan is not just food.",
        "Third lesson: my opinions come seasoned.",
        "He is still learning. Lovingly.",
    ][:slide_count]
    visuals = [
        "Aachu places a cup of noon chai in front of Zuv with playful seriousness.",
        "Close-up of pink noon chai, small Kashmiri cues, and Zuv listening carefully.",
        "A warm wazwan table memory with Aachu explaining and Zuv smiling patiently.",
        "Aachu counts lessons on her fingers while Zuv holds snacks and nods.",
        "A tiny dictionary-style final frame: Aachu as spark, Zuv as steady student of love.",
    ][:slide_count]
    return build_slide_records(copies, visuals, image_paths, "make Kashmir feel personal, funny, and loving")
```

```python
def build_chaotic_calm_slides(image_paths: list[Path], slide_count: int) -> list[dict[str, Any]]:
    copies = [
        "He didn't marry peace.",
        "He married 'I'm leaving' with no shoes on.",
        "He married 10 moods before breakfast.",
        "He brings snacks. I bring weather.",
        "Somehow, he still calls it home.",
    ][:slide_count]
    visuals = [
        "Aachu bursts into frame like a spark while Zuv stands calm with a soft smile.",
        "Aachu points toward an imaginary exit, barefoot; Zuv calmly holds her shoes.",
        "Three tiny Aachu mood poses around a breakfast plate while Zuv holds chai.",
        "Aachu's playful storm cloud beside Zuv's water bottle and snack plate.",
        "A tender final frame with spark and steady diya flame side by side.",
    ][:slide_count]
    return build_slide_records(copies, visuals, image_paths, "make couples send this as tender chaos humor")
```

Add helper:

```python
def build_slide_records(copies: list[str], visuals: list[str], image_paths: list[Path], cta_intent: str) -> list[dict[str, Any]]:
    source_groups = distribute_sources(image_paths, len(copies))
    roles = ["hook", "proof", "turn", "proof", "payoff"][: len(copies)]
    emotions = ["playful", "specific", "recognition", "warm", "tender"][: len(copies)]
    return [
        {
            "slide": index,
            "copy": copy,
            "role": roles[index - 1],
            "visual": visuals[index - 1],
            "emotion": emotions[index - 1],
            "cta_intent": cta_intent,
            "source_images": source_groups[index - 1],
        }
        for index, copy in enumerate(copies, start=1)
    ]
```

- [x] **Step 3: Route lanes**

At the top of `build_slides(...)`, add:

```python
    if lane == "Kashmiri Wife x Non-Kashmiri Husband":
        return build_kashmiri_lessons_slides(image_paths, slide_count)
    if lane == "Chaotic Wife, Calm Husband":
        return build_chaotic_calm_slides(image_paths, slide_count)
```

- [x] **Step 4: Add lane-specific human truths**

In `build_package(...)`, add branches for these lanes before the generic fallback:

```python
    elif lane == "Kashmiri Wife x Non-Kashmiri Husband":
        human_truth = "Aachu's Kashmiri world becomes part of the marriage, and Zuv's love shows up as patient, curious learning."
        emotional_arc = "culture hook -> food/phrase lesson -> playful overwhelm -> tenderness -> shared home"
        caption_recommended = "he married me.\n\nthen noon chai, wazwan, and my strong opinions moved in too."
        caption_alt = "A Kashmiri wife, a patient non-Kashmiri husband, and the tiny lessons that become married life."
        hashtags = ["#AStoryOfTwo", "#KashmiriWife", "#NoonChai", "#Wazwan", "#AachuAndZuv"]
    elif lane == "Chaotic Wife, Calm Husband":
        human_truth = "The joke is that Aachu is the spark and Zuv is the steady flame, but underneath the chaos is safety."
        emotional_arc = "identity joke -> chaos proof -> calm response -> soft turn -> home"
        caption_recommended = "he wanted peace.\n\nthen he married me.\n\nsomehow he still smiles like this is normal."
        caption_alt = "A soft illustrated chaos catalog of Aachu's drama and Zuv's patient love."
        hashtags = ["#AStoryOfTwo", "#ChaoticWife", "#CalmHusband", "#MarriedLife", "#AachuAndZuv"]
```

- [x] **Step 5: Verify**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

---

### Task 8: Repair The Existing `love-kept-the-same-posture` Package

**Files:**
- Modify generated package under `output/carousels/2026-05-16/love-kept-the-same-posture/`

- [x] **Step 1: Rebuild the package with the identity image**

Use the real identity reference path supplied by the user. Example:

```bash
venv/bin/python scripts/create_illustration_carousel.py \
  --story "Right before I proposed to Anchal, I tied an anklet around her foot. Years later, after marriage, I still find myself kneeling down to tie her shoes and sandals. The gesture changed from proposal magic to ordinary married life, but the posture stayed the same: love, quietly choosing care again." \
  --title "Love Kept The Same Posture" \
  --image "/Users/himanshusharma/Downloads/WhatsApp Image 2026-05-10 at 20.45.06.jpeg" \
  --image "/Users/himanshusharma/Downloads/WhatsApp Image 2026-05-10 at 20.48.32.jpeg" \
  --identity-image "/Users/himanshusharma/Downloads/WhatsApp Image 2026-05-16 at 10.16.37 (1).jpeg" \
  --output-root output/carousels \
  --no-render
```

Expected: creates a new dated package with `identity_references` in `manifest.json` and `identity_reference_images` in `prompt-pack.json`.

- [ ] **Step 2: Generate clean art outside the package**

Generate five clean illustrations from `prompt-pack.json`. Each generation prompt must include:

```text
No text inside the artwork. No rendered captions, no quote text, no fake typography. Reserve clean whitespace for a later local text overlay.
```

Stage selected outputs as:

```text
tmp/final-art/love-kept-the-same-posture/slide-01.png
tmp/final-art/love-kept-the-same-posture/slide-02.png
tmp/final-art/love-kept-the-same-posture/slide-03.png
tmp/final-art/love-kept-the-same-posture/slide-04.png
tmp/final-art/love-kept-the-same-posture/slide-05.png
```

- [ ] **Step 3: Package generated art**

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

Expected:

```text
output/carousels/2026-05-16/love-kept-the-same-posture/final/slide-01.png
output/carousels/2026-05-16/love-kept-the-same-posture/final/slide-02.png
output/carousels/2026-05-16/love-kept-the-same-posture/final/slide-03.png
output/carousels/2026-05-16/love-kept-the-same-posture/final/slide-04.png
output/carousels/2026-05-16/love-kept-the-same-posture/final/slide-05.png
output/carousels/2026-05-16/love-kept-the-same-posture/final-images.json
```

- [ ] **Step 4: Render local text overlays**

Run:

```bash
venv/bin/python scripts/render_carousel_text_overlays.py output/carousels/2026-05-16/love-kept-the-same-posture
```

Expected:

```text
output/carousels/2026-05-16/love-kept-the-same-posture/final-with-text/slide-01.png
output/carousels/2026-05-16/love-kept-the-same-posture/final-with-text/slide-02.png
output/carousels/2026-05-16/love-kept-the-same-posture/final-with-text/slide-03.png
output/carousels/2026-05-16/love-kept-the-same-posture/final-with-text/slide-04.png
output/carousels/2026-05-16/love-kept-the-same-posture/final-with-text/slide-05.png
output/carousels/2026-05-16/love-kept-the-same-posture/text-overlay.json
```

- [ ] **Step 5: Complete visual QA**

Open `visual-qa.md` and change only verified items from unchecked to checked. Any face/storyboard problem must be marked like this:

```markdown
- [x] FAIL: Slide 3 does not match the storyboard split-memory composition.
- [x] FAIL: Aachu face drifted from the identity reference.
```

Expected: final audit remains `NEEDS_FIXES` while failed or unchecked face/storyboard items remain.

- [ ] **Step 6: Re-run tests and final audit**

Run:

```bash
venv/bin/python -m unittest tests.test_illustration_carousel -v
```

Expected: PASS.

Final package status should be:

```text
PASS_WITH_NOTES: if clean final art and overlays exist, but manual face QA is still pending.
PASS: only after final images, local overlays, dimensions, identity references, and face/storyboard QA are all complete.
```

---

## Self-Review

- Spec coverage: Covers canonical style prompt, identity reference wiring, clean art generation, no random AI typography, local text overlay, final image packaging, final audit gates, face/storyboard QA, and existing package repair.
- Placeholder scan: No `TBD`, `TODO`, or “implement later” placeholders are present.
- Type consistency: New code snippets use existing `Path`, `dict[str, Any]`, `create_codex_native_carousel(...)`, and `unittest` patterns already present in the repo.
