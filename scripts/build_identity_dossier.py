#!/usr/bin/env python3
"""Build the required Aachu/Zuv identity dossier before image generation."""

from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from pipeline.stages.identity_dossier import build_identity_dossier_artifacts  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Build identity-dossier.json, identity-generation-preflight.md, and identity-face-contact-sheet.jpg.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=Path("."),
        help="Workspace root containing identity_images/.",
    )
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=Path("identity_images") / "_identity_dossier",
        help="Directory where dossier artifacts should be written.",
    )
    parser.add_argument(
        "--selected-image",
        dest="selected_images",
        action="append",
        default=[],
        help="Selected face/posture/clothing reference image. Repeat for multiple references.",
    )
    args = parser.parse_args()

    workspace_root = args.workspace_root.expanduser().resolve()
    selected_paths = [Path(path).expanduser() for path in args.selected_images]
    dossier = build_identity_dossier_artifacts(
        workspace_root=workspace_root,
        out_dir=args.out_dir.expanduser(),
        selected_paths=selected_paths,
        today=date.today(),
    )
    print(f"identity dossier -> {dossier['path']}")
    print(f"preflight -> {dossier['preflight_path']}")
    print(f"contact sheet -> {dossier['contact_sheet_path']}")
    print(f"identity library images -> {dossier['library']['image_count']}")


if __name__ == "__main__":
    main()
