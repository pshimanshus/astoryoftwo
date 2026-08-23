import { describe, it, expect, beforeEach } from 'vitest';
import {
  MAX_CAROUSELS, getDeviceId, getCarouselsCreated, getRemaining,
  recordCarouselCreated, hasReachedCap,
} from './deviceId';

beforeEach(() => localStorage.clear());

describe('deviceId + 3-cap', () => {
  it('creates and persists a stable device id', () => {
    const id = getDeviceId();
    expect(id).toMatch(/^dev_/);
    expect(getDeviceId()).toBe(id); // stable across calls
  });

  it('starts with zero created and full remaining', () => {
    expect(getCarouselsCreated()).toBe(0);
    expect(getRemaining()).toBe(MAX_CAROUSELS);
    expect(hasReachedCap()).toBe(false);
  });

  it('counts up and reaches the cap at 3', () => {
    recordCarouselCreated();
    recordCarouselCreated();
    expect(getRemaining()).toBe(1);
    expect(hasReachedCap()).toBe(false);
    recordCarouselCreated();
    expect(getCarouselsCreated()).toBe(3);
    expect(getRemaining()).toBe(0);
    expect(hasReachedCap()).toBe(true);
  });

  it('never lets remaining go negative', () => {
    for (let i = 0; i < 5; i++) recordCarouselCreated();
    expect(getRemaining()).toBe(0);
  });
});
