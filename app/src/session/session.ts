export type Relationship = 'together' | 'sending';

export interface Slide {
  id: string;
  imageUrl: string;
  caption: string;
}

export interface SessionState {
  relationship: Relationship | null;
  creatorName: string;
  partnerName: string;
  photos: string[];
  recordingUrl: string | null;
  recordingDurationSec: number;
  storyBeats: string[];
  rating: number | null;
  slides: Slide[] | null;
}

export function createInitialSession(): SessionState {
  return {
    relationship: null,
    creatorName: '',
    partnerName: '',
    photos: [],
    recordingUrl: null,
    recordingDurationSec: 0,
    storyBeats: [],
    rating: null,
    slides: null,
  };
}

export const hasPhotos = (s: SessionState) => s.photos.length > 0;
export const hasRecording = (s: SessionState) => s.recordingUrl !== null;
export const displayPartnerName = (s: SessionState) =>
  s.partnerName.trim() ? s.partnerName.trim() : 'your person';
