import { describe, it, expect } from 'vitest';
import { computeRms, getMicLevel, isMicActive, setMicActive, setMicLevel } from './micLevel';

describe('computeRms', () => {
  it('returns 0 for a perfectly silent buffer (all 128, the AnalyserNode zero-crossing)', () => {
    expect(computeRms(new Uint8Array(64).fill(128))).toBe(0);
  });

  it('returns 0 for an empty buffer', () => {
    expect(computeRms(new Uint8Array(0))).toBe(0);
  });

  it('returns 1 for a full-scale square wave (0/255 alternating)', () => {
    const bytes = new Uint8Array(64);
    for (let i = 0; i < bytes.length; i++) bytes[i] = i % 2 === 0 ? 0 : 255;
    expect(computeRms(bytes)).toBeCloseTo(1, 1);
  });

  it('is monotonic with amplitude', () => {
    const quiet = new Uint8Array(64).fill(140); // small deviation from 128
    const loud = new Uint8Array(64).fill(220); // large deviation from 128
    expect(computeRms(loud)).toBeGreaterThan(computeRms(quiet));
  });
});

describe('micLevel store', () => {
  it('reads back what was last written, module-level (not React state)', () => {
    setMicLevel(0.42);
    expect(getMicLevel()).toBe(0.42);
    setMicLevel(0);
    expect(getMicLevel()).toBe(0);
  });

  it('going inactive resets the level, so a stopped recording never leaves a stale non-zero level', () => {
    setMicActive(true);
    setMicLevel(0.7);
    expect(isMicActive()).toBe(true);
    expect(getMicLevel()).toBe(0.7);
    setMicActive(false);
    expect(isMicActive()).toBe(false);
    expect(getMicLevel()).toBe(0);
  });
});
