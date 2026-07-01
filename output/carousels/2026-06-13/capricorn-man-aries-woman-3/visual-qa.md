# Visual QA

Status: PROOF_READY_AWAITING_CREATOR_APPROVAL

## V2 Visual-System Proof

Status: AWAITING_CREATOR_APPROVAL

Candidate:

- Slide 01 v2 proof: `proofs/slide-01-v2-proof-candidate-colorfixed.png`
- Source generated image: `/Users/himanshusharma/.codex/generated_images/019ec20a-929c-7523-829a-eb09566a7cda/ig_067c2793d0bc74f1016a2da9a4b0dc8191af403f7f1a6c0ad1.png`
- Rejected uncorrected candidate: `proofs/slide-01-v2-proof-candidate.png`
- Rejected previous v2 attempt: `proofs/rejected/slide-01-v2-proof-rejected-tall-yellow-microtext.png`

V2 proof checks:

- [x] 4:5 composition: 1122x1402, ratio 0.8003
- [x] both faces visible
- [x] Aachu is not cropped into a torso/limb fragment
- [x] hand gesture reads as playful invitation, not restraint
- [x] Zuv is active through eye-line and expression
- [x] visual logic reads before text: he plans; she starts
- [x] no zodiac symbols, infographic, or quote-card layout
- [x] palette gate PASS: `paper RGB=(239,235,228); paper sat=0.037; paper B/G=0.970; yellow-band fraction=0.038`
- [ ] OCR gate not run: `easyocr` is not installed in the venv, so text verification is manual

Batch generation remains blocked until creator approves this v2 visual system.

Proof generated:

- Slide 07 Instagram post proof: `proofs/instagram-post-slide-07-proof.png`
- Rejected first attempt: `proofs/rejected/instagram-post-slide-07-proof-v1-yellow-wrong-ratio.png`

Proof checks:

- [x] native 4:5-ish Instagram proof output: 1122x1402
- [x] exact visible on-image text: `he acts calm.` / `but he loves the chaos.`
- [x] tiny `@a.storyof.two` brandmark bottom-right
- [x] Zuv is active through eye-line and softened attention
- [x] Aachu is expressive/playful without being mocked
- [x] no generic zodiac graphics or quote-card layout
- [x] palette gate PASS: `paper RGB=(242,237,227); paper sat=0.062; paper B/G=0.958; yellow-band fraction=0.042`
- [ ] OCR gate not run: `easyocr` is not installed in the venv, so text verification is manual for this proof

Creator proof approval is required before generating the rest of the carousel.

Before final approval, generate separate native 4:5 and native 9:16 slides from the prompt handoff and check:

- exact on-image text and line breaks;
- tiny @a.storyof.two brandmark bottom-right;
- Aachu/Zuv likeness from selected identity bundle;
- no generic zodiac graphics or quote-card layout;
- Zuv active in every frame;
- Aachu expressive but never mocked;
- 4:5 and 9:16 are generated separately, not resized from each other.
