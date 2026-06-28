import { defineConfig } from "vitest/config";
import { resolve } from "node:path";

export default defineConfig({
  resolve: {
    alias: {
      "@aqyra/visor": resolve(__dirname, "visor/src/index.ts"),
      "@aqyra/openbim": resolve(__dirname, "openbim/src/index.ts"),
      "@aqyra/embed": resolve(__dirname, "embed/src/index.ts"),
    },
  },
  test: {
    environment: "jsdom",
    include: ["**/test/**/*.test.ts"],
  },
});
