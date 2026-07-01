/**
 * Arnés golden — USABILIDAD · slice #2: divisores arrastrables (splitter).
 *
 * Llave 1 (golden verde) del NÚCLEO DETERMINISTA del splitter: el clampeo de
 * tamaños (un panel nunca baja de su mínimo ni se come al vecino) y el saneado de
 * los tamaños persistidos (defensa contra localStorage corrupto/manipulado). El
 * arrastre con puntero y la medición de layout son visuales (jsdom no compone
 * layout) → su verificación es la Llave 2 (el ojo de JM en pantalla).
 *
 * Frontera C1: cero. La IA prepara; la firma es de JM. Un fallo se arregla en el
 * código, nunca aflojando el golden.
 *
 *   ../node_modules/.bin/vitest run --root . test/splitter.golden.test.ts
 */
import { describe, it, expect } from "vitest";
import { clampSize, sanitizeSizes } from "../src/splitter";

describe("clampSize — un panel nunca sale del rango [min, max]", () => {
  it("respeta el valor dentro de rango", () => {
    expect(clampSize(200, 80, 400)).toBe(200);
  });
  it("no baja del mínimo", () => {
    expect(clampSize(40, 80, 400)).toBe(80);
  });
  it("no supera el máximo (el vecino no cede más)", () => {
    expect(clampSize(900, 80, 400)).toBe(400);
  });
  it("si max < min, gana min (degenerado: el vecino ya está al límite)", () => {
    expect(clampSize(500, 120, 50)).toBe(120);
    expect(clampSize(10, 120, 50)).toBe(120);
  });
});

describe("sanitizeSizes — defensa del estado persistido (formato abierto)", () => {
  const keys = ["tree", "chat"];
  it("conserva solo claves conocidas con números finitos > 0", () => {
    expect(sanitizeSizes({ tree: 320, chat: 400, otra: 999 }, keys)).toEqual({ tree: 320, chat: 400 });
  });
  it("descarta no-números, negativos, cero, NaN e Infinity", () => {
    expect(sanitizeSizes({ tree: "320", chat: -10 }, keys)).toEqual({});
    expect(sanitizeSizes({ tree: 0, chat: NaN }, keys)).toEqual({});
    expect(sanitizeSizes({ tree: Infinity, chat: 380 }, keys)).toEqual({ chat: 380 });
  });
  it("tolera entradas basura sin lanzar (null, array, string, number)", () => {
    expect(sanitizeSizes(null, keys)).toEqual({});
    expect(sanitizeSizes([1, 2, 3], keys)).toEqual({});
    expect(sanitizeSizes("corrupto", keys)).toEqual({});
    expect(sanitizeSizes(42, keys)).toEqual({});
  });
});
