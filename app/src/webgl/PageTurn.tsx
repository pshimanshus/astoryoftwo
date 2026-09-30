import { useMemo } from 'react';
import * as THREE from 'three';
import CustomShaderMaterial from 'three-custom-shader-material';
import CSMVanilla from 'three-custom-shader-material/vanilla';
import { usePageBendGeometry } from './pageBendGeometry';

// The printing -> reveal page turn: a subdivided plane bent by a vertex shader patched onto
// MeshStandardMaterial via CSM, so the bend keeps real PBR lighting/shadow — that's the whole
// reason it reads as paper being turned rather than a flat textured quad rotating.
//
// The bend is a "roll" (arc-length-preserving curl around a hinge at local x=0), not a rigid
// door-hinge rotation: the whole point of turning a page is that the sheet visibly flexes as it
// goes, which a rigid rotation can't show. At progress=0 it's exactly flat (avoids the R=width/0
// singularity at zero progress via the step() blend below, not epsilon-clamping).
const BEND_VERTEX_SHADER = /* glsl */ `
  uniform float uProgress; // 0 = flat (unturned), 1 = fully turned (180 degrees)
  uniform float uWidth;    // plane width along the bend axis, hinge at local x=0

  void main() {
    float maxAngle = 3.14159265 * uProgress;
    float R = uWidth / max(maxAngle, 0.0001);
    float angle = (position.x / uWidth) * maxAngle;

    float s = sin(angle);
    float c = cos(angle);

    vec3 bentPosition = vec3(R * s, position.y, R * (1.0 - c));
    vec3 bentNormal = vec3(s, 0.0, c); // the flat (0,0,1) normal rotated by angle, around Y

    float isBending = step(0.0001, uProgress);
    csm_Position = mix(position, bentPosition, isBending);
    csm_Normal = mix(normal, normalize(bentNormal), isBending);
  }
`;

const PAPER_COLOR = '#f6f1e7'; // --paper, hardcoded — three.js materials need a real hex, not a CSS var

export interface PageTurnProps {
  /** 0 = flat/unturned, 1 = fully turned. */
  progress: number;
  /** The finished illustration, shown on the sheet's back face. Front face is plain paper. */
  backTexture?: THREE.Texture | null;
  width?: number;
  height?: number;
}

function useBendUniforms(progress: number, width: number) {
  const uniforms = useMemo(
    () => ({ uProgress: { value: progress }, uWidth: { value: width } }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [width],
  );
  uniforms.uProgress.value = progress; // mutate in place; both the colour and depth materials share this object
  return uniforms;
}

/**
 * CSM does NOT automatically make the bend respect the shadow-map pass — MeshStandardMaterial's
 * castShadow silhouette is normally rendered with a separate, auto-generated MeshDepthMaterial
 * that knows nothing about csm_Position. Confirmed against the library's own docs: the only
 * shadow-related hook it documents (csm_DepthAlpha) exists specifically because you're expected
 * to build your own customDepthMaterial with the SAME vertex shader. Without this, castShadow
 * on a bent sheet casts the shadow of the original FLAT geometry. Verified via a throwaway spike
 * (src/webgl/PageTurnSpike.tsx) before this was wired to real screens.
 */
function useBendDepthMaterial(uniforms: ReturnType<typeof useBendUniforms>) {
  return useMemo(
    () =>
      new CSMVanilla({
        baseMaterial: THREE.MeshDepthMaterial,
        vertexShader: BEND_VERTEX_SHADER,
        uniforms,
        depthPacking: THREE.RGBADepthPacking,
      }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );
}

export function PageTurn({ progress, backTexture = null, width = 3, height = 4 }: PageTurnProps) {
  const geometry = usePageBendGeometry(width, height);
  const uniforms = useBendUniforms(progress, width);
  const depthMaterial = useBendDepthMaterial(uniforms);

  return (
    <group>
      {/* Front face — plain paper, no texture. Faces the camera at progress=0. */}
      <mesh geometry={geometry} castShadow receiveShadow customDepthMaterial={depthMaterial}>
        <CustomShaderMaterial
          baseMaterial={THREE.MeshStandardMaterial}
          vertexShader={BEND_VERTEX_SHADER}
          uniforms={uniforms}
          color={PAPER_COLOR}
          roughness={0.9}
          metalness={0}
          side={THREE.FrontSide}
        />
      </mesh>
      {/* Back face — the finished illustration. Same bent geometry, opposite winding, so it's
          only visible once the sheet has turned far enough to show its underside. */}
      <mesh geometry={geometry} castShadow receiveShadow customDepthMaterial={depthMaterial}>
        <CustomShaderMaterial
          baseMaterial={THREE.MeshStandardMaterial}
          vertexShader={BEND_VERTEX_SHADER}
          uniforms={uniforms}
          color={backTexture ? '#ffffff' : PAPER_COLOR}
          map={backTexture}
          roughness={0.9}
          metalness={0}
          side={THREE.BackSide}
        />
      </mesh>
    </group>
  );
}
