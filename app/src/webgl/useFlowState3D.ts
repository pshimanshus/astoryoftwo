import { useMemo } from 'react';
import { useFlow } from '../flow/FlowProvider';
import { useSession } from '../session/SessionProvider';
import type { Slide } from '../session/session';

// Thin bridge for components rendered inside <Canvas>. R3F's Canvas doesn't break React context —
// SheetCanvas mounts inside PaperBackground, which is already inside FlowProvider/SessionProvider
// in App.tsx — so meshes can call this directly instead of the screen tree threading step/session
// down as Canvas props. Note: whether the user is actively recording (vs merely on the record
// screen) is NOT carried here — that's read straight from micLevel.ts's module store inside each
// mesh's own useFrame, matching the pattern of keeping audio-rate signals out of React entirely.
export interface FlowState3D {
  step: string; // Step | 'cap-reached' — kept as string here so this file needs no Step import
  coverSlide: Slide | null;
}

export function useFlowState3D(): FlowState3D {
  const { step } = useFlow();
  const { session } = useSession();
  const coverSlide = session.slides?.[0] ?? null;
  return useMemo(() => ({ step, coverSlide }), [step, coverSlide]);
}
