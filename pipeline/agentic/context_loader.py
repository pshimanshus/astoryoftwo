"""Context manifest loading and budgeted context pack assembly."""

from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any

from pipeline.agentic.contracts import ContextPack, ContextSection
from pipeline.agentic.rule_includes import expand_rule_includes, rule_names_referenced


MANIFEST_PATH = Path("config/agentic_context_manifest.json")


class RequiredSectionTruncatedError(RuntimeError):
    """Raised when the complete required context cannot fit its budget."""


def estimate_tokens(text: str) -> int:
    """Deterministic character-based estimate, not a model tokenizer count."""
    return math.ceil(len(text) / 4)


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing context manifest: {MANIFEST_PATH}")
    return json.loads(path.read_text(encoding="utf-8"))


def trim_to_budget(text: str, budget_tokens: int) -> tuple[str, bool]:
    if estimate_tokens(text) <= budget_tokens:
        return text, False
    marker = "\n\n[TRUNCATED_FOR_CONTEXT_BUDGET]"
    max_chars = max(0, budget_tokens * 4)
    if max_chars < len(marker):
        return "", True
    return text[:max_chars - len(marker)].rstrip() + marker, True


def optional_budget(item: dict[str, Any], remaining_tokens: int) -> int:
    if "max_tokens" not in item:
        return remaining_tokens
    max_tokens = int(item["max_tokens"])
    if max_tokens < 0:
        raise ValueError("Optional section max_tokens must be nonnegative")
    return min(remaining_tokens, max_tokens)


def assemble_context_pack(root: Path, profile: str | None = None) -> ContextPack:
    root = root.resolve()
    manifest = load_manifest(root)
    selected_profile = profile or manifest["default_profile"]
    profile_config = manifest["profiles"][selected_profile]
    budget_tokens = int(profile_config["budget_tokens"])
    if budget_tokens < 0:
        raise ValueError("Context budget must be nonnegative")

    # Validate every required file before allocation. Optional material must
    # never consume space reserved for required sections later in the manifest.
    loaded = []
    for item in profile_config.get("sections", []):
        relative = item["path"]
        path = root / relative
        required = bool(item.get("required", True))
        if not path.exists():
            if required:
                raise FileNotFoundError(f"Missing required context file: {relative}")
            continue
        raw = path.read_text(encoding="utf-8")
        expanded = expand_rule_includes(raw, root)
        loaded.append((item, required, expanded, rule_names_referenced(raw)))

    required_tokens = sum(estimate_tokens(text) for _, required, text, _ in loaded if required)
    if required_tokens > budget_tokens:
        details = "; ".join(
            f"{item['id']} ({item['path']}): {estimate_tokens(text)}"
            + (f"; rule includes {rules}" if rules else "")
            for item, required, text, rules in loaded if required
        )
        raise RequiredSectionTruncatedError(
            f"Profile '{selected_profile}' requires {required_tokens} estimated tokens "
            f"but its budget is {budget_tokens}. Required sections cannot be truncated "
            f"or omitted: {details}. Select a smaller task profile or explicitly "
            "increase its budget."
        )

    optional_remaining = budget_tokens - required_tokens
    sections: list[ContextSection] = []
    for item, required, expanded, _ in loaded:
        if required:
            content, truncated = expanded, False
        else:
            section_budget = optional_budget(item, optional_remaining)
            content, truncated = trim_to_budget(expanded, section_budget)
        tokens = estimate_tokens(content)
        if not required:
            optional_remaining -= tokens
        sections.append(
            ContextSection(
                id=item["id"],
                path=item["path"],
                kind=item["kind"],
                estimated_tokens=tokens,
                content=content,
                required=required,
                truncated=truncated,
            )
        )

    return ContextPack(
        profile=selected_profile,
        budget_tokens=budget_tokens,
        estimated_tokens=sum(section.estimated_tokens for section in sections),
        sections=sections,
    )


def render_context_pack(pack: ContextPack) -> str:
    lines = [
        "# Agentic Context Pack",
        "",
        f"Profile: {pack.profile}",
        f"Budget: {pack.estimated_tokens}/{pack.budget_tokens} estimated content tokens (characters / 4; excludes rendering metadata)",
        "",
    ]
    for section in pack.sections:
        if not section.required and not section.content.strip():
            continue
        status = "required" if section.required else "optional"
        truncated = "yes" if section.truncated else "no"
        lines.extend(
            [
                f"## {section.id}",
                "",
                f"Source: `{section.path}`",
                f"Kind: {section.kind}",
                f"Tokens: {section.estimated_tokens}",
                f"Required: {status}",
                f"Truncated: {truncated}",
                "",
                section.content.strip(),
                "",
            ]
        )
    return "\n".join(lines).rstrip() + "\n"
