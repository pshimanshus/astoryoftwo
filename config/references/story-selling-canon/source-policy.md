# Story Selling Canon Source Policy

last_updated: 2026-05-18
owner: Layer E story-canon subsystem

## Purpose

The story-selling canon exists to extract reusable romance, relationship, scene,
and story-selling patterns for @a.storyof.two carousels and articles. The schema
file is the product: every source must be traceable, legally safe, and useful
without copying protected work into the repo.

## Required Source Fields

Every source in `source-register.json` must include:

- `id`
- `type`
- `title`
- `creator`
- `source_url`
- `license_status`
- `allowed_use`
- `ingestion_mode`
- `priority`
- `confidence`
- `scraped_at`

`allowed_use` must be a non-empty list. `confidence` must be between 0 and 1.
The validator normalizes IDs to lowercase slug form.

Allowed `allowed_use` values:

- `citation`
- `derived_patterns`
- `discovery_reference_only`
- `full_text_analysis`
- `ingestion_rules`
- `internal_research`
- `metadata_analysis`
- `short_quotes`
- `short_summary`
- `source_discovery`
- `visual_reference_review`

## Allowed Ingestion

- Public-domain books may be used for full-text analysis when sourced from
  Project Gutenberg robot-approved harvest/catalog paths, Internet Archive
  public-domain files, or another clearly licensed source.
- Open Library may be used through its APIs or bulk data for metadata,
  discovery, and links. Do not scrape Open Library HTML pages.
- Public-domain film pages and metadata may be used from Library of Congress,
  Wikidata, IMDb non-commercial datasets for internal use, and similar metadata
  sources whose terms allow the intended use.
- Modern craft articles and online story-selling frameworks may be stored as
  source cards: citation, URL, creator, short summary, tags, extraction notes,
  and abstracted lessons. Do not mirror the full article body.
- User-provided excerpts may be stored only when the user confirms they have
  rights to use them. Store the confirmation note with the source card.
- Homepage, tag-page, channel, broad site, API, dataset, and policy references
  are discovery/support records only until they are replaced with a specific
  reviewed URL. Use `discovery_reference_only`, `source_discovery`, or
  `ingestion_rules`; do not generate story patterns from them.

## Disallowed Ingestion

Hard bans:

- No full scraping or storage of modern copyrighted novels.
- No scraping or storage of paid craft books.
- No bulk copyrighted screenplays, including bulk scraping or storage of
  copyrighted screenplay text.
- No random PDF mirrors.
- No IMSDb or ScriptSlug bulk scraping.
- No Open Library HTML scraping.
- No review-page scraping, fan transcript scraping, or plot-page scraping from
  sites that do not clearly permit it.

When in doubt, store only a citation, link, short notes, and derived patterns.

`full_text_analysis` is allowed only for public-domain, licensed full-text, or
rights-confirmed records. Any license status containing copyright, paid,
unknown, unclear, review, metadata, terms, policy, API, dataset, platform,
site-reference, or video-reference language is blocked from full-text use.

## Quote And Storage Limits

- Public-domain sources can be quoted as needed for analysis, but extracts
  should remain purposeful and not become replacement editions.
- Modern articles, craft books, films, and screenplays should use short quotes
  only when necessary. Prefer paraphrase, source card notes, and derived
  concepts.
- Do not store modern full text, screenplay text, paid book chapters, or copied
  article mirrors in `corpus/story-canon/`.

## API And Terms Notes

- Project Gutenberg: use robot-approved harvest and catalog access. Avoid
  normal human pages for automated scraping.
- Open Library: use APIs for low-volume discovery and dumps for bulk work.
  HTML scraping is banned.
- IMDb datasets: internal, non-commercial metadata use only. Do not scrape IMDb
  webpages, reviews, or plot pages.
- TMDB: only use with API-key compliance and attribution if added later.
- Wikidata: metadata only unless a linked source has a clearer license for more.

## Citation Rules

Every derived pattern must carry source IDs and confidence. Source cards should
record title, creator, source URL, license status, allowed use, ingestion mode,
date accessed, and extraction notes. If a source is later contradicted or found
unsafe, lower confidence and supersede the record instead of silently deleting
it.
