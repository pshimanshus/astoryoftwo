import { useState } from 'react';
import { copy } from '../content/copy';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';
import type { Relationship } from '../session/session';

export function HelloScreen() {
  const { advance } = useFlow();
  const { session, update } = useSession();
  const [rel, setRel] = useState<Relationship | null>(session.relationship);
  const [me, setMe] = useState(session.creatorName);
  const [them, setThem] = useState(session.partnerName);

  const ready = rel !== null && me.trim().length > 0;
  const begin = () => { update({ relationship: rel, creatorName: me.trim(), partnerName: them.trim() }); advance(); };

  const choice = (value: Relationship, label: string) => (
    <button onClick={() => setRel(value)}
      style={{ padding: '12px 16px', borderRadius: 14, border: `1.5px solid ${rel === value ? 'var(--ink)' : 'var(--hairline)'}`, background: rel === value ? 'var(--ink)' : 'transparent', color: rel === value ? 'var(--paper)' : 'var(--ink)' }}>
      {label}
    </button>
  );

  const field = (ph: string, v: string, on: (s: string) => void) => (
    <input value={v} placeholder={ph} onChange={(e) => on(e.target.value)}
      style={{ padding: '12px 14px', borderRadius: 12, border: '1.5px solid var(--hairline)', background: 'transparent', fontFamily: 'var(--font-body)', fontSize: 16 }} />
  );

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', justifyContent: 'center', gap: 18, padding: 28 }}>
      <p style={{ fontSize: 20, lineHeight: 1.35 }}>{copy.hello.prompt}</p>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {choice('together', copy.hello.together)}
        {choice('sending', copy.hello.sending)}
      </div>
      {field(copy.hello.yourName, me, setMe)}
      {field(copy.hello.theirName, them, setThem)}
      <button disabled={!ready} onClick={begin}
        style={{ marginTop: 8, padding: '14px', borderRadius: 14, background: ready ? 'var(--accent)' : 'var(--hairline)', color: 'var(--paper)', fontSize: 16 }}>
        {copy.hello.continue}
      </button>
    </div>
  );
}
