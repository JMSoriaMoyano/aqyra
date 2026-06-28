import { defineConfig } from "vitest/config";

/**
 * Config del arnés golden (Llave 1). Aislada del `vite.config.ts` del servidor de
 * desarrollo: los tests del núcleo (model/fixture/c1-bridge) son lógica pura sin
 * DOM ni red, así que corren en entorno `node`. Vitest prefiere este fichero sobre
 * `vite.config.ts`, evitando arrancar el plugin del servidor en los tests.
 *
 *   pnpm --filter @aqyra/demo test      # una pasada (CI / firma)
 *   pnpm --filter @aqyra/demo test:watch
 */
export default defineConfig({
  test: {
    environment: "node",
    include: ["test/**/*.test.ts"],
  },
});
