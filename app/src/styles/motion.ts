// Motion tokens for anything a CSS custom property can't express — springs. Durations/eases that
// CSS *can* express live in tokens.css (--dur-*, --ease-*); this is the spring-driven layer.
//
// House choreography rules:
//   - bounce never above 0.15 — paper settles, it doesn't wobble.
//   - stagger step <= 0.08s; total cascade <= 0.40s.
//   - this installed framer-motion's Transition.delayChildren is typed `number`, not
//     DynamicOption<number> — the stagger() helper's return type doesn't fit it. Compute
//     per-item delays by hand (see RateScreen.tsx) rather than fighting that mismatch.
import type { Transition } from 'framer-motion';

/** A screen or panel settling into place. */
export const paperSettle: Transition = {
  type: 'spring',
  visualDuration: 0.5,
  bounce: 0.12,
};

/** A card or slide traveling from one position to another. */
export const cardTravel: Transition = {
  type: 'spring',
  visualDuration: 0.45,
  bounce: 0.08,
};

/** The printing -> reveal page turn's DOM-side settle, timed to match the WebGL bend. */
export const pageTurn: Transition = {
  type: 'spring',
  visualDuration: 0.62,
  bounce: 0.14,
};

/** A finger pressing paper: fast in, no rebound. */
export const press: Transition = {
  duration: 0.2,
  ease: [0.3, 0, 0.2, 1],
};

/** A step change settling. */
export const screenSettle: Transition = {
  duration: 0.4,
  ease: [0.22, 1, 0.36, 1],
};
