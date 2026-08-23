"""Manual end-to-end smoke against real providers. Run:
    ASTORY_LIVE_SMOKE=1 python3 scripts/live_smoke.py path/to/voice.webm
Requires OPENAI_API_KEY and GEMINI_API_KEY in .env.local.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# Make backend/ importable when run as `python3 scripts/live_smoke.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from app.deps import get_bank
from app.models import Job, JobInput
from app.pipeline.run import run_job
from app.providers.gemini import GeminiProvider
from app.providers.openai_renderer import OpenAIRenderer
from app.store import JobStore


def main() -> int:
    if os.environ.get("ASTORY_LIVE_SMOKE") != "1":
        print("Refusing to run: set ASTORY_LIVE_SMOKE=1 to call real paid/free APIs.")
        return 2
    if not settings.openai_api_key or not settings.gemini_api_key:
        print("Missing OPENAI_API_KEY or GEMINI_API_KEY in .env.local.")
        return 2
    audio_path = Path(sys.argv[1])
    store = JobStore(db_path=settings.data_dir / "smoke/jobs.db", blob_root=settings.data_dir / "smoke")
    job = Job.new(JobInput(device_id="smoke", delivery_contact="me", creator_name="Aarav",
                           partner_name="Mira", relationship="together", setting_choice="fresh",
                           quote_mode="agent", quote_copy=None, photo_paths=[], audio_path=""))
    store.create(job)
    job.input.audio_path = store.save_blob(job.id, "voice.webm", audio_path.read_bytes())
    store.save(job)
    run_job(job.id, store, GeminiProvider(settings.gemini_api_key, settings.gemini_model),
            OpenAIRenderer(settings.openai_api_key, settings.image_model),
            bank=get_bank(), size=settings.image_size)
    done = store.get(job.id)
    print("status:", done.status.value, "| error:", done.error, "| slides:", len(done.slides))
    return 0 if done.status.value == "ready" else 1


if __name__ == "__main__":
    raise SystemExit(main())
