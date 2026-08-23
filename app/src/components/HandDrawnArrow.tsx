export function HandDrawnArrow({ caption }: { caption: string }) {
  return (
    <div style={{ textAlign: 'center', color: 'var(--ink-soft)' }}>
      <p style={{ fontFamily: 'var(--font-hand)', fontSize: 24, lineHeight: 1.2 }}>{caption}</p>
      <svg width="60" height="70" viewBox="0 0 60 70" aria-hidden style={{ display: 'block', margin: '0 auto' }}>
        <path d="M30 4 C 18 26, 42 40, 30 62" fill="none" stroke="var(--ink-soft)" strokeWidth="2.5" strokeLinecap="round" />
        <path d="M20 52 L30 64 L40 52" fill="none" stroke="var(--ink-soft)" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    </div>
  );
}
