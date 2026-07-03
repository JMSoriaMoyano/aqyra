import { defineConfig } from "vite";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  root: aqui,
  // las fixtures ancladas (federado.ifc + árbol BCF + índice) se sirven en /
  publicDir: resolve(aqui, "..", "fixtures"),
  resolve: {
    alias: { "@aqyra/visor": resolve(aqui, "..", "src", "index.ts") },
  },
  server: {
    fs: { allow: [resolve(aqui, "..", "..", "..")] },
  },
});
