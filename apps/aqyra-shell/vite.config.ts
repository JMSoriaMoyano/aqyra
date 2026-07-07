import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";
import { createReadStream, existsSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

const aqui = dirname(fileURLToPath(import.meta.url));
const raiz = resolve(aqui, "..", ".."); // raíz del monorepo

// El .wasm de web-ifc se sirve desde el directorio REAL del paquete (mismo criterio
// que la demo del visor): la app pide wasmPath "/wasm-web-ifc/".
const require = createRequire(import.meta.url);
const wasmDir = dirname(require.resolve("web-ifc"));

const servirWasmWebIfc: Plugin = {
  name: "servir-wasm-web-ifc",
  configureServer(server) {
    server.middlewares.use("/wasm-web-ifc", (req, res, next) => {
      const nombre = (req.url ?? "").split("?")[0]!.replace(/^\//, "");
      const fichero = join(wasmDir, nombre);
      if (nombre && !nombre.includes("..") && existsSync(fichero)) {
        res.setHeader(
          "Content-Type",
          nombre.endsWith(".wasm") ? "application/wasm" : "application/octet-stream",
        );
        createReadStream(fichero).pipe(res);
        return;
      }
      next();
    });
  },
};

// Maestro federado de MUESTRA para arrancar en la vista de visor (como el mockup): sirve la
// fixture del visor en /federado.ifc. Solo dev; NO altera la zona anclada (solo lectura).
const fixtureVisor = resolve(aqui, "..", "visor", "fixtures", "federado.ifc");
const servirMuestra: Plugin = {
  name: "servir-muestra-ifc",
  configureServer(server) {
    server.middlewares.use("/federado.ifc", (_req, res, next) => {
      if (existsSync(fixtureVisor)) {
        res.setHeader("Content-Type", "application/octet-stream");
        createReadStream(fixtureVisor).pipe(res);
        return;
      }
      next();
    });
  },
};

export default defineConfig({
  root: aqui,
  plugins: [react(), servirWasmWebIfc, servirMuestra],
  resolve: {
    // el visor se consume desde su fuente (igual que su propia demo)
    alias: { "@aqyra/visor": resolve(aqui, "..", "visor", "src", "index.ts") },
  },
  server: {
    fs: { allow: [raiz] },
  },
});
