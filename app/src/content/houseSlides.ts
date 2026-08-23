// House-style illustration frames for the faked reveal. Replace urls with real
// A Story of Two assets dropped into app/src/assets/ when available.
export interface HouseTemplate { id: string; imageUrl: string; captionTemplate: string; }
export const houseSlides: HouseTemplate[] = [
  { id: 's1', imageUrl: 'https://picsum.photos/seed/astory-draw1/900/1100', captionTemplate: 'the day {creator} first really saw {partner}.' },
  { id: 's2', imageUrl: 'https://picsum.photos/seed/astory-draw2/900/1100', captionTemplate: '{beat}' },
  { id: 's3', imageUrl: 'https://picsum.photos/seed/astory-draw3/900/1100', captionTemplate: '{beat}' },
  { id: 's4', imageUrl: 'https://picsum.photos/seed/astory-draw4/900/1100', captionTemplate: 'and still, {creator} & {partner}.' },
];
