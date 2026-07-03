import { defineConfig } from "vitest/config";
import { dirname, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));

export default defineConfig({
  resolve: {
    alias: { "@aqyra/visor": resolve(aqui, "src/index.ts") },
  },
  test: {
    environment: "jsdom",
    include: ["test/**/*.test.ts"],
  },
});
