"""Synthetic invocation fixtures; these records never establish live tool execution.

Tests use authored call arguments and solid-color PNGs to exercise the runtime
contract. Only a real tool dispatch can provide live execution evidence.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any


def synthetic_invocation_records(
    package: Path, generated_paths_by_format: dict[str, list[Path]],
) -> list[dict[str, Any]]:
    from pipeline.stages.codex_builtin_image_generation import build_compiled_prompt_handoff
    from pipeline.stages.carousel_generation_state import read_generation_state

    package = Path(package).resolve()
    state = read_generation_state(package)
    selected = [int(n) for n in state.get("selected_slides", [])]
    formats = list(generated_paths_by_format)
    handoff = build_compiled_prompt_handoff(
        package, slide_numbers=selected, output_formats=formats,
    )
    records: list[dict[str, Any]] = []
    for fmt, paths in generated_paths_by_format.items():
        for number, source in zip(selected, paths):
            entry = next(f for f in handoff["files"] if f["slide"] == number and f["format"] == fmt)
            inputs = entry.get("input_images", handoff["reference_bindings"])
            records.append({
                "slide": number,
                "format": fmt,
                "intent": entry.get("intent", "generate"),
                "tool": "image_gen.imagegen",
                "sent_prompt_sha256": entry["sha256"],
                "input_images": inputs,
                "returned_source_sha256": "sha256:" + hashlib.sha256(Path(source).read_bytes()).hexdigest(),
            })
    return records


def ingest_synthetic_outputs(package: Path, outputs: dict[str, list[Path]], **kwargs: Any) -> dict[str, Any]:
    """Exercise production ingestion with explicitly fabricated test call records."""
    from pipeline.stages.codex_builtin_image_generation import ingest_generated_outputs

    if "invocation_records" not in kwargs:
        records = synthetic_invocation_records(package, outputs)
        if kwargs.get("tool_reported_model") is not None:
            for record in records:
                record["model"] = kwargs["tool_reported_model"]
        kwargs["invocation_records"] = records
    return ingest_generated_outputs(package, outputs, **kwargs)


def with_synthetic_cli_invocation(args: tuple[str, ...]) -> tuple[str, ...]:
    """Attach an authored fixture record to a synthetic CLI ingest invocation."""
    if not args or args[0] != "ingest" or "--invocation-json" in args or len(args) < 2:
        return args
    package = Path(args[1])
    from pipeline.stages.carousel_generation_state import archived_package_read_only_reason
    if not package.is_dir():
        return args
    if archived_package_read_only_reason(package):
        # Reach the production archive guard with a syntactically valid CLI
        # argument; never inspect or mutate an archived package's evidence.
        target = package.parent / "synthetic-archived-invocations.json"
        target.write_text("[{}]", encoding="utf-8")
        return (*args, "--invocation-json", str(target))
    outputs: dict[str, list[Path]] = {}
    flag_formats = {"--instagram-post": "instagram_post", "--reels-stories": "reels_stories", "--square": "square"}
    for index, arg in enumerate(args[:-1]):
        if arg in flag_formats:
            outputs.setdefault(flag_formats[arg], []).append(Path(args[index + 1]))
    if not outputs:
        return args
    records = synthetic_invocation_records(package, outputs)
    if "--model" in args:
        model = args[args.index("--model") + 1]
        for record in records:
            record["model"] = model
    target = package.parent / "synthetic-invocations.json"
    target.write_text(json.dumps(records), encoding="utf-8")
    return (*args, "--invocation-json", str(target))
