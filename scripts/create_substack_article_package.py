import argparse
import json
import re
from datetime import date
from pathlib import Path
from typing import Any

from pipeline.agentic.workflow_metadata import (
    build_workflow_contract,
    build_workflow_metadata,
    build_workflow_recall_markdown,
)
from pipeline.layer_e.artifacts import write_layer_e_artifacts
from pipeline.layer_e.engine import run_layer_e


ARTICLE_ARTIFACTS = [
    "source-manifest.json",
    "source-memory-brief.md",
    "article-brief.md",
    "image-reference-review.md",
    "title-growth-pack.md",
    "outline.md",
    "draft.md",
    "editorial-gates.md",
    "publish-package.md",
    "notes-promo.md",
    "final-approval.md",
]

REQUIRED_CAROUSEL_ARTIFACTS = [
    "concept.json",
    "storyboard.md",
    "slides.json",
    "copy.json",
]

STORY_SELLING_CONTRACT = {
    "skill": "config/skills/romance-story-selling-engine.md",
    "references": [
        "config/references/story-selling-canon/source-policy.md",
        "config/references/story-selling-canon/a-story-of-two-adaptation.md",
        "config/references/story-selling-canon/concept-process-cards.md",
        "config/references/story-selling-canon/rubric.md",
        "config/references/story-selling-canon/story-selling-online.md",
    ],
    "minimum_score": "28/30 when Layer E is invoked",
    "rule": (
        "Use story-selling patterns as source memory for a love/couple essay; "
        "do not turn the article into a craft teardown."
    ),
}


def slugify_title(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    return slug or "couple-love-article"


def read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def discover_carousel_images(carousel_dir: Path) -> list[Path]:
    for candidate_dir in [carousel_dir, carousel_dir / "final", carousel_dir / "source-generated"]:
        images = sorted(candidate_dir.glob("slide-*.png"))
        if images:
            return images
    return []


def write_if_missing(path: Path, content: str) -> None:
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def infer_workspace_root(carousel_dir: Path) -> Path:
    for candidate in [carousel_dir, *carousel_dir.parents]:
        if (candidate / "config" / "agentic_context_manifest.json").exists():
            return candidate
    return Path.cwd()


def build_article_agentic_os(carousel_dir: Path, article_title: str) -> tuple[dict[str, Any], str]:
    workspace_root = infer_workspace_root(carousel_dir)
    query = f"{article_title} {carousel_dir.name}"
    try:
        metadata = build_workflow_metadata(
            workspace_root,
            skill_system_name="story_article",
            recall_query=query,
            profile="article",
        )
        recall_text = build_workflow_recall_markdown(
            workspace_root,
            query=query,
            profile="article",
        )
        metadata["recall_brief"] = "source-memory-brief.md"
        return metadata, recall_text
    except Exception as exc:  # noqa: BLE001 - package creation should expose, not hide, missing OS setup.
        metadata = build_workflow_contract("story_article")
        metadata.update(
            {
                "status": "recall_unavailable",
                "reason": str(exc),
                "recall_brief": "source-memory-brief.md",
            }
        )
        recall_text = (
            "# Recall Bundle\n\n"
            "Status: recall_unavailable\n\n"
            f"Reason: {exc}\n"
        )
        return metadata, recall_text


def infer_layer_e_root(workspace_root: Path) -> Path:
    if (workspace_root / "output" / "story-canon").exists():
        return workspace_root
    return Path(__file__).resolve().parents[1]


def build_article_story_source(carousel_dir: Path, concept: dict[str, Any], article_title: str) -> str:
    storyboard = (
        (carousel_dir / "storyboard.md").read_text(encoding="utf-8", errors="ignore")
        if (carousel_dir / "storyboard.md").exists()
        else ""
    )
    slides = read_json(carousel_dir / "slides.json")
    slide_text = json.dumps(slides, ensure_ascii=False)[:1800] if slides else ""
    existing_layer_e = concept.get("layer_e_story_selling", {})
    existing_lens = existing_layer_e.get("selected_story_lens", "") if isinstance(existing_layer_e, dict) else ""
    return "\n\n".join(
        part
        for part in [
            f"Article title: {article_title}",
            f"Carousel title: {concept.get('title', '')}",
            f"Human truth: {concept.get('human_truth', '')}",
            f"Emotional arc: {concept.get('emotional_arc', '')}",
            f"Existing Layer E lens: {existing_lens}",
            storyboard[:2400],
            slide_text,
        ]
        if part.strip()
    )


def create_article_package(
    carousel_dir: Path,
    title: str | None = None,
    output_root: Path = Path("output/articles"),
    today: date | None = None,
) -> Path:
    today = today or date.today()
    concept = read_json(carousel_dir / "concept.json")
    article_title = title or concept.get("title") or "Couple Love Article"
    slug = slugify_title(article_title)
    out_dir = output_root / today.isoformat() / slug
    out_dir.mkdir(parents=True, exist_ok=True)

    missing = [name for name in REQUIRED_CAROUSEL_ARTIFACTS if not (carousel_dir / name).exists()]
    images = discover_carousel_images(carousel_dir)
    agentic_os, recall_text = build_article_agentic_os(carousel_dir, article_title)
    workspace_root = infer_workspace_root(carousel_dir)
    layer_e_decision = run_layer_e(
        infer_layer_e_root(workspace_root),
        {
            "task_type": "article_angle",
            "story_or_moment": build_article_story_source(carousel_dir, concept, article_title),
            "constraints": [
                "Substack love article",
                "love and couple dynamics first",
                "no process teardown unless explicitly requested",
            ],
            "requested_tone": "warm couple essay",
            "reference_images": [str(path) for path in images],
        },
    )
    layer_e_payload = layer_e_decision.model_dump(mode="json")
    manifest = {
        "date": today.isoformat(),
        "title": article_title,
        "slug": slug,
        "theme": "couple-love-substack",
        "status": "draft_gated",
        "source_carousel": str(carousel_dir),
        "required_source_artifacts": REQUIRED_CAROUSEL_ARTIFACTS,
        "missing_source_artifacts": missing,
        "carousel_images": [str(path) for path in images],
        "story_selling_contract": STORY_SELLING_CONTRACT,
        "layer_e_story_selling": {
            "artifact": "layer-e-story-selling.json",
            "markdown_artifact": "layer-e-story-selling.md",
            "status": layer_e_payload["status"],
            "selected_story_lens": layer_e_payload["selected_story_lens"],
            "emotional_machine": layer_e_payload["emotional_machine"],
        },
        "agentic_os": agentic_os,
        "artifacts": ARTICLE_ARTIFACTS,
        "publish_rule": "Do not publish until every gate is PASS or PASS_WITH_NOTES.",
    }
    (out_dir / "source-manifest.json").write_text(
        json.dumps(manifest, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (out_dir / "source-memory-brief.md").write_text(recall_text, encoding="utf-8")
    write_layer_e_artifacts(out_dir, layer_e_decision)

    human_truth = concept.get("human_truth", "Define the emotional truth before drafting.")
    write_if_missing(
        out_dir / "article-brief.md",
        f"""# Article Brief

## Working Title

{article_title}

## Source Carousel

{carousel_dir}

## Core Love Theme

{human_truth}

## Layer E Story-Selling Angle

{layer_e_decision.selected_story_lens}

## Emotional Machine

{layer_e_decision.emotional_machine}

## Reader Mirror

{layer_e_decision.reader_mirror}

## Distribution Reason

{layer_e_decision.distribution_reason}

## Required Angle

Write a love/couple essay, not a tool/process teardown. The article must use the
carousel images as emotional evidence and keep the focus on love, safety,
chaos, calm, and being fully known.

## Story-Selling Contract

Apply `config/skills/romance-story-selling-engine.md` before drafting. Use
Layer E as the multi-room story-selling brain, then keep the essay rooted in
the couple's emotional obstacle, proof beats, reversal, and payoff.
The story-selling layer must strengthen the love story without replacing the
golden theme or turning the piece into writing advice.

## Audience

- Couples who recognize the chaos/calm dynamic.
- People who feel expressive, dramatic, or emotionally full.
- Partners who love quietly and steadily.

""",
    )

    image_lines = "\n".join(
        f"- [ ] `{path}` - placement: TBD - emotional job: TBD - alt text: TBD"
        for path in images
    ) or "- [ ] No carousel images found. Source gate must fail until images are supplied."
    write_if_missing(
        out_dir / "image-reference-review.md",
        f"""# Image Reference Review

## Image Inventory

{image_lines}

## Gate Checks

- [ ] Hero image selected from carousel slides.
- [ ] Middle images support specific scenes, not decoration.
- [ ] Final image supports the emotional thesis.
- [ ] Every image has alt text.
- [ ] The article references images as story evidence, not filler.

""",
    )

    write_if_missing(
        out_dir / "title-growth-pack.md",
        """# Title And Growth Pack

## Subject Line Candidates

- TBD
- TBD
- TBD

## Preview Text

TBD

## Suggested Slug

TBD

## Reader Comment Prompt

TBD

## Substack Note

TBD

## Growth Checks

- [ ] Title is emotional and clear in an inbox.
- [ ] Preview text adds curiosity without clickbait.
- [ ] First screen contains the hook, thesis, and hero image.
- [ ] Ending includes a comment/share prompt.
- [ ] Notes promo can stand alone without context.

""",
    )

    write_if_missing(
        out_dir / "outline.md",
        f"""# Outline

## Opening Hook

{layer_e_decision.reader_mirror}

## Emotional Problem

{layer_e_decision.selected_story_lens}

## Carousel Proof Beats

{layer_e_decision.proof_engine}

## Deeper Turn

{layer_e_decision.emotional_machine}

## Final Payoff

{layer_e_decision.distribution_reason}

""",
    )

    write_if_missing(
        out_dir / "draft.md",
        """# Draft

Draft the article here only after the source, theme, image, and growth gates
have been checked.

""",
    )

    write_if_missing(
        out_dir / "editorial-gates.md",
        """# Editorial Gates

Do not publish until every gate is PASS or PASS_WITH_NOTES.

## Gate 1 - Source Integrity

Status: PENDING

- Carousel package exists.
- `concept.json`, `storyboard.md`, `slides.json`, and `copy.json` reviewed.
- Carousel images discovered and usable.

## Gate 2 - Love Theme Fit

Status: PENDING

- Article is about love/couple dynamics, not tools or process.
- Starts from a universal relationship truth.
- Uses Aachu/Zuv specifics as proof.
- Keeps humor affectionate.

## Gate 3 - Image Reference Fit

Status: PENDING

- Hero, middle, and final image placements are chosen.
- Images are referenced as emotional evidence.
- Alt text exists for every image.

## Gate 4 - Article Structure

Status: PENDING

- Opening earns the inbox click.
- Sections flow from recognition to tenderness.
- Ending lands on a send/save-worthy thesis.

## Gate 5 - Voice And Taste

Status: PENDING

- Voice matches @a.storyof.two: warm, intimate, emotionally honest.
- No mean-spirited husband-wife humor.
- No generic relationship advice filler.

## Gate 6 - Substack Growth Package

Status: PENDING

- 3-5 subject lines.
- Preview text.
- SEO-friendly slug.
- Comment prompt.
- Substack Note/social excerpt.

## Gate 7 - Final Publish Approval

Status: PENDING

- Final article assembled in `publish-package.md`.
- All gates are PASS or PASS_WITH_NOTES.
- Any notes or limitations are explicit.

## Gate 8 - Story Selling Fit

Status: PENDING

- `config/skills/romance-story-selling-engine.md` was used before drafting.
- A concept-process card shaped the hook, proof, reversal, and payoff.
- The article would score 28/30 or higher on the Story-Selling rubric when
  Layer E is invoked.
- No copyrighted source text is copied into the draft or publish package.

""",
    )

    write_if_missing(
        out_dir / "publish-package.md",
        """# Publish Package

Final clean article goes here after gates pass.

## Metadata

- Title: TBD
- Subtitle/preview: TBD
- Slug: TBD

## Article

TBD

## Images

TBD

""",
    )

    write_if_missing(
        out_dir / "notes-promo.md",
        """# Notes Promo

## Primary Note

TBD

## Alternate Notes

- TBD
- TBD

""",
    )

    write_if_missing(
        out_dir / "final-approval.md",
        """# Final Approval

- [ ] I approve the title and preview text.
- [ ] I approve the emotional thesis.
- [ ] I approve the image placements.
- [ ] I approve the final article for Substack.

""",
    )

    return out_dir


def main() -> None:
    parser = argparse.ArgumentParser(description="Create a gated Substack article package from a carousel.")
    parser.add_argument("--carousel-dir", required=True, type=Path)
    parser.add_argument("--title")
    parser.add_argument("--output-root", type=Path, default=Path("output/articles"))
    args = parser.parse_args()

    out_dir = create_article_package(
        carousel_dir=args.carousel_dir,
        title=args.title,
        output_root=args.output_root,
    )
    print(out_dir)


if __name__ == "__main__":
    main()
