from __future__ import annotations

from app.models import JobInput, MatchResult, SlidePrompt
from app.providers.base import LLMProvider

_SYSTEM = (
    "You are the Prompt Room for A Story of Two. For each emotional beat, write an image-generation "
    "prompt for a hand-drawn, warm, paper-textured romantic illustration in the A Story of Two house "
    "style. Respond ONLY as JSON: {\"slides\": [{\"image_prompt\": str, \"on_image_text\": str}]} "
    "with one entry per beat, in order."
)


def _style_suffix(brandmark: str) -> str:
    return (f" Hand-drawn A Story of Two house style, warm paper texture, soft line art. "
            f"Native 1024x1536 portrait. Include a tiny low-contrast handwritten "
            f"'{brandmark}' brandmark in the top-right corner.")


def build_slide_prompts(match: MatchResult, job_input: JobInput, llm: LLMProvider,
                        brandmark: str = "@a.storyof.two") -> list[SlidePrompt]:
    prompt = (
        f"Couple: {job_input.creator_name} & {job_input.partner_name}.\n"
        f"Beats (in order): {match.beats}\n"
        f"Write {match.slide_count} slides."
    )
    data = llm.reason_json(_SYSTEM, prompt)
    slides = list(data.get("slides", []))[:match.slide_count]
    while len(slides) < match.slide_count:
        slides.append({"image_prompt": "", "on_image_text": None})

    own_lines = []
    if job_input.quote_mode == "own" and job_input.quote_copy:
        own_lines = [s.strip() for s in job_input.quote_copy.split("|")]

    use_ref = job_input.setting_choice == "keep"
    out: list[SlidePrompt] = []
    for i, s in enumerate(slides):
        if job_input.quote_mode == "none":
            text = None
        elif job_input.quote_mode == "own":
            text = own_lines[i] if i < len(own_lines) else None
        else:  # agent
            text = s.get("on_image_text")
        out.append(SlidePrompt(
            index=i,
            image_prompt=(s.get("image_prompt", "") + _style_suffix(brandmark)),
            on_image_text=text,
            use_setting_ref=use_ref,
        ))
    return out
