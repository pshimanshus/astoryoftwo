BRAND ZONE: applies only when the brief includes a `brand:` field. Otherwise this rule is inert.

The brand product remains secondary to the love-story scene, but the brand name and core product cue must be clearly readable at phone-screen size.

Placement: front-facing or three-quarter product angle, enough product size, clean contrast, minimal occlusion. Product is part of the scene, not stuck on top of it.

HARD FAIL when brand integration is requested:
- brand name, logo wordmark, or product type not legible at phone-screen size
- product hidden behind scarves, hands, glare, folds, or clutter
- unrelated logos, labels, or random text added that were not requested
- disclosure language missing where required by Indian advertising regulations
- product placement that covers a face or core emotional gesture

Brand-label workflow: for tiny product packaging, illustrate the product body, placement, color, and scene integration first. If the brand/product wording is not legible from the model output alone, apply a controlled exact-label pass using `scripts/render_brand_product_labels.swift` so the final image preserves the watercolor-and-ink style while making the brand name and product type readable. This exception applies only to brand/product microtext — the slide's narrative ON-IMAGE TEXT still belongs in the illustration-generation prompt.
