// @vitest-environment node
/** compliance — lectura del cumplimiento 6D (Pset_Aqyra_Cumplimiento) + helpers de color/leyenda.
 *  `leerCumplimiento` sobre el fixture 6D (escrito por engines/cumplimiento.escribir_cumplimiento
 *  sobre el derivado federado, veredicto de GOL-CTE-01) devuelve el mapa por elemento y el resumen.
 *  Colores por resultado = D-6D-4. El fixture es el 6D determinista del golden GOL-CTE-6D-01. */
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import {
  IfcLoader, colorPorResultado, leyendaCumplimiento, HEX_CUMPLIMIENTO,
  RESULTADOS_CUMPLIMIENTO, GRIS_SIN_DATO,
} from "@aqyra/visor";

const aqui = dirname(fileURLToPath(import.meta.url));
const FIX = join(aqui, "..", "fixtures");

describe("colorPorResultado · D-6D-4 (puro)", () => {
  it("las 4 claves de la taxonomía dan su color de marca", () => {
    expect(colorPorResultado("cumple")).toEqual({ r: 0x2e / 255, g: 0x9e / 255, b: 0x5b / 255 });
    expect(colorPorResultado("no-cumple")).toEqual({ r: 0xd6 / 255, g: 0x45 / 255, b: 0x45 / 255 });
    expect(colorPorResultado("no-aplica")).toEqual({ r: 0x8a / 255, g: 0x8f / 255, b: 0x98 / 255 });
    expect(colorPorResultado("no-verificable")).toEqual({ r: 0xe0 / 255, g: 0xa4 / 255, b: 0x3a / 255 });
  });
  it("no-cumple es rojizo (r domina) y cumple verdoso (g domina)", () => {
    const nc = colorPorResultado("no-cumple");
    expect(nc.r).toBeGreaterThan(nc.g);
    const c = colorPorResultado("cumple");
    expect(c.g).toBeGreaterThan(c.r);
  });
  it("un resultado fuera de taxonomía cae a gris neutro", () => {
    expect(colorPorResultado("desconocido")).toEqual(GRIS_SIN_DATO);
  });
  it("HEX_CUMPLIMIENTO cubre las 4 claves de la taxonomía", () => {
    expect(Object.keys(HEX_CUMPLIMIENTO).sort()).toEqual([...RESULTADOS_CUMPLIMIENTO].sort());
  });
});

describe("leerCumplimiento · el visor lee el veredicto 6D del Maestro", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: wasmDir, wasmAbsolute: true });
    await loader.init();
  });

  it("porElemento (13) + resumen: todos no-cumple (E-SI-RF-DECL domina el peor caso)", async () => {
    const data = readFileSync(join(FIX, "federado_6d.ifc"), "utf-8");
    const m = await loader.open({ name: "federado_6d", data });
    const cump = loader.readCompliance(m.modelID);
    expect(cump).not.toBeNull();
    const c = cump!;

    expect(c.porElemento.size).toBe(13);
    expect(c.resumen).toEqual({ "cumple": 0, "no-cumple": 13, "no-aplica": 0, "no-verificable": 0 });

    // el muro M-Fachada (mismo GUID que el E2E 5D) lleva el peor caso + su exigencia dominante
    const muro = c.porElemento.get("0EAm14JNX7Hu9QtYUgOaK4");
    expect(muro).toBeDefined();
    expect(muro!.resultado).toBe("no-cumple");
    expect(muro!.exigencia).toBe("E-SI-RF-DECL");
    expect(muro!.documentoBasico).toBe("DB-SI");
    expect(muro!.pack).toBe("CTE/2019");

    // todos los elementos con Pset están en la taxonomía cerrada
    for (const e of c.porElemento.values()) {
      expect(RESULTADOS_CUMPLIMIENTO).toContain(e.resultado);
    }

    // leyenda de 4 con el conteo del resumen
    const leg = leyendaCumplimiento(c);
    expect(leg.map((x) => x.resultado)).toEqual([...RESULTADOS_CUMPLIMIENTO]);
    expect(leg.find((x) => x.resultado === "no-cumple")!.count).toBe(13);

    loader.close(m.modelID);
  });

  it("un modelo SIN Pset de cumplimiento (el derivado base) da null (no es 6D)", async () => {
    const data = readFileSync(join(FIX, "federado.ifc"), "utf-8");
    const m = await loader.open({ name: "federado", data });
    expect(loader.readCompliance(m.modelID)).toBeNull();
    loader.close(m.modelID);
  });
});
