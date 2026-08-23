// Bundled sample photos for the simulated gallery. Uses picsum seeds so no binary assets are needed.
export interface GalleryPhoto { id: string; url: string; }
export const sampleGallery: GalleryPhoto[] = Array.from({ length: 9 }, (_, i) => ({
  id: `photo-${i + 1}`,
  url: `https://picsum.photos/seed/astory${i + 1}/400/400`,
}));
