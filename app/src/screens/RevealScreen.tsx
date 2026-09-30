import { copy } from '../content/copy';
import { Carousel } from '../components/Carousel';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function RevealScreen() {
  const { advance } = useFlow();
  const { session } = useSession();
  return (
    // No entrance animation of its own — the App-level crossfade (App.tsx's CurrentScreen)
    // already handles the entrance. Two animations describing the same event is the bug that
    // shows up the moment the WebGL page turn (printing->reveal) is wired in: that turn IS this
    // screen's real entrance. sheet--plain: the carousel is its own framed object, not composed
    // against the margin rule.
    <div className="sheet sheet--plain" style={{ padding: '24px 22px', gap: 'var(--space-5)', justifyContent: 'center' }}>
      <p className="headline headline--hand" style={{ textAlign: 'center', maxWidth: 'none', margin: 0 }}>{copy.reveal.title}</p>
      <Carousel slides={session.slides ?? []} />
      <button onClick={advance} className="stamp stamp--solid stamp--block">
        continue
      </button>
    </div>
  );
}
