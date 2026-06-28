/**
 * Generadores de distribución (P1·B·2, Inc 1 — base genérica).
 *
 * El conocimiento de tipología deja de estar incrustado en el modelo/render y se
 * aísla aquí: un GENERADOR recibe parámetros y el rectángulo de planta del edificio
 * y devuelve ESPACIOS COLOCADOS (footprints en metros). Render, árbol y autoría
 * operan sobre esos footprints genéricos, da igual la tipología.
 *
 * Determinismo: misma entrada → mismos footprints (verificable con golden por
 * generador). La residencia-pasillo es el generador nº1; los siguientes (parking,
 * aulario…) se enchufan sin tocar el núcleo.
 */

import type { Orient } from "./model";

/** Huella en planta, en metros. Ejes: X=ancho (0..W), Y=fondo (0..D), N=+Y. */
export interface Footprint { x: number; y: number; w: number; d: number; }

/** Contexto de planta: dimensiones del edificio (X=ancho, Y=fondo). */
export interface PlanContext { W: number; D: number; }

/** Un espacio colocado por un generador (aún sin código IFC; lo pone el modelo). */
export interface GeneratedSpace {
  objectType: string;            // dato: Habitacion | Pasillo | Nucleo | PlazaAparcamiento | …
  longName: string;
  zone: string;                  // nombre de uso → IfcZone (genérico): privado|comunes|aparcamiento|…
  footprint: Footprint;
  sideTag?: string;              // IZQ|DER | orientación | fila (Fn)
  numbered?: boolean;            // si el código lleva secuencia (mm)
}

/** Interfaz de generador: params + contexto → espacios colocados. */
export interface DistributionGenerator<P> {
  id: string;
  generate(params: P, ctx: PlanContext): GeneratedSpace[];
}

// ── parámetros de la residencia-pasillo (= la "planta tipo" del diálogo) ──────
export interface ResidenceParams {
  rooms: { count: number; layout: "both-sides" | "single-side" } | null;
  corridor: { width: number } | null;
  cores: { orientation: Orient; detail?: string }[];
}

const fmtM = (m: number): string => m.toFixed(2).replace(".", ",");
const clamp = (x: number, lo: number, hi: number): number => Math.max(lo, Math.min(hi, x));

/**
 * Generador nº1: habitaciones a uno o ambos lados de un pasillo central que corre
 * por el eje largo (X), con núcleos en sus esquinas según orientación.
 */
export const residenceGenerator: DistributionGenerator<ResidenceParams> = {
  id: "residence-corridor",
  generate(p, ctx): GeneratedSpace[] {
    const { W, D } = ctx;
    const out: GeneratedSpace[] = [];

    // banda de pasillo centrada en Y (acotada para no comerse las habitaciones)
    const cw = p.corridor ? clamp(p.corridor.width, 0.6, D * 0.6) : 0;
    const cy0 = (D - cw) / 2;       // borde sur del pasillo
    const cy1 = (D + cw) / 2;       // borde norte del pasillo

    // habitaciones: fila norte (IZQ) y fila sur (DER)
    if (p.rooms && p.rooms.count > 0) {
      const both = p.rooms.layout === "both-sides";
      const total = p.rooms.count;
      const nTop = both ? Math.ceil(total / 2) : total;
      const nBot = both ? total - nTop : 0;
      const row = (n: number, y0: number, depth: number, side: "IZQ" | "DER"): void => {
        if (n <= 0 || depth <= 0) return;
        const rw = W / n;
        for (let i = 0; i < n; i++) {
          out.push({
            objectType: "Habitacion", longName: "Habitación", zone: "privado",
            sideTag: side, numbered: true,
            footprint: { x: i * rw, y: y0, w: rw, d: depth },
          });
        }
      };
      if (both) {
        row(nTop, cy1, D - cy1, "IZQ");
        row(nBot, 0, cy0, "DER");
      } else {
        row(total, 0, D, "IZQ");
      }
    }

    // pasillo
    if (p.corridor) {
      out.push({
        objectType: "Pasillo", longName: `Pasillo (${fmtM(p.corridor.width)} m)`,
        zone: "comunes", footprint: { x: 0, y: cy0, w: W, d: cw },
      });
    }

    // núcleos: caja en la esquina/borde según orientación (N=+Y, E=+X)
    for (const c of p.cores) {
      const kw = W * 0.17, kd = D * 0.5;
      const o = c.orientation;
      const x = o.includes("E") ? W - kw : o.includes("O") ? 0 : (W - kw) / 2;
      const y = o.includes("N") ? D - kd : o.includes("S") ? 0 : (D - kd) / 2;
      out.push({
        objectType: "Nucleo",
        longName: `Núcleo ${o}${c.detail ? " · " + c.detail : ""}`,
        zone: "comunes", sideTag: o,
        footprint: { x, y, w: kw, d: kd },
      });
    }

    return out;
  },
};

// ── generador nº2: parking en peine (prueba de extensibilidad, Inc 2) ─────────
/** Disposición de la plaza respecto al vial. */
export type ParkingDisposition = "bateria" | "linea";
export interface ParkingParams {
  bays: number;                 // nº de plazas objetivo por planta
  bay?: { w: number; d: number }; // tamaño físico de plaza (def 2,5 × 5,0 m)
  aisle?: number;               // ancho de vial entre filas (def 5,5 m)
  ramps?: Orient[];             // extremos con rampa (p. ej. ["O","E"])
  ramp?: Orient;                // compat: una sola rampa
  disposition?: ParkingDisposition; // batería (90°, def) | línea/cordón (0°)
}

/**
 * Plazas en peine: filas perpendiculares separadas por viales. El GENERADOR es la
 * autoridad geométrica (decisión JM): coloca una RAMPA por cada extremo pedido (una
 * franja a fondo completo) y RECORTA las plazas que solapan cada rampa. Así "rampas
 * en los dos extremos eliminando plazas" ocurre de verdad en la geometría, no en la
 * narración. Determinista → golden-able.
 *
 * DISPOSICIÓN (P1·B, profundización): la MISMA plaza física se coloca en BATERÍA
 * (perpendicular al vial: largo en profundidad) o en LÍNEA/cordón (paralela al vial:
 * el rectángulo girado 90°, largo a lo largo del vial — SIGUE alineado a ejes). De esa
 * orientación salen el paso a lo largo de la fila (pitchX) y el fondo de la fila
 * (rowDepth); el footprint sigue siendo {x,y,w,d}, sin tocar el núcleo. La oblicua
 * (45°/60°) NO entra aquí: exige footprint girado → incremento de núcleo aparte.
 */
export const parkingGenerator: DistributionGenerator<ParkingParams> = {
  id: "parking-comb",
  generate(p, ctx): GeneratedSpace[] {
    const { W, D } = ctx;
    const out: GeneratedSpace[] = [];
    const stallW = p.bay?.w ?? 2.5, stallD = p.bay?.d ?? 5.0; // físico de la plaza
    const aisle = p.aisle ?? 5.5;
    // En LÍNEA la plaza va girada 90°: el largo (stallD) corre a lo largo del vial y el
    // ancho (stallW) es la profundidad. En BATERÍA al revés. Ambos = rectángulo de ejes.
    const inline = (p.disposition ?? "bateria") === "linea";
    const pitchX = inline ? stallD : stallW;   // paso/anchura de plaza a lo largo de la fila
    const rowDepth = inline ? stallW : stallD; // fondo que ocupa una fila
    const perRow = Math.max(1, Math.floor(W / pitchX));

    // rampas: franja vertical (a fondo completo) en cada extremo pedido
    const ramps = p.ramps ?? (p.ramp ? [p.ramp] : []);
    const rampW = clamp(pitchX * 2, 0, W / 2);
    const rampBands = ramps.map((o) => {
      const x0 = o.includes("E") ? W - rampW : o.includes("O") ? 0 : (W - rampW) / 2;
      return { o, x0, x1: x0 + rampW };
    });
    const inRamp = (x0: number, x1: number): boolean =>
      rampBands.some((r) => x0 < r.x1 - 1e-6 && x1 > r.x0 + 1e-6);

    // nº de FILAS que caben en el fondo: n·rowDepth + (n-1)·aisle ≤ D (doble fila = 2
    // filas compartiendo un vial central). Se centra el conjunto y NO se dejan viales
    // colgando.
    let rows = Math.floor((D + aisle) / (rowDepth + aisle));
    if (rows < 1 && D >= rowDepth) rows = 1;
    const used = rows > 0 ? rows * rowDepth + (rows - 1) * aisle : 0;
    const y0 = Math.max(0, (D - used) / 2);

    let placed = 0;
    for (let r = 0; r < rows && placed < p.bays; r++) {
      const y = y0 + r * (rowDepth + aisle);
      for (let i = 0; i < perRow && placed < p.bays; i++) {
        const x0 = i * pitchX, x1 = x0 + pitchX;
        if (inRamp(x0, x1)) continue; // hueco reservado para la rampa
        out.push({
          objectType: "PlazaAparcamiento", longName: "Plaza de aparcamiento",
          zone: "aparcamiento", numbered: true, sideTag: `F${r + 1}`,
          footprint: { x: x0, y, w: pitchX, d: rowDepth },
        });
        placed++;
      }
    }
    // viales SOLO entre filas (uno por cada par de filas contiguas)
    for (let r = 0; r < rows - 1; r++) {
      out.push({
        objectType: "Vial", longName: "Vial de circulación", zone: "circulacion",
        footprint: { x: 0, y: y0 + r * (rowDepth + aisle) + rowDepth, w: W, d: aisle },
      });
    }
    for (const r of rampBands) {
      out.push({
        objectType: "Rampa", longName: `Rampa ${r.o}`, zone: "circulacion", sideTag: r.o,
        footprint: { x: r.x0, y: 0, w: r.x1 - r.x0, d: D },
      });
    }
    return out;
  },
};

/** Registro de generadores (id → generador). Inc 2: enchufar tipologías sin tocar el núcleo. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const GENERATORS: Record<string, DistributionGenerator<any>> = {
  [residenceGenerator.id]: residenceGenerator,
  [parkingGenerator.id]: parkingGenerator,
};
