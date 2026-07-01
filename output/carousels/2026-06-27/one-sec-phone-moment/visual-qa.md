# Visual QA

Status: `PROOF_FAILED_DIMENSION_GATE`

Two generated proof images exist:

- `proofs/slide-06-proof.png`
- `proofs/slide-06-proof-v2.png`

Both are rejected for final/proof approval because they are `1254 x 1254`, not native `1080 x 1080`.

Reference inputs used/loaded for the proof attempt:

- `config/references/identity/aachu/portrait-02.jpg`
- `config/references/identity/zuv/portrait-05.jpg`
- `config/references/identity/together/together-18.jpg`
- `config/references/identity/together/together-21.jpg`
- `config/references/style-lock/observational-intimacy-premium/contact-sheet.png`

Proof slide: slide 06.

Proof v2 visual notes:

- scene/action: PASS, shows Aachu showing the phone and Zuv turned toward her
- inactive phone: PASS, one face-down phone visible on table
- exact text: PASS by visual inspection
- paper tone: closer to PASS than v1, neutral enough for rough review
- dimensions: FAIL, `1254 x 1254`
- final/proof acceptance: FAIL

Accepted proof must pass:

- native `1080x1080`
- exact on-image text
- tiny bottom-right `@a.storyof.two`
- warm ivory paper, not yellow/parchment
- recognizable Aachu/Zuv identity
- one phone face-down and one shared viewing moment
- no readable phone UI
- no quote-card composition
