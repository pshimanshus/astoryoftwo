from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from PIL import Image

from pipeline.stages.identity_dossier import (
    DOSSIER_JSON,
    FACE_CONTACT_SHEET,
    PREFLIGHT_MD,
    build_identity_dossier_artifacts,
    discover_identity_images,
)


def save_image(path: Path, size: tuple[int, int] = (96, 128)) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", size, color=(220, 190, 160)).save(path)
    return path


def test_discover_identity_images_skips_existing_dossier_outputs(tmp_path: Path) -> None:
    identity_dir = tmp_path / "identity_images"
    aachu = save_image(identity_dir / "aachu.jpg")
    zuv = save_image(identity_dir / "zuv.png")
    save_image(identity_dir / "_identity_dossier" / "contact-sheet.jpg")

    discovered = discover_identity_images(tmp_path)

    assert discovered == [aachu, zuv]


def test_build_identity_dossier_artifacts_writes_preflight_bundle(tmp_path: Path) -> None:
    identity_dir = tmp_path / "identity_images"
    aachu = save_image(identity_dir / "aachu.jpg")
    zuv = save_image(identity_dir / "zuv.png")
    out_dir = identity_dir / "_identity_dossier"

    dossier = build_identity_dossier_artifacts(
        workspace_root=tmp_path,
        out_dir=out_dir,
        selected_paths=[zuv],
        today=date(2026, 6, 30),
    )

    assert Path(dossier["path"]) == out_dir / DOSSIER_JSON
    assert Path(dossier["preflight_path"]) == out_dir / PREFLIGHT_MD
    assert Path(dossier["contact_sheet_path"]) == out_dir / FACE_CONTACT_SHEET
    assert (out_dir / DOSSIER_JSON).exists()
    assert (out_dir / PREFLIGHT_MD).exists()
    assert (out_dir / FACE_CONTACT_SHEET).exists()

    payload = json.loads((out_dir / DOSSIER_JSON).read_text(encoding="utf-8"))
    assert payload["last_updated"] == "2026-06-30"
    assert payload["library"]["image_count"] == 2
    assert [Path(item["path"]) for item in payload["library"]["images"]] == [aachu, zuv]
    assert payload["selected_generation_bundle"] == [str(zuv)]
    assert payload["selected_generation_options"][0]["path"] == str(zuv)
    assert str(out_dir / FACE_CONTACT_SHEET) in payload["reference_images_for_generation"]
