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
    """Raised when a required section would be truncated mid-content by the
    context-pack budget. A silent mid-string cut on a rule-include section
    can mutilate a constraint (e.g. drop "HARD FAIL: yellow"), so the
    context-pack assembly fails loudly instead.
    """


def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    if any(char.isspace() for char in text):
        return max(1, math.ceil(len(text.split()) / 4))
    return max(1, math.ceil(len(text) / 4))


def load_manifest(root: Path) -> dict[str, Any]:
    path = root / MANIFEST_PATH
    if not path.exists():
        raise FileNotFoundError(f"Missing context manifest: {MANIFEST_PATH}")
    return json.loads(path.read_text(encoding="utf-8"))


def trim_to_budget(text: str, budget_tokens: int) -> tuple[str, bool]:
    estimated = estimate_tokens(text)
    if estimated <= budget_tokens:
        return text, False
    max_chars = max(0, budget_tokens * 4)
    if max_chars == 0:
        return "", True
    return text[:max_chars].rstrip() + "\n\n[TRUNCATED_FOR_CONTEXT_BUDGET]", True


def assemble_context_pack(root: Path, profile: str | None = None) -> ContextPack:
    root = root.resolve()
    manifest = load_manifest(root)
    selected_profile = profile or manifest["default_profile"]
    profile_config = manifest["profiles"][selected_profile]
    budget_tokens = int(profile_config["budget_tokens"])
    remaining = budget_tokens
    sections: list[ContextSection] = []

    for item in profile_config.get("sections", []):
        relative = item["path"]
        path = root / relative
        required = bool(item.get("required", True))
        if not path.exists():
            if required:
                raise FileNotFoundError(f"Missing required context file: {relative}")
            continue
        raw = path.read_text(encoding="utf-8", errors="ignore")
        expanded = expand_rule_includes(raw, root)
        content, truncated = trim_to_budget(expanded, remaining)
        if truncated and required and rule_names_referenced(raw):
            raise RequiredSectionTruncatedError(
                f"Required section '{item['id']}' (source: {relative}) expands to "
                f"{estimate_tokens(expanded)} tokens but only {remaining} remain "
                f"in the budget. The section references rule includes "
                f"({rule_names_referenced(raw)}); silently truncating it would "
                "risk dropping a HARD FAIL constraint. Raise the budget for this "
                "profile or move this section earlier in the manifest."
            )
        tokens = estimate_tokens(content)
        remaining = max(0, remaining - tokens)
        sections.append(
            ContextSection(
                id=item["id"],
                path=relative,
                kind=item["kind"],
                estimated_tokens=tokens,
                content=content,
                required=required,
                truncated=truncated,
            )
        )
        if remaining <= 0:
            break

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
        f"Budget: {pack.estimated_tokens}/{pack.budget_tokens} estimated tokens",
        "",
    ]
    for section in pack.sections:
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
