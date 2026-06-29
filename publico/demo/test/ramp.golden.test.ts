/**
 * Arnés golden — RAMPA DE ACCESO del parking (IfcRamp, losa inclinada localizada).
 *
 * Llave 1: prueba que la rampa de acceso (1) es un IfcRamp (ya NO un IfcSpace), (2) sube
 * una planta por salto (PB→P1…), (3) está LOCALIZADA pegada a la fachada pedida con
 * recorrido = desnivel/pendiente (NO una franja a fondo completo — el bug que reportó JM),
 * y (4) cruza a C1 por el primitivo `rampas` (inicio/fin con z) → FRONTERA-CERO. Re-firma
 * del parking con rampas porque la Rampa deja de ser IfcSpace. La IA prepara; firma JM.
 *
 *   ../node_modules/.bin/vitest run --root . test/ramp.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { buildModel, rampCount, openingCount, type BuildingInput } from "../src/model";
import { checkFixture, type CaseFixture } from "../src/fixture";
import { toAltoSpec } from "../src/c1-bridge";

import parking from "../fixtures/parking-120x24-2filas.json";
import parkingLinea from "../fixtures/parking-linea-60x12.json";

// Caso SABA (el de JM): parking 31×200, 2 plantas, rampa de acceso en la fachada NORTE.
const saba: BuildingInput = {
  project: "Parking SABA", building: "P",
  storeys: { count: 2, height: 2.5 },
  plan: { rooms: null, corridor: null, cores: [] },
  program: { generator: "parking-comb", params: { bays: 400, aisle: 6, ramps: ["N"] } },
};
const CTX = { W: 31, D: 200 };

describe("buildModel — rampa de acceso = IfcRamp localizada (no el espinazo)", () => {
  it("una rampa por salto de planta (2 plantas → 1), como elemento IfcRamp", () => {
    const m = buildModel(saba, CTX);
    expect(rampCount(m)).toBe(1);
    const r = m.storeys[0].elements.find((e) => e.ifcClass === "IfcRamp")!;
    expect(r.predefinedType).toBe("STRAIGHT");
    expect(r.placement.kind).toBe("line");
    expect(r.uriBsdd).toContain("/class/IfcRamp");
    expect(m.storeys[1].elements.some((e) => e.ifcClass === "IfcRamp")).toBe(false); // la última no sube
  });

  it("LOCALIZADA en la fachada norte (arranca en y=D y NO recorre los 200 m)", () => {
    const m = buildModel(saba, CTX);
    const r = m.storeys[0].elements.find((e) => e.ifcClass === "IfcRamp")!;
    if (r.placement.kind !== "line") throw new Error("línea");
    expect(r.placement.start[1]).toBe(200);                 // borde de la fachada (cota baja)
    const run = Math.abs(r.placement.start[1] - r.placement.end[1]);
    expect(run).toBeCloseTo(16.67, 1);                      // = altura/pendiente (2,50 / 0,15)
    expect(run).toBeLessThan(200);                          // NO es la franja a fondo completo
    expect(r.width).toBe(6);                                // ancho = vial
  });

  it("la Rampa ya NO es un IfcSpace", () => {
    const m = buildModel(saba, CTX);
    expect(m.storeys.flatMap((s) => s.spaces).some((s) => s.objectType === "Rampa")).toBe(false);
  });

  it("la rampa PERFORA el forjado al que sube (hueco en P01, no en la cubierta)", () => {
    const m = buildModel(saba, CTX);
    expect(openingCount(m)).toBe(1); // 2 plantas → 1 rampa → 1 hueco en el forjado de P1
    const hue = m.storeys.flatMap((s) => s.elements).find((e) => e.ifcClass === "IfcOpeningElement" && e.code.includes("RAM"))!;
    expect(hue.host).toBe("AQ-FOR-P01");      // vacía el forjado de la planta donde EMERGE
    expect(hue.placement.kind).toBe("polygon");
    expect(hue.storeyIndex).toBe(1);
    // la cubierta (último nivel) NO se perfora
    expect(m.storeys.flatMap((s) => s.elements).some((e) => e.ifcClass === "IfcOpeningElement" && e.host === "AQ-FOR-CUB")).toBe(false);
  });
});

describe("c1-bridge — la rampa cruza por `rampas` (inicio/fin 3D) · frontera-cero", () => {
  it("emite rampas[] con la cota baja en la fachada y la alta una planta arriba", () => {
    const spec = toAltoSpec(buildModel(saba, CTX), { ancho: 31, largo: 200, altura: 2.5 });
    expect(spec.rampas?.length).toBe(1);
    const r = spec.rampas![0];
    expect(r.inicio[2]).toBe(0);        // z baja = cota de PB
    expect(r.fin[2]).toBe(2.5);         // z alta = cota de P1
    expect(r.ancho).toBe(6);
    expect(r.peldaneada).toBe(false);   // rampa de vehículos = lisa
  });

  it("el hueco que abre la rampa cruza como losas[].huecos (frontera-cero)", () => {
    const spec = toAltoSpec(buildModel(saba, CTX), { ancho: 31, largo: 200, altura: 2.5 });
    const losaP1 = spec.losas?.find((l) => l.nombre === "AQ-FOR-P01");
    expect(losaP1?.huecos?.length).toBe(1);
    expect(losaP1?.huecos?.[0].contorno).toHaveLength(4); // el rectángulo de la rampa
  });
});

describe("fixtures golden de parking — re-firma y no-regresión", () => {
  it("parking 120×24 con rampas O/E (re-frozen: Rampa → IfcRamp) no regresiona", () => {
    const r = checkFixture(parking as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });

  it("parking en línea (SIN rampas) sigue idéntico — no le afecta el cambio", () => {
    const r = checkFixture(parkingLinea as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });
});
