from __future__ import annotations

from app.models import SlidePrompt
from app.pipeline.render import render_slide
from app.providers.base import LLMProvider, QAResult, Renderer

_SYSTEM = (
    "You are Image QA for A Story of Two. Check whether the image is on-brand: hand-drawn warm "
    "house style, the @a.storyof.two brandmark present top-right, any on-image text correct and "
    "legible, no obvious artifacts. Respond ONLY as JSON: {\"passed\": bool, \"reason\": str}."
)


def qa_slide(image: bytes, prompt: SlidePrompt, llm: LLMProvider) -> QAResult:
    ask = f"Intended on-image text: {prompt.on_image_text!r}. Prompt: {prompt.image_prompt}"
    data = llm.reason_json(_SYSTEM, ask, image_bytes=[image])
    return QAResult(passed=bool(data.get("passed", False)), reason=str(data.get("reason", "")))


def render_with_qa(prompt: SlidePrompt, renderer: Renderer, llm: LLMProvider, size: str,
                   style_refs: list[bytes], setting_ref: bytes | None, max_retries: int = 2) -> bytes:
    last = "no attempt"
    for _ in range(max_retries + 1):
        image = render_slide(prompt, renderer, size, style_refs, setting_ref)
        result = qa_slide(image, prompt, llm)
        if result.passed:
            return image
        last = result.reason
    raise RuntimeError(f"QA failed after retries: {last}")
