"""
Identity dossier builder for Aachu/Zuv image generation.

The image model should not be asked to infer likeness from a few adjectives.
This module creates a required preflight artifact from the identity image
library: a JSON dossier, a human-readable preflight checklist, and a contact
sheet that can be passed as a compact visual reference before generation.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Any

import cv2
import numpy as np


SUPPORTED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DOSSIER_JSON = "identity-dossier.json"
PREFLIGHT_MD = "identity-generation-preflight.md"
FACE_CONTACT_SHEET = "identity-face-contact-sheet.jpg"


FACE_IDENTITY_CONTRACT = {
    "Himanshu/Zuv": {
        "non_negotiable": [
            "dark wavy hair with visible volume",
            "thick dark brows",
            "warm brown skin tone",
            "rounded/oval smiling face structure",
            "trimmed full beard and mustache",
            "calm grounded expression, not a generic model face",
            "medium-tall broader build relative to Aachu",
        ],
        "expression_range": [
            "tired but soft",
            "small private smile",
            "warm amused smile",
            "steady attentive look",
        ],
        "clothing_and_detail_anchors": [
            "light blue or white shirt when story-relevant",
            "dark shirt from close couch selfie when story-relevant",
            "grey trousers",
            "red-black shoes",
            "simple chain/neck detail when visible",
        ],
    },
    "Aachu/Anchal": {
        "non_negotiable": [
            "long dark hair",
            "expressive eyes and brows",
            "warm fair-medium skin tone",
            "soft oval/round face structure",
            "fuller lips and expressive smile",
            "playful dramatic energy under the softness",
            "slightly smaller/petite presence relative to Himanshu",
        ],
        "expression_range": [
            "bright smile",
            "dramatic waiting face",
            "soft affectionate look",
            "playful chaos, never mocked",
        ],
        "clothing_and_detail_anchors": [
            "white/light shirt",
            "grey pinstripe jacket when story-relevant",
            "blue jeans",
            "red bag and red shoes as strong continuity props",
            "soft gold jewelry/necklace when visible",
            "pink-tinted glasses only when supported by reference context",
        ],
    },
}


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def discover_identity_images(workspace_root: Path) -> list[Path]:
    identity_dir = workspace_root / "identity_images"
    if not identity_dir.exists():
        return []
    return sorted(
        path
        for path in identity_dir.rglob("*")
        if path.is_file() and path.suffix.lower() in SUPPORTED_IMAGE_EXTENSIONS
        and "_identity_dossier" not in path.parts
    )


def read_image(path: Path) -> Any:
    image = cv2.imdecode(np.fromfile(str(path), dtype=np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise RuntimeError(f"Could not read identity image: {path}")
    return image


def detect_faces(image: Any) -> list[dict[str, int]]:
    cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    cascade = cv2.CascadeClassifier(cascade_path)
    if cascade.empty():
        return []
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, scaleFactor=1.08, minNeighbors=4, minSize=(48, 48))
    return [
        {"x": int(x), "y": int(y), "width": int(w), "height": int(h)}
        for x, y, w, h in sorted(faces, key=lambda item: item[2] * item[3], reverse=True)
    ]


def crop_face_or_center(image: Any, faces: list[dict[str, int]]) -> Any:
    height, width = image.shape[:2]
    if faces:
        face = faces[0]
        x = face["x"]
        y = face["y"]
        w = face["width"]
        h = face["height"]
        pad = round(max(w, h) * 0.55)
        left = max(0, x - pad)
        top = max(0, y - pad)
        right = min(width, x + w + pad)
        bottom = min(height, y + h + pad)
        return image[top:bottom, left:right]

    side = min(height, width)
    left = max(0, (width - side) // 2)
    top = max(0, (height - side) // 2)
    return image[top : top + side, left : left + side]


def fit_square(image: Any, size: int) -> Any:
    height, width = image.shape[:2]
    scale = size / max(1, max(height, width))
    resized = cv2.resize(
        image,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )
    canvas = np.full((size, size, 3), (248, 242, 232), dtype=np.uint8)
    y = (size - resized.shape[0]) // 2
    x = (size - resized.shape[1]) // 2
    canvas[y : y + resized.shape[0], x : x + resized.shape[1]] = resized
    return canvas


def dominant_color_hex(image: Any) -> str:
    pixels = image.reshape(-1, 3)
    sample = pixels[:: max(1, len(pixels) // 12000)]
    color = np.median(sample, axis=0).astype(int)
    # OpenCV is BGR.
    return f"#{color[2]:02x}{color[1]:02x}{color[0]:02x}"


def build_contact_sheet(inventory: list[dict[str, Any]], output_path: Path) -> None:
    if not inventory:
        return
    thumb = 280
    label_h = 86
    cols = 4
    rows = int(np.ceil(len(inventory) / cols))
    sheet = np.full((rows * (thumb + label_h), cols * thumb, 3), (248, 242, 232), dtype=np.uint8)
    for index, item in enumerate(inventory):
        try:
            image = read_image(Path(item["path"]))
            crop = crop_face_or_center(image, item["faces"])
            tile = fit_square(crop, thumb)
        except RuntimeError:
            tile = np.full((thumb, thumb, 3), (232, 224, 210), dtype=np.uint8)
            cv2.putText(tile, "image", (82, 120), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (88, 80, 70), 2, cv2.LINE_AA)
            cv2.putText(tile, "unreadable", (52, 154), cv2.FONT_HERSHEY_SIMPLEX, 0.62, (88, 80, 70), 2, cv2.LINE_AA)
        row = index // cols
        col = index % cols
        y = row * (thumb + label_h)
        x = col * thumb
        sheet[y : y + thumb, x : x + thumb] = tile
        option_id = item.get("option_id", f"ID{index + 1:02d}")
        cv2.rectangle(sheet, (x + 8, y + 8), (x + 78, y + 38), (248, 242, 232), -1)
        cv2.putText(sheet, option_id, (x + 14, y + 30), cv2.FONT_HERSHEY_SIMPLEX, 0.65, (44, 38, 32), 2, cv2.LINE_AA)
        filename = Path(item["path"]).name
        label = filename[:32]
        cv2.putText(sheet, f"{option_id} {label}", (x + 8, y + thumb + 24), cv2.FONT_HERSHEY_SIMPLEX, 0.42, (44, 38, 32), 1, cv2.LINE_AA)
        cv2.putText(
            sheet,
            f"faces:{len(item['faces'])}  {item.get('width', 0)}x{item.get('height', 0)}",
            (x + 8, y + thumb + 46),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (88, 80, 70),
            1,
            cv2.LINE_AA,
        )
        cv2.putText(
            sheet,
            f"path: {filename[-28:]}",
            (x + 8, y + thumb + 68),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.36,
            (110, 102, 92),
            1,
            cv2.LINE_AA,
        )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ok, encoded = cv2.imencode(".jpg", sheet, [cv2.IMWRITE_JPEG_QUALITY, 92])
    if not ok:
        raise RuntimeError(f"Could not encode identity contact sheet: {output_path}")
    output_path.write_bytes(encoded.tobytes())


def inventory_identity_images(paths: list[Path]) -> list[dict[str, Any]]:
    inventory = []
    for index, path in enumerate(paths, start=1):
        option_id = f"ID{index:02d}"
        try:
            image = read_image(path)
            faces = detect_faces(image)
            height, width = image.shape[:2]
            inventory.append(
                {
                    "option_id": option_id,
                    "path": str(path),
                    "filename": path.name,
                    "width": int(width),
                    "height": int(height),
                    "faces": faces,
                    "face_count": len(faces),
                    "dominant_color": dominant_color_hex(image),
                    "readable": True,
                }
            )
        except RuntimeError as exc:
            inventory.append(
                {
                    "option_id": option_id,
                    "path": str(path),
                    "filename": path.name,
                    "width": 0,
                    "height": 0,
                    "faces": [],
                    "face_count": 0,
                    "dominant_color": None,
                    "readable": False,
                    "warning": str(exc),
                }
            )
    return inventory


def build_preflight_markdown(dossier: dict[str, Any]) -> str:
    lines = [
        "# Identity Generation Preflight",
        "",
        "This file must be read before every carousel image-generation run.",
        "",
        "## Hard Rule",
        "",
        "Do not generate or accept a slide if Aachu or Zuv look like generic illustrated people. Face structure is the first requirement, before style, text, props, or background.",
        "",
        "## Required Visual Inputs",
        "",
    ]
    for path in dossier["reference_images_for_generation"]:
        lines.append(f"- {path}")
    lines.extend(["", "## Face Identity Contract", ""])
    for person, details in dossier["face_identity_contract"].items():
        lines.append(f"### {person}")
        lines.extend(f"- {item}" for item in details["non_negotiable"])
        lines.append("")
    lines.extend(
        [
        "## Generation Procedure",
        "",
        "1. Load the identity contact sheet into the image context.",
        "2. Use the visible ID labels on the contact sheet to choose 2-4 strongest current anchors for the story.",
        "3. Load the selected face/posture/clothing references into the image context as actual images.",
        "4. Start the prompt with the face identity contract.",
        "5. Generate one slide at a time.",
        "6. Reject the image if either face, hair, brows, beard, skin tone, body proportions, or clothing anchors drift from the references.",
        "7. If Aachu/Anchal is wrong, do not continue the set; pick stronger Anchal option IDs from the contact sheet and regenerate from slide 1.",
        "8. Only then check typography, brandmark, and storyboard match.",
            "",
            "## Acceptance Standard",
            "",
            "A stranger who knows Aachu and Zuv from the identity folder should recognize both people before reading the text.",
            "",
        ]
    )
    return "\n".join(lines)


def build_identity_dossier_artifacts(
    *,
    workspace_root: Path,
    out_dir: Path,
    selected_paths: list[Path],
    today: date | None = None,
) -> dict[str, Any]:
    today = today or date.today()
    library_paths = discover_identity_images(workspace_root)
    if not library_paths:
        library_paths = selected_paths
    library_paths = sorted(dict.fromkeys(path.expanduser() for path in library_paths))
    selected_paths = sorted(dict.fromkeys(path.expanduser() for path in selected_paths))

    out_dir.mkdir(parents=True, exist_ok=True)
    inventory = inventory_identity_images(library_paths)
    contact_sheet_path = out_dir / FACE_CONTACT_SHEET
    build_contact_sheet(inventory, contact_sheet_path)

    reference_images = [str(contact_sheet_path), *[str(path) for path in selected_paths]]
    def path_key(path: Path) -> str:
        expanded = path.expanduser()
        try:
            return str(expanded.resolve())
        except FileNotFoundError:
            return str(expanded)

    inventory_by_path = {path_key(Path(item["path"])): item for item in inventory}
    selected_generation_options = []
    for path in selected_paths:
        item = inventory_by_path.get(path_key(path))
        if item:
            selected_generation_options.append(
                {
                    "option_id": item["option_id"],
                    "path": item["path"],
                    "filename": item["filename"],
                    "face_count": item["face_count"],
                    "width": item["width"],
                    "height": item["height"],
                }
            )
    dossier = {
        "schema_version": "1.0",
        "status": "REQUIRED_BEFORE_IMAGE_GENERATION",
        "last_updated": str(today),
        "purpose": "Preflight identity memory for Aachu/Zuv face and clothes consistency before any image generation.",
        "library": {
            "source_dir": str(workspace_root / "identity_images"),
            "image_count": len(library_paths),
            "images": inventory,
        },
        "selected_generation_bundle_count": len(selected_paths),
        "selected_generation_bundle": [str(path) for path in selected_paths],
        "selected_generation_options": selected_generation_options,
        "reference_images_for_generation": reference_images,
        "face_identity_contract": FACE_IDENTITY_CONTRACT,
        "identity_contact_sheet_guidance": {
            "option_id_rule": "Use the ID labels printed on identity-face-contact-sheet.jpg when discussing or replacing references.",
            "aachu_repair_rule": "If Anchal/Aachu face is wrong, stop generation, choose 2-4 stronger Aachu face IDs from the contact sheet, rebuild the package with those identity images, and regenerate from slide 1.",
            "zuv_repair_rule": "If Himanshu/Zuv face is wrong, stop generation, choose 1-2 stronger Zuv face IDs from the contact sheet, rebuild the package with those identity images, and regenerate from slide 1.",
            "hard_limit": "Do not accept a pretty scene or correct text as final when either face fails likeness.",
        },
        "hard_fails": [
            "Generation starts without loading the identity contact sheet.",
            "Generation starts without loading the selected identity references.",
            "Prompt only describes the faces in text but does not use actual identity images.",
            "Generated Himanshu/Zuv loses dark wavy hair, thick brows, beard/mustache, face structure, or build.",
            "Generated Aachu/Anchal loses long dark hair, expressive eyes/brows, face structure, or soft dramatic energy.",
            "A slide is accepted because the scene is pretty even though the faces are wrong.",
        ],
        "human_review_required": True,
        "limitations": [
            "This dossier inventories the local identity library and creates visual preflight anchors; it cannot mathematically guarantee model output likeness.",
            "Final acceptance still requires visual QA against the identity references before packaging a slide as final.",
        ],
    }
    write_json(out_dir / DOSSIER_JSON, dossier)
    (out_dir / PREFLIGHT_MD).write_text(build_preflight_markdown(dossier), encoding="utf-8")
    return {
        **dossier,
        "path": str(out_dir / DOSSIER_JSON),
        "preflight_path": str(out_dir / PREFLIGHT_MD),
        "contact_sheet_path": str(contact_sheet_path),
    }
