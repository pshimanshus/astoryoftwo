// THROWAWAY — de-risks the CSM bend + shadow pipeline in isolation before wiring PageTurn into
// real flow state. Delete this file and its main.tsx branch once the real printing->reveal
// integration (build order step 6) replaces it. Not part of the shipped app.
import { useState } from 'react';
import { Canvas } from '@react-three/fiber';
import { ContactShadows } from '@react-three/drei';
import { PageTurn } from './PageTurn';

export function PageTurnSpike() {
  const [progress, setProgress] = useState(0.35);
  return (
    <div style={{ width: '100vw', height: '100vh', background: '#15110d', position: 'relative' }}>
      <Canvas camera={{ position: [7, 4, 8], fov: 45 }} shadows dpr={[1, 2]}>
        <color attach="background" args={['#15110d']} />
        <ambientLight intensity={0.25} />
        {/* Exactly one key light — the brief's binding rule, honoured even in a spike. */}
        <directionalLight position={[3, 5, 2]} intensity={1.4} castShadow
          shadow-mapSize={[1024, 1024]} />
        <group position={[-1.5, 0, 0]}>
          <PageTurn progress={progress} />
        </group>
        {/* A real shadow-receiving plane — more diagnostic than ContactShadows' blurred
            approximation for checking whether the shadow silhouette follows the bend. */}
        <mesh position={[0, -2.05, 0]} rotation={[-Math.PI / 2, 0, 0]} receiveShadow>
          <planeGeometry args={[14, 14]} />
          <meshStandardMaterial color="#d8cfbd" />
        </mesh>
        <ContactShadows position={[0, -2.04, 0]} opacity={0.4} scale={10} blur={1.5} far={4} />
      </Canvas>
      <div style={{ position: 'absolute', bottom: 24, left: 24, right: 24, display: 'flex', flexDirection: 'column', gap: 8, fontFamily: 'monospace', color: '#f6f1e7' }}>
        <label htmlFor="progress">uProgress: {progress.toFixed(2)}</label>
        <input id="progress" type="range" min={0} max={1} step={0.01} value={progress}
          onChange={(e) => setProgress(Number(e.target.value))} />
      </div>
    </div>
  );
}
