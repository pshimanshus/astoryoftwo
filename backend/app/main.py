from __future__ import annotations

import io

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse

from app import deps
from app.config import settings
from app.models import Job, JobInput
from app.pipeline.run import run_job

app = FastAPI(title="A Story of Two — Generation Backend")


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/jobs")
async def submit_job(
    background: BackgroundTasks,
    device_id: str = Form(...),
    delivery_contact: str = Form(...),
    creator_name: str = Form(...),
    partner_name: str = Form(...),
    relationship: str = Form(...),
    setting_choice: str = Form(...),
    quote_mode: str = Form(...),
    quote_copy: str = Form(""),
    photos: list[UploadFile] = File(default=[]),
    audio: UploadFile = File(...),
    store=Depends(deps.get_store),
    llm=Depends(deps.get_llm),
    renderer=Depends(deps.get_renderer),
    bank=Depends(deps.get_bank),
) -> dict:
    job = Job.new(JobInput(
        device_id=device_id, delivery_contact=delivery_contact, creator_name=creator_name,
        partner_name=partner_name, relationship=relationship, setting_choice=setting_choice,
        quote_mode=quote_mode, quote_copy=(quote_copy or None), photo_paths=[], audio_path="",
    ))
    store.create(job)
    photo_paths = []
    for i, up in enumerate(photos):
        photo_paths.append(store.save_blob(job.id, f"photo_{i}.jpg", await up.read()))
    job.input.photo_paths = photo_paths
    job.input.audio_path = store.save_blob(job.id, "voice.webm", await audio.read())
    store.save(job)

    background.add_task(run_job, job.id, store, llm, renderer,
                        bank=bank, size=settings.image_size,
                        min_slides=settings.min_slides, max_slides=settings.max_slides)
    return {"job_id": job.id}


@app.get("/jobs/{job_id}")
def get_job(job_id: str, store=Depends(deps.get_store)) -> dict:
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    return {
        "status": job.status.value,
        "error": job.error,
        "slides": [{"index": s.index, "caption": s.caption,
                    "url": f"/jobs/{job_id}/slides/{s.index}.png"} for s in job.slides],
    }


@app.get("/jobs/{job_id}/slides/{index}.png")
def get_slide(job_id: str, index: int, store=Depends(deps.get_store)):
    job = store.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="job not found")
    match = [s for s in job.slides if s.index == index]
    if not match:
        raise HTTPException(status_code=404, detail="slide not found")
    return StreamingResponse(io.BytesIO(store.read_blob(match[0].image_path)), media_type="image/png")
