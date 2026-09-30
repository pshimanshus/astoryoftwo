"""Immutable publication joins and dated outcome observations, outside packages.

These functions validate supplied research evidence; they do not publish posts,
inspect pixels, infer private DMs/retention, or promote production policy.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from PIL import Image

from pipeline.stages.a3_analyzer import AGE_BANDS, analyze_posts, canonical_post, collection_date
from pipeline.stages.carousel_generation_state import STATE_SCHEMA_VERSION, read_generation_state
from pipeline.stages.carousel_pixel_qa import manifest_fingerprint
from pipeline.stages.carousel_quality import build_final_audit

NATIVE_METRICS = {"Views": "views", "Viewers": "viewers", "Shares": "shares", "Saves": "saves",
                  "Follows": "follows", "Profile visits": "profile_visits", "reach": "reach", "sends": "sends"}
PUBLICATIONS = Path("corpus/publications")
INSIGHTS = Path("corpus/insights")
REPORTS = Path("output/reports/carousel-results")


def _read(path: Path) -> dict:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"Expected an object: {path}")
    return value


def _digest(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode()
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def _file_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def _code(shortcode: Any) -> str:
    if not isinstance(shortcode, str) or not re.fullmatch(r"[A-Za-z0-9_-]+", shortcode):
        raise ValueError("A valid shortcode is required")
    return shortcode


def _timestamp(value: Any, field: str) -> datetime:
    try:
        stamp = datetime.fromisoformat(value.replace("Z", "+00:00")) if isinstance(value, str) else None
    except ValueError:
        stamp = None
    if stamp is None or stamp.tzinfo is None or stamp.utcoffset() is None:
        raise ValueError(f"{field} requires an ISO timestamp with timezone")
    stamp = stamp.astimezone(timezone.utc)
    if stamp > datetime.now(timezone.utc):
        raise ValueError(f"{field} cannot be in the future")
    return stamp


def _iso(stamp: datetime) -> str:
    return stamp.isoformat().replace("+00:00", "Z")


def _text(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} requires evidence text")
    return value


def _immutable(path: Path, payload: dict) -> dict:
    """Exclusive creation: retries preserve bytes; conflicting records fail."""
    data = json.dumps(payload, indent=2, ensure_ascii=False, allow_nan=False) + "\n"
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open("x", encoding="utf-8") as handle:
            handle.write(data)
    except FileExistsError:
        if _read(path) != payload:
            raise ValueError(f"Record is immutable; conflicting observation: {path}") from None
    return payload


def _path_in(root: Path, raw: Any, allowed: Path, *, label: str) -> Path:
    if not isinstance(raw, str) or not raw or Path(raw).is_absolute():
        raise ValueError(f"{label} must be a relative path")
    candidate = root / raw
    if ".." in Path(raw).parts or any(part.is_symlink() for part in [candidate, *candidate.parents] if part != root.parent):
        raise ValueError(f"{label} cannot escape through a symlink or parent path")
    resolved = candidate.resolve(strict=True)
    if not resolved.is_relative_to(allowed.resolve()):
        raise ValueError(f"{label} must belong to the published archive or allowed package")
    if not resolved.is_file():
        raise ValueError(f"{label} must identify an image file")
    return resolved


def _correspondence(root: Path, package: Path, code: str, order: list[int], assets: dict[int, dict],
                    record: Any, published: datetime) -> dict:
    if not isinstance(record, dict) or record.get("status") not in {"unverified", "reviewed"}:
        raise ValueError("correspondence must explicitly be unverified or reviewed")
    if record["status"] == "unverified":
        if set(record) - {"status", "reason"}:
            raise ValueError("Unverified correspondence cannot contain certified bindings")
        return dict(record)
    reviewer = _text(record.get("reviewer"), "correspondence reviewer")
    reviewed = _timestamp(record.get("reviewed_at"), "correspondence reviewed_at")
    if reviewed < published:
        raise ValueError("Correspondence review predates publication")
    slides = record.get("slides")
    if not isinstance(slides, list) or len(slides) != len(order):
        raise ValueError("Reviewed correspondence requires evidence for every published slide")
    bound = []
    for position, (slide, number) in enumerate(zip(slides, order), 1):
        if not isinstance(slide, dict) or slide.get("published_position") != position or slide.get("package_slide") != number:
            raise ValueError("Correspondence positions must match confirmed slide order")
        path = _path_in(root, slide.get("published_image_path"), root / "corpus/media" / code, label="published archive image")
        with Image.open(path) as image:
            dimensions = list(image.size)
        digest = _file_hash(path)
        local_digest = assets[number]["sha256"]
        bound.append({"published_position": position, "package_slide": number,
                      "published_image_path": str(path.relative_to(root)), "published_sha256": digest,
                      "published_dimensions": dimensions, "final_sha256": local_digest,
                      "byte_identity": digest == local_digest, "evidence": _text(slide.get("evidence"), "correspondence evidence")})
    return {"status": "reviewed", "reviewer": reviewer, "reviewed_at": _iso(reviewed), "slides": bound}


def record_publication(root: Path, package_dir: Path, record: dict) -> dict:
    """Bind an explicitly confirmed publication to current finalized v3 assets."""
    root = Path(root).resolve()
    package = Path(package_dir)
    package = (package if package.is_absolute() else root / package).resolve(strict=True)
    if not package.is_relative_to(root) or not isinstance(record, dict):
        raise ValueError("Publication requires a package inside this workspace and a record object")
    code = _code(record.get("shortcode"))
    if record.get("confirmed") is not True:
        raise ValueError("Publication shortcode, URL, time and order must be confirmed")
    url = record.get("url")
    parsed = urlparse(url) if isinstance(url, str) else None
    if (not parsed or parsed.scheme != "https" or parsed.netloc not in {"instagram.com", "www.instagram.com"}
            or parsed.path.rstrip("/") != f"/p/{code}" or parsed.query or parsed.fragment):
        raise ValueError("Publication URL must match the confirmed Instagram post shortcode")
    published = _timestamp(record.get("published_at"), "published_at")
    state = read_generation_state(package)
    if state.get("schema_version") != STATE_SCHEMA_VERSION or state.get("status") != "publish_ready":
        raise ValueError("Publication linking requires a finalized publish_ready v3 package")
    manifest = _read(package / "final-images.json")
    stored = _read(package / "final-audit.json")
    fingerprint = manifest_fingerprint(manifest)
    if stored.get("status") != "PASS" or stored.get("issues") != [] or stored.get("manifest_sha256") != fingerprint:
        raise ValueError("Stored final audit or manifest binding is missing, failed or stale")
    audit = build_final_audit(package, write=False)
    if audit.get("status") != "PASS" or audit.get("issues"):
        raise ValueError("Current final audit failed: " + "; ".join(audit.get("issues", [])))
    output_format = record.get("output_format", "instagram_post")
    if output_format not in {"instagram_post", "instagram_square"} or output_format not in manifest.get("selected_formats", []):
        raise ValueError("Published carousel output_format must be a finalized post format")
    records = manifest.get("slides", [])
    numbers = [slide["slide"] for slide in records]
    order = record.get("slide_order")
    if (not isinstance(order, list) or not order or any(type(n) is not int for n in order)
            or len(order) != len(numbers) or set(order) != set(numbers)):
        raise ValueError("Confirmed slide_order must include every final slide exactly once")
    assets = {slide["slide"]: slide["native_outputs"][output_format] for slide in records}
    for binding in assets.values():
        path = _path_in(package, binding.get("path"), package, label="final package image")
        if _file_hash(path) != binding.get("sha256"):
            raise ValueError("Final image manifest bytes changed")
    context = _read(package / "creative-context.json")
    qa = _read(package / "visual-qa.json")
    correspondence = _correspondence(root, package, code, order, assets, record.get("correspondence"), published)
    payload = {"schema_version": "carousel-publication/v1", "shortcode": code, "url": url,
               "published_at": _iso(published), "confirmed": True, "post_type": "sidecar",
               "package_id": str(package.relative_to(root)), "final_manifest_sha256": fingerprint,
               "output_format": output_format, "slide_order": order, "final_manifest_order": numbers,
               "final_assets": [{"package_slide": n, **assets[n]} for n in order],
               "story_plan": context.get("story_plan", {}), "final_sequence_review": qa.get("sequence_review"),
               "correspondence": correspondence, "submitted_record": record}
    for field in ("caption_changes", "context_changes", "distribution_conditions", "creative_hypothesis", "next_hypothesis"):
        if field in record:
            payload[field] = record[field]
    return _immutable(root / PUBLICATIONS / f"{code}.json", payload)


def _publication(root: Path, code: str) -> dict:
    path = root / PUBLICATIONS / f"{_code(code)}.json"
    if not path.is_file():
        raise ValueError(f"Confirmed publication metadata is required for {code}")
    publication = _read(path)
    if publication.get("schema_version") != "carousel-publication/v1" or publication.get("shortcode") != code or publication.get("confirmed") is not True:
        raise ValueError("Invalid publication metadata")
    return publication


def _snapshot_payload(publication: dict, shortcode: str, record: dict) -> dict:
    """Derive the normalized fields exclusively from the retained submission."""
    if not isinstance(record, dict):
        raise ValueError("Snapshot requires an object")
    observed = _timestamp(record.get("observed_at"), "observed_at")
    published = _timestamp(publication["published_at"], "published_at")
    if observed < published:
        raise ValueError("Observation predates publication")
    source = record.get("source")
    if not isinstance(source, dict) or source.get("kind") not in {"native_insights", "export", "api"}:
        raise ValueError("Source kind must be native_insights, export or api")
    _text(source.get("reference"), "source reference")
    values = record.get("metrics")
    if not isinstance(values, dict) or not values:
        raise ValueError("Snapshot requires a native metrics object")
    if set(values) - set(NATIVE_METRICS):
        raise ValueError("Unsupported native metric labels: " + ", ".join(sorted(set(values) - set(NATIVE_METRICS))))
    metrics = {}
    for label in NATIVE_METRICS:
        value = values.get(label)
        try:
            valid = value is None or (not isinstance(value, bool) and isinstance(value, (int, float)) and math.isfinite(value) and value >= 0)
        except OverflowError:
            valid = False
        if not valid:
            raise ValueError(f"{label} must be an available nonnegative numeric count or null")
        metrics[label] = {"value": value, "availability": "observed" if value is not None else "unavailable", "native_label": label}
    payload = {"schema_version": "carousel-insights/v1", "shortcode": shortcode,
               "publication_sha256": _digest(publication), "published_at": publication["published_at"],
               "observed_at": _iso(observed), "post_age_days": (observed - published).total_seconds() / 86400,
               "source": source, "metrics": metrics, "submitted_record": record}
    for field in ("checkpoint", "next_hypothesis"):
        if field in record:
            payload[field] = record[field]
    return payload


def record_snapshot(root: Path, shortcode: str, record: dict) -> dict:
    """Save one actual native observation. No checkpoint time is synthesized."""
    root = Path(root).resolve()
    publication = _publication(root, shortcode)
    payload = _snapshot_payload(publication, shortcode, record)
    observed = _timestamp(payload["observed_at"], "observed_at")
    return _immutable(root / INSIGHTS / shortcode / (observed.strftime("%Y-%m-%dT%H%M%S.%fZ") + ".json"), payload)


def _observation(row: dict, source: dict, *, collected: date | None = None) -> dict:
    post = canonical_post(row)
    observed_raw = row.get("observed_at")
    observed = _timestamp(observed_raw, "observed_at") if observed_raw else None
    collected_raw = row.get("collected_on")
    observed_day = observed.date() if observed else date.fromisoformat(collected_raw) if collected_raw else collected
    if observed_day and observed_day > date.today():
        raise ValueError("Collection date cannot be in the future")
    age = None
    published = post.get("timestamp")
    if isinstance(published, str):
        try:
            dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
            if observed and dt.tzinfo is not None:
                age = (observed - dt).total_seconds() / 86400
            elif observed_day:
                age = (observed_day - dt.date()).days
        except ValueError:
            pass
    post.update(observed_at=_iso(observed) if observed else None,
                collected_on=observed_day.isoformat() if observed_day else None,
                observation_precision="timestamp" if observed else "day" if observed_day else "unknown",
                age_days=age, post_age_days=age, source=source)
    post["reported_age_days"] = row.get("age_days") if age is None else None
    post["metric_provenance"] = {metric: source for metric, value in post["engagement"].items() if value is not None}
    post["metrics"] = {label: post["engagement"][metric] for label, metric in NATIVE_METRICS.items()}
    post["age_band"] = next((f"{lo}-{hi}" for lo, hi in AGE_BANDS if age is not None and lo <= age < hi + 1), None)
    return post


def load_metric_observations(root: Path) -> list[dict]:
    """Shared native/normalized adapter; one row per post and dated snapshot.

    Dated raw exports win over their normalized counterpart. Embedded observation
    timestamps are retained. Same-identity conflicting snapshots are excluded,
    never averaged or selected by file order. Unknown observation dates cannot
    enter age-aware cohorts.
    """
    root = Path(root).resolve()
    files = {}
    for folder, suffix in (("posts", "posts"), ("raw", "raw")):
        for path in sorted((root / "corpus" / folder).glob(f"*-{suffix}.json")):
            collected = collection_date(path)
            if collected:
                files[collected] = path
    rows = []
    sources = [(collected, path) for collected, path in sorted(files.items())]
    # Legacy direct native exports are readable but their reported age is not
    # collection provenance. Avoid recursive competitor/media/document scans.
    sources += [(None, path) for path in sorted((root / "corpus").glob("*.json"))]
    for collected, path in sources:
        raw = path.read_bytes()
        payload = json.loads(raw)
        if isinstance(payload, dict) and isinstance(payload.get("posts"), list):
            payload = payload["posts"]
        if not isinstance(payload, list):
            raise ValueError(f"Expected a post list: {path}")
        source = {"path": str(path.relative_to(root)), "sha256": "sha256:" + hashlib.sha256(raw).hexdigest(),
                  "date_basis": "embedded observed_at/collected_on when supplied; otherwise dated snapshot filename"}
        for row in payload:
            if isinstance(row, dict):
                rows.append(_observation(row, source, collected=collected))
    for path in sorted((root / INSIGHTS).glob("*/*.json")):
        raw = _read(path)
        if raw.get("schema_version") != "carousel-insights/v1":
            raise ValueError(f"Invalid Insights snapshot: {path}")
        code = _code(raw.get("shortcode"))
        publication = _publication(root, code)
        if raw.get("publication_sha256") != _digest(publication) or raw.get("published_at") != publication["published_at"]:
            raise ValueError(f"Insights publication binding changed: {path}")
        if raw != _snapshot_payload(publication, code, raw.get("submitted_record")):
            raise ValueError(f"Insights snapshot disagrees with its retained submission: {path}")
        row = {"id": code, "shortcode": code, "type": "Sidecar", "timestamp": publication["published_at"],
               "observed_at": raw["observed_at"], "ownerUsername": "a.storyof.two", "slide_count": len(publication["slide_order"])}
        for label, metric in raw["metrics"].items():
            if label in NATIVE_METRICS and metric.get("availability") == "observed":
                row[label] = metric["value"]
        rows.append(_observation(row, {**raw["source"], "path": str(path.relative_to(root)), "sha256": _file_hash(path)}))
    unique, conflict = {}, set()
    for row in rows:
        code = row.get("shortcode") or row.get("id")
        stamp = row["observed_at"] or row["collected_on"]
        if not code:
            continue
        key = (str(code), row["observation_precision"], stamp or row["source"]["path"])
        if key in conflict:
            continue
        if key in unique:
            prior = unique[key]
            mismatched = prior["timestamp"] != row["timestamp"] or prior["post_type"] != row["post_type"]
            overlap = set(prior["engagement"]) & set(row["engagement"])
            mismatched = mismatched or any(prior["engagement"][m] is not None and row["engagement"][m] is not None
                                           and prior["engagement"][m] != row["engagement"][m] for m in overlap)
            if mismatched:
                conflict.add(key)
                unique.pop(key)
            else:
                # Only complementary observations at the exact same timestamp
                # may be joined. Date-only exports cannot certify simultaneity.
                if row["observation_precision"] == "day" and prior["engagement"] != row["engagement"]:
                    conflict.add(key)
                    unique.pop(key)
                    continue
                native = str(row["source"]["path"]).startswith(str(INSIGHTS) + "/")
                base, extra = (row, prior) if native else (prior, row)
                for metric, value in extra["engagement"].items():
                    if base["engagement"].get(metric) is None and value is not None:
                        base["engagement"][metric] = value
                        base["metric_status"][metric] = "observed"
                        base["metric_provenance"][metric] = extra["metric_provenance"][metric]
                base["metrics"] = {label: base["engagement"][metric] for label, metric in NATIVE_METRICS.items()}
                base.setdefault("duplicate_sources", []).extend([extra["source"], *extra.get("duplicate_sources", [])])
                unique[key] = base
        else:
            unique[key] = row
    return sorted(unique.values(), key=lambda row: (row["observed_at"] or row["collected_on"] or "", str(row.get("shortcode") or row["id"])))


def _rates(row: dict) -> dict:
    rates = {}
    for metric in ("shares", "saves", "sends"):
        numerator, reach = row["engagement"][metric], row["engagement"]["reach"]
        value = numerator / reach if numerator is not None and reach is not None and reach > 0 else None
        if value is not None and not math.isfinite(value):
            value = None
        label = next(label for label, name in NATIVE_METRICS.items() if name == metric)
        rates[f"{metric}_per_reach"] = {"value": value, "numerator": {"label": label, "value": numerator},
                                       "denominator": {"label": "reach", "value": reach},
                                       "source": {"numerator": row.get("metric_provenance", {}).get(metric, row["source"]),
                                                  "denominator": row.get("metric_provenance", {}).get("reach", row["source"])},
                                       "observed_at": row["observed_at"],
                                       "availability": "observed" if value is not None else "unavailable"}
    return rates


def _current_correspondence(root: Path, publication: dict) -> dict:
    correspondence = publication["correspondence"]
    if correspondence["status"] != "reviewed":
        return correspondence
    stale = []
    for slide in correspondence["slides"]:
        try:
            path = _path_in(root, slide["published_image_path"], root / "corpus/media" / publication["shortcode"], label="published archive image")
            if _file_hash(path) != slide["published_sha256"]:
                stale.append(slide["published_position"])
        except (OSError, ValueError):
            stale.append(slide["published_position"])
    return {**correspondence, "status": "stale" if stale else "reviewed", "stale_positions": stale}


def review_results(root: Path, shortcode: str) -> dict:
    """Write a descriptive, source-bound review; editorial conclusions stay open."""
    root = Path(root).resolve()
    publication = _publication(root, shortcode)
    rows = load_metric_observations(root)
    observations = [row for row in rows if row.get("shortcode") == shortcode]
    # Only linked native snapshots establish this package's result timeline.
    linked = [row for row in observations if str(row["source"].get("path", "")).startswith(str(INSIGHTS / shortcode) + "/")]
    latest = max(linked, key=lambda row: row["observed_at"]) if linked else None
    comparisons, comparison_posts = [], []
    if latest and latest["age_band"]:
        candidates = {}
        for row in rows:
            code = row.get("shortcode") or row.get("id")
            if row["post_type"] != "sidecar" or row["age_band"] != latest["age_band"] or code == shortcode:
                continue
            # Keep one observation per post, nearest the target's actual age.
            rank = (abs(row["age_days"] - latest["age_days"]), row["observed_at"] or row["collected_on"], row["source"]["path"])
            if code not in candidates or rank < candidates[code][0]:
                candidates[code] = (rank, row)
        selected = [latest] + [value[1] for value in candidates.values()]
        summary = analyze_posts(selected, today=date.today())
        comparisons = [group for group in summary["cohorts"] if group["comparisons"]]
        comparison_posts = [{key: row.get(key) for key in ("id", "shortcode", "post_type", "observed_at", "collected_on", "age_days", "observation_precision", "source", "engagement")} for row in summary["posts"]]
    latest_path = root / latest["source"]["path"] if latest else None
    next_hypothesis = (_read(latest_path).get("next_hypothesis") if latest_path else None) or publication.get("next_hypothesis")
    limits = ["Counts describe cumulative distribution and response at the recorded post age; they do not identify a creative cause.",
              "Shares do not establish private DM counts; sends are retained only when explicitly observed.",
              "No snapshot establishes per-slide abandonment, dwell or completion; swipe judgments remain editorial hypotheses.",
              "Different collection periods, paid distribution, collaborations and caption/context changes can affect comparisons.",
              "Low distribution alone does not establish creative failure; missing observations remain unavailable."]
    correspondence = _current_correspondence(root, publication)
    if publication.get("slide_order") != publication.get("final_manifest_order"):
        limits.append("Published order differs from final-manifest order; the package's final sequence judgment does not certify the published sequence.")
    if correspondence["status"] != "reviewed":
        limits.append("Published-image correspondence is unverified or stale; local final art is not certified as the published imagery.")
    if not comparisons:
        limits.append("No eligible same-format cohort with A3's five-observation and 80% coverage safeguards; results remain descriptive.")
    review = {"schema_version": "carousel-results/v1", "shortcode": shortcode, "url": publication["url"],
              "publication_source": str(PUBLICATIONS / f"{shortcode}.json"), "publication_sha256": _digest(publication),
              "package_id": publication["package_id"], "final_manifest_sha256": publication["final_manifest_sha256"],
              "published_at": publication["published_at"], "story_plan": publication["story_plan"],
              "intended_hypothesis": publication.get("creative_hypothesis"),
              "final_work_evidence": {"sequence_review": publication.get("final_sequence_review"), "published_correspondence": correspondence},
              "publication_context": {key: publication.get(key) for key in ("caption_changes", "context_changes", "distribution_conditions")},
              "outcome_status": "observed" if latest else "unavailable", "observation_count": len(linked),
              "latest_observation": {**latest, "rates": _rates(latest)} if latest else None,
              "observation_sources": [row["source"] for row in linked], "comparisons": comparisons,
              "comparison_posts": comparison_posts, "slide_order": publication["slide_order"],
              "final_manifest_order": publication.get("final_manifest_order"),
              "mechanism_assessment": {"status": "ambiguous", "reason": "Dated counts and editorial evidence do not by themselves confirm or contradict the proposed mechanism."},
              "next_hypothesis": next_hypothesis,
              "unmeasured": ["private_dm_count", "per_slide_abandonment", "dwell", "completion"], "limits": limits,
              "policy_updated": False}
    path = root / REPORTS / f"{shortcode}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(review, indent=2, ensure_ascii=False, allow_nan=False) + "\n", encoding="utf-8")
    path.with_suffix(".md").write_text(_markdown(review), encoding="utf-8")
    return review


def _markdown(review: dict) -> str:
    from pipeline.stages.a3_analyzer import cell
    lines = [f"# Carousel result: {review['shortcode']}", "", f"[Published post]({review['url']}) · {review['published_at']}", "",
             "## Intended story and final work", "", json.dumps(review["story_plan"], ensure_ascii=False), "",
             f"Creative hypothesis: {cell(review.get('intended_hypothesis') or 'not supplied')}",
             f"Published-image correspondence: {review['final_work_evidence']['published_correspondence']['status']}.",
             "The JSON retains the final sequence review, confirmed slide order binding, and publication changes.", "", "## Available outcome", ""]
    latest = review["latest_observation"]
    if latest:
        lines += [f"Observed {latest['observed_at']}; post age {latest['age_days']:.3f} days.",
                  f"Source: {cell(latest['source']['path'])}", "", "| Native metric | Value |", "| --- | ---: |"]
        lines += [f"| {label} | {value if value is not None else 'unavailable'} |" for label, value in latest["metrics"].items()]
        for name, rate in latest["rates"].items():
            lines.append(f"{name}: {rate['value'] if rate['value'] is not None else 'unavailable'}; denominator reach={rate['denominator']['value'] if rate['denominator']['value'] is not None else 'unavailable'} at the same observation.")
    else:
        lines.append("No dated linked Insights observation is available. This is not observed performance.")
    lines += ["", "## Same-format comparisons", ""]
    for group in review["comparisons"]:
        lines.append(f"{group['format']}, {group['age_band']} days, n={group['n']}; primary metric {group['primary_metric']}. Sources and differences are retained per post in the JSON.")
    if not review["comparisons"]:
        lines.append("No eligible comparison cohort.")
    lines += ["", "## Limits", "", *[f"- {limit}" for limit in review["limits"]], "", "## Next hypothesis", "",
              str(review["next_hypothesis"] or "Not supplied. Review the evidence before choosing a focused next test."), "",
              "Mechanism assessment: ambiguous. This review does not update production rules or policy.", ""]
    return "\n".join(lines)
