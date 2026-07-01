"""Artifact writers for Codex-native carousel packages."""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.c1_illustration_carousel import ARTIFACT_CONTRACT
from pipeline.stages.carousel_generation_state import GenerationStatus, write_generation_state
from pipeline.stages.carousel_lanes import CAROUSEL_STORY_DIRECTOR_CONTRACT
from pipeline.stages.carousel_quality import QUALITY_ARTIFACTS
from pipeline.stages.successful_carousel_standard import (
    SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT,
    evaluate_successful_carousel_standard,
)


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def write_storyboard(out_dir: Path, package: dict[str, Any]) -> None:
    concept = package["concept"]
    lines = [
        f"# {concept['title']}",
        "",
        concept["human_truth"],
        "",
        "## Story-Selling Spine",
        "",
        f"- Card: {concept['story_selling_decision']['selected_concept_process_card']}",
        f"- Score: {concept['story_selling_decision']['score']['total']} / 30",
        f"- Decision: {concept['story_selling_decision']['decision']}",
        f"- Authorial rule: {concept['story_selling_decision']['authorial_flow']['writer_rule']}",
        "",
        "## Story Director Persona",
        "",
        f"- Status: {concept['carousel_story_director_persona']['status']}",
        f"- Selected hook: {concept['carousel_story_director_persona']['selected_hook']}",
        f"- Verdict: {concept['carousel_story_director_persona']['verdict']}",
        "",
        "## Emotional Arc",
        "",
        concept["emotional_arc"],
        "",
        "## Slide Flow",
        "",
    ]
    for slide in package["slides"]:
        lines.append(f"- {slide['slide']}: {slide['copy']} - {slide['visual']}")
    lines.extend(["", "## Recommended Caption", "", package["copy"]["caption_recommended"], ""])
    (out_dir / "storyboard.md").write_text("\n".join(lines), encoding="utf-8")


def write_approval(out_dir: Path, package: dict[str, Any]) -> None:
    review = package["review"]
    changes = review.get("required_changes_before_image_generation") or ["No required changes listed by reviewer."]
    lines = [
        "# Final Approval Checklist",
        "",
        f"Status: {review['status']}",
        f"Score: {review['total']} / {review['max']}",
        f"Story-Selling: {review['story_selling_score']['total']} / 30",
        f"Story-Selling Gate: {review['story_selling_gate']['status']}",
        f"Story Director Gate: {review['story_director_gate']['status']}",
        f"Pass: {review['pass']}",
        "",
        "## Before Posting",
        "",
        "- [ ] Slide copy is final.",
        "- [ ] `post-copy-visual-room.json` is GO after copy confirmation.",
        "- [ ] Reference photo details are preserved.",
        "- [ ] Aachu/Zuv identity references are present and used.",
        "- [ ] `visual-plan-quality.json` is PASS before image generation.",
        "- [ ] `identity-consistency-review.json` passes before image generation.",
        "- [ ] Story-Selling gate is PASS and the selected process card is visible in `concept.json`.",
        "- [ ] Story Director gate is PASS: hook, story, bridge, Zuv role, ending, and send/save reason are visible.",
        "- [ ] Successful carousel standard is PASS: agents aligned to the real goals, not a keyword checklist.",
        "- [ ] Model-native 4:5 Instagram post images exist in `final/slide-XX.png`.",
        "- [ ] Model-native 9:16 Reels/Stories images exist in `final-reels-stories/slide-XX.png`.",
        "- [ ] The 9:16 outputs were generated natively, not resized/cropped/padded from the 4:5 outputs.",
        "- [ ] Exact slide copy and brandmark are rendered inside the artwork.",
        "- [ ] Text is readable at Instagram size and has no spelling errors.",
        "- [ ] `visual-qa.md` has no failed checks.",
        "- [ ] The package does not feel like generic couple content.",
        "",
        "## Required Changes",
        "",
    ]
    lines.extend(f"- [ ] {change}" for change in changes)
    (out_dir / "final-approval.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def write_agent_reports(out_dir: Path, package: dict[str, Any]) -> None:
    lines = [
        "# C-Layer Agent Reports",
        "",
        "Runtime: codex_native_local",
        "",
        "This package was produced by the local Codex-native builder, which mirrors the C-layer roles without requiring an external API key.",
        "",
        "## C1 - Story Miner",
        "",
        package["concept"]["human_truth"],
        "",
        "## C2 - Arc Builder",
        "",
        package["concept"]["emotional_arc"],
        "",
        "## E-Layer - Story-Selling Authorial Spine",
        "",
        f"Card: {package['concept']['story_selling_decision']['selected_concept_process_card']}",
        f"Score: {package['review']['story_selling_score']['total']} / 30",
        package["concept"]["story_selling_decision"]["selector_verdict"],
        "",
        "## C0.25 - Carousel Story Director Persona",
        "",
        f"Status: {package['concept']['carousel_story_director_persona']['status']}",
        f"Selected hook: {package['concept']['carousel_story_director_persona']['selected_hook']}",
        package["concept"]["carousel_story_director_persona"]["verdict"],
        "",
        "## Success Carousel Standard",
        "",
        f"Source: {package['concept']['successful_carousel_standard']['source']}",
        package["concept"]["successful_carousel_standard"]["rule"],
        f"Gate: {package['review']['successful_carousel_standard_gate']['status']}",
        "",
        "## C5.5 - Post-Copy Visual Creative Room",
        "",
        f"Status: {package['post_copy_visual_room']['status']}",
        f"Selected visual system: {package['post_copy_visual_room']['selected_visual_system']}",
        package["post_copy_visual_room"]["why_it_wins"],
        "",
        "## C3/C4 - Visual And Prompt Direction",
        "",
        package["prompt_pack"]["shared_style_prompt"],
        "",
        "## C3A-C3C - Visual Debate Gate",
        "",
        f"Winner: {package['visual_debate']['winner']}",
        "",
        package["visual_debate"]["selector_verdict"],
        "",
        "## C3D - Pre-Generation Visual Screen",
        "",
        f"Status: {package['visual_plan_quality']['status']}",
        f"Decision: {package['visual_plan_quality']['decision']}",
        *(
            f"- {issue}"
            for issue in package["visual_plan_quality"].get("issues", [])
        ),
        "",
        "## C3.5 - Identity Consistency",
        "",
        f"Status: {package['identity_consistency_review']['status']}",
        "",
        *(
            f"- Slide {item['slide']}: "
            + ", ".join(name for name, passed in item["checks"].items() if passed)
            for item in package["identity_consistency_review"]["slides"]
        ),
        "",
        "## C5 - Copy Packager",
        "",
        package["copy"]["caption_recommended"],
        "",
        "## C6 - Reviewer",
        "",
        f"Score: {package['review']['total']} / {package['review']['max']}",
        f"Story-Selling: {package['review']['story_selling_score']['total']} / 30",
    ]
    (out_dir / "agent-reports.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def build_manifest(
    *,
    title: str,
    slug: str,
    story: str,
    image_paths: list[Path],
    identity_image_paths: list[Path],
    identity_reference_selection: dict[str, Any],
    identity_dossier: dict[str, Any],
    slide_count: int,
    today: date,
) -> dict[str, Any]:
    return {
        "date": str(today),
        "slug": slug,
        "title": title,
        "channel": "@a.storyof.two",
        "pipeline": "C-layer illustrated carousel",
        "runtime": "codex_native_local",
        "status": "draft_for_human_review",
        "source_story": story,
        "format": {
            "platform": "instagram",
            "type": "carousel",
            "slide_count": slide_count,
            "native_outputs": {
                "instagram_post": {
                    "aspect_ratio": "4:5",
                    "size": "1080x1350",
                    "directory": "final/",
                },
                "reels_stories": {
                    "aspect_ratio": "9:16",
                    "size": "1080x1920",
                    "directory": "final-reels-stories/",
                },
            },
            "native_output_rule": "Generate both formats separately. Never resize, crop, pad, or extend one output into the other.",
        },
        "reference_images": [
            {"path": str(path), "role": "user supplied story reference"}
            for path in image_paths
        ],
        "identity_references": [
            {"path": str(path), "role": "Aachu/Zuv face consistency reference"}
            for path in identity_image_paths
        ],
        "identity_reference_selection": identity_reference_selection,
        "identity_dossier": {
            "path": identity_dossier.get("path"),
            "preflight_path": identity_dossier.get("preflight_path"),
            "contact_sheet_path": identity_dossier.get("contact_sheet_path"),
            "status": identity_dossier.get("status"),
        },
        "agentic_os": {
            "context_manifest": "config/agentic_context_manifest.json",
            "skill_systems": "config/skill-systems.json",
            "skill_system": "carousel_jam",
        },
        "successful_carousel_standard": SUCCESSFUL_CAROUSEL_STANDARD_CONTRACT,
        "carousel_story_director_persona": CAROUSEL_STORY_DIRECTOR_CONTRACT,
        "artifacts": ARTIFACT_CONTRACT,
        "quality_spine": {
            "observer": "C0.5-Jarvis",
            "reviewers": [
                "intake_reviewer",
                "story_reviewer",
                "arc_reviewer",
                "visual_reviewer",
                "identity_consistency_reviewer",
                "prompt_reviewer",
                "copy_reviewer",
                "success_standard_reviewer",
                "asset_reviewer",
                "wiki_learning_reviewer",
                "C7-Final Contract Auditor",
            ],
            "artifacts": {
                **QUALITY_ARTIFACTS,
                "identity_consistency_review": "identity-consistency-review.json",
                "post_copy_visual_room": "post-copy-visual-room.json",
                "visual_debate": "visual-debate.json",
                "visual_plan_quality": "visual-plan-quality.json",
            },
        },
    }


def write_package(out_dir: Path, manifest: dict[str, Any], package: dict[str, Any]) -> None:
    package["review"]["successful_carousel_standard_gate"] = evaluate_successful_carousel_standard(
        package,
        slide_count=len(package["slides"]),
    )
    out_dir.mkdir(parents=True, exist_ok=True)
    write_json(out_dir / "manifest.json", manifest)
    write_json(out_dir / "creative-baseline.json", package["creative_baseline"])
    write_json(out_dir / "concept.json", package["concept"])
    if package.get("concept_selection"):
        write_json(out_dir / "concept-selection.json", package["concept_selection"])
    write_json(out_dir / "post-copy-visual-room.json", package["post_copy_visual_room"])
    write_json(out_dir / "visual-debate.json", package["visual_debate"])
    write_json(out_dir / "visual-plan-quality.json", package["visual_plan_quality"])
    write_json(out_dir / "slides.json", package["slides"])
    write_json(out_dir / "prompt-pack.json", package["prompt_pack"])
    write_json(out_dir / "identity-consistency-review.json", package["identity_consistency_review"])
    write_json(out_dir / "copy.json", package["copy"])
    write_json(out_dir / "review.json", package["review"])
    write_storyboard(out_dir, package)
    write_approval(out_dir, package)
    write_agent_reports(out_dir, package)
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


def try_render_assets(out_dir: Path, slides: list[dict[str, Any]]) -> dict[str, Any]:
    try:
        import cv2
        import numpy as np
    except ImportError as exc:
        return {"status": "skipped", "reason": f"OpenCV render dependency unavailable: {exc}"}

    if not any(slide.get("source_images") for slide in slides):
        return {
            "status": "skipped",
            "reason": "No source images supplied for local preview renderer.",
            "slides": [],
        }

    def read_image(path: str) -> Any:
        image = cv2.imdecode(np.fromfile(path, dtype=np.uint8), cv2.IMREAD_COLOR)
        if image is None:
            raise RuntimeError(f"Could not read image: {path}")
        return image

    def cover_resize(image: Any, width: int, height: int) -> Any:
        h, w = image.shape[:2]
        scale = max(width / w, height / h)
        resized = cv2.resize(image, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_LANCZOS4)
        rh, rw = resized.shape[:2]
        x = max(0, (rw - width) // 2)
        y = max(0, (rh - height) // 2)
        return resized[y : y + height, x : x + width]

    def wrap(text: str, limit: int) -> list[str]:
        lines: list[str] = []
        current: list[str] = []
        for word in text.split():
            candidate = " ".join([*current, word])
            if len(candidate) > limit and current:
                lines.append(" ".join(current))
                current = [word]
            else:
                current.append(word)
        if current:
            lines.append(" ".join(current))
        return lines

    def stylize(image: Any) -> Any:
        small = cv2.resize(image, None, fx=0.55, fy=0.55, interpolation=cv2.INTER_AREA)
        smooth = cv2.pyrMeanShiftFiltering(small, sp=18, sr=34)
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        gray = cv2.medianBlur(gray, 7)
        edges = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 9, 5)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        poster = np.clip(np.round(smooth.astype(np.float32) / 32) * 32, 0, 255).astype(np.uint8)
        cartoon = cv2.bitwise_and(poster, edges)
        return cv2.resize(cartoon, (image.shape[1], image.shape[0]), interpolation=cv2.INTER_CUBIC)

    def write_jpg(path: Path, image: Any) -> None:
        ok, encoded = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 88])
        if not ok:
            raise RuntimeError(f"Could not encode {path}")
        path.write_bytes(encoded.tobytes())

    for folder in ["legacy-preview-clean", "legacy-preview-text"]:
        (out_dir / folder).mkdir(parents=True, exist_ok=True)

    rendered = []
    for slide in slides:
        source_images = slide.get("source_images") or []
        if not source_images:
            rendered.append(
                {
                    "slide": slide["slide"],
                    "status": "skipped",
                    "reason": "No source images supplied for this slide.",
                }
            )
            continue
        source = source_images[0]
        try:
            image = stylize(read_image(source))
        except Exception as exc:  # noqa: BLE001 - best-effort renderer should not break package creation.
            return {"status": "partial", "reason": str(exc), "slides": rendered}

        clean = cover_resize(image, 1080, 1350)
        text_preview = clean.copy()
        copy_lines = wrap(slide["copy"], 30)
        panel_height = 85 + (len(copy_lines) * 63)
        overlay = text_preview.copy()
        cv2.rectangle(overlay, (48, 42), (1032, panel_height), (236, 226, 207), -1)
        text_preview = cv2.addWeighted(overlay, 0.72, text_preview, 0.28, 0)
        y = 95
        for line in copy_lines:
            cv2.putText(text_preview, line, (72, y), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (42, 38, 33), 3, cv2.LINE_AA)
            y += 63
        cv2.putText(text_preview, f"{slide['slide']:02d} / {len(slides):02d}", (72, 1272), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (92, 86, 76), 1, cv2.LINE_AA)
        cv2.putText(text_preview, "@a.storyof.two", (780, 1272), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (92, 86, 76), 1, cv2.LINE_AA)

        number = f"{slide['slide']:02d}"
        outputs = {
            "legacy_preview_clean": f"legacy-preview-clean/slide-{number}.jpg",
            "legacy_preview_text": f"legacy-preview-text/slide-{number}.jpg",
        }
        write_jpg(out_dir / outputs["legacy_preview_clean"], clean)
        write_jpg(out_dir / outputs["legacy_preview_text"], text_preview)
        rendered.append({"slide": slide["slide"], "source": source, "outputs": outputs})

    return {"status": "rendered", "mode": "local_cv2_stylized_render", "slides": rendered}
