import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    globals: true,
    environment: 'jsdom',
    setupFiles: ['./src/test/setup.ts'],
    // jsdom has no WebGL context; alias the real R3F canvas to a no-op stub so a future
    // component-render test doesn't fail obscurely trying to construct one. See sheetStub.tsx.
    alias: {
      './webgl/SheetCanvas': new URL('./src/test/sheetStub.tsx', import.meta.url).pathname,
    },
  },
});
