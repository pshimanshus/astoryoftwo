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
sys.path.insert(0, str(ROOT))

from pipeline.stages.carousel_visual_integrity import (  # noqa: E402
    build_hand_ownership_map,
    hand_is_visible,
)
from tests.helpers.imagegen_invocations import with_synthetic_cli_invocation
from tests.helpers.carousel_qa import (  # noqa: E402
    synthetic_route_sequence_review,
    synthetic_route_story_plan,
)


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
    rows = (
        (1, "cover", "Aachu places one brass key in Zuv's open palm.", "quietly certain together"),
        (2, "deepening", "They point from one moving box toward different doors.", "connected through uncertain direction"),
        (3, "turn", "They pull one folded map gently toward opposite sides.", "tender inside active disagreement"),
        (4, "payoff", "They rotate the map and trace one route together.", "committed through shared learning"),
    )
    payload = {
        "story_plan": synthetic_route_story_plan(),
        "slides": [
            {
                "copy": (
                    "I knew your hand.",
                    "Life gave us two directions.",
                    "Love did not choose the road.",
                    "",
                )[number - 1],
                "copy_mode": "wordless" if number == 4 else "text",
                "beat_delta": (
                    "The offered key establishes their shared-home commitment.",
                    "Their pointing arms reveal two different immediate destinations.",
                    "Opposing grips make the map a physical disagreement.",
                    "Adjacent fingers trace the same route without further dialogue.",
                )[number - 1],
                "copy_image_relation": {
                    "kind": "wordless" if number == 4 else "completion",
                    "proof": action,
                },
                "role": role,
                "physical_action": action,
                "relationship_state": state,
                "camera": {
                    "shot_size": ("wide geography shot", "medium action shot", "close evidence shot", "medium-wide payoff shot")[number - 1],
                    "position": "Doorway-height three-quarter view from the room's left side.",
                    "negative_space": "Quiet upper-left wall protects the exact copy space.",
                },
                "focal_hierarchy": "First read the physical action, then their gaze, then the protected copy space.",
                "setting": {
                    "place": "The worn dining-table corner beside the kitchen doorway.",
                    "time": "Late monsoon afternoon after rain.",
                    "motivated_light": "Cool window light enters from frame left across their hands.",
                    "depth_layers": {
                        "foreground": "A soft chair edge locates the viewer inside the room.",
                        "midground": "Aachu and Zuv perform the changing shared action.",
                        "background": "The open doorway preserves the likely next movement.",
                    },
                },
                "visual_richness": {
                    "scene_action_binding": action,
                    "point_of_view": "The frame follows the partner noticing the shared action change.",
                    "before_frame": "The shared object was still before both partners reached for it.",
                    "after_frame": "Their hands begin settling into one shared direction.",
                    "continuation_pull": "The visible change leaves their next choice open.",
                    "story_evidence": [
                        {"carrier": "creased shared paper", "observable_state": "its fold changes between their hands", "narrative_job": "proves the action changed a shared object"},
                        {"carrier": "two cooling cups", "observable_state": "both sit untouched beside the action", "narrative_job": "proves a lived moment rather than a pose"},
                    ],
                    "posed_portrait_allowed": False,
                    "decorative_clutter_allowed": False,
                },
                "send_reason": (
                    "Send this to the partner who is still learning the shared route with you."
                    if number == len(rows)
                    else ""
                ),
            }
            for number, role, action, state in rows
        ]
    }
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _call(*args: str) -> dict[str, Any]:
    args = with_synthetic_cli_invocation(args)
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
    style_refs = [str(prompt_pack["style_profile"]["reference"]["path"])]
    if len(refs) != 4:
        raise RuntimeError("synthetic fixture expected four identity-role references")
    if len(style_refs) != 1:
        raise RuntimeError("synthetic fixture expected one style reference")
    records: list[dict[str, Any]] = []
    for slide in selected:
        copy = copies[slide]
        slide_record = next(record for record in slides if int(record["slide"]) == slide)
        scene = str(slide_record.get("physical_action") or slide_record.get("visual") or "")
        hand_map = slide_record.get("hand_map")
        if not isinstance(hand_map, dict):
            hand_map = build_hand_ownership_map(scene)
        people = [str(value) for value in hand_map.get("people", [])]
        visible_hands = [
            {
                "owner": str(hand.get("owner") or "person"),
                "side": str(hand.get("side") or "hand"),
                "story_required": True,
                "attachment_traceable": True,
                "contact_geometry_pass": True,
                "solid_object_intersection": False,
                "malformed_or_extra_fingers": False,
                "contact": str(hand.get("contact") or "no unintended object contact"),
                "evidence": "The forearm and wrist continue cleanly into this visible hand.",
            }
            for hand in hand_map.get("hands", [])
            if isinstance(hand, dict) and hand_is_visible(hand)
        ]
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
                            "cinematic_story_frame": {
                                "status": "PASS",
                                "evidence": "The decoded frame shows a layered caught event with a visible temporal consequence.",
                                "frame_reads_as_caught_event": True,
                                "before_after_implied": True,
                                "motivated_light_observed": "Cool window light enters from frame left across their hands.",
                                "depth_layers_observed": dict(slide_record["setting"]["depth_layers"]),
                                "focal_action_clear": True,
                                "story_evidence": [dict(item) for item in slide_record["visual_richness"]["story_evidence"]],
                                "posed_portrait": False,
                                "decorative_clutter": False,
                                "generic_ai_tells": [],
                                **(
                                    {"final_payoff_observed": "Their hands visibly settle into one shared decision."}
                                    if slide == len(slides)
                                    else {"continuation_pull_observed": str(slide_record["visual_richness"]["continuation_pull"])}
                                ),
                            },
                            "entity_spatial_integrity": {
                                "status": "PASS",
                                "evidence": "Every planned person and visible hand has explicit ownership, anatomy, and contact evidence.",
                                "expected_people": len(people),
                                "observed_people": len(people),
                                "observed_people_names": people,
                                "unexpected_entities": [],
                                "unexpected_limbs": [],
                                "duplicated_limbs": [],
                                "ambiguous_contacts": [],
                                "silhouette_evidence": "Every person has a continuous silhouette separated from solid objects.",
                                "visible_hands": visible_hands,
                            },
                            "identity_wardrobe_accessories": {
                                "status": "PASS",
                                "evidence": (
                                    "Aachu retains long dense very dark mostly-straight hair with soft bends, "
                                    "large expressive dark round-almond eyes and full mostly-straight brows with a low soft arch, "
                                    "and warm medium-brown skin tone. Zuv retains thick dark curly hair with visible top and side volume, "
                                    "thick dark brows, and warm brown skin tone; their referenced proportions, clothing, and accessories match."
                                ),
                                "references": {
                                    "aachu": [refs[0]],
                                    "zuv": [refs[1]],
                                    "together": refs[2:],
                                },
                            },
                            "text_brandmark_style_dimensions": {
                                "status": "PASS",
                                "evidence": (
                                    "No story text is present; only the top-right brandmark remains at native size."
                                    if not copy else
                                    "Exact copy and top-right brandmark are visible at native size."
                                ),
                                "expected_text": copy,
                                "observed_text": copy,
                                "unexpected_visible_text": [],
                                "observed_brandmark": "@a.storyof.two",
                                "style_references": style_refs,
                            },
                        }
                    }
                },
            }
        )
    result = {
        "status": "PASS",
        "inspection": {
            "method": "codex_view_image",
            "decoded_pixels_observed": True,
        },
        "selected_slides": selected,
        "slides": records,
    }
    if selected == [1, 2, 3, 4]:
        result["sequence_review"] = synthetic_route_sequence_review(package)
    return result


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
    if approved["state"] != "handoff_ready":
        raise RuntimeError(f"approval returned {approved}")

    ingest_args = ["ingest", str(package)]
    for slide in approved["selected_slides"]:
        image = _write_png(
            root / f"generated/slide-{slide:02d}.png", (1080, 1440), "cornsilk"
        )
        ingest_args.extend(("--instagram-post", str(image)))
    _call(*ingest_args)
    final_qa = _write_json(
        root / "final-qa-authored.json", _observations(package, [1, 2, 3, 4])
    )
    final_review = _call("review", str(package), "--qa", str(final_qa))
    if final_review["state"] != "publish_ready":
        raise RuntimeError(f"final review returned {final_review}")
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
