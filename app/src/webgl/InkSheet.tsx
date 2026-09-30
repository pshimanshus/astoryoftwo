import { useEffect, useMemo, useRef } from 'react';
import { useFrame, useThree } from '@react-three/fiber';
import * as THREE from 'three';
import { getMicLevel, isMicActive } from './micLevel';

// RecordScreen's real, simplified ink+cockle: NOT the full incompressible-fluid pressure solve —
// a single ping-ponged diffusion+decay pass. Two things keep this on-theme rather than reading as
// a generic reactive blob:
//   - ANISOTROPIC blur: sample offsets scaled by a grain-direction vector, not a uniform radius —
//     this is what makes ink wick further along the paper's machine direction than across it.
//   - a PERMANENT-BUCKLE channel: the texture's G channel is a running max of R, monotonic, never
//     decays — free, same pass, and it's the only way this cheap a model gets a genuinely
//     permanent mark rather than a temporary one.
// RGBA8 targets, 144px square — deliberately not the brief's 256/512 half-float sizing (that was
// sized for a real pressure solver this pass doesn't build); RGBA8 sidesteps the iOS half-float
// risk entirely, by construction.

const SIM_SIZE = 144;
const PLANE_WIDTH = 2.7;
const PLANE_HEIGHT = 4.7;

const SIM_VERTEX_SHADER = /* glsl */ `
  varying vec2 vUv;
  void main() {
    vUv = uv;
    gl_Position = vec4(position.xy, 0.0, 1.0);
  }
`;

const SIM_FRAGMENT_SHADER = /* glsl */ `
  varying vec2 vUv;
  uniform sampler2D uPrev;
  uniform vec2 uTexel;       // 1/resolution
  uniform vec2 uGrainDir;    // normalized, the paper's machine direction
  uniform float uSeedAmount; // this frame's injection, driven by mic RMS
  uniform float uDecay;      // per-frame multiplicative decay
  uniform float uAspect;     // plane width/height — keeps the splat circular in WORLD space,
                              // not squashed by the mesh's aspect ratio in UV space

  void main() {
    vec2 cross_ = vec2(-uGrainDir.y, uGrainDir.x);

    // Anisotropic blur: wider taps along the grain, narrow across it. 5 taps along, 3 across.
    float sum = 0.0;
    float weight = 0.0;
    for (int i = -2; i <= 2; i++) {
      vec2 offset = uGrainDir * uTexel * float(i) * 2.2;
      float w = 1.0 - abs(float(i)) * 0.18;
      sum += texture2D(uPrev, vUv + offset).r * w;
      weight += w;
    }
    for (int j = -1; j <= 1; j++) {
      vec2 offset = cross_ * uTexel * float(j) * 1.1;
      float w = 0.6 - abs(float(j)) * 0.18;
      sum += texture2D(uPrev, vUv + offset).r * w;
      weight += w;
    }
    float blurred = sum / weight;

    // Seed a splat at the sheet's centre — the "nib" — sized/intensified by mic level. Corrected
    // for the mesh's aspect ratio so the splat is circular in world space, not stretched into an
    // ellipse by UV distance alone — that stretching would swamp the blur's actual anisotropy.
    vec2 centered = vUv - 0.5;
    centered.x *= uAspect;
    float distFromNib = length(centered);
    float splat = uSeedAmount * smoothstep(0.1, 0.0, distFromNib);

    float density = clamp(blurred * uDecay + splat, 0.0, 1.0);
    float prevMax = texture2D(uPrev, vUv).g;
    float permanentMax = max(prevMax, density);

    gl_FragColor = vec4(density, permanentMax, 0.0, 1.0);
  }
`;

const DISPLAY_VERTEX_SHADER = /* glsl */ `
  uniform sampler2D uInkMap;
  varying vec2 vUv;
  varying float vWetness;

  void main() {
    vUv = uv;
    vec4 ink = texture2D(uInkMap, uv);
    float wetness = max(ink.r, ink.g);
    vWetness = wetness;

    // Cockle: low ridges running parallel to the grain — a constrained sheet that swells
    // cross-grain has nowhere to go but up. Sine ridges phased across the cross-grain axis,
    // amplitude driven by wetness (current ink OR permanent buckle, whichever is larger).
    vec3 pos = position;
    float ridge = sin(uv.y * 34.0) * 0.06 + sin(uv.x * 21.0 + uv.y * 9.0) * 0.03;
    pos.z += ridge * wetness;

    vec4 mvPosition = modelViewMatrix * vec4(pos, 1.0);
    gl_Position = projectionMatrix * mvPosition;
  }
`;

const DISPLAY_FRAGMENT_SHADER = /* glsl */ `
  uniform sampler2D uInkMap;
  uniform vec3 uPaperColor;
  uniform vec3 uInkColor;
  uniform float uSigma; // Beer-Lambert absorption coefficient, --ink-sigma
  varying vec2 vUv;
  varying float vWetness;

  void main() {
    float density = texture2D(uInkMap, vUv).r;
    // Beer-Lambert: pooled ink reads DARKER, not more opaque — paper * exp(-k * absorbance).
    float absorption = exp(-uSigma * density);
    vec3 color = mix(uInkColor, uPaperColor, absorption);
    // A faint sheen where the sheet is wet, independent of ink colour.
    color += vWetness * 0.015;
    gl_FragColor = vec4(color, 1.0);
  }
`;

function makeSimMaterial(texel: THREE.Vector2) {
  return new THREE.ShaderMaterial({
    vertexShader: SIM_VERTEX_SHADER,
    fragmentShader: SIM_FRAGMENT_SHADER,
    uniforms: {
      uPrev: { value: null },
      uTexel: { value: texel },
      uGrainDir: { value: new THREE.Vector2(Math.cos((12 * Math.PI) / 180), Math.sin((12 * Math.PI) / 180)) },
      uSeedAmount: { value: 0 },
      uDecay: { value: 0.965 },
      uAspect: { value: PLANE_WIDTH / PLANE_HEIGHT },
    },
    depthTest: false,
    depthWrite: false,
  });
}

export function InkSheet() {
  const { gl } = useThree();
  const geometry = useMemo(() => new THREE.PlaneGeometry(PLANE_WIDTH, PLANE_HEIGHT, 48, 64), []);

  // Ping-pong render targets + an offscreen scene/camera to run the sim pass into them.
  const targets = useMemo(
    () => [
      new THREE.WebGLRenderTarget(SIM_SIZE, SIM_SIZE, { depthBuffer: false, stencilBuffer: false }),
      new THREE.WebGLRenderTarget(SIM_SIZE, SIM_SIZE, { depthBuffer: false, stencilBuffer: false }),
    ],
    [],
  );
  const readIndex = useRef(0);
  const simScene = useMemo(() => new THREE.Scene(), []);
  const simCamera = useMemo(() => new THREE.OrthographicCamera(-1, 1, 1, -1, 0, 1), []);
  const simMaterial = useMemo(() => makeSimMaterial(new THREE.Vector2(1 / SIM_SIZE, 1 / SIM_SIZE)), []);
  const simMesh = useMemo(() => {
    const mesh = new THREE.Mesh(new THREE.PlaneGeometry(2, 2), simMaterial);
    return mesh;
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [simMaterial]);

  useEffect(() => {
    simScene.add(simMesh);
    // Clear both targets to a dry, flat sheet before the first real frame.
    for (const target of targets) {
      gl.setRenderTarget(target);
      gl.clear();
    }
    gl.setRenderTarget(null);
    return () => {
      targets.forEach((t) => t.dispose());
      simMaterial.dispose();
      simMesh.geometry.dispose();
      geometry.dispose();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const displayUniforms = useMemo(
    () => ({
      uInkMap: { value: targets[0].texture },
      uPaperColor: { value: new THREE.Color('#f6f1e7') },
      uInkColor: { value: new THREE.Color('#2b2622') },
      uSigma: { value: 2.6 }, // --ink-sigma
    }),
    // eslint-disable-next-line react-hooks/exhaustive-deps
    [],
  );

  const stoppedAt = useRef<number | null>(null);
  const SETTLE_TAIL_SECONDS = 2.5; // keep decaying briefly after the mic stops, then go idle

  useFrame((state) => {
    const active = isMicActive();
    const now = state.clock.elapsedTime;
    if (active) stoppedAt.current = null;
    else if (stoppedAt.current === null) stoppedAt.current = now;

    const withinSettleTail = stoppedAt.current !== null && now - stoppedAt.current < SETTLE_TAIL_SECONDS;
    if (!active && !withinSettleTail) return; // fully idle: no sim step, no invalidate — frame loop sleeps

    const writeTarget = targets[1 - readIndex.current];
    const readTarget = targets[readIndex.current];
    simMaterial.uniforms.uPrev.value = readTarget.texture;
    // Scaled down from a raw RMS level: sustained loud speech should build a soft, gradient
    // bloom over real time, not saturate to solid ink within a handful of frames.
    simMaterial.uniforms.uSeedAmount.value = active ? Math.min(0.55, getMicLevel() * 0.6) : 0;

    gl.setRenderTarget(writeTarget);
    gl.render(simScene, simCamera);
    gl.setRenderTarget(null);

    readIndex.current = 1 - readIndex.current;
    displayUniforms.uInkMap.value = writeTarget.texture;

    state.invalidate(); // self-limiting: stops the instant this branch stops running
  });

  return (
    <mesh geometry={geometry} position={[0, 0, -0.3]}>
      <shaderMaterial
        vertexShader={DISPLAY_VERTEX_SHADER}
        fragmentShader={DISPLAY_FRAGMENT_SHADER}
        uniforms={displayUniforms}
      />
    </mesh>
  );
}
