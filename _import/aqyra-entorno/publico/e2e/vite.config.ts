import { defineConfig } from "vite";
import { resolve } from "node:path";

export default defineConfig({
  root: __dirname,
  resolve: {
    alias: {
      "@aqyra/embed": resolve(__dirname, "../embed/src/index.ts"),
      "@aqyra/visor": resolve(__dirname, "../visor/src/index.ts"),
      "@aqyra/openbim": resolve(__dirname, "../openbim/src/index.ts"),
    },
  },
  build: { outDir: "dist", emptyOutDir: true },
});
