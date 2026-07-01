/**
 * Encaje proporcional de una huella W×D dentro de un recuadro — USABILIDAD (puro,
 * sin DOM, golden Llave 1). La planta tipo 2D de la skin Diseño debe CABER en su
 * panel (ancho y alto), no solo ajustar el ancho: una planta muy alargada (D≫W o
 * W≫D) ya no se desborda y tapa la maqueta 3D. Frontera C1: cero.
 */

export interface Box { x: number; y: number; w: number; h: number; }
export interface Fit { fx: number; fy: number; fw: number; fh: number; }

/** Escala W×D para CABER en `box` (limitado por ancho O alto), preserva la
 *  proporción y centra el resultado dentro del recuadro. */
export function fitContain(W: number, D: number, box: Box): Fit {
  const s = Math.min(box.w / Math.max(W, 1e-6), box.h / Math.max(D, 1e-6));
  const fw = W * s, fh = D * s;
  return { fx: box.x + (box.w - fw) / 2, fy: box.y + (box.h - fh) / 2, fw, fh };
}
