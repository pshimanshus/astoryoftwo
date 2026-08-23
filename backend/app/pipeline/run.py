from __future__ import annotations

from app.data_refs import house_style_ref_paths, load_winner_bank
from app.models import JobStatus
from app.pipeline.assemble import assemble_slides
from app.pipeline.match import match_winner
from app.pipeline.prompt_build import build_slide_prompts
from app.pipeline.qa import render_with_qa
from app.pipeline.transcribe import story_from_audio
from app.providers.base import LLMProvider, Renderer
from app.store import JobStore


def run_job(job_id: str, store: JobStore, llm: LLMProvider, renderer: Renderer, *,
            bank=None, size: str = "1024x1536", min_slides: int = 3, max_slides: int = 5,
            max_retries: int = 2) -> None:
    job = store.get(job_id)
    if job is None:
        return
    try:
        job.status = JobStatus.RUNNING
        job.touch()
        store.save(job)

        ji = job.input
        audio = store.read_blob(ji.audio_path)
        story = story_from_audio(audio, "audio/webm", llm)
        job.story_text = story
        store.save(job)

        bank = bank if bank is not None else load_winner_bank()
        match = match_winner(story, ji.creator_name, ji.partner_name, ji.relationship,
                             bank, llm, min_slides=min_slides, max_slides=max_slides)
        job.match = match
        store.save(job)

        prompts = build_slide_prompts(match, ji, llm)

        style_refs = [p.read_bytes() for p in house_style_ref_paths()]
        setting_ref = store.read_blob(ji.photo_paths[0]) if ji.photo_paths else None

        images = [render_with_qa(p, renderer, llm, size, style_refs, setting_ref, max_retries)
                  for p in prompts]

        job.slides = assemble_slides(prompts, images,
                                     lambda name, data: store.save_blob(job_id, name, data))
        job.status = JobStatus.READY
        job.touch()
        store.save(job)
    except Exception as exc:  # never raise out of the worker
        job.status = JobStatus.FAILED
        job.error = str(exc)
        job.touch()
        store.save(job)
