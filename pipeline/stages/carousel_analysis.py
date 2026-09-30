"""Join carousel metrics to ordered, hash-bound observations of local pixels.

The CLI inventories assets and validates saved reviews. Codex must actually
open new images before recording observations; filenames and prompts are not
visual evidence. Generated drafts are not silently matched to published posts.
"""
from __future__ import annotations

import hashlib
import json
import re
from io import BytesIO
from pathlib import Path

from PIL import Image

EVIDENCE_PATH = Path('output/reports/carousel-visual-evidence.json')
ASSESSMENTS = ('hook', 'sequence', 'visual_story', 'text_image_relationship', 'payoff', 'send_reason', 'risk')


def carousel_visual_evidence(root: Path, posts: list[dict]) -> dict:
    root = root.resolve()
    path = root / EVIDENCE_PATH
    issues, reviews, payload = [], {}, {}
    if path.exists():
        try:
            payload = json.loads(path.read_text())
            for review in payload['reviews']:
                code = review.get('shortcode')
                if not isinstance(code, str) or code in reviews:
                    raise ValueError('invalid or duplicate shortcode in visual evidence')
                reviews[code] = review
        except (OSError, ValueError, KeyError, TypeError, AttributeError):
            issues.append('Visual evidence file is invalid; no saved review was accepted.')
            reviews = {}
            payload = {}
    records = []
    for post in posts:
        if post.get('post_type') not in ('sidecar', 'carousel'):
            continue
        code = post.get('shortcode')
        if not isinstance(code, str) or not re.fullmatch(r'[A-Za-z0-9_-]+', code):
            code = None
        folder = root / 'corpus/media' / code if code else None
        assets = []
        if folder and folder.is_dir():
            for asset in sorted(folder.iterdir()):
                match = re.fullmatch(r'slide-(\d+)\.(?:jpg|jpeg|png|webp)', asset.name, re.I)
                if match and asset.is_file():
                    assets.append({'slide': int(match[1]), 'path': str(asset.relative_to(root))})
        expected = post.get('slide_count')
        expected = expected if isinstance(expected, int) and not isinstance(expected, bool) and expected > 0 else None
        review = reviews.get(code, {})
        valid, invalid = [], []
        seen = set()
        review_slides = review.get('slides', [])
        if not isinstance(review_slides, list):
            review_slides = []
            invalid.append('invalid slide list')
        for slide in review_slides:
            try:
                n = slide['slide']
                if not isinstance(n, int) or isinstance(n, bool) or n < 1 or n in seen or (expected and n > expected):
                    raise ValueError('invalid slide order')
                seen.add(n)
                image_path = (root / slide['image_path']).resolve()
                # Published assets must belong to this shortcode's archive.
                if not folder or not image_path.is_relative_to(folder.resolve()):
                    raise ValueError('asset is not in this post archive')
                data = image_path.read_bytes()
                if hashlib.sha256(data).hexdigest() != slide['sha256']:
                    raise ValueError('image bytes changed')
                with Image.open(BytesIO(data)) as image:
                    if list(image.size) != slide['dimensions']:
                        raise ValueError('image dimensions changed')
                if slide.get('review_method') != 'view_image':
                    raise ValueError('no pixel review recorded')
                if slide.get('evidence_kind') not in ('contact_sheet_panel', 'individual_slide'):
                    raise ValueError('unknown pixel evidence kind')
                if slide.get('evidence_kind') == 'contact_sheet_panel':
                    if image_path.name not in ('contact-sheet.jpg', 'contact-sheet.png') or slide.get('panel') != n:
                        raise ValueError('contact sheet panel not identified')
                elif not re.fullmatch(rf'slide-0*{n}\.(?:jpg|jpeg|png|webp)', image_path.name, re.I):
                    raise ValueError('image does not match slide number')
                if not isinstance(slide.get('main_on_image_text'), str) or not all(isinstance(slide.get(field), str) and slide[field].strip() for field in ('observed_scene', 'story_job')):
                    raise ValueError('text/scene observations missing')
                valid.append(slide)
            except (OSError, ValueError, KeyError, TypeError, AttributeError):
                invalid.append(slide.get('slide', '?') if isinstance(slide, dict) else '?')
        valid.sort(key=lambda s: s['slide'])
        reviewed_numbers = {s['slide'] for s in valid}
        missing = sorted(set(range(1, expected + 1)) - reviewed_numbers) if expected else None
        assessment = review.get('assessment', {})
        assessment_valid = isinstance(assessment, dict) and all(isinstance(assessment.get(k), str) and assessment[k].strip() for k in ASSESSMENTS)
        # A changed image invalidates sequence judgments, even if other slides
        # still match. Retain valid slide observations and request a new review.
        if invalid or not assessment_valid:
            assessment = {}
        complete = expected is not None and not missing and bool(valid) and bool(assessment)
        state = ('reviewed_complete' if complete else 'reviewed_partial' if valid else
                 'available_unreviewed' if assets else 'local_images_not_found')
        if invalid:
            state = 'stale_review'
        records.append({'id': post['id'], 'shortcode': code, 'title': review.get('title') if assessment else None,
                        'published_on': post.get('published_on'), 'age_days': post.get('age_days'),
                        'metrics': post['engagement'], 'caption': post.get('caption', ''),
                        'expected_slides': expected, 'local_assets': assets, 'slides': valid,
                        'missing_review_slides': missing, 'invalid_review_slides': invalid,
                        'state': state, 'assessment': assessment})
    comparisons = []
    lookup = {r['shortcode']: r for r in records}
    candidates = payload.get('comparisons', [])
    for comparison in candidates if isinstance(candidates, list) else []:
        try:
            refs = comparison['references']
            if not isinstance(refs, list) or not refs:
                continue
            if not all(isinstance(comparison.get(k), str) and comparison[k].strip() for k in ('observation', 'hypothesis')):
                continue
            for ref in refs:
                record = lookup[ref['shortcode']]
                if not record['assessment'] or not set(ref['slides']).issubset({s['slide'] for s in record['slides']}):
                    raise ValueError('comparison evidence incomplete or stale')
            comparisons.append(comparison)
        except (ValueError, KeyError, TypeError):
            continue
    return {'evidence_path': str(path), 'issues': issues, 'carousels': records, 'comparisons': comparisons,
            'counts': {'carousels': len(records), 'with_local_images': sum(bool(r['local_assets']) for r in records),
                       'reviewed_slides': sum(len(r['slides']) for r in records),
                       'complete_reviews': sum(r['state'] == 'reviewed_complete' for r in records),
                       'partial_reviews': sum(r['state'] == 'reviewed_partial' for r in records)}}


def carousel_report_lines(evidence: dict, root: Path) -> list[str]:
    count = evidence['counts']
    lines = ['## Carousel images, text and swipe sequence', '',
             f"{count['carousels']} published carousels in this snapshot; {count['with_local_images']} have individually saved slides in the shortcode archive. {count['reviewed_slides']} slides have current pixel observations: {count['complete_reviews']} complete sequences and {count['partial_reviews']} partial sequences.",
             'Reviews below come from local images opened with view_image, including explicitly identified contact-sheet panels. Their hashes are rechecked on each run. The report does not download images or pretend to inspect new pixels automatically.', '',
             '| Carousel | Likes at collection | Age at collection | Slides reviewed / expected | Review state |',
             '| --- | ---: | ---: | --- | --- |']
    for r in sorted(evidence['carousels'], key=lambda r: r['metrics'].get('likes') if r['metrics'].get('likes') is not None else -1, reverse=True):
        code = r['shortcode'] or r['id']
        link = f'[{code}](https://www.instagram.com/p/{code}/)' if r['shortcode'] else code
        likes = r['metrics'].get('likes')
        lines.append(f"| {link} | {likes:,.0f} | {r['age_days']} | {len(r['slides'])} / {r['expected_slides'] or 'unknown'} | {r['state']} |" if likes is not None else f"| {link} | unavailable | {r['age_days']} | {len(r['slides'])} / {r['expected_slides'] or 'unknown'} | {r['state']} |")
    lines += ['', 'This table describes response; it does not establish that any visual choice caused the difference. Post ages and distribution differ. Missing slides remain missing; prompts or generated variants are not substituted for published artwork.']
    for issue in evidence['issues']:
        lines.append(issue)
    if evidence['comparisons']:
        lines += ['', '### What the carousel images reveal', '']
        for comparison in evidence['comparisons']:
            sources = []
            for ref in comparison['references']:
                sources.append(f"[{ref['shortcode']}](https://www.instagram.com/p/{ref['shortcode']}/), slides {', '.join(map(str,ref['slides']))}")
            lines += [comparison['observation'], '', f"Evidence: {'; '.join(sources)}.", '',
                      f"Proposed test: {comparison['hypothesis']}", '']
    for r in evidence['carousels']:
        if not r['slides']:
            continue
        title = r['title'] or r['shortcode']
        lines += ['', f'### {title}', '', f"Review: {r['state']}; missing slide reviews: {r['missing_review_slides'] or 'none'}.",
                  f"Published caption (separate from slide text): {r['caption']}", '']
        for name in ASSESSMENTS:
            if r['assessment'].get(name):
                lines.append(f"**{name.replace('_', ' ').capitalize()}:** {r['assessment'][name]}")
        lines += ['', '#### Slide evidence', '']
        for s in r['slides']:
            source = root / s['image_path']
            panel = ' (contact-sheet panel)' if s['evidence_kind'] == 'contact_sheet_panel' else ''
            lines += [f"- [Slide {s['slide']}]({source}){panel} — {s['story_job']}",
                      f"  - Main on-image text: {json.dumps(s['main_on_image_text'], ensure_ascii=False)}",
                      f"  - Visible scene: {s['observed_scene']}"]
    lines += ['', '### Next carousel decision', '',
              'Compare how the cover makes a relationship recognisable, whether each swipe adds a new event, how the images complete the words, and whether the last scene changes the opening meaning. Test a new scene-led cover against a reflective cover while preserving the same love theme; do not copy the historical calm-man/chaotic-woman formula as a rule.',
              'Use the linked scenes to form the hypothesis. Reach, sends and swipe retention are unavailable unless supplied separately; editorial judgments above are not measurements of those outcomes.', '']
    return lines


def carousel_results_evidence(root: Path) -> dict:
    """Rebuild joined reviews from publication/snapshot evidence, not old reports."""
    from pipeline.stages.carousel_results import PUBLICATIONS, review_results
    reviews, issues = [], []
    for path in sorted((root / PUBLICATIONS).glob("*.json")):
        try:
            reviews.append(review_results(root, path.stem))
        except (OSError, ValueError, KeyError, TypeError) as exc:
            issues.append(f"{path.stem}: publication results unavailable: {exc}")
    return {"reviews": reviews, "issues": issues}


def carousel_results_lines(evidence: dict, root: Path) -> list[str]:
    if not evidence["reviews"] and not evidence["issues"]:
        return []
    lines = ["## Dated publication results", "",
             "These package-linked native Insights observations are separate from the export snapshot above. Each review rechecks its publication and snapshot bindings; counts are not added across the two sources.", ""]
    for review in evidence["reviews"]:
        latest = review["latest_observation"]
        observed = f"{latest['observed_at']}, post age {latest['age_days']:.3f} days" if latest else "dated observation unavailable"
        path = root / "output/reports/carousel-results" / f"{review['shortcode']}.md"
        lines.append(f"- [{review['shortcode']}]({path}): {observed}; mechanism {review['mechanism_assessment']['status']}.")
    lines.extend(f"- {issue}" for issue in evidence["issues"])
    return lines + [""]
