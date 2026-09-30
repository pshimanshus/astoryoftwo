import { useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { press } from '../styles/motion';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

// Entrance stagger, "from: center" — the middle star blooms first, each neighbour 55ms behind
// the one closer to center. Computed by hand: the installed framer-motion's Transition type
// doesn't accept framer-motion's own stagger() helper (DynamicOption isn't assignable to
// delayChildren: number here), so five known items get their delay computed directly instead.
const STAR_TRANSITION = { duration: 0.2, ease: [0.3, 0, 0.2, 1] as const };
const CENTER_INDEX = 2;

export function RateScreen() {
  const { advance } = useFlow();
  const { session, update } = useSession();
  const [rating, setRating] = useState(session.rating ?? 0);

  return (
    <div className="sheet" style={{ padding: '64px 28px 32px', justifyContent: 'center', gap: 'var(--space-7)' }}>
      <span className="sheet__spine">08 — the verdict</span>

      <p className="headline" style={{ fontSize: 'clamp(24px, 7vw, 32px)' }}>{copy.rate.prompt}</p>

      <div style={{ display: 'flex', gap: 'var(--space-3)' }}>
        {[1, 2, 3, 4, 5].map((n, i) => (
          <motion.button key={n}
            initial={{ opacity: 0, scale: 0.5 }} animate={{ opacity: 1, scale: 1 }}
            transition={{ ...STAR_TRANSITION, delay: Math.abs(i - CENTER_INDEX) * 0.055 }}
            onClick={() => { setRating(n); update({ rating: n }); }}
            style={{ fontSize: 38, color: n <= rating ? 'var(--accent)' : 'var(--hairline)' }} aria-label={`${n} stars`}>
            ★
          </motion.button>
        ))}
      </div>

      <div className="spacer" />

      <motion.button disabled={rating === 0} onClick={advance} whileTap={{ y: 2 }} transition={press}
        className={`stamp stamp--block ${rating ? 'stamp--solid' : ''}`}>
        continue
      </motion.button>
    </div>
  );
}
