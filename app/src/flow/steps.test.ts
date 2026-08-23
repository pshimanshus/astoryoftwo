import { describe, it, expect } from 'vitest';
import { ORDER, nextStep, prevStep, isFirst, isLast } from './steps';

describe('flow steps', () => {
  it('has the linear happy-path order', () => {
    expect(ORDER).toEqual([
      'landing', 'hello', 'photos', 'review', 'record', 'printing', 'reveal', 'rate', 'send',
    ]);
  });

  it('advances forward through the order', () => {
    expect(nextStep('landing')).toBe('hello');
    expect(nextStep('record')).toBe('printing');
  });

  it('stays on the last step when advancing past the end', () => {
    expect(nextStep('send')).toBe('send');
  });

  it('goes back through the order', () => {
    expect(prevStep('hello')).toBe('landing');
  });

  it('stays on the first step when going back past the start', () => {
    expect(prevStep('landing')).toBe('landing');
  });

  it('knows first and last', () => {
    expect(isFirst('landing')).toBe(true);
    expect(isLast('send')).toBe(true);
    expect(isLast('reveal')).toBe(false);
  });
});
