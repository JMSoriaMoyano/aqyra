import { describe, it, expect } from "vitest";
import { mapaColorPorElemento } from "../src/dock";

describe("mapaColorPorElemento · cableado del dock a capacidades del visor (F2.2)", () => {
  it("mapea a expressId solo los globalId presentes en el modelo", () => {
    const porElemento = new Map<string, { v: number }>([
      ["G1", { v: 10 }],
      ["G2", { v: 20 }],
      ["G-ausente", { v: 99 }],
    ]);
    const exprPorGuid = new Map<string, number>([["G1", 101], ["G2", 102]]);
    const mapa = mapaColorPorElemento(porElemento, exprPorGuid, (d) => ({ r: d.v, g: 0, b: 0 }));
    expect(mapa.size).toBe(2);
    expect(mapa.get(101)).toEqual({ r: 10, g: 0, b: 0 });
    expect(mapa.get(102)).toEqual({ r: 20, g: 0, b: 0 });
    expect(mapa.has(999)).toBe(false);
  });

  it("devuelve un mapa vacío si ningún globalId casa (modelo sin ese dato)", () => {
    const mapa = mapaColorPorElemento(
      new Map<string, number>([["A", 1]]),
      new Map<string, number>([["B", 2]]),
      () => ({ r: 0, g: 0, b: 0 }),
    );
    expect(mapa.size).toBe(0);
  });
});
