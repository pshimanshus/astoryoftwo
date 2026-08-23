import type { ReactNode } from 'react';

// Full-bleed warm paper layer. Subtle layered radial grain via CSS only.
export function PaperBackground({ children }: { children: ReactNode }) {
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
      {children}
    </div>
  );
}
