/**
 * Arnés golden — MODO EDICIÓN (Hito 2): manipulación directa como DATO (overrides).
 *
 * Llave 1: prueba que un override por código (1) TRASLADA y GIRA el elemento de forma
 * determinista (mismo input → misma salida), (2) ARRASTRA al derivado acoplado (la rampa
 * mueve el hueco que perfora, aunque viva en otra planta), (3) cruza a C1 con las
 * coordenadas YA movidas y la cota z INTACTA → FRONTERA-CERO (sin tocar el contrato), y
 * (4) SIN overrides el modelo es idéntico (no-regresión). La IA prepara; firma JM.
 *
 *   ../node_modules/.bin/vitest run --root . test/overrides.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { buildModel, applyOverride, type BuildingInput, type Placement } from "../src/model";
import { toAltoSpec } from "../src/c1-bridge";

// Mismo caso SABA del golden de la rampa: parking 31×200, 2 plantas, rampa de acceso N.
const saba: BuildingInput = {
  project: "Parking SABA", building: "P",
  storeys: { count: 2, height: 2.5 },
  plan: { rooms: null, corridor: null, cores: [] },
  program: { generator: "parking-comb", params: { bays: 400, aisle: 6, ramps: ["N"] } },
};
const CTX = { W: 31, D: 200 };
const RAMP = "AQ-RAM-P00-01";          // la rampa que sube de PB a P1
const HOLE = "AQ-HUE-P01-RAM-01";      // el hueco que perfora en el forjado de P1

const line = (pl: Placement): { start: [number, number]; end: [number, number] } => {
  if (pl.kind !== "line") throw new Error("se esperaba línea");
  return { start: pl.start, end: pl.end };
};
const findEl = (m: ReturnType<typeof buildModel>, code: string) =>
  m.storeys.flatMap((s) => s.elements).find((e) => e.code === code)!;
const len = (a: [number, number], b: [number, number]): number => Math.hypot(b[0] - a[0], b[1] - a[1]);
const mid = (a: [number, number], b: [number, number]): [number, number] => [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2];

describe("applyOverride — función pura (no muta) y composición giro→traslación", () => {
  it("no muta el placement de entrada", () => {
    const pl: Placement = { kind: "line", start: [0, 0], end: [10, 0] };
    const out = applyOverride(pl, { dx: 5, dy: 2, rotDeg: 90 });
    expect(pl.start).toEqual([0, 0]);        // intacto
    expect(out).not.toBe(pl);
  });
  it("un punto es invariante al giro sobre sí mismo, pero sí se traslada", () => {
    const pl: Placement = { kind: "point", x: 3, y: 4 };
    expect(applyOverride(pl, { rotDeg: 45 })).toEqual({ kind: "point", x: 3, y: 4 });
    expect(applyOverride(pl, { dx: 1, dy: -1 })).toEqual({ kind: "point", x: 4, y: 3 });
  });
});

describe("buildModel — traslación de la rampa (dato) y arrastre del hueco acoplado", () => {
  it("dy:-10 desplaza inicio/fin de la rampa 10 m exactos", () => {
    const base = line(findEl(buildModel(saba, CTX), RAMP).placement);
    const mov = line(findEl(buildModel({ ...saba, overrides: { [RAMP]: { dy: -10 } } }, CTX), RAMP).placement);
    expect(mov.start[1]).toBeCloseTo(base.start[1] - 10, 6);
    expect(mov.end[1]).toBeCloseTo(base.end[1] - 10, 6);
    expect(mov.start[0]).toBeCloseTo(base.start[0], 6);   // X intacta
  });

  it("el HUECO que perfora la rampa se mueve con ella (mismo driver, otra planta)", () => {
    const baseHole = findEl(buildModel(saba, CTX), HOLE).placement;
    const movHole = findEl(buildModel({ ...saba, overrides: { [RAMP]: { dy: -10 } } }, CTX), HOLE).placement;
    if (baseHole.kind !== "polygon" || movHole.kind !== "polygon") throw new Error("polígono");
    movHole.contour.forEach(([, y], k) => expect(y).toBeCloseTo(baseHole.contour[k][1] - 10, 6));
    movHole.contour.forEach(([x], k) => expect(x).toBeCloseTo(baseHole.contour[k][0], 6)); // X intacta
  });
});

describe("buildModel — giro de la rampa sobre su centroide", () => {
  it("rotDeg:180 intercambia los extremos (gira media vuelta)", () => {
    const base = line(findEl(buildModel(saba, CTX), RAMP).placement);
    const rot = line(findEl(buildModel({ ...saba, overrides: { [RAMP]: { rotDeg: 180 } } }, CTX), RAMP).placement);
    expect(rot.start[1]).toBeCloseTo(base.end[1], 2);
    expect(rot.end[1]).toBeCloseTo(base.start[1], 2);
  });
  it("rotDeg:90 conserva longitud y centroide, y pone el eje perpendicular", () => {
    const base = line(findEl(buildModel(saba, CTX), RAMP).placement);
    const rot = line(findEl(buildModel({ ...saba, overrides: { [RAMP]: { rotDeg: 90 } } }, CTX), RAMP).placement);
    expect(len(rot.start, rot.end)).toBeCloseTo(len(base.start, base.end), 2);   // longitud
    expect(mid(rot.start, rot.end)[0]).toBeCloseTo(mid(base.start, base.end)[0], 2); // centroide X
    expect(mid(rot.start, rot.end)[1]).toBeCloseTo(mid(base.start, base.end)[1], 2); // centroide Y
    expect(rot.start[1]).toBeCloseTo(rot.end[1], 2);   // eje N-S original → ahora E-O (misma y)
  });
});

describe("c1-bridge — la rampa movida cruza por `rampas` con z intacta · FRONTERA-CERO", () => {
  it("inicio/fin reflejan la traslación; la cota z NO cambia (es del nivel)", () => {
    const dims = { ancho: 31, largo: 200, altura: 2.5 };
    const base = toAltoSpec(buildModel(saba, CTX), dims).rampas![0];
    const mov = toAltoSpec(buildModel({ ...saba, overrides: { [RAMP]: { dy: -10 } } }, CTX), dims).rampas![0];
    expect(mov.inicio[1]).toBeCloseTo(base.inicio[1] - 10, 3);   // y baja movida
    expect(mov.fin[1]).toBeCloseTo(base.fin[1] - 10, 3);         // y alta movida
    expect(mov.inicio[2]).toBe(base.inicio[2]);                  // z baja intacta (0)
    expect(mov.fin[2]).toBe(base.fin[2]);                        // z alta intacta (2,5)
  });
  it("el hueco acoplado cruza como losas[].huecos ya movido", () => {
    const dims = { ancho: 31, largo: 200, altura: 2.5 };
    const base = toAltoSpec(buildModel(saba, CTX), dims).losas!.find((l) => l.nombre === "AQ-FOR-P01")!.huecos![0];
    const mov = toAltoSpec(buildModel({ ...saba, overrides: { [RAMP]: { dy: -10 } } }, CTX), dims).losas!.find((l) => l.nombre === "AQ-FOR-P01")!.huecos![0];
    mov.contorno.forEach(([, y], k) => expect(y).toBeCloseTo(base.contorno[k][1] - 10, 3));
  });
});

describe("determinismo y no-regresión", () => {
  it("mismo input con override → misma salida (golden-able)", () => {
    const a = buildModel({ ...saba, overrides: { [RAMP]: { dx: 3, dy: -7, rotDeg: 90 } } }, CTX);
    const b = buildModel({ ...saba, overrides: { [RAMP]: { dx: 3, dy: -7, rotDeg: 90 } } }, CTX);
    expect(JSON.stringify(a)).toBe(JSON.stringify(b));
  });
  it("SIN overrides el modelo es byte-idéntico al de siempre (no regresiona)", () => {
    const sinCampo = buildModel(saba, CTX);
    const conCampoVacio = buildModel({ ...saba, overrides: {} }, CTX);
    expect(JSON.stringify(conCampoVacio)).toBe(JSON.stringify(sinCampo));
  });
  it("un override a un código inexistente no altera nada", () => {
    const base = buildModel(saba, CTX);
    const noop = buildModel({ ...saba, overrides: { "AQ-NO-EXISTE": { dx: 99, rotDeg: 33 } } }, CTX);
    expect(JSON.stringify(noop)).toBe(JSON.stringify(base));
  });
});
