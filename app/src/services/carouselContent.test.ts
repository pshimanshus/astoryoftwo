import { describe, it, expect } from 'vitest';
import { buildSlides } from './carouselContent';
import { createInitialSession } from '../session/session';
import { houseSlides } from '../content/houseSlides';

describe('buildSlides', () => {
  it('produces one slide per template with names interpolated', () => {
    const s = { ...createInitialSession(), creatorName: 'Arjun', partnerName: 'Mira', storyBeats: ['we met in the rain', 'we argued about coffee'] };
    const slides = buildSlides(s);
    expect(slides).toHaveLength(houseSlides.length);
    expect(slides[0].caption).toBe('the day Arjun first really saw Mira.');
    expect(slides[3].caption).toBe('and still, Arjun & Mira.');
  });

  it('fills {beat} slots from storyBeats, cycling if needed', () => {
    const s = { ...createInitialSession(), creatorName: 'A', partnerName: 'B', storyBeats: ['only beat'] };
    const slides = buildSlides(s);
    expect(slides[1].caption).toBe('only beat');
    expect(slides[2].caption).toBe('only beat'); // cycled
  });

  it('uses the warm placeholder when partner name is blank', () => {
    const s = { ...createInitialSession(), creatorName: 'A', partnerName: '', storyBeats: ['x'] };
    expect(buildSlides(s)[0].caption).toBe('the day A first really saw your person.');
  });
});
