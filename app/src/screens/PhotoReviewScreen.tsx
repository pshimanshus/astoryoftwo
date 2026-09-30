import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { press } from '../styles/motion';
import { sampleGallery } from '../content/sampleGallery';
import { TornPhoto } from '../components/TornPhoto';
import { HandDrawnArrow } from '../components/HandDrawnArrow';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function PhotoReviewScreen() {
  const { advance } = useFlow();
  const { session } = useSession();
  const chosen = sampleGallery.filter((p) => session.photos.includes(p.id));

  return (
    <div className="sheet" style={{ padding: '48px 20px 28px', justifyContent: 'center', gap: 'var(--space-8)' }}>
      <span className="sheet__spine">04 — one last look</span>

      <div style={{ display: 'flex', overflowX: 'auto', padding: '16px 8px 16px 4px' }}>
        {chosen.map((p, i) => (
          <div key={p.id} style={{ flex: '0 0 auto', marginLeft: i === 0 ? 0 : -48, zIndex: i }}>
            <TornPhoto src={p.url} alt="" seed={p.id} width={170} height={226} />
          </div>
        ))}
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)' }}>
        <HandDrawnArrow caption={copy.review.mic} />
        <motion.button onClick={advance} className="seal" aria-label="record your story"
          whileTap={{ scale: 0.94 }} transition={press} style={{ background: 'var(--accent)', color: '#fff', fontSize: 28 }}>
          🎙
        </motion.button>
      </div>
    </div>
  );
}
