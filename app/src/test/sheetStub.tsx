// jsdom has no WebGL context; @react-three/fiber's <Canvas> throws on mount under vitest.
// None of the 6 kept test files render a component (they're pure-logic/localStorage tests), so
// this alias is preemptive insurance — App.tsx now imports the real SheetCanvas at runtime, and
// this keeps a future render-test from failing obscurely on a WebGL context it can't create.
export default function SheetCanvasStub() {
  return null;
}
