// @vitest-environment node
import { describe, it, expect } from "vitest";
import { sunPosition, trueNorthInProject, shadow } from "@aqyra/visor";

// Golden de SOLEAMIENTO y NORTE REAL (P1·A). Ancla: Can Cabassa (Sant Cugat),
// latitud 41.4730°N, longitud 2.0453°E (Catastro, EPSG:4326). Los valores de
// referencia son FÍSICOS: la altitud solar máxima (mediodía solar) a latitud φ es
// 90 − φ + δ, con δ la declinación (≈ +23.44° en solsticio de verano, −23.44° en
// invierno, 0° en equinoccio). La IA prepara; JM firma.
const LAT = 41.4730;
const LON = 2.0453;

/** Altitud máxima del Sol y su azimut a lo largo de un día (barrido de 1 min). */
function dailyMax(dateUtcMidnight: Date): { altitudeDeg: number; azimuthDeg: number } {
  let best = { altitudeDeg: -90, azimuthDeg: 0 };
  for (let m = 0; m < 1440; m++) {
    const d = new Date(dateUtcMidnight.getTime() + m * 60000);
    const s = sunPosition(LAT, LON, d);
    if (s.altitudeDeg > best.altitudeDeg) best = s;
  }
  return best;
}

describe("solar · Norte real (rotación de IfcMapConversion → ejes del proyecto)", () => {
  it("rotationDeg=0 ⇒ Norte = +Y", () => {
    const n = trueNorthInProject(0);
    expect(n.x).toBeCloseTo(0, 6);
    expect(n.y).toBeCloseTo(1, 6);
  });
  it("rotationDeg=90 ⇒ Norte = +X (giro de 90° del proyecto)", () => {
    const n = trueNorthInProject(90);
    expect(n.x).toBeCloseTo(1, 6);
    expect(n.y).toBeCloseTo(0, 6);
  });
});

describe("solar · soleamiento en Can Cabassa (altitud máxima = 90 − φ + δ)", () => {
  it("solsticio de verano: altitud máx ≈ 71.97° mirando al Sur (~180°)", () => {
    const max = dailyMax(new Date("2026-06-21T00:00:00Z"));
    expect(max.altitudeDeg).toBeCloseTo(90 - LAT + 23.44, 0); // ±0.5°
    expect(max.azimuthDeg).toBeGreaterThan(175);
    expect(max.azimuthDeg).toBeLessThan(185);
  });

  it("solsticio de invierno: altitud máx ≈ 25.09°", () => {
    const max = dailyMax(new Date("2026-12-21T00:00:00Z"));
    expect(max.altitudeDeg).toBeCloseTo(90 - LAT - 23.44, 0); // ±0.5°
  });

  it("equinoccio: altitud máx ≈ 48.53° (90 − φ)", () => {
    const max = dailyMax(new Date("2026-03-20T00:00:00Z"));
    expect(max.altitudeDeg).toBeCloseTo(90 - LAT, 0); // ±0.5°
  });

  it("de madrugada el Sol está bajo el horizonte (altitud < 0)", () => {
    // 01:00 UTC = 03:00 local (CEST) en pleno verano: noche cerrada.
    const s = sunPosition(LAT, LON, new Date("2026-06-21T01:00:00Z"));
    expect(s.altitudeDeg).toBeLessThan(0);
  });

  it("por la mañana el Sol sale por el Este (azimut < 180°)", () => {
    // 06:00 UTC = 08:00 local en verano.
    const s = sunPosition(LAT, LON, new Date("2026-06-21T06:00:00Z"));
    expect(s.altitudeDeg).toBeGreaterThan(0);
    expect(s.azimuthDeg).toBeLessThan(180);
  });
});

describe("solar · sombra", () => {
  it("con el Sol a 45° de altitud la sombra mide 1× la altura y apunta opuesta al Sol", () => {
    const sh = shadow({ altitudeDeg: 45, azimuthDeg: 180 }); // Sol al Sur
    expect(sh.lengthFactor).toBeCloseTo(1, 6);
    expect(sh.azimuthDeg).toBe(0); // sombra hacia el Norte
  });
  it("con el Sol en el horizonte la sombra es infinita (sin soleamiento útil)", () => {
    const sh = shadow({ altitudeDeg: 0, azimuthDeg: 120 });
    expect(sh.lengthFactor).toBe(Infinity);
  });
});
