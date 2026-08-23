import { useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
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
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18, padding: 28 }}>
      {!open ? (
        <motion.button whileTap={{ scale: 0.95 }} onClick={reveal}
          style={{ padding: '16px 28px', borderRadius: 16, background: 'var(--accent)', color: '#fff', fontSize: 20 }}>
          {copy.send.primary(partner)}
        </motion.button>
      ) : (
        <motion.div initial={{ opacity: 0, y: 12 }} animate={{ opacity: 1, y: 0 }}
          style={{ display: 'flex', flexDirection: 'column', gap: 10, width: '100%' }}>
          {SHARE_TARGETS.map((t) => (
            <button key={t.id} onClick={() => shareTo(t, msg)}
              style={{ padding: 14, borderRadius: 14, border: '1.5px solid var(--hairline)', fontSize: 16, textAlign: 'left' }}>
              {t.label}
            </button>
          ))}
          <p style={{ fontSize: 13, color: 'var(--ink-soft)', textAlign: 'center', marginTop: 6 }}>{copy.send.note}</p>
        </motion.div>
      )}
    </div>
  );
}
