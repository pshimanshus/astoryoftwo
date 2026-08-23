import { describe, it, expect } from 'vitest';
import { deriveStoryBeats, PHASE_TIMINGS } from './fakeGeneration';
import { createInitialSession } from '../session/session';

describe('fakeGeneration', () => {
  it('derives a deterministic, non-empty set of beats from the session', () => {
    const s = { ...createInitialSession(), relationship: 'together' as const, creatorName: 'Arjun', partnerName: 'Mira' };
    const a = deriveStoryBeats(s);
    const b = deriveStoryBeats(s);
    expect(a.length).toBeGreaterThanOrEqual(3);
    expect(a).toEqual(b); // deterministic
    expect(a.join(' ')).toContain('Mira'); // personalized
  });

  it('changes when names change', () => {
    const base = { ...createInitialSession(), relationship: 'sending' as const, creatorName: 'A', partnerName: 'B' };
    const other = { ...base, partnerName: 'C' };
    expect(deriveStoryBeats(base)).not.toEqual(deriveStoryBeats(other));
  });

  it('exposes positive phase timings', () => {
    expect(PHASE_TIMINGS.greet).toBeGreaterThan(0);
    expect(PHASE_TIMINGS.read).toBeGreaterThan(0);
    expect(PHASE_TIMINGS.feed).toBeGreaterThan(0);
  });
});
