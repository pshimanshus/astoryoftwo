"""Evidence-bound mechanism recall, independent of production policy."""

import hashlib
import json
from pathlib import Path

import pytest

from pipeline.agentic.memory_index import build_memory_index, search_memory
from pipeline.stages.carousel_patterns import (
    PatternEvidenceError,
    find_patterns,
    load_patterns,
)


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = Path('config/references/carousel-patterns.json')


def write_json(root, relative, payload):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload), encoding='utf-8')
    return hashlib.sha256(path.read_bytes()).hexdigest()


@pytest.fixture
def evidence_root(tmp_path):
    """Small archive includes a duplicate and independent unpublished evidence."""
    image = tmp_path / 'output/sources/cup.png'
    image.parent.mkdir(parents=True)
    image.write_bytes(b'saved cup pixels')
    image_hash = hashlib.sha256(image.read_bytes()).hexdigest()
    sources = []
    notes = []
    original = '/old/workspace'
    for code in ('A', 'B'):
        slides = [{'slide': 1, 'path': f'{original}/output/sources/cup.png'}]
        sources.append({'shortcode': code, 'slides': slides})
        notes.append({'shortcode': code, 'title': code, 'evidence': 'local_contact_sheet_inspected_2026-09-20', 'slides': [dict(slides[0], development='Two cups share the table.', handoff='Ownership accumulates.')]})
    archive = 'output/reports/example'
    source_hash = write_json(tmp_path, f'{archive}/source-index.json', sources)
    notes_hash = write_json(tmp_path, f'{archive}/beat-notes.json', notes)
    manifest_hash = write_json(tmp_path, f'{archive}/archive-manifest.json', {'mapped_sequences': 2, 'mapped_slide_positions': 2, 'unique_image_hashes': 1, 'files': {'source-index.json': source_hash, 'beat-notes.json': notes_hash}})
    refs = [{'shortcode': code, 'slide': 1} for code in ('A', 'B')]
    example = {'shortcode': 'A', 'slides': [1], 'observed': 'Two cups share the table.', 'interpretation': 'Shared ownership is suggested.'}
    counter = {'shortcode': 'B', 'slides': [1], 'observed': 'Two cups share the table.', 'interpretation': 'Another mapped cut is not independent evidence.'}
    pattern = {'id': 'shared-ownership', 'title': 'Shared ownership through ordinary objects', 'theme': 'shared home', 'sequence_modes': ['accumulating_evidence'], 'hook_mechanism': 'two cups in one home', 'mismatch': 'mine versus ours', 'visual_carrier': 'objects', 'ending_mechanism': 'accumulation', 'failure_mode': 'redundant object pairs', 'when_useful': 'When ordinary objects make shared life tangible.', 'interpretation': 'Objects can establish cohabitation.', 'creative_hypothesis': 'Test distinct ownership details before a shared-table ending.', 'supporting_examples': [example], 'counterexamples': [counter], 'limits': ['No measured slide completion; duplicate images are not independent observations.'], 'performance_snapshots': [], 'tags': ['shared', 'ownership', 'cups']}
    registry = {'schema_version': 'carousel-patterns/v1', 'saved_on': '2026-09-20', 'evidence_basis': 'Saved September 20 contact-sheet inspection, not fresh vision.', 'archive': {'path': archive, 'original_root': original, 'manifest_sha256': manifest_hash}, 'source_bindings': [], 'coverage': {'mapped_sequences': 2, 'mapped_slide_positions': 2, 'unique_image_hashes': 1, 'duplicate_image_groups': [{'sha256': image_hash, 'positions': refs}]}, 'source_index': [{'shortcode': code, 'title': code, 'evidence_kind': 'local_source_counterpart', 'reviewed_on': '2026-09-20', 'published_image_correspondence': 'unverified', 'slides': [{'slide': 1, 'path': 'output/sources/cup.png', 'sha256': image_hash}]} for code in ('A', 'B')], 'supersessions': [], 'patterns': [pattern]}
    write_json(tmp_path, REGISTRY, registry)
    return tmp_path


def test_real_registry_carries_corrected_mappings_duplicates_and_limits():
    result = load_patterns(ROOT)
    assert result['status'] == 'verified_saved_evidence'
    assert 8 <= len(result['patterns']) <= 12
    coverage = result['coverage']
    assert (coverage['mapped_sequences'], coverage['mapped_slide_positions'], coverage['unique_image_hashes']) == (27, 158, 153)
    assert len(coverage['duplicate_image_groups']) == 5
    assert {p['shortcode'] for group in coverage['duplicate_image_groups'] for p in group['positions']} == {'DcT42EoCb1d', 'DbGSctjiWAB'}
    corrections = {item['shortcode']: item['current_mapping'] for item in result['supersessions']}
    assert corrections == {'Dc5eniKic95': 'public-pressure/husband-alliance', 'DcRQEEjCSNo': 'chores', 'DcG9gVzCfO7': 'continuing commitment'}
    for pattern in result['patterns']:
        assert pattern['supporting_examples'] and pattern['counterexamples'] and pattern['limits']
        assert pattern['interpretation'] and pattern['creative_hypothesis']
        for example in pattern['supporting_examples'] + pattern['counterexamples']:
            assert example['source_refs']
            assert all(ref['evidence_kind'] in {'local_source_counterpart', 'downloaded_published_frames', 'saved_published_review'} for ref in example['source_refs'])
    summons = next(p for p in result['patterns'] if p['id'] == 'summons-duration-reciprocity')
    assert summons['supporting_examples'][0]['source_refs'][0]['evidence_kind'] == 'saved_published_review'


def test_saved_evidence_recall_returns_limit_and_does_not_force_match(evidence_root):
    hits = find_patterns(evidence_root, 'shared ownership cups')
    assert len(hits) == 1
    assert hits[0]['counterexamples'] and 'No measured' in hits[0]['limits'][0]
    assert hits[0]['supporting_examples'][0]['source_refs'][0]['published_image_correspondence'] == 'unverified'
    assert hits[0]['evidence_basis'].startswith('Saved September 20')
    assert find_patterns(evidence_root, 'quantum zebra') == []
    assert find_patterns(evidence_root, 'cups', limit=0) == []


@pytest.mark.parametrize('target', ['image', 'notes', 'index', 'manifest'])
def test_changed_evidence_fails_closed(evidence_root, target):
    paths = {'image': 'output/sources/cup.png', 'notes': 'output/reports/example/beat-notes.json', 'index': 'output/reports/example/source-index.json', 'manifest': 'output/reports/example/archive-manifest.json'}
    path = evidence_root / paths[target]
    path.write_bytes(path.read_bytes() + b' ')
    with pytest.raises(PatternEvidenceError, match='hash|drift'):
        load_patterns(evidence_root)
    with pytest.raises(PatternEvidenceError):
        find_patterns(evidence_root, 'cups')


@pytest.mark.parametrize('mutation', ['slide', 'duplicate', 'mapping', 'schema', 'path'])
def test_registry_mistakes_fail_closed(evidence_root, mutation):
    path = evidence_root / REGISTRY
    registry = json.loads(path.read_text())
    if mutation == 'slide':
        registry['patterns'][0]['supporting_examples'][0]['slides'] = [99]
    elif mutation == 'duplicate':
        registry['coverage']['duplicate_image_groups'] = []
    elif mutation == 'mapping':
        registry['supersessions'] = [{'shortcode': 'A', 'current_mapping': 'corrected title', 'current_title': 'wrong', 'superseded_sources': ['old.md']}]
    elif mutation == 'schema':
        registry['schema_version'] = 'unknown'
    else:
        registry['source_index'][0]['slides'][0]['path'] = '../../outside.png'
    path.write_text(json.dumps(registry))
    with pytest.raises(PatternEvidenceError):
        load_patterns(evidence_root)


def test_absent_registry_is_explicitly_unavailable(tmp_path):
    assert load_patterns(tmp_path)['status'] == 'unavailable'
    assert find_patterns(tmp_path, 'cups') == []


def test_individual_patterns_are_fts_records_with_evidence_limits(evidence_root):
    index = build_memory_index(evidence_root)
    hits = search_memory(index, 'shared ownership', limit=2)
    assert hits[0].kind == 'carousel_pattern'
    assert hits[0].path == f'{REGISTRY.as_posix()}#shared-ownership'
    assert 'Limit:' in hits[0].snippet
    assert 'Counterexample:' in hits[0].snippet
    assert 'Saved' in hits[0].snippet


def test_stale_registry_is_not_silently_indexed(evidence_root):
    (evidence_root / 'output/sources/cup.png').write_bytes(b'changed')
    with pytest.raises(PatternEvidenceError):
        build_memory_index(evidence_root)


def test_result_research_is_recalled_as_research_not_policy(tmp_path):
    write_json(tmp_path, 'output/reports/carousel-results/cup-result.json', {'schema_version': 'carousel-result/v1', 'result_id': 'cup-result', 'package_id': 'cup-story', 'reviewed_at': '2026-09-20', 'review': {'mechanism_assessment': 'Shared ownership remains ambiguous with low distribution.', 'limits': ['No slide completion data.'], 'next_test': 'Vary the opening object.'}})
    hits = search_memory(build_memory_index(tmp_path), 'shared ownership')
    assert hits[0].kind == 'carousel_result'
    assert 'research' in hits[0].snippet.lower()
    assert 'No slide completion' in hits[0].snippet


@pytest.mark.parametrize('mutation', ['value', 'date', 'shortcode'])
def test_snapshot_values_dates_and_post_identity_are_source_bound(evidence_root, mutation):
    source = 'output/reports/review.json'
    payload = {'posts': [{'shortcode': 'A', 'metrics': {'observed_at': '2026-09-12', 'Shares': 12, 'Viewers': 100}}]}
    digest = write_json(evidence_root, source, payload)
    path = evidence_root / REGISTRY
    registry = json.loads(path.read_text())
    registry['source_bindings'].append({'path': source, 'sha256': digest})
    snapshot = {'shortcode': 'A', 'source': source, 'pointer': '/posts/0/metrics', 'observed_at': '2026-09-12', 'native_metrics': {'Shares': 12, 'Viewers': 100}, 'limit': 'One dated observation, no causal inference.'}
    registry['patterns'][0]['performance_snapshots'] = [snapshot]
    write_json(evidence_root, REGISTRY, registry)
    assert load_patterns(evidence_root)['patterns'][0]['performance_snapshots'][0]['native_metrics']['Shares'] == 12
    if mutation == 'value':
        snapshot['native_metrics']['Shares'] = 12000
    elif mutation == 'date':
        snapshot['observed_at'] = '2026-09-20'
    else:
        snapshot['shortcode'] = 'B'
    write_json(evidence_root, REGISTRY, registry)
    with pytest.raises(PatternEvidenceError, match='Performance'):
        load_patterns(evidence_root)


def test_supplemental_source_hash_drift_is_not_verified(evidence_root):
    source = 'wiki/review.md'
    file = evidence_root / source
    file.parent.mkdir(parents=True)
    file.write_text('Saved observation')
    path = evidence_root / REGISTRY
    registry = json.loads(path.read_text())
    registry['source_bindings'].append({'path': source, 'sha256': hashlib.sha256(file.read_bytes()).hexdigest()})
    write_json(evidence_root, REGISTRY, registry)
    file.write_text('Changed observation')
    with pytest.raises(PatternEvidenceError, match='hash drift'):
        load_patterns(evidence_root)


def test_observations_cannot_be_rewritten_as_saved_facts(evidence_root):
    path = evidence_root / REGISTRY
    registry = json.loads(path.read_text())
    registry['patterns'][0]['supporting_examples'][0]['observed'] = 'An unseen dramatic rescue.'
    write_json(evidence_root, REGISTRY, registry)
    with pytest.raises(PatternEvidenceError, match='Observation differs'):
        load_patterns(evidence_root)


def test_current_result_schema_preserves_uncertainty_in_recall(tmp_path):
    write_json(tmp_path, 'output/reports/carousel-results/ABC.json', {
        'schema_version': 'carousel-results/v1', 'shortcode': 'ABC',
        'package_id': 'output/carousels/2026-09-20/cups',
        'intended_hypothesis': 'Shared cups make ownership tangible.',
        'outcome_status': 'unavailable', 'latest_observation': None,
        'mechanism_assessment': {'status': 'ambiguous', 'reason': 'No native Insights observation is available.'},
        'next_hypothesis': None, 'limits': ['No completion data or dated metrics.'],
    })
    hits = search_memory(build_memory_index(tmp_path), 'shared cups')
    assert hits[0].kind == 'carousel_result'
    assert 'ambiguous' in hits[0].snippet and 'unavailable' in hits[0].snippet
    assert 'No completion data' in hits[0].snippet
    assert 'not production policy' in hits[0].snippet


@pytest.fixture
def archived_external_source(evidence_root):
    """Never create/delete the historical Downloads path; only a declared copy."""
    registry = json.loads((evidence_root / REGISTRY).read_text())
    archive = Path(registry['archive']['path'])
    historical = str(evidence_root / 'historical-downloads' / 'cup.png')
    digest = registry['source_index'][0]['slides'][0]['sha256']
    canonical = (archive / 'evidence-assets' / f'{digest}.png').as_posix()
    asset = evidence_root / canonical
    asset.parent.mkdir(parents=True)
    asset.write_bytes((evidence_root / 'output/sources/cup.png').read_bytes())
    for filename in ('source-index.json', 'beat-notes.json'):
        path = evidence_root / archive / filename
        records = json.loads(path.read_text())
        for record in records:
            record['slides'][0]['path'] = historical
        write_json(evidence_root, archive / filename, records)
    manifest = json.loads((evidence_root / archive / 'archive-manifest.json').read_text())
    for filename in ('source-index.json', 'beat-notes.json'):
        manifest['files'][filename] = hashlib.sha256((evidence_root / archive / filename).read_bytes()).hexdigest()
    registry['archive']['manifest_sha256'] = write_json(evidence_root, archive / 'archive-manifest.json', manifest)
    for record in registry['source_index']:
        slide = record['slides'][0]
        slide['path'] = historical
        slide['canonical_asset'] = {'path': canonical, 'sha256': digest, 'bound_on': '2026-09-20', 'provenance': 'Identical-byte copy of the historical local source; canonical evidence, no fallback or fresh inspection.'}
    write_json(evidence_root, REGISTRY, registry)
    return evidence_root, historical, asset


def test_declared_archive_is_canonical_when_original_was_never_present(archived_external_source):
    root, historical, asset = archived_external_source
    assert not Path(historical).exists()
    result = load_patterns(root)
    reference = result['patterns'][0]['supporting_examples'][0]['source_refs'][0]
    assert reference['path'] == asset.relative_to(root).as_posix()
    assert reference['original_path'] == historical
    assert reference['source_path_role'] == 'canonical_archived_evidence'
    assert result['status'] == 'verified_saved_evidence'


@pytest.mark.parametrize('mutation', ['missing', 'changed', 'wrong_hash', 'wrong_location'])
def test_declared_canonical_asset_cannot_fall_back_or_drift(archived_external_source, mutation):
    root, historical, asset = archived_external_source
    # This is a test-only source. Its presence must not become an implicit fallback.
    original = Path(historical)
    original.parent.mkdir(parents=True)
    original.write_bytes(asset.read_bytes())
    if mutation == 'missing':
        asset.unlink()
    elif mutation == 'changed':
        asset.write_bytes(b'changed canonical source')
    else:
        registry = json.loads((root / REGISTRY).read_text())
        canonical = registry['source_index'][0]['slides'][0]['canonical_asset']
        if mutation == 'wrong_hash':
            canonical['sha256'] = '0' * 64
        else:
            canonical['path'] = 'output/sources/cup.png'
        write_json(root, REGISTRY, registry)
    with pytest.raises(PatternEvidenceError):
        load_patterns(root)


def test_historical_external_path_is_not_a_current_runtime_source(archived_external_source):
    root, historical, _asset = archived_external_source
    original = Path(historical)
    original.parent.mkdir(parents=True)
    original.write_bytes(b'a different current Downloads file, not the declared evidence source')
    assert load_patterns(root)['status'] == 'verified_saved_evidence'


def test_real_registry_has_no_external_runtime_image_dependencies():
    registry = load_patterns(ROOT)
    canonical = []
    for source in registry['source_index']:
        for slide in source['slides']:
            if 'path' in slide and Path(slide['path']).is_absolute():
                canonical.append(slide['canonical_asset'])
    assert len(canonical) == 7
    assert all(not Path(asset['path']).is_absolute() for asset in canonical)
    for pattern in registry['patterns']:
        for example in pattern['supporting_examples'] + pattern['counterexamples']:
            assert all(not Path(ref.get('path', '')).is_absolute() for ref in example['source_refs'])
