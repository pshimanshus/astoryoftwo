# Romance Story Selling Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [x]`) syntax for tracking.

**Goal:** Build a repo-native skill that converts legally sourced romance novels, films, screenwriting craft, and online story-selling research into concept processes for @a.storyof.two carousels and articles.

**Architecture:** Add a new Layer E story-canon subsystem that sits above the existing C-layer and D-layer. It ingests allowed sources into `corpus/story-canon/`, distills reusable patterns into `config/references/story-selling-canon/`, and exposes a concise operational skill at `config/skills/romance-story-selling-engine.md`.

**Tech Stack:** Python 3, existing `venv/bin/python`, JSON/Markdown artifacts, Project Gutenberg robot endpoints, Open Library APIs or dumps, Wikidata SPARQL/exports, Library of Congress public-domain film pages, manually curated URL manifests, repo-local Markdown skills.

---

## Non-Negotiable Source Policy

Do not scrape or store full copyrighted modern novels, paid craft books, or copyrighted screenplays. The skill should import:

- full text only from public-domain or clearly licensed sources;
- metadata from APIs whose terms allow the intended use;
- short notes, citations, and abstracted lessons from modern articles/books/films;
- user-provided notes or legally obtained excerpts when the user confirms they have rights;
- links and source cards for copyrighted works, not the full work.

Every source record must include `license_status`, `allowed_use`, `source_url`, `scraped_at`, and `confidence`.

## Source Map: What To Scrape From Where

### Public-domain romance and relationship novels

Use these for full-text analysis, scene maps, tropes, emotional reversals, dialogue restraint, misunderstandings, and payoff structures.

- Project Gutenberg robot harvest and catalog metadata:
  - `https://www.gutenberg.org/policy/robot_access.html`
  - scrape only through robot-approved harvest/catalog paths, not normal human pages.
  - seed authors: Jane Austen, Charlotte Bronte, Emily Bronte, Anne Bronte, Elizabeth Gaskell, George Eliot, Edith Wharton, Thomas Hardy, L. M. Montgomery, Shakespeare.
  - seed works: `Pride and Prejudice`, `Persuasion`, `Sense and Sensibility`, `Jane Eyre`, `Wuthering Heights`, `North and South`, `The Age of Innocence`, `Far from the Madding Crowd`, `Anne of Green Gables`, `Romeo and Juliet`.
- Open Library APIs or bulk data:
  - `https://openlibrary.org/developers/api`
  - use APIs for low-volume discovery and monthly dumps for bulk. Do not scrape Open Library HTML.
  - scrape fields: title, author, publish year, subjects, work key, edition count, full-text availability, links to IA/Gutenberg where present.
- Internet Archive/Open Library public-domain files:
  - use only items marked public-domain or otherwise legally downloadable.
  - scrape metadata and public text where license is clear.

### Film and screenplay learning

Use films for structure, scenes, emotional rhythm, and visual proof. Be strict with copyright.

- Library of Congress free-to-use National Film Registry:
  - `https://www.loc.gov/free-to-use/public-domain-films-from-the-national-film-registry`
  - scrape film list, metadata pages, public-domain videos/stills where available.
  - romance-relevant seed examples: `May Irwin Kiss`, `Within Our Gates`, early courtship/comedy shorts, and any public-domain romantic comedy or melodrama identified by metadata.
- Wikidata:
  - query for works with genre romance, romantic comedy, melodrama, courtship, marriage, love story, Indian romance, Bollywood romance.
  - scrape metadata only: title, year, country, genre, director, writer, cast, awards, adaptation source, public-domain status if present.
- IMDb non-commercial datasets:
  - `https://www.imdb.com/interfaces/`
  - use only if this remains internal/non-commercial. Store source terms in `source-policy.md`.
  - scrape title basics, ratings, genres, runtime, start year. Do not scrape reviews or plot pages.
- TMDB API:
  - use only with attribution and API-key compliance if selected later.
  - scrape metadata/popularity only, not copyrighted descriptions beyond allowed API use.
- Screenplays:
  - preferred: official award-season studio PDFs when terms allow personal analysis, or public-domain scripts.
  - disallowed by default: bulk scraping IMSDb, ScriptSlug, random PDF mirrors, or copyrighted screenplay repositories.
  - store abstract beat maps and citations, not screenplay text.

### Craft articles and concept-process references

Use these as reference cards, not full scraped article mirrors. Store citation, short summary, framework tags, and practical extraction.

- Story Grid Love Genre:
  - `https://storygrid.com/love-genre/`
  - extract: love as connection, hate-love value, moral failing, sacrifice, obligatory love-story movements.
- Save the Cat:
  - `https://savethecat.com/how-to-write-a-screenplay`
  - extract: 10 story types, 15 beats, transformation machine, Board-style planning.
- Pixar/Khan Academy storytelling:
  - `https://www.khanacademy.org/computing/pixar/storytelling`
  - extract: story spine, wants vs needs, obstacles, stakes, character arc, visual language.
- Reedsy romance guide:
  - `https://reedsy.com/blog/guide/romance/how-to-write-a-romance-novel/`
  - extract: niche, main couple, tropes, intimacy, secondary characters, happy ending.
- Writer's Digest romance conflict:
  - `https://www.writersdigest.com/whats-new/how-to-write-a-romance-novel-the-keys-to-conflict`
  - extract: external conflict must reflect internal emotional stakes.
- Jane Friedman love-scene restraint:
  - `https://janefriedman.com/write-love-scene/`
  - extract: restraint, subtext, delay, non-relationship problem, less explicit dialogue.
- Copyblogger story that sells:
  - `https://copyblogger.com/how-to-write-a-story/`
  - extract: hero story, headline, in-medias-res opening, customer/reader as protagonist.
- Animalz quality content:
  - `https://www.animalz.co/blog/quality-content`
  - extract: examine reader, simple explanation, strong angle, logical structure, earned trust.
- StoryBrand framework:
  - `https://storybrand.com/learn-the-framework/`
  - extract: customer as hero, clear message, guide, plan, call to action.
- Buffer/CXL/MarketingSherpa storytelling examples:
  - use as optional marketing examples after source review.
  - extract: story formulas, funnel placement, emotional storytelling, case studies, sequencing.

## Target Folder Structure

```text
agents/
  story-canon-orchestrator.md
  story-source-curator.md
  romance-arc-miner.md
  film-scene-miner.md
  online-story-selling-miner.md
  story-skill-reviewer.md

config/
  skills/
    romance-story-selling-engine.md
  references/
    story-selling-canon/
      source-policy.md
      source-register.json
      romance-novel-canon.md
      romance-film-canon.md
      screenplay-patterns.md
      story-selling-online.md
      a-story-of-two-adaptation.md
      concept-process-cards.md
      rubric.md

corpus/
  story-canon/
    raw/
      books/
      films/
      articles/
    parsed/
      books/
      films/
      articles/
    source-cards/

output/
  story-canon/
    YYYY-MM-DD/
      ingestion-report.md
      pattern-map.json
      concept-process-bank.json
      skill-build-review.md

scripts/
  build_story_source_register.py
  ingest_story_canon.py
  analyze_story_canon.py
  build_romance_story_selling_skill.py

tests/
  test_story_source_register.py
  test_story_canon_parser.py
  test_romance_story_selling_skill.py
```

## Artifact Contracts

### `source-register.json`

```json
{
  "sources": [
    {
      "id": "gutenberg-pride-and-prejudice",
      "type": "book",
      "title": "Pride and Prejudice",
      "creator": "Jane Austen",
      "source_url": "https://www.gutenberg.org/ebooks/1342",
      "license_status": "public_domain_us",
      "allowed_use": ["full_text_analysis", "short_quotes", "derived_patterns"],
      "ingestion_mode": "robot_harvest_or_manual_seed",
      "priority": 1,
      "confidence": 0.95
    }
  ]
}
```

### `concept-process-bank.json`

```json
{
  "processes": [
    {
      "id": "romantic-restraint-to-payoff",
      "source_patterns": ["jane-friedman-restraint", "austen-courtship-delay"],
      "best_for": ["carousel", "substack_article", "reel_script"],
      "steps": [
        "Name the feeling that cannot be said directly.",
        "Show a tiny behavior that leaks the feeling.",
        "Add an obstacle that makes confession costly.",
        "Let the partner respond through care, not explanation.",
        "Land the final line as emotional release."
      ],
      "a_story_of_two_filter": "Must preserve Aachu spark plus Zuv active steadiness.",
      "golden_theme_score_hint": ["universal_hook", "concrete_proof", "tender_thesis"]
    }
  ]
}
```

## Implementation Tasks

### Task 1: Add The Source Policy And Seed Register

**Files:**
- Create: `config/references/story-selling-canon/source-policy.md`
- Create: `config/references/story-selling-canon/source-register.json`
- Create: `scripts/build_story_source_register.py`
- Test: `tests/test_story_source_register.py`

- [x] Write `source-policy.md` with allowed/disallowed ingestion rules, citation rules, quote limits, API terms notes, and a hard ban on bulk copyrighted screenplay scraping.
- [x] Seed `source-register.json` with 40-60 sources across public-domain novels, public-domain film metadata, craft articles, and online story-selling frameworks.
- [x] Implement `build_story_source_register.py` to validate required fields and normalize source ids.
- [x] Add tests that fail when a source is missing `license_status`, `allowed_use`, `source_url`, or `confidence`.
- [x] Run `venv/bin/python -m pytest tests/test_story_source_register.py -v`.

### Task 2: Add Story Canon Ingestion

**Files:**
- Create: `scripts/ingest_story_canon.py`
- Create directories under `corpus/story-canon/`
- Test: `tests/test_story_canon_parser.py`

- [x] Implement safe ingestion modes:
  - `--source-register config/references/story-selling-canon/source-register.json`
  - `--type book|film|article|all`
  - `--dry-run`
  - `--max-sources N`
- [x] For Project Gutenberg, use approved robot/catalog paths or manually seeded text URLs only.
- [x] For Open Library, use APIs for low-volume metadata and require dumps for bulk work.
- [x] For craft articles, store URL, title, author when available, date when available, 150-250 word summary, process tags, and extraction notes. Do not store full article bodies.
- [x] For screenplays, store only metadata and derived beat maps unless the source is public domain or explicitly licensed.
- [x] Run `venv/bin/python scripts/ingest_story_canon.py --dry-run --max-sources 5`.

### Task 3: Analyze Books, Films, And Articles Into Patterns

**Files:**
- Create: `scripts/analyze_story_canon.py`
- Create: `config/references/story-selling-canon/romance-novel-canon.md`
- Create: `config/references/story-selling-canon/romance-film-canon.md`
- Create: `config/references/story-selling-canon/screenplay-patterns.md`
- Create: `config/references/story-selling-canon/story-selling-online.md`
- Output: `output/story-canon/YYYY-MM-DD/pattern-map.json`

- [x] Add deterministic extraction schemas:
  - `romance_arc`: meet, attraction, misread, intimacy, rupture, proof, choice, payoff.
  - `scene_engine`: want, obstacle, hidden feeling, reversal, visible behavior.
  - `sell_online_engine`: reader identity, desire, tension, proof, transformation, CTA.
  - `carousel_adapter`: universal hook, Aachu spark, proof beat, Zuv active care, tender thesis.
- [x] Generate pattern summaries without long quotes.
- [x] Add confidence scores and source ids to every pattern.
- [x] Run `venv/bin/python scripts/analyze_story_canon.py --source-register config/references/story-selling-canon/source-register.json`.

### Task 4: Build The Repo-Native Skill

**Files:**
- Create: `config/skills/romance-story-selling-engine.md`
- Create: `config/references/story-selling-canon/a-story-of-two-adaptation.md`
- Create: `config/references/story-selling-canon/concept-process-cards.md`
- Create: `config/references/story-selling-canon/rubric.md`
- Modify: `scripts/create_illustration_carousel.py`
- Modify: `scripts/create_substack_article_package.py`

- [x] Write `romance-story-selling-engine.md` as the lightweight entry skill.
- [x] Keep the skill body concise and point to references only when needed.
- [x] Add mandatory use cases:
  - creator asks for a carousel idea with a romantic/story lens;
  - creator wants a more cinematic or novelistic story;
  - creator asks why a love story feels flat;
  - creator asks for an article angle that can sell online without becoming generic.
- [x] Add the core process:
  - source memory check;
  - choose one concept-process card;
  - run golden-theme tournament;
  - score with both Golden Theme and Story-Selling rubrics;
  - adapt to C-layer or D-layer artifact contract.
- [x] Integrate the skill into carousel and article scripts as a pre-concept reference, without replacing the existing golden theme gate.

### Task 5: Add Agents For The E-Layer

**Files:**
- Create: `agents/story-canon-orchestrator.md`
- Create: `agents/story-source-curator.md`
- Create: `agents/romance-arc-miner.md`
- Create: `agents/film-scene-miner.md`
- Create: `agents/online-story-selling-miner.md`
- Create: `agents/story-skill-reviewer.md`

- [x] `story-source-curator`: verifies legality, source quality, and source diversity.
- [x] `romance-arc-miner`: extracts emotional arcs from public-domain books.
- [x] `film-scene-miner`: extracts visual scene patterns from public-domain films and metadata.
- [x] `online-story-selling-miner`: extracts story-to-conversion processes from craft/marketing articles.
- [x] `story-skill-reviewer`: rejects generic romance advice and verifies A Story of Two fit.
- [x] `story-canon-orchestrator`: synthesizes all outputs into skill references.

### Task 6: Add Rubrics And Gates

**Files:**
- Create: `config/references/story-selling-canon/rubric.md`
- Modify: `config/skills/golden-viral-carousel-theme.md`
- Modify: `config/skills/couple-substack-article-framework.md`

- [x] Add a 30-point Story-Selling rubric:
  - reader identity mirror: 0-5
  - romantic conflict/stakes: 0-5
  - specificity of proof: 0-5
  - emotional reversal: 0-5
  - visual scene clarity: 0-5
  - online share/save/sell potential: 0-5
- [x] Add hard fails:
  - no emotional obstacle;
  - only a pretty moment;
  - couple dynamic is generic;
  - Zuv has no active emotional role;
  - ending is a quote, not an earned payoff;
  - copyrighted source text is copied into artifacts.
- [x] Require a 28/30 Story-Selling score before the C-layer proceeds when this skill is invoked.

### Task 7: Validate With Golden Carousel Backtest

**Files:**
- Output: `output/story-canon/YYYY-MM-DD/gold-carousel-backtest.md`
- Modify tests as needed.

- [x] Backtest the skill against `wiki/themes/calm-enough-for-chaos.md`.
- [x] Backtest against `output/reports/2026-05-17-he-didnt-marry-peace-viral-theme-analysis.md`.
- [x] Confirm the skill rediscovers the same winning machine:
  - universal anti-ideal;
  - Aachu proof;
  - Zuv active steadiness;
  - tender acceptance thesis.
- [x] Run one new concept tournament using only the skill and verify the winner scores 28/30 or higher.

### Task 8: Document Usage In AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [x] Add Layer E above Layer D:
  - "Romance Story Selling Canon"
  - entry skill: `config/skills/romance-story-selling-engine.md`
  - references: `config/references/story-selling-canon/`
- [x] Add command guidance:
  - when the user asks to make a story more cinematic, novelistic, romantic, or better at selling online, use Layer E before C-layer or D-layer concepting.
- [x] Keep the golden theme as mandatory for carousel work.

## First Build Scope

The first implementation should avoid overbuilding. Use:

- 12 public-domain books;
- 10 public-domain or metadata-only romance films;
- 15 craft/story-selling articles;
- 20 concept-process cards;
- one backtest against the gold carousel;
- one fresh carousel idea tournament.

## Definition Of Done

- `config/skills/romance-story-selling-engine.md` exists and is usable by future `/story` and `/article` work.
- `config/references/story-selling-canon/` contains source policy, source register, pattern references, process cards, and rubric.
- No copyrighted full modern work is stored in the repo.
- Every reference claim has source ids and confidence.
- C-layer concepting can invoke the skill before the golden-theme tournament.
- D-layer articles can invoke the skill for article angles that feel emotionally strong and sellable online.
- Tests pass for source validation and parser behavior.
