import { createRequire } from "node:module";
import { dirname } from "node:path";

// Directorio real del paquete web-ifc (donde viven los .wasm). web-ifc es
// dependencia de @aqyra/visor y NO se hoistea a `node_modules/` raíz con pnpm,
// así que `process.cwd()/node_modules/web-ifc` NO existe en una instalación
// pnpm. Lo resolvemos por el resolvedor de Node → independiente de la
// instalación (pnpm/npm), apuntando al directorio que contiene web-ifc-node.wasm.
const require = createRequire(import.meta.url);
export const wasmDir = dirname(require.resolve("web-ifc")) + "/";
