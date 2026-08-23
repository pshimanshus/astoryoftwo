import type { SessionState, Slide } from '../session/session';
import { displayPartnerName } from '../session/session';
import { houseSlides } from '../content/houseSlides';

export function buildSlides(session: SessionState): Slide[] {
  const creator = session.creatorName.trim() || 'someone';
  const partner = displayPartnerName(session);
  let beatIdx = 0;
  const beats = session.storyBeats.length ? session.storyBeats : ['a story still being written'];

  return houseSlides.map((t) => {
    const caption = t.captionTemplate
      .replace(/\{creator\}/g, creator)
      .replace(/\{partner\}/g, partner)
      .replace(/\{beat\}/g, () => beats[beatIdx++ % beats.length]);
    return { id: t.id, imageUrl: t.imageUrl, caption };
  });
}
