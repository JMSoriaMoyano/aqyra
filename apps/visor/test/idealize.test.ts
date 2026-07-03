// Derivación del modelo analítico (PURO, sin web-ifc): PCA del eje, clustering
// de nudos por tolerancia y clasificación por PredefinedType. Es la MECÁNICA del
// pre-proceso (cebo). Cubre la lección D-008: lo derivado es geometría, no
// criterio; debe ser revisable.
import { describe, it, expect } from "vitest";
import { deriveModel, pcaAxisStrategy } from "@aqyra/visor";
import type { PhysicalElement } from "@aqyra/visor";

/** 8 vértices de una caja AABB [x0,x1]×[y0,y1]×[z0,z1] (xyz plano). */
function box(x0: number, x1: number, y0: number, y1: number, z0: number, z1: number): number[] {
  const v: number[] = [];
  for (const x of [x0, x1]) for (const y of [y0, y1]) for (const z of [z0, z1]) v.push(x, y, z);
  return v;
}

describe("idealize · derivación del analítico (D-009)", () => {
  it("deriva el eje de una barra prismática por PCA (caja 0.3×0.3×4 a lo largo de Z)", () => {
    const el: PhysicalElement = { expressId: 30, ifcType: "IFCBEAM", verts: box(0, 0.3, 0, 0.3, 0, 4) };
    const m = deriveModel([el]);
    expect(m.members.length).toBe(1);
    expect(m.members[0]!.kind).toBe("beam");
    expect(m.members[0]!.length).toBeCloseTo(4, 3);
    const zs = m.nodes.map((n) => n.z).sort((a, b) => a - b);
    expect(zs[0]!).toBeCloseTo(0, 3);
    expect(zs[zs.length - 1]!).toBeCloseTo(4, 3);
  });

  it("funde extremos coincidentes en un nudo compartido (conectividad real)", () => {
    const a: PhysicalElement = { expressId: 1, ifcType: "IFCCOLUMN", verts: box(0, 0.3, 0, 0.3, 0, 3) };
    const b: PhysicalElement = { expressId: 2, ifcType: "IFCCOLUMN", verts: box(0, 0.3, 0, 0.3, 3, 6) };
    const m = deriveModel([a, b], { tolerance: 0.02 });
    expect(m.members.length).toBe(2);
    expect(m.nodes.length).toBe(3); // 0 — 3(compartido) — 6
  });

  it("clasifica IfcMember por PredefinedType (CHORD → chord)", () => {
    const el: PhysicalElement = { expressId: 9, ifcType: "IFCMEMBER", predefinedType: "CHORD", verts: box(0, 4, 0, 0.2, 0, 0.2) };
    const m = deriveModel([el]);
    expect(m.members[0]!.kind).toBe("chord");
  });

  it("omite elementos no-barra (slab/wall): no fabrica ejes espurios", () => {
    const slab: PhysicalElement = { expressId: 5, ifcType: "IFCSLAB", verts: box(0, 5, 0, 5, 0, 0.3) };
    expect(pcaAxisStrategy.axisOf(slab)).toBeNull();
    expect(deriveModel([slab]).members.length).toBe(0);
  });

  it("conserva la trazabilidad al elemento físico (ifcGlobalId)", () => {
    const el: PhysicalElement = { expressId: 7, globalId: "GID-BEAM-7", ifcType: "IFCBEAM", verts: box(0, 0.3, 0, 0.3, 0, 4) };
    const m = deriveModel([el]);
    expect(m.members[0]!.ifcGlobalId).toBe("GID-BEAM-7");
    expect(m.members[0]!.id).toBe("B7");
  });

  it("parte la barra donde otra acomete a mitad de vano (conectividad T: tirante/vigueta)", () => {
    // Pilar vertical 0→6 y una viga cuyo EXTREMO cae en (0,0,3): acomete a media altura.
    const col: PhysicalElement = { expressId: 1, ifcType: "IFCCOLUMN", verts: box(-0.15, 0.15, -0.15, 0.15, 0, 6) };
    const beam: PhysicalElement = { expressId: 2, ifcType: "IFCBEAM", verts: box(0, 4, -0.1, 0.1, 2.9, 3.1) };
    const m = deriveModel([col, beam], { tolerance: 0.15 });
    expect(m.members.length).toBe(3); // pilar partido (0–3, 3–6) + viga = 3
    expect(m.nodes.some((n) => Math.abs(n.z - 3) < 0.2)).toBe(true); // nudo compartido a cota 3
  });

  it("splitAtIntersections:false desactiva el partido (un eje por elemento)", () => {
    const col: PhysicalElement = { expressId: 1, ifcType: "IFCCOLUMN", verts: box(-0.15, 0.15, -0.15, 0.15, 0, 6) };
    const beam: PhysicalElement = { expressId: 2, ifcType: "IFCBEAM", verts: box(0, 4, -0.1, 0.1, 2.9, 3.1) };
    const m = deriveModel([col, beam], { tolerance: 0.15, splitAtIntersections: false });
    expect(m.members.length).toBe(2);
  });

  it("conecta tirante vertical × viga de forjado en su CRUCE interior (parte ambas)", () => {
    const tie: PhysicalElement = { expressId: 1, ifcType: "IFCMEMBER", verts: box(-0.1, 0.1, -0.1, 0.1, 0, 10) };
    const beam: PhysicalElement = { expressId: 2, ifcType: "IFCBEAM", verts: box(-3, 3, -0.1, 0.1, 4.9, 5.1) };
    const m = deriveModel([tie, beam], { tolerance: 0.15 });
    expect(m.members.length).toBe(4); // tirante (2) + viga (2), partidos en el nudo común
    expect(m.nodes.some((n) => Math.abs(n.z - 5) < 0.2 && Math.abs(n.x) < 0.2)).toBe(true);
  });

  it("NO conecta las aspas inclinadas de un arriostramiento (conservador)", () => {
    const d1: PhysicalElement = { expressId: 1, ifcType: "IFCMEMBER", verts: [0, 0, 0, 4, 0, 4] };
    const d2: PhysicalElement = { expressId: 2, ifcType: "IFCMEMBER", verts: [0, 0, 4, 4, 0, 0] };
    const m = deriveModel([d1, d2], { tolerance: 0.15 });
    expect(m.members.length).toBe(2); // cruzan en (2,0,2) pero NO se parten (inclinadas)
  });

  it("deriva losa→diafragma (normal vertical) y muro→lámina (con malla)", () => {
    const slab: PhysicalElement = { expressId: 1, ifcType: "IFCSLAB", verts: box(0, 6, 0, 4, 0, 0.2) };
    const wall: PhysicalElement = { expressId: 2, ifcType: "IFCWALL", verts: box(0, 4, 0, 0.2, 0, 3) };
    const m = deriveModel([slab, wall]);
    expect(m.surfaces.length).toBe(2);
    const s = m.surfaces.find((x) => x.id === "S1")!;
    expect(s.kind).toBe("diaphragm");
    expect(Math.abs(s.normal[2])).toBeGreaterThan(0.95); // normal ~ vertical (Z)
    expect(s.outline.length).toBe(4);
    expect(s.planar).toBe(true);
    expect(s.area).toBeGreaterThan(0);
    const w = m.surfaces.find((x) => x.id === "S2")!;
    expect(w.kind).toBe("shell");
    expect((w.mesh?.nodes.length ?? 0)).toBeGreaterThan(0);
    expect((w.mesh?.quads.length ?? 0)).toBeGreaterThan(0);
  });

  it("Indicación A: el área real (envolvente) de una planta trapecial es menor que el rectángulo", () => {
    // Trapecio 0,0 · 10,0 · 8,4 · 2,4 (área real 32) en losa fina; rectángulo envolvente 40.
    const tz: number[] = [];
    for (const [x, y] of [[0, 0], [10, 0], [8, 4], [2, 4]]) for (const z of [0, 0.2]) tz.push(x, y, z);
    const s = deriveModel([{ expressId: 9, ifcType: "IFCSLAB", verts: tz }]).surfaces[0]!;
    expect(s.area).toBeCloseTo(32, 0);
    expect(s.extentArea).toBeCloseTo(40, 0);
    expect(s.area).toBeLessThan(s.extentArea);
  });

  it("Indicación B: un núcleo-caja (no plano) se marca planar=false (no colapsar a 1 lámina)", () => {
    const bx: number[] = [];
    for (const x of [0, 4]) for (const y of [0, 4]) for (const z of [0, 3]) bx.push(x, y, z);
    const s = deriveModel([{ expressId: 9, ifcType: "IFCWALL", verts: bx }]).surfaces[0]!;
    expect(s.planar).toBe(false);
    expect(s.mesh).toBeUndefined(); // no se falsea como lámina plana
  });

  it("alternativa B: un núcleo-caja genera una columna-cajón con sección (A, Ix, Iy, J)", () => {
    const bx: number[] = [];
    for (const x of [0, 4]) for (const y of [0, 4]) for (const z of [0, 9]) bx.push(x, y, z);
    const c = deriveModel([{ expressId: 9, ifcType: "IFCWALL", verts: bx }], { coreThickness: 0.3 }).cores[0]!;
    expect(c.Agross).toBeCloseTo(16, 0); // contorno exterior 4×4 (bruta)
    expect(c.hollow).toBe(true); // sección HUECA (exterior − interior)
    expect(c.A).toBeLessThan(c.Agross); // hueca < bruta
    expect(c.A).toBeGreaterThan(0);
    expect(c.Ix).toBeGreaterThan(0);
    expect(c.Iy).toBeGreaterThan(0);
    expect(c.J).toBeGreaterThan(0);
    expect(c.perimeter).toBeCloseTo(16, 0);
  });

  it("agrupa caras planas en un NÚCLEO por esquinas: caja cerrada (4 caras) vs U abierta (3)", () => {
    // 4 muros planos finos (e=0,3) formando una caja 6×4 (alto 10).
    const sur: PhysicalElement = { expressId: 1, ifcType: "IFCWALL", verts: box(0, 6, 0, 0.3, 0, 10) };
    const nor: PhysicalElement = { expressId: 2, ifcType: "IFCWALL", verts: box(0, 6, 3.7, 4, 0, 10) };
    const est: PhysicalElement = { expressId: 3, ifcType: "IFCWALL", verts: box(5.7, 6, 0, 4, 0, 10) };
    const oes: PhysicalElement = { expressId: 4, ifcType: "IFCWALL", verts: box(0, 0.3, 0, 4, 0, 10) };
    const boxModel = deriveModel([sur, nor, est, oes]);
    expect(boxModel.coreGroups.length).toBe(1);
    expect(boxModel.coreGroups[0]!.closed).toBe(true);
    expect(boxModel.coreGroups[0]!.members.length).toBe(4);
    // 4 láminas COSIDAS: malla unificada con nudos de esquina compartidos.
    const m = boxModel.coreGroups[0]!.mesh!;
    expect(m.quads.length).toBeGreaterThan(0);
    expect(m.nodes.length).toBeGreaterThan(0);
    // Quitando una cara → U abierta.
    const u = deriveModel([sur, nor, est]);
    expect(u.coreGroups.length).toBe(1);
    expect(u.coreGroups[0]!.closed).toBe(false);
  });

  it("Indicación C: marca GRUESO un muro de depósito (e=0,50, h=4,35) y NO una losa fina", () => {
    const muro = deriveModel([{ expressId: 1, ifcType: "IFCWALL", verts: box(0, 21.5, 0, 0.5, 0, 4.35) }]).surfaces[0]!;
    expect(muro.thick).toBe(true); // t/luz ≈ 0,12 > 0,1 → lámina delgada no aplica
    const losa = deriveModel([{ expressId: 2, ifcType: "IFCSLAB", verts: box(0, 6, 0, 4, 0, 0.3) }]).surfaces[0]!;
    expect(losa.thick).toBe(false); // 0,3/4 = 0,075 < 0,1
  });

  it("Indicación C: detecta un muro TORCIDO (plano ladeado de la vertical) como artefacto", () => {
    // Muro fino en un plano inclinado 45° → normal con componente vertical ≈0,71.
    const n = [0, Math.SQRT1_2, Math.SQRT1_2];
    const u = [1, 0, 0];
    const v = [0, Math.SQRT1_2, -Math.SQRT1_2];
    const verts: number[] = [];
    for (const su of [-3, 3]) for (const sv of [-2, 2]) for (const sn of [-0.15, 0.15]) {
      verts.push(u[0] * su + v[0] * sv + n[0] * sn, u[1] * su + v[1] * sv + n[1] * sn, u[2] * su + v[2] * sv + n[2] * sn);
    }
    const torc = deriveModel([{ expressId: 1, ifcType: "IFCWALL", verts }]).surfaces[0]!;
    expect(torc.skewed).toBe(true);
    const recto = deriveModel([{ expressId: 2, ifcType: "IFCWALL", verts: box(0, 6, 0, 0.3, 0, 4) }]).surfaces[0]!;
    expect(recto.skewed).toBe(false);
  });

  it("Indicación C: VERTICALIZA un muro físicamente vertical cuyo plano PCA sale ladeado (~14°)", () => {
    // Panel fino con normal ligeramente inclinada (artefacto); debe enderezarse a vertical.
    const u: [number, number, number] = [1, 0, 0];
    const a = 0.25; // rad (~14°)
    const n: [number, number, number] = [0, Math.cos(a), Math.sin(a)];
    const v: [number, number, number] = [
      n[1] * u[2] - n[2] * u[1],
      n[2] * u[0] - n[0] * u[2],
      n[0] * u[1] - n[1] * u[0],
    ];
    const verts: number[] = [];
    for (const su of [-3, 3]) for (const sv of [-2, 2]) for (const sn of [-0.15, 0.15]) {
      verts.push(u[0] * su + v[0] * sv + n[0] * sn, u[1] * su + v[1] * sv + n[1] * sn, u[2] * su + v[2] * sv + n[2] * sn);
    }
    const s = deriveModel([{ expressId: 1, ifcType: "IFCWALL", verts }]).surfaces[0]!;
    expect(Math.abs(s.normal[2])).toBeLessThan(0.05); // normal horizontal → muro vertical, no torcido
    expect(s.skewed).toBe(false);
  });
});
