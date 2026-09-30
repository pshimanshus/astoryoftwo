"""A4: checked, receipt-backed compilation of one A3 analysis into the wiki."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from dataclasses import dataclass
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any

from pipeline.stages.a2_parser import latest_file
from pipeline.stages.source_integrity import (
    atomic_write_text,
    relative_to_root,
    source_receipt_path,
    verify_provenance,
    verify_source_receipt,
    workspace_lock,
)
from pipeline.stages.wiki_health import replace_or_insert_metadata, wiki_pages


PROVENANCE_RE = re.compile(r"<!--\s*a-story-source-provenance:\s*(\{.*?\})\s*-->")


@dataclass(frozen=True)
class CompilePlan:
    """A fully rendered A4 transaction, inspectable before it mutates the wiki."""

    root: Path
    analysis_path: Path
    analysis_json_path: Path
    provenance: dict[str, Any]
    insight_path: Path
    index_path: Path
    receipt_path: Path
    journal_path: Path
    insight_text: str
    index_text: str
    receipt: dict[str, Any]


def _file_hash(path: Path) -> str | None:
    return hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None


def _analysis_summary(analysis_path: Path) -> tuple[Path, dict[str, Any]]:
    json_path = analysis_path.with_suffix(".json")
    if not json_path.is_file():
        raise ValueError(f"A4 requires the A3 JSON companion: {json_path}")
    value = json.loads(json_path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError("A3 JSON companion must be an object")
    return json_path, value


def _verified_source_receipt(root: Path, embedded: dict[str, Any]) -> tuple[Path, Path, dict[str, Any]]:
    normalized = embedded.get("normalized_path")
    if not isinstance(normalized, str):
        raise ValueError("A4 A2 source receipt does not name its normalized artifact")
    normalized_path = (root / normalized).resolve()
    if relative_to_root(normalized_path, root) != normalized or not normalized_path.is_file():
        raise ValueError("A4 normalized source artifact is missing or outside the workspace")
    current, errors = verify_source_receipt(root, normalized_path)
    if errors:
        raise ValueError(f"A4 refuses invalid A2 source receipt: {'; '.join(errors)}")
    if current != embedded:
        raise ValueError("A4 embedded A2 source receipt is stale")
    return normalized_path, source_receipt_path(normalized_path), current


def _source_bound_claims(
    summary: dict[str, Any], *, source_path: str, source_hash: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    claims: list[dict[str, Any]] = []
    by_feature: dict[str, set[int]] = {}
    for cohort_index, cohort in enumerate(summary.get("cohorts", [])):
        if not isinstance(cohort, dict):
            continue
        for pattern_index, pattern in enumerate(cohort.get("caption_patterns", [])):
            if not isinstance(pattern, dict) or not pattern.get("feature"):
                continue
            difference = float(pattern.get("difference", 0.0))
            feature = str(pattern["feature"])
            direction = 1 if difference > 0 else -1 if difference < 0 else 0
            by_feature.setdefault(feature, set()).add(direction)
            claims.append({
                "claim_id": f"cohort-{cohort_index}-caption-{pattern_index}",
                "claim": f"Within {cohort.get('format')} posts aged {cohort.get('age_band')} days, {feature} differed between the higher and lower observed tails.",
                "direction": "higher" if direction > 0 else "lower" if direction < 0 else "no_difference",
                "effect": difference,
                "source_path": source_path,
                "source_sha256": source_hash,
                "json_pointer": f"/cohorts/{cohort_index}/caption_patterns/{pattern_index}",
                "authority": "reviewed_observation",
            })
    conflicts = [
        {
            "feature": feature,
            "status": "preserved_conflict",
            "directions": sorted("higher" if item > 0 else "lower" if item < 0 else "no_difference" for item in directions),
        }
        for feature, directions in sorted(by_feature.items())
        if len(directions - {0}) > 1
    ]
    return claims, conflicts


def extract_report_provenance(analysis_path: Path) -> dict[str, Any]:
    text = analysis_path.read_text(encoding="utf-8")
    match = PROVENANCE_RE.search(text)
    if not match:
        raise ValueError(f"A4 refuses unbound analysis without A1 provenance: {analysis_path}")
    try:
        value = json.loads(match.group(1))
    except json.JSONDecodeError as exc:
        raise ValueError(f"A4 found malformed source provenance in {analysis_path}") from exc
    if not isinstance(value, dict):
        raise ValueError("A4 source provenance must be an object")
    return value


def checked_provenance(root: Path, analysis_path: Path) -> dict[str, Any]:
    provenance = extract_report_provenance(analysis_path)
    errors = verify_provenance(root, provenance)
    if errors:
        raise ValueError(f"A4 refuses analysis with invalid source provenance: {'; '.join(errors)}")
    return provenance


def build_latest_analysis_page(
    analysis_path: Path,
    provenance: dict[str, Any],
    today: date,
    claims: list[dict[str, Any]] | None = None,
    conflicts: list[dict[str, Any]] | None = None,
) -> str:
    lines = [
            "# Latest Corpus Analysis",
            "",
            f"last_updated: {today}",
            "confidence: 0.72",
            "sources:",
            f"- {analysis_path.as_posix()}",
            f"- {provenance['raw_path']}",
            "",
            "## Source Provenance",
            "",
            f"- status: {provenance['status']}",
            f"- snapshot_id: {provenance['snapshot_id']}",
            f"- raw_sha256: {provenance['raw_sha256']}",
            f"- raw_path: {provenance['raw_path']}",
            f"- normalized_posts_path: {provenance.get('normalized_posts_path', '')}",
            "",
            "## Summary",
            "",
            "This page is a checked compilation of the latest A3 corpus analysis. The source hash above must resolve through `corpus/integrity/raw-snapshots.json` before A4 can write it.",
            "",
            "## Artifact",
            "",
            f"- {analysis_path.as_posix()}",
            "",
        ]
    claims = claims or []
    conflicts = conflicts or []
    lines += ["## Source-bound claims", ""]
    if not claims:
        lines.append("No eligible comparative claim was produced; the absence is preserved.")
    for claim in claims:
        lines.append(
            f"- `{claim['claim_id']}` {claim['claim']} Direction: {claim['direction']}; "
            f"source `{claim['source_path']}#{claim['json_pointer']}`; SHA-256 `{claim['source_sha256']}`."
        )
    lines += ["", "## Conflicts", ""]
    if not conflicts:
        lines.append("No cross-cohort directional conflict was detected in this analysis.")
    for conflict in conflicts:
        lines.append(f"- {conflict['feature']}: {', '.join(conflict['directions'])} ({conflict['status']}).")
    lines.append("")
    return "\n".join(lines)


def index_with_compiled_analysis(index_path: Path, insight_path: Path, root: Path, today: date) -> str:
    text = index_path.read_text(encoding="utf-8") if index_path.exists() else "# Wiki Index\n\n"
    existing = {path.resolve() for path in wiki_pages(root)}
    existing.add(insight_path.resolve())
    text = replace_or_insert_metadata(text, "last_updated", str(today))
    text = replace_or_insert_metadata(text, "total_pages", str(len(existing)))
    section = "## Compiled Analysis"
    block = "\n".join(
        [section, "", "| Analysis | Updated |", "| --- | --- |", f"| [Latest Corpus Analysis](insights/latest-analysis.md) | {today} |", ""]
    )
    start = text.find(section)
    if start == -1:
        return text.rstrip() + "\n\n" + block
    end = text.find("\n## ", start + len(section))
    if end == -1:
        return text[:start].rstrip() + "\n\n" + block
    return text[:start].rstrip() + "\n\n" + block + text[end:]


def build_compile_plan(root: Path, analysis_path: Path | None = None, today: date | None = None) -> CompilePlan:
    root = root.resolve()
    today = today or date.today()
    analysis_path = (analysis_path or latest_file(root / "output" / "reports", "*-analysis.md")).resolve()
    provenance = checked_provenance(root, analysis_path)
    analysis_json_path, summary = _analysis_summary(analysis_path)
    receipt = summary.get("source", {}).get("receipt") if isinstance(summary.get("source"), dict) else None
    if not isinstance(receipt, dict) or receipt.get("status") != "verified":
        raise ValueError("A4 production compilation requires a verified A2 source receipt")
    if receipt.get("source_provenance") != provenance:
        raise ValueError("A4 A3 JSON receipt does not match the Markdown provenance")
    _normalized_path, a2_receipt_path, verified_receipt = _verified_source_receipt(root, receipt)
    analysis_json_relative = analysis_json_path.relative_to(root).as_posix()
    analysis_json_sha256 = _file_hash(analysis_json_path)
    assert analysis_json_sha256 is not None
    claims, conflicts = _source_bound_claims(
        summary,
        source_path=analysis_json_relative,
        source_hash=analysis_json_sha256,
    )
    insight_path = root / "wiki" / "insights" / "latest-analysis.md"
    index_path = root / "wiki" / "index.md"
    digest = hashlib.sha256(analysis_path.read_bytes()).hexdigest()
    receipt_path = root / "output" / "receipts" / "a4-wiki" / f"{analysis_path.stem}.json"
    insight_text = build_latest_analysis_page(
        analysis_path.relative_to(root), provenance, today, claims=claims, conflicts=conflicts
    )
    index_text = index_with_compiled_analysis(index_path, insight_path, root, today)
    output_hashes = {
        insight_path.relative_to(root).as_posix(): hashlib.sha256(insight_text.encode("utf-8")).hexdigest(),
        index_path.relative_to(root).as_posix(): hashlib.sha256(index_text.encode("utf-8")).hexdigest(),
    }
    compile_receipt = {
        "schema_version": "a4-compile-receipt/v2",
        "stage": "a4_wiki",
        "status": "applied",
        "analysis_path": analysis_path.relative_to(root).as_posix(),
        "analysis_sha256": digest,
        "analysis_json_path": analysis_json_relative,
        "analysis_json_sha256": analysis_json_sha256,
        "source_receipt_path": a2_receipt_path.relative_to(root).as_posix(),
        "source_receipt_sha256": _file_hash(a2_receipt_path),
        "normalized_sha256": verified_receipt["normalized_sha256"],
        "source_provenance": provenance,
        "targets": [insight_path.relative_to(root).as_posix(), index_path.relative_to(root).as_posix()],
        "before_hashes": {
            insight_path.relative_to(root).as_posix(): _file_hash(insight_path),
            index_path.relative_to(root).as_posix(): _file_hash(index_path),
        },
        "output_hashes": output_hashes,
        "affected_pages": [insight_path.relative_to(root).as_posix()],
        "claim_ids": [claim["claim_id"] for claim in claims],
        "conflicts": conflicts,
        "compiled_on": str(today),
    }
    return CompilePlan(
        root=root,
        analysis_path=analysis_path,
        analysis_json_path=analysis_json_path,
        provenance=provenance,
        insight_path=insight_path,
        index_path=index_path,
        receipt_path=receipt_path,
        journal_path=root / "output" / "receipts" / "a4-wiki" / ".pending.json",
        insight_text=insight_text,
        index_text=index_text,
        receipt=compile_receipt,
    )


# Compatibility for callers written during the initial migration.
plan_compile = build_compile_plan


def apply_compile_plan(plan: CompilePlan) -> Path:
    """Apply a preflighted plan under one lock; re-check inputs before every write."""
    with workspace_lock(plan.root, "a4-wiki"):
        current = checked_provenance(plan.root, plan.analysis_path)
        if current != plan.provenance:
            raise ValueError("A4 source provenance changed after compile plan creation")
        if hashlib.sha256(plan.analysis_path.read_bytes()).hexdigest() != plan.receipt["analysis_sha256"]:
            raise ValueError("A4 analysis changed after compile plan creation")
        if _file_hash(plan.analysis_json_path) != plan.receipt["analysis_json_sha256"]:
            raise ValueError("A4 analysis JSON changed after compile plan creation")
        source = json.loads(plan.analysis_json_path.read_text(encoding="utf-8")).get("source", {})
        embedded = source.get("receipt") if isinstance(source, dict) else None
        if not isinstance(embedded, dict):
            raise ValueError("A4 analysis JSON lost its A2 source receipt")
        normalized_path, current_receipt_path, current_receipt = _verified_source_receipt(plan.root, embedded)
        if _file_hash(current_receipt_path) != plan.receipt["source_receipt_sha256"]:
            raise ValueError("A4 source receipt changed after compile plan creation")
        if _file_hash(normalized_path) != plan.receipt["normalized_sha256"]:
            raise ValueError("A4 normalized source changed after compile plan creation")
        if current_receipt != embedded:
            raise ValueError("A4 embedded source receipt changed after compile plan creation")
        desired = {
            plan.insight_path: plan.insight_text,
            plan.index_path: plan.index_text,
        }
        for target, content in desired.items():
            relative = target.relative_to(plan.root).as_posix()
            current_hash = _file_hash(target)
            expected_before = plan.receipt["before_hashes"][relative]
            expected_after = plan.receipt["output_hashes"][relative]
            if current_hash not in {expected_before, expected_after}:
                raise ValueError(f"A4 target changed after compile plan creation: {relative}")
            if hashlib.sha256(content.encode("utf-8")).hexdigest() != expected_after:
                raise ValueError(f"A4 rendered output changed after compile plan creation: {relative}")
        journal = {
            "schema_version": "a4-compile-journal/v1",
            "status": "pending",
            "receipt_path": plan.receipt_path.relative_to(plan.root).as_posix(),
            "analysis_sha256": plan.receipt["analysis_sha256"],
            "output_hashes": plan.receipt["output_hashes"],
        }
        atomic_write_text(plan.journal_path, json.dumps(journal, indent=2, sort_keys=True) + "\n")
        atomic_write_text(plan.insight_path, plan.insight_text)
        atomic_write_text(plan.index_path, plan.index_text)
        applied_receipt = dict(plan.receipt)
        applied_receipt["applied_at"] = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        atomic_write_text(plan.receipt_path, json.dumps(applied_receipt, indent=2, sort_keys=True) + "\n")
        plan.journal_path.unlink(missing_ok=True)
    return plan.insight_path


def check_compile(root: Path, analysis_path: Path | None = None, today: date | None = None) -> list[str]:
    """Return drift and interrupted-transaction errors without mutating the workspace."""
    root = root.resolve()
    errors: list[str] = []
    journal = root / "output" / "receipts" / "a4-wiki" / ".pending.json"
    if journal.exists():
        errors.append(f"interrupted compile journal exists: {journal.relative_to(root).as_posix()}")
    if analysis_path is None:
        applied: list[tuple[float, int, str, Path]] = []
        receipt_dir = root / "output" / "receipts" / "a4-wiki"
        for receipt_path in receipt_dir.glob("*.json") if receipt_dir.exists() else []:
            try:
                receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
                raw_applied = receipt.get("applied_at")
                applied_at = datetime.fromisoformat(
                    str(raw_applied).replace("Z", "+00:00")
                ).timestamp() if raw_applied else 0.0
                named_analysis = (root / str(receipt["analysis_path"])).resolve()
                if named_analysis.is_file():
                    applied.append((applied_at, receipt_path.stat().st_mtime_ns, receipt_path.name, named_analysis))
            except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError):
                continue
        if applied:
            analysis_path = max(applied)[3]
        else:
            try:
                analysis_path = latest_file(root / "output" / "reports", "*-analysis.md")
            except FileNotFoundError:
                analysis_path = None
    if today is None and analysis_path is not None:
        candidate = root / "output" / "receipts" / "a4-wiki" / f"{Path(analysis_path).stem}.json"
        if candidate.is_file():
            try:
                prior_receipt = json.loads(candidate.read_text(encoding="utf-8"))
                today = date.fromisoformat(str(prior_receipt["compiled_on"]))
            except (OSError, KeyError, ValueError, json.JSONDecodeError):
                pass
    try:
        plan = build_compile_plan(root, analysis_path=analysis_path, today=today)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        return [*errors, str(exc)]
    if not plan.receipt_path.is_file():
        errors.append("compile receipt is missing")
    else:
        try:
            receipt = json.loads(plan.receipt_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"compile receipt is unreadable: {exc}")
        else:
            for key in (
                "analysis_sha256",
                "analysis_json_sha256",
                "source_receipt_sha256",
                "normalized_sha256",
                "output_hashes",
                "source_provenance",
            ):
                if receipt.get(key) != plan.receipt.get(key):
                    errors.append(f"compile receipt {key} is stale")
    for target in (plan.insight_path, plan.index_path):
        relative = target.relative_to(root).as_posix()
        if _file_hash(target) != plan.receipt["output_hashes"][relative]:
            errors.append(f"compiled output is stale: {relative}")
    return errors


def run(root: Path | None = None, analysis_path: Path | None = None, today: date | None = None) -> Path:
    return apply_compile_plan(build_compile_plan(root or Path.cwd(), analysis_path=analysis_path, today=today))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="A4 compile a provenance-checked latest analysis into wiki.")
    parser.add_argument("--analysis-path", type=Path)
    parser.add_argument("--workspace-root", type=Path, default=Path.cwd())
    parser.add_argument("--plan", action="store_true", help="Validate and print the planned receipt without writing.")
    parser.add_argument("--check", action="store_true", help="Fail when compiled outputs or receipts are stale; never write.")
    args = parser.parse_args(argv)
    if args.check:
        errors = check_compile(args.workspace_root, analysis_path=args.analysis_path)
        if errors:
            for error in errors:
                print(f"FAIL: {error}")
            return 1
        print("A4 compile check: PASS")
        return 0
    plan = build_compile_plan(root=args.workspace_root, analysis_path=args.analysis_path)
    if args.plan:
        print(json.dumps(plan.receipt, indent=2, sort_keys=True))
        return 0
    print(apply_compile_plan(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
