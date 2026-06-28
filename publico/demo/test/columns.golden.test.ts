/**
 * Arnés golden — capa de ELEMENTOS (IfcColumn + IfcSlab + IfcOpeningElement + IfcWall).
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
  resolveGrid, buildGrid, buildModel, columnCount, slabCount, openingCount, wallCount,
  type BuildingInput,
} from "../src/model";
import { checkFixture, type CaseFixture } from "../src/fixture";
import { toAltoSpec } from "../src/c1-bridge";

import reticula from "../fixtures/reticula-120x24-6x6.json";
import parking from "../fixtures/parking-120x24-2filas.json";
import resid from "../fixtures/residencia-4plantas-2nucleos.json";

const CTX = { W: 120, D: 24 };

describe("buildGrid — determinismo y nudos", () => {
  it("misma entrada → misma malla (determinista)", () => {
    const g = resolveGrid({ sepX: 6, sepY: 6 }, CTX);
    expect(buildGrid(g)).toEqual(buildGrid(g));
  });

  it("cuenta los nudos que caben en la huella (autoridad del visor)", () => {
    const g = resolveGrid({ sepX: 6, sepY: 6 }, CTX);
    expect([g.axesX.length, g.axesY.length]).toEqual([21, 5]); // ejes 0..120 paso 6 = 21; 0..24 paso 6 = 5
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

  it("columnas en TODAS las plantas (cada una sostiene la losa de arriba)", () => {
    const m = buildModel(input, CTX);
    expect(m.storeys.map((s) => s.elements.filter((e) => e.ifcClass === "IfcColumn").length)).toEqual([105, 105, 105]);
    expect(columnCount(m)).toBe(315);
  });

  it("nomenclatura AQ-PIL-Pnn-<eje> y identidad IfcColumn", () => {
    const m = buildModel(input, CTX);
    const c = m.storeys[0].elements[0];
    expect(c.code).toBe("AQ-PIL-P00-A1");
    expect(c.ifcClass).toBe("IfcColumn");
    expect(c.predefinedType).toBe("COLUMN");
    expect(c.uriBsdd).toContain("/class/IfcColumn");
  });

  it("una sola planta → tiene pilares (y su cubierta)", () => {
    const m = buildModel({ ...input, storeys: { count: 1, height: 3 } }, CTX);
    expect(m.storeys[0].elements.filter((e) => e.ifcClass === "IfcColumn").length).toBe(105);
  });
});

describe("c1-bridge — emite pilares[] explícitos (frontera-cero)", () => {
  const input: BuildingInput = {
    project: "R", building: "B",
    storeys: { count: 3, height: 3 },
    plan: { rooms: null, corridor: null, cores: [] },
    grid: { sepX: 6, sepY: 6 },
  };

  it("un pilar por columna; el edificio cede los suyos", () => {
    const spec = toAltoSpec(buildModel(input, CTX), { ancho: 120, largo: 24, altura: 3 });
    expect(spec.pilares?.length).toBe(315);
    expect(spec.pilares?.[0]).toMatchObject({
      nombre: "AQ-PIL-P00-A1", nivel: "Planta Baja", pos: [0, 0], seccion: [0.4, 0.4], altura: 3, material: "HA-30",
    });
    expect(spec.edificios[0].pilares).toBe(false); // los pilares los da el cebo
  });

  it("sin retícula no emite pilares y el edificio mantiene los suyos", () => {
    const { grid, ...noGrid } = input;
    const spec = toAltoSpec(buildModel(noGrid, CTX), { ancho: 120, largo: 24, altura: 3 });
    expect(spec.pilares).toBeUndefined();
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

  it("suelo por planta 1..n-1 + cubierta sobre la última; la baja apoya en terreno", () => {
    const m = buildModel(base, CTX);
    expect(m.storeys.map((s) => s.elements.filter((e) => e.ifcClass === "IfcSlab").length)).toEqual([0, 1, 1, 2]); // P3: su suelo + la cubierta
    expect(slabCount(m)).toBe(4); // 3 suelos + cubierta
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

  it("una sola planta → solo la cubierta (sin forjado de suelo)", () => {
    const m = buildModel({ ...base, storeys: { count: 1, height: 3 } }, CTX);
    expect(slabCount(m)).toBe(1);
    expect(m.storeys[0].elements.find((e) => e.ifcClass === "IfcSlab")!.objectType).toBe("Cubierta");
  });

  it("la CUBIERTA va encima de la última planta (ROOF), con pilares debajo", () => {
    const m = buildModel({ ...base, grid: { sepX: 6, sepY: 6 } }, CTX);
    const top = m.storeys[m.storeys.length - 1];
    const cub = top.elements.find((e) => e.code === "AQ-FOR-CUB")!;
    expect(cub.predefinedType).toBe("ROOF");
    expect(cub.storeyIndex).toBe(4); // nivel n, encima de la planta 3
    expect(top.elements.some((e) => e.ifcClass === "IfcColumn")).toBe(true); // la última planta TIENE pilares
  });
});

describe("buildModel — huecos de forjado (IfcOpeningElement, host=forjado)", () => {
  const base: BuildingInput = {
    project: "R", building: "B",
    storeys: { count: 4, height: 3 },
    plan: {
      rooms: { count: 8, layout: "both-sides" }, corridor: { width: 1.4 },
      cores: [{ orientation: "SE", detail: "asc+esc" }, { orientation: "NO", detail: "esc" }],
    },
  };

  it("un hueco por (núcleo × forjado): 2 núcleos × 3 plantas con forjado = 6", () => {
    const m = buildModel(base, CTX);
    expect(openingCount(m)).toBe(6);
    expect(m.storeys.map((s) => s.elements.filter((e) => e.ifcClass === "IfcOpeningElement").length)).toEqual([0, 2, 2, 2]);
  });

  it("el hueco tiene host = el forjado de su planta (capa relacional)", () => {
    const m = buildModel(base, CTX);
    const op = m.storeys[1].elements.find((e) => e.ifcClass === "IfcOpeningElement")!;
    expect(op.host).toBe("AQ-FOR-P01");
    expect(op.predefinedType).toBe("OPENING");
    expect(op.placement.kind).toBe("polygon");
    expect(op.uriBsdd).toContain("/class/IfcOpeningElement");
  });

  it("el puente emite losas con huecos y forjados:false", () => {
    const spec = toAltoSpec(buildModel(base, CTX), { ancho: 31, largo: 15.6, altura: 3 });
    expect(spec.edificios[0].forjados).toBe(false);
    expect(spec.losas?.length).toBe(4); // 3 suelos + cubierta
    const conHuecos = spec.losas?.find((l) => (l.huecos?.length ?? 0) > 0);
    expect(conHuecos?.huecos?.length).toBe(2);
  });

  it("residencia 4 plantas · 2 núcleos no regresiona", () => {
    const r = checkFixture(resid as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });
});

describe("resolveGrid — ejes explícitos (alineación no uniforme)", () => {
  it("ejes Y explícitos caen exactos, incl. la fachada lejana", () => {
    const g = resolveGrid({ sepX: 5, axesY: [0, 6.75, 15] }, { W: 20, D: 15 });
    expect(g.axesY).toEqual([0, 6.75, 15]);
    expect(g.axesX).toEqual([0, 5, 10, 15, 20]); // atajo sep 5 anclado a 0 y 20
  });

  it("atajo uniforme ancla a las dos fachadas (incluye 0 y W)", () => {
    const g = resolveGrid({ sepX: 6, sepY: 6 }, { W: 15, D: 15 });
    expect(g.axesX[0]).toBe(0);
    expect(g.axesX[g.axesX.length - 1]).toBe(15);
  });

  it("un nudo cae exacto en la fachada norte (y = D), antes desplazado", () => {
    const m = buildModel(
      { project: "R", building: "B", storeys: { count: 2, height: 3 }, plan: { rooms: null, corridor: null, cores: [] }, grid: { sepX: 5, axesY: [0, 6.75, 15] } },
      { W: 20, D: 15 },
    );
    const cols = m.storeys[0].elements.filter((e) => e.ifcClass === "IfcColumn");
    expect(cols.some((c) => c.placement.kind === "point" && c.placement.y === 15)).toBe(true);
  });
});

describe("buildModel — muros de fachada (IfcWall, línea, por planta)", () => {
  const base: BuildingInput = {
    project: "R", building: "B",
    storeys: { count: 4, height: 3 },
    plan: { rooms: null, corridor: null, cores: [] },
  };

  it("4 muros de fachada por planta (lados de la huella)", () => {
    const m = buildModel(base, CTX);
    expect(wallCount(m)).toBe(16);
    expect(m.storeys.map((s) => s.elements.filter((e) => e.ifcClass === "IfcWall").length)).toEqual([4, 4, 4, 4]);
  });

  it("el muro es LÍNEA, exterior, con su extensión [i,i+1]", () => {
    const m = buildModel(base, CTX);
    const w = m.storeys[0].elements.find((e) => e.ifcClass === "IfcWall")!;
    expect(w.placement.kind).toBe("line");
    expect(w.exterior).toBe(true);
    expect(w.spans).toEqual([0, 1]);
    expect(w.code).toBe("AQ-MUR-P00-FAC-S");
    expect(w.uriBsdd).toContain("/class/IfcWall");
  });

  it("el puente emite muros[] y muros_perimetrales:false", () => {
    const spec = toAltoSpec(buildModel(base, CTX), { ancho: 31, largo: 15.6, altura: 3 });
    expect(spec.muros?.length).toBe(16);
    expect(spec.edificios[0].muros_perimetrales).toBe(false);
    expect(spec.muros?.[0]).toMatchObject({ nivel: "Planta Baja", exterior: true, espesor: 0.25, altura: 3 });
  });
});
