import hashlib
import json
from datetime import date
from pathlib import Path

from PIL import Image

from pipeline.stages.carousel_analysis import ASSESSMENTS, EVIDENCE_PATH, carousel_visual_evidence
from pipeline.stages.a3_analyzer import run


def evidence(root, *, expected=2, reviewed=(1, 2)):
    folder = root / 'corpus/media/ABC'
    folder.mkdir(parents=True)
    slides = []
    for n in reviewed:
        path = folder / f'slide-{n:02}.png'
        Image.new('RGB', (20, 30), (n, 10, 20)).save(path)
        slides.append({'slide': n, 'image_path': str(path.relative_to(root)), 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'dimensions': [20, 30], 'review_method': 'view_image', 'evidence_kind': 'individual_slide', 'main_on_image_text': f'Exact text {n}', 'observed_scene': f'Visible action {n}', 'story_job': 'new event'})
    payload = {'reviews': [{'shortcode': 'ABC', 'title': 'A carousel', 'slides': slides, 'assessment': {k: f'Observed {k}' for k in ASSESSMENTS}}], 'comparisons': [{'references': [{'shortcode': 'ABC', 'slides': list(reviewed)}], 'observation': 'A supported visual observation', 'hypothesis': 'A proposed test'}]}
    path = root / EVIDENCE_PATH
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(payload))
    post = {'id': '1', 'shortcode': 'ABC', 'post_type': 'sidecar', 'slide_count': expected, 'engagement': {'likes': 50}, 'caption': 'Caption is separate'}
    return post, slides, path


def test_current_reviews_join_metrics_and_exact_slide_text(tmp_path):
    post, _, _ = evidence(tmp_path)
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['counts']['complete_reviews'] == 1
    assert result['carousels'][0]['slides'][0]['main_on_image_text'] == 'Exact text 1'
    assert result['carousels'][0]['metrics']['likes'] == 50
    assert len(result['comparisons']) == 1


def test_missing_slide_keeps_sequence_partial(tmp_path):
    post, _, _ = evidence(tmp_path, expected=3)
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['carousels'][0]['state'] == 'reviewed_partial'
    assert result['carousels'][0]['missing_review_slides'] == [3]
    assert result['counts']['complete_reviews'] == 0


def test_pixel_change_invalidates_sequence_and_comparison(tmp_path):
    post, slides, _ = evidence(tmp_path)
    Image.new('RGB', (20, 30), 'red').save(tmp_path / slides[0]['image_path'])
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['carousels'][0]['state'] == 'stale_review'
    assert result['carousels'][0]['assessment'] == {}
    assert result['comparisons'] == []


def test_files_without_review_are_not_claimed_as_seen(tmp_path):
    post, _, path = evidence(tmp_path)
    path.unlink()
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['carousels'][0]['state'] == 'available_unreviewed'
    assert result['counts']['reviewed_slides'] == 0


def test_asset_from_other_post_or_generated_variant_cannot_be_substituted(tmp_path):
    post, slides, path = evidence(tmp_path)
    payload = json.loads(path.read_text())
    outside = tmp_path / 'draft.png'
    outside.write_bytes((tmp_path / slides[0]['image_path']).read_bytes())
    payload['reviews'][0]['slides'][0]['image_path'] = 'draft.png'
    path.write_text(json.dumps(payload))
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['carousels'][0]['invalid_review_slides'] == [1]
    assert result['counts']['complete_reviews'] == 0


def test_contact_sheet_panel_is_explicit_and_hash_bound(tmp_path):
    post, slides, path = evidence(tmp_path, expected=1, reviewed=(1,))
    sheet = tmp_path / 'corpus/media/ABC/contact-sheet.png'
    sheet.write_bytes((tmp_path / slides[0]['image_path']).read_bytes())
    payload = json.loads(path.read_text())
    payload['reviews'][0]['slides'][0].update(image_path=str(sheet.relative_to(tmp_path)), evidence_kind='contact_sheet_panel', panel=1)
    path.write_text(json.dumps(payload))
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['counts']['complete_reviews'] == 1
    assert result['carousels'][0]['slides'][0]['evidence_kind'] == 'contact_sheet_panel'


def test_invalid_evidence_shapes_do_not_claim_a_review(tmp_path):
    post, _, path = evidence(tmp_path)
    path.write_text('{"reviews": null}')
    result = carousel_visual_evidence(tmp_path, [post])
    assert result['issues']
    assert result['counts']['reviewed_slides'] == 0


def test_default_analyzer_focuses_on_carousels_even_when_reels_dominate(tmp_path):
    post, _, _ = evidence(tmp_path)
    raw = [{'id': '1', 'shortCode': 'ABC', 'type': 'Sidecar', 'likesCount': 50, 'timestamp': '2026-08-10', 'childPosts': [{}, {}]}]
    raw += [{'id': str(n), 'type': 'Video', 'likesCount': 100000, 'timestamp': '2026-08-10'} for n in range(2, 12)]
    folder = tmp_path / 'corpus/raw'
    folder.mkdir(parents=True)
    (folder / '2026-09-01-raw.json').write_text(json.dumps(raw))
    output = run(tmp_path, today=date(2026, 9, 5))
    payload = json.loads(output.with_suffix('.json').read_text())
    assert payload['post_count'] == 1
    assert payload['analysis_focus'] == 'carousel'
    assert payload['carousel_visual_evidence']['counts']['complete_reviews'] == 1
    text = output.read_text()
    assert text.index('Carousel images, text') < text.index('Metric coverage')
    assert 'Exact text 1' in text
    assert '100,000' not in text


def test_real_archive_review_covers_all_available_published_slides():
    root = Path(__file__).resolve().parents[1]
    from pipeline.stages.a3_analyzer import canonical_post
    rows = json.loads((root / 'corpus/raw/2026-06-06-raw.json').read_text())
    result = carousel_visual_evidence(root, [canonical_post(p) for p in rows])
    assert result['counts']['reviewed_slides'] == 22
    assert result['counts']['complete_reviews'] == 4
    assert result['counts']['partial_reviews'] == 0
    assert len(result['comparisons']) == 2
    assert all(not r['invalid_review_slides'] for r in result['carousels'])
