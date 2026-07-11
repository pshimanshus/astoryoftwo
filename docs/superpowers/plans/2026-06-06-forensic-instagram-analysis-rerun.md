# Forensic Instagram Analysis Rerun Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the @a.storyof.two Instagram analysis from the attached forensic prompt using larger Apify collection, post-level metrics, comment-language proxies, network discovery, and ASOT-specific remix ideas.

**Architecture:** Use ignored `tmp/` scripts for data collection and deterministic analysis, keeping generated research outputs in `corpus/` and `output/reports/`. Treat Apify public fields as evidence and explicitly mark missing metrics such as saves, shares, DM sends, retention, and inaccessible comment depth.

**Tech Stack:** Python 3.13, httpx, Apify `apify~instagram-scraper`, existing repo corpus/output folders.

---

### Task 1: Target Corpus

**Files:**
- Use: `scripts/scrape_instagram.py`
- Write: `corpus/raw/2026-06-06-raw.json`
- Write: `corpus/posts/2026-06-06-posts.json`

- [x] **Step 1: Run ASOT scrape with `--limit 150`**

Run: `sh -c 'set -a; . ./.env; set +a; venv/bin/python scripts/scrape_instagram.py --limit 150'`
Expected: Apify succeeds and reports the available public post count.

- [x] **Step 2: Parse target corpus**

Run: `venv/bin/python -m pipeline.stages.a2_parser --raw-path corpus/raw/2026-06-06-raw.json`
Expected: `corpus/posts/2026-06-06-posts.json` is written.

### Task 2: Candidate Universe

**Files:**
- Create: `tmp/forensic_instagram_candidates.py`
- Write: `output/reports/2026-06-06-forensic-candidate-universe.json`

- [ ] **Step 1: Extract ASOT graph signals**

Read ASOT captions, mentions, hashtags, and latest comments. Score comment accounts by repeated presence and partner-tag behavior.

- [ ] **Step 2: Add seed accounts and search/tag discovery handles**

Include direct, adjacent, inspiration, and interaction-led candidates. Ensure at least 60 candidate accounts before scraping.

### Task 3: Expanded Apify Scrape

**Files:**
- Create: `tmp/forensic_instagram_scrape.py`
- Write: `corpus/forensic-instagram/2026-06-06/accounts/*.json`
- Write: `corpus/forensic-instagram/2026-06-06/manifest.json`

- [ ] **Step 1: Scrape batches of candidate accounts**

Use the same Apify actor with profile URLs and a per-profile post limit target of 50 when the actor supports it.

- [ ] **Step 2: Record scrape failures and partial results**

Do not hide failed handles. Write status and item counts into the manifest.

### Task 4: Forensic Metrics And Report

**Files:**
- Create: `tmp/forensic_instagram_report.py`
- Write: `output/reports/2026-06-06-forensic-instagram-growth-analysis.md`
- Write: `output/reports/2026-06-06-forensic-instagram-growth-metrics.json`

- [ ] **Step 1: Compute post metrics**

Compute engagement rate, view rate, comment intensity, like efficiency, velocity proxy, within-account outlier score, follower tier, and comment/sendability proxy where comments are present.

- [ ] **Step 2: Classify mechanics**

Assign primary mechanic and emotional flavor using deterministic keyword and caption heuristics, then preserve raw evidence for manual review.

- [ ] **Step 3: Build prompt-structured report**

Write the required sections: data audit, discovery map, top viral posts, interaction posts, themes, ASOT working/not-working autopsy, competitor teardown, mechanics library, opportunity gaps, strategies to avoid, 30-day plan, 75 ideas, and prioritized next 10 posts.

### Task 5: Verification

**Files:**
- Use: `tests/test_pipeline_runner_contract.py`
- Use: `scripts/wiki_health.py`

- [ ] **Step 1: Run focused pipeline tests**

Run: `venv/bin/python -m pytest tests/test_pipeline_runner_contract.py -q`
Expected: all selected tests pass.

- [ ] **Step 2: Run wiki health**

Run: `venv/bin/python scripts/wiki_health.py --write --fix-index --session-note "Forensic Instagram analysis rerun."`
Expected: `wiki health: PASS`.
