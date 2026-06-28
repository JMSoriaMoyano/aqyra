// @vitest-environment node
import { describe, it, expect } from "vitest";
import { gridToMesh, localize, elevationRange, type TerrainGrid } from "@aqyra/visor";

// Golden del TERRENO (P1·A). Triangulación de rejilla regular de cotas → TIN.
// La IA prepara; JM firma (el volcado a IFC revisita la decisión 2).
const grid: TerrainGrid = {
  nx: 3, ny: 3, originE: 420200, originN: 4591600, dx: 10, dy: 10,
  heights: [100, 101, 102, 100.5, 101.5, 102.5, 101, 102, 103],
};

describe("terrain · gridToMesh", () => {
  const m = gridToMesh(grid);
  it("genera nx*ny vértices y 2 triángulos por celda", () => {
    expect(m.positions.length).toBe(9);
    expect(m.triangles.length).toBe(2 * (3 - 1) * (3 - 1)); // 8
  });
  it("coloca los vértices en la rejilla (E,N,Z)", () => {
    expect(m.positions[0]).toEqual([420200, 4591600, 100]);
    expect(m.positions[8]).toEqual([420220, 4591620, 103]);
  });
  it("todos los índices de triángulo son válidos", () => {
    const max = Math.max(...m.triangles.flat());
    expect(max).toBeLessThan(m.positions.length);
    expect(Math.min(...m.triangles.flat())).toBeGreaterThanOrEqual(0);
  });
  it("rechaza rejillas degeneradas o incoherentes", () => {
    expect(() => gridToMesh({ ...grid, nx: 1 })).toThrow();
    expect(() => gridToMesh({ ...grid, heights: [1, 2, 3] })).toThrow();
  });
});

describe("terrain · localize / elevationRange", () => {
  const m = gridToMesh(grid);
  it("localize resta el origen (coords relativas al proyecto)", () => {
    const l = localize(m, [420200, 4591600, 100]);
    expect(l.positions[0]).toEqual([0, 0, 0]);
    expect(l.triangles).toBe(m.triangles);
  });
  it("elevationRange da min/max de cota", () => {
    expect(elevationRange(m)).toEqual({ min: 100, max: 103 });
  });
});
