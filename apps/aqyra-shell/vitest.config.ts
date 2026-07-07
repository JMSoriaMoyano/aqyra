import { defineConfig } from "vitest/config";

// Tests del shell. El núcleo puro (tema, helpers) corre headless en Node — sin WASM ni DOM.
// Los slices que necesiten DOM (panel flotante, dock) añadirán `environment: "jsdom"` cuando
// aparezcan (patrón del vitest del visor).
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts", "test/**/*.test.tsx"],
  },
});
