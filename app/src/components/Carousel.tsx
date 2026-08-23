import { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Slide } from '../session/session';

export function Carousel({ slides }: { slides: Slide[] }) {
  const [i, setI] = useState(0);
  const go = (d: number) => setI((p) => Math.max(0, Math.min(slides.length - 1, p + d)));
  if (!slides.length) return null;
  const s = slides[i];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 12, width: '100%' }}>
      <div style={{ position: 'relative', width: '100%', aspectRatio: '9/11', borderRadius: 18, overflow: 'hidden', background: 'var(--paper-shadow)' }}>
        <AnimatePresence mode="wait">
          <motion.img key={s.id} src={s.imageUrl} alt={s.caption}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}
            drag="x" dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => { if (info.offset.x < -60) go(1); if (info.offset.x > 60) go(-1); }}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </AnimatePresence>
      </div>
      <p style={{ fontFamily: 'var(--font-hand)', fontSize: 22, textAlign: 'center', minHeight: 56 }}>{s.caption}</p>
      <div style={{ display: 'flex', gap: 6 }}>
        {slides.map((sl, idx) => (
          <span key={sl.id} onClick={() => setI(idx)}
            style={{ width: 8, height: 8, borderRadius: '50%', background: idx === i ? 'var(--ink)' : 'var(--hairline)' }} />
        ))}
      </div>
    </div>
  );
}
