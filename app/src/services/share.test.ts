import { describe, it, expect } from 'vitest';
import { buildShareMessage, SHARE_TARGETS } from './share';
import { createInitialSession } from '../session/session';

describe('share', () => {
  it('addresses the partner and carries the invite url', () => {
    const s = { ...createInitialSession(), creatorName: 'Arjun', partnerName: 'Mira' };
    const msg = buildShareMessage(s);
    expect(msg.text).toContain('Mira');
    expect(msg.text.toLowerCase()).toContain('arjun');
    expect(msg.inviteUrl).toMatch(/^https?:\/\//);
  });

  it('falls back to the warm placeholder for a blank partner name', () => {
    const s = { ...createInitialSession(), creatorName: 'Arjun', partnerName: '' };
    expect(buildShareMessage(s).text).toContain('your person');
  });

  it('offers only send-only targets (no download/copy)', () => {
    const ids = SHARE_TARGETS.map((t) => t.id);
    expect(ids).toEqual(['whatsapp', 'whatsapp-status', 'instagram-story', 'wallpaper-mobile', 'wallpaper-desktop']);
    expect(ids).not.toContain('download');
    expect(ids).not.toContain('copy');
  });
});
