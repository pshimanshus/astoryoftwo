import type { CSSProperties } from 'react';

// A photo torn from a sheet, not a rounded rectangle in a box. Every place a photo appears in
// this app — the picker grid, the review strip, the printing feed, the reveal carousel — should
// read as paper, not as generic card UI. The tear and the tilt are both deterministic per `seed`
// (typically the photo's own id), so the same photo always tears the same way across re-renders
// and screens, rather than jittering on every render.

function seededRandom(seed: string) {
  let h = 0;
  for (let i = 0; i < seed.length; i++) h = (Math.imul(31, h) + seed.charCodeAt(i)) | 0;
  return (salt: number) => {
    const x = Math.sin(h + salt * 999.7) * 43758.5453;
    return x - Math.floor(x);
  };
}

/** A jagged clip-path polygon approximating a torn paper edge — small inward jitter on each of
 * the four sides, more points than a plain rectangle so the tear reads as irregular, not faceted. */
function tornClipPath(seed: string): string {
  const rand = seededRandom(seed);
  const points: string[] = [];
  const perSide = 5;
  const jitter = 2.6; // percent

  const edge = (from: [number, number], to: [number, number], saltBase: number) => {
    for (let i = 0; i <= perSide; i++) {
      const t = i / perSide;
      const x = from[0] + (to[0] - from[0]) * t;
      const y = from[1] + (to[1] - from[1]) * t;
      const j = i === 0 || i === perSide ? 0 : (rand(saltBase + i) - 0.5) * 2 * jitter;
      // Jitter perpendicular to the edge direction.
      const dx = to[0] - from[0];
      const dy = to[1] - from[1];
      const len = Math.hypot(dx, dy) || 1;
      const nx = -dy / len;
      const ny = dx / len;
      points.push(`${(x + nx * j).toFixed(2)}% ${(y + ny * j).toFixed(2)}%`);
    }
  };

  edge([0, 0], [100, 0], 1);
  edge([100, 0], [100, 100], 2);
  edge([100, 100], [0, 100], 3);
  edge([0, 100], [0, 0], 4);

  return `polygon(${points.join(', ')})`;
}

export interface TornPhotoProps {
  src: string;
  alt: string;
  seed: string;
  width?: number | string;
  height?: number | string;
  /** Small deterministic tilt, like a photo dropped on a desk. 0 disables it (e.g. inside a
   * carousel, where tilt would fight the drag gesture). */
  tilt?: boolean;
  style?: CSSProperties;
}

export function TornPhoto({ src, alt, seed, width, height, tilt = true, style }: TornPhotoProps) {
  const rand = seededRandom(seed);
  const rotation = tilt ? (rand(9) - 0.5) * 7 : 0; // +/- 3.5deg
  return (
    <div
      style={{
        width,
        height,
        transform: `rotate(${rotation.toFixed(2)}deg)`,
        filter: 'drop-shadow(0 6px 10px rgba(0,0,0,0.16))',
        ...style,
      }}
    >
      <img
        src={src}
        alt={alt}
        style={{
          width: '100%',
          height: '100%',
          objectFit: 'cover',
          display: 'block',
          clipPath: tornClipPath(seed),
        }}
      />
    </div>
  );
}
