---
name: a-story-article
description: Turn an A Story of Two carousel package, source story, or lived love theme into a Substack article brief, outline, editorial gates, growth package, or publish package. Use for article, essay, newsletter, Substack, longform, article-from-carousel, or love-story-to-article requests; do not use for making the carousel itself.
---

# A Story Article

## Overview

Use this repo skill for the D-layer Substack love article workflow. It wraps the
existing Agentic OS `story_article` system instead of duplicating the long
article framework.

## Load First

1. `config/skill-systems.json` -> `story_article`
2. `config/skills/romance-story-selling-engine.md`
3. `config/skills/couple-substack-article-framework.md`
4. `config/rules/voice.md`
5. `config/rules/story-selling.md`

Use `venv/bin/python scripts/agentic_os.py skill-system story_article` for the
machine-readable workflow record.

## Operating Contract

- Check source integrity before drafting.
- Keep the article about a lived love theme, not generic relationship advice.
- Run Layer E to find the emotional obstacle, proof, reversal, and payoff.
- Preserve @a.storyof.two voice and taste.
- Produce the article brief, outline, editorial gates, growth package, and final
  publish package before calling it ready.
- Link to canonical rules and framework files instead of copying long guidance
  into the skill.

## Workflow

1. Identify the source package or story and preserve exact user-provided lines.
2. Load the `story_article` system and article framework.
3. Run the love-theme diagnosis before outlining.
4. Draft the article brief, outline, editorial gates, growth package, and
   publish package.
5. Validate source integrity, voice, structure, and growth package before
   calling the article ready.

## Useful Commands

```bash
make article CAROUSEL=output/carousels/YYYY-MM-DD/slug
venv/bin/python scripts/create_substack_article_package.py --carousel-dir output/carousels/YYYY-MM-DD/slug
venv/bin/python scripts/agentic_os.py skill-system story_article
```
