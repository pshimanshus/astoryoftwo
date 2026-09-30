import { motion } from 'framer-motion';
import { press } from '../styles/motion';

export function MicButton({ recording, onToggle }: { recording: boolean; onToggle: () => void }) {
  return (
    <motion.button onClick={onToggle} aria-pressed={recording}
      animate={{ background: recording ? 'var(--accent)' : 'var(--ink)' }}
      transition={press}
      style={{ width: 96, height: 96, borderRadius: '50%', color: 'var(--paper)', fontSize: 34, display: 'grid', placeItems: 'center' }}>
      {recording ? '■' : '🎙'}
    </motion.button>
  );
}
