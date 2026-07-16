/** Cableado del dock/herramientas del chrome a capacidades EXISTENTES del visor (D-CH-3,
 *  F2.2 · cableado conservador). Helper PURO (sin React, sin wasm): construye el mapa
 *  expressId→color que consumen `Viewer.setCostHeatmap` / `Viewer.setCumplimientoColors`.
 *  Testeable headless (vitest en Node). */

export type ColorRGB = { r: number; g: number; b: number };

/** A partir de un mapa `globalId → dato` del elemento (p. ej. coste o cumplimiento) y del índice
 *  `globalId → expressId` del modelo abierto, produce el mapa `expressId → color` aplicando
 *  `color(dato)`. Solo incluye los elementos cuyo globalId existe en el modelo (ignora
 *  asignaciones a GUIDs ausentes; determinista). */
export function mapaColorPorElemento<T>(
  porElemento: ReadonlyMap<string, T>,
  exprPorGuid: ReadonlyMap<string, number>,
  color: (dato: T) => ColorRGB,
): Map<number, ColorRGB> {
  const out = new Map<number, ColorRGB>();
  for (const [guid, dato] of porElemento) {
    const ex = exprPorGuid.get(guid);
    if (ex !== undefined) out.set(ex, color(dato));
  }
  return out;
}
