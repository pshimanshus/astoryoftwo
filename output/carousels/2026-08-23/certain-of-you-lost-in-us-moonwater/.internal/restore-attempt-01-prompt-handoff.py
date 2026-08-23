from __future__ import annotations

import copy
import hashlib
import json
from pathlib import Path

from pipeline.stages.codex_builtin_image_generation import _retry_prompt_records


PACKAGE = Path("output/carousels/2026-08-23/certain-of-you-lost-in-us-moonwater")
ACTIVE = PACKAGE / "codex-image-prompts"


def replace_all(value, before: str, after: str):
    if isinstance(value, str):
        return value.replace(before, after)
    if isinstance(value, list):
        return [replace_all(item, before, after) for item in value]
    if isinstance(value, dict):
        return {key: replace_all(item, before, after) for key, item in value.items()}
    return value


pack = json.loads((PACKAGE / "prompt-pack.json").read_text(encoding="utf-8"))
slide = next(item for item in pack["slides"] if int(item["slide"]) == 4)
new_scene = slide["scene"]
wardrobe_insert = (
    "HARD WARDROBE CONTINUITY: Aachu wears her black open overshirt over a black top with blue jeans; "
    "Zuv wears his white zip jacket with charcoal trousers. These exact clothes and colors override every "
    "outfit visible in a style reference; never render Aachu in a white shirt or Zuv in a navy T-shirt. "
)
old_scene = new_scene.replace(wardrobe_insert, "")
new_wardrobe = slide["wardrobe"]
old_wardrobe = "Same wardrobe, damp at knees and hems, no color change."
old_pack = replace_all(copy.deepcopy(pack), new_scene, old_scene)
old_pack = replace_all(old_pack, new_wardrobe, old_wardrobe)
excluded_route_language = (
    "No theatre or stage imagery; no curtain, script, chair motif, maze, blueprint, diagram, map, "
    "compass, path, route line, red thread, arrow, wedding symbolism, rescue gesture, extra person, "
    "reflection-person, silhouette-person, or unrequested text."
)
# The repair script appended this negative layer once more while preparing attempt 02.
# Restore the exact attempt-01 repetition count so its immutable prompt hashes can be verified.
old_pack["shared_negative_prompt"] = old_pack["shared_negative_prompt"].rsplit(
    " " + excluded_route_language, 1
)[0]
for record in old_pack["slides"]:
    record["negative_prompt"] = record["negative_prompt"].rsplit(
        " " + excluded_route_language, 1
    )[0]
payload = (json.dumps(old_pack, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
print("reconstructed_prompt_pack_sha256=sha256:" + hashlib.sha256(payload).hexdigest())

ACTIVE.mkdir(parents=True, exist_ok=True)
_retry_prompt_records(
    PACKAGE,
    prompt_staging_dir=ACTIVE,
    slides=[next(item for item in old_pack["slides"] if int(item["slide"]) == 4)],
    output_formats=["instagram_post"],
    prompt_pack=old_pack,
)
for path in sorted(ACTIVE.rglob("*")):
    if path.is_file():
        print(path.relative_to(PACKAGE).as_posix() + " sha256:" + hashlib.sha256(path.read_bytes()).hexdigest())
