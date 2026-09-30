import { lazy, Suspense, useEffect, useState, type ReactNode } from 'react';
import { supportsWebGL } from '../webgl/supportsWebGL';

const SheetCanvas = lazy(() => import('../webgl/SheetCanvas'));

function usePrefersReducedMotion(): boolean {
  const [reduced, setReduced] = useState(
    () => typeof window !== 'undefined' && window.matchMedia('(prefers-reduced-motion: reduce)').matches,
  );
  useEffect(() => {
    const mq = window.matchMedia('(prefers-reduced-motion: reduce)');
    const onChange = () => setReduced(mq.matches);
    mq.addEventListener('change', onChange);
    return () => mq.removeEventListener('change', onChange);
  }, []);
  return reduced;
}

// Full-bleed warm paper layer. Tier 1 (reduced motion, or no WebGL2/WebGL support) never even
// imports the canvas chunk — the CSS radial-gradient below is the real fallback, not a loading
// state, so a WebGL context-creation failure has something correct already in the DOM underneath
// it. Tier 2/3 lazy-load SheetCanvas as a sibling behind {children}, absolutely positioned.
export function PaperBackground({ children }: { children: ReactNode }) {
  const reducedMotion = usePrefersReducedMotion();
  // supportsWebGL() probes lazily (see webgl/supportsWebGL.ts) — safe to call directly, it's
  // cached after the first call and touches only a throwaway <canvas>, never triggers the import.
  const canUseWebGL = !reducedMotion && supportsWebGL();

  return (
    <div
      style={{
        position: 'absolute',
        inset: 0,
        background:
          'radial-gradient(120% 80% at 50% 0%, #fbf7ee 0%, var(--paper) 55%, var(--paper-shadow) 100%)',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      {canUseWebGL && (
        <Suspense fallback={null}>
          <SheetCanvas />
        </Suspense>
      )}
      {children}
    </div>
  );
}
