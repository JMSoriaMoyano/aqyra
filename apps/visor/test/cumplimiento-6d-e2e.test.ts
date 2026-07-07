// @vitest-environment node
/** E2E headless del cumplimiento 6D: el visor abre el Maestro 6D (Pset_Aqyra_Cumplimiento escrito
 *  por engines/cumplimiento.escribir_cumplimiento sobre el derivado federado) y LEE el veredicto por
 *  elemento. Ancla lo ESTRUCTURAL: md5 LF del fixture (== el 6D determinista de GOL-CTE-6D-01,
 *  normalizado a LF por git) + el color por elemento (D-6D-4). Sin golden de píxeles. `federado.ifc`
 *  (dcb1e144) y su E2E NO se tocan; `federado_5d.ifc` (3e302e5f) tampoco. */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, colorPorResultado } from "@aqyra/visor";

const aqui = dirname(fileURLToPath(import.meta.url));
const FIX = join(aqui, "..", "fixtures");

// Identidad del 6D — md5 LF (git normaliza apps/visor/fixtures a LF; el raw determinista del golden
// es d9b68d46…, aquí anclamos el LF que ve el CI). Un fallo se investiga en el ENGINE (escritura.py).
const MD5_6D_LF = "fffeb26f7cbf2c34148a9d57b89d5e5c";
const N_ELEMENTOS = 13;

const md5 = (b: Buffer): string => createHash("md5").update(b).digest("hex");
const ROJO_NO_CUMPLE = { r: 0xd6 / 255, g: 0x45 / 255, b: 0x45 / 255 }; // #d64545 (D-6D-4)

describe("E2E · el visor pinta el cumplimiento (Maestro 6D)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: wasmDir, wasmAbsolute: true });
    await loader.init();
  });

  it("el fixture 6D ES el 6D (md5 LF, determinista == GOL-CTE-6D-01)", () => {
    expect(md5(readFileSync(join(FIX, "federado_6d.ifc")))).toBe(MD5_6D_LF);
  });

  it("lee el Pset por elemento y da el color por resultado (D-6D-4)", async () => {
    const data = readFileSync(join(FIX, "federado_6d.ifc"), "utf-8");
    const m = await loader.open({ name: "federado_6d", data });
    const cump = loader.readCompliance(m.modelID);
    expect(cump).not.toBeNull();
    const c = cump!;

    // el lector de DATOS ve los 13 IfcElement con Pset (incluidos ascensor y hueco), todos no-cumple
    // (E-SI-RF-DECL domina el peor caso, D-6D-2).
    expect(c.porElemento.size).toBe(N_ELEMENTOS);
    expect(c.resumen["no-cumple"]).toBe(N_ELEMENTOS);

    // color por elemento (lo que el viewer pinta): cada GlobalId enumerado → su color de resultado.
    // El loader enumera los elementos RENDERABLES (ELEMENT_TYPES): son 11 de los 13 (IfcTransportElement
    // y IfcOpeningElement no se enumeran); todos ellos ⊆ los 13 con veredicto → todos reciben color.
    const exprPorGuid = new Map(m.elements.map((e) => [e.globalId, e.expressId]));
    const colorPorExpress = new Map<number, { r: number; g: number; b: number }>();
    for (const [guid, ec] of c.porElemento) {
      const ex = exprPorGuid.get(guid);
      if (ex !== undefined) colorPorExpress.set(ex, colorPorResultado(ec.resultado));
    }
    expect(colorPorExpress.size).toBe(m.elements.length); // todos los renderables tienen resultado
    for (const col of colorPorExpress.values()) expect(col).toEqual(ROJO_NO_CUMPLE);

    // el muro M-Fachada (GUID estable, mismo del E2E 5D) → rojo no-cumple
    const exMuro = exprPorGuid.get("0EAm14JNX7Hu9QtYUgOaK4")!;
    expect(colorPorExpress.get(exMuro)).toEqual(ROJO_NO_CUMPLE);

    loader.close(m.modelID);
  });
});
