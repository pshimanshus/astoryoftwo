import { copy } from '../content/copy';
import { useFlow } from '../flow/FlowProvider';

export function CapReachedScreen() {
  const { goTo } = useFlow();
  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', gap: 18, padding: 32, textAlign: 'center' }}>
      <p style={{ fontSize: 24, fontFamily: 'var(--font-hand)' }}>{copy.cap.title}</p>
      <p style={{ fontSize: 16, lineHeight: 1.5, color: 'var(--ink-soft)' }}>{copy.cap.body}</p>
      <button onClick={() => goTo('landing')} style={{ padding: 14, borderRadius: 14, background: 'var(--ink)', color: 'var(--paper)', fontSize: 16 }}>
        back to start
      </button>
    </div>
  );
}
