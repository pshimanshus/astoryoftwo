import '@testing-library/jest-dom/vitest';

// Newer Node releases expose an experimental `localStorage` global that is
// undefined unless Node is started with --localstorage-file. Install a small,
// browser-compatible in-memory implementation so application tests do not
// depend on Node CLI flags or a machine-local storage file.
const values = new Map<string, string>();
const localStorageMock: Storage = {
  get length() {
    return values.size;
  },
  clear() {
    values.clear();
  },
  getItem(key) {
    return values.get(key) ?? null;
  },
  key(index) {
    return [...values.keys()][index] ?? null;
  },
  removeItem(key) {
    values.delete(key);
  },
  setItem(key, value) {
    values.set(key, String(value));
  },
};

Object.defineProperty(globalThis, 'localStorage', {
  configurable: true,
  value: localStorageMock,
});
