# A Story of Two — Generation Backend

## Setup
    cd backend && python3 -m venv .venv && . .venv/bin/activate && pip install -r requirements.txt

Add to repo-root `.env.local`: `OPENAI_API_KEY=...` and `GEMINI_API_KEY=...`

## Run
    . .venv/bin/activate && uvicorn app.main:app --reload

## Test
    . .venv/bin/activate && python3 -m unittest

## Live smoke (manual, costs OpenAI credits)
    . .venv/bin/activate
    ASTORY_LIVE_SMOKE=1 python3 scripts/live_smoke.py path/to/voice.webm
Outputs to backend/data/smoke/. Requires OPENAI_API_KEY + GEMINI_API_KEY in .env.local.
