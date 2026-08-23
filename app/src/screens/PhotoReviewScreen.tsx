import { copy } from '../content/copy';
import { sampleGallery } from '../content/sampleGallery';
import { HandDrawnArrow } from '../components/HandDrawnArrow';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';

export function PhotoReviewScreen() {
  const { advance } = useFlow();
  const { session } = useSession();
  const chosen = sampleGallery.filter((p) => session.photos.includes(p.id));

  return (
    <div style={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 20, gap: 22, justifyContent: 'center' }}>
      <div style={{ display: 'flex', gap: 12, overflowX: 'auto', padding: '8px 4px' }}>
        {chosen.map((p) => (
          <img key={p.id} src={p.url} alt=""
            style={{ width: 180, height: 240, flex: '0 0 auto', objectFit: 'cover', borderRadius: 18, boxShadow: '0 8px 20px rgba(0,0,0,0.18)' }} />
        ))}
      </div>
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 10, alignSelf: 'center' }}>
        <HandDrawnArrow caption={copy.review.mic} />
        <button onClick={advance} aria-label="record your story"
          style={{ width: 72, height: 72, borderRadius: '50%', background: 'var(--accent)', color: '#fff', display: 'grid', placeItems: 'center', fontSize: 30 }}>
          🎙
        </button>
      </div>
    </div>
  );
}
