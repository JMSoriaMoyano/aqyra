/**
 * Arnés golden — USABILIDAD · la planta tipo 2D CABE en su panel (no tapa el 3D).
 *
 * Llave 1 (golden verde): `fitContain` encaja W×D dentro del recuadro por ancho U
 * alto, preservando proporción y centrando. La regresión que evita: una planta muy
 * alargada (p. ej. un aparcamiento estrecho y largo) cuya altura se disparaba y se
 * salía del panel cubriendo la maqueta. Frontera C1: cero. La IA prepara; firma JM.
 *
 *   ../node_modules/.bin/vitest run --root . test/plan-fit.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { fitContain, type Box } from "../src/plan-fit";

const BOX: Box = { x: 60, y: 484, w: 382, h: 184 }; // hueco útil del panel de Diseño

describe("fitContain — la huella nunca se sale del recuadro", () => {
  it("cuadrada: cabe y se centra", () => {
    const f = fitContain(20, 20, BOX);
    expect(f.fw).toBeCloseTo(184);   // limitada por el alto (el menor)
    expect(f.fh).toBeCloseTo(184);
    expect(f.fx).toBeCloseTo(60 + (382 - 184) / 2);
    expect(f.fy).toBeCloseTo(484);
  });

  it("muy alargada (D≫W): se limita por el ALTO y NO desborda", () => {
    const f = fitContain(16, 80, BOX); // parking estrecho y largo
    expect(f.fh).toBeLessThanOrEqual(BOX.h + 1e-6);
    expect(f.fw).toBeLessThanOrEqual(BOX.w + 1e-6);
    expect(f.fh).toBeCloseTo(184);     // toca el alto
    expect(f.fw).toBeCloseTo(16 * (184 / 80));
  });

  it("muy ancha (W≫D): se limita por el ANCHO y NO desborda", () => {
    const f = fitContain(100, 10, BOX);
    expect(f.fw).toBeLessThanOrEqual(BOX.w + 1e-6);
    expect(f.fh).toBeLessThanOrEqual(BOX.h + 1e-6);
    expect(f.fw).toBeCloseTo(382);
  });

  it("preserva la proporción W:D en todos los casos", () => {
    for (const [W, D] of [[31, 15.6], [16, 80], [100, 10]] as const) {
      const f = fitContain(W, D, BOX);
      expect(f.fw / f.fh).toBeCloseTo(W / D, 5);
    }
  });

  it("queda dentro de los límites del recuadro (centrado, sin recorte)", () => {
    const f = fitContain(16, 80, BOX);
    expect(f.fx).toBeGreaterThanOrEqual(BOX.x - 1e-6);
    expect(f.fy).toBeGreaterThanOrEqual(BOX.y - 1e-6);
    expect(f.fx + f.fw).toBeLessThanOrEqual(BOX.x + BOX.w + 1e-6);
    expect(f.fy + f.fh).toBeLessThanOrEqual(BOX.y + BOX.h + 1e-6);
  });
});
