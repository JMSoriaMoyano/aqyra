/**
 * Arnés golden — AUDITORÍA BÁSICA (P1·C, hito 4).
 *
 * Llave 1 (golden verde): prueba que (a) el MODELO del cebo, tal como lo emite
 * `buildModel`, es 100 % CONFORME a la regla básica (nomenclatura AQ-* + doble
 * clasificación bsDD + Uniclass) → la auditoría no encuentra nada; y (b) que el motor
 * NO es vacío: ante un modelo manipulado, reporta EXACTAMENTE las no-conformidades.
 * La coherencia bsDD/Uniclass es POR CONSTRUCCIÓN (el modelo emite y la auditoría
 * espera desde la misma fuente) y aquí se comprueba explícitamente. La IA lo prepara;
 * la firma (Llave 2) es de JM. Un fallo se arregla en el código, nunca aflojando el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/audit.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { buildModel, type BuildingInput, type PlanContext } from "../src/model";
import { auditModel, RULES } from "../src/audit";
import { classUri } from "../src/bsdd";
import { uniclassFor } from "../src/uniclass";

import reticula from "../fixtures/reticula-120x24-6x6.json";
import parking from "../fixtures/parking-120x24-2filas.json";
import resid from "../fixtures/residencia-4plantas-2nucleos.json";

type Frozen = { input: BuildingInput; ctx: PlanContext };
const CASES: Array<{ name: string; fx: Frozen }> = [
  { name: "retícula 120×24 · 6×6 (pilares + forjados)", fx: reticula as unknown as Frozen },
  { name: "parking en peine (plazas + viales + rampas)", fx: parking as unknown as Frozen },
  { name: "residencia 4 plantas · 2 núcleos (muros + huecos + escaleras)", fx: resid as unknown as Frozen },
];

describe("auditoría básica — el modelo del cebo es conforme (anti-regresión)", () => {
  for (const c of CASES) {
    it(`${c.name} → sin no-conformidades`, () => {
      const m = buildModel(c.fx.input, c.fx.ctx);
      const r = auditModel(m);
      expect(r.nonConformances).toEqual([]); // si falla, imprime QUÉ incumple
      expect(r.ok).toBe(true);
      expect(r.conformant).toBe(r.audited);
      // todas las reglas presentes y a cero
      for (const rule of RULES) expect(r.byRule[rule.id]).toBe(0);
    });
  }

  it("determinismo — mismo modelo → mismo informe", () => {
    const m = buildModel(resid.input as unknown as BuildingInput, resid.ctx as unknown as PlanContext);
    expect(auditModel(m)).toEqual(auditModel(m));
  });
});

describe("doble clasificación — coherencia POR CONSTRUCCIÓN en cada elemento", () => {
  it("uriBsdd == classUri(clase) y uniclass == uniclassFor(clase, predefinedType)", () => {
    const m = buildModel(resid.input as unknown as BuildingInput, resid.ctx as unknown as PlanContext);
    let checked = 0;
    for (const s of m.storeys) for (const e of s.elements) {
      expect(e.uriBsdd).toBe(classUri(e.ifcClass));
      const want = uniclassFor(e.ifcClass, e.predefinedType);
      if (want) expect(e.uniclass).toEqual(want);          // clase clasificable → presente y coherente
      else expect(e.uniclass).toBeUndefined();             // hueco (IfcOpeningElement) → sin Uniclass
      checked++;
    }
    expect(checked).toBeGreaterThan(0);
  });
});

describe("el motor NO es vacío — detecta lo que se rompe", () => {
  // Modelo pequeño y determinista (1 planta, retícula gruesa → pocos pilares).
  const base: BuildingInput = {
    project: "T", building: "B",
    storeys: { count: 1, height: 3 },
    plan: { rooms: null, corridor: null, cores: [] },
    grid: { sepX: 60, sepY: 24 },
  };
  const CTX: PlanContext = { W: 120, D: 24 };

  it("modelo manipulado → una no-conformidad por cada cara rota", () => {
    const m = buildModel(base, CTX);
    const els = m.storeys[0].elements;
    expect(els.length).toBeGreaterThanOrEqual(5);
    // 1) formato AQ-* roto
    els[0].code = "PILAR_MAL";
    // 2) duplicado (dos elementos con el mismo código)
    els[1].code = els[2].code;
    // 3) bsDD incoherente
    els[3].uriBsdd = "http://incoherente";
    // 4) Uniclass ausente (los pilares la requieren)
    delete els[4]?.uniclass;

    const r = auditModel(m);
    expect(r.byRule["AQ-NMB-01"]).toBe(1);
    expect(r.byRule["AQ-NMB-02"]).toBe(1);
    expect(r.byRule["AQ-CLS-01"]).toBe(1);
    expect(r.byRule["AQ-CLS-02"]).toBe(1);
    expect(r.ok).toBe(false);
    expect(r.nonConformances).toHaveLength(4);
  });
});
