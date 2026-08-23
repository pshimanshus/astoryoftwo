from __future__ import annotations

from app.models import SlidePrompt
from app.providers.base import Renderer


def render_slide(prompt: SlidePrompt, renderer: Renderer, size: str,
                 style_refs: list[bytes], setting_ref: bytes | None) -> bytes:
    refs = list(style_refs)
    if prompt.use_setting_ref and setting_ref is not None:
        refs.append(setting_ref)
    return renderer.render(prompt.image_prompt, refs, size)
