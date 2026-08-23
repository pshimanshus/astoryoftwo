import type { SessionState } from '../session/session';
import { displayPartnerName } from '../session/session';

export const PHASE_TIMINGS = { greet: 3500, read: 6000, feed: 5500 } as const;

const TOGETHER = (p: string) => [
  `the small fights that end in laughing about ${p}`,
  `the way ${p} hums when the food is good`,
  `choosing each other again on an ordinary Tuesday`,
];
const SENDING = (p: string) => [
  `the distance that never quite reached ${p}`,
  `saving the good news to tell ${p} first`,
  `counting days until ${p} is close again`,
];

export function deriveStoryBeats(session: SessionState): string[] {
  const p = displayPartnerName(session);
  return session.relationship === 'sending' ? SENDING(p) : TOGETHER(p);
}
