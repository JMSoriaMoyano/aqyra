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
import { cambioDeCarrilClotoide, resolverAlineacion } from "./alineacion";
import type { Alineacion, Segmento } from "./alineacion";
import { helixFootprint, DEFAULT_HELIX_RADIUS } from "./parking-helix";

/** Huella del núcleo helicoidal de acceso (o null si no se pidió). Compartida por las
 *  disposiciones: coloca el núcleo y RECORTA las plazas que pisa. */
function coreFoot(p: ParkingParams, ctx: PlanContext): { o: Orient; x: number; y: number; w: number; d: number } | null {
  if (p.core?.kind !== "helix") return null;
  const f = helixFootprint(p.core.side, p.core.radius ?? DEFAULT_HELIX_RADIUS, ctx.W, ctx.D);
  return { o: p.core.side, ...f };
}

/** Huella en planta, en metros. Ejes: X=ancho (0..W), Y=fondo (0..D), N=+Y. */
export interface Footprint { x: number; y: number; w: number; d: number; }

/** Contexto de planta: dimensiones del edificio (X=ancho, Y=fondo) y altura de planta.
 *  `h` (altura piso a piso) es opcional: solo lo usan los generadores que dimensionan
 *  geometría con desnivel (p. ej. la rampa de acceso del parking = rise/pendiente). */
export interface PlanContext { W: number; D: number; h?: number; }

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
const round2 = (n: number): number => Math.round(n * 100) / 100;

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
/**
 * Disposición del aparcamiento. Las dos primeras describen la ORIENTACIÓN DE LA PLAZA
 * con viales transversales (peine clásico); `longitudinal` cambia la DIRECCIÓN DEL VIAL:
 * viales a lo largo del eje largo (Y, N-S), con bandas de plazas en batería a los lados.
 */
export type ParkingDisposition = "bateria" | "linea" | "longitudinal";
export interface ParkingParams {
  bays: number;                 // nº de plazas objetivo por planta (peine); en longitudinal = cap opcional (0/omitir = llenar)
  bay?: { w: number; d: number }; // tamaño físico de plaza (def 2,5 × 5,0 m)
  aisle?: number;               // ancho de vial (def 5,5 m peine · 6,0 longitudinal típico)
  ramps?: Orient[];             // extremos con rampa (p. ej. ["O","E"])
  ramp?: Orient;                // compat: una sola rampa
  disposition?: ParkingDisposition; // batería (90°, def) | línea/cordón (0°) | longitudinal (viales N-S)
  lanes?: number;               // longitudinal: nº de viales deseado (omitir = los que quepan)
  /** NÚCLEO de acceso HELICOIDAL (rampa en hélice) pegado a una fachada. La huella se
   *  coloca aquí (recorta plazas); la directriz helicoidal (Alineacion) la compone
   *  `parking-helix.ts` y se enchufa al canal de alineaciones (igual que los ejes de vial). */
  core?: { kind: "helix"; side: Orient; radius?: number };
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
    if (p.disposition === "longitudinal") return longitudinalParking(p, ctx);
    const out: GeneratedSpace[] = [];
    const stallW = p.bay?.w ?? 2.5, stallD = p.bay?.d ?? 5.0; // físico de la plaza
    const aisle = p.aisle ?? 5.5;
    // En LÍNEA la plaza va girada 90°: el largo (stallD) corre a lo largo del vial y el
    // ancho (stallW) es la profundidad. En BATERÍA al revés. Ambos = rectángulo de ejes.
    const inline = (p.disposition ?? "bateria") === "linea";
    const pitchX = inline ? stallD : stallW;   // paso/anchura de plaza a lo largo de la fila
    const rowDepth = inline ? stallW : stallD; // fondo que ocupa una fila
    const perRow = Math.max(1, Math.floor(W / pitchX));

    // RAMPA DE ACCESO (entre plantas): losa inclinada LOCALIZADA pegada a la fachada
    // pedida (recorrido = desnivel/pendiente), NO una franja a fondo completo. La
    // promueve model.ts a IfcRamp y C1 la autora vía `rampas` (inicio/fin con z). Aquí
    // solo su HUELLA en planta + las plazas que pisa (las consume por solape 2D).
    const ramps = p.ramps ?? (p.ramp ? [p.ramp] : []);
    const RAMP_SLOPE = 0.15;                          // 15% (rampa de vehículos)
    const rise = ctx.h && ctx.h > 0 ? ctx.h : 3;      // desnivel = altura de planta
    const run = round2(rise / RAMP_SLOPE);            // recorrido en planta (m)
    const rampWide = clamp(aisle, 2.5, Math.min(W, D)); // ancho de rampa = vial
    const rampFoots = ramps.map((o) => {
      // el recorrido va hacia la fachada pedida; el ancho, perpendicular y centrado
      if (o.includes("N")) return { o, x: round2((W - rampWide) / 2), y: round2(Math.max(0, D - run)), w: rampWide, d: round2(Math.min(run, D)) };
      if (o.includes("S")) return { o, x: round2((W - rampWide) / 2), y: 0, w: rampWide, d: round2(Math.min(run, D)) };
      if (o.includes("E")) return { o, x: round2(Math.max(0, W - run)), y: round2((D - rampWide) / 2), w: round2(Math.min(run, W)), d: rampWide };
      return { o, x: 0, y: round2((D - rampWide) / 2), w: round2(Math.min(run, W)), d: rampWide }; // O/oeste por defecto
    });
    // núcleo helicoidal de acceso (opt-in): su huella también recorta plazas
    const cf = coreFoot(p, ctx);
    const blockers = [...rampFoots, ...(cf ? [cf] : [])];
    const overlaps = (bx: number, by: number, bw: number, bd: number): boolean =>
      blockers.some((r) => bx < r.x + r.w - 1e-6 && bx + bw > r.x + 1e-6 && by < r.y + r.d - 1e-6 && by + bd > r.y + 1e-6);

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
        const x0 = i * pitchX;
        if (overlaps(x0, y, pitchX, rowDepth)) continue; // plaza pisada por la rampa
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
    for (const r of rampFoots) {
      out.push({
        objectType: "Rampa", longName: `Rampa de acceso ${r.o}`, zone: "circulacion", sideTag: r.o,
        footprint: { x: r.x, y: r.y, w: r.w, d: r.d },
      });
    }
    if (cf) out.push({
      objectType: "NucleoRampa", longName: `Núcleo de rampa helicoidal ${cf.o}`, zone: "circulacion", sideTag: cf.o,
      footprint: { x: cf.x, y: cf.y, w: cf.w, d: cf.d },
    });
    return out;
  },
};

// ── Disposición LONGITUDINAL (P1·B · "parking desde la circulación", paso A→B) ──
// Viales a lo largo del eje largo (Y, N-S), ancho `aisle`; plazas en BATERÍA en bandas
// a los lados (perpendiculares al vial). Sección en X: banda de borde · vial · banda
// DOBLE (espalda contra espalda) · vial · … · banda de borde. El generador es la
// AUTORIDAD geométrica: coloca los viales que CABEN (o los `lanes` pedidos) y llena las
// bandas; el self-check del visor reporta lo realmente colocado. Determinista.

interface ParkLayout { lanes: { x0: number; cx: number }[]; cols: { x: number; w: number }[]; aisle: number; bayY: number; }

/** Reparto transversal compartido por plazas y ejes (misma verdad geométrica). */
function parkingLayout(p: ParkingParams, ctx: PlanContext): ParkLayout {
  const { W } = ctx;
  const bayDepth = p.bay?.d ?? 5.0;   // profundidad de plaza (X, hacia el vial)
  const bayY = p.bay?.w ?? 2.5;       // anchura de plaza (Y, a lo largo del vial)
  const aisle = p.aisle ?? 6.0;
  const minBand = 2.3;                // banda mínima utilizable (m)
  const maxLanes = p.lanes && p.lanes > 0 ? p.lanes : Infinity;
  const eps = 1e-6;
  const lanes: { x0: number; cx: number }[] = [];
  const bandRanges: [number, number][] = [];
  let x = Math.min(bayDepth, W);
  if (x >= minBand) bandRanges.push([0, x]);                       // banda de borde inicial
  while (lanes.length < maxLanes && x + aisle <= W + eps) {
    lanes.push({ x0: round2(x), cx: round2(x + aisle / 2) });      // vial
    x += aisle;
    const rem = W - x;
    if (rem <= eps) break;
    if (lanes.length < maxLanes && rem >= 2 * bayDepth + aisle) {
      bandRanges.push([x, x + 2 * bayDepth]); x += 2 * bayDepth;   // banda doble interior
    } else {
      if (Math.min(rem, bayDepth) >= minBand) bandRanges.push([x, x + Math.min(rem, bayDepth)]); // borde final
      break;
    }
  }
  const cols: { x: number; w: number }[] = [];                     // columnas de plaza
  for (const [a, b] of bandRanges) {
    let cx = a;
    while (b - cx >= minBand) { const w = Math.min(bayDepth, b - cx); cols.push({ x: round2(cx), w: round2(w) }); cx += w; }
  }
  return { lanes, cols, aisle, bayY };
}

/** Plazas + viales longitudinales (+ rampa de acceso). El layout DESCUENTA las plazas que
 *  pisa la circulación (clotoides de entrada/salida, giro de 180°) y el hueco de rampa al N
 *  del atraque → el recuento refleja la ocupación real. `dockY` = cota de atraque del nivel
 *  (P1 por defecto; en niveles superiores baja, ver parkingDockY). Determinista → golden-able. */
function longitudinalParking(p: ParkingParams, ctx: PlanContext, dockY?: number): GeneratedSpace[] {
  const { W, D } = ctx;
  const { lanes, cols, aisle, bayY } = parkingLayout(p, ctx);
  const out: GeneratedSpace[] = [];
  // RAMPA de acceso: franja en la fachada pedida (recorrido = desnivel/pendiente); recorta plazas.
  const ramps = p.ramps ?? (p.ramp ? [p.ramp] : []);
  const rampN = ramps.some((o) => o.includes("N"));
  const rise = ctx.h && ctx.h > 0 ? ctx.h : 3;
  const run = round2(rise / 0.15);
  const rampWide = clamp(aisle, 2.5, Math.min(W, D));
  const rampFoots = ramps.map((o) => {
    if (o.includes("N")) return { o, x: round2((W - rampWide) / 2), y: round2(Math.max(0, D - run)), w: rampWide, d: round2(Math.min(run, D)) };
    if (o.includes("S")) return { o, x: round2((W - rampWide) / 2), y: 0, w: rampWide, d: round2(Math.min(run, D)) };
    if (o.includes("E")) return { o, x: round2(Math.max(0, W - run)), y: round2((D - rampWide) / 2), w: round2(Math.min(run, W)), d: rampWide };
    return { o, x: 0, y: round2((D - rampWide) / 2), w: round2(Math.min(run, W)), d: rampWide };
  });
  const cf = coreFoot(p, ctx); // núcleo helicoidal de acceso (opt-in): recorta plazas
  const blockers = [...rampFoots, ...(cf ? [cf] : [])];
  const overlaps = (bx: number, by: number, bw: number, bd: number): boolean =>
    blockers.some((r) => bx < r.x + r.w - 1e-6 && bx + bw > r.x + 1e-6 && by < r.y + r.d - 1e-6 && by + bd > r.y + 1e-6);
  // ÁREA DE GIRO (apron) al fondo S: con ≥2 viales la circulación gira 180° al final
  // (S), así que ese fondo NO puede llevar plazas. Se deja libre una franja de
  // apronClear = R + holgura, con R = media separación entre viales (el radio del giro).
  const TURN_APRON = 1.0;
  const turnR = lanes.length >= 2 ? round2((lanes[1].cx - lanes[0].cx) / 2) : 0;
  const apronClear = turnR > 0 ? round2(turnR + TURN_APRON) : 0;
  // ATRAQUE del nivel: al N de él está la rampa (o el hueco de rampas en niveles altos),
  // así que no lleva plazas. P1 = D − recorrido; niveles superiores, dockY explícito.
  const dock = dockY ?? (rampN ? round2(D - run) : D);
  // OCUPACIÓN DE LA CIRCULACIÓN: la trayectoria (clotoides de entrada/salida + giro de
  // 180°) barre área que NO puede llevar plazas. Se descuenta toda plaza a < medio carril
  // de la directriz. Los tramos rectos van por los viales (ya sin plazas); descuenta de
  // verdad las CURVAS (clotoides al N, giro al S) que invaden las bandas.
  const trajPts: [number, number][] = [];
  for (const tr of parkingTrajectories(p, ctx, TURN_APRON, undefined, dockY)) {
    for (const q of resolverAlineacion(tr, 1).puntos) trajPts.push(q);
  }
  const clearHalf = aisle / 2;
  const onTraj = (cx: number, cy: number, hw: number, hd: number): boolean =>
    trajPts.some(([tx, ty]) => {
      const dx = Math.max(Math.abs(tx - cx) - hw, 0), dy = Math.max(Math.abs(ty - cy) - hd, 0);
      return dx * dx + dy * dy < clearHalf * clearHalf - 1e-9;
    });
  // PLAZAS: cada columna se llena a lo largo de Y (paso bayY)
  const nY = Math.floor(D / bayY);
  const cap = p.bays && p.bays > 0 ? p.bays : Infinity;
  let placed = 0;
  cols.forEach((c, ci) => {
    for (let k = 0; k < nY && placed < cap; k++) {
      const y = round2(k * bayY);
      if (y + bayY > dock + 1e-6) continue;             // al N del atraque: rampa / hueco de rampas
      if (y < apronClear - 1e-6) continue;              // fondo S libre para el giro
      if (overlaps(c.x, y, c.w, bayY)) continue;        // rampa de acceso
      if (onTraj(c.x + c.w / 2, y + bayY / 2, c.w / 2, bayY / 2)) continue; // pisada por la circulación
      out.push({
        objectType: "PlazaAparcamiento", longName: "Plaza de aparcamiento",
        zone: "aparcamiento", numbered: true, sideTag: `C${ci + 1}`,
        footprint: { x: c.x, y, w: c.w, d: bayY },
      });
      placed++;
    }
  });
  // VIALES longitudinales a fondo completo; un SENTIDO por vial (alterno)
  lanes.forEach((ln, i) => {
    const haciaN = i % 2 === 0;
    out.push({
      objectType: "Vial", longName: `Vial de circulación (sentido ${haciaN ? "S→N" : "N→S"})`,
      zone: "circulacion", sideTag: `V${i + 1}-${haciaN ? "N" : "S"}`,
      footprint: { x: ln.x0, y: 0, w: aisle, d: D },
    });
  });
  for (const r of rampFoots) out.push({
    objectType: "Rampa", longName: `Rampa de acceso ${r.o}`, zone: "circulacion", sideTag: r.o,
    footprint: { x: r.x, y: r.y, w: r.w, d: r.d },
  });
  if (cf) out.push({
    objectType: "NucleoRampa", longName: `Núcleo de rampa helicoidal ${cf.o}`, zone: "circulacion", sideTag: cf.o,
    footprint: { x: cf.x, y: cf.y, w: cf.w, d: cf.d },
  });
  return out;
}

/** Ejes de los viales longitudinales como ALINEACIONES (recta N-S; el sentido único va
 *  en el acimut). EL PUENTE HACIA B: el vial es un IfcAlignment, no una franja "tonta". */
export function parkingAxes(p: ParkingParams, ctx: PlanContext): Alineacion[] {
  if (p.disposition !== "longitudinal") return [];
  const { D } = ctx;
  const { lanes, aisle } = parkingLayout(p, ctx);
  return lanes.map((ln, i) => {
    const haciaN = i % 2 === 0;
    return {
      nombre: `Eje vial ${i + 1}`,
      infraestructura: { clase: "IfcRoad", nombre: "Vial de circulación" },
      ancho_ref: aisle,
      inicio: haciaN
        ? { x: ln.cx, y: 0, acimut_deg: 90, cota: 0 }   // S→N (hacia +Y/Norte)
        : { x: ln.cx, y: round2(D), acimut_deg: 270, cota: 0 }, // N→S (hacia −Y/Sur)
      planta: [{ tipo: "recta", longitud: round2(D) }],
    };
  });
}

/**
 * TRAYECTORIA(S) de circulación del parking longitudinal como ALINEACIÓN: el coche BAJA
 * por el vial E (N→S), GIRA 180° al fondo (S) y SUBE por el vial O contiguo (S→N) —
 * circulación por la derecha del conductor, un sentido por vial. El RADIO del giro = media
 * separación entre ejes de vial, así el ARCO define el giro con PRECISIÓN (lo que un
 * IfcSpace rectangular no puede). Vehículo ligero: el self-check de radios compara ese
 * radio con el mínimo de giro (parametrizable). `apron` = holgura del giro al fondo (m),
 * = distancia del vértice del giro a la fachada S. Determinista → golden-able.
 */
export function parkingTrajectories(p: ParkingParams, ctx: PlanContext, apron = 1.0, transRadio?: number, dockY?: number): Alineacion[] {
  if (p.disposition !== "longitudinal") return [];
  const { W, D } = ctx;
  const { lanes } = parkingLayout(p, ctx);     // ordenados por x ascendente (O…E)
  const out: Alineacion[] = [];
  const rampN = (p.ramps ?? (p.ramp ? [p.ramp] : [])).some((o) => o.includes("N"));
  const ramRun = round2((ctx.h && ctx.h > 0 ? ctx.h : 3) / 0.15); // recorrido en planta de la rampa
  // Cota de ATRAQUE de este nivel (extremo alto de SU rampa). P1 = D − recorrido; en
  // niveles superiores la rampa TELESCOPA hacia el S (libre de las clotoides del nivel
  // inferior), así que el atraque baja: dockY se pasa explícito (ver parkingDockY).
  for (let i = 0; i + 1 < lanes.length; i += 2) {
    const xO = lanes[i].cx, xE = lanes[i + 1].cx;  // i = menor x (Oeste), i+1 = mayor x (Este)
    const R = round2((xE - xO) / 2);
    const yT = round2(R + apron);                  // estación del giro (vértice = apron al S)
    const planta: Segmento[] = [];
    const ramp = rampN && i === 0;
    const rampX = round2(W / 2);                     // eje de la rampa (centrada)
    const desY = dockY ?? round2(D - ramRun);        // extremo ALTO de la rampa que atraca en este nivel
    const Rt = transRadio ?? R;                      // radio mínimo de las transiciones (paramétrico)
    // ENTRADA: el coche atraca P1 por el EXTREMO ALTO de la rampa (no la fachada/PB), rodando
    // según el EJE de la rampa, que aquí es PARALELO a los viales (N-S). Pasar de la rampa al
    // vial E es un CAMBIO DE CARRIL entre alineaciones paralelas → CLOTOIDES, no un giro. Sin
    // rampa N, la trayectoria arranca directamente en el vial E (compat. anterior).
    let inicio = { x: xE, y: round2(D), acimut_deg: 270, cota: 0 }; // por defecto: en el vial E, hacia S
    let yTopE = D;                                   // estación donde la trayectoria llega al vial E
    const latEnt = round2(xE - rampX);               // desfase rampa→vial E (+ = a la izquierda del rumbo S)
    if (ramp && Math.abs(latEnt) > 0.1) {
      const t = cambioDeCarrilClotoide(270, latEnt, Rt); // S de 4 clotoides; sale rumbo S sobre el vial E
      inicio = { x: rampX, y: desY, acimut_deg: 270, cota: 0 };
      planta.push(...t.segmentos);
      yTopE = round2(desY + t.fin.y);                // donde la entrada aterriza en el vial E
    } else if (ramp) {
      inicio = { x: xE, y: desY, acimut_deg: 270, cota: 0 };
      yTopE = desY;
    }
    planta.push({ tipo: "recta", longitud: round2(yTopE - yT) });   // baja por el vial E (N→S)
    planta.push({ tipo: "curva", longitud: Math.PI * R, radio: -R }); // GIRO 180° a derechas al fondo (S)
    // SALIDA: sube por el vial O y, si hay rampa, vuelve a la rampa con OTRO cambio de carril
    // de clotoides (rumbo N), para SALIR de P1 por el mismo extremo alto. Simétrico a la
    // entrada (el desfase O↔rampa puede diferir del rampa↔E: la rampa no equidista).
    const latSal = round2(-(rampX - xO));            // desfase vial O→rampa (a la derecha del rumbo N)
    if (ramp && Math.abs(latSal) > 0.1) {
      const tEx = cambioDeCarrilClotoide(90, latSal, Rt); // sube hacia N y cambia de carril a la rampa
      const yExitStart = round2(desY - tEx.fin.y);   // estación del vial O donde arranca la salida
      planta.push({ tipo: "recta", longitud: round2(yExitStart - yT) }); // sube O hasta el inicio de la salida
      planta.push(...tEx.segmentos);                 // O→rampa: sale por la rampa rumbo N
    } else {
      planta.push({ tipo: "recta", longitud: round2(D - yT) });      // sube por el vial O hasta N
    }
    out.push({
      nombre: `Trayectoria circulación ${i / 2 + 1}`,
      infraestructura: { clase: "IfcRoad", nombre: "Circulación de vehículos ligeros" },
      ancho_ref: p.aisle ?? 6,
      inicio,
      planta,
    });
  }
  return out;
}

/**
 * Cota de ATRAQUE (extremo alto de la rampa) del nivel `nivel` (1 = P1, 2 = P2, …). Las
 * rampas TELESCOPAN hacia el S: cada nivel se separa del inferior por el RECORRIDO de la
 * rampa + la OCUPACIÓN de la clotoide de entrada del nivel inferior, de modo que la rampa
 * del nivel superior ARRANCA LIBRE de las transiciones del nivel de abajo (no las pisa).
 * El INICIO de la rampa que sube a `nivel` queda en y = dock(nivel) + recorrido. Determinista.
 */
export function parkingDockY(nivel: number, p: ParkingParams, ctx: PlanContext, transRadio?: number): number {
  const { W, D } = ctx;
  const ramRun = round2((ctx.h && ctx.h > 0 ? ctx.h : 3) / 0.15);
  const { lanes } = parkingLayout(p, ctx);
  if (lanes.length < 2) return round2(D - ramRun);
  const xO = lanes[0].cx, xE = lanes[1].cx;
  const Rt = transRadio ?? round2((xE - xO) / 2);
  const occup = Math.abs(cambioDeCarrilClotoide(270, round2(xE - W / 2), Rt).fin.y); // avance N-S de la entrada
  let dock = D - ramRun;                                  // P1
  for (let k = 2; k <= nivel; k++) dock -= occup + ramRun; // cada nivel telescopa al S
  return round2(dock);
}

/** Registro de generadores (id → generador). Inc 2: enchufar tipologías sin tocar el núcleo. */
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export const GENERATORS: Record<string, DistributionGenerator<any>> = {
  [residenceGenerator.id]: residenceGenerator,
  [parkingGenerator.id]: parkingGenerator,
};
