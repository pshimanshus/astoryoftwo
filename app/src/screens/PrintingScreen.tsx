import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';
import { deriveStoryBeats, PHASE_TIMINGS } from '../services/fakeGeneration';
import { buildSlides } from '../services/carouselContent';

type Phase = 'greet' | 'read' | 'feed';

export function PrintingScreen() {
  const { advance } = useFlow();
  const { session, update } = useSession();
  const [phase, setPhase] = useState<Phase>('greet');
  const [followed, setFollowed] = useState(false);
  const [askDismissed, setAskDismissed] = useState(false);

  // Compute the faked generation once on mount.
  useEffect(() => {
    const beats = deriveStoryBeats(session);
    update({ storyBeats: beats, slides: buildSlides({ ...session, storyBeats: beats }) });
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    const t1 = setTimeout(() => setPhase('read'), PHASE_TIMINGS.greet);
    const t2 = setTimeout(() => setPhase('feed'), PHASE_TIMINGS.greet + PHASE_TIMINGS.read);
    const t3 = setTimeout(() => advance(), PHASE_TIMINGS.greet + PHASE_TIMINGS.read + PHASE_TIMINGS.feed);
    return () => { clearTimeout(t1); clearTimeout(t2); clearTimeout(t3); };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const name = session.creatorName || 'friend';

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 24, gap: 16, justifyContent: 'center' }}>
      <motion.div animate={{ opacity: [0.4, 1, 0.4] }} transition={{ repeat: Infinity, duration: 2 }}
        style={{ fontFamily: 'var(--font-hand)', fontSize: 16, color: 'var(--ink-soft)', textAlign: 'center' }}>
        …drawing your story…
      </motion.div>

      {phase === 'greet' && (
        <p style={{ fontSize: 20, lineHeight: 1.4, textAlign: 'center' }}>{copy.printing.greet(name)}</p>
      )}

      {phase === 'read' && (
        <p style={{ fontSize: 16, lineHeight: 1.6 }}>
          We started A Story of Two for one couple, on cheap paper, late at night. Every story since has been
          someone trusting us with the smallest true thing about their love. Yours is printing now.
        </p>
      )}

      {phase === 'feed' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          <div style={{ display: 'flex', gap: 10, overflowX: 'auto' }}>
            {[1, 2, 3].map((n) => (
              <img key={n} src={`https://picsum.photos/seed/astory-feed${n}/300/380`} alt=""
                style={{ width: 150, height: 190, flex: '0 0 auto', borderRadius: 14, objectFit: 'cover' }} />
            ))}
          </div>
          {!askDismissed && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, alignItems: 'center' }}>
              <p style={{ fontSize: 13, color: 'var(--ink-soft)', textAlign: 'center' }}>{copy.printing.askOnce}</p>
              <div style={{ display: 'flex', gap: 8 }}>
                <button onClick={() => setFollowed(true)}
                  style={{ padding: '8px 16px', borderRadius: 12, background: followed ? 'var(--ink)' : 'var(--accent)', color: '#fff', fontSize: 14 }}>
                  {followed ? 'following ♥' : copy.printing.follow}
                </button>
                <button onClick={() => setAskDismissed(true)} style={{ color: 'var(--ink-soft)', fontSize: 13 }}>not now</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
