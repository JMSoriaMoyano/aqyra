/**
 * Arnés golden — capa de ELEMENTOS (Inc núcleo: IfcColumn + IfcSlab).
 *
 * Llave 1 (golden verde): este arnés prueba que `buildGrid`/`buildModel` son
 * DETERMINISTAS y que los fixtures congelados no regresionan. La IA lo prepara;
 * la firma (Llave 2) es de JM. Un fallo se arregla en el código, nunca aflojando
 * el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/columns.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import {
  resolveGrid, buildGrid, buildModel, columnCount, slabCount,
  type BuildingInput,
} from "../src/model";
import { checkFixture, type CaseFixture } from "../src/fixture";
import { toAltoSpec } from "../src/c1-bridge";

import reticula from "../fixtures/reticula-120x24-6x6.json";
import parking from "../fixtures/parking-120x24-2filas.json";

const CTX = { W: 120, D: 24 };

describe("buildGrid — determinismo y nudos", () => {
  it("misma entrada → misma malla (determinista)", () => {
    const g = resolveGrid({ sepX: 6, sepY: 6 }, CTX);
    expect(buildGrid(g)).toEqual(buildGrid(g));
  });

  it("cuenta los nudos que caben en la huella (autoridad del visor)", () => {
    const g = resolveGrid({ sepX: 6, sepY: 6 }, CTX);
    expect([g.nx, g.ny]).toEqual([21, 5]); // 0..120 paso 6 = 21; 0..24 paso 6 = 5
    const nodes = buildGrid(g);
    expect(nodes).toHaveLength(105);
    expect(nodes[0]).toMatchObject({ ix: 0, iy: 0, x: 0, y: 0, axis: "A1" });
    expect(nodes[1]).toMatchObject({ x: 6, y: 0, axis: "A2" });
    expect(nodes[21]).toMatchObject({ ix: 0, iy: 1, x: 0, y: 6, axis: "B1" });
  });

  it("defaults de sección/material = C1 (0,40 × 0,40 · HA-30)", () => {
    const g = resolveGrid({ sepX: 6, sepY: 6 }, CTX);
    expect(g.section).toEqual({ w: 0.4, d: 0.4 });
    expect(g.material).toBe("HA-30");
  });
});

describe("buildModel — el pilar se repite por planta estructural", () => {
  const input: BuildingInput = {
    project: "R", building: "B",
    storeys: { count: 3, height: 3 },
    plan: { rooms: null, corridor: null, cores: [] },
    grid: { sepX: 6, sepY: 6 },
  };

  it("columnas en plantas 0..n-2 (cubierta sin pilar), espejo del estr de C1", () => {
    const m = buildModel(input, CTX);
    expect(m.storeys.map((s) => s.elements.filter((e) => e.ifcClass === "IfcColumn").length)).toEqual([105, 105, 0]);
    expect(columnCount(m)).toBe(210);
  });

  it("nomenclatura AQ-PIL-Pnn-<eje> y identidad IfcColumn", () => {
    const m = buildModel(input, CTX);
    const c = m.storeys[0].elements[0];
    expect(c.code).toBe("AQ-PIL-P00-A1");
    expect(c.ifcClass).toBe("IfcColumn");
    expect(c.predefinedType).toBe("COLUMN");
    expect(c.uriBsdd).toContain("/class/IfcColumn");
  });

  it("una sola planta → la baja es estructural", () => {
    const m = buildModel({ ...input, storeys: { count: 1, height: 3 } }, CTX);
    expect(m.storeys[0].elements.length).toBe(105);
  });
});

describe("c1-bridge — emite reticulas_pilares (frontera menor, sin bump)", () => {
  const input: BuildingInput = {
    project: "R", building: "B",
    storeys: { count: 3, height: 3 },
    plan: { rooms: null, corridor: null, cores: [] },
    grid: { sepX: 6, sepY: 6 },
  };

  it("la retícula va compacta y el edificio cede los pilares", () => {
    const spec = toAltoSpec(buildModel(input, CTX), { ancho: 120, largo: 24, altura: 3 });
    expect(spec.reticulas_pilares).toHaveLength(1);
    expect(spec.reticulas_pilares![0]).toMatchObject({
      nx: 21, ny: 5, sep_x: 6, sep_y: 6, seccion: [0.4, 0.4], material: "HA-30", niveles: "todas",
    });
    expect(spec.edificios[0].pilares).toBe(false); // la retícula es la autoridad
  });

  it("sin retícula no emite reticulas_pilares y el edificio mantiene sus pilares", () => {
    const { grid, ...noGrid } = input;
    const spec = toAltoSpec(buildModel(noGrid, CTX), { ancho: 120, largo: 24, altura: 3 });
    expect(spec.reticulas_pilares).toBeUndefined();
    expect(spec.edificios[0].pilares).toBe(true);
  });
});

describe("fixtures golden — anti-regresión", () => {
  it("retícula 120×24 · 6×6 no regresiona", () => {
    const r = checkFixture(reticula as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });

  it("parking previo (sin columnas) sigue verde — compatibilidad", () => {
    const r = checkFixture(parking as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });
});

describe("buildModel — forjados automáticos (IfcSlab)", () => {
  const base: BuildingInput = {
    project: "R", building: "B",
    storeys: { count: 4, height: 3 },
    plan: { rooms: null, corridor: null, cores: [] },
  };

  it("losa por planta 1..n-1; la baja apoya en terreno (sin losa)", () => {
    const m = buildModel(base, CTX);
    expect(m.storeys.map((s) => s.elements.filter((e) => e.ifcClass === "IfcSlab").length)).toEqual([0, 1, 1, 1]);
    expect(slabCount(m)).toBe(3);
  });

  it("identidad IfcSlab: code AQ-FOR-Pnn, FLOOR, polígono, espesor 0,30", () => {
    const m = buildModel(base, CTX);
    const f = m.storeys[1].elements.find((e) => e.ifcClass === "IfcSlab")!;
    expect(f.code).toBe("AQ-FOR-P01");
    expect(f.predefinedType).toBe("FLOOR");
    expect(f.placement.kind).toBe("polygon");
    expect(f.thickness).toBe(0.3);
    expect(f.uriBsdd).toContain("/class/IfcSlab");
  });

  it("una sola planta → sin forjado", () => {
    const m = buildModel({ ...base, storeys: { count: 1, height: 3 } }, CTX);
    expect(slabCount(m)).toBe(0);
  });
});
