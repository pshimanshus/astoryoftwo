import { useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { HandDrawnArrow } from '../components/HandDrawnArrow';
import { useFlow } from '../flow/FlowProvider';
import { hasReachedCap } from '../session/deviceId';

export function LandingScreen() {
  const { advance, goTo } = useFlow();
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  const start = () => (hasReachedCap() ? goTo('cap-reached') : advance());

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 24, padding: 24 }}>
      <HandDrawnArrow caption={copy.landing.cta} />
      <motion.button
        onClick={start}
        whileTap={{ scale: 0.94 }}
        aria-label="start your story"
        style={{ width: 84, height: 84, borderRadius: '50%', background: 'var(--ink)', color: 'var(--paper)', fontSize: 40, lineHeight: 1, boxShadow: '0 10px 24px rgba(0,0,0,0.25)' }}
      >
        +
      </motion.button>

      <button onClick={() => setShowDisclaimer(true)} style={{ position: 'absolute', bottom: 24, fontSize: 13, color: 'var(--ink-soft)', textDecoration: 'underline' }}>
        before you begin
      </button>

      {showDisclaimer && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} onClick={() => setShowDisclaimer(false)}
          style={{ position: 'absolute', inset: 0, background: 'rgba(20,16,12,0.45)', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: 28 }}>
          <div style={{ background: 'var(--paper)', borderRadius: 'var(--radius)', padding: 22, fontSize: 15, lineHeight: 1.5 }}>
            <p>{copy.landing.disclaimer}</p>
            <p style={{ marginTop: 14, fontFamily: 'var(--font-hand)', color: 'var(--ink-soft)' }}>tap anywhere to close</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
