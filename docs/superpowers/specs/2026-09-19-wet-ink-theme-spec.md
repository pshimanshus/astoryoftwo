# Wet Ink — app theme spec

Date: 2026-09-19 · Target: `app/` · Source: run `wf_0abb22e4-1dd`, 13 agents, 88 research findings.

## Chosen

Wet Ink — the one-sheet paper-physics theme. Grafted in: (a) The Second Drum's two-plate overprint beat, where drum one completes the image in --ink alone and only THEN drum two lays --accent over it misregistered, with a macro hold on the overlap; (b) The Second Drum's rule that the rating is physically stamped onto the artefact and travels with it to send; (c) The Tunnel Book's authored-still-as-first-paint, where the same WebP that is the reduced-motion fallback is also every user's first painted frame, so the fallback path is exercised on every session and can never silently rot; (d) The Tunnel Book's review rule that nothing in the flow may be expressible ONLY in 3D.

## Rationale

WHY WET INK WINS FOR THIS BRAND AND THIS CREATOR.

The decisive fact is asset dependency, and it is not close. The Tunnel Book's own spec concedes its identity "rests on two illustrated cut-outs that do not exist yet, and no shader can substitute for them" — a team would spend two weeks staring at grey rectangles unable to tell whether the idea is beautiful or embarrassing. The Second Drum concedes a wrong *object* is recognisably wrong, that "a grey under-modelled press reads instantly as a Blender starter file," and that its poster — a render of that same model — is the first thing anyone sees. Both concepts therefore require a commissioned artist before a single line of WebGL can be evaluated. This is a solo prototype on a 390px frame. A theme whose quality gate is "did the illustrator deliver" is not shippable here.

Wet Ink is the only one of the three whose 3D is *generated rather than modelled*. The sheet is a subdivided plane, the fibre is a CC0 normal map, the ink is a solve, the buckle is eight lines of vertex shader. Every single thing a developer can iterate alone, at 2am, without a Blender file. That is the difference between a 4-week estimate and a 4-week estimate plus an unbounded art dependency.

On brand-truth it also simply wins. @a.storyof.two is warm paper, ink, handwriting. Wet Ink's central material IS ink on paper — the brand mark is the medium. The Tunnel Book is a lit room with dust in it, which is beautiful and has been Awwwards' house style since 2019; a depth-separated diorama with rack focus and volumetric shaft is *exactly* the anonymous work the brief forbids the moment you remove the two cut-outs, and the cut-outs are the part that does not exist. The Second Drum is a machine, and a machine is the wrong emotional register for a product whose copy says "no downloads — this is meant to be given, not saved."

On holding across nine screens, Wet Ink holds by construction: nine steps are nine states of one sheet, and there is no screen where the concept goes quiet. The Tunnel Book admits the opposite in its own words — "the payoff is fully realised on exactly three screens" and five of nine are forms that "do not want to be in a room." The Second Drum holds structurally (nine stations on a rail) but each station needs its own modelled prop.

And the killer argument against The Second Drum is the one it makes itself, which I want on the record because it is the most honest paragraph in all three specs: *the machine is a lie about what the app does.* `PrintingScreen.tsx` is a `setTimeout` over `PHASE_TIMINGS` and `deriveStoryBeats` is a two-branch template in `src/services/fakeGeneration.ts`. Fifteen seconds of registered, two-pass mechanical theatre over that asks the user to believe in a process that is not happening — in an app whose voice is unusually, deliberately honest. Wet Ink has no such problem: ink wicking into fibre and drying is *literally what the GPU is doing*. It claims no process it does not have. That distinction is worth more to this brand than any shader.

WHAT I REJECTED FROM EACH LOSER.

From The Tunnel Book I rejected: the nine camera stations (a room that sways when a user oscillates between hello and photos to settle on names is worse than no camera, which the spec itself flags as its third weakness, worst exactly where people hesitate); the volumetric light shaft and 400 dust motes (this is the god-ray demo the brief names, and it belongs to no one); the per-layer rack focus across five depths (12M texture fetches/frame at dpr 2 is the single largest fill-rate risk in any of the three specs, spent on an effect nobody names); and the two illustrated figure cut-outs as a hard dependency.

From The Second Drum I rejected: the press itself, the wooden desk, the brass crank, the two mugs and the paper-path lever. All of it is modelled geometry, all of it is skeuomorphic fiction, and the mugs-move-based-on-your-answer beat — while genuinely lovely — is the app performing intimacy rather than producing it. I also rejected its dark `--desk #15110d` scene: turning the whole frame dark to make brass read is the moment this brand stops being paper.

WHAT I CUT FROM WET INK ITSELF, because its self-declared weakness is real and I am acting on it rather than defending it. Its author is right that fidelity nobody can see at thumb scale is burned budget. So: the 1.8x wick anisotropy stays as two uniforms but gets ZERO tuning budget and is not a reviewable feature; the tear's fibre whiskers, the burnish roughness delta on the fold crease, and the deboss rim ridge on HelloScreen's chips are all cut as imperceptible at 390px; the reveal depth-map parallax is cut outright, because at the sub-2% displacement that keeps it tasteful it is invisible, and above it, it is the 2018 fake-3D-photo trick — the residual cockle raking across the finished carousel is a stronger and cheaper payoff and it is the concept's own thesis; and DeviceOrientation tilt is cut across every screen, because iOS requires a gesture-gated `requestPermission()` modal that would sit in the middle of this app's quietest moments, and a slow autonomous 9s light-azimuth drift buys the same raking read for free.

Net: the innovation budget concentrates on the two moments the user is actually looking at the paper — the record screen's live wet ink, and the printing→reveal page turn — and everything else is the same material behaving consistently for near-zero marginal cost.

## Design principles

- ONE SHEET, NINE STATES. The app is not nine screens, it is one sheet of paper that is never cut and never cross-faded. Every step change is that sheet changing state. This is why AnimatePresence stops using mode="wait" with an opacity+y crossfade: the sheet persists across the step boundary and only its contents change. If a proposed treatment requires the sheet to disappear and a new one to appear, it is wrong by definition.
- PAPER REMEMBERS. Every mark is permanent within a session. Ink dries and stays. A pressed impression never lifts — de-selecting a HelloScreen chip or lowering a star rating leaves a blind emboss with no ink, because you cannot un-press paper. 18% of the record screen's wetness buckle survives drying and is still raking across the finished carousel four screens later. This is the concept in one rule, it is deliberately unforgiving, and it will generate at least one piece of feedback that reads as a bug report. Ship it anyway.
- THE CANVAS IS THE SURFACE, THE DOM IS EVERYTHING YOU READ OR TOUCH. No text, no button, no image, no PhoneFrame, no HandDrawnArrow, no MicButton chrome is ever rendered in WebGL. Caveat and Georgia stay crisp and selectable, every touch target stays a real <button> with its aria-label, and the canvas is aria-hidden for its entire life. The WebGL layer sits behind the UI at z-index 0 and is decoration of the substrate, never of the interface.
- GRAIN BELONGS TO THE SHEET AND THE PRINTED ARTEFACT, NEVER TO CONTROLS. MicButton, the Carousel chrome, the star row, the HelloScreen inputs and the share-target buttons stay clean flat --paper/--ink/--accent. The moment paper texture creeps onto a control, the app reads as a themed skin rather than as a thing made of paper.
- NOTHING IN THE FLOW IS EXPRESSIBLE ONLY IN 3D. Every piece of state carried by the canvas is ALSO carried by DOM the user can read: the photo selection by its accent outline and count, the recording by the Caveat seconds counter, the printing progress by its phase copy, the rating by the star fill, the send by the target list. Strip the canvas entirely and the app is exactly as usable and exactly as legible. This is enforced in review, per screen, as a yes/no question.
- NO EMISSIVE, NO BLOOM, NO ENVIRONMENT, NO NEW COLOUR. Nothing in this app emits light — emissive is 0.0 everywhere, not 1.0. No drei <Environment>, because reflections turn paper into plastic. Exactly one soft key at 14° elevation. Every colour a shader or material receives is one of the seven existing tokens or a stated derivation of them, and shadow colour tints to --paper-shadow, never to grey.
- FIDELITY IS SPENT WHERE THE EYE IS. Budget goes to the record screen and the printing→reveal turn, because that is where the user is looking at paper rather than at copy or at their own photos. Detail that is only legible above thumb scale gets zero tuning time and is not a reviewable feature.

## Motion system

THE GRAMMAR, not a list of durations.

Every motion in this app answers one question: what is happening to the sheet? There are exactly four verbs, and every animation in the codebase must be one of them. If a proposed motion is not one of these four, it does not ship.

1. PRESS — something makes contact with paper. --dur-press (200ms) on --ease-press, zero bounce, no rebound. Paper does not spring back. This covers: the landing + button (which presses INTO the sheet 0.6mm rather than scaling — buttons on paper do not shrink, paper yields), the HelloScreen chip deboss, every star stamp, the send button, the fold burnish, the postmark. `whileTap={{ scale: 0.95 }}` is deleted everywhere it currently appears (src/screens/SendScreen.tsx, src/screens/LandingScreen.tsx) and replaced with the press.

2. SETTLE — something with mass comes to rest on or with the sheet. paperSettle spring (visualDuration 0.50, bounce 0.12). Paper has mass and almost no bounce. This covers: the + button rise, photos landing on the sheet, the deboss rim, the letter fold's 4° overshoot, the MicButton entrance.

3. TRAVEL — an object moves across the sheet without changing state. cardTravel spring (visualDuration 0.45, bounce 0.08). This covers: layoutId transitions from the photo grid to the review strip, carousel slides sliding off the pile, the share-target cascade.

4. DRY — a physical process runs to completion on a diffusion curve. --dur-dry (1800ms) on --ease-dry (0.16, 0.9, 0.3, 1) — fast then very slow, because evaporation is diffusion-limited and a symmetric ease is a lie about the physics. This covers: ink drying, wetness decay, the cockle relaxing to its 18% residual, the ink draining from a downgraded star.

CHOREOGRAPHY RULES, enforced in review:

Asymmetry is mandatory where a hand is implied. Erasing is faster than drawing (the grease-pencil selection mark draws in 0.22s and erases in 0.14s). A plate drops, it does not ease — the accent misregistration slams in on --ease-press 200ms while the dot ramp beneath it runs 3.5s on --ease-soft. A stamp lands hard with no settle; the ink that fills it trails by 60ms and takes 180ms on --ease-dry.

Stagger: step <= 0.08s, total cascade <= 0.40s, and `from` varies per screen deliberately. RateScreen uses stagger(0.055, { from: 'center' }) so the rating blooms outward from the middle star instead of sweeping left-to-right like a form — 0.22s total for five. Everywhere else is from: 'first'.

Two animations never describe the same event. src/screens/RevealScreen.tsx currently opens with `initial={{ opacity: 0, scale: 0.96 }}` over 0.6s — that is deleted, because the page turn IS the entrance and doing both is the double-animation smell.

Infinite loops are banned. Both existing ones go: src/screens/PrintingScreen.tsx's `animate={{ opacity: [0.4, 1, 0.4] }}` becomes a 0.5Hz dot-density breath in the halftone itself (as if the ink supply pulses), and src/components/MicButton.tsx's `scale: [1, 1.08, 1]` is deleted because the pulse moves into the ink, where amplitude already lives — the button just switches to --accent over 200ms. This is not only a taste call: `reducedMotion="user"` deliberately preserves opacity animations, so the printing pulse would survive the accessibility fix. Deleting them removes the bug at the source rather than guarding it.

The step transition itself changes character. src/App.tsx's `{ opacity: 0, y: 12 } → { opacity: 1, y: 0 }` at a hardcoded 0.35s is replaced by opacity-only at --dur-screen on --ease-soft, with AnimatePresence switching from mode="wait" to mode="popLayout" inside a LayoutGroup so shared elements can travel (mode="wait" forbids them by definition). The sheet does not fade — it persists. Only what is on it changes. That is the whole system in one diff.

## tokens.css

```css
:root {
  /* ─────────────────────────────────────────────────────────────
     EXISTING — unchanged. This block is the only colour authority
     for the app surface. No shader uniform, no material, no vendor
     demo palette invents a colour; everything below is one of these
     seven or a stated derivation of them.
     ───────────────────────────────────────────────────────────── */
  --paper: #f6f1e7;
  --paper-shadow: #e7dfcf;
  --ink: #2b2622;
  --ink-soft: #6b6258;
  --accent: #c2462f;        /* warm red used sparingly */
  --hairline: #d8cfbd;

  --font-hand: 'Caveat', 'Bradley Hand', cursive;
  --font-body: 'Georgia', 'Times New Roman', serif;

  --space: 16px;
  --radius: 20px;
  --ease-soft: cubic-bezier(0.22, 1, 0.36, 1);

  /* ─────────────────────────────────────────────────────────────
     MOTION SCALE
     tokens.css previously had exactly one motion token and
     src/App.tsx did not use it — it hardcodes duration: 0.35.
     Magnitudes anchored on M3's published ladder.
     ───────────────────────────────────────────────────────────── */
  --dur-press:    200ms;  /* M3 short4  — a finger on paper */
  --dur-screen:   400ms;  /* M3 medium4 — a step change */
  --dur-turn:     900ms;  /* the page turn; spring-driven, this is the visualDuration target */
  --dur-dry:     1800ms;  /* ink evaporation */
  --dur-ambient: 9000ms;  /* light-azimuth drift, idle breathe */

  --ease-press: cubic-bezier(0.3, 0, 0.2, 1);    /* fast in, no overshoot — paper does not rebound */
  --ease-dry:   cubic-bezier(0.16, 0.9, 0.3, 1); /* fast then very slow — evaporation is diffusion-limited */

  /* Springs do NOT live in CSS. See src/styles/motion.ts:
       paperSettle { spring, visualDuration 0.50, bounce 0.12 }
       cardTravel  { spring, visualDuration 0.45, bounce 0.08 }
       pageTurn    { spring, visualDuration 0.62, bounce 0.14 }
     House rules: bounce never above 0.15 (higher reads as a rubber
     toy, not paper); stagger step <= 0.08s; total cascade <= 0.40s;
     stagger `from` is 'center' on RateScreen and 'first' elsewhere. */

  /* ─────────────────────────────────────────────────────────────
     DEPTH SCALE — millimetres of real sheet, not pixels.
     Read by JS and converted to world units at one place
     (src/webgl/sheet.ts). Stated in mm so the numbers cannot drift.
     ───────────────────────────────────────────────────────────── */
  --z-rest:    0mm;
  --z-lift:    0.4mm;   /* a photo corner off the sheet */
  --z-deboss: -0.5mm;   /* a stamped star */
  --z-cockle:  0.9mm;   /* peak buckle at full wetness */
  --z-fold:    2.4mm;   /* three-fold letter thickness */

  --cockle-residual: 0.18;  /* what survives drying. the concept in one number. */

  /* ─────────────────────────────────────────────────────────────
     LIGHT + MATERIAL — one soft key, raking. No environment map,
     no second light, no emissive anywhere in this app.
     ───────────────────────────────────────────────────────────── */
  --light-elevation: 14deg;   /* RAKING. this single number is why fibre is visible at all. */
  --light-azimuth:  312deg;   /* drifts +/-6deg over --dur-ambient. no device tilt, ever. */
  --paper-roughness: 0.92;

  /* ─────────────────────────────────────────────────────────────
     INK PHYSICS — Beer-Lambert absorption over the paper substrate,
     so overlapping inks mix like pigment instead of blurring.
     ───────────────────────────────────────────────────────────── */
  --grain-direction: 12deg;  /* machine direction. shared by ink wick AND cockle. the spine. */
  --wick-anisotropy: 1.8;    /* along-grain : cross-grain. zero tuning budget — see principles. */
  --ink-sigma:    2.9;       /* Beer-Lambert k for --ink */
  --accent-sigma: 2.2;       /* --accent is a thinner ink */

  /* ─────────────────────────────────────────────────────────────
     PRINT — two plates, and the misregistration between them is
     the entire soul of riso. Three plates is the cap; four-plate
     CMYK is out of budget at 390x844.
     ───────────────────────────────────────────────────────────── */
  --riso-angle-ink:    105deg;
  --riso-angle-accent:  45deg;
  --misregister: 1.7px;   /* drum two offset from drum one; lands hard, never eases */
  --dither-grid: 3;       /* 2-4. larger tips into Game Boy. */

  /* ─────────────────────────────────────────────────────────────
     THE ONLY THREE NEW COLOUR VALUES. All three are derivations of
     existing tokens observed under a stated condition, not new
     brand colours.
     ───────────────────────────────────────────────────────────── */
  --ink-wet:       #1c1814;  /* --ink while wet. dries TO --ink over --dur-dry. */
  --paper-backlit: #fbf3e2;  /* --paper with light behind it, at the page-turn apex.
                                also the existing top stop of PaperBackground's gradient. */
  --overprint:     #241b19;  /* Beer-Lambert product of --ink over --accent. exists only
                                where both plates touched the same fibre. the signature tone. */
}
```

## WebGL architecture

ONE CANVAS, MOUNTED OUTSIDE AnimatePresence, NEVER UNMOUNTED.

Current tree (src/App.tsx): SessionProvider > FlowProvider > PhoneFrame > PaperBackground > CurrentScreen (which owns the AnimatePresence). The diff is small and surgical:

  <PhoneFrame>
    <PaperBackground>                                  {/* baked WebP, no longer a radial gradient */}
      <Suspense fallback={null}><SheetLazy /></Suspense>  {/* inset:0, z-index:0, aria-hidden */}
      <MotionConfig reducedMotion="user">
        <LayoutGroup><CurrentScreen /></LayoutGroup>      {/* z-index:1, transparent backgrounds */}
      </MotionConfig>
    </PaperBackground>
  </PhoneFrame>

The canvas sits BEHIND the DOM UI and outside AnimatePresence, so the nine step changes never unmount it and Safari never exhausts WebGL contexts. Every screen in src/screens/ is already background-free except the disclaimer card, so the DOM diff is close to nothing.

NO drei <View> / <View.Port>. View exists to scissor one canvas into several independently-tracked DOM regions. This design has exactly one thing on screen — a sheet that always fills the frame inside a fixed 390x844 PhoneFrame. Dropping View removes per-frame getBoundingClientRect entirely and sidesteps drei issue #2471 (single View.Port, no z-interleaving) rather than working around it. The permitted drei surface therefore shrinks to five imports, written as a comment at the top of src/webgl/Sheet.tsx and enforced in review: useTexture, ContactShadows, PerformanceMonitor, AdaptiveDpr, Decal. Nothing else.

THE SHEET SUBSCRIBES TO FLOW ITSELF. src/webgl/useSheetState.ts reads useFlow() and drives the sheet's uniforms directly, so a step change never remounts anything 3D. Because FlowProvider is a plain useState (src/flow/FlowProvider.tsx), no change is needed there; the sheet just consumes the same context.

FILES:
  src/webgl/Sheet.tsx          the single <Canvas>, the sheet mesh, the key light
  src/webgl/paperMaterial.ts   three-custom-shader-material patch over MeshStandardMaterial:
                               cockle vertex displacement, deboss impressions, bend, tear alpha-clip
  src/webgl/inkSolve.ts        ping-ponged velocity/ink targets, record-only, disposed on leave
  src/webgl/passes.ts          the ordered-Bayer dither and the two-plate halftone — hand-rolled,
                               mutually exclusive, never stacked
  src/webgl/useSheetState.ts   reads useFlow(), sets uniforms, calls invalidate()
  src/webgl/perf.ts            dpr stepping, disposal registry
  src/styles/motion.ts         the spring scale + house rules as comments
  public/textures/paper-base.webp    baked offline from @paper-design/shaders-react
  public/textures/paper-nrm.webp     Poly Haven CC0 paper-card, 512², normal in RG + roughness in B

FRAMELOOP. frameloop="demand" with invalidate() wired into flow transitions. Six of nine screens render ZERO frames at rest. frameloop="always" is switched on for exactly three windows: the record screen's live solve (gated on recording === true), the printing dot ramp plus the plate-two drop, and the 900ms page turn. That architectural choice — not shader micro-optimisation — is what keeps the phone cool: the GPU is awake for roughly 20 seconds across a 90-second session. Canvas props: dpr={[1,2]} (a 3x phone otherwise renders 9x the pixels), gl={{ antialias: false, alpha: true, powerPreference: 'low-power' }}, <PerformanceMonitor> stepping dpr down on decline, <AdaptiveDpr>.

FULL-SCREEN PASS BUDGET: exactly one at any moment, ever. Dither runs on review; halftone REPLACES it on printing. No @react-three/postprocessing — +113KB gzip to obtain precisely the bloom/DOF/chromatic-aberration the brief names as the failure mode.

LAZY LOADING AND BUNDLE. const Sheet = lazy(() => import('./webgl/Sheet')). The entry chunk stays DOM-only — react, react-dom, framer-motion, the nine screens — at today's measured 88,579 B gzip, ±2 KB after the framer-motion 11→13 bump. The 3D chunk is fetched on the + tap at the end of LandingScreen and lands during HelloScreen's 8–20s typing dwell. Measure it at ~172 KB gzip, not the ~60 KB a naive three-only estimate suggests: @react-three/fiber does `import * as THREE` (node_modules/@react-three/fiber/dist/react-three-fiber.esm.js line 4), which defeats tree-shaking, so if R3F is in the graph you ship all of three. There is no partial version of that cost, only a deferred one. CI gate: the entry chunk must stay under 92 KB gzip or the build fails.

PINNED PACKAGES (React 18 is a hard ceiling — fiber@8.18.0 peers react ">=18 <19", drei@9.122.0 peers react "^18" + fiber "^8"; fiber@9/drei@10 demand React 19 and ERESOLVE against this app's react ^18.3.1, and every current R3F doc snippet assumes v9):
  three@0.180.0  @react-three/fiber@8.18.0  @react-three/drei@9.122.0
  three-custom-shader-material@6.4.0   (4 KB gzip; keeps MeshStandardMaterial's lighting and
                                        shadows so a bent or buckled sheet still takes its
                                        contact shadow — the entire reason it reads as paper)
  framer-motion@^13.4.0                (upgrade in place; v13's only breaking change,
                                        @emotion/is-prop-valid, is a no-op in a 100% inline-styled app)
  @paper-design/shaders-react@0.0.81   (pinned exactly, BUILD TIME ONLY — see below)

@paper-design/shaders-react is used to BAKE, not at runtime. <PaperTexture creasedPreset> renders once via a node script to public/textures/paper-base.webp. Rationale: once three is in the graph, a second WebGL library means a second context, which is precisely the Safari context-exhaustion failure the constraints name. Baking keeps the visual and ships zero runtime bytes. (If the team wants a paper upgrade before any canvas work lands, keep it at runtime for that interim and swap to the bake when three arrives.)

DISPOSAL IS THE LOAD-BEARING DISCIPLINE. AnimatePresence unmounts a screen on every one of the nine steps. The canvas survives, but the fluid targets, the photo quads and the impression buffers churn. Every geometry, material, texture and render target registers with src/webgl/perf.ts and is disposed explicitly; the merge gate is that renderer.info.memory returns to its step-1 baseline after a full nine-step run. Undisposed objects are how a phone prototype dies on screen seven.

VRAM, as designed: normal+roughness 512² 1.0 MB, paper base 0.2 MB, ink RT 512² RG16F ping-pong 2.0 MB, velocity 256² RG16F ping-pong 0.5 MB. Peak 3.7 MB for the ~2.5s of record→printing, 1.5 MB steady state once the fluid targets are disposed.

VERIFICATION IS TOOLING, NOT JUDGEMENT. Fix the currently-failing Playwright MCP plugin config rather than installing a second browser tool — leaving it broken is itself the risk, because it is the enforcement mechanism for both hard gates: browser_resize to exactly 390x844, browser_emulate_media for prefers-reduced-motion, browser_evaluate for a rAF FPS counter and renderer.info reads. Add threejs-devtools-mcp (dev-only; verify the bridge is absent from `npm run build` output) for live draw calls, texture memory and undisposed-object diagnostics — the leak tooling is the part that matters. Two per-skill installs only, so no showreel sibling lands in .claude/skills/ waiting to auto-trigger: `npx skills add iart-ai/webgl-animation-skills --skill shader-glsl` (fbm/domain-warp for the wick edge and the tear path) and `npx skills add iart-ai/web-animation-skills --skill accessible-animation` (the tiering below).

## Reduced motion

FIRST, FIX THE FLOOR. It is broken today and this is a live accessibility bug independent of any theme.

src/styles/global.css line 12 is `* { animation-duration: 0.001ms !important; transition-duration: 0.001ms !important; }`. That touches CSS animation and CSS transition and nothing else. framer-motion drives inline styles from rAF and ignores it completely — so today, for a user who explicitly asked for less motion, src/App.tsx's 0.35s opacity+y crossfade runs nine times at full amplitude, src/screens/PrintingScreen.tsx's `animate={{ opacity: [0.4,1,0.4] }}` pulses forever, and src/components/MicButton.tsx's `scale: [1,1.08,1]` pulses forever. Replace that rule with `<MotionConfig reducedMotion="user">` wrapping the tree in src/App.tsx. Do NOT swap it for the `0s !important` variant — that breaks any JS waiting on transitionend.

THE TRAP: reducedMotion="user" deliberately PRESERVES opacity animations. So the printing pulse and any other opacity loop survive the fix. In this theme both infinite loops are deleted outright rather than guarded — the printing pulse becomes a halftone dot-density breath and the mic pulse moves into the ink — which removes the bug at its source. Any future infinite opacity animation needs an explicit useReducedMotion() branch, and that is written into src/styles/motion.ts as a comment.

THREE TIERS, and the top one is a genuine upgrade over what ships today, not a shell.

TIER 1 — prefers-reduced-motion: reduce. NO CANVAS IS EVER MOUNTED. The lazy chunk is never requested, so this user's entry bundle is unchanged at 88,579 B gzip and their time-to-interactive is the best of any tier. The accessible path is the fast path, which is the correct relationship and almost never the one a WebGL theme delivers.

  PaperBackground renders /public/textures/paper-base.webp — real fibre and crumple, strictly better paper than today's CSS radial gradient. CRUCIALLY, grafted from The Tunnel Book: that same WebP is also the first-paint image for EVERY user on landing, on every tier. So the fallback path is exercised on every single session and can never silently rot, and on a WebGL context-creation failure there is literally nothing to swap in — the correct image is already in the DOM underneath.

  Screen transitions become opacity-only at 200ms. Information is NOT removed, only motion:
    - RecordScreen shows a static ink stain that grows in discrete steps at 1s intervals. That is a state change communicating "we are hearing you", not an animation.
    - PrintingScreen shows its three phases as three static plate states at the existing PHASE_TIMINGS boundaries — including the misregistered overprint, which is perfectly legible in a still — plus a text progress line with aria-live, so the user still knows where they are in a 15-second wait. No pulse, no spinner, no infinite anything.
    - RevealScreen is a crossfade; the Carousel keeps its existing drag-to-swipe with a plain image swap.
    - RateScreen stars fill instantly in --accent and STILL bloom from centre at 0ms stagger — order is preserved, only duration goes to zero.
    - SendScreen shows the folded letter as a still.
  Nothing is unreachable and nothing is unexplained.

TIER 2 — the canvas mounts but the device cannot carry the simulation (no WebGL2, no EXT_color_buffer_half_float, or PerformanceMonitor reports sustained decline; this tier can be entered live, mid-run, without a reload). Everything structural survives and only the simulation is swapped for its recording: the fluid solve is replaced by a pre-baked 24-frame ink-bloom sequence in one 2048² WebP atlas (~180 KB, fetched only on this tier) with the correct anisotropic lozenge rendered offline, so the wick still looks right — it just is not solved live. Cockle amplitude halves to 0.45mm, dpr pins to 1, the halftone drops to a single plate (losing misregistration, keeping the dot ramp). The page turn, deboss, tear and fold all stay: they are vertex work, which is cheap, and they are the load-bearing motions.

TIER 3 — full, as specified.

THE RULE THAT MAKES THE FALLBACK GOOD RATHER THAN MERELY PRESENT, and it is checkable per screen in review: nothing in the flow is expressible ONLY in 3D. The photo selection is carried by its DOM outline and count; the recording by the Caveat seconds counter; the printing progress by its phase copy; the rating by the star fill; the send by the target list. Strip the canvas and the app is exactly as usable and exactly as legible — it is simply a story told on a still sheet instead of a live one. The canvas is aria-hidden throughout and every word lives in DOM, so screen-reader users are unaffected on every tier.

TIERING IS TESTED, NOT ASSUMED. Playwright browser_emulate_media with prefers-reduced-motion: reduce at 390x844, asserting no resource matching /three|fiber/ was ever fetched. Plus a vitest case that mocks matchMedia and asserts the lazy import is never called.

## Screens

### landing — 'say your story, get it illustrated', ink + button, 'before you begin' link — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/LandingScreen.tsx`

**Visual.** ZERO WebGL. This screen must never pay for the 3D chunk. The sheet arrives folded in three, letter-fold, creases painted into the baked texture — three DOM panels over /public/textures/paper-base.webp (390x844@2x, ~58KB, baked offline from @paper-design/shaders-react <PaperTexture creasedPreset>). The + button sits on the top panel. HandDrawnArrow's stroked path is replaced by a variable-width FILLED outline path revealed by a sweeping clipPath, so the line has real nib pressure — thin at entry, swelling through the curve, thin at release. The 'before you begin' disclaimer overlay keeps its existing scrim; its card is the same folded paper, not flat --paper.

**Motion.** Entrance: arrow draws over 1.1s, pathLength 0→1 on --ease-soft with a 0.18s dwell at 85% (the hand slowing before the arrowhead); + button rises 10px on paperSettle 120ms later. Idle: the three panels breathe ±1px on a 9s (--dur-ambient) CSS transform loop and their crease shadows lengthen with it. Exit on tap: + presses INTO the paper 0.6mm (--dur-press, --ease-press), then the three panels rotate open on their crease hinges with transform-style: preserve-3d — bottom third down 0.30s, top third up 0.30s, overlapping by 0.09s, each with a 4° overshoot because paper does not lie flat immediately. Total 0.51s.

**WebGL.** none — and this is load-bearing, not an omission. Tapping + fires the React.lazy chunk fetch at the same instant the fold-open begins, so the ~172KB download hides inside 0.51s of motion plus HelloScreen's typing dwell. The entry bundle stays at today's measured 88,579B gzip.

**Acceptance.** Playwright at 390x844: `performance.getEntriesByType('resource')` contains no chunk matching /three|fiber/ at any point before pointerdown on the + button. The landing render is pixel-identical between the full tier and the reduced-motion tier (same WebP, same DOM) — diff the two screenshots, expect zero differing pixels outside the arrow's animated region.

### hello — 'are you here with your special one — or sending them something from afar?', two choice chips, two name fields, 'begin' — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/HelloScreen.tsx`

**Visual.** Canvas is now mounted behind the DOM form, sheet flat and matching the fold-open's final state exactly. Two things make the sheet participate. Picking a relationship chip DEBOSSES the sheet under it — a 0.5mm vertex impression (--z-deboss). Committing a name field on blur or Enter writes a 2px wet-ink seed at the field's baseline into the ink target at 4% wetness: your names are soaking into the sheet you will send. All existing DOM is byte-identical — same chips, same --hairline borders, same --accent 'begin'. Only the surface under them changes. Per the grain rule the inputs and chips themselves get no paper texture.

**Motion.** Entrance: form fades in opacity-only at --dur-screen; the sheet does NOT move, because it was already there and that is the point. Deboss on chip select: --dur-press in, then paperSettle — 240ms total. Deselecting the other chip does NOT lift its impression; it stays as blind emboss with no ink. Name seed: ink wicks 0.4s on --ease-dry, sheet cockles ~0.3mm in a 14px radius. Exit: opacity-only 200ms.

**WebGL.** Sheet mesh + deboss impressions + the first ink seeds. frameloop stays 'demand' — this screen renders zero frames except on interaction. The lazy chunk lands during the 8–20s of real dwell while the user types two names; if it has not landed, the baked WebP holds and the deboss simply does not happen, which nobody notices once.

**Acceptance.** Select chip A, select chip B, screenshot: A's impression is still visible and unfilled. `renderer.info.render.frame` is unchanged across a 5-second idle with no input. Vitest: HelloScreen renders and both inputs are submittable with the canvas module mocked to null.

### photos — 'choose your photos' / 'pick the moments that are you two', 3-col grid, 'these are us (n)' — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/PhotoSelectScreen.tsx`

**Visual.** The grid becomes a CONTACT SHEET. The existing 3-column CSS grid is unchanged, but the gutters show the sheet's fibre and the cells read as printed cells rather than floating rounded rectangles. Selection loses the accent outline and the ✓ badge, and gains a GREASE-PENCIL CIRCLE drawn around the cell — SVG, variable-width filled path, the actual editorial gesture for 'this one'. The chosen frame lifts --z-lift (0.4mm) off the sheet with a real contact shadow. Unselected cells keep their existing 0.85 opacity and now read as unprinted.

**Motion.** Select: pencil draws in 0.22s, pathLength with a pressure-heavy start; cell lifts on paperSettle and its shadow's penumbra widens as it rises. Deselect: pencil ERASES in 0.14s, reverse pathLength — erasing is always faster than drawing, and that asymmetry is a real hand. Cell settles back on --ease-press 200ms. Button label 'these are us (3)' uses layout="position" so Georgia glyphs never scale-distort. Entrance: cells cascade at stagger 0.045s from 'first', total 0.36s, opacity + 6px y.

**WebGL.** Cell lift positions pushed as a uniform array of up to 12 vec3 (x, y, selected) from fixed CSS grid math — NO per-frame getBoundingClientRect. <ContactShadows resolution={256}> under the lifted cells. invalidate() on selection change only.

**Acceptance.** Toggle a cell 20 times: `renderer.info.memory.geometries` and `.textures` are identical before and after. The selection count in the button text matches the number of drawn circles at every intermediate state. Keyboard-only: each cell is still a focusable button with its existing aria state — the circle is decoration, the button carries the truth.

### review — chosen photos in a horizontal strip, HandDrawnArrow 'record your story — we draw from your voice', mic button — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/PhotoReviewScreen.tsx`

**Visual.** The chosen photos are LAID ONTO the sheet. Each arrives via layoutId from the grid (LayoutGroup, AnimatePresence switched to mode="popLayout"), lands with a 1.5° random rotation, and its top-left corner lifts: the sheet bows up 0.4mm underneath and the photo's quad takes a cylindrical curl on that corner. Each photo renders through the ordered Bayer dither pass at --dither-grid 3, quantised toward --ink / --paper / --accent, so a stranger's photograph reads as PRINTED ONTO the sheet rather than as a screen image. This is the one place the dither earns its keep outside a transition, and it is what stitches the user's own pictures into the brand. Mic button and arrow are untouched DOM.

**Motion.** Photos travel from their grid positions on cardTravel with 0.06s stagger, landing rotations settling on paperSettle. Corner curl unfurls 0.3s after landing, 0.5s on --ease-soft. Dither ramps over 0.4s from gridSize 1 (undithered) to 3, so you watch the photo become printed. Arrow draws 0.9s after the last photo lands. Exit to record: photos slide down out of frame 0.35s on --ease-press, clearing the sheet for ink.

**WebGL.** One full-screen ordered-Bayer dither pass, hand-rolled — NOT @react-three/postprocessing, which is +113KB gzip to get the bloom/DOF the brief names as the failure mode. Photo quads with per-corner curl. This is the only screen where the dither pass is live outside a transition; it is replaced (never stacked) by the halftone pass on printing.

**Acceptance.** Exactly one full-screen pass is active: assert the render-pass count is 1 in the frame graph. The dithered photo at gridSize 3 uses no colour outside {--ink, --paper, --accent} — sample 200 random pixels and assert each is within ΔE 4 of one of the three. layoutId travel does not remount the <img>: assert the same DOM node identity survives the step change.

### record — 'tell us about you two. take your time.', seconds counter, MicButton, stop/skip — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/RecordScreen.tsx`

**Visual.** THE SIGNATURE SCREEN AND THE CHEAPEST PROOF OF THE WHOLE THESIS. The sheet is clear. The existing getUserMedia stream (already created at src/screens/RecordScreen.tsx line ~22) gains an AnalyserNode; RMS drives a real ink source at the sheet's centre — a nib whose radius and flow scale with pressure = smoothstep(0.02, 0.35, rms) → radius 4–11px, flow 0.3–1.0. Silence lifts the nib and nothing is injected, so a pause reads as the sheet waiting, which matters because the copy already says 'take your time.' Ink wicks out in a lozenge, longer along --grain-direction than across it. Where the user paused and ink pooled it is genuinely darker — Beer-Lambert paper·exp(−k·a) at --ink-sigma 2.9, not more opacity. And the sheet COCKLES: wetness sampled in the vertex shader buckles the plane into ridges parallel to the grain at ~9mm wavelength, --z-cockle 0.9mm peak, caught by the 14° raking key. The Caveat seconds counter sits on that buckled paper and its baseline tilts as a ridge passes under it. Error path ('skip — we'll imagine it') paints one pre-baked stain and reaches the same state.

**Motion.** Entrance: prompt fades at --dur-screen, MicButton rises on paperSettle. MicButton's infinite scale [1, 1.08, 1] pulse is DELETED — the pulse moves into the ink where amplitude already lives; the button just switches to --accent over --dur-press. Stop: injection halts, wetness decays over --dur-dry (1800ms) on --ease-dry, cockle relaxes toward --cockle-residual 0.18. That residual is still there four screens later. Exit at 2.1s, the sheet carrying its stain and its permanent buckle into printing.

**WebGL.** The only screen that earns frameloop="always", and only while recording === true. Ping-ponged 256² RG16F velocity / 512² RG16F ink, 12 Jacobi pressure iterations, anisotropic diffusion tensor aligned to --grain-direction. Feature-detect EXT_color_buffer_half_float; on failure fall back to the pre-baked 24-frame ink-bloom atlas. dpr capped [1,2], stepped to 1 by <PerformanceMonitor> on decline. Both fluid targets are disposed on leaving printing. frameloop returns to 'demand' at 2.1s.

**Acceptance.** THE KILL GATE FOR THE ENTIRE THEME. Ship this screen alone to 20 people and count how many film their screen or send it to someone. If nobody does, stop — keep this screen plus the page turn, bake everything else, and do not spend weeks 3 and 4. Engineering gate: ≥50fps p95 on a Pixel 6a-class device at 390x844 dpr 2 through 30 seconds of continuous recording, measured by a rAF counter via Playwright browser_evaluate. iOS Safari under Low Power Mode must be measured on real hardware in week one, not assumed — half-float render-target behaviour there is the single unresolved unknown in this spec. `renderer.info.memory.textures` returns to its pre-record value within 3s of stopping.

### printing — '…drawing your story…', three phases: greet 3500ms / read 6000ms / feed 5500ms, follow-ask — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/PrintingScreen.tsx`

**Visual.** The sheet becomes a PRESS, and this is where The Second Drum's best beat is grafted in. PHASE_TIMINGS is untouched. greet: plate one, --ink at --riso-angle-ink 105°, dot radius ramping 4.2px → 0.9px across the phase, so the greeting copy literally resolves from coarse to crisp as the screen gets finer. read: the image COMPLETES in one colour and the press stops — the sheet looks finished. feed at ~13200ms: plate two, --accent at --riso-angle-accent 45°, lands with --misregister 1.7px, and the camera pushes to macro on ONE overlap region and holds 400ms. Two dot grids at different angles, neither aligned, and in the overlap a warm dark --overprint #241b19 that is on neither plate because it exists only where both inks touched the same fibre. Then it pulls back. That 400ms frame is the screenshot, and it is the only macro moment in the app, so it is unmistakable and unrepeatable. The existing feed thumbnails and follow-ask ride in on fresh sheet below.

**Motion.** The infinite opacity [0.4, 1, 0.4] pulse is REPLACED — it is the exact animation reducedMotion="user" would preserve while still being wrong — with a 0.5Hz dot-density breath in the halftone itself, as if the ink supply pulses. Copy per phase enters at --dur-screen opacity+4px, exits 200ms opacity-only. Dot-radius ramp runs on --ease-soft across the full 3.5s. Plate two SLAMS in on --ease-press 200ms: a plate drops, it does not ease. Macro push 400ms on --ease-soft, hold, pull back 400ms. Follow buttons enter at stagger 0.06s from 'first'.

**WebGL.** One hand-rolled two-plate halftone pass that REPLACES the dither pass rather than stacking with it, so the two-pass budget is never both at once. three/examples/jsm/postprocessing/HalftonePass.js is READ for the screen-angle maths, not imported — it does not expose two plates with independent angles and a misregistration offset. frameloop 'always' during the greet dot ramp and the plate-two drop; 'demand' during read.

**Acceptance.** Assert exactly one full-screen pass is active at every point in the 15s (never dither AND halftone). Sample the overlap region at 13400ms and assert the modal pixel value is within ΔE 3 of --overprint #241b19, and that this value appears nowhere on screen at 13000ms. Existing fakeGeneration.test.ts still passes untouched — PHASE_TIMINGS and deriveStoryBeats are not modified by this theme.

### reveal — 'your story, drawn', Carousel of house slides, 'continue' — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/RevealScreen.tsx`

**Visual.** The printing→reveal transition is THE PAGE TURN, the second signature moment. The sheet bends on a vertex shader — uProgress 0→1 with uBend bowing it out of plane — patched into MeshStandardMaterial via three-custom-shader-material so the bending sheet STILL RECEIVES its contact shadow. That shadow is the entire reason it reads as paper and not as a textured quad. An invisible backdrop plane catches the tap, because a GPU-side vertex bend is invisible to the CPU raycaster. Front face: the printing UI. Back face: the finished carousel. At the apex, edge-on to the raking key, the Beer-Lambert backlight term peaks and you see the printed ink GLOWING THROUGH from the other side, mirrored in U, at heavier sigma, against --paper-backlit. After the turn, slides stay DOM <img> so they are crisp and the existing drag-to-swipe survives untouched. The record screen's residual cockle rakes visibly across the finished piece — that is the payoff, and it replaces the depth-map parallax, which is cut.

**Motion.** Turn: --dur-turn 900ms, and NOT one curve — pageTurn spring on uProgress (visualDuration 0.62, bounce 0.14) so it starts slow, accelerates past vertical as gravity takes it, then catches air; plus a decaying 6Hz flutter on uBend across the final 0.3s. Backlight peaks at progress 0.5, gone by 0.72. Title and 'continue' fade in 200ms after the flutter settles. The existing scale 0.96→1 / 0.6s wrapper entrance is DELETED — the turn IS the entrance. Swipe: the outgoing slide is SLID OFF THE PILE, not crossfaded — 0.34s cardTravel, shadow narrowing as it leaves. Dots keep their instant state change. Idle: light azimuth drifts ±6° over --dur-ambient, raking across the residual cockle.

**WebGL.** Bend material on a subdivided plane (48x96), plus the invisible raycast backdrop. No depth-map parallax, no tilt, no device orientation — cut deliberately: at the sub-2% displacement that keeps it tasteful it is invisible, and above it, it is the 2018 fake-3D-photo trick. frameloop 'always' for the 900ms of the turn, then 'demand'.

**Acceptance.** Tapping anywhere during the turn is caught — assert the backdrop plane receives the pointer event at uProgress 0.5 (a GPU vertex bend is invisible to the raycaster, and this is the most likely single bug in the build). Carousel drag-to-swipe passes its existing behaviour test unchanged. The cockle residual is measurably present: sample the normal-map-lit highlight row at reveal and assert it is non-flat, i.e. that the sheet did not reset between screens.

### rate — 'did this feel like you?', five stars, 'continue' — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/RateScreen.tsx`

**Visual.** The stars are not glyphs on top of paper. They are STAMPED INTO it. Tapping star n debosses the sheet at n positions (--z-deboss 0.5mm) and ink fills each impression at --accent. The existing ★ glyphs are kept as the DOM hit targets with their aria-label intact, but rendered at --paper against the ink-filled impression, so what you see is the hole, not the character. The unforgiving detail, and the concept's central rule: retapping to a LOWER rating leaves the extra impressions as blind embossing with no ink, because you cannot un-press paper. Grafted from The Second Drum: the final rating leaves a faint --accent impression on the sheet's corner that PERSISTS into send — the rating is physically on the letter rather than disappearing into state, which is a small honesty the app currently lacks.

**Motion.** Stamp cascade: stagger(0.055, { from: 'center' }) so the rating BLOOMS outward from the middle star instead of sweeping left-to-right like a form — 0.22s total for five, inside the ≤0.40s house rule. Each individual stamp is --dur-press on --ease-press with zero bounce: a stamp does not rebound. Ink fill trails the impression by 60ms and takes 180ms on --ease-dry. Downgrade: ink drains from the de-selected impressions over 260ms; the geometry does not move. 'continue' enables with a 200ms opacity+background crossfade.

**WebGL.** Deboss impressions written into the same wetness/impression target the sheet already carries from hello — no new render target. One-shot ink fill reusing the record screen's compositing path at a fixed radius (no fluid solve). invalidate() per tap only.

**Acceptance.** Tap 5, then tap 2: assert three unfilled impressions remain visible and the DOM rating state is 2. The five stars remain keyboard-reachable with correct aria-label at every state. Under reduced motion the stars fill instantly in --accent and still bloom from centre at 0ms stagger — i.e. order is preserved, only duration goes to zero.

### send — 'send it to {name}', share target list, 'no downloads — this is meant to be given, not saved.' — `/Users/himanshusharma/astoryoftwo-analysis/app/src/screens/SendScreen.tsx`

**Visual.** The sheet is TORN FROM THE PAD, FOLDED, AND SEALED. Tap: a procedural tear crosses the top — an animated alpha-clip threshold along a hand-authored jagged path warped by fbm. (The second higher-frequency 'fibre whisker' band is CUT — imperceptible at 390px and expensive to tune.) Then a three-panel letter fold at three hinge lines, using the same bend material as the page turn. Then <Decal> stamps a postmark in --accent at 6°, with fbm-thresholded alpha so it has the ink-starved patchiness of a real rubber stamp — and the rating impression from the previous screen is visible in the corner, folded into the letter. The share-target list rises as DOM buttons over the folded letter, which stays visible behind them, folded, waiting. The existing 'no downloads' note is unchanged and is now literally true on screen: nothing in this app ever travels toward the viewer, it leaves.

**Motion.** Send button press: the existing whileTap scale 0.95 is REPLACED — the button presses INTO the sheet 0.6mm and the paper dents around it (--dur-press, --ease-press). Buttons on paper do not shrink; paper yields. Tear: 0.55s on --ease-soft. Fold: bottom third up 0.34s, top third down 0.34s, overlapping by 0.10s, each on paperSettle with a 4° overshoot because paper does not fold crisply until pressed. Burnish press: 0.20s --ease-press snap, no bounce. Postmark: 0.16s, lands hard, 6°, no settle. Share buttons rise at stagger 0.05s from 'first', 6px y + opacity on cardTravel — 0.20s total for four targets.

**WebGL.** Tear alpha-clip + three-hinge fold on the bend material + one <Decal>. Reuses the page-turn material, so this screen adds one shader variant, not a new system. This is the block to cut first if the budget moves — it is the last 4 days and the least load-bearing.

**Acceptance.** All four share targets remain real <button>s and src/services/share.test.ts passes unchanged. After a full nine-step run, `renderer.info.memory.geometries` and `.textures` are back to their step-1 baseline — this is the leak gate, and AnimatePresence unmounting a screen on every one of the nine steps is exactly how a phone prototype dies on screen seven. The rating impression from RateScreen is visible in the folded letter's corner.

## Build order

1. PHASE 0 — 1 day, zero WebGL, SHIPS ALONE AND IS WORTH SHIPPING ALONE. Install framer-motion@^13.4.0 and wrap src/App.tsx in <MotionConfig reducedMotion="user">. Delete src/styles/global.css line 12. Delete both infinite loops: src/screens/PrintingScreen.tsx's opacity pulse and src/components/MicButton.tsx's scale pulse. Write src/styles/motion.ts with the three springs and the house rules as comments, and paste the new tokens.css. Switch src/App.tsx's hardcoded duration: 0.35 opacity+y to opacity-only at --dur-screen on --ease-soft, and AnimatePresence from mode="wait" to mode="popLayout" inside a LayoutGroup. This fixes a live accessibility bug and gives the app a real motion vocabulary before a single shader exists. If everything after this is cancelled, the app is still better.

2. PHASE 1 — 1 day, still zero three.js, SHIPS ALONE. Bake /public/textures/paper-base.webp offline from @paper-design/shaders-react <PaperTexture creasedPreset> and swap it into src/components/PaperBackground.tsx for the CSS radial gradient (one file, same component boundary, same children). Wire it as the first-paint image for every tier. Download the Poly Haven CC0 paper-card normal + roughness pair, channel-pack to 512² WebP. The app already feels more like paper and the Tier-1 fallback is now complete and permanently exercised.

3. PHASE 2 — 5-6 days, THE CHEAPEST PROOF OF THE THESIS AND THE KILL GATE. Build ONLY the record screen. Canvas shell, sheet mesh, 14° raking key, light-azimuth drift, the ink fluid solve with Beer-Lambert compositing, and the wetness-driven cockle. Nothing else — no page turn, no printing, no deboss. Ship it to twenty people and watch whether anyone films their screen or sends it to someone. This is Wet Ink's own proposed falsifiable test and I am making it the gate: if nobody does, keep this one screen, bake the rest, and stop. The remaining weeks would be decoration. Measure iOS Safari half-float render targets under Low Power Mode on real hardware in this phase, not later — it is the one unknown that cannot be resolved from a desk.

4. PHASE 3 — 3 days, THE SECOND SIGNATURE MOMENT. The printing→reveal page turn: bend vertex shader via three-custom-shader-material, the Beer-Lambert backlight at the apex, the decaying 6Hz flutter, the invisible raycast backdrop plane. Plus the residual cockle raking across RevealScreen, which is what makes Phase 2 pay off four screens later. Delete RevealScreen's scale 0.96→1 entrance. After this phase the two moments anyone would screenshot both exist.

5. PHASE 4 — 3 days. The printing screen's two-plate riso: dot-radius ramp on plate one, then the plate-two --accent drop at --misregister 1.7px, then the 400ms macro hold on the --overprint region. Plus the ordered-Bayer dither on PhotoReviewScreen. Verify the one-pass-at-a-time budget holds.

6. PHASE 5 — 3 days. The cheap reuses of material already built: deboss on HelloScreen chips, the star stamps on RateScreen with the permanent blind-emboss rule, the rating impression carried into SendScreen, the grease-pencil selection mark on PhotoSelectScreen, and the layoutId travel from grid to review strip. Individually small because they reuse Phase 2 and Phase 3 shaders.

7. PHASE 6 — 4 days, CUT FIRST IF THE BUDGET MOVES. SendScreen's tear, three-panel fold and <Decal> postmark, plus LandingScreen's three-panel fold-open. These are the least load-bearing motions in the theme and the last to be seen.

8. PHASE 7 — 4 days, NON-NEGOTIABLE. Real-Android perf and thermal soak on a Pixel 6a-class device. The disposal audit: assert renderer.info.memory is flat from step 1 to step 9. dpr stepping and the Tier-2 sprite-atlas fallback. Fix the failing Playwright MCP plugin config and wire both hard gates into CI: entry chunk under 92 KB gzip, and no three/fiber resource fetched under prefers-reduced-motion.

## Risks

- HIGH — the ink fluid solve is the only genuine engineering risk in the theme. 512² ink plus 256² velocity at 12 Jacobi iterations is roughly 5 MP/frame of fragment fill; at 60fps that is 300 MP/s, which a Pixel 6a / Galaxy A54 class GPU handles but does not shrug off. Mitigation is already tiered (velocity to 128², iterations 12→6, then the pre-baked sprite atlas). The specific unknown that CANNOT be resolved from a desk is iOS Safari's half-float render-target behaviour under Low Power Mode. Measure it on real hardware in Phase 2, week one. If it fails there, Tier 2 becomes the default on iOS and the theme still works — but discovering that in week four instead of week one costs three weeks.
- HIGH — the theme's own strongest self-criticism, which I have acted on but not eliminated: the user's eyes are on the mic button, the copy, and their own carousel, not on the paper. There is a real chance a user's entire summary is 'the paper looked nice', which a good static texture plus framer-motion would have bought in Phase 0 and Phase 1 for two days and zero bundle. This is exactly why Phase 2 is a kill gate with a behavioural test (does anyone film it?) rather than a design review. If nobody films it, the honest move is to stop after Phase 2 and bake the rest. Unmeasurable value is how design budgets get burned.
- MEDIUM — the 'one sheet' conceit fights the flow in two places, and I want this on the record rather than buried. PhotoSelectScreen is an interaction with twelve objects and RevealScreen is an interaction with a stack of cards; neither is naturally one sheet. The contact-sheet and card-pile framings are both defensible but they are the two screens where the metaphor is doing work rather than being obviously true. If a reviewer says the contact sheet feels imposed, they are seeing something real, and the honest fix is to let those two screens be sheets-plural rather than to force the conceit until it reads as a gimmick.
- MEDIUM — the permanent-impression rules are deliberate design and hostile to exploration. A user who taps all five stars to see what happens has permanently marked their letter. I believe this is correct and would ship it, but it is a refusal to be forgiving and it will generate at least one piece of user feedback that reads as a bug report. Do not 'fix' it in response to that first report without discussing it.
- MEDIUM — first-frame jank when the 3D chunk hydrates during HelloScreen. Mitigated because the user is typing two names (8–20s of real dwell), but it must be measured with a PerformanceObserver longtask entry, not eyeballed. If the hydration blocks the main thread while a text input has focus, that is worse than any frame-rate number.
- MEDIUM — the raycast bug. A GPU-side vertex bend is invisible to the CPU raycaster, so during the 900ms page turn nothing is where it looks like it is. The invisible backdrop plane handles it, but this is the single most likely bug to ship undetected, because it only manifests if someone taps mid-turn. It has its own acceptance test for that reason.
- LOW — leaks. AnimatePresence unmounts a screen on every one of the nine steps in src/flow/steps.ts. The canvas survives, but fluid targets, photo quads and impression buffers churn. Mitigated by an explicit disposal registry and a merge gate asserting renderer.info.memory is flat from step 1 to step 9 — but a leak here does not show up in a 30-second demo, only on screen seven of a real session.
- LOW — bundle creep. @react-three/fiber does `import * as THREE`, so tree-shaking does not apply and the 3D chunk cannot be made smaller than ~172 KB gzip by optimisation. The only defences are the lazy boundary and the CI gate at 92 KB on the entry chunk. Anyone who statically imports anything from src/webgl/ into a screen file silently doubles the landing payload; the CI gate is what catches it.
- LOW — thermal. Six of nine screens render zero frames under frameloop="demand"; the GPU is awake for roughly 20 seconds across a 90-second session. Real, but structurally handled.