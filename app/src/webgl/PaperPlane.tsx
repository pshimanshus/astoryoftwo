import { useMemo } from 'react';
import * as THREE from 'three';

// The paper substrate itself — a full-bleed background layer behind every screen. Procedural fbm
// noise perturbs the surface normal for fine fibre detail, lit by ONE hardcoded raking key light
// (the brief's binding rule: no environment map, no second light, nothing emissive). Deliberately
// a raw ShaderMaterial, not MeshStandardMaterial/CSM — this plane never moves and never receives
// a cast shadow, so CSM's normal-recompute/shadow machinery (built for InkSheet/PageTurn, which
// genuinely deform) would be unneeded complexity here.
//
// Rendered directly in clip space (vertex shader ignores the camera's model/view/projection
// matrices) so it always exactly fills the viewport regardless of camera framing or aspect ratio
// — the classic "full-screen background quad" trick. Geometry is a plain PlaneGeometry(2, 2)
// centered at the origin, whose corners already sit at NDC (-1,-1) to (1,1).
const VERTEX_SHADER = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

const FRAGMENT_SHADER = /* glsl */ `
  varying vec2 vUv;
  uniform vec2 uResolution;
  uniform vec3 uPaperColor;
  uniform float uGrainAngle;    // radians — the paper's machine direction (--grain-angle)
  uniform float uLightElevation; // radians — how low/raking the key light is (--light-elevation)

  // Classic value-noise + fbm. Cheap, no texture lookups, tuned for fine paper-fibre grain
  // rather than large-scale features.
  float hash(vec2 p) {
    p = fract(p * vec2(123.34, 456.21));
    p += dot(p, p + 45.32);
    return fract(p.x * p.y);
  }

  float valueNoise(vec2 p) {
    vec2 i = floor(p);
    vec2 f = fract(p);
    float a = hash(i);
    float b = hash(i + vec2(1.0, 0.0));
    float c = hash(i + vec2(0.0, 1.0));
    float d = hash(i + vec2(1.0, 1.0));
    vec2 u = f * f * (3.0 - 2.0 * f);
    return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
  }

  float fbm(vec2 p) {
    float sum = 0.0;
    float amp = 0.5;
    for (int i = 0; i < 4; i++) {
      sum += amp * valueNoise(p);
      p *= 2.02;
      amp *= 0.5;
    }
    return sum;
  }

  void main() {
    // Stretch the noise field along the grain axis so fibre reads as directional, not isotropic
    // static — the same --grain-angle the ink layer wicks along (InkSheet), so the whole sheet
    // shares one material identity.
    vec2 aspectUv = vUv * uResolution / min(uResolution.x, uResolution.y);
    float ca = cos(uGrainAngle);
    float sa = sin(uGrainAngle);
    vec2 grainUv = vec2(aspectUv.x * ca - aspectUv.y * sa, aspectUv.x * sa + aspectUv.y * ca);
    vec2 fibreUv = vec2(grainUv.x * 14.0, grainUv.y * 90.0); // fine along-grain, coarse cross-grain

    float height = fbm(fibreUv);

    // Approximate the surface normal from the height field's local gradient (forward differences).
    float eps = 0.01;
    float hx = fbm(fibreUv + vec2(eps, 0.0)) - height;
    float hy = fbm(fibreUv + vec2(0.0, eps)) - height;
    vec3 normal = normalize(vec3(-hx * 6.0, -hy * 6.0, 1.0));

    // One hardcoded raking key light — elevation only (no azimuth uniform needed for a static
    // background; the fixed diagonal below reads correctly at --light-elevation's shallow angle).
    vec3 lightDir = normalize(vec3(cos(uLightElevation), sin(uLightElevation) * 0.4, sin(uLightElevation)));
    float lambert = max(dot(normal, lightDir), 0.0);

    // Ambient floor so crevices read as shaded paper, not black — paper doesn't have hard shadows.
    float shade = mix(0.86, 1.06, lambert);
    vec3 color = uPaperColor * shade;

    // A very subtle darkening in the noise valleys reads as grain/fibre, independent of lighting.
    color *= mix(0.985, 1.0, smoothstep(0.35, 0.65, height));

    gl_FragColor = vec4(color, 1.0);
  }
`;

export interface PaperPlaneProps {
  /** CSS pixel size of the canvas, used to keep the grain's aspect correct. */
  width: number;
  height: number;
}

export function PaperPlane({ width, height }: PaperPlaneProps) {
  const uniforms = useMemo(
    () => ({
      uResolution: { value: new THREE.Vector2(width, height) },
      uPaperColor: { value: new THREE.Color('#f6f1e7') }, // --paper, hardcoded — see MicButton.tsx note
      uGrainAngle: { value: (12 * Math.PI) / 180 }, // --grain-angle: 12deg
      uLightElevation: { value: (14 * Math.PI) / 180 }, // --light-elevation: 14deg
    }),
    [], // eslint-disable-line react-hooks/exhaustive-deps -- resolution updates below, not recreated
  );
  uniforms.uResolution.value.set(width, height);

  return (
    <mesh renderOrder={-1} frustumCulled={false}>
      <planeGeometry args={[2, 2]} />
      <shaderMaterial
        vertexShader={VERTEX_SHADER}
        fragmentShader={FRAGMENT_SHADER}
        uniforms={uniforms}
        depthTest={false}
        depthWrite={false}
      />
    </mesh>
  );
}
