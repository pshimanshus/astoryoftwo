import { useState } from 'react';
import { copy } from '../content/copy';
import { sampleGallery } from '../content/sampleGallery';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function PhotoSelectScreen() {
  const { advance } = useFlow();
  const { session, update } = useSession();
  const [picked, setPicked] = useState<string[]>(session.photos);

  const toggle = (id: string) =>
    setPicked((p) => (p.includes(id) ? p.filter((x) => x !== id) : [...p, id]));

  const done = () => { update({ photos: picked }); advance(); };

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 20, gap: 14 }}>
      <p style={{ fontSize: 20 }}>{copy.photos.title}</p>
      <p style={{ fontSize: 14, color: 'var(--ink-soft)' }}>{copy.photos.hint}</p>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 8, overflowY: 'auto', flex: 1 }}>
        {sampleGallery.map((ph) => {
          const on = picked.includes(ph.id);
          return (
            <button key={ph.id} onClick={() => toggle(ph.id)}
              style={{ position: 'relative', aspectRatio: '1', borderRadius: 12, overflow: 'hidden', outline: on ? '3px solid var(--accent)' : 'none' }}>
              <img src={ph.url} alt="" style={{ width: '100%', height: '100%', objectFit: 'cover', opacity: on ? 1 : 0.85 }} />
              {on && <span style={{ position: 'absolute', top: 6, right: 6, background: 'var(--accent)', color: '#fff', borderRadius: '50%', width: 22, height: 22, display: 'grid', placeItems: 'center', fontSize: 13 }}>✓</span>}
            </button>
          );
        })}
      </div>
      <button disabled={picked.length === 0} onClick={done}
        style={{ padding: 14, borderRadius: 14, background: picked.length ? 'var(--ink)' : 'var(--hairline)', color: 'var(--paper)', fontSize: 16 }}>
        {copy.photos.done} {picked.length ? `(${picked.length})` : ''}
      </button>
    </div>
  );
}
