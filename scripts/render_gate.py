#!/usr/bin/env python3
"""Renderer capability gate for the video line.

The imagegen contract assumes Codex, which owns a built-in ImageGen tool. Claude
Code and other harnesses have no renderer. This gate makes that difference
explicit instead of letting a run quietly stall or, worse, be reported as done.

It never renders anything. It validates that a prompt pack's bindings are real
and unchanged, emits a handoff bundle a human or Codex can execute, and holds
the shot in a blocked state until actual returned pixels are ingested and
inspected.

    render_gate.py prepare PROMPT_PACK.md [--out DIR]
    render_gate.py ingest SHOT_DIR --image PATH
    render_gate.py status SHOT_DIR

Renderer availability is declared by ASOT_RENDERER. Default is "none", so the
gate fails closed: absence of a declaration is treated as absence of a renderer.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
STYLE_CONTRACT = REPO / "config" / "carousel_style_contract.json"

STATE_BLOCKED = "BLOCKED_AWAITING_PIXELS"
STATE_REVIEW = "AWAITING_PIXEL_REVIEW"

EXPECTED_CANVAS = (1080, 1920)
MAX_ATTACHMENTS = 5


class GateError(Exception):
    """Anything that should stop the run with a readable message."""


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return f"sha256:{digest.hexdigest()}"


def renderer_available() -> tuple[bool, str]:
    import os

    declared = os.environ.get("ASOT_RENDERER", "none").strip().lower()
    return declared not in ("", "none", "false", "0"), declared or "none"


# --- prompt pack parsing ----------------------------------------------------
# The markdown pack is the single source of truth. Parsing it beats maintaining
# a parallel JSON that can drift away from the document humans actually edit.


def parse_pack(pack_path: Path) -> dict:
    if not pack_path.is_file():
        raise GateError(f"Prompt pack not found: {pack_path}")
    text = pack_path.read_text(encoding="utf-8")

    fences = re.findall(r"```text\n(.*?)```", text, flags=re.DOTALL)
    if not fences:
        raise GateError(
            f"{pack_path.name} has no ```text fence. The compiled prompt must live "
            "in one, so the gate hands off exactly what was authored."
        )
    prompt = fences[0].strip()

    attach_section = re.search(
        r"##\s*Attachments.*?\n(.*?)(?=\n##\s|\Z)", text, flags=re.DOTALL
    )
    if not attach_section:
        raise GateError(f"{pack_path.name} has no '## Attachments' section.")
    paths: list[str] = []
    for row in attach_section.group(1).splitlines():
        if not row.strip().startswith("|"):
            continue
        found = re.findall(r"`([^`]+\.(?:jpg|jpeg|png))`", row)
        paths.extend(found)
    if not paths:
        raise GateError("No attachment paths found in the Attachments table.")

    checks = re.findall(r"^\s*-\s*\[\s*\]\s*(.+)$", text, flags=re.MULTILINE)

    shot = re.search(r"^shot:\s*(.+)$", text, flags=re.MULTILINE)
    return {
        "prompt": prompt,
        "attachments": paths,
        "acceptance_checks": [c.strip() for c in checks],
        "shot_label": shot.group(1).strip() if shot else pack_path.stem,
    }


def expected_style_board_hash() -> tuple[str, str] | tuple[None, None]:
    if not STYLE_CONTRACT.is_file():
        return None, None
    data = json.loads(STYLE_CONTRACT.read_text(encoding="utf-8"))
    ref = data.get("style_profile", {}).get("reference", {})
    return ref.get("path"), ref.get("sha256")


def validate_attachments(paths: list[str]) -> list[dict]:
    if len(paths) > MAX_ATTACHMENTS:
        raise GateError(
            f"{len(paths)} attachments listed, maximum is {MAX_ATTACHMENTS}. "
            "Reference minimalism is a standing rule: more photographs make the "
            "model average across faces instead of locking to one."
        )
    board_path, board_hash = expected_style_board_hash()
    resolved: list[dict] = []
    missing: list[str] = []
    for rel in paths:
        path = (REPO / rel).resolve()
        if not path.is_file():
            missing.append(rel)
            continue
        entry = {"path": rel, "sha256": sha256_file(path), "bytes": path.stat().st_size}
        if board_path and rel == board_path:
            entry["role"] = "style_board"
            if board_hash and entry["sha256"] != board_hash:
                raise GateError(
                    "Style board hash does not match the style contract.\n"
                    f"  expected {board_hash}\n  found    {entry['sha256']}\n"
                    "The locked board changed or the wrong file is bound. Stop."
                )
        resolved.append(entry)
    if missing:
        raise GateError("Attachments not found:\n  " + "\n  ".join(missing))
    return resolved


# --- commands ---------------------------------------------------------------


def cmd_prepare(args: argparse.Namespace) -> int:
    pack_path = Path(args.pack).expanduser()
    pack = parse_pack(pack_path)
    attachments = validate_attachments(pack["attachments"])

    out = Path(args.out).expanduser() if args.out else REPO / "output" / "video" / pack_path.stem
    handoff = out / "handoff"
    handoff.mkdir(parents=True, exist_ok=True)

    (handoff / "prompt.txt").write_text(pack["prompt"] + "\n", encoding="utf-8")
    (handoff / "attachments.json").write_text(
        json.dumps(attachments, indent=2) + "\n", encoding="utf-8"
    )

    available, declared = renderer_available()
    state = {
        "shot": pack["shot_label"],
        "prompt_pack": str(pack_path.relative_to(REPO)) if pack_path.is_absolute() else str(pack_path),
        "prompt_sha256": f"sha256:{hashlib.sha256(pack['prompt'].encode()).hexdigest()}",
        "attachments": attachments,
        "acceptance_checks": pack["acceptance_checks"],
        "renderer_declared": declared,
        "renderer_available": available,
        "state": STATE_BLOCKED,
        "attempts": [],
        "prepared_at": _now(),
    }
    (out / "STATE.json").write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    lines = [
        f"# Handoff — {pack['shot_label']}",
        "",
        f"prepared: {state['prepared_at']}",
        f"renderer declared: `{declared}`",
        "",
        "## Run this",
        "",
        "Attach these files, in these roles, and nothing else:",
        "",
    ]
    for item in attachments:
        lines.append(f"- `{item['path']}`")
    lines += [
        "",
        "Then send the contents of `handoff/prompt.txt` verbatim. Do not paraphrase,",
        "reflow, or summarise it.",
        "",
        "## Then come back",
        "",
        "```bash",
        f"python3 scripts/render_gate.py ingest {out.relative_to(REPO) if out.is_absolute() else out} --image PATH_TO_RETURNED_IMAGE",
        "```",
        "",
        "## Acceptance checks (inspect pixels, not the prompt)",
        "",
    ]
    lines += [f"- [ ] {c}" for c in pack["acceptance_checks"]]
    (handoff / "RUN.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"Prepared handoff for {pack['shot_label']}")
    print(f"  bundle: {handoff}")
    print(f"  attachments validated: {len(attachments)}")
    if available:
        print(f"  renderer declared as '{declared}' — render now, then ingest.")
    else:
        print("  NO RENDERER in this session. State is BLOCKED_AWAITING_PIXELS.")
        print("  Run the bundle in Codex (or by hand), then ingest the result.")
    return 0


def cmd_ingest(args: argparse.Namespace) -> int:
    shot_dir = Path(args.shot_dir).expanduser()
    state_path = shot_dir / "STATE.json"
    if not state_path.is_file():
        raise GateError(f"No STATE.json in {shot_dir}. Run prepare first.")
    state = json.loads(state_path.read_text(encoding="utf-8"))

    image = Path(args.image).expanduser()
    if not image.is_file():
        raise GateError(f"Image not found: {image}")

    try:
        from PIL import Image
    except ImportError as exc:  # pragma: no cover - environment issue
        raise GateError("Pillow is required to verify returned pixels.") from exc

    with Image.open(image) as img:
        size = img.size

    received = shot_dir / "received"
    received.mkdir(parents=True, exist_ok=True)
    attempt_no = len(state.get("attempts", [])) + 1
    dest = received / f"attempt-{attempt_no:02d}{image.suffix.lower()}"
    dest.write_bytes(image.read_bytes())

    attempt = {
        "attempt": attempt_no,
        "file": str(dest.relative_to(shot_dir)),
        "sha256": sha256_file(dest),
        "size": list(size),
        "canvas_ok": list(size) == list(EXPECTED_CANVAS),
        "ingested_at": _now(),
    }
    state.setdefault("attempts", []).append(attempt)
    state["state"] = STATE_REVIEW
    state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")

    print(f"Ingested attempt {attempt_no}: {dest}")
    print(f"  sha256: {attempt['sha256']}")
    print(f"  size:   {size[0]}x{size[1]}", end="")
    if not attempt["canvas_ok"]:
        print(f"  ← WRONG, expected {EXPECTED_CANVAS[0]}x{EXPECTED_CANVAS[1]}")
    else:
        print("  ok")

    print("\nState is AWAITING_PIXEL_REVIEW. Nothing is approved yet.")
    print("Open the image and check every line before promoting it:\n")
    for check in state.get("acceptance_checks", []):
        print(f"  [ ] {check}")

    if attempt_no >= 2:
        print(
            "\nTwo attempts used on this premise. Per the imagegen contract's repair"
            "\nrule, rewrite the scene rather than re-rolling it again."
        )
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    state_path = Path(args.shot_dir).expanduser() / "STATE.json"
    if not state_path.is_file():
        raise GateError(f"No STATE.json in {args.shot_dir}.")
    state = json.loads(state_path.read_text(encoding="utf-8"))
    print(f"shot:     {state.get('shot')}")
    print(f"state:    {state.get('state')}")
    print(f"renderer: {state.get('renderer_declared')}")
    print(f"attempts: {len(state.get('attempts', []))}")
    for attempt in state.get("attempts", []):
        flag = "" if attempt.get("canvas_ok") else "  (wrong canvas)"
        print(f"  {attempt['attempt']}: {attempt['file']} {attempt['size']}{flag}")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Renderer capability gate for video shots.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("prepare", help="Validate bindings and emit a handoff bundle.")
    p.add_argument("pack")
    p.add_argument("--out")
    p.set_defaults(func=cmd_prepare)

    i = sub.add_parser("ingest", help="Record returned pixels and open review.")
    i.add_argument("shot_dir")
    i.add_argument("--image", required=True)
    i.set_defaults(func=cmd_ingest)

    s = sub.add_parser("status", help="Report shot state.")
    s.add_argument("shot_dir")
    s.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    try:
        return args.func(args)
    except GateError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
