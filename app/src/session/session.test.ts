import { describe, it, expect } from 'vitest';
import { createInitialSession, hasPhotos, hasRecording, displayPartnerName } from './session';

describe('session', () => {
  it('starts empty', () => {
    const s = createInitialSession();
    expect(s.relationship).toBeNull();
    expect(s.creatorName).toBe('');
    expect(s.partnerName).toBe('');
    expect(s.photos).toEqual([]);
    expect(s.recordingUrl).toBeNull();
    expect(s.storyBeats).toEqual([]);
    expect(s.rating).toBeNull();
    expect(s.slides).toBeNull();
  });

  it('detects photos and recording presence', () => {
    const s = createInitialSession();
    expect(hasPhotos(s)).toBe(false);
    expect(hasRecording(s)).toBe(false);
    expect(hasPhotos({ ...s, photos: ['a'] })).toBe(true);
    expect(hasRecording({ ...s, recordingUrl: 'blob:x' })).toBe(true);
  });

  it('falls back to a warm placeholder when partner name is blank', () => {
    const s = createInitialSession();
    expect(displayPartnerName(s)).toBe('your person');
    expect(displayPartnerName({ ...s, partnerName: 'Mira' })).toBe('Mira');
  });
});
