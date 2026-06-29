/**
 * Arnés golden — el SALTO: envolvente POLIGONAL (huella opt-in arbitraria).
 *
 * Llave 1 (golden verde): prueba que la huella poligonal (`outline`) deriva de forma
 * DETERMINISTA la FACHADA (aristas del polígono), el FORJADO/CUBIERTA (el polígono) y
 * la RETÍCULA RECORTADA (solo los nudos dentro), y que SIN outline el camino es
 * BYTE-IDÉNTICO al rectángulo de siempre (no regresiona la capa de elementos). El
 * puente C1 es FRONTERA-CERO: serializa losas-polígono y muros-arista sin tocar el
 * contrato. La IA prepara; la firma (Llave 2) es de JM. Un fallo se arregla en el
 * código, nunca aflojando el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/outline.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import {
  buildModel, columnCount, slabCount, wallCount,
  pointInPolygon, cleanOutline, type BuildingInput,
} from "../src/model";
import { checkFixture, type CaseFixture } from "../src/fixture";
import { toAltoSpec } from "../src/c1-bridge";

import envolvente from "../fixtures/envolvente-L-3plantas.json";

// Huella en L sobre bbox 20×20 (se quita el cuadrante NE): 6 vértices CCW.
const L: [number, number][] = [[0, 0], [20, 0], [20, 10], [10, 10], [10, 20], [0, 20]];
const CTX = { W: 20, D: 20 };
const base: BuildingInput = {
  project: "Env", building: "B",
  storeys: { count: 3, height: 3 },
  plan: { rooms: null, corridor: null, cores: [] },
  grid: { sepX: 10, sepY: 10 },
  outline: L,
};

describe("pointInPolygon — borde incluido (un pilar en la fachada cae dentro)", () => {
  const poly = cleanOutline(L)!;
  it("interior, exterior, borde, vértice reflejo y esquina recortada", () => {
    expect(pointInPolygon(5, 5, poly)).toBe(true);    // dentro
    expect(pointInPolygon(15, 15, poly)).toBe(false); // en el cuadrante recortado
    expect(pointInPolygon(20, 10, poly)).toBe(true);  // sobre una arista
    expect(pointInPolygon(10, 10, poly)).toBe(true);  // vértice reflejo (esquina interior)
    expect(pointInPolygon(20, 20, poly)).toBe(false); // esquina eliminada
  });
  it("cleanOutline funde el cierre y exige ≥3 vértices", () => {
    expect(cleanOutline([[0, 0], [10, 0], [10, 10], [0, 0]])).toHaveLength(3); // cierre fundido
    expect(cleanOutline([[0, 0], [1, 1]])).toBeNull();
    expect(cleanOutline(undefined)).toBeNull();
  });
});

describe("buildModel — envolvente poligonal (fachada · forjado · retícula recortada)", () => {
  it("fachada = una arista del polígono por planta (FAC-01…FAC-06)", () => {
    const m = buildModel(base, CTX);
    expect(wallCount(m)).toBe(18); // 6 aristas × 3 plantas
    const fac = m.storeys[0].elements.filter((e) => e.objectType === "Fachada");
    expect(fac.map((e) => e.code)).toEqual([
      "AQ-MUR-P00-FAC-01", "AQ-MUR-P00-FAC-02", "AQ-MUR-P00-FAC-03",
      "AQ-MUR-P00-FAC-04", "AQ-MUR-P00-FAC-05", "AQ-MUR-P00-FAC-06",
    ]);
    expect(fac[0].exterior).toBe(true);
    expect(fac[0].predefinedType).toBe("SOLIDWALL");
  });

  it("forjado y cubierta = el polígono (contorno de 6 vértices)", () => {
    const m = buildModel(base, CTX);
    expect(slabCount(m)).toBe(3); // 2 suelos (P01,P02) + cubierta
    for (const s of m.storeys.flatMap((st) => st.elements).filter((e) => e.ifcClass === "IfcSlab")) {
      expect(s.placement.kind).toBe("polygon");
      if (s.placement.kind === "polygon") expect(s.placement.contour).toHaveLength(6);
    }
  });

  it("retícula RECORTADA: el nudo de la esquina eliminada (20,20) no se coloca", () => {
    const m = buildModel(base, CTX);
    expect(columnCount(m)).toBe(24); // 8 nudos dentro × 3 plantas (de 9 del bbox)
    const cols = m.storeys[0].elements.filter((e) => e.ifcClass === "IfcColumn");
    expect(cols).toHaveLength(8);
    expect(cols.some((c) => c.placement.kind === "point" && c.placement.x === 20 && c.placement.y === 20)).toBe(false);
    expect(cols.map((c) => c.code)).toEqual([
      "AQ-PIL-P00-A1", "AQ-PIL-P00-A2", "AQ-PIL-P00-A3",
      "AQ-PIL-P00-B1", "AQ-PIL-P00-B2", "AQ-PIL-P00-B3",
      "AQ-PIL-P00-C1", "AQ-PIL-P00-C2",
    ]);
  });

  it("determinista: mismo input → misma salida", () => {
    expect(JSON.stringify(buildModel(base, CTX))).toEqual(JSON.stringify(buildModel(base, CTX)));
  });
});

describe("c1-bridge — el salto es FRONTERA-CERO (losas-polígono · muros-arista)", () => {
  it("emite losas con el contorno poligonal, muros por arista y el edificio cede todo", () => {
    const spec = toAltoSpec(buildModel(base, CTX), { ancho: 20, largo: 20, altura: 3 });
    expect(spec.losas?.length).toBe(3);
    expect(spec.losas?.every((l) => l.contorno.length === 6)).toBe(true);
    expect(spec.muros?.length).toBe(18);
    expect(spec.pilares?.length).toBe(24);
    // el macro `edificio` ancho×largo queda informativo: todo se emite explícito
    expect(spec.edificios[0].muros_perimetrales).toBe(false);
    expect(spec.edificios[0].forjados).toBe(false);
    expect(spec.edificios[0].pilares).toBe(false);
  });
});

describe("backward-compat — SIN outline, el rectángulo de siempre (no regresiona)", () => {
  it("fachada vuelve a S/E/N/O y la retícula no se recorta", () => {
    const { outline, ...noOut } = base;
    const m = buildModel(noOut, CTX);
    expect(m.storeys[0].elements.filter((e) => e.objectType === "Fachada").map((e) => e.code)).toEqual([
      "AQ-MUR-P00-FAC-S", "AQ-MUR-P00-FAC-E", "AQ-MUR-P00-FAC-N", "AQ-MUR-P00-FAC-O",
    ]);
    expect(columnCount(m)).toBe(27); // 3×3 nudos × 3 plantas, sin recorte
    const slab = m.storeys[1].elements.find((e) => e.ifcClass === "IfcSlab")!;
    if (slab.placement.kind === "polygon") expect(slab.placement.contour).toHaveLength(4); // rectángulo
  });
});

describe("fixtures golden — anti-regresión", () => {
  it("envolvente L · 3 plantas no regresiona", () => {
    const r = checkFixture(envolvente as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });
});
