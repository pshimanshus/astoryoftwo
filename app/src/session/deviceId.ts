export const MAX_CAROUSELS = 3;
const ID_KEY = 'astory.deviceId';
const COUNT_KEY = 'astory.carouselsCreated';

export function getDeviceId(): string {
  let id = localStorage.getItem(ID_KEY);
  if (!id) {
    id = `dev_${Math.random().toString(36).slice(2)}${Date.now().toString(36)}`;
    localStorage.setItem(ID_KEY, id);
  }
  return id;
}

export function getCarouselsCreated(): number {
  return Number(localStorage.getItem(COUNT_KEY) ?? '0');
}

export function getRemaining(): number {
  return Math.max(0, MAX_CAROUSELS - getCarouselsCreated());
}

export function recordCarouselCreated(): void {
  localStorage.setItem(COUNT_KEY, String(getCarouselsCreated() + 1));
}

export function hasReachedCap(): boolean {
  return getRemaining() === 0;
}
