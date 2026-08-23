import { createContext, useContext, useState, type ReactNode } from 'react';
import { type Step, nextStep, prevStep } from './steps';

interface FlowCtx {
  step: Step | 'cap-reached';
  advance: () => void;
  back: () => void;
  goTo: (s: Step | 'cap-reached') => void;
}

const Ctx = createContext<FlowCtx | null>(null);

export function FlowProvider({ children }: { children: ReactNode }) {
  const [step, setStep] = useState<Step | 'cap-reached'>('landing');
  const advance = () => setStep((s) => (s === 'cap-reached' ? s : nextStep(s)));
  const back = () => setStep((s) => (s === 'cap-reached' ? 'landing' : prevStep(s)));
  const goTo = (s: Step | 'cap-reached') => setStep(s);
  return <Ctx.Provider value={{ step, advance, back, goTo }}>{children}</Ctx.Provider>;
}

export function useFlow() {
  const c = useContext(Ctx);
  if (!c) throw new Error('useFlow must be used within FlowProvider');
  return c;
}
