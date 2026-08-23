from __future__ import annotations

from typing import Callable

from app.models import Slide, SlidePrompt


def assemble_slides(prompts: list[SlidePrompt], images: list[bytes],
                    save_blob: Callable[[str, bytes], str]) -> list[Slide]:
    slides: list[Slide] = []
    for prompt, image in zip(sorted(prompts, key=lambda p: p.index), images):
        path = save_blob(f"slide_{prompt.index}.png", image)
        slides.append(Slide(index=prompt.index, image_path=path, caption=prompt.on_image_text))
    return slides
