// Idealización de superficies por PLANO MEDIO (OBB) — corrige el render del depósito.
// La 1.ª versión del item 2 (descomposición por triángulos) se afinó sobre cajas
// sintéticas perfectas y NO sobrevivía a la geometría real de Revit (IfcFacetedBrep,
// IfcBooleanClippingResult, CSG): los muros se fragmentaban y el relleno sobresalía.
// El modo "obb" deriva UNA lámina por elemento como su superficie media: el eje de
// menor extensión es el espesor; el plano medio perpendicular es la lámina, con
// espesor y orientación REALES. MECÁNICA abierta (cebo), PROPUESTA revisable.
import { describe, it, expect } from "vitest";
import { deriveModel } from "@aqyra/visor";
import type { PhysicalElement } from "@aqyra/visor";

const OBB = { surfaceMode: "obb" as const };

/** 8 vértices de un prisma L(x)×T(y)×H(z), opcionalmente girado `rot` en planta y trasladado. */
function box(L: number, T: number, H: number, rot = 0, cx = 0, cy = 0, cz = 0): number[] {
  const c = Math.cos(rot), s = Math.sin(rot);
  const v: number[] = [];
  for (const x of [-L / 2, L / 2]) for (const y of [-T / 2, T / 2]) for (const z of [0, H]) {
    v.push(c * x - s * y + cx, s * x + c * y + cy, z + cz);
  }
  return v;
}
const wall = (id: number, verts: number[]): PhysicalElement => ({ expressId: id, ifcType: "IFCWALL", verts });

describe("idealize · plano medio por OBB (corrige el render real del depósito)", () => {
  it("un MURO grueso recto → UNA lámina vertical, espesor y área reales, sin tilt", () => {
    const m = deriveModel([wall(1, box(21.5, 0.5, 4.35))], OBB);
    expect(m.surfaces.length).toBe(1);
    const s = m.surfaces[0]!;
    expect(s.kind).toBe("shell");
    expect(s.decomposed).toBe(true);
    expect(s.planar).toBe(true); // nunca falso no-plano (rojo)
    expect(s.skewed).toBe(false); // nunca muro torcido
    expect(Math.abs(s.normal[2])).toBeLessThan(0.05); // lámina vertical (normal horizontal)
    expect(s.thickness).toBeCloseTo(0.5, 1);
    expect(s.area).toBeCloseTo(21.5 * 4.35, 0);
    expect(s.thick).toBe(true); // t/luz ≈ 0,11 > 0,1
    expect(s.outline.length).toBe(4);
    expect(s.mesh && s.mesh.quads.length).toBeGreaterThan(0);
  });

  it("un MURO girado 18° en planta conserva orientación real (sin tilt del conjunto)", () => {
    const s = deriveModel([wall(1, box(21.5, 0.5, 4.35, (18 * Math.PI) / 180))], OBB).surfaces[0]!;
    expect(s.skewed).toBe(false);
    expect(Math.abs(s.normal[2])).toBeLessThan(0.05); // sigue vertical
    expect(s.thickness).toBeCloseTo(0.5, 1);
    expect(s.area).toBeCloseTo(21.5 * 4.35, 0);
  });

  it("un muro CORTO/BAJO da lámina vertical (la normal = eje de espesor, que es horizontal)", () => {
    const s = deriveModel([wall(1, box(2, 0.2, 4))], OBB).surfaces[0]!;
    expect(Math.abs(s.normal[2])).toBeLessThan(0.5); // normal = espesor (horizontal) → lámina vertical
    expect(s.thickness).toBeCloseTo(0.2, 1);
  });

  it("una LOSA → UN diafragma horizontal con su espesor real", () => {
    const m = deriveModel([{ expressId: 7, ifcType: "IFCSLAB", verts: box(20, 12, 0.6) }], OBB);
    expect(m.surfaces.length).toBe(1);
    const s = m.surfaces[0]!;
    expect(s.kind).toBe("diaphragm");
    expect(Math.abs(s.normal[2])).toBeGreaterThan(0.95); // horizontal
    expect(s.thickness).toBeCloseTo(0.6, 1);
    expect(s.thick).toBe(false); // 0,6/12 < 0,1
    expect(s.area).toBeCloseTo(240, 0);
  });

  it("un muro NO rectangular (con zapata/pie) → una lámina vertical envolvente (proposal)", () => {
    // muro 10×0,5×4 + un pie más ancho abajo (nube no prismática, como un brep de Revit).
    const v = box(10, 0.5, 4);
    for (const x of [-5, 5]) for (const y of [-0.6, 0.6]) for (const z of [0, 0.4]) v.push(x, y, z);
    const s = deriveModel([wall(1, v)], OBB).surfaces[0]!;
    expect(Math.abs(s.normal[2])).toBeLessThan(0.5); // vertical
    expect(s.skewed).toBe(false);
    expect(s.thick).toBe(true); // el pie engruesa → se marca grueso (revisable)
  });

  it("4 muros finos → caja CERRADA cosida (núcleo reconocido por esquinas)", () => {
    // caja 6×4 (alto 10), muros e=0,3 como 4 elementos.
    const m = deriveModel([
      wall(1, box(6, 0.3, 10, 0, 3, 0.15, 0)),     // sur
      wall(2, box(6, 0.3, 10, 0, 3, 3.85, 0)),     // norte
      wall(3, box(0.3, 4, 10, 0, 0.15, 2, 0)),     // oeste
      wall(4, box(0.3, 4, 10, 0, 5.85, 2, 0)),     // este
    ], OBB);
    expect(m.surfaces.length).toBe(4);
    expect(m.surfaces.every((s) => s.planar && !s.skewed)).toBe(true);
    expect(m.coreGroups.length).toBe(1);
    expect(m.coreGroups[0]!.closed).toBe(true);
    expect(m.coreGroups[0]!.mesh!.quads.length).toBeGreaterThan(0);
  });

  it("descarta tiras DEGENERADAS (canto/bordillo, dim. menor < 1 m) — no son láminas", () => {
    // El "muro de 20 cm" del depósito sale como 22 m × 0,1 m → borde casi-1D, no lámina.
    const m = deriveModel([wall(1, box(22, 0.2, 0.1))], OBB); // alto 0,1 m = degenerado
    expect(m.surfaces.length).toBe(0);
    // pero un muro de altura normal SÍ se conserva
    const ok = deriveModel([wall(2, box(22, 0.2, 4.35))], OBB);
    expect(ok.surfaces.length).toBe(1);
  });

  it("compatibilidad: SIN surfaceMode se mantiene el plano PCA único (camino heredado)", () => {
    // mismo núcleo-caja en 1 elemento, modo por defecto → se marca no-plano (como antes).
    const bx: number[] = [];
    for (const x of [0, 4]) for (const y of [0, 4]) for (const z of [0, 3]) bx.push(x, y, z);
    const m = deriveModel([{ expressId: 5, ifcType: "IFCWALL", verts: bx }]); // sin OBB
    expect(m.surfaces[0]!.planar).toBe(false);
    expect(m.surfaces[0]!.decomposed).toBeUndefined();
  });
});
