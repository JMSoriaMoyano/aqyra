import { copyFileSync, mkdirSync } from "node:fs";
import { createRequire } from "node:module";
import { dirname, join, resolve } from "node:path";
import { fileURLToPath } from "node:url";

// Resuelve web-ifc desde el paquete @aqyra/visor (su dependencia real),
// no desde demo/ — así funciona con el aislamiento estricto de pnpm.
const here = dirname(fileURLToPath(import.meta.url)); // .../demo/scripts
const require = createRequire(resolve(here, "..", "..", "visor", "package.json"));
const wifc = dirname(require.resolve("web-ifc"));
const pub = resolve(here, "..", "public");
mkdirSync(pub, { recursive: true });
for (const f of ["web-ifc.wasm", "web-ifc-mt.wasm"]) {
  try {
    copyFileSync(join(wifc, f), join(pub, f));
  } catch {
    /* web-ifc-mt.wasm es opcional */
  }
}
console.log("web-ifc wasm -> demo/public/");
