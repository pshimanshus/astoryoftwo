import React from 'react';
import {
  AbsoluteFill,
  Img,
  staticFile,
  useCurrentFrame,
  useVideoConfig,
} from 'remotion';

type PetalSpec = {
  x: number;
  y: number;
  width: number;
  height: number;
  baseRotation: number;
  driftX: number;
  driftY: number;
  rotationSwing: number;
  phase: number;
  opacity: number;
  scalePulse?: number;
  blur?: number;
  tint?: 'peach' | 'rose' | 'pale';
};

const petals: PetalSpec[] = [
  {
    x: 185,
    y: 255,
    width: 56,
    height: 34,
    baseRotation: -25,
    driftX: 14,
    driftY: 9,
    rotationSwing: 8,
    phase: 0.04,
    opacity: 0.58,
    scalePulse: 0.025,
  },
  {
    x: 116,
    y: 535,
    width: 72,
    height: 40,
    baseRotation: 31,
    driftX: 18,
    driftY: 11,
    rotationSwing: 10,
    phase: 0.34,
    opacity: 0.52,
    scalePulse: 0.018,
    tint: 'rose',
  },
  {
    x: 864,
    y: 696,
    width: 62,
    height: 38,
    baseRotation: -38,
    driftX: 12,
    driftY: 13,
    rotationSwing: 9,
    phase: 0.56,
    opacity: 0.55,
  },
  {
    x: 877,
    y: 1392,
    width: 69,
    height: 40,
    baseRotation: 18,
    driftX: 15,
    driftY: 10,
    rotationSwing: 7,
    phase: 0.79,
    opacity: 0.5,
    tint: 'rose',
  },
  {
    x: 720,
    y: 505,
    width: 34,
    height: 21,
    baseRotation: -12,
    driftX: 22,
    driftY: 14,
    rotationSwing: 14,
    phase: 0.18,
    opacity: 0.22,
    blur: 0.25,
    tint: 'pale',
  },
  {
    x: 445,
    y: 905,
    width: 28,
    height: 18,
    baseRotation: 42,
    driftX: 17,
    driftY: 12,
    rotationSwing: 12,
    phase: 0.68,
    opacity: 0.18,
    blur: 0.35,
    tint: 'pale',
  },
  {
    x: 56,
    y: 1045,
    width: 31,
    height: 19,
    baseRotation: -44,
    driftX: 11,
    driftY: 10,
    rotationSwing: 11,
    phase: 0.91,
    opacity: 0.2,
    blur: 0.35,
  },
];

const watercolorColors = {
  peach: {
    fill: 'rgba(220, 117, 77, 0.42)',
    edge: 'rgba(142, 78, 49, 0.34)',
    vein: 'rgba(160, 84, 52, 0.28)',
    wash: 'rgba(255, 198, 161, 0.26)',
  },
  rose: {
    fill: 'rgba(218, 102, 83, 0.38)',
    edge: 'rgba(144, 70, 52, 0.32)',
    vein: 'rgba(158, 76, 55, 0.24)',
    wash: 'rgba(255, 190, 172, 0.24)',
  },
  pale: {
    fill: 'rgba(223, 149, 111, 0.26)',
    edge: 'rgba(150, 92, 62, 0.18)',
    vein: 'rgba(165, 92, 62, 0.16)',
    wash: 'rgba(255, 218, 190, 0.18)',
  },
};

const TWO_PI = Math.PI * 2;

const Petal = ({spec, index}: {spec: PetalSpec; index: number}) => {
  const frame = useCurrentFrame();
  const {durationInFrames} = useVideoConfig();
  const loop = (frame / durationInFrames + spec.phase) % 1;
  const wave = loop * TWO_PI;
  const bob = Math.sin(wave);
  const sway = Math.sin(wave + index * 0.73);
  const secondSway = Math.sin(wave * 2 + index);
  const breathe = 1 + (spec.scalePulse ?? 0.015) * Math.sin(wave + 1.2);
  const x = spec.x + spec.driftX * sway + spec.driftX * 0.35 * secondSway;
  const y = spec.y + spec.driftY * bob;
  const rotation =
    spec.baseRotation + spec.rotationSwing * Math.sin(wave + index * 1.35);
  const colors = watercolorColors[spec.tint ?? 'peach'];

  return (
    <svg
      viewBox="0 0 72 42"
      style={{
        position: 'absolute',
        left: x,
        top: y,
        width: spec.width,
        height: spec.height,
        opacity: spec.opacity,
        overflow: 'visible',
        transform: `translate(-50%, -50%) rotate(${rotation}deg) scale(${breathe})`,
        transformOrigin: '50% 50%',
        filter: `drop-shadow(0 2px 2px rgba(116, 75, 43, 0.08)) blur(${spec.blur ?? 0}px)`,
        mixBlendMode: 'multiply',
      }}
    >
      <path
        d="M4 22C17 2 48 2 68 18C55 36 21 41 4 22Z"
        fill={colors.fill}
        stroke={colors.edge}
        strokeWidth="1.4"
        strokeLinecap="round"
      />
      <path
        d="M10 22C24 18 43 16 63 18"
        fill="none"
        stroke={colors.vein}
        strokeWidth="1"
        strokeLinecap="round"
      />
      <path
        d="M20 10C28 7 43 9 55 17C42 20 30 21 17 24C16 19 17 14 20 10Z"
        fill={colors.wash}
      />
      <path
        d="M31 17C28 22 24 27 19 31"
        fill="none"
        stroke={colors.vein}
        strokeWidth="0.8"
        strokeLinecap="round"
      />
    </svg>
  );
};

export const AnimatedPetals = () => {
  return (
    <AbsoluteFill style={{backgroundColor: '#f8edda'}}>
      <Img
        src={staticFile('frame-03.png')}
        style={{
          position: 'absolute',
          inset: 0,
          width: '100%',
          height: '100%',
          objectFit: 'cover',
        }}
      />
      <AbsoluteFill style={{pointerEvents: 'none'}}>
        {petals.map((spec, index) => (
          <Petal key={`${spec.x}-${spec.y}`} spec={spec} index={index} />
        ))}
      </AbsoluteFill>
    </AbsoluteFill>
  );
};
