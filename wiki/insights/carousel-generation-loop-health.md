# Carousel Generation Loop Health

last_updated: 2026-05-16
confidence: 0.8
sources:
- config/carousel_style_contract.json
- docs/audits/2026-05-16-carousel-pipeline-structure-audit.md
- tests/test_illustration_carousel.py
- pipeline/stages/carousel_quality.py

---

## Insight

The C-layer must treat final carousel images as a separate hard gate from prompt
packages or local previews. A `/story` run is not ready until the package has
Aachu/Zuv identity references, clean generated art in `final/`, integrated final-image typography
exports when needed, and a visual QA checklist with no failed checks.

## Canonical Rule

`config/carousel_style_contract.json` is the source of truth for:

- Aachu/Zuv North Star
- character bible
- Product Unshipped-like soft flat vector style
- negative prompt
- brandmark
- integrated final-image typography policy
- content lanes

## Failure Memory

Older C-layer runs could pass despite missing final generated images. Going
forward, `REQ-FINAL-IMAGES-001` and `REQ-IDENTITY-001` must fail the final audit
until final image files and identity references are present.

## Visual QA Gate

Every final carousel requires `visual-qa.md` to check:

- storyboard-to-slide match
- Aachu face consistency
- Zuv face consistency
- soft flat illustration style
- readable integrated final-image typography
- final image existence
