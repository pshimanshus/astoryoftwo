import { createContext, useContext, useState, type ReactNode } from 'react';
import { type SessionState, createInitialSession } from './session';

interface SessionCtx {
  session: SessionState;
  update: (patch: Partial<SessionState>) => void;
  reset: () => void;
}

const Ctx = createContext<SessionCtx | null>(null);

export function SessionProvider({ children }: { children: ReactNode }) {
  const [session, setSession] = useState<SessionState>(createInitialSession);
  const update = (patch: Partial<SessionState>) => setSession((s) => ({ ...s, ...patch }));
  const reset = () => setSession(createInitialSession());
  return <Ctx.Provider value={{ session, update, reset }}>{children}</Ctx.Provider>;
}

export function useSession() {
  const c = useContext(Ctx);
  if (!c) throw new Error('useSession must be used within SessionProvider');
  return c;
}
