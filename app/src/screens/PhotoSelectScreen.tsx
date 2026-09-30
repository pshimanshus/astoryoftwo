import { useState } from 'react';
import { copy } from '../content/copy';
import { sampleGallery } from '../content/sampleGallery';
import { TornPhoto } from '../components/TornPhoto';
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
    <div className="sheet" style={{ padding: '32px 22px 20px' }}>
      <span className="sheet__spine">03 — the proof</span>

      <p className="headline" style={{ fontSize: 'clamp(24px, 7vw, 32px)' }}>{copy.photos.title}</p>
      <p className="kicker">{copy.photos.hint}</p>

      <div className="mosaic" style={{ flex: 1, overflowY: 'auto', marginTop: 'var(--space-4)', paddingBottom: 4 }}>
        {sampleGallery.map((ph) => {
          const on = picked.includes(ph.id);
          return (
            <button key={ph.id} onClick={() => toggle(ph.id)} style={{ position: 'relative' }} aria-pressed={on}>
              <TornPhoto src={ph.url} alt="" seed={ph.id} width="100%" height="100%"
                style={{ opacity: on ? 1 : 0.8, transition: 'opacity 0.2s' }} />
              {on && (
                <svg viewBox="0 0 100 100" style={{ position: 'absolute', inset: -6, pointerEvents: 'none' }}>
                  <path d="M 50 8 C 78 9, 92 28, 90 50 C 92 74, 72 92, 48 91 C 22 90, 8 72, 9 49 C 7 24, 25 7, 50 8 Z"
                    fill="none" stroke="var(--accent)" strokeWidth="3" strokeLinecap="round" opacity={0.85} />
                </svg>
              )}
            </button>
          );
        })}
      </div>

      <button disabled={picked.length === 0} onClick={done}
        className={`stamp stamp--block ${picked.length ? 'stamp--solid' : ''}`} style={{ marginTop: 'var(--space-4)' }}>
        {copy.photos.done} {picked.length ? `(${picked.length})` : ''}
      </button>
    </div>
  );
}
