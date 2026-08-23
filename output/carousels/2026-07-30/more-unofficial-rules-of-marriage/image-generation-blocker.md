# Image Generation Blocker

status: BLOCKED_VISUAL_QA
date: 2026-07-30
proof_slide: 5
locked_format: instagram_post
required_dimensions: 1080x1440

## What passed

- Exact nine-slide copy is locked.
- Instagram post is the only requested format.
- Event A copy-hidden storyboard review passed.
- Current pre-generation visual-story check passed.
- Current workflow doctor reached `handoff_ready`.
- Actual Aachu/Zuv identity references and a house-style reference were attached.
- The second candidate made the charger, shared turn, luggage ownership and comic consequence readable.

## Failed candidates

1. `/Users/himanshusharma/.codex/generated_images/019fa92a-ef8b-7b00-ad9e-9bd6d2526850/call_n5tnugjyxpihefFTgeJuOxTV.png`
   - observed dimensions: 1086x1448
   - story failure: both characters looked toward the viewer instead of the charger
   - blocking failure: Zuv carried a bag, weakening the “did not pack” contradiction

2. `/Users/himanshusharma/.codex/generated_images/019fa92a-ef8b-7b00-ad9e-9bd6d2526850/call_jqbR3beHCWeeEvHDa8zVnMUq.png`
   - observed dimensions: 1086x1448
   - story read: improved; both characters look at the charger and luggage ownership is clear
   - hard failure: wrong native dimensions repeated despite an explicit exact-pixel correction
   - identity limitation: mostly rear/profile faces are insufficient for a full likeness pass

3. `/Users/himanshusharma/.codex/generated_images/019fb39f-1717-7370-b301-0d7d51b9bab5/exec-103fd6ca-f9b1-48af-b737-eef4ca66922e.png`
   - observed dimensions: 1086x1448
   - text and brandmark: present and readable
   - story improvement: the forgotten charger is visibly plugged in inside the home
   - story failure: Zuv carries a large travel bag, weakening the locked “person who did not pack” contradiction
   - hard failure: wrong native dimensions repeated despite the active compiled prompt requiring exactly 1080x1440

## Decision

Do not package, resize, crop, pad, stretch or promote any candidate. Do not
continue to the remaining slides until a proof is generated natively at exactly
1080x1440 and passes identity, anatomy/entity/spatial, exact-text, style and
image-first story review.
