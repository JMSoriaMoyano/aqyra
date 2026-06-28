/**
 * Arnés golden — generador parking-comb · DISPOSICIÓN (batería / línea).
 *
 * Llave 1 (golden verde): prueba que el generador es DETERMINISTA y que la
 * disposición batería/línea coloca footprints ALINEADOS A EJES (la oblicua queda
 * para un incremento de núcleo: exige footprint girado). La IA prepara; la firma
 * (Llave 2) es de JM. Un fallo se arregla en el código, nunca aflojando el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/parking.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { parkingGenerator, type ParkingParams, type Footprint } from "../src/generators";
import { checkFixture, type CaseFixture } from "../src/fixture";

import bateria from "../fixtures/parking-120x24-2filas.json";
import linea from "../fixtures/parking-linea-60x12.json";

const overlap = (a: Footprint, b: Footprint): boolean =>
  a.x < b.x + b.w - 1e-6 && a.x + a.w > b.x + 1e-6 &&
  a.y < b.y + b.d - 1e-6 && a.y + a.d > b.y + 1e-6;

const plazas = (p: ParkingParams, W: number, D: number): Footprint[] =>
  parkingGenerator.generate(p, { W, D })
    .filter((s) => s.objectType === "PlazaAparcamiento")
    .map((s) => s.footprint);

const filas = (fps: Footprint[]): number => new Set(fps.map((f) => f.y.toFixed(2))).size;

describe("parking-comb · disposición batería/línea", () => {
  it("determinista: mismo input → mismos footprints", () => {
    const p: ParkingParams = { bays: 60, aisle: 5.5, disposition: "linea" };
    expect(parkingGenerator.generate(p, { W: 60, D: 12 }))
      .toEqual(parkingGenerator.generate(p, { W: 60, D: 12 }));
  });

  it("default = batería (retrocompatible): plaza perpendicular al vial (2,5 × 5,0)", () => {
    const sinDisp = plazas({ bays: 60, aisle: 5.5 }, 60, 12);
    const bat = plazas({ bays: 60, aisle: 5.5, disposition: "bateria" }, 60, 12);
    expect(sinDisp).toEqual(bat);
    expect(bat[0]).toMatchObject({ w: 2.5, d: 5 });
  });

  it("línea/cordón: la MISMA plaza girada 90° (5,0 × 2,5), sigue alineada a ejes", () => {
    const lin = plazas({ bays: 60, aisle: 5.5, disposition: "linea" }, 60, 12);
    expect(lin[0]).toMatchObject({ w: 5, d: 2.5 });
  });

  it("60×12: línea = 24 plazas en 2 filas; batería = 24 en 1 fila (geometría distinta)", () => {
    const lin = plazas({ bays: 60, aisle: 5.5, disposition: "linea" }, 60, 12);
    const bat = plazas({ bays: 60, aisle: 5.5, disposition: "bateria" }, 60, 12);
    expect([lin.length, filas(lin)]).toEqual([24, 2]);
    expect([bat.length, filas(bat)]).toEqual([24, 1]);
  });

  it("sin solapes y dentro de la huella (línea, con y sin rampa)", () => {
    const casos: ParkingParams[] = [
      { bays: 60, aisle: 5.5, disposition: "linea" },
      { bays: 60, aisle: 5.5, disposition: "linea", ramps: ["O"] },
    ];
    for (const params of casos) {
      const fps = plazas(params, 60, 12);
      for (const f of fps) {
        expect(f.x).toBeGreaterThanOrEqual(-1e-6);
        expect(f.y).toBeGreaterThanOrEqual(-1e-6);
        expect(f.x + f.w).toBeLessThanOrEqual(60 + 1e-6);
        expect(f.y + f.d).toBeLessThanOrEqual(12 + 1e-6);
      }
      for (let i = 0; i < fps.length; i++)
        for (let j = i + 1; j < fps.length; j++)
          expect(overlap(fps[i], fps[j])).toBe(false);
    }
  });
});

describe("fixtures golden — anti-regresión", () => {
  it("parking batería 120×24 (2 filas, 2 rampas) no regresiona", () => {
    const r = checkFixture(bateria as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });

  it("parking línea/cordón 60×12 (2 filas) no regresiona", () => {
    const r = checkFixture(linea as unknown as CaseFixture);
    expect(r.diffs).toEqual([]);
    expect(r.ok).toBe(true);
  });
});
