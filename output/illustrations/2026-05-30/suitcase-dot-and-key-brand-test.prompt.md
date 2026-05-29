# Suitcase Dot & Key Brand Test

date: 2026-05-30
source_image: `/Users/himanshusharma/.codex/generated_images/019e6fc3-0bfc-7893-b34c-716f8430c13e/ig_005b0284f3751528016a19e1df63a08191a1b2abfea4e253f2.png`
saved_image: `output/illustrations/2026-05-30/suitcase-dot-and-key-brand-test.png`
exact_label_image: `output/illustrations/2026-05-30/suitcase-dot-and-key-brand-test-v3-exact-labels.png`
text_and_brand_image: `output/illustrations/2026-05-30/suitcase-dot-and-key-brand-test-v4-with-slide-text.png`
label_manifest: `output/illustrations/2026-05-30/suitcase-dot-and-key-brand-labels.json`
dimensions: `977x1610`

## Brand Cue

Dot & Key integration test using the attached product reference and official
brand/product cues:

- orange-and-white Vitamin C+E SPF 50+ sunscreen bottle
- blue-and-white barrier-repair moisturizer tube
- products appear as small packed travel skincare props around the suitcase
- product labels are the only intentional text inside the illustration
- V3 uses `scripts/render_brand_product_labels.swift` for exact readable
  product-label text after the watercolor product bodies are generated.

## Prompt

```text
Edit the attached A Story of Two suitcase-packing watercolor illustration.
Preserve the illustration almost exactly: same couple faces, same pose, same
bedroom setting, same suitcase, same warm ivory paper, same tall 977x1610-style
portrait composition, same airy clean upper negative space, no added narrative
text, no captions, no speech bubbles, no watermark.

Add a subtle brand-integration test using the attached Dot & Key product
reference image. Place two small travel skincare products naturally around the
suitcase/packing area, as if the couple is packing them:
1. A small rounded orange-and-white Dot & Key Vitamin C+E SPF 50+ sunscreen
   bottle near the front-right edge of the suitcase, partly tucked beside the
   cream toiletry pouch and scarf.
2. A small blue-and-white Dot & Key barrier-repair moisturizer tube lying near
   the tangled chargers or inside the open suitcase.

The products should be illustrated in the same watercolor-and-ink style, not
photorealistic and not pasted in. Keep the brand cue readable enough at phone
size: simple white "DOT & KEY" lettering on each product, with minimal small
product text like "SPF 50+" on the orange bottle and "Barrier Repair" on the
blue tube. Do not add any other text. Keep the products secondary and tasteful,
like real travel props inside the story, not an advertisement. Preserve all
faces, hands, anatomy, wardrobe, palette, and composition. Natural hands and
fingers, no extra limbs, no distorted faces, no random text, no logo except the
product labels explicitly requested.
```

## Label QA Rule

Brand integration is accepted only when the brand name and product type are
readable at phone-screen size. If image generation misspells or blurs package
microtext, keep the illustrated product body/placement and repair the label with
the controlled exact-label renderer.
