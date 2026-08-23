import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { Carousel } from '../components/Carousel';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function RevealScreen() {
  const { advance } = useFlow();
  const { session } = useSession();
  return (
    <motion.div initial={{ opacity: 0, scale: 0.96 }} animate={{ opacity: 1, scale: 1 }} transition={{ duration: 0.6 }}
      style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 20, gap: 14, justifyContent: 'center' }}>
      <p style={{ fontSize: 22, textAlign: 'center' }}>{copy.reveal.title}</p>
      <Carousel slides={session.slides ?? []} />
      <button onClick={advance} style={{ padding: 14, borderRadius: 14, background: 'var(--ink)', color: 'var(--paper)', fontSize: 16 }}>
        continue
      </button>
    </motion.div>
  );
}
