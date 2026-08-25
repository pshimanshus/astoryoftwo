#!/usr/bin/env python3
"""Benchmark the synthetic carousel CLI lifecycle without claiming visual QA."""

from __future__ import annotations

import argparse
import json
import math
import resource
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import Any

from PIL import Image


ROOT = Path(__file__).resolve().parents[1]
CAROUSEL = ROOT / "scripts/carousel.py"
BUDGETS = {
    "create_and_proof_p95_seconds": 3.0,
    "full_lifecycle_p95_seconds": 10.0,
    "peak_rss_mib": 256.0,
    "non_reference_package_mib": 1.0,
}


def _write_png(path: Path, size: tuple[int, int], color: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color).save(path, optimize=True)
    return path


def _brief(path: Path) -> Path:
    payload = {
        "slides": [
            {
                "copy": f"Locked line {number}.",
                "physical_action": action,
                "relationship_state": state,
            }
            for number, action, state in (
                (1, "Aachu places one brass key in Zuv's open palm.", "certain together"),
                (2, "They point from one moving box toward different doors.", "uncertain direction"),
                (3, "They pull one folded map gently toward opposite sides.", "connected disagreement"),
                (4, "They rotate the map and trace one route together.", "committed learning"),
            )
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _call(*args: str) -> dict[str, Any]:
    result = subprocess.run(
        [sys.executable, str(CAROUSEL), *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stdout + result.stderr)
    payload = json.loads(result.stdout)
    if payload.get("schema_version") != "carousel-cli/v1":
        raise RuntimeError("carousel CLI returned an unversioned response")
    return payload


def _observations(package: Path, selected: list[int]) -> dict[str, Any]:
    raw_slides = json.loads((package / "slides.json").read_text(encoding="utf-8"))
    slides = raw_slides["slides"] if isinstance(raw_slides, dict) else raw_slides
    copies = {int(record["slide"]): str(record["copy"]) for record in slides}
    prompt_pack = json.loads((package / "prompt-pack.json").read_text(encoding="utf-8"))
    refs = [str(value) for value in prompt_pack["identity_reference_images"]]
    style_refs = [str(value) for value in prompt_pack["style_reference_images"]]
    if len(refs) != 4:
        raise RuntimeError("synthetic fixture expected four identity-role references")
    if len(style_refs) != 1:
        raise RuntimeError("synthetic fixture expected one style reference")
    records: list[dict[str, Any]] = []
    for slide in selected:
        copy = copies[slide]
        records.append(
            {
                "slide": slide,
                "reviews": {
                    "instagram_post": {
                        "checks": {
                            "physical_action": {
                                "status": "PASS",
                                "evidence": "The intended shared-object hand action is visible.",
                            },
                            "relationship_state": {
                                "status": "PASS",
                                "evidence": "Their gaze and distance show the intended state.",
                            },
                            "entity_spatial_integrity": {
                                "status": "PASS",
                                "evidence": "Two continuous people and four owned hands are visible.",
                            },
                            "identity_wardrobe_accessories": {
                                "status": "PASS",
                                "evidence": "Both people match the named face, body, and clothing references.",
                                "references": {
                                    "aachu": [refs[0]],
                                    "zuv": [refs[1]],
                                    "together": refs[2:],
                                },
                            },
                            "text_brandmark_style_dimensions": {
                                "status": "PASS",
                                "evidence": "Exact copy and top-right brandmark are visible at native size.",
                                "expected_text": copy,
                                "observed_text": copy,
                                "observed_brandmark": "@a.storyof.two",
                                "style_references": style_refs,
                            },
                        }
                    }
                },
            }
        )
    return {
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": selected,
        "slides": records,
    }


def _write_json(path: Path, payload: object) -> Path:
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _non_reference_bytes(package: Path) -> int:
    image_suffixes = {".png", ".jpg", ".jpeg", ".webp"}
    total = 0
    for path in package.rglob("*"):
        if not path.is_file() or path.suffix.lower() in image_suffixes:
            continue
        relative = path.relative_to(package)
        if "references" in relative.parts:
            continue
        total += path.stat().st_size
    return total


def _run_once(root: Path) -> dict[str, float]:
    aachu = _write_png(root / "identity/aachu/a.png", (16, 16), "salmon")
    zuv = _write_png(root / "identity/zuv/z.png", (16, 16), "skyblue")
    together_face = _write_png(root / "identity/together/face.png", (16, 16), "tan")
    together_body = _write_png(root / "identity/together/body.png", (16, 16), "plum")
    style = _write_png(root / "style/watercolor.png", (16, 16), "ivory")
    brief = _brief(root / "brief.json")

    lifecycle_start = time.perf_counter()
    create_start = time.perf_counter()
    created = _call(
        "create",
        "--story",
        "Synthetic orchestration benchmark.",
        "--creative-brief",
        str(brief),
        "--identity-image",
        str(aachu),
        "--identity-image",
        str(zuv),
        "--identity-image",
        str(together_face),
        "--identity-image",
        str(together_body),
        "--style-reference",
        str(style),
        "--prepare-proof",
        "--proof-slide",
        "3",
        "--output-root",
        str(root / "output/carousels"),
    )
    create_seconds = time.perf_counter() - create_start
    if created["state"] != "handoff_ready":
        raise RuntimeError(f"create did not prepare proof: {created}")
    package = Path(created["package_dir"])

    proof = _write_png(root / "generated/proof.png", (1080, 1440), "linen")
    ingested = _call(
        "ingest", str(package), "--instagram-post", str(proof), "--proof-slide", "3"
    )
    if ingested["state"] != "proof_qa_required":
        raise RuntimeError(f"proof ingest returned {ingested}")
    proof_qa = _write_json(root / "proof-qa-authored.json", _observations(package, [3]))
    reviewed = _call("review", str(package), "--qa", str(proof_qa))
    approved = _call(
        "approve",
        str(package),
        "--proof-sha256",
        str(reviewed["proof_sha256"]),
    )
    if approved["state"] != "batch_ready":
        raise RuntimeError(f"approval returned {approved}")

    prepared = _call("prepare", str(package))
    ingest_args = ["ingest", str(package)]
    for slide in prepared["selected_slides"]:
        image = _write_png(
            root / f"generated/slide-{slide:02d}.png", (1080, 1440), "cornsilk"
        )
        ingest_args.extend(("--instagram-post", str(image)))
    _call(*ingest_args)
    final_qa = _write_json(
        root / "final-qa-authored.json", _observations(package, [1, 2, 3, 4])
    )
    final_review = _call("review", str(package), "--qa", str(final_qa))
    if final_review["state"] != "final_qa_required" or final_review["next_action"] != "finalize_deck":
        raise RuntimeError(f"final review returned {final_review}")
    finalized = _call("finalize", str(package))
    if finalized["state"] != "publish_ready":
        raise RuntimeError(f"finalize returned {finalized}")
    lifecycle_seconds = time.perf_counter() - lifecycle_start
    return {
        "create_and_proof_seconds": create_seconds,
        "full_lifecycle_seconds": lifecycle_seconds,
        "non_reference_package_mib": _non_reference_bytes(package) / (1024 * 1024),
    }


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(len(ordered) * 0.95) - 1)]


def _peak_child_rss_mib() -> float:
    raw = float(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss)
    return raw / (1024 * 1024) if sys.platform == "darwin" else raw / 1024


def run_benchmark(runs: int) -> dict[str, Any]:
    if runs < 1:
        raise ValueError("--runs must be at least 1")
    measurements: list[dict[str, float]] = []
    for index in range(runs):
        with tempfile.TemporaryDirectory(prefix=f"asot-carousel-benchmark-{index}-") as raw:
            measurements.append(_run_once(Path(raw)))
    observed = {
        "create_and_proof_p95_seconds": _p95(
            [item["create_and_proof_seconds"] for item in measurements]
        ),
        "full_lifecycle_p95_seconds": _p95(
            [item["full_lifecycle_seconds"] for item in measurements]
        ),
        "peak_rss_mib": _peak_child_rss_mib(),
        "non_reference_package_mib": max(
            item["non_reference_package_mib"] for item in measurements
        ),
    }
    issues = [
        f"{key}={observed[key]:.3f} exceeds {limit:.3f}"
        for key, limit in BUDGETS.items()
        if observed[key] > limit
    ]
    return {
        "schema_version": "carousel-benchmark/v1",
        "status": "PASS" if not issues else "FAIL",
        "synthetic_orchestration_only": True,
        "runs": runs,
        "budgets": BUDGETS,
        "observed": observed,
        "issues": issues,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runs", type=int, default=3)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        report = run_benchmark(args.runs)
    except (OSError, RuntimeError, ValueError, json.JSONDecodeError) as exc:
        report = {
            "schema_version": "carousel-benchmark/v1",
            "status": "FAIL",
            "synthetic_orchestration_only": True,
            "runs": args.runs,
            "budgets": BUDGETS,
            "observed": {},
            "issues": [str(exc)],
        }
    if args.json:
        print(json.dumps(report, ensure_ascii=False, sort_keys=True))
    else:
        print(f"status: {report['status']}")
        print("synthetic orchestration only: yes")
        for key, value in report.get("observed", {}).items():
            print(f"{key}: {value:.3f} (budget {BUDGETS[key]:.3f})")
        for issue in report["issues"]:
            print(f"issue: {issue}")
    return 0 if report["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
