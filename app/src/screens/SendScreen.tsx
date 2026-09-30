import { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { press, screenSettle } from '../styles/motion';
import { useSession } from '../session/SessionProvider';
import { displayPartnerName } from '../session/session';
import { SHARE_TARGETS, buildShareMessage, shareTo } from '../services/share';
import { recordCarouselCreated } from '../session/deviceId';

export function SendScreen() {
  const { session } = useSession();
  const [open, setOpen] = useState(false);
  const counted = useRef(false);
  const partner = displayPartnerName(session);
  const msg = buildShareMessage(session);

  const reveal = () => {
    if (!counted.current) { recordCarouselCreated(); counted.current = true; }
    setOpen(true);
  };

  return (
    <div className="sheet" style={{ padding: '64px 28px 32px', justifyContent: open ? 'flex-start' : 'center', gap: 'var(--space-5)' }}>
      <span className="sheet__spine">09 — send it</span>

      {!open ? (
        <>
          <p className="headline" style={{ fontSize: 'clamp(24px, 7vw, 32px)' }}>ready.</p>
          <motion.button whileTap={{ y: 2, boxShadow: '0 4px 12px rgba(0,0,0,0.3)' }} transition={press} onClick={reveal}
            className="stamp stamp--accent">
            {copy.send.primary(partner)}
          </motion.button>
        </>
      ) : (
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} transition={screenSettle}
          style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
          {SHARE_TARGETS.map((t) => (
            <button key={t.id} onClick={() => shareTo(t, msg)}
              style={{ padding: '14px 0', borderBottom: '1.5px solid var(--hairline)', fontSize: 'var(--text-body)', textAlign: 'left' }}>
              {t.label}
            </button>
          ))}
          <p className="kicker" style={{ marginTop: 'var(--space-3)' }}>{copy.send.note}</p>
        </motion.div>
      )}
    </div>
  );
}
