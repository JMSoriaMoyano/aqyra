/**
 * Arnés golden — PUENTE GESTO→DATOS del viewport (Pieza 2): `deriveOverride`.
 *
 * Llave 1: prueba que `deriveOverride` es el INVERSO de `applyOverride` (ida y vuelta):
 * (1) derivar de un antes/después recupera el override que lo produjo; (2) aplicar el
 * override derivado reproduce el placement observado. Es el contrato que el gizmo (Three
 * o cualquier renderer) debe cumplir: el dato NO se inventa, se deriva. La IA prepara; JM firma.
 *
 *   ../node_modules/.bin/vitest run --root . test/derive-override.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { applyOverride, deriveOverride, type Placement, type ElementOverride } from "../src/model";

const ramp: Placement = { kind: "line", start: [15.5, 200], end: [15.5, 183.33] };
const hole: Placement = { kind: "polygon", contour: [[12.5, 183.33], [18.5, 183.33], [18.5, 200], [12.5, 200]] };

const cl = (a: number, b: number, p = 1) => expect(a).toBeCloseTo(b, p);
const eqPlacement = (a: Placement, b: Placement) => {
  expect(a.kind).toBe(b.kind);
  if (a.kind === "line" && b.kind === "line") { cl(a.start[0], b.start[0]); cl(a.start[1], b.start[1]); cl(a.end[0], b.end[0]); cl(a.end[1], b.end[1]); }
  else if (a.kind === "polygon" && b.kind === "polygon") a.contour.forEach((p, i) => { cl(p[0], (b.contour[i])[0]); cl(p[1], (b.contour[i])[1]); });
  else if (a.kind === "point" && b.kind === "point") { cl(a.x, b.x); cl(a.y, b.y); }
};

describe("deriveOverride — recupera el override que produjo el antes/después (línea)", () => {
  const cases: ElementOverride[] = [
    { dx: 3, dy: -7 }, { rotDeg: 90 }, { rotDeg: -45 }, { dx: -2, dy: 4, rotDeg: 30 }, { dx: 10, dy: 0, rotDeg: 180 },
  ];
  for (const ov of cases) {
    it(`rampa · ${JSON.stringify(ov)}`, () => {
      const observed = applyOverride(ramp, ov);
      const back = deriveOverride(ramp, observed);
      cl(back.dx ?? 0, ov.dx ?? 0); cl(back.dy ?? 0, ov.dy ?? 0); cl(back.rotDeg ?? 0, ov.rotDeg ?? 0);
    });
  }
});

describe("deriveOverride — polígono (hueco) y reconstrucción exacta del placement", () => {
  it("hueco · {dx,dy,rotDeg} se recupera", () => {
    const ov = { dx: -5, dy: 8, rotDeg: 60 };
    const back = deriveOverride(hole, applyOverride(hole, ov));
    cl(back.dx ?? 0, -5); cl(back.dy ?? 0, 8); cl(back.rotDeg ?? 0, 60);
  });
  it("aplicar el override derivado reproduce el placement observado (línea y polígono)", () => {
    for (const [base, ov] of [[ramp, { dx: 4, dy: -3, rotDeg: 75 }], [hole, { dx: -6, dy: 2, rotDeg: -120 }]] as const) {
      const observed = applyOverride(base, ov);
      const reapplied = applyOverride(base, deriveOverride(base, observed));
      eqPlacement(reapplied, observed);
    }
  });
});

describe("deriveOverride — casos límite", () => {
  it("sin movimiento → override nulo", () => {
    const back = deriveOverride(ramp, ramp);
    cl(back.dx ?? 0, 0); cl(back.dy ?? 0, 0); cl(back.rotDeg ?? 0, 0);
  });
  it("un punto sólo recupera traslación (giro no recuperable → 0)", () => {
    const base: Placement = { kind: "point", x: 3, y: 4 };
    const back = deriveOverride(base, applyOverride(base, { dx: 2, dy: -1, rotDeg: 90 }));
    cl(back.dx ?? 0, 2); cl(back.dy ?? 0, -1); cl(back.rotDeg ?? 0, 0);
  });
});
