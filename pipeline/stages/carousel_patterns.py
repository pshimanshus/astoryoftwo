"""Small, evidence-bound carousel mechanism recall; never production policy.

Validation checks saved records and current local byte bindings. It does not
perform a fresh visual inspection or establish published-image correspondence.
"""

from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import re
from typing import Any


REGISTRY_PATH = Path('config/references/carousel-patterns.json')
SCHEMA_VERSION = 'carousel-patterns/v1'


class PatternEvidenceError(ValueError):
    """A present reference registry cannot substantiate its evidence bindings."""


def _require(condition: object, message: str) -> None:
    if not condition:
        raise PatternEvidenceError(message)


def _path(root: Path, relative: str) -> Path:
    _require(isinstance(relative, str) and relative.strip(), 'Missing source path')
    candidate = Path(relative)
    _require(not candidate.is_absolute() and '..' not in candidate.parts, f'Unsafe source path: {relative}')
    # Source files can be shared with a managed worktree through symlinks. The
    # registry path itself must still be relative and cannot traverse upwards.
    return root / candidate


def _json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError) as exc:
        raise PatternEvidenceError(f'Unavailable or invalid source: {path}: {exc}') from exc


def _hash(path: Path) -> str:
    try:
        digest = hashlib.sha256()
        with path.open('rb') as source:
            for chunk in iter(lambda: source.read(1024 * 1024), b''):
                digest.update(chunk)
        return digest.hexdigest()
    except OSError as exc:
        raise PatternEvidenceError(f'Unavailable source: {path}: {exc}') from exc


def _pointer(payload: Any, pointer: str) -> Any:
    _require(isinstance(pointer, str) and pointer.startswith('/'), 'Invalid source JSON pointer')
    try:
        for part in pointer[1:].split('/'):
            part = part.replace('~1', '/').replace('~0', '~')
            payload = payload[int(part)] if isinstance(payload, list) else payload[part]
        return payload
    except (IndexError, KeyError, ValueError, TypeError) as exc:
        raise PatternEvidenceError(f'Unresolved source pointer: {pointer}') from exc


def _original_relative(value: str, original_root: str) -> str:
    prefix = original_root.rstrip('/') + '/'
    if value.startswith(prefix):
        return value[len(prefix):]
    # The archived map also contains explicitly recorded Downloads sources.
    # Preserve those paths; never guess another root or silently rebind them.
    return value


def _rows_by_code(rows: Any, label: str) -> dict[str, dict[str, Any]]:
    _require(isinstance(rows, list), f'{label} must be a list')
    result = {}
    for row in rows:
        _require(isinstance(row, dict) and row.get('shortcode'), f'Invalid {label} record')
        _require(row['shortcode'] not in result, f'Duplicate shortcode in {label}: {row["shortcode"]}')
        result[row['shortcode']] = row
    return result


def _duplicate_key(groups: list[dict[str, Any]]) -> list[tuple[str, tuple[tuple[str, int], ...]]]:
    return sorted((group['sha256'], tuple(sorted((position['shortcode'], position['slide']) for position in group['positions']))) for group in groups)



def _canonical_image_path(archive: dict[str, Any], slide: dict[str, Any]) -> str:
    """Select the declared source, never an existence-dependent backup.

    An absolute historical path requires a hash-named copy in this archive.
    The original path remains provenance and is deliberately not read again.
    """
    historical = slide['path']
    canonical = slide.get('canonical_asset')
    if canonical is None:
        _require(not Path(historical).is_absolute(), f'External source lacks canonical archive asset: {historical}')
        return historical
    _require(isinstance(canonical, dict), 'Invalid canonical evidence asset')
    relative = canonical['path']
    declared_path = Path(relative)
    expected_parent = Path(archive['path']) / 'evidence-assets'
    _require(not declared_path.is_absolute() and declared_path.parent == expected_parent, 'Canonical evidence asset must be inside archive/evidence-assets')
    _require(canonical['sha256'] == slide['sha256'], 'Canonical evidence hash differs from original binding')
    _require(declared_path.stem == slide['sha256'] and declared_path.suffix == Path(historical).suffix, 'Canonical evidence filename does not preserve source hash and suffix')
    _require(canonical.get('bound_on') and canonical.get('provenance'), 'Canonical evidence lacks copy provenance')
    return relative


def _load_patterns(root: Path) -> dict[str, Any]:
    registry = _json(root / REGISTRY_PATH)
    _require(isinstance(registry, dict) and registry.get('schema_version') == SCHEMA_VERSION, 'Unsupported carousel pattern schema')
    _require(registry.get('evidence_basis'), 'Missing saved inspection basis')
    archive = registry['archive']
    archive_path = _path(root, archive['path'])
    _require(_hash(archive_path / 'archive-manifest.json') == archive['manifest_sha256'], 'Archive manifest hash drift')
    manifest = _json(archive_path / 'archive-manifest.json')
    for relative, expected in manifest['files'].items():
        _require(_hash(_path(archive_path, relative)) == expected, f'Archive source hash drift: {relative}')
    _require({'source-index.json', 'beat-notes.json'} <= manifest['files'].keys(), 'Archive lacks source/observation hash bindings')
    mapped = _rows_by_code(_json(archive_path / 'source-index.json'), 'saved source index')
    notes_list = _json(archive_path / 'beat-notes.json')
    notes = _rows_by_code(notes_list, 'saved beat notes')
    _require(mapped.keys() == notes.keys(), 'Source and observed sequence coverage drift')
    note_positions = {row['shortcode']: i for i, row in enumerate(notes_list)}
    bound_sources = {}
    for binding in registry['source_bindings']:
        relative = binding['path']
        source = _path(root, relative)
        _require(relative not in bound_sources, f'Duplicate source binding: {relative}')
        _require(_hash(source) == binding['sha256'], f'Source binding hash drift: {relative}')
        bound_sources[relative] = _json(source) if source.suffix == '.json' else None
    indexed = _rows_by_code(registry['source_index'], 'registry source index')
    local_codes = {code for code, source in indexed.items() if source['evidence_kind'] != 'saved_published_review'}
    _require(local_codes == set(mapped), 'Registry source coverage drift')
    all_refs = {}
    hash_positions: dict[str, list[dict[str, Any]]] = defaultdict(list)
    file_hashes = {}
    for code, source in indexed.items():
        kind = source['evidence_kind']
        _require(kind in {'local_source_counterpart', 'downloaded_published_frames', 'saved_published_review'}, f'Unknown evidence kind: {kind}')
        _require(source.get('reviewed_on') and source.get('published_image_correspondence'), f'Missing evidence provenance: {code}')
        positions = source['slides']
        _require([slide['slide'] for slide in positions] == list(range(1, len(positions) + 1)), f'Nonsequential slide positions: {code}')
        if kind == 'saved_published_review':
            review_path = source['review_path']
            _require(review_path in bound_sources, f'Unbound published review: {review_path}')
            review = _pointer(bound_sources[review_path], source['review_pointer'])
            _require(review['shortcode'] == code and review['reviewed_on'] == source['reviewed_on'], f'Published review mapping drift: {code}')
            _require(review.get('complete') is True and len(review['slides']) == len(positions), f'Incomplete published review: {code}')
        else:
            original = mapped[code]['slides']
            observed = notes[code]['slides']
            _require(len(positions) == len(original) == len(observed), f'Slide coverage drift: {code}')
            _require(source['title'] == notes[code]['title'], f'Current source title drift: {code}')
            _require(notes[code].get('evidence') == f'local_contact_sheet_inspected_{source["reviewed_on"]}', f'Saved inspection date drift: {code}')
        for i, slide in enumerate(positions):
            ref = {'shortcode': code, 'slide': slide['slide'], 'evidence_kind': kind, 'reviewed_on': source['reviewed_on'], 'published_image_correspondence': source['published_image_correspondence']}
            if kind == 'saved_published_review':
                expected_pointer = source['review_pointer'] + f'/slides/{i}'
                _require(slide['review_pointer'] == expected_pointer, f'Published slide reference drift: {code}')
                observed_slide = _pointer(bound_sources[review_path], expected_pointer)
                _require(observed_slide['slide'] == slide['slide'], f'Published slide position drift: {code}')
                ref.update({'source': review_path, 'pointer': expected_pointer, 'observed': observed_slide['observed_scene']})
            else:
                _require(slide['slide'] == original[i]['slide'] == observed[i]['slide'], f'Source slide position drift: {code}')
                relative = slide['path']
                _require(relative == _original_relative(original[i]['path'], archive['original_root']) == _original_relative(observed[i]['path'], archive['original_root']), f'Source mapping drift: {code} slide {slide["slide"]}')
                canonical_path = _canonical_image_path(archive, slide)
                if canonical_path not in file_hashes:
                    file_hashes[canonical_path] = _hash(_path(root, canonical_path))
                _require(file_hashes[canonical_path] == slide['sha256'], f'Image hash drift: {canonical_path}')
                if kind == 'downloaded_published_frames':
                    _require(relative.startswith(f'corpus/media/{code}/'), f'Unsubstantiated downloaded-frame provenance: {code}')
                else:
                    _require(source['published_image_correspondence'] == 'unverified', f'Local source cannot claim published identity: {code}')
                hash_positions[slide['sha256']].append({'shortcode': code, 'slide': slide['slide']})
                ref.update({'path': canonical_path, 'sha256': slide['sha256'], 'source': f'{archive["path"]}/beat-notes.json', 'pointer': f'/{note_positions[code]}/slides/{i}', 'observed': observed[i]['development']})
                if slide.get('canonical_asset'):
                    ref.update({'original_path': relative, 'original_sha256': slide['sha256'], 'source_path_role': 'canonical_archived_evidence', 'copy_provenance': slide['canonical_asset']['provenance']})
            all_refs[(code, slide['slide'])] = ref
    coverage = registry['coverage']
    actual = {'mapped_sequences': len(mapped), 'mapped_slide_positions': sum(len(row['slides']) for row in mapped.values()), 'unique_image_hashes': len(hash_positions)}
    for key, value in actual.items():
        _require(coverage[key] == value == manifest[key], f'Archive coverage drift: {key}')
    duplicates = [{'sha256': digest, 'positions': positions} for digest, positions in hash_positions.items() if len(positions) > 1]
    _require(_duplicate_key(duplicates) == _duplicate_key(coverage['duplicate_image_groups']), 'Duplicate imagery disclosure drift')
    for correction in registry['supersessions']:
        code = correction['shortcode']
        _require(code in indexed and correction['current_title'] == indexed[code]['title'], f'Superseded mapping not resolved: {code}')
        _require(correction.get('current_mapping') and correction.get('superseded_sources'), f'Missing supersession provenance: {code}')
        for relative in correction['superseded_sources']:
            _require(_path(root, relative).is_file(), f'Unresolved historical supersession source: {relative}')
    pattern_ids = set()
    required_text = ('id', 'title', 'theme', 'hook_mechanism', 'mismatch', 'visual_carrier', 'ending_mechanism', 'failure_mode', 'when_useful', 'interpretation', 'creative_hypothesis')
    for pattern in registry['patterns']:
        _require(all(isinstance(pattern.get(key), str) and pattern[key].strip() for key in required_text), 'Incomplete mechanism record')
        _require(pattern['id'] not in pattern_ids, f'Duplicate mechanism id: {pattern["id"]}')
        pattern_ids.add(pattern['id'])
        _require(pattern.get('sequence_modes') and pattern.get('limits') and all(isinstance(limit, str) and limit.strip() for limit in pattern['limits']), f'Missing mechanism mode or limit: {pattern["id"]}')
        for field in ('supporting_examples', 'counterexamples'):
            _require(isinstance(pattern.get(field), list) and pattern[field], f'Missing {field}: {pattern["id"]}')
            for example in pattern[field]:
                _require(example.get('observed') and example.get('interpretation') and example.get('slides'), f'Incomplete {field}: {pattern["id"]}')
                refs = []
                for number in example['slides']:
                    key = (example['shortcode'], number)
                    _require(key in all_refs, f'Unresolved slide reference: {key}')
                    refs.append(deepcopy(all_refs[key]))
                _require(example['observed'] == ' '.join(ref['observed'] for ref in refs), f'Observation differs from saved source: {pattern["id"]}')
                example['source_refs'] = refs
        for snapshot in pattern['performance_snapshots']:
            _require(snapshot['source'] in bound_sources, 'Unbound performance snapshot')
            snapshot_record = _pointer(bound_sources[snapshot['source']], snapshot['pointer'].rsplit('/', 1)[0])
            _require(snapshot_record.get('shortcode') == snapshot['shortcode'], 'Performance shortcode mapping drift')
            metrics = _pointer(bound_sources[snapshot['source']], snapshot['pointer'])
            _require(snapshot['observed_at'] == metrics['observed_at'], 'Performance observation date drift')
            _require(snapshot.get('limit'), 'Performance snapshot lacks a limit')
            _require(all(label in metrics and value == metrics[label] for label, value in snapshot['native_metrics'].items()), 'Performance snapshot value drift')
        pattern['evidence_basis'] = registry['evidence_basis']
        pattern['evidence_status'] = 'verified_saved_evidence'
    registry['status'] = 'verified_saved_evidence'
    return registry


def load_patterns(root: Path) -> dict[str, Any]:
    """Return verified saved evidence, or explicitly unavailable when absent.

    Present but malformed/missing/stale evidence raises PatternEvidenceError.
    Callers must report that error instead of silently treating it as verified.
    """
    root = Path(root)
    if not (root / REGISTRY_PATH).exists():
        return {'schema_version': SCHEMA_VERSION, 'status': 'unavailable', 'patterns': [], 'source_index': [], 'coverage': {}, 'supersessions': []}
    try:
        return _load_patterns(root)
    except PatternEvidenceError:
        raise
    except (KeyError, TypeError, ValueError, AttributeError) as exc:
        raise PatternEvidenceError(f'Malformed carousel pattern registry: {exc}') from exc


_STOP_WORDS = frozenset('a an and are as at be by can for from how i in is it me my of on or our that the their them this to us we what when with you your'.split())


def _terms(text: str) -> set[str]:
    return {word for word in re.findall(r'[a-z0-9]+', text.lower()) if len(word) > 2 and word not in _STOP_WORDS}


def find_patterns(root: Path, query: str, limit: int = 2) -> list[dict[str, Any]]:
    """Recall only lexical matches, each with its examples and limits intact."""
    if limit <= 0 or not _terms(query):
        return []
    query_terms = _terms(query)
    matches = []
    for pattern in load_patterns(root)['patterns']:
        prominent = ' '.join([pattern['title'], pattern['theme'], pattern['id'], *pattern.get('tags', []), *pattern['sequence_modes']])
        # Match the proposed use/mechanism, not generic limit or metrics prose.
        detail = ' '.join(pattern[key] for key in ('when_useful', 'interpretation', 'hook_mechanism', 'mismatch', 'visual_carrier', 'ending_mechanism', 'failure_mode'))
        score = 3 * len(query_terms & _terms(prominent)) + len(query_terms & _terms(detail))
        if score:
            matches.append((score, pattern['id'], pattern))
    return [pattern for _, _, pattern in sorted(matches, key=lambda match: (-match[0], match[1]))[:limit]]


def pattern_recall_text(pattern: dict[str, Any]) -> str:
    """FTS content retains the full mechanism, sources and editorial limits."""
    return json.dumps(pattern, ensure_ascii=False, indent=2)


def pattern_recall_snippet(text: str) -> str:
    """A compact result cannot drop the counterexample or evidence qualification."""
    pattern = json.loads(text)
    example = pattern['supporting_examples'][0]
    counter = pattern['counterexamples'][0]
    dates = sorted({ref['reviewed_on'] for entry in pattern['supporting_examples'] + pattern['counterexamples'] for ref in entry['source_refs']})
    return (f'Saved inspection ({", ".join(dates)}). {pattern["interpretation"]} '
            f'Example: {example["shortcode"]} slides {example["slides"]}. '
            f'Counterexample: {counter["shortcode"]} slides {counter["slides"]}: {counter["interpretation"]} '
            f'Limit: {pattern["limits"][0]}')
