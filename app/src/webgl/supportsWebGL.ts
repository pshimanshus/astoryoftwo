// One-time capability probe, cached. If this returns false, PaperBackground never imports the
// canvas chunk at all — a Tier-1 user's bundle cost is identical to the pre-3D prototype.
let cached: boolean | null = null;

export function supportsWebGL(): boolean {
  if (cached !== null) return cached;
  try {
    const canvas = document.createElement('canvas');
    cached = !!(canvas.getContext('webgl2') || canvas.getContext('webgl'));
  } catch {
    cached = false;
  }
  return cached;
}
