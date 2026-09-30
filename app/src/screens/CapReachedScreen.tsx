import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { press } from '../styles/motion';
import { useFlow } from '../flow/FlowProvider';

export function CapReachedScreen() {
  const { goTo } = useFlow();
  return (
    <div className="sheet sheet--plain" style={{ alignItems: 'center', justifyContent: 'center', gap: 'var(--space-5)', padding: 32, textAlign: 'center' }}>
      <p className="headline headline--hand" style={{ margin: 0, maxWidth: 'none' }}>{copy.cap.title}</p>
      <p className="lede" style={{ maxWidth: 260, textAlign: 'center' }}>{copy.cap.body}</p>
      <motion.button onClick={() => goTo('landing')} whileTap={{ y: 2 }} transition={press} className="stamp stamp--solid">
        back to start
      </motion.button>
    </div>
  );
}
