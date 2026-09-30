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

  return (
    <div className="sheet" style={{ padding: '56px 28px 28px', gap: 'var(--space-7)' }}>
      <span className="sheet__spine">02 — who's this for</span>

      <p className="headline">{copy.hello.prompt}</p>

      <div className="choice-row">
        <button className="choice" aria-pressed={rel === 'together'} onClick={() => setRel('together')}>
          {copy.hello.together}
        </button>
        <button className="choice" aria-pressed={rel === 'sending'} onClick={() => setRel('sending')}>
          {copy.hello.sending}
        </button>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
        <label className="field">
          <span className="field__tag">you,</span>
          <input value={me} placeholder={copy.hello.yourName} onChange={(e) => setMe(e.target.value)} />
        </label>
        <label className="field">
          <span className="field__tag">for</span>
          <input value={them} placeholder={copy.hello.theirName} onChange={(e) => setThem(e.target.value)} />
        </label>
      </div>

      <div className="spacer" />

      <button disabled={!ready} onClick={begin} className={`stamp stamp--block ${ready ? 'stamp--accent' : ''}`}>
        {copy.hello.continue}
      </button>
    </div>
  );
}
