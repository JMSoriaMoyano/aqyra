/** costHeatColor — rampa del heatmap de coste (V9): pura, determinista, clampeada. */
import { describe, it, expect } from "vitest";
import { costHeatColor } from "@aqyra/visor";

describe("costHeatColor · rampa azul→rojo", () => {
  it("t=0 es azulado y t=1 rojizo", () => {
    const lo = costHeatColor(0);
    const hi = costHeatColor(1);
    expect(lo.b).toBeGreaterThan(lo.r); // azul: b domina
    expect(hi.r).toBeGreaterThan(hi.b); // rojo: r domina
  });
  it("clampa fuera de [0,1] y trata NaN como 0", () => {
    expect(costHeatColor(-5)).toEqual(costHeatColor(0));
    expect(costHeatColor(9)).toEqual(costHeatColor(1));
    expect(costHeatColor(Number.NaN)).toEqual(costHeatColor(0));
  });
  it("es monótona creciente en el canal rojo", () => {
    expect(costHeatColor(0.8).r).toBeGreaterThan(costHeatColor(0.2).r);
  });
});
