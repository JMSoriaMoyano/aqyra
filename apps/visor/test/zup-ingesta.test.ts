import { describe, it, expect } from "vitest";
import { aZup } from "@aqyra/visor"; // helper NUEVO a exportar (viewer/ifc-loader)

// Convenio Z-up (paso 1): la ingesta deshace el swap de web-ifc con +90° sobre X:
//   (x, y, z)_yup → (x, −z, y)_ifc
// Es el inverso EXACTO de m(v)=[x, z, −y] de bcf.ts (round-trip comprobado).
describe("Ingesta Z-up · deshace el swap de web-ifc (+90° X)", () => {
  it("mapea un vértice Y-up de web-ifc de vuelta a IFC Z-up", () => {
    expect(aZup([1, 2, 3])).toEqual([1, -3, 2]);
  });

  it("round-trip: IFC→(web-ifc Y-up)→aZup === IFC", () => {
    const ifc: [number, number, number] = [10, 20, 30];
    const yup: [number, number, number] = [ifc[0], ifc[2], -ifc[1]]; // lo que entrega web-ifc
    expect(aZup(yup)).toEqual(ifc);
  });
});
