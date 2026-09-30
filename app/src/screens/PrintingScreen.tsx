import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { copy } from '../content/copy';
import { press } from '../styles/motion';
import { TornPhoto } from '../components/TornPhoto';
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
    <div className="sheet" style={{ padding: '64px 26px 32px', justifyContent: 'center', gap: 'var(--space-5)' }}>
      <span className="sheet__spine">06 — printing</span>

      {/* No infinite pulse here — reducedMotion="user" preserves opacity animations, so an
          infinite loop would keep running for a user who asked for less motion. Static text; the
          WebGL page-turn (printing->reveal) is where this screen's motion budget actually goes. */}
      <p className="kicker" style={{ marginBottom: 0 }}>…drawing your story…</p>

      {phase === 'greet' && <p className="headline" style={{ fontSize: 'clamp(22px, 7vw, 30px)' }}>{copy.printing.greet(name)}</p>}

      {phase === 'read' && (
        <p className="lede" style={{ maxWidth: '30ch' }}>
          We started A Story of Two for one couple, on cheap paper, late at night. Every story since has been
          someone trusting us with the smallest true thing about their love. Yours is printing now.
        </p>
      )}

      {phase === 'feed' && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-5)' }}>
          <div style={{ display: 'flex', overflowX: 'auto', padding: '12px 20px 12px 0' }}>
            {[1, 2, 3].map((n, i) => (
              <div key={n} style={{ flex: '0 0 auto', marginLeft: i === 0 ? 0 : -30, zIndex: i }}>
                <TornPhoto src={`https://picsum.photos/seed/astory-feed${n}/300/400`} alt="" seed={`feed${n}`} width={140} height={188} />
              </div>
            ))}
          </div>
          {!askDismissed && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
              <p className="kicker" style={{ marginBottom: 0 }}>{copy.printing.askOnce}</p>
              <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
                <motion.button onClick={() => setFollowed(true)} whileTap={{ y: 1 }} transition={press}
                  className={`stamp ${followed ? 'stamp--solid' : 'stamp--accent'}`} style={{ padding: '10px 16px', fontSize: 11 }}>
                  {followed ? 'following ♥' : copy.printing.follow}
                </motion.button>
                <button onClick={() => setAskDismissed(true)} className="kicker" style={{ marginBottom: 0 }}>not now</button>
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
