import { useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { press } from '../styles/motion';
import { useFlow } from '../flow/FlowProvider';
import { hasReachedCap } from '../session/deviceId';

export function LandingScreen() {
  const { advance, goTo } = useFlow();
  const [showDisclaimer, setShowDisclaimer] = useState(false);

  const start = () => (hasReachedCap() ? goTo('cap-reached') : advance());

  return (
    <div className="sheet" style={{ padding: '80px 28px 32px' }}>
      <span className="sheet__spine">01 — say hello</span>

      <p className="headline headline--hand">{copy.landing.cta}</p>

      <div className="spacer" />

      <div style={{ display: 'flex', justifyContent: 'center', paddingBottom: 'var(--space-7)' }}>
        <motion.button onClick={start} className="seal" aria-label="start your story"
          whileTap={{ y: 2, boxShadow: '0 4px 12px rgba(0,0,0,0.25)' }} transition={press}>
          +
        </motion.button>
      </div>

      <button onClick={() => setShowDisclaimer(true)} className="stamp stamp--ghost"
        style={{ alignSelf: 'center', marginBottom: 8 }}>
        before you begin
      </button>

      {showDisclaimer && (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={{ duration: 0.2 }}
          onClick={() => setShowDisclaimer(false)}
          style={{ position: 'absolute', inset: 0, background: 'rgba(20,16,12,0.5)', display: 'flex', alignItems: 'flex-end', padding: 0 }}>
          <div style={{ background: 'var(--paper)', padding: '28px 28px 36px', borderTop: '2px solid var(--ink)', width: '100%' }}>
            <p className="lede" style={{ color: 'var(--ink)' }}>{copy.landing.disclaimer}</p>
            <p className="kicker" style={{ marginTop: 14, marginBottom: 0 }}>tap anywhere to close</p>
          </div>
        </motion.div>
      )}
    </div>
  );
}
