---
name: a-story-article
description: Use when turning a carousel package or A Story of Two love story into a Substack article brief, outline, editorial gates, growth package, or publish package.
---

# A Story Article

Use this repo skill for the D-layer Substack love article workflow. It wraps the
existing Agentic OS `story_article` system.

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

## Useful Commands

```bash
make article CAROUSEL=output/carousels/YYYY-MM-DD/slug
venv/bin/python scripts/create_substack_article_package.py --carousel-dir output/carousels/YYYY-MM-DD/slug
venv/bin/python scripts/agentic_os.py skill-system story_article
```
