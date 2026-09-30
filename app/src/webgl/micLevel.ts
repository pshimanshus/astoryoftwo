// Module-level mutable store, deliberately NOT React state. RecordScreen's audio rAF loop writes
// here at audio rate (every animation frame while recording); InkSheet's useFrame reads it inside
// the WebGL render loop. Routing this through React state/context would re-render the component
// tree at audio rate for no reason — nothing outside the 3D layer needs to know the instantaneous
// level, only whether recording is happening at all (which IS real flow state, read separately).
//
// This file must NOT statically import '@react-three/fiber' (or anything that imports 'three') —
// RecordScreen.tsx imports it unconditionally, and RecordScreen is part of App.tsx's always-on
// screen list, not behind the lazy WebGL boundary. A static import here would pull three.js into
// the main bundle for every user, including the reduced-motion tier that must never fetch it —
// exactly the regression this file's own architecture exists to prevent. Instead, SheetCanvas
// hands this module a plain callback once it's actually mounted (see registerInvalidate below).
const state = { current: 0, active: false };
let wake: (() => void) | null = null;

/** Called once by SheetCanvas on mount, from inside the already-lazy-loaded WebGL layer — the
 * only place allowed to import '@react-three/fiber'. null on unmount (defensive; SheetCanvas is
 * actually persistent and never unmounts once loaded, see PaperBackground.tsx). */
export function registerInvalidate(fn: (() => void) | null) {
  wake = fn;
}

export function setMicLevel(level: number) {
  state.current = level;
  // frameloop="demand" means R3F never calls useFrame at all until something invalidates at
  // least once — flipping this module-level value doesn't wake the render loop on its own.
  // A no-op if no canvas is mounted (e.g. the reduced-motion tier, where RecordScreen still
  // runs normally and `wake` is simply never registered).
  wake?.();
}

export function getMicLevel(): number {
  return state.current;
}

/** Whether a MediaRecorder session is actively capturing right now — distinct from the level
 * itself, since a silent moment mid-recording (active, level 0) must still keep the ink decaying,
 * while an idle record screen (inactive, level 0) must not. RecordScreen sets this in start()/
 * stop(); InkSheet's useFrame reads it to decide whether to keep calling invalidate(). */
export function setMicActive(active: boolean) {
  state.active = active;
  if (!active) state.current = 0;
  wake?.(); // wake the render loop on both the start (seed) and stop (settle-tail) edges
}

export function isMicActive(): boolean {
  return state.active;
}

/** Root-mean-square of a Uint8Array time-domain buffer from AnalyserNode.getByteTimeDomainData,
 * normalised to roughly [0, 1]. 128 is silence (the unsigned-byte zero-crossing); deviation from
 * it is signal. */
export function computeRms(bytes: Uint8Array): number {
  if (bytes.length === 0) return 0;
  let sumSquares = 0;
  for (let i = 0; i < bytes.length; i++) {
    const centered = (bytes[i] - 128) / 128;
    sumSquares += centered * centered;
  }
  return Math.sqrt(sumSquares / bytes.length);
}
