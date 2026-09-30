import { useMemo } from 'react';
import * as THREE from 'three';

/** A plane subdivided densely along its bend axis (x) and sparsely across it (y) — geometry
 * detail should follow curvature, and all the curvature in a page turn runs along x. Authored
 * with the hinge at x=0 (translated from PlaneGeometry's default centered origin) so the vertex
 * shader's bend math (see PageTurn.tsx) can treat local x directly as distance-from-hinge. */
export function usePageBendGeometry(width: number, height: number) {
  return useMemo(() => {
    const geo = new THREE.PlaneGeometry(width, height, 60, 8);
    geo.translate(width / 2, 0, 0);
    return geo;
  }, [width, height]);
}
