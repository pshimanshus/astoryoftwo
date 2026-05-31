"""Deterministic gates for the carousel workflow runner.

Each module exposes a single `check_*` function returning a typed
`WorkflowGate` so the runner can promote/halt a state on measurement,
not on an LLM's opinion.
"""

from pipeline.agentic.checks.image_size import check_image_size
from pipeline.agentic.checks.ocr_text import check_ocr_text
from pipeline.agentic.checks.palette import check_palette
from pipeline.agentic.checks.prompt_constraints import check_prompt_constraints

__all__ = [
    "check_image_size",
    "check_ocr_text",
    "check_palette",
    "check_prompt_constraints",
]
