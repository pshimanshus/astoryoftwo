#!/usr/bin/env python3
"""
Scrape @a.storyof.two via Apify instagram-profile-scraper.
Usage: python scripts/scrape_instagram.py [--limit 50]
"""
import json
import os
import sys
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

APIFY_API_KEY = os.getenv("APIFY_API_KEY")
INSTAGRAM_HANDLE = "a.storyof.two"
ACTOR_ID = "apify~instagram-scraper"
BASE_URL = "https://api.apify.com/v2"


def run_scrape(limit: int = 50) -> dict:
    if not APIFY_API_KEY:
        raise RuntimeError("APIFY_API_KEY must be set in the environment before scraping.")

    headers = {"Authorization": f"Bearer {APIFY_API_KEY}"}
    payload = {
        "directUrls": [f"https://www.instagram.com/{INSTAGRAM_HANDLE}/"],
        "resultsType": "posts",
        "resultsLimit": limit,
        "addParentData": True,
    }

    print(f"Starting Apify actor {ACTOR_ID} for @{INSTAGRAM_HANDLE} (limit={limit})...")
    resp = httpx.post(
        f"{BASE_URL}/acts/{ACTOR_ID}/runs",
        headers=headers,
        json=payload,
        timeout=30,
    )
    resp.raise_for_status()
    run_id = resp.json()["data"]["id"]
    print(f"Run started: {run_id}")

    # Poll for completion
    import time
    while True:
        status_resp = httpx.get(f"{BASE_URL}/actor-runs/{run_id}", headers=headers, timeout=10)
        status = status_resp.json()["data"]["status"]
        print(f"  Status: {status}")
        if status in ("SUCCEEDED", "FAILED", "ABORTED"):
            break
        time.sleep(5)

    if status != "SUCCEEDED":
        raise RuntimeError(f"Apify run failed with status: {status}")

    # Fetch dataset
    dataset_id = status_resp.json()["data"]["defaultDatasetId"]
    items_resp = httpx.get(
        f"{BASE_URL}/datasets/{dataset_id}/items",
        headers=headers,
        params={"format": "json"},
        timeout=30,
    )
    items = items_resp.json()
    print(f"Fetched {len(items)} posts.")
    return items


def save_corpus(items: list) -> Path:
    today = datetime.now().strftime("%Y-%m-%d")
    raw_dir = ROOT / "corpus" / "raw"
    raw_dir.mkdir(parents=True, exist_ok=True)
    out_path = raw_dir / f"{today}-raw.json"
    with open(out_path, "w") as f:
        json.dump(items, f, indent=2, default=str)
    print(f"Saved raw corpus to {out_path}")
    return out_path


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--limit", type=int, default=50)
    args = parser.parse_args()

    items = run_scrape(limit=args.limit)
    save_corpus(items)
    print("Done. Next: run `python -m pipeline.stages.a2_parser` to parse corpus.")
