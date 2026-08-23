import type { ReactNode } from 'react';

export function PhoneFrame({ children }: { children: ReactNode }) {
  return (
    <div
      style={{
        width: 390,
        height: 844,
        maxHeight: '95vh',
        borderRadius: 44,
        overflow: 'hidden',
        position: 'relative',
        boxShadow: '0 30px 80px rgba(0,0,0,0.55)',
        border: '10px solid #0b0907',
        background: 'var(--paper)',
      }}
    >
      {children}
    </div>
  );
}
