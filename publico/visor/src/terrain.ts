/**
 * Terreno triangulado (P1·A) — TIN a partir de una rejilla regular de cotas.
 *
 * Módulo PURO (sin web-ifc, sin DOM, con golden). Convierte una malla regular de
 * alturas (muestreada del MDT del ICGC sobre el bbox de la parcela) en una malla
 * triangulada lista para: (a) verse en 3D en el visor, y (b) autorarse a IFC como
 * IfcTriangulatedFaceSet (ver author.ts). La cota Z es ortométrica (m).
 *
 * Decisión de JM (2026-06-27): "ambos" — malla visual ahora + camino a IFC luego
 * (con golden y firma). El volcado a IFC revisita la decisión 2 (entorno→IFC).
 */

/** Rejilla regular de cotas. heights va por filas: índice = j*nx + i (i en E, j en N). */
export interface TerrainGrid {
  nx: number;
  ny: number;
  /** Esquina (E,N) del primer punto (i=0, j=0), en el CRS del proyecto (p. ej. EPSG:25831). */
  originE: number;
  originN: number;
  /** Paso de la rejilla en metros. */
  dx: number;
  dy: number;
  /** Cotas ortométricas (m), nx*ny valores. */
  heights: number[];
}

/** Malla triangulada: vértices [E,N,Z] y triángulos por índices 0-based. */
export interface TerrainMesh {
  positions: number[][];
  triangles: number[][];
}

/**
 * Triangula una rejilla regular: 2 triángulos por celda. Devuelve vértices en el
 * mismo CRS de la rejilla (E,N,Z absolutos). Para el IFC se localizan luego
 * (restando el origen del MapConversion) — ver author.ts.
 */
export function gridToMesh(g: TerrainGrid): TerrainMesh {
  if (g.nx < 2 || g.ny < 2) throw new Error("La rejilla necesita al menos 2×2 puntos.");
  if (g.heights.length !== g.nx * g.ny) throw new Error("heights no casa con nx*ny.");
  const positions: number[][] = [];
  for (let j = 0; j < g.ny; j++) {
    for (let i = 0; i < g.nx; i++) {
      positions.push([g.originE + i * g.dx, g.originN + j * g.dy, g.heights[j * g.nx + i]]);
    }
  }
  const idx = (i: number, j: number) => j * g.nx + i;
  const triangles: number[][] = [];
  for (let j = 0; j < g.ny - 1; j++) {
    for (let i = 0; i < g.nx - 1; i++) {
      const a = idx(i, j), b = idx(i + 1, j), c = idx(i + 1, j + 1), d = idx(i, j + 1);
      triangles.push([a, b, c], [a, c, d]);
    }
  }
  return { positions, triangles };
}

/** Traslada los vértices a coordenadas LOCALES (resta un origen). Para el IFC: el
 *  origen es (eastings, northings, orthogonalHeight) del MapConversion, de modo que
 *  el terreno queda centrado cerca del origen del proyecto y la georreferencia lo
 *  sitúa en el mapa. Devuelve una malla nueva (no muta la entrada). */
export function localize(mesh: TerrainMesh, origin: [number, number, number]): TerrainMesh {
  const [ox, oy, oz] = origin;
  return {
    positions: mesh.positions.map(([x, y, z]) => [x - ox, y - oy, z - oz]),
    triangles: mesh.triangles,
  };
}

/** Rango de cotas (min/max Z) — útil para encuadre y para informar la pendiente. */
export function elevationRange(mesh: TerrainMesh): { min: number; max: number } {
  let min = Infinity, max = -Infinity;
  for (const p of mesh.positions) { if (p[2] < min) min = p[2]; if (p[2] > max) max = p[2]; }
  return { min, max };
}
