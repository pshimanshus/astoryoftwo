"""Carousel-specific evidence and concept-lock analysis.

This module deliberately keeps three evidence classes separate: official
platform documentation, patterns observed in the reviewed local corpus, and
creative hypotheses to test.  The readiness score is an internal editorial
floor; it is not a reach or ranking prediction.
"""
from __future__ import annotations

import json
import hashlib
import re
import tempfile
from pathlib import Path
from typing import Any

INTELLIGENCE_SCHEMA_VERSION = "carousel-intelligence/v1"
SEED_SCHEMA_VERSION = "carousel-seed-evidence/v1"
DEFAULT_HEURISTIC_FLOOR = 70
REQUIRED_DIMENSION_MINIMUMS = {"scene_proof": 3, "relationship_motion": 3, "send_save_reason": 3}
NATIVE_METRIC_LABELS = ("Views", "Viewers", "Shares", "Saves", "Profile visits", "Follows", "reach", "sends")
OFFICIAL_SOURCES = (
    "https://transparency.meta.com/features/explaining-ranking/ig-feed/",
    "https://transparency.meta.com/features/explaining-ranking/ig-feed-recommendations/",
    "https://about.instagram.com/blog/announcements/instagram-ranking-explained",
)
GATE_POLICY_SCHEMA_VERSION = "carousel-intelligence-gate/v2"

# These are evidence-mapping aliases, not new creative requirements.  The
# verified seed audit uses several editorial phrases for the same story
# function, while the first analyzer pass only recognized the literal words
# ``payoff`` and ``thesis``.
_PAYOFF_MARKERS = (
    r"payoff",
    r"reframe",
    r"terminal",
    r"final synthesis",
    r"synthesis",
    r"names the (?:emotional )?(?:result|behavior|actual longing|whole sequence)",
    r"compact name",
    r"principle",
    r"circular close",
    r"closes with a memorable loop",
    r"time passes,? care remains",
    r"compresses time while preserving affection",
    r"affection returns",
    r"intimacy",
    r"devotion",
    r"meaning",
    r"became ours",
    r"still choosing",
    r"still learning",
    r"maybe love",
    r"feels softer",
    r"bearable again",
    r"full story",
    r"weather inside you",
    r"makes the metaphor bodily",
    r"thesis",
    r"ending",
)
_RELATIONSHIP_MARKERS = (
    r"choos",
    r"listen",
    r"hold",
    r"help",
    r"sit",
    r"stay",
    r"leave",
    r"fight",
    r"turn",
    r"share",
    r"learn",
    r"wait",
    r"carry",
    r"ask",
    r"respond",
    r"repair",
    r"reconcil",
    r"support",
    r"preserv(?:es|ing)? affection",
    r"time passes",
    r"care remains",
    r"affection returns",
    r"relationship",
)
_ADDRESSABILITY_MARKERS = (
    r"couple",
    r"partner",
    r"relationship",
    r"together",
    r"love",
    r"marri(?:age|ed|es)?",
    r"husband",
    r"wife",
    r"biwi",
    r"family",
    r"ghar",
    r"team",
    r"long distance",
    r"ordinary time",
    r"weather",
    r"chaos",
    r"silence",
    r"calm",
    r"intimacy",
    r"story",
    r"people",
    r"care",
    r"devotion",
    r"ours",
    r"home",
    r"choose",
    r"choosing",
    r"learn",
    r"learning",
    r"walking there",
    r"you",
    r"we",
    r"us",
    r"when",
    r"why",
    r"how",
    r"rule",
)

def _read_json(path: Path) -> Any:
    if not path.is_file() or path.is_symlink():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def carousel_gate_policy(root: Path) -> dict[str, Any]:
    """Return the hash-bound creator-approved gate policy.

    A missing, malformed, drifted, or threshold-changing policy disables the
    gate. This makes activation explicit and fail-closed without weakening the
    reviewed 70-point and 3/5 floors.
    """

    root = root.expanduser().resolve()
    policy_path = root / "config/carousel-intelligence-gate.json"
    payload = _read_json(policy_path)
    if not isinstance(payload, dict) or payload.get("schema_version") not in {GATE_POLICY_SCHEMA_VERSION, "carousel-intelligence-gate/v1"}:
        return {"enabled": False, "mode": "fail_closed", "reason": "missing_or_invalid_policy"}

    errors: list[str] = []
    current = payload.get("schema_version") == GATE_POLICY_SCHEMA_VERSION
    if current and (payload.get("evaluation") != "structural_with_advisory_heuristics"
                    or payload.get("required_story_contract") != "carousel-sequence/v1"):
        errors.append("sequence_evaluation_policy")
    if payload.get("mode") != "fail_closed":
        errors.append("mode")
    thresholds = payload.get("thresholds") if isinstance(payload.get("thresholds"), dict) else {}
    if thresholds.get("heuristic_floor") != DEFAULT_HEURISTIC_FLOOR:
        errors.append("heuristic_floor")
    if thresholds.get("required_dimension_minimums") != REQUIRED_DIMENSION_MINIMUMS:
        errors.append("required_dimension_minimums")

    bindings = payload.get("bindings") if isinstance(payload.get("bindings"), dict) else {}
    for name in (("visual_decisions", "local_path_map", "pattern_registry") if current else ("visual_decisions", "local_path_map")):
        binding = bindings.get(name) if isinstance(bindings.get(name), dict) else {}
        relative = binding.get("path")
        expected_hash = binding.get("sha256")
        if not isinstance(relative, str) or not isinstance(expected_hash, str):
            errors.append(f"{name}_binding")
            continue
        bound_path = root / relative
        if not bound_path.is_file() or bound_path.is_symlink():
            errors.append(f"{name}_missing")
            continue
        actual_hash = hashlib.sha256(bound_path.read_bytes()).hexdigest()
        if actual_hash != expected_hash:
            errors.append(f"{name}_drift")

    requested = payload.get("enabled") is True
    if errors:
        return {
            "enabled": False,
            "mode": "fail_closed",
            "reason": "policy_validation_failed",
            "errors": errors,
        }
    return {
        "enabled": requested,
        "mode": "fail_closed",
        "reason": ("creator_approved_workflow" if current else "creator_approved_calibration") if requested else "policy_disabled",
        "approved_on": payload.get("approved_on"),
        "approved_by": payload.get("approved_by"),
        "evaluation": payload.get("evaluation", "historical_keyword_calibration"),
    }
def _first(data: dict[str, Any], *keys: str) -> Any:
    for key in keys:
        value = data.get(key)
        if value not in (None, "", [], {}):
            return value
    return None


def _slides(package_dir: Path) -> list[dict[str, Any]]:
    raw = _read_json(package_dir / "slides.json")
    if raw is None:
        raw = _read_json(package_dir / "copy.json")
    if isinstance(raw, dict):
        raw = raw.get("slides") or raw.get("sequence") or []
    if not isinstance(raw, list):
        return []
    result = []
    for index, item in enumerate(raw, 1):
        if not isinstance(item, dict):
            continue
        result.append({
            "slide": int(item.get("slide") or item.get("index") or index),
            "copy": str(_first(item, "copy", "text", "main_on_image_text", "on_image_text") or "").strip(),
            "scene": str(_first(item, "visual", "scene", "physical_action", "observed_scene", "visual_description") or "").strip(),
            "story_job": str(_first(item, "story_job", "role", "job") or "").strip(),
            "transition": str(_first(item, "transition", "bridge", "continuity_lock") or "").strip(),
            "payoff": str(_first(item, "payoff", "reframe", "ending") or "").strip(),
            "send_reason": str(_first(item, "send_reason", "save_reason", "cta_intent", "cta") or "").strip(),
            "relationship_motion": str(_first(item, "relationship_motion", "relationship_turn", "relationship_state") or "").strip(),
            "evidence_class": str(item.get("evidence_class") or "hypothesis"),
        })
    by_slide = {item["slide"]: item for item in result}
    for name in ("visual-plan.json", "visual-plan-quality.json", "post-copy-visual-room.json"):
        payload = _read_json(package_dir / name)
        candidates = payload.get("slides") if isinstance(payload, dict) else payload
        if isinstance(payload, dict) and not isinstance(candidates, list):
            candidates = payload.get("visual_plan") or payload.get("visuals") or []
        if not isinstance(candidates, list):
            continue
        for item in candidates:
            if not isinstance(item, dict):
                continue
            number = item.get("slide") or item.get("index")
            if not isinstance(number, int):
                continue
            target = by_slide.setdefault(number, {"slide": number, "copy": "", "scene": "", "story_job": "", "transition": "", "payoff": "", "send_reason": "", "relationship_motion": "", "evidence_class": "hypothesis"})
            target["scene"] = target["scene"] or str(_first(item, "visual", "scene", "physical_action", "observed_scene", "visual_description") or "").strip()
            target["story_job"] = target["story_job"] or str(_first(item, "story_job", "role", "job") or "").strip()
            target["transition"] = target["transition"] or str(_first(item, "transition", "bridge", "continuity_lock") or "").strip()
            target["relationship_motion"] = target["relationship_motion"] or str(_first(item, "relationship_motion", "relationship_turn", "relationship_state") or "").strip()
    return [by_slide[number] for number in sorted(by_slide)]


def _concept(package_dir: Path) -> dict[str, Any]:
    merged: dict[str, Any] = {}
    for name in ("manifest.json", "creative-context.json", "copy.json", "concept.json"):
        value = _read_json(package_dir / name)
        if isinstance(value, dict):
            merged.update(value)
    return merged


def _workspace_root(package_dir: Path) -> Path:
    package_dir = package_dir.expanduser().resolve()
    for candidate in (package_dir, *package_dir.parents):
        if (candidate / "config").is_dir() and (candidate / "output").is_dir():
            return candidate
    return package_dir.parents[3] if len(package_dir.parents) > 3 else package_dir


def _norm(value: str) -> str:
    return re.sub(r"\s+", " ", value.lower()).strip()


def _has_relationship(slides: list[dict[str, Any]], concept: dict[str, Any]) -> bool:
    text = " ".join(str(value) for value in concept.values() if isinstance(value, (str, list)))
    text += " " + " ".join(f"{s['copy']} {s['scene']} {s['story_job']} {s['relationship_motion']}" for s in slides)
    return any(re.search(rf"\b{marker}\w*\b", text.lower()) for marker in _RELATIONSHIP_MARKERS)


def _has_payoff(slides: list[dict[str, Any]], concept: dict[str, Any]) -> bool:
    if not slides:
        return False
    last = slides[-1]
    explicit = " ".join((last["story_job"], last["payoff"], last["copy"]))
    explicit += " " + " ".join(str(value) for key, value in concept.items() if key in {"payoff", "reframe", "ending", "thesis"})
    return any(re.search(marker, explicit.lower()) for marker in _PAYOFF_MARKERS)


def _has_send_save(slides: list[dict[str, Any]], concept: dict[str, Any]) -> bool:
    if any(slide["send_reason"] for slide in slides):
        return True
    text = " ".join(str(value) for key, value in concept.items() if key in {"send_reason", "save_reason", "cta", "cta_intent", "share_reason"})
    if text.strip():
        return True
    # A locked terminal thesis with an explicit payoff role is a concrete
    # send/save invitation even when the brief did not name the CTA separately.
    if not slides or not slides[-1]["copy"] or not _has_payoff(slides, concept):
        return False
    # A terminal, relationship-specific line is a concrete send/save reason.
    # This remains an observed editorial signal; it is not a platform ranking
    # claim and does not infer shareability from generic sentiment alone.
    terminal = f"{slides[-1]['story_job']} {slides[-1]['copy']}"
    return any(re.search(marker, terminal.lower()) for marker in _ADDRESSABILITY_MARKERS)


def _load_seed(root: Path) -> dict[str, Any]:
    path = root / "output/reports/2026-09-19-full-carousel-audit/current-carousel-sequences.json"
    value = _read_json(path)
    if isinstance(value, dict) and value.get("schema_version") == SEED_SCHEMA_VERSION:
        return value
    audit = _read_json(root / "output/reports/2026-09-19-full-carousel-audit/current-carousel-audit.json") or {}
    return {"schema_version": SEED_SCHEMA_VERSION, "source_report": audit.get("report"), "coverage": {}, "sequences": []}


def _load_local_path_map(root: Path) -> dict[str, Any]:
    payload = _read_json(
        root / "output/reports/2026-09-19-full-carousel-audit/local-slide-path-map.json"
    )
    if not isinstance(payload, dict) or payload.get("schema_version") != "carousel-local-path-map/v1":
        return {}
    sequences = payload.get("sequences")
    return sequences if isinstance(sequences, dict) else {}


def _load_visual_decisions(root: Path) -> dict[str, Any]:
    payload = _read_json(
        root / "output/reports/2026-09-19-full-carousel-audit/visual-verification-decisions.json"
    )
    if not isinstance(payload, dict) or payload.get("schema_version") != "carousel-visual-verification-decisions/v1":
        return {}
    sequences = payload.get("sequences")
    return sequences if isinstance(sequences, dict) else {}


def _display_path(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _local_slide_inventory(root: Path, seed: dict[str, Any]) -> dict[str, Any]:
    """Inventory the slide files that are actually present in this checkout.

    The verified audit can establish that pixels were viewed elsewhere, but a
    calibration artifact must also state what this workspace can reproduce.
    Missing files are data gaps and never get silently counted as reviewed.
    """

    path_map = _load_local_path_map(root)
    sequences: list[dict[str, Any]] = []
    expected = available = 0
    for sequence in seed.get("sequences", []) if isinstance(seed.get("sequences"), list) else []:
        if not isinstance(sequence, dict):
            continue
        shortcode = str(sequence.get("shortcode") or "")
        slide_numbers = [
            int(item.get("slide"))
            for item in sequence.get("slides", [])
            if isinstance(item, dict) and str(item.get("slide") or "").isdigit()
        ]
        paths: dict[int, str] = {}
        hashes: dict[int, str] = {}
        missing: list[int] = []
        mapped = path_map.get(shortcode) if isinstance(path_map.get(shortcode), dict) else {}
        for number in slide_numbers:
            expected += 1
            mapped_path: Path | None = None
            explicit_paths = mapped.get("paths") if isinstance(mapped.get("paths"), dict) else {}
            explicit = explicit_paths.get(str(number))
            if isinstance(explicit, str) and explicit:
                candidate = Path(explicit).expanduser()
                mapped_path = candidate if candidate.is_absolute() else root / candidate
            elif isinstance(mapped.get("pattern"), str):
                slide_map = mapped.get("slide_map") if isinstance(mapped.get("slide_map"), dict) else {}
                asset = slide_map.get(str(number))
                if isinstance(asset, int):
                    candidate = Path(mapped["pattern"].format(asset=asset)).expanduser()
                    mapped_path = candidate if candidate.is_absolute() else root / candidate
            candidates = [
                *([mapped_path] if mapped_path is not None else []),
                root / "corpus/media" / shortcode / f"slide-{number:02d}.jpg",
                root / "corpus/media" / shortcode / f"slide-{number}.jpg",
                root / "corpus/media" / shortcode / f"slide-{number:02d}.png",
                root / "corpus/media" / shortcode / f"slide-{number}.png",
            ]
            path = next((candidate for candidate in candidates if candidate.is_file() and not candidate.is_symlink()), None)
            if path is None:
                missing.append(number)
                continue
            available += 1
            paths[number] = _display_path(path, root)
            hashes[number] = "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()
        sequences.append({
            "shortcode": shortcode,
            "expected_slide_count": len(slide_numbers),
            "available_slide_count": len(paths),
            "missing_slides": missing,
            "available_paths": paths,
            "sha256": hashes,
            "status": "complete" if not missing else "partial" if paths else "missing",
            "review_method": "codex_view_image" if paths else None,
            "mapping_note": mapped.get("note") if isinstance(mapped, dict) else None,
        })
    return {
        "expected_slide_count": expected,
        "available_slide_count": available,
        "missing_slide_count": expected - available,
        "visual_status": "complete" if expected and available == expected else "partial" if available else "missing",
        "sequences": sequences,
        "note": "Workspace inventory resolves the reviewed explicit path map first, then corpus/media fallbacks. It is separate from the verified audit's historical direct-pixel count.",
    }


def _metric_rows(root: Path) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from pipeline.stages.carousel_results import load_metric_observations
    rows = [row for row in load_metric_observations(root) if row.get("post_type") in {"sidecar", "carousel"}]
    coverage = {"eligible_rows": len(rows), "native_metric_labels": list(NATIVE_METRIC_LABELS),
                "age_bands_complete": False, "visual_evidence_complete": False,
                "note": "Dated rows and same-format sample/coverage checks in results analysis govern comparison; age-band labels alone are insufficient.",
                "causal_claims_allowed": False}
    return rows, coverage


def analyze_package(package_dir: Path, *, root: Path | None = None) -> dict[str, Any]:
    package_dir = package_dir.expanduser().resolve()
    root = (root or _workspace_root(package_dir)).resolve()
    from pipeline.stages.carousel_sequence import package_sequence_inputs, sequence_enabled
    context, canonical_slides = package_sequence_inputs(package_dir)
    if sequence_enabled(context, canonical_slides):
        return _analyze_sequence_package(package_dir, root, context, canonical_slides)
    concept = _concept(package_dir)
    slides = _slides(package_dir)
    seed = _load_seed(root)
    metric_rows, metric_coverage = _metric_rows(root)
    visual_count = sum(bool(slide["scene"]) for slide in slides)
    copy_count = sum(bool(slide["copy"]) for slide in slides)
    jobs_count = sum(bool(slide["story_job"]) for slide in slides)
    fingerprints = [_norm(slide["scene"]) for slide in slides if slide["scene"]]
    unique_scenes = len(set(fingerprints))
    continuous = bool(concept.get("continuous_sequence") or concept.get("allow_repeated_scene"))
    repeated_static = bool(fingerprints and len(fingerprints) >= 3 and (len(fingerprints) - unique_scenes) / len(fingerprints) > 0.5 and not continuous)
    cover = slides[0] if slides else {}
    # The cover's story job is reviewed evidence about what the visible copy
    # and scene are doing. Excluding it caused concrete couple hooks such as a
    # first-date image or a repeated partner-request setup to look generic.
    cover_text = (
        f"{cover.get('copy', '')} {cover.get('scene', '')} "
        f"{cover.get('story_job', '')} {cover.get('relationship_motion', '')}"
    )
    addressable_signal = any(re.search(rf"\b{marker}\w*\b", cover_text.lower()) for marker in _ADDRESSABILITY_MARKERS)
    cover_addressable = bool(cover.get("copy") and cover.get("scene") and addressable_signal and len(cover.get("copy", "").split()) >= 2)
    relationship = _has_relationship(slides, concept)
    payoff = _has_payoff(slides, concept)
    send_save = _has_send_save(slides, concept)
    role_text = " ".join(slide["story_job"] for slide in slides)
    progression_signal = any(
        re.search(rf"\b{marker}\w*\b", role_text.lower())
        for marker in (
            r"escalat",
            r"turn",
            r"conflict",
            r"reversal",
            r"payoff",
            r"deepening",
            r"bridge",
            r"shift",
            r"thesis",
            r"ending",
            r"compresses time",
            r"time passes",
            r"preserv(?:es|ing)? affection",
            r"affection returns",
            r"private habit",
            r"micro-ritual",
            r"specificity",
            r"inner life",
            r"emotional expansion",
            r"keeps the sequence moving",
        )
    )
    progression = len(set(fingerprints)) >= 2 and len(slides) >= 2 and (progression_signal or relationship)
    alignment = bool(slides) and copy_count == len(slides) and visual_count == len(slides)
    scene_score = round(5 * visual_count / len(slides)) if slides else 0
    motion_score = 5 if relationship else 0
    send_score = 5 if send_save else 0
    dimensions = {
        "hook_addressability": {"score": 20 if cover_addressable else 0, "max": 20},
        "visible_scene_proof": {"score": round(20 * visual_count / len(slides)) if slides else 0, "max": 20},
        "beat_novelty": {"score": 15 if progression and not repeated_static else (8 if progression else 0), "max": 15},
        "relationship_motion": {"score": 15 if relationship else 0, "max": 15},
        "payoff_reframe": {"score": 15 if payoff else 0, "max": 15},
        "send_save_reason": {"score": 10 if send_save else 0, "max": 10},
        "copy_visual_cohesion": {"score": 5 if alignment else 0, "max": 5},
    }
    total = sum(item["score"] for item in dimensions.values())
    gates = {
        "cover_addressable": cover_addressable,
        "all_slides_have_visible_scene": bool(slides) and visual_count == len(slides),
        "all_slides_have_story_job": bool(slides) and jobs_count == len(slides),
        "sequence_progression": progression,
        "relationship_movement": relationship,
        "ending_payoff_or_reframe": payoff,
        "send_or_save_reason": send_save,
        "copy_visual_alignment": alignment,
        "repeated_static_scene_rejected": not repeated_static,
    }
    repairs = []
    if not slides: repairs.append("Add slides.json with one structured record per beat.")
    if not gates["cover_addressable"]: repairs.append("Rewrite the cover around one specific, addressable couple situation or claim.")
    if not gates["all_slides_have_visible_scene"]: repairs.append("Give every slide a concrete action, prop, or spatial change.")
    if not gates["all_slides_have_story_job"]: repairs.append("Assign an explicit story job to every slide.")
    if not gates["sequence_progression"]: repairs.append("Add escalation, relationship movement, or a reversal between beats.")
    if not gates["relationship_movement"]: repairs.append("Show the relationship changing through a choice, response, conflict, or repair.")
    if not gates["ending_payoff_or_reframe"]: repairs.append("Make the ending deepen or change the opening meaning.")
    if not gates["send_or_save_reason"]: repairs.append("Add a concrete reason someone would send or save this to a partner.")
    if not gates["copy_visual_alignment"]: repairs.append("Align each copy beat with its planned visual proof.")
    if not gates["repeated_static_scene_rejected"]: repairs.append("Replace repeated static scenes with visible beat changes or explicitly mark one continuous scene.")
    if total < DEFAULT_HEURISTIC_FLOOR: repairs.append(f"Raise the internal readiness score from {total} to at least {DEFAULT_HEURISTIC_FLOOR}.")
    if scene_score < 3: repairs.append("Scene proof must score at least 3/5.")
    if motion_score < 3: repairs.append("Relationship motion must score at least 3/5.")
    if send_score < 3: repairs.append("Send/save reason must score at least 3/5.")
    blocked = bool(repairs)
    return {
        "schema_version": INTELLIGENCE_SCHEMA_VERSION,
        "package": str(package_dir),
        "sequence": {"title": concept.get("title") or concept.get("name"), "slide_count": len(slides), "source_provenance": "package concept/slides/copy/visual-plan artifacts"},
        "slides": [{**slide, "evidence_class": slide.get("evidence_class") or "hypothesis"} for slide in slides],
        "evidence": {"official_platform_signals": list(OFFICIAL_SOURCES), "observed_corpus_pattern": {"seed_schema": seed.get("schema_version"), "coverage": seed.get("coverage", {}), "sequence_identities": [{"shortcode": item.get("shortcode"), "source_url": item.get("source_url"), "slide_count": item.get("slide_count")} for item in seed.get("sequences", []) if isinstance(item, dict)]}, "hypotheses": ["Scene-led progression and a reframe are worth testing; this report does not establish causality."]},
        "metrics": {"native_labels": list(NATIVE_METRIC_LABELS), "eligible_carousel_rows": metric_rows, "coverage": metric_coverage},
        "heuristic": {"floor": DEFAULT_HEURISTIC_FLOOR, "total": total, "dimensions": dimensions, "required_dimension_scores": {"scene_proof": scene_score, "relationship_motion": motion_score, "send_save_reason": send_score}},
        "concept_gate": {"status": "blocked" if blocked else "passed", "gates": gates, "repairs": repairs, "causal_claims_allowed": False, "note": "Internal creative readiness only; not a prediction of Instagram reach or ranking."},
    }


def _analyze_sequence_package(package_dir: Path, root: Path, context: dict, slides: list[dict]) -> dict[str, Any]:
    """Validate current handoffs without certifying copy/image meaning by regex."""
    from pipeline.stages.carousel_sequence import sequence_input_fingerprint, sequence_plan_issues
    from pipeline.stages.carousel_visual_storytelling import physical_action_issue

    repairs = sequence_plan_issues(context, slides)
    for slide in slides:
        issue = physical_action_issue(slide.get("physical_action"), copy=slide.get("copy"))
        if issue:
            repairs.append(f"slide {slide.get('slide')}: {issue}")
    plan = context.get("story_plan") if isinstance(context.get("story_plan"), dict) else {}
    evidence: dict[str, Any] = {"status": "unavailable", "patterns": [], "limits": []}
    try:
        from pipeline.stages.carousel_patterns import load_patterns, find_patterns
        registry = load_patterns(root)
        query = " ".join(str(plan.get(k) or "") for k in ("theme", "sequence_mode", "mismatch", "payoff"))
        evidence = {"status": registry.get("status"), "coverage": registry.get("coverage", {}),
                    "supersessions": registry.get("supersessions", {}),
                    "patterns": find_patterns(root, query), "causal_claims_allowed": False}
        refs = context.get("research_refs", [])
        known = {p["id"] for p in registry.get("patterns", [])}
        if not isinstance(refs, list) or any(
            not ((isinstance(r, str) and r in known) or
                 (isinstance(r, dict) and isinstance(r.get("pattern_id"), str)
                  and r["pattern_id"] in known and isinstance(r.get("why"), str) and r["why"].strip()))
            for r in refs
        ):
            repairs.append("research_refs must contain verified pattern ids or {pattern_id, why} records")
    except (ValueError, OSError) as exc:
        evidence = {"status": "invalid", "patterns": [], "limits": [str(exc)], "causal_claims_allowed": False}
        if context.get("research_refs"):
            repairs.append("selected research_refs are unavailable or stale; repair evidence before relying on them")
    metrics: list[dict] = []
    # Current production does not scan the complete historical corpus. Results
    # analysis has its own explicit command and date/denominator safeguards.
    return {
        "schema_version": INTELLIGENCE_SCHEMA_VERSION,
        "package": str(package_dir), "input_sha256": sequence_input_fingerprint(context, slides),
        "research_refs": context.get("research_refs", []),
        "sequence": {"title": context.get("title"), "slide_count": len(slides),
                     "mode": plan.get("sequence_mode"), "story_plan": plan,
                     "source_provenance": "approved creative-context and canonical slides"},
        "slides": slides, "evidence": evidence,
        "metrics": {"native_labels": list(NATIVE_METRIC_LABELS), "eligible_carousel_rows": metrics,
                    "coverage": {"status": "use_results_review", "causal_claims_allowed": False}},
        "heuristic": {"blocking": False, "total": None, "floor": None, "dimensions": {},
                      "note": "Historical keyword scores do not certify current editorial or pixel quality."},
        "concept_gate": {"status": "blocked" if repairs else "passed", "repairs": repairs,
                         "gates": {"story_and_slide_contract": not repairs},
                         "pixel_review_status": "not_run", "causal_claims_allowed": False,
                         "note": "Structural handoff only. Creator concept lock and actual-pixel review remain required; not a prediction of reach."},
    }


def render_intelligence_markdown(report: dict[str, Any]) -> str:
    gate = report["concept_gate"]
    heuristic = report["heuristic"]
    score = "Advisory only; story and pixel meaning require review." if heuristic.get("blocking") is False else f"Historical rubric: {heuristic['total']}/{heuristic['floor']} floor"
    lines = ["# Carousel intelligence", "", f"**Schema:** `{report['schema_version']}`", f"**Concept gate:** **{gate['status']}**", score, "", "This is a creative readiness measure. It is not Instagram's private algorithm, not a prediction of reach, and not a causal performance claim.", "", "## Evidence classes", "", "- Observed corpus patterns: what the saved carousel inspection contains, with its limits.", "- Hypotheses: what the next package should test.", "", "## Heuristic dimensions", ""]
    for name, item in heuristic["dimensions"].items():
        lines.append(f"- {name}: {item['score']}/{item['max']}")
    lines += ["", "## Gate results", ""]
    for name, passed in gate["gates"].items():
        lines.append(f"- {'PASS' if passed else 'BLOCK'} — {name}")
    lines += ["", "## Repair actions", ""]
    lines += [f"- {item}" for item in gate["repairs"]] or ["- None."]
    lines += ["", "## Metrics and coverage", "", f"Native labels preserved: {', '.join(report['metrics']['native_labels'])}.", f"Eligible carousel rows: {len(report['metrics']['eligible_carousel_rows'])}.", "Reels and single-image posts are excluded from carousel calibration.", "Causal claims remain disabled when age bands, metric provenance, or visual coverage are incomplete.", ""]
    return "\n".join(lines)


def write_intelligence_artifacts(package_dir: Path, report: dict[str, Any]) -> dict[str, Any]:
    package_dir = package_dir.resolve()
    (package_dir / "carousel-intelligence.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    (package_dir / "carousel-intelligence.md").write_text(render_intelligence_markdown(report), encoding="utf-8")
    return report


def analyze_and_write(package_dir: Path, *, root: Path | None = None) -> dict[str, Any]:
    return write_intelligence_artifacts(package_dir, analyze_package(package_dir, root=root))


def dry_run_seed(root: Path) -> dict[str, Any]:
    """Apply the package analyzer to every verified seed sequence in memory.

    The temporary package files are intentionally ephemeral: the dry run
    never migrates or rewrites archived carousel packages.
    """
    root = root.expanduser().resolve()
    seed = _load_seed(root)
    sequences = seed.get("sequences", []) if isinstance(seed.get("sequences"), list) else []
    results: list[dict[str, Any]] = []
    with tempfile.TemporaryDirectory(prefix="carousel-intelligence-dry-run-") as directory:
        workspace = Path(directory)
        for sequence in sequences:
            if not isinstance(sequence, dict):
                continue
            shortcode = str(sequence.get("shortcode") or "unknown")
            package = workspace / shortcode
            package.mkdir()
            planned = []
            for item in sequence.get("slides", []) if isinstance(sequence.get("slides"), list) else []:
                if not isinstance(item, dict):
                    continue
                planned.append({
                    "slide": item.get("slide"),
                    "copy": item.get("copy"),
                    "visual": item.get("observed_scene"),
                    "role": item.get("story_job"),
                    "payoff": item.get("payoff"),
                    "send_reason": item.get("send_reason"),
                    "relationship_motion": item.get("relationship_motion"),
                })
            (package / "slides.json").write_text(json.dumps({"slides": planned}), encoding="utf-8")
            (package / "concept.json").write_text(json.dumps({"title": shortcode}), encoding="utf-8")
            report = analyze_package(package, root=root)
            gate = report["concept_gate"]
            results.append({
                "shortcode": shortcode,
                "slide_count": len(planned),
                "status": gate["status"],
                "heuristic_total": report["heuristic"]["total"],
                "heuristic_dimensions": report["heuristic"]["dimensions"],
                "gates": gate["gates"],
                "repairs": gate["repairs"],
                "repair_count": len(gate["repairs"]),
            })
    gate_counts: dict[str, int] = {}
    for result in results:
        for name, passed in result["gates"].items():
            if passed:
                gate_counts[name] = gate_counts.get(name, 0) + 1
    totals = [result["heuristic_total"] for result in results]
    return {
        "schema_version": "carousel-intelligence-dry-run/v1",
        "seed_schema_version": seed.get("schema_version"),
        "source_report": seed.get("source_report"),
        "coverage": seed.get("coverage", {}),
        "sequence_count": len(results),
        "slide_count": sum(result["slide_count"] for result in results),
        "passed_count": sum(result["status"] == "passed" for result in results),
        "blocked_count": sum(result["status"] == "blocked" for result in results),
        "heuristic_summary": {
            "floor": DEFAULT_HEURISTIC_FLOOR,
            "min": min(totals) if totals else 0,
            "max": max(totals) if totals else 0,
            "average": round(sum(totals) / len(totals), 2) if totals else 0,
        },
        "gate_pass_counts": gate_counts,
        "sequences": results,
        "workspace_visual_inventory": _local_slide_inventory(root, seed),
        "causal_claims_allowed": False,
        "note": "Dry-run calibration only. Observed patterns do not establish that any visual choice caused performance.",
    }


def write_dry_run_report(root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    report = dry_run_seed(root)
    target = (output_dir or root / "output/reports/2026-09-19-full-carousel-audit").expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    (target / "carousel-intelligence-dry-run.json").write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    lines = [
        "# Carousel intelligence dry run",
        "",
        f"Verified sequences: **{report['sequence_count']}**",
        f"Verified slides: **{report['slide_count']}**",
        f"Passed: **{report['passed_count']}**; blocked: **{report['blocked_count']}**",
        f"Heuristic range: **{report['heuristic_summary']['min']}–{report['heuristic_summary']['max']}**; average **{report['heuristic_summary']['average']}**; floor **{report['heuristic_summary']['floor']}**.",
        "",
        "This is calibration evidence only. It does not establish causality or predict Instagram distribution.",
        "",
        "## Gate coverage",
        "",
    ]
    for name, count in sorted(report["gate_pass_counts"].items()):
        lines.append(f"- {name}: {count}/{report['sequence_count']} pass")
    lines += ["", "## Sequences", "", "| Shortcode | Slides | Status | Score | Repairs |", "| --- | ---: | --- | ---: | ---: |"]
    for item in report["sequences"]:
        lines.append(f"| {item['shortcode']} | {item['slide_count']} | {item['status']} | {item['heuristic_total']} | {item['repair_count']} |")
    (target / "carousel-intelligence-dry-run.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return report


def _calibration_classification(
    *,
    before: bool | None,
    after: bool,
    pixel_status: str,
) -> str:
    if before is False and after is True:
        return "evidence_mapping_gap"
    if after:
        return "preserved_pass"
    if pixel_status != "complete":
        return "data_gap"
    return "true_creative_gap"


def calibrate_seed(root: Path) -> dict[str, Any]:
    """Create a per-carousel calibration table without changing seed packages."""

    root = root.expanduser().resolve()
    gate_policy = carousel_gate_policy(root)
    seed = _load_seed(root)
    after = dry_run_seed(root)
    baseline_path = root / "output/reports/2026-09-19-full-carousel-audit/carousel-intelligence-dry-run.json"
    baseline = _read_json(baseline_path) or {}
    # Once a calibration has been accepted, keep its original before-state as
    # the comparison point even though the regular dry-run artifact is
    # refreshed after every analyzer change.
    prior_calibration = _read_json(
        root / "output/reports/2026-09-19-full-carousel-audit/carousel-intelligence-calibration.json"
    ) or {}
    if isinstance(prior_calibration.get("sequences"), list) and prior_calibration.get("baseline"):
        reconstructed = []
        gate_names = tuple(after.get("sequences", [{}])[0].get("gates", {}).keys()) if after.get("sequences") else ()
        for item in prior_calibration["sequences"]:
            if not isinstance(item, dict):
                continue
            before_row = item.get("before") if isinstance(item.get("before"), dict) else {}
            failed = set(before_row.get("failed_gates") or [])
            reconstructed.append({
                "shortcode": item.get("shortcode"),
                "status": before_row.get("status"),
                "heuristic_total": before_row.get("score"),
                "gates": {name: name not in failed for name in gate_names},
            })
        if reconstructed:
            baseline = {
                "passed_count": prior_calibration["baseline"].get("passed_count"),
                "blocked_count": prior_calibration["baseline"].get("blocked_count"),
                "sequences": reconstructed,
            }
    before_by_shortcode = {
        str(item.get("shortcode")): item
        for item in baseline.get("sequences", [])
        if isinstance(item, dict)
    }
    after_by_shortcode = {
        str(item.get("shortcode")): item
        for item in after.get("sequences", [])
        if isinstance(item, dict)
    }
    inventory_by_shortcode = {
        str(item.get("shortcode")): item
        for item in after.get("workspace_visual_inventory", {}).get("sequences", [])
        if isinstance(item, dict)
    }
    visual_decisions = _load_visual_decisions(root)
    rows: list[dict[str, Any]] = []
    for sequence in seed.get("sequences", []) if isinstance(seed.get("sequences"), list) else []:
        if not isinstance(sequence, dict):
            continue
        shortcode = str(sequence.get("shortcode") or "")
        before = before_by_shortcode.get(shortcode, {})
        current = after_by_shortcode.get(shortcode, {})
        inventory = inventory_by_shortcode.get(shortcode, {})
        visual_review = visual_decisions.get(shortcode)
        if not isinstance(visual_review, dict):
            visual_review = {
                "status": "block",
                "classification": "data_gap",
                "reason": "No current visual-verification decision is recorded.",
            }
        before_gates = before.get("gates", {}) if isinstance(before.get("gates"), dict) else {}
        current_gates = current.get("gates", {}) if isinstance(current.get("gates"), dict) else {}
        classifications = {
            name: _calibration_classification(
                before=before_gates.get(name),
                after=bool(value),
                pixel_status=str(inventory.get("status") or "missing"),
            )
            for name, value in current_gates.items()
        }
        changed = [
            name for name, value in current_gates.items()
            if before_gates.get(name) is not None and bool(before_gates.get(name)) != bool(value)
        ]
        mapping_repairs = [
            name for name, classification in classifications.items()
            if classification in {"evidence_mapping_gap", "analyzer_false_negative"}
        ]
        if inventory.get("status") != "complete":
            effective_decision = "block_data_gap"
        elif visual_review.get("status") != "pass":
            effective_decision = (
                "block_analyzer_false_positive"
                if visual_review.get("classification") == "analyzer_false_positive"
                else "keep_blocked"
            )
        elif current.get("status") == "passed":
            effective_decision = "allow_pass"
        else:
            effective_decision = "block_analyzer_unresolved"
        rows.append({
            "shortcode": shortcode,
            "slide_count": int(sequence.get("slide_count") or len(sequence.get("slides") or [])),
            "pixel_evidence": {
                "status": inventory.get("status", "missing"),
                "expected_slides": inventory.get("expected_slide_count", 0),
                "reviewed_slides": inventory.get("available_slide_count", 0),
                "missing_slides": inventory.get("missing_slides", []),
                "paths": inventory.get("available_paths", {}),
                "review_note": visual_review.get("reason"),
            },
            "before": {
                "status": before.get("status"),
                "score": before.get("heuristic_total"),
                "failed_gates": [name for name, value in before_gates.items() if not value],
            },
            "after": {
                "status": current.get("status"),
                "score": current.get("heuristic_total"),
                "failed_gates": [name for name, value in current_gates.items() if not value],
                "repairs": current.get("repairs", []),
            },
            "gate_classifications": classifications,
            "changed_gates": changed,
            "visual_verification": {
                "status": visual_review.get("status"),
                "classification": visual_review.get("classification"),
                "reason": visual_review.get("reason"),
            },
            "decision": effective_decision,
            "mapping_repairs": mapping_repairs,
        })
    effective_passed = sum(item["decision"] == "allow_pass" for item in rows)
    return {
        "schema_version": "carousel-intelligence-calibration/v1",
        "seed_schema_version": seed.get("schema_version"),
        "source_report": seed.get("source_report"),
        "coverage": {
            **(seed.get("coverage") if isinstance(seed.get("coverage"), dict) else {}),
            "workspace_visual_inventory": after.get("workspace_visual_inventory", {}),
        },
        "baseline": {
            "source": str(baseline_path.relative_to(root)) if baseline_path.is_file() else None,
            "passed_count": baseline.get("passed_count"),
            "blocked_count": baseline.get("blocked_count"),
        },
        "after": {
            "passed_count": after.get("passed_count"),
            "blocked_count": after.get("blocked_count"),
            "causal_claims_allowed": False,
        },
        "effective": {
            "passed_count": effective_passed,
            "blocked_count": len(rows) - effective_passed,
            "basis": "complete local pixels plus the recorded visual-verification decision plus analyzer pass",
        },
        "gate_enablement": gate_policy,
        "classification_legend": {
            "evidence_mapping_gap": "The verified structured audit supports the gate, but the earlier analyzer vocabulary missed it.",
            "analyzer_false_negative": "The analyzer rejected evidence that is present in the structured sequence or reviewed pixels.",
            "true_creative_gap": "The available evidence does not satisfy the gate; keep the concept blocked.",
            "data_gap": "The workspace does not contain every expected local slide pixel, so visual confirmation is incomplete.",
            "preserved_pass": "The gate passed before and after calibration.",
        },
        "sequences": rows,
        "note": "This calibration separates verified audit observations from local workspace pixel availability; it makes no causal or reach claim. Gate activation is hash-bound to the creator-approved visual decisions and path map.",
    }


def write_calibration_report(root: Path, output_dir: Path | None = None) -> dict[str, Any]:
    root = root.expanduser().resolve()
    report = calibrate_seed(root)
    target = (output_dir or root / "output/reports/2026-09-19-full-carousel-audit").expanduser().resolve()
    target.mkdir(parents=True, exist_ok=True)
    (target / "carousel-intelligence-calibration.json").write_text(
        json.dumps(report, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    lines = [
        "# Carousel intelligence calibration",
        "",
        f"Verified sequences: **{len(report['sequences'])}**",
        f"Verified slides: **{sum(item['slide_count'] for item in report['sequences'])}**",
        f"Before: **{report['baseline'].get('passed_count')} passed / {report['baseline'].get('blocked_count')} blocked**",
        f"After: **{report['after']['passed_count']} passed / {report['after']['blocked_count']} blocked**",
        f"Review-ready effective decision: **{report['effective']['passed_count']} passed / {report['effective']['blocked_count']} blocked**",
        f"Workspace pixels reviewed: **{report['coverage']['workspace_visual_inventory'].get('available_slide_count', 0)} / {report['coverage']['workspace_visual_inventory'].get('expected_slide_count', 0)}**",
        f"Gate enabled: **{'YES' if report['gate_enablement']['enabled'] else 'NO'}** ({report['gate_enablement']['reason']})",
        "",
        "Pixel coverage is reported separately from the verified audit. Missing local files are data gaps, not inferred visual reviews.",
        "",
        "| Shortcode | Pixels | Before | Analyzer after | Effective decision | Visual classification | Visual reason |",
        "| --- | --- | --- | --- | --- | --- | --- |",
    ]
    for item in report["sequences"]:
        pixel = f"{item['pixel_evidence']['reviewed_slides']}/{item['pixel_evidence']['expected_slides']}"
        visual = item["visual_verification"]
        lines.append(
            f"| {item['shortcode']} | {pixel} | {item['before']['status']} ({item['before']['score']}) | {item['after']['status']} ({item['after']['score']}) | {item['decision']} | {visual['classification']} | {visual['reason']} |"
        )
    lines += [
        "",
        "## Evidence boundaries",
        "",
        "- Official platform signals, observed corpus patterns, and hypotheses remain separate.",
        "- Reels and single-image posts remain excluded from carousel calibration.",
        "- Causal claims remain disabled.",
        "- The 70-point floor and required dimension minimums remain unchanged.",
        "- Gate activation is fail-closed and hash-bound to the creator-approved visual decisions and path map.",
        "",
    ]
    (target / "carousel-intelligence-calibration.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def require_concept_gate(package_dir: Path) -> dict[str, Any]:
    report = _read_json(package_dir / "carousel-intelligence.json")
    if not isinstance(report, dict) or report.get("schema_version") != INTELLIGENCE_SCHEMA_VERSION:
        raise ValueError("Concept gate required: run carousel concept-check before proof preparation.")
    from pipeline.stages.carousel_sequence import package_sequence_inputs, sequence_enabled, sequence_input_fingerprint
    context, slides = package_sequence_inputs(package_dir)
    if sequence_enabled(context, slides) and report.get("input_sha256") != sequence_input_fingerprint(context, slides):
        raise ValueError("Concept gate is stale: recheck the current story and slide inputs.")
    if sequence_enabled(context, slides) and report.get("research_refs", []) != context.get("research_refs", []):
        raise ValueError("Concept gate research selection is stale: recheck the selected evidence.")
    gate = report.get("concept_gate")
    if not isinstance(gate, dict) or gate.get("status") != "passed":
        repairs = gate.get("repairs", []) if isinstance(gate, dict) else []
        detail = "; ".join(str(item) for item in repairs[:3])
        raise ValueError("Concept gate blocked; repair carousel-intelligence.json" + (f": {detail}" if detail else "."))
    return report
