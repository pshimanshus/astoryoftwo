"""
Quality spine for Codex-native illustrated carousel packages.

The creative pipeline builds the package. This module records what was expected,
what was produced, what reviewers checked, and what the wiki should remember.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.stages.carousel_style_consistency import prompt_style_drift_issues
from pipeline.stages.successful_carousel_standard import (
    SUCCESSFUL_CAROUSEL_STANDARD_PATH,
    evaluate_successful_carousel_standard,
)


QUALITY_ARTIFACTS = {
    "run_ledger": "run-ledger.json",
    "stage_reviews": "stage-reviews.json",
    "final_audit": "final-audit.json",
    "wiki_update": "wiki-update.md",
    "visual_qa": "visual-qa.md",
}

BASE_ARTIFACTS = {
    "manifest": "manifest.json",
    "concept": "concept.json",
    "post_copy_visual_room": "post-copy-visual-room.json",
    "visual_debate": "visual-debate.json",
    "visual_plan_quality": "visual-plan-quality.json",
    "slides": "slides.json",
    "prompt_pack": "prompt-pack.json",
    "identity_dossier": "identity-dossier.json",
    "identity_generation_preflight": "identity-generation-preflight.md",
    "identity_face_contact_sheet": "identity-face-contact-sheet.jpg",
    "identity_consistency_review": "identity-consistency-review.json",
    "copy": "copy.json",
    "review": "review.json",
    "approval": "final-approval.md",
    "storyboard": "storyboard.md",
    "agent_reports": "agent-reports.md",
    "image_generation": "image-generation.json",
    "final_images": "final-images.json",
}

MIN_STORY_SLIDES = 4
MAX_STORY_SLIDES = 10

FORBIDDEN_FINAL_SOURCE_PARTS = {
    "source-generated-local",
    "hd-clean",
    "hd-story",
    "instagram-clean",
    "instagram-story",
}

REQUIRED_VISUAL_QA_CHECKS = {
    "storyboard",
    "aachu_face",
    "zuv_face",
    "dress_continuity",
    "style",
    "scene_logic",
    "pose_anatomy",
    "model_native_text",
    "final_files",
}

FACE_VISUAL_QA_CHECKS = {
    "aachu_face": "Aachu/Anchal",
    "zuv_face": "Himanshu/Zuv",
}

PUBLISHABLE_FINAL_GENERATION_MODES = {
    "model_native_publishable",
    "model_art_local_text_publishable",
}


@dataclass(frozen=True)
class QualityContext:
    story: str
    title: str
    slug: str
    today: date
    out_dir: Path
    image_paths: list[Path]
    slide_count: int
    package: dict[str, Any]
    manifest: dict[str, Any]
    render_result: dict[str, Any]
    workspace_root: Path


def write_json(path: Path, data: Any) -> None:
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def status_from_issues(issues: list[str], notes: list[str] | None = None) -> str:
    if issues:
        return "NEEDS_FIXES"
    if notes:
        return "PASS_WITH_NOTES"
    return "PASS"


def required_artifacts() -> dict[str, str]:
    artifacts = dict(BASE_ARTIFACTS)
    artifacts.update(QUALITY_ARTIFACTS)
    return artifacts


def build_requirements(context: QualityContext) -> list[dict[str, Any]]:
    return [
        {
            "id": "REQ-STYLE-001",
            "label": "Use romantic watercolor-and-ink / identity-rooted illustration style",
            "source": "creator master-prompt style requirement",
            "evidence": ["prompt_pack.shared_style_prompt", "concept.visual_style"],
            "critical": True,
        },
        {
            "id": "REQ-HOUSE-STYLE-SCENE-001",
            "label": "Final prompts stay scene-first in the @a.storyof.two house style",
            "source": "creator style-consistency correction on 2026-05-24",
            "evidence": ["prompt_pack.slides[].prompt"],
            "critical": True,
        },
        {
            "id": "REQ-PHOTO-001",
            "label": "Preserve supplied photo cues, outfits, settings, poses, and relationship energy",
            "source": "C-layer framework",
            "evidence": ["slides[].source_images", "prompt_pack.slides[].prompt"],
            "critical": True,
        },
        {
            "id": "REQ-IDENTITY-001",
            "label": "Aachu/Zuv identity reference is present in manifest and prompt pack",
            "source": "user face-consistency requirement",
            "critical": True,
        },
        {
            "id": "REQ-IDENTITY-DOSSIER-001",
            "label": "Identity dossier, preflight checklist, and face contact sheet are present before image generation",
            "source": "user face-consistency requirement",
            "critical": True,
        },
        {
            "id": "REQ-IDENTITY-CONSISTENCY-001",
            "label": "Face structure, expressions, clothing, and cross-slide identity continuity are reviewed before image generation",
            "source": "user identity-consistency gate requirement",
            "critical": True,
        },
        {
            "id": "REQ-POST-COPY-VISUAL-ROOM-001",
            "label": "Run the post-copy visual creative room after approved copy and before prompt/image handoff",
            "source": "creator mandatory visual-room workflow",
            "critical": True,
        },
        {
            "id": "REQ-VISUAL-PLAN-QUALITY-001",
            "label": "Per-slide visual screen passes before image generation",
            "source": "user pre-generation storyboard QA requirement",
            "critical": True,
        },
        {
            "id": "REQ-SLIDES-001",
            "label": "Create an approved 4-10 slide carousel arc, matching prompt count",
            "source": "/story contract",
            "expected": context.slide_count,
            "critical": True,
        },
        {
            "id": "REQ-SUCCESS-STANDARD-001",
            "label": "Successful carousel standard is carried as open agent alignment and passes before final approval",
            "source": SUCCESSFUL_CAROUSEL_STANDARD_PATH,
            "evidence": [
                "concept.successful_carousel_standard",
                "prompt_pack.successful_carousel_standard",
                "review.successful_carousel_standard_gate",
            ],
            "critical": True,
        },
        {
            "id": "REQ-FINAL-IMAGES-001",
            "label": "Final generated carousel images are packaged as separate native 4:5 and 9:16 outputs, not local placeholders",
            "source": "user final-output requirement",
            "expected": context.slide_count,
            "critical": True,
        },
        {
            "id": "REQ-MODEL-NATIVE-TEXT-001",
            "label": "Default final slides include rendered copy and brandmark inside both final/ and final-reels-stories/",
            "source": "user publishable composition requirement",
            "expected": context.slide_count,
            "critical": True,
        },
        {
            "id": "REQ-VISUAL-QA-001",
            "label": "Structured face and storyboard visual QA gate passes with evidence",
            "source": "user face/storyboard QA requirement",
            "critical": True,
        },
        {
            "id": "REQ-BRAND-001",
            "label": "Keep @a.storyof.two as a tiny, low-contrast bottom-right brandmark",
            "source": "brandmark rule",
            "critical": True,
        },
        {
            "id": "REQ-NEGATIVE-001",
            "label": "Block photorealism, 3D rendering, generic stock couple art, and quote-card layout",
            "source": "negative prompt contract",
            "critical": True,
        },
        {
            "id": "REQ-OUTPUT-001",
            "label": "Write complete C-layer artifact contract",
            "source": "AGENTS.md C-layer output",
            "expected": sorted(required_artifacts().values()),
            "critical": True,
        },
        {
            "id": "REQ-WIKI-001",
            "label": "Enrich wiki, index, working memory, and graph memory after the run",
            "source": "Rohit v2 wiki memory lifecycle",
            "critical": True,
        },
    ]


def build_run_ledger(context: QualityContext) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "observer": {
            "agent": "C0.5-Jarvis",
            "role": "Track requirements, stage completion, reviewer findings, and final gate status.",
        },
        "run": {
            "date": str(context.today),
            "title": context.title,
            "slug": context.slug,
            "channel": "@a.storyof.two",
            "pipeline": "C-layer illustrated carousel",
            "runtime": context.manifest.get("runtime", "codex_native_local"),
            "output_dir": str(context.out_dir),
        },
        "source_inputs": {
            "story": context.story,
            "slide_count": context.slide_count,
            "reference_images": [str(path) for path in context.image_paths],
        },
        "requirements": build_requirements(context),
        "expected_artifacts": required_artifacts(),
        "stage_statuses": {
            "intake": "PENDING",
            "story": "PENDING",
            "arc": "PENDING",
            "visual": "PENDING",
            "identity_consistency": "PENDING",
            "prompt": "PENDING",
            "copy": "PENDING",
            "success_standard": "PENDING",
            "assets": "PENDING",
            "wiki_learning": "PENDING",
            "final_contract": "PENDING",
        },
        "final_gate": {
            "status": "PENDING",
            "pass": False,
            "notes": [],
        },
    }


def prompt_pack(context: QualityContext) -> dict[str, Any]:
    return context.package.get("prompt_pack", {})


def identity_consistency_review(context: QualityContext) -> dict[str, Any]:
    value = context.package.get("identity_consistency_review")
    if isinstance(value, dict):
        return value
    path = context.out_dir / BASE_ARTIFACTS["identity_consistency_review"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def visual_plan_quality(context: QualityContext) -> dict[str, Any]:
    value = context.package.get("visual_plan_quality")
    if isinstance(value, dict):
        return value
    path = context.out_dir / BASE_ARTIFACTS["visual_plan_quality"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def post_copy_visual_room(context: QualityContext) -> dict[str, Any]:
    value = context.package.get("post_copy_visual_room")
    if isinstance(value, dict):
        return value
    path = context.out_dir / BASE_ARTIFACTS["post_copy_visual_room"]
    if path.exists():
        return json.loads(path.read_text(encoding="utf-8"))
    return {}


def is_identity_only_context(context: QualityContext) -> bool:
    prompt_refs = prompt_pack(context).get("identity_reference_images", [])
    manifest_refs = context.manifest.get("identity_references", [])
    return not context.image_paths and bool(prompt_refs) and bool(manifest_refs)


def slides(context: QualityContext) -> list[dict[str, Any]]:
    value = context.package.get("slides", [])
    return value if isinstance(value, list) else []


def review_item(stage: str, expected: list[str], done: list[str], issues: list[str], notes: list[str] | None = None) -> dict[str, Any]:
    notes = notes or []
    return {
        "stage": stage,
        "status": status_from_issues(issues, notes),
        "expected": expected,
        "done": done,
        "issues": issues,
        "notes": notes,
    }


def final_image_gate(context: QualityContext, final_files: list[Path]) -> dict[str, Any]:
    final_manifest_path = context.out_dir / BASE_ARTIFACTS["final_images"]
    issues: list[str] = []
    manifest: dict[str, Any] = {}
    required_formats = ["instagram_post", "reels_stories"]
    if final_manifest_path.exists():
        manifest = json.loads(final_manifest_path.read_text(encoding="utf-8"))
    else:
        issues.append("final-images.json is missing.")

    if not all(path.exists() for path in final_files):
        missing = [str(path) for path in final_files if not path.exists()]
        issues.append("Missing final images: " + ", ".join(missing))

    if manifest:
        if manifest.get("status") not in {"packaged", "generated"}:
            issues.append(f"final-images.json status is {manifest.get('status')!r}, expected 'packaged' or 'generated'.")
        contract_formats = manifest.get("native_output_contract", {}).get("formats", [])
        if contract_formats != required_formats:
            issues.append(
                "final-images.json native output contract must require exactly: "
                + ", ".join(required_formats)
            )
        records = manifest.get("slides", [])
        if len(records) != context.slide_count:
            issues.append(f"final-images.json has {len(records)} slide records, expected {context.slide_count}.")
        for record in records:
            number = int(record.get("slide", 0) or 0)
            expected_file = context.out_dir / "final" / f"slide-{number:02d}.png"
            expected_reels_file = context.out_dir / "final-reels-stories" / f"slide-{number:02d}.png"
            actual_file = Path(record.get("file", ""))
            if actual_file and actual_file != expected_file:
                issues.append(f"Slide {number} final path is {actual_file}, expected {expected_file}.")
            actual_reels_file = Path(record.get("reels_stories_file", ""))
            if actual_reels_file and actual_reels_file != expected_reels_file:
                issues.append(
                    f"Slide {number} Reels/Stories final path is {actual_reels_file}, expected {expected_reels_file}."
                )
            if not expected_reels_file.exists():
                issues.append(f"Missing Reels/Stories final image: {expected_reels_file}.")

            native_outputs = record.get("native_outputs", {})
            if not isinstance(native_outputs, dict):
                native_outputs = {}
            missing_formats = [name for name in required_formats if name not in native_outputs]
            if missing_formats:
                issues.append(
                    f"Slide {number} native_outputs missing required format(s): "
                    + ", ".join(missing_formats)
                )
                continue

            instagram_output = native_outputs["instagram_post"]
            reels_output = native_outputs["reels_stories"]
            instagram_source = str(instagram_output.get("source", ""))
            reels_source = str(reels_output.get("source", ""))
            if not instagram_source:
                issues.append(f"Slide {number} instagram_post native source provenance is missing.")
            if not reels_source:
                issues.append(f"Slide {number} reels_stories native source provenance is missing.")
            if instagram_source and reels_source and instagram_source == reels_source:
                issues.append(f"Slide {number} Instagram and Reels/Stories outputs use the same source image.")
            for format_name, source_text in [
                ("instagram_post", instagram_source),
                ("reels_stories", reels_source),
            ]:
                source_parts = set(Path(source_text).parts)
                forbidden = sorted(source_parts & FORBIDDEN_FINAL_SOURCE_PARTS)
                if forbidden:
                    issues.append(
                        f"Slide {number} {format_name} source uses forbidden local placeholder/preview path part(s): "
                        + ", ".join(forbidden)
                    )
            if Path(instagram_output.get("file", "")) != expected_file:
                issues.append(f"Slide {number} instagram_post native output file must be {expected_file}.")
            if Path(reels_output.get("file", "")) != expected_reels_file:
                issues.append(f"Slide {number} reels_stories native output file must be {expected_reels_file}.")

    return {
        "pass": not issues,
        "evidence": {
            "files": [
                str(path)
                for path in [
                    *final_files,
                    *[
                        context.out_dir / "final-reels-stories" / f"slide-{number:02d}.png"
                        for number in range(1, context.slide_count + 1)
                    ],
                ]
                if path.exists()
            ],
            "manifest": str(final_manifest_path) if final_manifest_path.exists() else None,
            "status": manifest.get("status") if manifest else None,
            "issues": issues,
        },
    }


def structured_visual_qa_gate(context: QualityContext) -> dict[str, Any]:
    qa_path = context.out_dir / "visual-qa.json"
    failed: list[str] = []
    checks: dict[str, Any] = {}
    if not qa_path.exists():
        failed.append("visual-qa.json is missing; visual-qa.md is only a review worksheet.")
    else:
        qa = json.loads(qa_path.read_text(encoding="utf-8"))
        raw_checks = qa.get("checks", {})
        if isinstance(raw_checks, list):
            checks = {str(item.get("id", "")): item for item in raw_checks if isinstance(item, dict)}
        elif isinstance(raw_checks, dict):
            checks = raw_checks
        else:
            failed.append("visual-qa.json checks must be an object or list.")

        missing = sorted(REQUIRED_VISUAL_QA_CHECKS - set(checks))
        if missing:
            failed.append("visual-qa.json missing required checks: " + ", ".join(missing))
        for check_id, check in checks.items():
            passed = check.get("pass") if isinstance(check, dict) else check is True
            if passed is not True:
                failed.append(f"visual-qa.json check failed: {check_id}")
        for check_id, person in FACE_VISUAL_QA_CHECKS.items():
            check = checks.get(check_id)
            if not isinstance(check, dict):
                failed.append(f"visual-qa.json {check_id} must include reference_option_ids and likeness_notes for {person}.")
                continue
            option_ids = check.get("reference_option_ids")
            notes = str(check.get("likeness_notes") or "").strip()
            if not isinstance(option_ids, list) or not option_ids or not all(str(item).startswith("ID") for item in option_ids):
                failed.append(f"visual-qa.json {check_id} must name contact-sheet reference_option_ids for {person}.")
            if len(notes) < 24:
                failed.append(f"visual-qa.json {check_id} must include specific likeness_notes for {person}.")

    return {
        "pass": not failed,
        "path": str(qa_path),
        "failed": failed,
    }


def build_stage_reviews(context: QualityContext, ledger: dict[str, Any]) -> dict[str, Any]:
    package_slides = slides(context)
    prompts = prompt_pack(context).get("slides", [])
    identity_review = identity_consistency_review(context)
    post_copy_room = post_copy_visual_room(context)
    visual_quality = visual_plan_quality(context)
    shared_style = prompt_pack(context).get("shared_style_prompt", "")
    negative = prompt_pack(context).get("shared_negative_prompt", "")
    success_gate = evaluate_successful_carousel_standard(
        context.package,
        slide_count=context.slide_count,
    )
    render_status = context.render_result.get("status", "unknown")
    final_files = [
        context.out_dir / "final" / f"slide-{number:02d}.png"
        for number in range(1, context.slide_count + 1)
    ]

    intake_issues = []
    if not context.story.strip():
        intake_issues.append("Story text is empty.")
    identity_only = is_identity_only_context(context)
    if not context.image_paths and not identity_only:
        intake_issues.append("No reference images were supplied.")
    missing_paths = [str(path) for path in context.image_paths if not path.exists()]
    if missing_paths:
        intake_issues.append("Missing reference image paths: " + ", ".join(missing_paths))

    slide_issues = []
    if context.slide_count < MIN_STORY_SLIDES or context.slide_count > MAX_STORY_SLIDES:
        slide_issues.append(f"Slide count must be between {MIN_STORY_SLIDES} and {MAX_STORY_SLIDES}.")
    if len(package_slides) != context.slide_count:
        slide_issues.append(f"slides.json has {len(package_slides)} slides, expected {context.slide_count}.")
    if len(prompts) != context.slide_count:
        slide_issues.append(f"prompt-pack.json has {len(prompts)} slide prompts, expected {context.slide_count}.")

    visual_issues = []
    if not post_copy_room:
        visual_issues.append("post-copy-visual-room.json is missing.")
    elif post_copy_room.get("status") != "GO":
        visual_issues.append(
            f"post-copy-visual-room.json status is {post_copy_room.get('status')}."
        )
    for slide in package_slides:
        required_visual_fields = ["copy", "role", "visual", "emotion", "cta_intent"]
        if not identity_only:
            required_visual_fields.append("source_images")
        missing = [
            field
            for field in required_visual_fields
            if not slide.get(field)
        ]
        if missing:
            visual_issues.append(f"Slide {slide.get('slide', '?')} missing: {', '.join(missing)}.")
    if not visual_quality:
        visual_issues.append("visual-plan-quality.json is missing.")
    else:
        if visual_quality.get("status") != "PASS" or not visual_quality.get("can_generate"):
            visual_issues.extend(
                visual_quality.get("issues")
                or ["visual-plan-quality.json did not pass the pre-generation screen."]
            )
        if len(visual_quality.get("slide_reviews", [])) != context.slide_count:
            visual_issues.append(
                f"visual-plan-quality.json has {len(visual_quality.get('slide_reviews', []))} slide records, expected {context.slide_count}."
            )

    identity_issues = []
    dossier_path = context.out_dir / "identity-dossier.json"
    preflight_path = context.out_dir / "identity-generation-preflight.md"
    contact_sheet_path = context.out_dir / "identity-face-contact-sheet.jpg"
    if not dossier_path.exists():
        identity_issues.append("identity-dossier.json is missing.")
    if not preflight_path.exists():
        identity_issues.append("identity-generation-preflight.md is missing.")
    if not contact_sheet_path.exists():
        identity_issues.append("identity-face-contact-sheet.jpg is missing.")
    if not prompt_pack(context).get("identity_dossier_reference_images"):
        identity_issues.append("prompt-pack.json missing identity_dossier_reference_images.")
    if not identity_review:
        identity_issues.append("identity-consistency-review.json is missing.")
    else:
        if identity_review.get("status") != "PASS":
            identity_issues.extend(identity_review.get("issues") or ["Identity consistency review did not pass."])
        if len(identity_review.get("slides", [])) != context.slide_count:
            identity_issues.append(
                f"identity-consistency-review.json has {len(identity_review.get('slides', []))} slide records, expected {context.slide_count}."
            )
    for slide in package_slides:
        continuity = slide.get("identity_continuity", {})
        missing = [
            field
            for field in ["face_structure", "facial_expression", "clothing", "cross_slide_consistency"]
            if not continuity.get(field)
        ]
        if missing:
            identity_issues.append(
                f"Slide {slide.get('slide', '?')} missing identity continuity fields: {', '.join(missing)}."
            )

    prompt_issues = []
    style_lower = shared_style.lower()
    if "watercolor" not in style_lower or "ink" not in style_lower:
        prompt_issues.append("Shared style prompt does not specify watercolor-and-ink illustration.")
    if "hand-drawn" not in style_lower and "hand drawn" not in style_lower:
        prompt_issues.append("Shared style prompt does not specify hand-drawn illustration.")
    if "photo" not in style_lower and "reference" not in style_lower:
        prompt_issues.append("Shared style prompt does not explicitly preserve photo/reference details.")
    prompt_issues.extend(prompt_style_drift_issues(prompt_pack(context)))
    negative_lower = negative.lower()
    for required_negative in ["photorealism", "3d", "stock", "quote-card"]:
        if required_negative not in negative_lower:
            prompt_issues.append(f"Negative prompt missing '{required_negative}'.")
    for prompt in prompts:
        if "identity continuity lock" not in prompt.get("prompt", "").lower():
            prompt_issues.append(f"Slide {prompt.get('slide', '?')} prompt missing Identity continuity lock.")

    copy_pack = context.package.get("copy", {})
    copy_issues = []
    if not copy_pack.get("caption_recommended"):
        copy_issues.append("Recommended caption is missing.")
    if not copy_pack.get("alt_text"):
        copy_issues.append("Alt text list is missing.")

    asset_notes = []
    asset_issues = []
    if render_status == "skipped":
        asset_notes.append(context.render_result.get("reason", "Asset rendering skipped."))
    elif render_status in {"dry_run_generated", "legacy_preview_generated"}:
        asset_notes.append(
            context.render_result.get(
                "reason",
                "Preview/dry-run images were generated, but they are not publishable final art.",
            )
        )
    elif render_status not in {"rendered", "partial", "generated"}:
        asset_issues.append(f"Unexpected render status: {render_status}.")
    if not all(path.exists() for path in final_files):
        missing = [str(path) for path in final_files if not path.exists()]
        asset_issues.append("Missing final generated images: " + ", ".join(missing))

    wiki_notes = [
        "Wiki and memory files are updated after final audit generation.",
    ]

    reviews = {
        "intake_reviewer": review_item(
            "intake",
            ["story captured", "reference images exist", "slide count accepted"],
            [
                "identity-only concept-led run" if identity_only else f"{len(context.image_paths)} reference image(s)",
                f"{context.slide_count} requested slide(s)",
            ],
            intake_issues,
            ["No story photos supplied; identity references and the creative brief are the source of truth."]
            if identity_only
            else [],
        ),
        "story_reviewer": review_item(
            "story",
            ["human truth present", "source story preserved"],
            [context.package.get("concept", {}).get("human_truth", "")],
            [] if context.package.get("concept", {}).get("human_truth") else ["Human truth is missing."],
        ),
        "arc_reviewer": review_item(
            "arc",
            ["slide plan count matches request", "prompt count matches slide plan"],
            [f"{len(package_slides)} planned slide(s)", f"{len(prompts)} prompt slide(s)"],
            slide_issues,
        ),
        "visual_reviewer": review_item(
            "visual",
            [
                "every slide has copy, role, visual, emotion, CTA intent, and source images",
                "post-copy visual room runs after copy lock",
                "pre-generation visual screen passes before image handoff",
            ],
            [
                f"checked {len(package_slides)} slide(s)",
                f"post-copy visual room: {post_copy_room.get('status', 'missing')}",
                f"visual screen: {visual_quality.get('status', 'missing')}",
            ],
            visual_issues,
        ),
        "identity_consistency_reviewer": review_item(
            "identity_consistency",
            [
                "selected identity bundle is present",
                "each slide locks face structure",
                "each slide locks facial expression",
                "each slide locks clothing/body-language cues",
                "each prompt includes Identity continuity lock before generation",
            ],
            [
                f"{len(identity_review.get('identity_references', [])) if identity_review else 0} identity reference(s)",
                f"{len(identity_review.get('slides', [])) if identity_review else 0} reviewed slide(s)",
            ],
            identity_issues,
        ),
        "prompt_reviewer": review_item(
            "prompt",
            ["shared style prompt", "shared negative prompt", "self-contained slide prompts"],
            ["style prompt present" if shared_style else "style prompt missing", "negative prompt present" if negative else "negative prompt missing"],
            prompt_issues,
        ),
        "copy_reviewer": review_item(
            "copy",
            ["caption", "alt text", "posting notes"],
            [key for key in ["caption_recommended", "alt_text", "posting_notes"] if copy_pack.get(key)],
            copy_issues,
        ),
        "success_standard_reviewer": review_item(
            "success_standard",
            [
                "open agent alignment to the success goals",
                "relationship-first premise",
                "Story-Selling / golden-theme / story-director support",
                "visual-room and visual-plan support",
                "prompt-level success-goal handoff",
            ],
            [
                f"standard source: {success_gate['source']}",
                f"gate: {success_gate['status']}",
            ],
            success_gate["issues"],
        ),
        "asset_reviewer": review_item(
            "assets",
            ["local preview status recorded", "final generated images packaged"],
            [f"render status: {render_status}", f"final images present: {sum(path.exists() for path in final_files)} / {context.slide_count}"],
            asset_issues,
            asset_notes,
        ),
        "wiki_learning_reviewer": review_item(
            "wiki_learning",
            ["wiki page", "wiki index link", "working memory entry", "graph entity"],
            ["scheduled wiki and memory updates"],
            [],
            wiki_notes,
        ),
    }

    stage_statuses = {
        "intake": reviews["intake_reviewer"]["status"],
        "story": reviews["story_reviewer"]["status"],
        "arc": reviews["arc_reviewer"]["status"],
        "visual": reviews["visual_reviewer"]["status"],
        "identity_consistency": reviews["identity_consistency_reviewer"]["status"],
        "prompt": reviews["prompt_reviewer"]["status"],
        "copy": reviews["copy_reviewer"]["status"],
        "success_standard": reviews["success_standard_reviewer"]["status"],
        "assets": reviews["asset_reviewer"]["status"],
        "wiki_learning": reviews["wiki_learning_reviewer"]["status"],
        "final_contract": "PENDING",
    }
    ledger["stage_statuses"].update(stage_statuses)

    return {
        "schema_version": "1.0",
        "observer": ledger["observer"],
        "reviews": reviews,
    }


def evaluate_requirements(context: QualityContext) -> dict[str, dict[str, Any]]:
    package_slides = slides(context)
    prompts = prompt_pack(context).get("slides", [])
    identity_review = identity_consistency_review(context)
    post_copy_room = post_copy_visual_room(context)
    visual_quality = visual_plan_quality(context)
    shared_style = prompt_pack(context).get("shared_style_prompt", "")
    negative = prompt_pack(context).get("shared_negative_prompt", "")
    identity_refs = context.manifest.get("identity_references", [])
    identity_prompt_refs = prompt_pack(context).get("identity_reference_images", [])
    style_lower = shared_style.lower()
    negative_lower = negative.lower()

    results: dict[str, dict[str, Any]] = {}
    results["REQ-STYLE-001"] = {
        "pass": ("watercolor" in style_lower and "ink" in style_lower)
        and ("hand-drawn" in style_lower or "hand drawn" in style_lower)
        and ("photo" in style_lower or "reference" in style_lower),
        "evidence": shared_style,
    }
    style_drift_issues = prompt_style_drift_issues(prompt_pack(context))
    results["REQ-HOUSE-STYLE-SCENE-001"] = {
        "pass": not style_drift_issues,
        "evidence": style_drift_issues or "No artifact/poster prompt drift detected.",
    }
    results["REQ-PHOTO-001"] = {
        "pass": (
            all(slide.get("source_images") for slide in package_slides)
            or is_identity_only_context(context)
        )
        and all("reference" in prompt.get("prompt", "").lower() or "photo" in prompt.get("prompt", "").lower() for prompt in prompts),
        "evidence": (
            "identity-only concept-led run using identity references and creative brief"
            if is_identity_only_context(context)
            else f"{len(package_slides)} slide(s), {len(prompts)} prompt(s)"
        ),
    }
    results["REQ-IDENTITY-001"] = {
        "pass": bool(identity_refs) and bool(identity_prompt_refs),
        "evidence": {"manifest": identity_refs, "prompt_pack": identity_prompt_refs},
    }
    dossier_path = context.out_dir / "identity-dossier.json"
    preflight_path = context.out_dir / "identity-generation-preflight.md"
    contact_sheet_path = context.out_dir / "identity-face-contact-sheet.jpg"
    dossier_prompt_refs = prompt_pack(context).get("identity_dossier_reference_images", [])
    results["REQ-IDENTITY-DOSSIER-001"] = {
        "pass": dossier_path.exists()
        and preflight_path.exists()
        and contact_sheet_path.exists()
        and bool(dossier_prompt_refs)
        and str(contact_sheet_path) in [str(path) for path in dossier_prompt_refs],
        "evidence": {
            "dossier": str(dossier_path) if dossier_path.exists() else None,
            "preflight": str(preflight_path) if preflight_path.exists() else None,
            "contact_sheet": str(contact_sheet_path) if contact_sheet_path.exists() else None,
            "prompt_refs": dossier_prompt_refs,
        },
    }
    identity_issues: list[str] = []
    if not identity_review:
        identity_issues.append("identity-consistency-review.json is missing.")
    elif identity_review.get("status") != "PASS":
        identity_issues.extend(identity_review.get("issues") or ["Identity consistency review did not pass."])
    if identity_review and len(identity_review.get("slides", [])) != context.slide_count:
        identity_issues.append(
            f"identity-consistency-review.json has {len(identity_review.get('slides', []))} slide records, expected {context.slide_count}."
        )
    for slide in package_slides:
        continuity = slide.get("identity_continuity", {})
        missing = [
            field
            for field in ["face_structure", "facial_expression", "clothing", "cross_slide_consistency"]
            if not continuity.get(field)
        ]
        if missing:
            identity_issues.append(
                f"Slide {slide.get('slide', '?')} missing identity continuity fields: {', '.join(missing)}."
            )
    for prompt in prompts:
        if "identity continuity lock" not in prompt.get("prompt", "").lower():
            identity_issues.append(f"Slide {prompt.get('slide', '?')} prompt missing Identity continuity lock.")
    results["REQ-IDENTITY-CONSISTENCY-001"] = {
        "pass": bool(identity_refs) and bool(identity_prompt_refs) and not identity_issues,
        "evidence": {
            "identity_review": str(context.out_dir / BASE_ARTIFACTS["identity_consistency_review"])
            if (context.out_dir / BASE_ARTIFACTS["identity_consistency_review"]).exists()
            else None,
            "status": identity_review.get("status") if identity_review else None,
            "issues": identity_issues,
        },
    }
    post_copy_issues: list[str] = []
    if not post_copy_room:
        post_copy_issues.append("post-copy-visual-room.json is missing.")
    else:
        if post_copy_room.get("status") != "GO":
            post_copy_issues.append(f"post-copy-visual-room.json status is {post_copy_room.get('status')}.")
        if len(post_copy_room.get("visual_system_candidates", [])) < 3:
            post_copy_issues.append("post-copy visual room must compare at least three visual systems.")
        if not post_copy_room.get("slide_visual_blueprint"):
            post_copy_issues.append("post-copy visual room must include slide_visual_blueprint.")
    results["REQ-POST-COPY-VISUAL-ROOM-001"] = {
        "pass": not post_copy_issues,
        "evidence": {
            "path": str(context.out_dir / BASE_ARTIFACTS["post_copy_visual_room"]),
            "status": post_copy_room.get("status") if post_copy_room else None,
            "decision": post_copy_room.get("decision") if post_copy_room else None,
            "selected_visual_system": post_copy_room.get("selected_visual_system") if post_copy_room else None,
            "issues": post_copy_issues,
        },
    }
    visual_quality_issues: list[str] = []
    if not visual_quality:
        visual_quality_issues.append("visual-plan-quality.json is missing.")
    else:
        if visual_quality.get("status") != "PASS":
            visual_quality_issues.append(
                f"visual-plan-quality.json status is {visual_quality.get('status')}."
            )
        if not visual_quality.get("can_generate"):
            visual_quality_issues.append("visual-plan-quality.json blocks image generation.")
        visual_quality_issues.extend(visual_quality.get("issues", []))
        if len(visual_quality.get("slide_reviews", [])) != context.slide_count:
            visual_quality_issues.append(
                f"visual-plan-quality.json has {len(visual_quality.get('slide_reviews', []))} slide records, expected {context.slide_count}."
            )
    results["REQ-VISUAL-PLAN-QUALITY-001"] = {
        "pass": not visual_quality_issues,
        "evidence": {
            "path": str(context.out_dir / BASE_ARTIFACTS["visual_plan_quality"]),
            "status": visual_quality.get("status") if visual_quality else None,
            "decision": visual_quality.get("decision") if visual_quality else None,
            "issues": visual_quality_issues,
        },
    }
    results["REQ-SLIDES-001"] = {
        "pass": MIN_STORY_SLIDES <= context.slide_count <= MAX_STORY_SLIDES
        and len(package_slides) == context.slide_count
        and len(prompts) == context.slide_count,
        "evidence": f"requested={context.slide_count}, slides={len(package_slides)}, prompts={len(prompts)}",
    }
    success_gate = evaluate_successful_carousel_standard(
        context.package,
        slide_count=context.slide_count,
    )
    results["REQ-SUCCESS-STANDARD-001"] = {
        "pass": success_gate["pass"],
        "evidence": success_gate,
    }
    final_files = [
        context.out_dir / "final" / f"slide-{number:02d}.png"
        for number in range(1, context.slide_count + 1)
    ]
    results["REQ-FINAL-IMAGES-001"] = final_image_gate(context, final_files)
    model_native_manifest_path = context.out_dir / BASE_ARTIFACTS["final_images"]
    model_native_issues: list[str] = []
    model_native_manifest: dict[str, Any] = {}
    if model_native_manifest_path.exists():
        model_native_manifest = json.loads(model_native_manifest_path.read_text(encoding="utf-8"))
    else:
        model_native_issues.append("final-images.json is missing.")
    if not all(path.exists() for path in final_files):
        missing = [str(path) for path in final_files if not path.exists()]
        model_native_issues.append("Missing publishable final slides: " + ", ".join(missing))
    if model_native_manifest:
        if model_native_manifest.get("backend") not in {"codex_builtin", "model_art_local_text"}:
            model_native_issues.append(
                "final-images.json backend must be codex_builtin or model_art_local_text for Instagram-grade final art."
            )
        if model_native_manifest.get("generation_mode") not in PUBLISHABLE_FINAL_GENERATION_MODES:
            model_native_issues.append(
                "final-images.json generation_mode must be one of: "
                + ", ".join(sorted(PUBLISHABLE_FINAL_GENERATION_MODES))
            )
        records = model_native_manifest.get("slides", [])
        if len(records) != context.slide_count:
            model_native_issues.append(f"final-images.json has {len(records)} slide records, expected {context.slide_count}.")
        for record in records:
            if record.get("backend") not in {"codex_builtin", "model_art_local_text"}:
                model_native_issues.append(f"Slide {record.get('slide')} backend is not an approved final-art backend.")
            if record.get("generation_mode") not in PUBLISHABLE_FINAL_GENERATION_MODES:
                model_native_issues.append(f"Slide {record.get('slide')} is not marked as a publishable final generation mode.")
            if record.get("local_generated_source"):
                model_native_issues.append(f"Slide {record.get('slide')} uses local_generated_source as final art provenance.")
            native_outputs = record.get("native_outputs", {})
            if isinstance(native_outputs, dict):
                for format_name, native_output in native_outputs.items():
                    if isinstance(native_output, dict) and native_output.get("local_generated_source"):
                        model_native_issues.append(
                            f"Slide {record.get('slide')} {format_name} uses local_generated_source as final art provenance."
                        )
            file_text = str(record.get("file", ""))
            if "final-with-text" in file_text:
                model_native_issues.append(f"Slide {record.get('slide')} uses final-with-text as publishable output.")
            if not record.get("prompt"):
                model_native_issues.append(f"Slide {record.get('slide')} is missing source prompt provenance.")
    if (context.out_dir / "final-with-text").exists():
        model_native_issues.append(
            "final-with-text exists; default publishable runs must publish both final/slide-XX.png "
            "and final-reels-stories/slide-XX.png, not local overlays."
        )
    results["REQ-MODEL-NATIVE-TEXT-001"] = {
        "pass": not model_native_issues,
        "evidence": {
            "files": [str(path) for path in final_files if path.exists()],
            "manifest": str(model_native_manifest_path) if model_native_manifest_path.exists() else None,
            "generation_mode": model_native_manifest.get("generation_mode"),
            "issues": model_native_issues,
        },
    }
    visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
    structured_qa = structured_visual_qa_gate(context)
    if visual_qa_path.exists():
        visual_qa_text = visual_qa_path.read_text(encoding="utf-8")
        failed_checks = [
            line.strip()
            for line in visual_qa_text.splitlines()
            if line.strip().startswith("- [x] FAIL")
        ]
        unchecked_face_or_storyboard_items = [
            line.strip()
            for line in visual_qa_text.splitlines()
            if line.strip().startswith("- [ ]")
            and ("face" in line.lower() or "storyboard" in line.lower())
        ]
    else:
        failed_checks = ["visual-qa.md is missing"]
        unchecked_face_or_storyboard_items = []
    results["REQ-VISUAL-QA-001"] = {
        "pass": visual_qa_path.exists()
        and structured_qa["pass"]
        and not failed_checks
        and not unchecked_face_or_storyboard_items,
        "evidence": {
            "visual_qa": str(visual_qa_path),
            "structured_visual_qa": structured_qa["path"],
            "failed": [*structured_qa["failed"], *failed_checks],
            "unchecked_face_or_storyboard_items": unchecked_face_or_storyboard_items,
        },
    }
    results["REQ-BRAND-001"] = {
        "pass": prompt_pack(context).get("text_overlay_plan", {}).get("brandmark") == "@a.storyof.two"
        and "bottom-right" in prompt_pack(context).get("text_overlay_plan", {}).get("brandmark_placement", ""),
        "evidence": prompt_pack(context).get("text_overlay_plan", {}),
    }
    results["REQ-NEGATIVE-001"] = {
        "pass": all(token in negative_lower for token in ["photorealism", "3d", "stock", "quote-card"]),
        "evidence": negative,
    }
    results["REQ-OUTPUT-001"] = {
        "pass": all((context.out_dir / path).exists() for path in BASE_ARTIFACTS.values()),
        "evidence": [path for path in BASE_ARTIFACTS.values() if (context.out_dir / path).exists()],
    }
    wiki_evidence = {
        name: path.exists()
        for name, path in expected_wiki_paths(context).items()
    }
    results["REQ-WIKI-001"] = {
        "pass": all(wiki_evidence.values()),
        "evidence": wiki_evidence,
    }
    return results


def build_final_audit(
    context: QualityContext,
    ledger: dict[str, Any],
    stage_reviews: dict[str, Any],
) -> dict[str, Any]:
    requirement_results = evaluate_requirements(context)
    issues: list[str] = []
    notes: list[str] = []

    for requirement in ledger["requirements"]:
        result = requirement_results.get(requirement["id"], {"pass": False, "evidence": "No evaluator."})
        if requirement.get("critical") and not result["pass"]:
            issues.append(f"{requirement['id']}: {requirement['label']}")

    for name, review in stage_reviews["reviews"].items():
        if review["status"] == "NEEDS_FIXES":
            issues.append(f"{name}: " + "; ".join(review["issues"]))
        elif review["status"] == "PASS_WITH_NOTES":
            notes.extend(review["notes"])

    missing_base_artifacts = [
        path for path in BASE_ARTIFACTS.values() if not (context.out_dir / path).exists()
    ]
    if missing_base_artifacts:
        issues.append("Missing base artifacts: " + ", ".join(missing_base_artifacts))

    render_status = context.render_result.get("status")
    if render_status == "skipped":
        reason = context.render_result.get("reason", "render skipped")
        if reason not in notes:
            notes.append(reason)

    visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
    final_images_exist = all(
        (context.out_dir / "final" / f"slide-{number:02d}.png").exists()
        for number in range(1, context.slide_count + 1)
    )
    if visual_qa_path.exists():
        visual_qa_text = visual_qa_path.read_text(encoding="utf-8")
        failed_checks = [
            line.strip()
            for line in visual_qa_text.splitlines()
            if line.strip().startswith("- [x] FAIL")
        ]
        if failed_checks:
            issues.append("Visual QA failed: " + "; ".join(failed_checks))
    elif final_images_exist:
        issues.append("Final images exist but visual-qa.md is missing.")

    blocked = False
    for artifact_name in ["image-generation.json", "final-images.json"]:
        artifact_path = context.out_dir / artifact_name
        if artifact_path.exists():
            try:
                artifact_status = json.loads(artifact_path.read_text(encoding="utf-8")).get("status")
                blocked = artifact_status in {"BLOCKED", "blocked"} or blocked
            except json.JSONDecodeError:
                pass
    status = "BLOCKED" if blocked else status_from_issues(issues, notes)
    return {
        "schema_version": "1.0",
        "auditor": "C7-Final Contract Auditor",
        "status": status,
        "pass": status in {"PASS", "PASS_WITH_NOTES"},
        "requirements": requirement_results,
        "checked_artifacts": {
            path: (context.out_dir / path).exists()
            for path in BASE_ARTIFACTS.values()
        },
        "quality_artifacts": QUALITY_ARTIFACTS,
        "issues": issues,
        "notes": notes,
    }


def markdown_link(title: str, target: str) -> str:
    return f"[{title}]({target})"


def build_wiki_update(context: QualityContext, audit: dict[str, Any]) -> str:
    concept = context.package.get("concept", {})
    copy_pack = context.package.get("copy", {})
    lines = [
        f"# {context.title} - Carousel Quality Update",
        "",
        f"last_updated: {context.today}",
        "confidence: 0.7",
        "sources:",
        f"- {context.out_dir / 'manifest.json'}",
        f"- {context.out_dir / 'prompt-pack.json'}",
        f"- {context.out_dir / 'final-audit.json'}",
        "",
        "## Status",
        "",
        f"Final audit: {audit['status']}",
        "",
    ]
    if audit.get("issues"):
        lines.extend(["## Issues", ""])
        lines.extend(f"- {issue}" for issue in audit["issues"])
        lines.append("")
    if audit.get("notes"):
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in audit["notes"])
        lines.append("")
    lines.extend(
        [
            "## Human Truth",
            "",
            concept.get("human_truth", ""),
            "",
            "## Learning",
            "",
            "- Keep the romantic watercolor-and-ink / identity-rooted style as the default for memory-led carousels.",
            "- Preserve source-photo objects before adding decorative story elements.",
            "- Preserve Aachu/Zuv identity references across every generated slide.",
            "- Carry the successful-carousel standard as open agent alignment, not a keyword checklist.",
            "- Generate model-native publishable slides when typography, face quality, outfit continuity, and composition must match the reference examples.",
            "",
            "## Caption",
            "",
            copy_pack.get("caption_recommended", ""),
            "",
        ]
    )
    return "\n".join(lines)


def build_carousel_wiki_page(context: QualityContext, audit: dict[str, Any]) -> str:
    concept = context.package.get("concept", {})
    lines = [
        f"# {context.title}",
        "",
        f"last_updated: {context.today}",
        "confidence: 0.7",
        "sources:",
        f"- {context.out_dir / 'manifest.json'}",
        f"- {context.out_dir / 'slides.json'}",
        f"- {context.out_dir / 'prompt-pack.json'}",
        f"- {context.out_dir / 'final-audit.json'}",
        "",
        "## Summary",
        "",
        concept.get("human_truth", ""),
        "",
        "## Style Memory",
        "",
        "- Romantic watercolor-and-ink / identity-rooted illustration.",
        "- Fine ink and pencil linework, transparent watercolor blooms, muted vintage colors, warm ivory paper with visible paper grain.",
        "- Preserve real outfits, poses, settings, and relationship cues.",
        "- Use Aachu/Zuv identity references for recurring character likeness.",
        "- Keep the successful-carousel standard active as open agent alignment: public identity mirror, private receipts, active Zuv response, emotional turn, and send/save thesis.",
        "",
        "## Slide Flow",
        "",
    ]
    for slide in slides(context):
        lines.append(f"- Slide {slide.get('slide')}: {slide.get('copy')} - {slide.get('visual')}")
    lines.extend(
        [
            "",
            "## Final Audit",
            "",
            f"Status: {audit['status']}",
            "",
        ]
    )
    if audit.get("issues"):
        lines.extend(["## Issues", ""])
        lines.extend(f"- {issue}" for issue in audit["issues"])
        lines.append("")
    if audit.get("notes"):
        lines.extend(["## Notes", ""])
        lines.extend(f"- {note}" for note in audit["notes"])
        lines.append("")
    lines.extend(
        [
            "## Artifact Links",
            "",
            f"- {markdown_link('Run ledger', str(context.out_dir / 'run-ledger.json'))}",
            f"- {markdown_link('Stage reviews', str(context.out_dir / 'stage-reviews.json'))}",
            f"- {markdown_link('Final audit', str(context.out_dir / 'final-audit.json'))}",
            "",
        ]
    )
    return "\n".join(lines)


def update_index(index_path: Path, context: QualityContext) -> None:
    link = f"| [{context.title}](carousels/{context.slug}.md) | {context.today} | {context.slide_count} | C-layer | 0.7 |"
    if index_path.exists():
        text = index_path.read_text(encoding="utf-8")
    else:
        text = (
            "# Wiki Index - @a.storyof.two Knowledge Base\n\n"
            "last_updated: 0\n"
            "total_pages: 0\n"
            "confidence_floor: 0.4\n\n"
            "---\n"
        )

    text = text.replace("last_updated: 0", f"last_updated: {context.today}")
    if "## Carousels" not in text:
        insertion = (
            "\n## Carousels\n"
            "Illustrated carousel packages and their learning records.\n\n"
            "| Carousel | Date | Slides | Pipeline | Confidence |\n"
            "|----------|------|--------|----------|------------|\n"
            f"{link}\n"
        )
        if "## Insights" in text:
            text = text.replace("## Insights", insertion + "\n## Insights", 1)
        else:
            text = text.rstrip() + "\n" + insertion
    elif link not in text:
        marker = "|----------|------|--------|----------|------------|"
        if marker in text:
            text = text.replace(marker, marker + "\n" + link, 1)
        else:
            text = text.rstrip() + "\n" + link + "\n"

    text = replace_metadata_value(text, "last_updated", str(context.today))
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text(text, encoding="utf-8")


def expected_wiki_paths(context: QualityContext) -> dict[str, Path]:
    return {
        "carousel_page": context.workspace_root / "wiki" / "carousels" / f"{context.slug}.md",
        "wiki_index": context.workspace_root / "wiki" / "index.md",
        "working_memory": context.workspace_root / "memory" / "working.md",
        "graph_memory": context.workspace_root / "memory" / "graph.json",
    }


def replace_metadata_value(text: str, key: str, value: str) -> str:
    lines = text.splitlines()
    for index, line in enumerate(lines):
        if line.startswith(f"{key}:"):
            lines[index] = f"{key}: {value}"
            return "\n".join(lines) + "\n"
    return f"{key}: {value}\n" + text


def append_working_memory(memory_path: Path, context: QualityContext, audit: dict[str, Any]) -> None:
    if memory_path.exists():
        text = memory_path.read_text(encoding="utf-8").rstrip()
    else:
        text = "# Working Memory - Current Analysis Session\n"

    header = f"## C-layer carousel run: {context.title}"
    header_index = text.find(header)
    if header_index != -1:
        next_header_index = text.find("\n## ", header_index + len(header))
        if next_header_index == -1:
            text = text[:header_index].rstrip()
        else:
            text = (text[:header_index].rstrip() + "\n" + text[next_header_index:].lstrip()).rstrip()

    entry = "\n".join(
        [
            "",
            header,
            f"- date: {context.today}",
            f"- slug: {context.slug}",
            f"- final_audit: {audit['status']}",
            "- learning: romantic watercolor-and-ink / identity-rooted style remains the default for story carousels.",
            f"- package: {context.out_dir}",
        ]
    )
    memory_path.parent.mkdir(parents=True, exist_ok=True)
    memory_path.write_text(text + "\n" + entry + "\n", encoding="utf-8")


def update_graph(graph_path: Path, context: QualityContext, audit: dict[str, Any]) -> None:
    if graph_path.exists():
        graph = json.loads(graph_path.read_text(encoding="utf-8"))
    else:
        graph = {"entities": {}, "relationships": [], "themes": {}}

    graph.setdefault("entities", {})
    graph.setdefault("relationships", [])
    graph.setdefault("themes", {})

    entity_id = f"carousel:{context.slug}"
    graph["entities"][entity_id] = {
        "id": entity_id,
        "type": "illustrated_carousel",
        "title": context.title,
        "date": str(context.today),
        "status": audit["status"],
        "slide_count": context.slide_count,
        "package": str(context.out_dir),
        "content_lane": context.package.get("concept", {}).get("content_lane"),
    }
    graph["themes"].setdefault(
        "watercolor_ink_identity_rooted",
        {
            "id": "watercolor_ink_identity_rooted",
            "type": "creative_style",
            "confidence": 0.7,
            "description": "Premium romantic watercolor-and-ink illustration rooted in identity references and story photos.",
        },
    )
    relationship = {
        "from": entity_id,
        "to": "watercolor_ink_identity_rooted",
        "type": "uses_creative_style",
        "confidence": 0.7,
    }
    if relationship not in graph["relationships"]:
        graph["relationships"].append(relationship)
    graph["last_updated"] = str(context.today)

    graph_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(graph_path, graph)


def update_wiki_memory(context: QualityContext, audit: dict[str, Any]) -> None:
    wiki_dir = context.workspace_root / "wiki"
    carousel_dir = wiki_dir / "carousels"
    memory_dir = context.workspace_root / "memory"

    carousel_dir.mkdir(parents=True, exist_ok=True)
    (carousel_dir / f"{context.slug}.md").write_text(
        build_carousel_wiki_page(context, audit),
        encoding="utf-8",
    )
    update_index(wiki_dir / "index.md", context)
    append_working_memory(memory_dir / "working.md", context, audit)
    update_graph(memory_dir / "graph.json", context, audit)


def build_visual_qa(context: QualityContext) -> str:
    structured_qa_passed = structured_visual_qa_gate(context)["pass"]
    mark = "x" if structured_qa_passed else " "
    status_note = (
        "Structured visual QA has passed; these checklist items mirror `visual-qa.json`."
        if structured_qa_passed
        else "Mark any failed item as `- [x] FAIL: ...`; the final audit treats that as a blocker."
    )
    lines = [
        "# Visual QA",
        "",
        status_note,
        "",
    ]
    for slide in slides(context):
        lines.append(
            f"- [{mark}] Slide {slide.get('slide')} final image matches slide "
            f"{slide.get('slide')} storyboard: {slide.get('copy')}"
        )
    lines.extend(
        [
            f"- [{mark}] Aachu face is recognizably based on the identity reference.",
            f"- [{mark}] Zuv face is recognizably based on the identity reference.",
            f"- [{mark}] Clothing and dress details follow the identity/style references.",
            f"- [{mark}] Illustration style matches the selected carousel style direction.",
            f"- [{mark}] Scene logic matches the copy: clothing, props, hands, and action prove the written line without contradiction.",
            f"- [{mark}] Pose/anatomy is natural and flattering for both Aachu and Zuv; no crouched, cramped, broken, or awkward body language.",
            f"- [{mark}] Successful carousel standard is visible: scene-first behavior proves the relationship truth before mood or decoration.",
            f"- [{mark}] Rendered text and brandmark are visible, accurate, and part of the artwork.",
            f"- [{mark}] Final publishable files exist in `final/` and `final-reels-stories/`.",
            "",
        ]
    )
    return "\n".join(lines)


def write_quality_artifacts(context: QualityContext) -> dict[str, Any]:
    ledger = build_run_ledger(context)
    stage_reviews = build_stage_reviews(context, ledger)
    update_wiki_memory(context, {"status": "PENDING"})
    context.out_dir.mkdir(parents=True, exist_ok=True)
    visual_qa_path = context.out_dir / QUALITY_ARTIFACTS["visual_qa"]
    if not visual_qa_path.exists():
        visual_qa_path.write_text(
            build_visual_qa(context),
            encoding="utf-8",
        )
    final_audit = build_final_audit(context, ledger, stage_reviews)
    ledger["stage_statuses"]["final_contract"] = final_audit["status"]
    ledger["final_gate"] = {
        "status": final_audit["status"],
        "pass": final_audit["pass"],
        "notes": final_audit["notes"],
    }

    write_json(context.out_dir / QUALITY_ARTIFACTS["run_ledger"], ledger)
    write_json(context.out_dir / QUALITY_ARTIFACTS["stage_reviews"], stage_reviews)
    write_json(context.out_dir / QUALITY_ARTIFACTS["final_audit"], final_audit)
    (context.out_dir / QUALITY_ARTIFACTS["wiki_update"]).write_text(
        build_wiki_update(context, final_audit),
        encoding="utf-8",
    )
    update_wiki_memory(context, final_audit)
    return final_audit
