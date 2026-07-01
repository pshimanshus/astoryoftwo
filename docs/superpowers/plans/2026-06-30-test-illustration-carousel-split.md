# Illustration Carousel Test Split Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Split `tests/test_illustration_carousel.py` from one 4,006-line, 92-test mixed suite into focused workflow-owned test modules without weakening any carousel production gates.

**Architecture:** Keep `tests/test_illustration_carousel.py` as a compact public entrypoint and C1 contract smoke suite. Extract shared filesystem, image, package, visual-QA, and CLI helpers into `tests/helpers/illustration_carousel.py`, then move existing test methods unchanged by behavior boundary. After each move, run the exact moved slice plus the remaining original file so regressions are caught while the split is still small.

**Tech Stack:** Python `unittest` tests run by `pytest`, `tempfile`, `pathlib`, `subprocess`, `cv2`/`numpy` image fixtures, existing carousel pipeline modules under `pipeline/stages/`, and script entrypoints under `scripts/`.

---

## Review Decision

Split the file. The issue is not only line count. The current file is acting as seven different suites at once:

- C1 public API, manifest, parsing, and entrypoint smoke tests.
- Creator story-lane regression tests with exact copy and visual expectations.
- Identity reference discovery, identity-only generation, and intake behavior.
- CLI behavior and script argument contracts.
- Image handoff and legacy model-native generation guard behavior.
- Generated-output packaging, native dimensions, and stale-file cleanup.
- Final audit, visual QA, integrated text, wiki update, and quality-spine gates.

Keep only the first category in `tests/test_illustration_carousel.py`. Everything else should move into named modules where failures tell the next agent which subsystem broke.

Do not do a broad rewrite while splitting. First pass should preserve assertions and fixture shape. Improvements such as parametrizing story-lane cases or replacing every manifest-only raw byte can happen after the behavioral split is green.

## File Structure

- Create: `tests/helpers/illustration_carousel.py`
  - Shared `IllustrationCarouselTestMixin`.
  - Valid PNG/JPEG fixture bytes.
  - Package-directory lookup independent of `date.today()`.
  - Passing structured visual QA writer.
  - Script runner with `timeout=30`.

- Keep and shrink: `tests/test_illustration_carousel.py`
  - Public C1/API smoke tests only.
  - No CLI subprocess tests.
  - No story-lane content regression tests.
  - No final audit or packaging gate tests.

- Create: `tests/test_carousel_story_lanes.py`
  - Exact creator-story copy, lane, caption, visual-debate, and visual-plan regressions.

- Create: `tests/test_carousel_identity_references.py`
  - Explicit identity references, auto-discovery, curated bundle limits, identity-only intake, and interactive blank identity behavior.

- Create: `tests/test_illustration_carousel_cli.py`
  - `scripts/create_illustration_carousel.py` and `scripts/package_generated_carousel.py` CLI behavior.

- Create: `tests/test_carousel_local_renderers.py`
  - Local dry-run backend and legacy preview renderer non-publishability.

- Create: `tests/test_carousel_prompt_and_handoff.py`
  - Prompt-pack style drift, Codex built-in handoff files, proof prompts, stale prompt cleanup, and visual-plan pre-generation blockers.

- Create: `tests/test_carousel_generation_guards.py`
  - Disabled legacy API/model-native image generation paths, mocked-client behavior, and reference selection.

- Create: `tests/test_carousel_generated_packaging.py`
  - `package_generated_carousel.py` and `package_codex_builtin_outputs` native output packaging, dimension checks, stale-file cleanup, audit refresh, and audit-failed result state.

- Create: `tests/test_carousel_final_audit.py`
  - Integrated text manifest, final image checks, final audit, structured visual QA, wiki update, and quality refresh behavior.

- Create: `tests/test_carousel_contract_surfaces.py`
  - Style contract, golden theme/story-selling registration, no one-off carousel scripts, split-module public routes, and successful-carousel-standard contract embedding.

## Keep In `tests/test_illustration_carousel.py`

Move all helper methods out, then keep these tests as the compact entrypoint suite:

- `test_slugify_title_keeps_carousel_paths_stable`
- `test_extract_json_object_handles_fenced_agent_output`
- `test_build_manifest_uses_artifact_contract_and_reference_images`
- `test_anthropic_manifest_can_record_identity_references`
- `test_story_command_defaults_to_five_slides`
- `test_slide_count_allows_longer_story_arcs_for_story_command`
- `test_codex_native_builder_creates_package_without_anthropic_key`
- `test_codex_native_prompt_pack_has_compact_generation_fields`

These tests explain the workflow entrypoint and should stay near `pipeline.stages.c1_illustration_carousel` imports.

## Move Map

`tests/test_carousel_story_lanes.py`:

- `test_food_denial_story_uses_shareable_not_hungry_arc`
- `test_private_captions_story_uses_selected_agent_room_copy_and_visual_system`
- `test_tasty_life_story_uses_repaired_payoff_arc_and_persona_gate`
- `test_tiny_ritual_story_uses_aachu_zuv_theme_not_travel_template`
- `test_chaotic_wife_story_uses_viral_reference_pattern`
- `test_mood_changed_story_preserves_selected_golden_theme_copy`
- `test_morning_person_story_uses_chai_silence_arc`
- `test_photo_ritual_story_uses_hinglish_bubble_arc`
- `test_kashmiri_language_story_uses_family_belonging_arc`
- `test_subtitles_story_uses_mood_translation_arc`
- `test_workday_homecoming_story_uses_himanshu_pov_arc_and_tournament`
- `test_high_maintenance_story_uses_care_without_shrinking_arc_and_tournament`
- `test_softness_under_fire_story_uses_be_safe_arc_and_tournament`
- `test_softness_under_fire_visual_quality_rejects_losing_visual_option_leak`
- `test_imperfect_repair_story_uses_spacious_apology_arc`
- `test_main_kar_lungi_story_uses_visual_debate_gate_and_outdoor_care_arc`

`tests/test_carousel_identity_references.py`:

- `test_codex_native_manifest_records_identity_reference`
- `test_codex_native_discovers_workspace_identity_images_folder`
- `test_codex_native_auto_identity_discovery_uses_curated_bundle`
- `test_codex_native_rejects_overlarge_explicit_identity_bundle`
- `test_interactive_mode_blank_identity_keeps_auto_discovery_enabled`
- `test_final_audit_accepts_identity_only_generated_carousel`

`tests/test_illustration_carousel_cli.py`:

- `test_cli_defaults_to_codex_native_without_anthropic_key`
- `test_cli_accepts_identity_image_for_codex_native_runs`
- `test_package_generated_carousel_direct_script_help_works`
- `test_cli_accepts_identity_only_codex_native_runs`
- `test_cli_rejects_legacy_api_image_backend_even_without_generation`
- `test_cli_rejects_local_dry_run_with_handoff_flags`
- `test_cli_generate_images_defaults_to_codex_builtin_handoff`
- `test_cli_proof_slide_implies_codex_builtin_handoff`

`tests/test_carousel_local_renderers.py`:

- `test_local_dry_run_backend_creates_both_native_formats`
- `test_local_dry_run_legacy_renderer_writes_preview_only_manifest`
- `test_legacy_local_carousel_renderer_writes_preview_only_state`
- `test_local_renderer_skips_text_only_slides_without_reference_images`

`tests/test_carousel_prompt_and_handoff.py`:

- `test_storyboard_prompt_pack_and_text_plan_match_slides`
- `test_prompts_require_publishable_art_with_integrated_text`
- `test_codex_handoff_blocks_artifact_prompt_style_drift`
- `test_style_consistency_allows_negated_artifact_terms`
- `test_codex_builtin_handoff_writes_identity_reference_prompt_files`
- `test_codex_builtin_handoff_compiles_fresh_package_prompt_files`
- `test_prepare_codex_handoff_can_write_single_proof_prompt`
- `test_prepare_codex_handoff_blocker_uses_reels_proof_prompt`
- `test_prepare_codex_handoff_clears_stale_prompts_when_later_run_blocks`
- `test_codex_builtin_handoff_blocks_missing_visual_plan_quality_gate`

`tests/test_carousel_generation_guards.py`:

- `test_model_native_generation_marks_missing_key_blocked`
- `test_model_native_generation_is_disabled_for_carousel_work`
- `test_model_native_generation_blocks_failed_identity_consistency_gate`
- `test_model_native_generation_marks_api_error_blocked`
- `test_model_native_reference_selection_uses_curated_identity_bundle_and_style_refs`
- `test_model_native_generation_never_writes_final_images_with_mocked_client`

`tests/test_carousel_generated_packaging.py`:

- `test_package_generated_carousel_packages_two_native_formats`
- `test_package_generated_carousel_refuses_doctor_blocked_package`
- `test_package_generated_carousel_rejects_local_native_renderer_sources`
- `test_package_codex_builtin_outputs_writes_model_native_manifest`
- `test_package_generated_outputs_removes_stale_extra_final_slide_files`
- `test_package_codex_builtin_outputs_rejects_wrong_native_source_dimensions`
- `test_package_codex_builtin_outputs_rejects_native_aspect_but_wrong_size`
- `test_package_generated_outputs_refreshes_final_audit`
- `test_package_generated_outputs_reports_audit_failed_status`
- `test_workspace_root_fallback_uses_package_parent_for_external_dirs`

`tests/test_carousel_final_audit.py`:

- `test_integrated_text_manifest_preserves_slide_copy`
- `test_integrated_text_manifest_records_storybook_typography_rules`
- `test_integrated_text_pass_fails_when_final_images_are_missing`
- `test_final_audit_fails_when_final_images_are_missing`
- `test_asset_reviewer_accepts_model_native_generated_status`
- `test_final_audit_fails_without_integrated_text_and_checked_visual_qa`
- `test_final_audit_rejects_final_with_text_as_publishable_output`
- `test_quality_refresh_does_not_overwrite_existing_visual_qa_markdown`
- `test_final_audit_rejects_local_placeholder_final_images`
- `test_final_audit_rejects_single_source_resized_output_manifest`
- `test_final_audit_rejects_checkbox_only_visual_qa`
- `test_structured_visual_qa_requires_face_reference_evidence`
- `test_structured_visual_qa_rejects_missing_status`
- `test_wiki_update_records_audit_issues_and_notes`

`tests/test_carousel_contract_surfaces.py`:

- `test_carousel_style_contract_contains_aachu_zuv_north_star`
- `test_golden_viral_theme_skill_is_required_for_carousels`
- `test_romance_story_selling_skill_is_registered_for_carousel_concepting`
- `test_anthropic_package_validation_requires_story_selling_gate`
- `test_style_contract_blocks_photo_filter_placeholders_as_final_art`
- `test_no_uncontracted_one_off_carousel_generator_scripts`
- `test_successful_carousel_standard_rejects_object_first_deck`
- `test_codex_native_carousel_split_modules_expose_public_routes`
- `test_codex_native_package_embeds_successful_carousel_standard_contract`

## Task 1: Extract Shared Test Helpers

**Files:**
- Create: `tests/helpers/illustration_carousel.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create helper module**

Create `tests/helpers/illustration_carousel.py` with:

```python
import json
import subprocess
import sys
import unittest
from pathlib import Path


class IllustrationCarouselTestMixin(unittest.TestCase):
    def png_bytes(self, width: int, height: int, value: int = 255) -> bytes:
        import cv2
        import numpy as np

        ok, encoded = cv2.imencode(".png", np.full((height, width, 3), value, dtype=np.uint8))
        self.assertTrue(ok)
        return encoded.tobytes()

    def image_bytes(
        self,
        width: int = 64,
        height: int = 64,
        value: int = 240,
        *,
        extension: str = ".jpg",
    ) -> bytes:
        import cv2
        import numpy as np

        ok, encoded = cv2.imencode(
            extension,
            np.full((height, width, 3), value, dtype=np.uint8),
        )
        self.assertTrue(ok)
        return encoded.tobytes()

    def package_dir_for_slug(self, output_root: Path, slug: str) -> Path:
        matches = sorted(output_root.glob(f"*/{slug}"))
        self.assertEqual(
            len(matches),
            1,
            f"Expected one package directory for {slug}, found: {matches}",
        )
        return matches[0]

    def png_size(self, path: Path) -> tuple[int, int]:
        import cv2

        image = cv2.imread(str(path))
        self.assertIsNotNone(image)
        height, width = image.shape[:2]
        return width, height

    def run_python_script(self, repo_root: Path, args: list[str], *, env: dict[str, str] | None = None):
        return subprocess.run(
            [sys.executable, *args],
            cwd=repo_root,
            env=env,
            text=True,
            capture_output=True,
            check=False,
            timeout=30,
        )

    def write_passing_visual_qa(self, out_dir: Path, slide_count: int = 5) -> None:
        (out_dir / "visual-qa.json").write_text(
            json.dumps(
                {
                    "schema_version": "1.0",
                    "status": "PASS",
                    "checks": {
                        "storyboard": {"pass": True, "evidence": "Human QA checked each slide against storyboard."},
                        "aachu_face": {
                            "pass": True,
                            "reference_option_ids": ["ID01"],
                            "likeness_notes": "Long dark hair, expressive brows, soft oval face, and smile energy match ID01.",
                        },
                        "zuv_face": {
                            "pass": True,
                            "reference_option_ids": ["ID01"],
                            "likeness_notes": "Dark wavy hair, thick brows, beard, face structure, and grounded expression match ID01.",
                        },
                        "dress_continuity": {"pass": True, "evidence": "Outfits and continuity cues were checked."},
                        "style": {"pass": True, "evidence": "Warm hand-drawn storybook style was checked."},
                        "scene_logic": {"pass": True, "evidence": "Copy, clothing, props, and action were checked for contradictions."},
                        "pose_anatomy": {"pass": True, "evidence": "Aachu/Zuv posture and body anatomy were checked as natural and flattering."},
                        "integrated_final_text": {"pass": True, "evidence": "Copy and brandmark were checked."},
                        "final_files": {"pass": True, "evidence": "All final files were checked."},
                    },
                }
            ),
            encoding="utf-8",
        )
        lines = ["# Visual QA", ""]
        for number in range(1, slide_count + 1):
            lines.append(f"- [x] Slide {number} final image matches slide {number} storyboard.")
        lines.extend(
            [
                "- [x] Aachu face is recognizably based on the identity reference.",
                "- [x] Zuv face is recognizably based on the identity reference.",
                "- [x] Clothing and dress details follow the identity/style references.",
                "- [x] Illustration style matches the selected carousel style direction.",
                "- [x] Rendered text and brandmark are visible, accurate, and part of the artwork.",
            ]
        )
        (out_dir / "visual-qa.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
```

- [ ] **Step 2: Update the original class inheritance**

In `tests/test_illustration_carousel.py`, add:

```python
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Change:

```python
class IllustrationCarouselTests(unittest.TestCase):
```

to:

```python
class IllustrationCarouselTests(IllustrationCarouselTestMixin):
```

Remove the duplicated helper methods from the class.

- [ ] **Step 3: Run the helper-preservation smoke test**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py::IllustrationCarouselTests::test_local_dry_run_backend_creates_both_native_formats -q
```

Expected: `1 passed`.

## Task 2: Shrink Original File To Entry Point Tests

**Files:**
- Modify: `tests/test_illustration_carousel.py`
- Create: the split files listed in later tasks

- [ ] **Step 1: Keep only the eight entrypoint tests**

Leave these tests in `tests/test_illustration_carousel.py`:

```text
test_slugify_title_keeps_carousel_paths_stable
test_extract_json_object_handles_fenced_agent_output
test_build_manifest_uses_artifact_contract_and_reference_images
test_anthropic_manifest_can_record_identity_references
test_story_command_defaults_to_five_slides
test_slide_count_allows_longer_story_arcs_for_story_command
test_codex_native_builder_creates_package_without_anthropic_key
test_codex_native_prompt_pack_has_compact_generation_fields
```

- [ ] **Step 2: Run the shrunken original suite**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel.py -q
```

Expected: `8 passed`.

## Task 3: Move Story-Lane Regressions

**Files:**
- Create: `tests/test_carousel_story_lanes.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the story-lane module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin


class CarouselStoryLaneTests(IllustrationCarouselTestMixin):
```

Move the story-lane tests listed in the Move Map into this class. Preserve existing assertions and story text.

- [ ] **Step 2: Run the moved story-lane suite**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_story_lanes.py -q
```

Expected: all moved story-lane tests pass.

## Task 4: Move Identity Reference Tests

**Files:**
- Create: `tests/test_carousel_identity_references.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the identity module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the identity tests listed in the Move Map into `CarouselIdentityReferenceTests`.

- [ ] **Step 2: Run identity tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_identity_references.py -q
```

Expected: all moved identity tests pass.

## Task 5: Move CLI Tests

**Files:**
- Create: `tests/test_illustration_carousel_cli.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the CLI module**

Use this header:

```python
import json
import os
import tempfile
from pathlib import Path

from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the CLI tests listed in the Move Map into `IllustrationCarouselCliTests`. Keep `timeout=30` on every subprocess call. Prefer the helper `self.run_python_script(...)` only where it keeps the command readable.

- [ ] **Step 2: Run CLI tests**

Run:

```bash
venv/bin/python -m pytest tests/test_illustration_carousel_cli.py -q
```

Expected: all moved CLI tests pass.

## Task 6: Move Local Renderer Tests

**Files:**
- Create: `tests/test_carousel_local_renderers.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the local renderer module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import patch

from pipeline.stages.codex_native_carousel import create_codex_native_carousel, try_render_assets
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the local renderer tests listed in the Move Map into `CarouselLocalRendererTests`.

- [ ] **Step 2: Run local renderer tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_local_renderers.py -q
```

Expected: all moved local renderer tests pass.

## Task 7: Move Prompt And Handoff Tests

**Files:**
- Create: `tests/test_carousel_prompt_and_handoff.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the prompt and handoff module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the prompt and handoff tests listed in the Move Map into `CarouselPromptAndHandoffTests`.

- [ ] **Step 2: Run prompt and handoff tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_and_handoff.py -q
```

Expected: all moved prompt and handoff tests pass.

## Task 8: Move Generation Guard Tests

**Files:**
- Create: `tests/test_carousel_generation_guards.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the generation guard module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path
from unittest.mock import Mock

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the generation guard tests listed in the Move Map into `CarouselGenerationGuardTests`.

- [ ] **Step 2: Run generation guard tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_generation_guards.py -q
```

Expected: all moved generation guard tests pass.

## Task 9: Move Generated Packaging Tests

**Files:**
- Create: `tests/test_carousel_generated_packaging.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the generated packaging module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the generated packaging tests listed in the Move Map into `CarouselGeneratedPackagingTests`.

- [ ] **Step 2: Run generated packaging tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_generated_packaging.py -q
```

Expected: all moved generated packaging tests pass.

## Task 10: Move Final Audit And Visual QA Tests

**Files:**
- Create: `tests/test_carousel_final_audit.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the final audit module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the final audit and visual QA tests listed in the Move Map into `CarouselFinalAuditTests`.

- [ ] **Step 2: Keep deliberate invalid image bytes only in negative tests**

After moving, replace raw fixture bytes with `self.image_bytes()` or `self.png_bytes(...)` unless the test asserts rejection of invalid placeholder or derived files. Deliberately invalid bytes should remain only in:

```text
test_final_audit_rejects_local_placeholder_final_images
test_final_audit_rejects_single_source_resized_output_manifest
test_final_audit_rejects_checkbox_only_visual_qa
```

- [ ] **Step 3: Run final audit tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_final_audit.py -q
```

Expected: all moved final audit tests pass.

## Task 11: Move Contract Surface Tests

**Files:**
- Create: `tests/test_carousel_contract_surfaces.py`
- Modify: `tests/test_illustration_carousel.py`

- [ ] **Step 1: Create the contract surface module**

Use this header:

```python
import json
import tempfile
from datetime import date
from pathlib import Path

from pipeline.stages.c1_illustration_carousel import ORCHESTRATOR_SKILLS, SPECIALIST_AGENTS, load_skill, validate_package
from pipeline.stages.codex_native_carousel import create_codex_native_carousel
from tests.helpers.illustration_carousel import IllustrationCarouselTestMixin
```

Move the contract surface tests listed in the Move Map into `CarouselContractSurfaceTests`.

- [ ] **Step 2: Run contract surface tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_contract_surfaces.py -q
```

Expected: all moved contract surface tests pass.

## Task 12: Final Verification

**Files:**
- Verify all files created or modified by this split.

- [ ] **Step 1: Run the split carousel suite**

Run:

```bash
venv/bin/python -m pytest \
  tests/test_illustration_carousel.py \
  tests/test_carousel_story_lanes.py \
  tests/test_carousel_identity_references.py \
  tests/test_illustration_carousel_cli.py \
  tests/test_carousel_local_renderers.py \
  tests/test_carousel_prompt_and_handoff.py \
  tests/test_carousel_generation_guards.py \
  tests/test_carousel_generated_packaging.py \
  tests/test_carousel_final_audit.py \
  tests/test_carousel_contract_surfaces.py \
  -q
```

Expected: same 92 test behaviors pass, now distributed across focused files.

- [ ] **Step 2: Run adjacent carousel contract tests**

Run:

```bash
venv/bin/python -m pytest tests/test_carousel_prompt_compiler.py tests/test_carousel_state_contract.py tests/test_checks_prompt_constraints.py -q
```

Expected: all tests pass.

- [ ] **Step 3: Run health because this touches test/workflow structure**

Run:

```bash
venv/bin/python scripts/agentic_os.py health
```

Expected: JSON summary prints with context sections, skill systems, and skill records.

## Self-Review

Spec coverage: The plan reviews the complete current file, makes an explicit keep/split decision, maps every observed test category to a destination file, and includes verification after each migration batch.

Placeholder scan: No task asks for an unspecified split. Every destination file has a responsibility, moved test list, import header, and verification command.

Risk notes:

- Move tests unchanged first. Do not parametrize story-lane tests until after the split is green.
- Keep `tests/test_illustration_carousel.py` as the public entrypoint smoke suite so future agents still have one obvious workflow overview.
- Preserve deliberate invalid bytes in negative final-audit tests. Replace fake bytes elsewhere only where image readability or dimension behavior matters.
- Do not stage unrelated dirty worktree changes while executing this plan.
