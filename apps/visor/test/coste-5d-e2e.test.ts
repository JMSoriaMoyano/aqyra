// @vitest-environment node
/** E2E headless del coste 5D (V10, hilo IV·h4): el visor abre el Maestro 5D (IfcCostSchedule
 *  escrito por engines/presupuesto.escribir_coste sobre el derivado federado) y LEE el modelo
 *  de coste. Ancla lo ESTRUCTURAL: md5 del fixture (== el 5D determinista de GOL-PRE-02) +
 *  el mapa de coste (importe por partida, costeAsignado por elemento, Σ = PEM medible). Sin
 *  golden de píxeles. `federado.ifc` (dcb1e144) y su E2E NO se tocan (V7/U4). */
import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader } from "@aqyra/visor";

const aqui = dirname(fileURLToPath(import.meta.url));
const FIX = join(aqui, "..", "fixtures");

// Identidad del 5D — determinista (== el 5D de GOL-PRE-02, V7).
const MD5_5D = "60c906932ebb9c102a07962449bae903";
const PEM_MEDIBLE = 6884.83; // Σ importes de partidas con geometría (SYS010 sin asignar)
const PEM = 7022.53;
const PEC = 10111.74;

const md5 = (b: Buffer): string => createHash("md5").update(b).digest("hex");

describe("E2E · el visor pinta el coste (Maestro 5D)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: wasmDir, wasmAbsolute: true });
    await loader.init();
  });

  it("el fixture 5D ES el 5D (md5 == GOL-PRE-02, determinista)", () => {
    expect(md5(readFileSync(join(FIX, "federado_5d.ifc")))).toBe(MD5_5D);
  });

  it("lee el cost schedule: partidas, asignaciones por GUID y totales", async () => {
    const data = readFileSync(join(FIX, "federado_5d.ifc"), "utf-8");
    const m = await loader.open({ name: "federado_5d", data });
    const coste = loader.readCost(m.modelID);
    expect(coste).not.toBeNull();
    const c = coste!;

    expect(c.moneda).toBe("EUR");

    // FAB010: 1065.14 sobre los 2 muros
    const fab = c.partidas.find((p) => p.codigo === "FAB010");
    expect(fab).toBeDefined();
    expect(fab!.importe).toBeCloseTo(1065.14, 2);
    expect(fab!.guids.sort()).toEqual(["0EAm14JNX7Hu9QtYUgOaK4", "2VyfKvXd12bOJLg7j2fUpO"].sort());

    // 7 partidas con asignación (SYS010 sin geometría → sin asignar)
    const conAsignacion = c.partidas.filter((p) => p.guids.length > 0);
    expect(conAsignacion.length).toBe(7);

    // el muro M-Fachada (0EAm…) recibe fábrica+enfoscado+pintura → su cuota
    const muro = c.porElemento.get("0EAm14JNX7Hu9QtYUgOaK4");
    expect(muro).toBeDefined();
    expect(muro!.partidas.sort()).toEqual(["FAB010", "PIN010", "REV010"]);
    expect(muro!.costeAsignado).toBeCloseTo((1065.14 + 859.03 + 454.26) / 2, 2);

    // invariante: Σ costeAsignado = PEM medible
    const suma = [...c.porElemento.values()].reduce((s, e) => s + e.costeAsignado, 0);
    expect(suma).toBeCloseTo(PEM_MEDIBLE, 2);

    // totales del IfcCostItem RESUMEN
    expect(c.totales.PEM).toBeCloseTo(PEM, 2);
    expect(c.totales.PEC).toBeCloseTo(PEC, 2);

    // 6 capítulos; C02 (Estructura) = EHS + EHL
    expect(c.capitulos.length).toBe(6);
    const c02 = c.capitulos.find((x) => x.codigo === "C02");
    expect(c02!.importe).toBeCloseTo(4298.19, 2);

    loader.close(m.modelID);
  });
});
