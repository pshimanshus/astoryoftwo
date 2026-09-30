import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import App from './App';

// THROWAWAY spike branch — delete alongside src/webgl/PageTurnSpike.tsx once the real
// printing->reveal wiring (build order step 6) lands. Isolates the CSM bend/shadow pipeline from
// real flow state so it can be verified on its own before being wired in.
const isSpike = new URLSearchParams(window.location.search).get('spike') === 'pageturn';

async function main() {
  const Root = isSpike ? (await import('./webgl/PageTurnSpike')).PageTurnSpike : App;
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <Root />
    </StrictMode>,
  );
}

main();
