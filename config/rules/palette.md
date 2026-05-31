PALETTE — the @a.storyof.two house illustration look. Default style is Observational Intimacy Premium watercolor-and-ink, locked by the creator on 2026-05-30. Reference bundle: `config/references/style-lock/observational-intimacy-premium/`. Original generation package: `output/illustrations/2026-05-30/observational-intimacy-premium/`.

PAPER
- Neutral warm ivory / off-white paper with visible paper grain.
- Paper region target: median RGB R ≥ 230, G ≥ 215, B ≥ 200; saturation < 0.18; blue/green ratio ≥ 0.85.
- Soft faded edges where the watercolor wash dissolves into the paper.
- The page must not read yellow, mustard, sepia, beige/tan, parchment, coffee-stained, or heavy cream on a phone screen. This is the most common rejection reason in this project; treat it as a hard fail, not a stylistic note.

WATERCOLOR AND INK
- Premium hand-painted watercolor-and-ink with fine graphite and ink contours.
- Soft transparent watercolor blooms; layered pigment; controlled crosshatching.
- Delicate sketch texture; visible hand-drawn linework; gentle imperfect organic edges.
- Hair drawn with layered curls and strands, not a flat black mass.
- Skin shaded with warm watercolor, not plastic smoothness.
- Clothing and props rendered with tactile detail: denim grain, fabric folds, scarf patterns, knit texture, leather straps, canvas bags, shoe stitching, wood grain, ceramic cups, small jewelry.

ACCENT PALETTE (use sparingly, always secondary to paper)
- muted denim blue
- soft navy
- off-white cotton
- terracotta red
- warm tan / camel (accent only, never the paper itself)
- gentle brown
- faded sage green
- peach blush
- dusty coral heart details

HARD FAIL: yellow — regenerate, do not accept
- yellow, mustard, sepia, parchment, tan, beige, cream-heavy, coffee-stained, ochre, golden cast, amber wash paper
- neon colors, oversaturated palette, harsh contrast, glossy digital finish
- photorealism
- generic AI watercolor (the over-soft, identityless look that any modern model defaults to without style references)
- UI / screenshot residue / platform watermarks
- random text, quote-card design, flat vector art, poster design
- hard rectangular scene box; backgrounds should fade into the cream paper, not sit in a frame
- heavy black outlines, harsh shadows
- anime, 3D render, children's cartoon style, hyperrealism

DETERMINISTIC ACCEPTANCE (used by pipeline/agentic/checks/palette.py)
- Paper region (brightest 15% of pixels by brightness): median R ≥ 230, median saturation < 0.18, median blue/green ratio ≥ 0.85.
- Yellow-band pixel fraction (hue 35–65°, saturation ≥ 0.35) across the full image stays below 0.05.
- These thresholds were calibrated against the 8 approved style-lock slides on 2026-05-31; do not edit casually.

ANTI-DRIFT NOTES (lessons from real rejections)
- 2026-05-30 phone-prank proof — paper read yellow/parchment, faces were generic. Hard fail. Do not use as reference for anything.
- When the model has only a text reference for style ("warm ivory watercolor"), it defaults to a goldenish wash. Text references alone are not enough. Pair the prompt with the style-lock bundle as an image reference whenever the generation path supports it.
- "Heavy cream" looks acceptable on the screen the model is rendering on but reads yellow at phone-screen viewing distance. Default to slightly cooler ivory rather than warmer.
