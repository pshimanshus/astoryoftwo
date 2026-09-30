import { useState, type CSSProperties } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import type { Slide } from '../session/session';

const CORNER: CSSProperties = { position: 'absolute', width: 10, height: 10, pointerEvents: 'none' };

export function Carousel({ slides }: { slides: Slide[] }) {
  const [i, setI] = useState(0);
  const go = (d: number) => setI((p) => Math.max(0, Math.min(slides.length - 1, p + d)));
  if (!slides.length) return null;
  const s = slides[i];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--space-3)', width: '100%' }}>
      {/* A print-proof frame, not a rounded card — a thin hairline border plus corner registration
          ticks, the vocabulary of a proof sheet rather than app UI. The image itself stays a plain
          rectangle (no torn clip-path here): it's the drag target, and clipping would shrink the
          hit area right where a thumb naturally starts a swipe. 3/4 matches the repo's real
          carousel export gate (1080x1440) — was 9/11, which cropped the preview. */}
      <div style={{ position: 'relative', width: '100%', aspectRatio: '3/4', border: '1px solid var(--hairline)', background: 'var(--paper-shadow)' }}>
        <AnimatePresence mode="wait">
          <motion.img key={s.id} src={s.imageUrl} alt={s.caption}
            initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }} transition={{ duration: 0.4 }}
            drag="x" dragConstraints={{ left: 0, right: 0 }}
            onDragEnd={(_, info) => { if (info.offset.x < -60) go(1); if (info.offset.x > 60) go(-1); }}
            style={{ width: '100%', height: '100%', objectFit: 'cover' }} />
        </AnimatePresence>
        <span style={{ ...CORNER, top: -1, left: -1, borderTop: '2px solid var(--ink)', borderLeft: '2px solid var(--ink)' }} />
        <span style={{ ...CORNER, top: -1, right: -1, borderTop: '2px solid var(--ink)', borderRight: '2px solid var(--ink)' }} />
        <span style={{ ...CORNER, bottom: -1, left: -1, borderBottom: '2px solid var(--ink)', borderLeft: '2px solid var(--ink)' }} />
        <span style={{ ...CORNER, bottom: -1, right: -1, borderBottom: '2px solid var(--ink)', borderRight: '2px solid var(--ink)' }} />
      </div>
      <p style={{ fontFamily: 'var(--font-hand)', fontSize: 'var(--text-hand)', textAlign: 'center', minHeight: 56 }}>{s.caption}</p>
      <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
        {slides.map((sl, idx) => (
          <span key={sl.id} onClick={() => setI(idx)}
            style={{ width: 8, height: 8, borderRadius: '50%', background: idx === i ? 'var(--ink)' : 'var(--hairline)' }} />
        ))}
      </div>
    </div>
  );
}
