# A Story of Two — `site-studio/` (our version)

This is **our** immersive multi-room website — kept in its own directory because
the `site/` folder is owned by the Codex agents (a different, illustrated
concept-art design). Nothing here touches `site/`.

## Run it

```bash
cd site-studio
python3 -m http.server 8755
# open http://localhost:8755
```

(Or open `site-studio/index.html` directly — numbers are baked in, so it works
as a file too.)

## Pages

`index.html` (immersive entry hub) → `reels.html` · `stories.html` ·
`memory.html` · `studio.html` · `brands.html`. Shared `styles.css` + `main.js`.

## Regenerate the room pages

The five rooms are generated from the real feed by `scripts/build_pages.py`,
which writes here via the `ASTORY_SITE_DIR` env var (default `site-studio`):

```bash
python3 scripts/build_pages.py                 # → site-studio/*.html
# (data refresh, if needed:)
python3 scripts/instagram_pull_account.py      # needs INSTAGRAM_ACCESS_TOKEN
python3 scripts/build_site_feed.py             # writes feed.json + reel covers
```

Real first-party data: 87 media · 33.1M views · 993K shares · 194K saves.
Full design rationale: `docs/superpowers/specs/2026-06-15-astory-website-v2-design.md`.
