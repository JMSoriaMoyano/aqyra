import { defineConfig, type Plugin } from "vite";
import { createReadStream, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));

// El .wasm de web-ifc NO es servible como /node_modules/* con root=demo (y con pnpm
// ni siquiera está hoisted): se sirve desde el directorio REAL del paquete, resuelto
// por Node (mismo criterio que test/_wasm.ts). La demo usa wasmPath "/wasm-web-ifc/".
const require = createRequire(import.meta.url);
const wasmDir = dirname(require.resolve("web-ifc"));

const servirWasmWebIfc: Plugin = {
  name: "servir-wasm-web-ifc",
  configureServer(server) {
    server.middlewares.use("/wasm-web-ifc", (req, res, next) => {
      const nombre = (req.url ?? "").split("?")[0]!.replace(/^\//, "");
      const fichero = join(wasmDir, nombre);
      if (nombre && !nombre.includes("..") && existsSync(fichero)) {
        res.setHeader("Content-Type", nombre.endsWith(".wasm")
          ? "application/wasm" : "application/octet-stream");
        createReadStream(fichero).pipe(res);
        return;
      }
      next();
    });
  },
};

export default defineConfig({
  root: aqui,
  // las fixtures ancladas (federado.ifc + árbol BCF + índice) se sirven en /
  publicDir: resolve(aqui, "..", "fixtures"),
  plugins: [servirWasmWebIfc],
  resolve: {
    alias: { "@aqyra/visor": resolve(aqui, "..", "src", "index.ts") },
  },
  server: {
    fs: { allow: [resolve(aqui, "..", "..", "..")] },
  },
});
