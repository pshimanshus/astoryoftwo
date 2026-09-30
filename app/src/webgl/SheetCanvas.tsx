import { useEffect } from 'react';
import { Canvas, invalidate, useThree } from '@react-three/fiber';
import { PaperPlane } from './PaperPlane';
import { InkSheet } from './InkSheet';
import { useFlowState3D } from './useFlowState3D';
import { registerInvalidate } from './micLevel';

// The single persistent WebGL canvas — mounted once in PaperBackground.tsx, outside
// CurrentScreen's AnimatePresence, and never torn down by a step change. See PaperBackground.tsx
// for why: a canvas per screen would create/destroy a WebGL context on every one of the 9 steps
// and exhaust Safari's context cap.
//
// frameloop="demand": this app is mostly-static paper, not a continuous 3D scene. R3F renders
// once on mount (painting PaperPlane) and then sits idle — GPU cost near zero — until something
// calls invalidate(). InkSheet and PageTurn (the latter wired in a later build-order step) call it
// themselves, only while actively recording or mid-turn — see each file's own useFrame.

function Scene() {
  const { size } = useThree();
  const { step } = useFlowState3D();

  // Hands micLevel.ts a way to wake the demand-mode render loop, without that module ever
  // needing to import '@react-three/fiber' itself. See micLevel.ts's own comment.
  useEffect(() => {
    registerInvalidate(() => invalidate());
    return () => registerInvalidate(null);
  }, []);

  return (
    <>
      <PaperPlane width={size.width} height={size.height} />
      {step === 'record' && <InkSheet />}
    </>
  );
}

export default function SheetCanvas() {
  return (
    <Canvas
      frameloop="demand"
      dpr={[1, 2]}
      gl={{ antialias: false, alpha: true, powerPreference: 'low-power' }}
      camera={{ position: [0, 0, 5.6], fov: 40 }}
      style={{ position: 'absolute', inset: 0, zIndex: 0 }}
      aria-hidden
    >
      <ambientLight intensity={0.3} />
      <directionalLight position={[2, 3, 4]} intensity={1.1} />
      <Scene />
    </Canvas>
  );
}
