/**
 * NÚCLEO DE RAMPA HELICOIDAL del parking — el PUENTE entre dos capacidades que ya
 * existen por separado: el PARKING (`generators.ts`) y la HÉLICE de la familia de
 * TRAZADO (`alineacion.ts`, alzado helicoidal). Aquí NO se inventa geometría nueva:
 * se COMPONE una `Alineacion` cuyo plano es un ARCO (radio R) y cuyo alzado es una
 * RAMPA de pendiente constante → al integrarse (resolverAlineacion) sube como una
 * hélice. Una vuelta por salto de planta. Determinista → golden-able. No toca
 * `alineacion.ts` (solo consume sus tipos); C1 la compila por `alineaciones[]`
 * (frontera-cero, C1 0.10.0 ya monta el alzado helicoidal).
 */

import type { Orient } from "./model";
import type { Footprint } from "./generators";
import type { Alineacion } from "./alineacion";

/** Radio de la directriz (centerline) por defecto (m): vuelta cómoda de vehículo. */
export const DEFAULT_HELIX_RADIUS = 6;
/** Ancho de la calzada de la rampa (m): la deja un swept de R±ancho/2 → huella = bbox. */
export const HELIX_LANE = 6;

/** Centro del círculo de la hélice, pegado a la fachada `side` (margen = radio exterior). */
function helixCenter(side: Orient, radius: number, W: number, D: number): [number, number] {
  const outer = radius + HELIX_LANE / 2;          // radio exterior de la calzada
  const cx = side.includes("E") ? W - outer : side.includes("O") ? outer : W / 2;
  const cy = side.includes("N") ? D - outer : side.includes("S") ? outer : D / 2;
  return [round2(cx), round2(cy)];
}

/** Huella en planta (bbox cuadrado del círculo exterior) del núcleo helicoidal. La usa
 *  el generador para colocar el núcleo y RECORTAR las plazas que pisa, y el modelo para
 *  perforar los forjados. Misma derivación de centro que la Alineación → coherencia. */
export function helixFootprint(side: Orient, radius: number, W: number, D: number): Footprint {
  const outer = radius + HELIX_LANE / 2;
  const [cx, cy] = helixCenter(side, radius, W, D);
  return { x: round2(cx - outer), y: round2(cy - outer), w: round2(2 * outer), d: round2(2 * outer) };
}

/**
 * Compone la `Alineacion` helicoidal: arco en planta (radio R, CCW) + alzado en rampa
 * de pendiente constante, una VUELTA por salto de planta (n-1 saltos suben de PB al
 * último nivel). Arranca en (cx+R, cy) tangente a +Y (acimut 90°), cota 0.
 *  · rise = (NF-1)·FF   (desnivel total que cubre la hélice)
 *  · turns = NF-1       (una vuelta por planta)
 *  · L = turns·2πR      (longitud en planta)  ·  pendiente = rise/L
 */
export function helixAlineacion(side: Orient, radius: number, W: number, D: number, NF: number, FF: number, name: string): Alineacion {
  const turns = Math.max(1, NF - 1);
  const rise = round3(turns * FF);
  const L = round3(turns * 2 * Math.PI * radius);
  const slope = round3(rise / L);
  const [cx, cy] = helixCenter(side, radius, W, D);
  return {
    nombre: name,
    infraestructura: { clase: "IfcRamp", nombre: "Núcleo de rampa helicoidal" },
    ancho_ref: HELIX_LANE,
    inicio: { x: round3(cx + radius), y: round3(cy), acimut_deg: 90, cota: 0 },
    planta: [{ tipo: "curva", longitud: L, radio: radius }],
    alzado: [{ tipo: "rampa", longitud: L, pendiente_ini: slope, pendiente_fin: slope }],
  };
}

const round2 = (n: number): number => Math.round(n * 100) / 100;
const round3 = (n: number): number => Math.round(n * 1000) / 1000;
