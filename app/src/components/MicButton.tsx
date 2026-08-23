import { motion } from 'framer-motion';

export function MicButton({ recording, onToggle }: { recording: boolean; onToggle: () => void }) {
  return (
    <motion.button onClick={onToggle} aria-pressed={recording}
      animate={recording ? { scale: [1, 1.08, 1] } : { scale: 1 }}
      transition={recording ? { repeat: Infinity, duration: 1.1 } : {}}
      style={{ width: 96, height: 96, borderRadius: '50%', background: recording ? 'var(--accent)' : 'var(--ink)', color: 'var(--paper)', fontSize: 34, display: 'grid', placeItems: 'center' }}>
      {recording ? '■' : '🎙'}
    </motion.button>
  );
}
