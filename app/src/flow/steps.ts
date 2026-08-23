export type Step =
  | 'landing' | 'hello' | 'photos' | 'review' | 'record'
  | 'printing' | 'reveal' | 'rate' | 'send';

export const ORDER: Step[] = [
  'landing', 'hello', 'photos', 'review', 'record', 'printing', 'reveal', 'rate', 'send',
];

export function nextStep(step: Step): Step {
  const i = ORDER.indexOf(step);
  return ORDER[Math.min(i + 1, ORDER.length - 1)];
}

export function prevStep(step: Step): Step {
  const i = ORDER.indexOf(step);
  return ORDER[Math.max(i - 1, 0)];
}

export const isFirst = (step: Step) => ORDER.indexOf(step) === 0;
export const isLast = (step: Step) => ORDER.indexOf(step) === ORDER.length - 1;
