import { useState } from 'react';
import { copy } from '../content/copy';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function RateScreen() {
  const { advance } = useFlow();
  const { session, update } = useSession();
  const [rating, setRating] = useState(session.rating ?? 0);

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 22, padding: 28 }}>
      <p style={{ fontSize: 20, textAlign: 'center' }}>{copy.rate.prompt}</p>
      <div style={{ display: 'flex', gap: 8 }}>
        {[1, 2, 3, 4, 5].map((n) => (
          <button key={n} onClick={() => { setRating(n); update({ rating: n }); }}
            style={{ fontSize: 36, color: n <= rating ? 'var(--accent)' : 'var(--hairline)' }} aria-label={`${n} stars`}>
            ★
          </button>
        ))}
      </div>
      <button disabled={rating === 0} onClick={advance}
        style={{ padding: 14, borderRadius: 14, background: rating ? 'var(--ink)' : 'var(--hairline)', color: 'var(--paper)', fontSize: 16, width: '100%' }}>
        continue
      </button>
    </div>
  );
}
