/**
 * Modelo de INSTANCIAS de la estructura espacial (P1·B·2, Inc 1 — base genérica).
 *
 * FUENTE DE VERDAD del árbol y del render: a partir de (nº de plantas × planta tipo)
 * genera, de forma DETERMINISTA, cada IfcBuildingStorey y cada IfcSpace con su
 * FOOTPRINT real, y las IfcZone. El dominio (habitación/pasillo/núcleo) ya NO vive
 * aquí: lo aporta un GENERADOR de distribución (generators.ts). El modelo solo
 * coloca, nombra y agrupa lo que el generador produce → vale para cualquier tipología.
 *
 * Nomenclatura (extiende la del golden incr. 1), derivada del objectType:
 *   IfcBuildingStorey → AQ-NIV-Pnn
 *   IfcSpace          → AQ-ESP-<ABBR>-Pnn[-<sideTag>][-mm]
 *                       (Habitacion→HAB, Pasillo→PAS, Nucleo→NUC; default = 3 letras)
 *   IfcZone           → AQ-ZON-{PRI|COM}
 */

import { residenceGenerator, GENERATORS, type Footprint, type PlanContext } from "./generators";

export type Orient = "N" | "S" | "E" | "O" | "NE" | "NO" | "SE" | "SO";

export interface SpaceInstance {
  code: string;
  ifcClass: "IfcSpace";
  objectType: string;          // dato: Habitacion | Pasillo | Nucleo | PlazaAparcamiento | …
  longName: string;
  footprint: Footprint;
  zone: string;                // nombre de uso → IfcZone (genérico)
  sideTag?: string;            // IZQ|DER | orientación | fila
}

// ── Capa de ELEMENTOS físicos (IfcElement) — Inc núcleo, primer slice ─────────
// Identidad = DATO, no código: UN ElementInstance genérico respaldado por el
// catálogo de C1 (no una batería de generadores). El cebo aporta identidad ligera
// (clase + colocación + sección + clasificación); C1 autora la geometría real.

/** Colocación de un elemento (m): punto (pilar), polígono (forjado) o línea (muro). */
export type Placement =
  | { kind: "point"; x: number; y: number }
  | { kind: "polygon"; contour: [number, number][] }
  | { kind: "line"; start: [number, number]; end: [number, number] };

/** Sección rectangular de pilar (m). Default C1: 0,40 × 0,40. */
export interface ColumnSection { w: number; d: number; }

export interface ElementInstance {
  code: string;                // AQ-PIL-Pnn-<eje>  (AQ-PUE-… | AQ-LAV-… en clones futuros)
  ifcClass: string;            // del catálogo C1 (dato): IfcColumn | IfcWall | …
  objectType: string;          // etiqueta de uso: Pilar | …
  predefinedType?: string;     // PredefinedType IFC (IfcColumn → COLUMN)
  placement: Placement;
  section?: ColumnSection;     // sección de barra (pilar/viga)
  thickness?: number;          // espesor (forjado/muro), m
  height?: number;             // altura del muro / del vano, m
  width?: number;              // ancho del vano (carpintería), m
  sill?: number;               // alféizar/antepecho del vano, m
  exterior?: boolean;          // IsExternal: fachada (true) | divisoria (false)
  spans?: [number, number];    // EXTENSIÓN vertical: rango de niveles [desde, hasta]
  material?: string;           // HA-30 (def. C1)
  level: string;               // nombre de la planta que lo contiene
  storeyIndex: number;         // índice de esa planta (para render por tramos)
  axis?: string;               // eje lógico de la retícula (p. ej. "B2")
  uriBsdd: string;             // clasificación bsDD (IFC 4.3)
  // Capa relacional (diferida en este slice, modelada con IfcWall/IfcDoor):
  host?: string;               // anfitrión (la puerta VA EN este muro)
  container?: string;          // contenido en (este lavamanos está EN esta habitación)
}

export interface StoreyInstance {
  code: string;
  ifcClass: "IfcBuildingStorey";
  index: number;
  name: string;
  elevation: number;
  spaces: SpaceInstance[];
  elements: ElementInstance[]; // IfcElement contenidos en la planta (Inc núcleo)
}
export interface ZoneInstance {
  code: string;
  ifcClass: "IfcZone";
  kind: string;                // nombre de uso (privado | comunes | aparcamiento | …)
  longName: string;
  members: string[];
}
export interface BuildingModel {
  project: { name: string; code: string };
  site: { name: string; longName?: string };
  building: { name: string; longName?: string };
  storeys: StoreyInstance[];
  zones: ZoneInstance[];
  grid?: GridResolved;         // retícula estructural del edificio (si la hay)
}

// ── Retícula estructural (sistema transversal que coloca IfcColumn) ───────────
// Decisión JM: ejes lógicos (cada columna lleva su cruce de ejes) pero SIN emitir
// un primitivo IfcGrid; el puente entrega `reticulas_pilares` a C1, que C1 ya
// consume. La retícula es a nivel de EDIFICIO; el pilar se REPITE por planta.

/**
 * Intención de retícula. Dos formas (ejes explícitos ganan al atajo uniforme):
 *  - EJES EXPLÍCITOS: `axesX`/`axesY` = posiciones de eje en m (no uniformes; el
 *    usuario alinea con fachadas, borde de pasillo… p. ej. axesY [0, 6.75, 15]).
 *  - ATAJO UNIFORME: `sepX`/`sepY` → ejes equiespaciados ANCLADOS a las dos
 *    fachadas (incluyen 0 y W/D), para que el pilar de fachada siempre caiga.
 */
export interface GridInput {
  sepX?: number;               // atajo: separación uniforme en X (m)
  sepY?: number;               // atajo: separación uniforme en Y (m)
  axesX?: number[];            // ejes explícitos en X (m)
  axesY?: number[];            // ejes explícitos en Y (m)
  section?: ColumnSection;     // sección de pilar (def 0,40 × 0,40)
  material?: string;           // def HA-30
}

/** Retícula resuelta = listas de ejes por dirección (determinista). IfcGrid-like. */
export interface GridResolved {
  axesX: number[];             // posiciones de eje en X (m), ordenadas
  axesY: number[];             // posiciones de eje en Y (m), ordenadas
  section: ColumnSection;
  material: string;
}

/** Un nudo de la retícula con su eje lógico, antes de asignarle código por planta. */
export interface GridNode { x: number; y: number; axis: string; ix: number; iy: number; }

export const DEFAULT_SECTION: ColumnSection = { w: 0.4, d: 0.4 };
export const DEFAULT_MATERIAL = "HA-30";
export const DEFAULT_SLAB_T = 0.3; // espesor de forjado (m), default C1
export const DEFAULT_WALL_T = 0.25; // espesor de muro de fachada (m), default C1
export const DEFAULT_PARTITION_T = 0.1; // espesor de tabique interior (m)
const BSDD = (cls: string): string => `https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/${cls}`;
const BSDD_COLUMN = BSDD("IfcColumn");
const BSDD_SLAB = BSDD("IfcSlab");
const BSDD_OPENING = BSDD("IfcOpeningElement");
const BSDD_WALL = BSDD("IfcWall");
const BSDD_DOOR = BSDD("IfcDoor");
const BSDD_WINDOW = BSDD("IfcWindow");
const BSDD_STAIR = BSDD("IfcStair");
/** Defaults de carpintería (m): ancho × alto × alféizar. */
const CARP_DEF = { door: { w: 0.9, h: 2.1, sill: 0 }, window: { w: 1.2, h: 1.2, sill: 0.9 } };

/** Contorno rectangular (m) de una huella, en orden CCW. */
const rectContour = (f: Footprint): [number, number][] =>
  [[f.x, f.y], [f.x + f.w, f.y], [f.x + f.w, f.y + f.d], [f.x, f.y + f.d]];

/** Datos acumulados desde el diálogo (= parámetros del generador residencia). */
export interface PlanInput {
  rooms: { count: number; layout: "both-sides" | "single-side" } | null;
  corridor: { width: number } | null;
  cores: { orientation: Orient; detail?: string }[];
}
export interface BuildingInput {
  project?: string;
  site?: string; siteLong?: string;
  building?: string; buildingLong?: string;
  storeys?: { count: number; height: number };
  plan: PlanInput;
  /** Programa no-residencial: generador del registro + sus parámetros (Inc 2). */
  program?: { generator: string; params: unknown };
  /** Retícula estructural del edificio (sistema transversal → IfcColumn). */
  grid?: GridInput;
  /** Tabiques interiores (divisorias) como líneas: el usuario los coloca a propósito. */
  partitions?: Array<{ start: [number, number]; end: [number, number] }>;
  /** Carpintería: puertas/ventanas en un punto sobre un muro (el modelo busca el anfitrión). */
  openings?: Array<{ kind: "door" | "window"; x: number; y: number; width?: number; height?: number }>;
}

/** Rectángulo de planta por defecto (m): X=ancho, Y=fondo. */
export const DEFAULT_CTX: PlanContext = { W: 31, D: 15.6 };

const ABBR: Record<string, string> = { Habitacion: "HAB", Pasillo: "PAS", Nucleo: "NUC" };
const ZONE_ABBR: Record<string, string> = { privado: "PRI", comunes: "COM", aparcamiento: "APA", circulacion: "CIR" };
const ZONE_LABEL: Record<string, string> = {
  privado: "Habitaciones (privado)", comunes: "Comunes · circulación",
  aparcamiento: "Aparcamiento", circulacion: "Circulación (viales y rampas)",
};
const pad2 = (n: number): string => String(n).padStart(2, "0");
const round2 = (x: number): number => Math.round(x * 100) / 100;
const abbrev = (objectType: string): string => ABBR[objectType] ?? objectType.slice(0, 3).toUpperCase();
const zabbr = (z: string): string => ZONE_ABBR[z] ?? z.slice(0, 3).toUpperCase();
const zlabel = (z: string): string => ZONE_LABEL[z] ?? z;
// Nombres de planta ALINEADOS con C1 (resolver_niveles): "Planta Baja" / "Planta i".
// Importa para el puente: los pilares/losas referencian el nivel por nombre.
function storeyName(i: number): string { return i === 0 ? "Planta Baja" : `Planta ${i}`; }

/** Etiqueta de eje en Y (filas): A, B, … Z, AA, AB… (determinista). */
function axisLetter(iy: number): string {
  let s = "", n = iy;
  do { s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26) - 1; } while (n >= 0);
  return s;
}

/** Limpia ejes explícitos: acota a [0,L], redondea, deduplica y ordena. */
function cleanAxes(axes: number[], L: number): number[] {
  const xs = axes.map((a) => round2(Math.min(Math.max(a, 0), L)));
  return [...new Set(xs)].sort((a, b) => a - b);
}
/** Ejes uniformes ANCLADOS a las dos fachadas: incluyen 0 y L, vanos ~iguales ≈ sep. */
function uniformAxes(L: number, sep?: number): number[] {
  const s = sep && sep > 0 ? sep : 5;
  const nbays = Math.max(1, Math.round(L / s));
  return Array.from({ length: nbays + 1 }, (_, k) => round2((L * k) / nbays));
}

/**
 * Resuelve la retícula a LISTAS DE EJES por dirección (IfcGrid-like). Ejes explícitos
 * si se dan (el usuario alinea con fachadas/pasillo); si no, el atajo uniforme anclado
 * a las dos fachadas. Determinista (mismo input → mismos ejes) → golden-able.
 */
export function resolveGrid(g: GridInput, ctx: PlanContext): GridResolved {
  const axesX = g.axesX ? cleanAxes(g.axesX, ctx.W) : uniformAxes(ctx.W, g.sepX);
  const axesY = g.axesY ? cleanAxes(g.axesY, ctx.D) : uniformAxes(ctx.D, g.sepY);
  return { axesX, axesY, section: g.section ?? DEFAULT_SECTION, material: g.material ?? DEFAULT_MATERIAL };
}

/** Nudos = producto cartesiano de los ejes; eje lógico B2 = letra(fila Y) + nº(col X). */
export function buildGrid(grid: GridResolved): GridNode[] {
  const out: GridNode[] = [];
  grid.axesY.forEach((y, iy) => {
    grid.axesX.forEach((x, ix) => {
      out.push({ ix, iy, x: round2(x), y: round2(y), axis: `${axisLetter(iy)}${ix + 1}` });
    });
  });
  return out;
}

/**
 * ¿Hay algo que mostrar? Crece con el diálogo: en cuanto se nombra proyecto/sitio/
 * edificio ya se pinta la cabecera; plantas y espacios se añaden después.
 */
/**
 * Muros entre espacios adyacentes (LINDES): aristas compartidas de footprints
 * rectangulares, fundidas en líneas continuas. Driver de la divisoria arquitectónica
 * (el tabique entre dos habitaciones = su arista común). Determinista.
 */
export function spaceBoundaryWalls(foots: Footprint[]): Array<{ start: [number, number]; end: [number, number] }> {
  const eps = 1e-6;
  const vert = new Map<string, [number, number][]>(); // x → intervalos [y0,y1]
  const horz = new Map<string, [number, number][]>(); // y → intervalos [x0,x1]
  const key = (n: number): string => (Math.round(n * 1000) / 1000).toFixed(3);
  const push = (m: Map<string, [number, number][]>, k: string, seg: [number, number]): void => {
    const a = m.get(k); if (a) a.push(seg); else m.set(k, [seg]);
  };
  for (let i = 0; i < foots.length; i++) for (let j = 0; j < foots.length; j++) {
    if (i === j) continue;
    const A = foots[i], B = foots[j];
    if (Math.abs(A.x + A.w - B.x) < eps) { // arista vertical: A a la izq. de B
      const y0 = Math.max(A.y, B.y), y1 = Math.min(A.y + A.d, B.y + B.d);
      if (y1 - y0 > eps) push(vert, key(A.x + A.w), [y0, y1]);
    }
    if (Math.abs(A.y + A.d - B.y) < eps) { // arista horizontal: A debajo de B
      const x0 = Math.max(A.x, B.x), x1 = Math.min(A.x + A.w, B.x + B.w);
      if (x1 - x0 > eps) push(horz, key(A.y + A.d), [x0, x1]);
    }
  }
  const merge = (segs: [number, number][]): [number, number][] => {
    const s = segs.slice().sort((a, b) => a[0] - b[0]); const out: [number, number][] = [];
    for (const [lo, hi] of s) {
      const last = out[out.length - 1];
      if (last && lo <= last[1] + eps) last[1] = Math.max(last[1], hi); else out.push([lo, hi]);
    }
    return out;
  };
  const out: Array<{ start: [number, number]; end: [number, number] }> = [];
  for (const [k, segs] of vert) { const x = round2(parseFloat(k)); for (const [y0, y1] of merge(segs)) out.push({ start: [x, round2(y0)], end: [x, round2(y1)] }); }
  for (const [k, segs] of horz) { const y = round2(parseFloat(k)); for (const [x0, x1] of merge(segs)) out.push({ start: [round2(x0), y], end: [round2(x1), y] }); }
  return out;
}

/** Localiza el muro (línea) que pasa por un punto; devuelve el muro y su dirección unitaria. */
function findHostWall(walls: ElementInstance[], x: number, y: number): { wall: ElementInstance; dir: [number, number] } | null {
  const tol = 0.06;
  for (const w of walls) {
    if (w.placement.kind !== "line") continue;
    const [ax, ay] = w.placement.start, [bx, by] = w.placement.end;
    const dx = bx - ax, dy = by - ay; const len = Math.hypot(dx, dy) || 1;
    const t = ((x - ax) * dx + (y - ay) * dy) / (len * len);
    if (t < -tol / len || t > 1 + tol / len) continue;
    const cx = ax + t * dx, cy = ay + t * dy;
    if (Math.hypot(x - cx, y - cy) <= tol) return { wall: w, dir: [dx / len, dy / len] };
  }
  return null;
}

export function hasModel(inp: BuildingInput): boolean {
  return Boolean(inp.project || inp.site || inp.building) || (inp.storeys?.count ?? 0) > 0;
}

/**
 * Genera el modelo completo. Determinista. El generador coloca los footprints de la
 * planta tipo (iguales en todas las plantas); el modelo asigna códigos por planta y
 * agrupa en zonas. Si no hay generador con datos, las plantas salen vacías.
 */
export function buildModel(inp: BuildingInput, ctx: PlanContext = DEFAULT_CTX): BuildingModel {
  const n = inp.storeys?.count ?? 0;
  const h = inp.storeys?.height ?? 0;
  // planta tipo: la coloca el generador ACTIVO (residencia por defecto, o el del
  // programa). El núcleo solo nombra/agrupa lo que el generador produce.
  const placed = inp.program
    ? (GENERATORS[inp.program.generator]?.generate(inp.program.params, ctx) ?? [])
    : residenceGenerator.generate(inp.plan, ctx);

  // retícula estructural (sistema transversal → IfcColumn). El pilar se REPITE en
  // TODAS las plantas: cada una sostiene la losa de arriba (la última, la CUBIERTA).
  const grid = inp.grid ? resolveGrid(inp.grid, ctx) : undefined;
  const gridNodes = grid ? buildGrid(grid) : [];
  const SLAB_CONTOUR: [number, number][] = [[0, 0], [ctx.W, 0], [ctx.W, ctx.D], [0, ctx.D]];

  const storeys: StoreyInstance[] = [];
  const zoneMembers = new Map<string, string[]>(); // zona → códigos (orden de aparición)

  for (let i = 0; i < n; i++) {
    const p = `P${pad2(i)}`;
    const counters = new Map<string, number>();
    const spaces: SpaceInstance[] = placed.map((g) => {
      const ab = abbrev(g.objectType);
      let code: string;
      if (g.numbered && g.sideTag) {
        const key = `${ab}-${g.sideTag}`;
        const seq = (counters.get(key) ?? 0) + 1;
        counters.set(key, seq);
        code = `AQ-ESP-${ab}-${p}-${g.sideTag}-${pad2(seq)}`;
      } else if (g.sideTag) {
        code = `AQ-ESP-${ab}-${p}-${g.sideTag}`;
      } else {
        code = `AQ-ESP-${ab}-${p}`;
      }
      const members = zoneMembers.get(g.zone) ?? [];
      members.push(code); zoneMembers.set(g.zone, members);
      return {
        code, ifcClass: "IfcSpace", objectType: g.objectType, longName: g.longName,
        footprint: g.footprint, zone: g.zone, sideTag: g.sideTag,
      };
    });
    // Pilares: en TODAS las plantas (cada una sube y sostiene la losa de arriba).
    const cols: ElementInstance[] = grid
      ? gridNodes.map((nd) => ({
          code: `AQ-PIL-${p}-${nd.axis}`,
          ifcClass: "IfcColumn", objectType: "Pilar", predefinedType: "COLUMN",
          placement: { kind: "point", x: nd.x, y: nd.y },
          section: grid.section, material: grid.material,
          level: storeyName(i), storeyIndex: i, axis: nd.axis, uriBsdd: BSDD_COLUMN,
        }))
      : [];

    // Forjados: el SUELO de cada planta i≥1 (la baja apoya en terreno) y, encima de
    // la ÚLTIMA planta, la CUBIERTA (techo, nivel n). Cubren la huella del edificio.
    const slabCode = `AQ-FOR-${p}`;
    const slabs: ElementInstance[] = [];
    if (i >= 1) slabs.push({
      code: slabCode, ifcClass: "IfcSlab", objectType: "Forjado", predefinedType: "FLOOR",
      placement: { kind: "polygon", contour: SLAB_CONTOUR },
      thickness: DEFAULT_SLAB_T, material: DEFAULT_MATERIAL,
      level: storeyName(i), storeyIndex: i, uriBsdd: BSDD_SLAB,
    });
    if (i === n - 1) slabs.push({
      code: "AQ-FOR-CUB", ifcClass: "IfcSlab", objectType: "Cubierta", predefinedType: "ROOF",
      placement: { kind: "polygon", contour: SLAB_CONTOUR },
      thickness: DEFAULT_SLAB_T, material: DEFAULT_MATERIAL,
      level: "Cubierta", storeyIndex: n, uriBsdd: BSDD_SLAB,
    });

    // Hueco de forjado: cada Nucleo (circulación vertical) vacía el forjado de PISO que
    // atraviesa (la CUBIERTA cierra por arriba: no se vacía). `host` = el forjado de piso
    // → estrena la capa relacional (IfcRelVoidsElement). Geometría = huella del núcleo.
    const openings: ElementInstance[] = i >= 1
      ? placed.filter((g) => g.objectType === "Nucleo").map((g, k) => ({
          code: `AQ-HUE-${p}-${pad2(k + 1)}`,
          ifcClass: "IfcOpeningElement", objectType: "HuecoForjado", predefinedType: "OPENING",
          placement: { kind: "polygon", contour: rectContour(g.footprint) },
          level: storeyName(i), storeyIndex: i, host: slabCode, uriBsdd: BSDD_OPENING,
        } as ElementInstance))
      : [];

    // Muros de FACHADA (driver = envolvente): 4 por planta, los lados de la huella.
    // POR PLANTA (de suelo a techo, altura h), geometría de LÍNEA, exterior=true.
    // `spans=[i,i+1]` deja la EXTENSIÓN como propiedad: el muro pasante (núcleo) será
    // el mismo elemento con otro rango. Driver de divisoria/núcleo = clon, después.
    const fachada: Array<{ tag: string; a: [number, number]; b: [number, number] }> = [
      { tag: "S", a: [0, 0], b: [ctx.W, 0] },
      { tag: "E", a: [ctx.W, 0], b: [ctx.W, ctx.D] },
      { tag: "N", a: [ctx.W, ctx.D], b: [0, ctx.D] },
      { tag: "O", a: [0, ctx.D], b: [0, 0] },
    ];
    const walls: ElementInstance[] = fachada.map((e) => ({
      code: `AQ-MUR-${p}-FAC-${e.tag}`,
      ifcClass: "IfcWall", objectType: "Fachada", predefinedType: "SOLIDWALL",
      placement: { kind: "line", start: e.a, end: e.b },
      thickness: DEFAULT_WALL_T, material: DEFAULT_MATERIAL, exterior: true,
      height: round2(h), spans: [i, i + 1],
      level: storeyName(i), storeyIndex: i, uriBsdd: BSDD_WALL,
    } as ElementInstance));

    // Tabiques interiores (DIVISORIAS): líneas que el usuario coloca a propósito
    // (alineadas a un eje o libres). Mismo molde que la fachada: línea, por planta,
    // pero INTERIOR (exterior:false, PARTITIONING). Driver = la línea dada, no la envolvente.
    const partitions: ElementInstance[] = (inp.partitions ?? []).map((d, k) => ({
      code: `AQ-MUR-${p}-DIV-${pad2(k + 1)}`,
      ifcClass: "IfcWall", objectType: "Divisoria", predefinedType: "PARTITIONING",
      placement: { kind: "line", start: d.start, end: d.end },
      thickness: DEFAULT_PARTITION_T, material: DEFAULT_MATERIAL, exterior: false,
      height: round2(h), spans: [i, i + 1],
      level: storeyName(i), storeyIndex: i, uriBsdd: BSDD_WALL,
    } as ElementInstance));

    // Muros de NÚCLEO (driver = huella del Nucleo): la caja de escalera/ascensor.
    // PASANTES: un solo elemento por lado, CONTINUO de suelo a cubierta (spans=[0,n],
    // altura=n·h), no por planta. Estructurales (SHEAR). Mismo driver que los huecos
    // (el Nucleo): los muros encierran el hueco que vacía los forjados. Solo i===0.
    const coreWalls: ElementInstance[] = i === 0
      ? placed.filter((g) => g.objectType === "Nucleo").flatMap((g, k) => {
          const f = g.footprint;
          const sides: Array<{ tag: string; a: [number, number]; b: [number, number] }> = [
            { tag: "S", a: [f.x, f.y], b: [f.x + f.w, f.y] },
            { tag: "E", a: [f.x + f.w, f.y], b: [f.x + f.w, f.y + f.d] },
            { tag: "N", a: [f.x + f.w, f.y + f.d], b: [f.x, f.y + f.d] },
            { tag: "O", a: [f.x, f.y + f.d], b: [f.x, f.y] },
          ];
          return sides.map((s) => ({
            code: `AQ-MUR-NUC-${pad2(k + 1)}-${s.tag}`,
            ifcClass: "IfcWall", objectType: "MuroNucleo", predefinedType: "SHEAR",
            placement: { kind: "line", start: s.a, end: s.b },
            thickness: DEFAULT_WALL_T, material: DEFAULT_MATERIAL, exterior: false,
            height: round2(n * h), spans: [0, n],
            level: storeyName(0), storeyIndex: 0, uriBsdd: BSDD_WALL,
          } as ElementInstance));
        })
      : [];

    // Divisorias por LINDES (driver = aristas compartidas de los espacios). Automáticas
    // en distribución residencial/oficina (no en parking → no separa plazas con muros).
    // Excluye el Nucleo (ya tiene sus muros pasantes). Mismo molde: interior, por planta.
    const lindes: ElementInstance[] = !inp.program
      ? spaceBoundaryWalls(placed.filter((g) => g.objectType !== "Nucleo").map((g) => g.footprint)).map((d, k) => ({
          code: `AQ-MUR-${p}-LIN-${pad2(k + 1)}`,
          ifcClass: "IfcWall", objectType: "Divisoria", predefinedType: "PARTITIONING",
          placement: { kind: "line", start: d.start, end: d.end },
          thickness: DEFAULT_PARTITION_T, material: DEFAULT_MATERIAL, exterior: false,
          height: round2(h), spans: [i, i + 1],
          level: storeyName(i), storeyIndex: i, uriBsdd: BSDD_WALL,
        } as ElementInstance))
      : [];

    // CARPINTERÍA (puertas/ventanas): hosteada por el muro que pasa por su punto.
    // Estrena el host/void en VERTICAL (el vano vacía el muro; C1 lo rellena con la
    // puerta/ventana). El vano = línea de su ancho sobre el muro. Por planta.
    const storeyWalls = [...walls, ...partitions, ...lindes, ...coreWalls];
    const carpentry: ElementInstance[] = (inp.openings ?? []).flatMap((o, k) => {
      const host = findHostWall(storeyWalls, o.x, o.y);
      if (!host) return [];
      const def = CARP_DEF[o.kind];
      const wdt = o.width ?? def.w, hgt = o.height ?? def.h;
      const [dx, dy] = host.dir;
      const isDoor = o.kind === "door";
      return [{
        code: `AQ-${isDoor ? "PUE" : "VEN"}-${p}-${pad2(k + 1)}`,
        ifcClass: isDoor ? "IfcDoor" : "IfcWindow", objectType: isDoor ? "Puerta" : "Ventana",
        placement: { kind: "line", start: [round2(o.x - dx * wdt / 2), round2(o.y - dy * wdt / 2)], end: [round2(o.x + dx * wdt / 2), round2(o.y + dy * wdt / 2)] },
        width: round2(wdt), height: round2(hgt), sill: def.sill,
        level: storeyName(i), storeyIndex: i, host: host.wall.code, uriBsdd: isDoor ? BSDD_DOOR : BSDD_WINDOW,
      } as ElementInstance];
    });

    // ESCALERA (IfcStair): cada Nucleo lleva una escalera, un TRAMO por planta (de i a
    // i+1). Contenida en el espacio del núcleo (container). El cebo da identidad +
    // colocación; C1 autora la geometría real (peldaños/meseta) desde `escaleras`.
    const stairs: ElementInstance[] = placed.filter((g) => g.objectType === "Nucleo").map((g, k) => {
      const f = g.footprint;
      const nucCode = `AQ-ESP-NUC-${p}${g.sideTag ? `-${g.sideTag}` : ""}`;
      return {
        code: `AQ-ESC-${p}-${pad2(k + 1)}`,
        ifcClass: "IfcStair", objectType: "Escalera", predefinedType: "HALF_TURN_STAIR",
        placement: { kind: "point", x: round2(f.x), y: round2(f.y) },
        width: round2(Math.min(1.2, f.w)), height: round2(h),
        container: nucCode, level: storeyName(i), storeyIndex: i, uriBsdd: BSDD_STAIR,
      } as ElementInstance;
    });

    const elements: ElementInstance[] = [...cols, ...slabs, ...openings, ...walls, ...partitions, ...lindes, ...coreWalls, ...carpentry, ...stairs];

    storeys.push({
      code: `AQ-NIV-${p}`, ifcClass: "IfcBuildingStorey", index: i,
      name: storeyName(i), elevation: round2(i * h), spaces, elements,
    });
  }

  const zones: ZoneInstance[] = [];
  for (const [zoneName, members] of zoneMembers) {
    zones.push({
      code: `AQ-ZON-${zabbr(zoneName)}`, ifcClass: "IfcZone", kind: zoneName,
      longName: zlabel(zoneName), members,
    });
  }

  return {
    project: { name: inp.project ?? "Proyecto", code: "AQ-PRY" },
    site: { name: inp.site ?? "Solar", longName: inp.siteLong },
    building: { name: inp.building ?? "Edificio", longName: inp.buildingLong },
    storeys, zones, grid,
  };
}

/** Recuento total de IfcSpace en el modelo. */
export function spaceCount(m: BuildingModel): number {
  return m.storeys.reduce((a, s) => a + s.spaces.length, 0);
}

/** Recuento de elementos de una clase IFC en todo el modelo. */
export function elementCount(m: BuildingModel, ifcClass: string): number {
  return m.storeys.reduce((a, s) => a + s.elements.filter((e) => e.ifcClass === ifcClass).length, 0);
}
/** Recuento total de IfcColumn (todas las plantas estructurales). */
export function columnCount(m: BuildingModel): number { return elementCount(m, "IfcColumn"); }
/** Recuento total de IfcSlab (forjados, todas las plantas menos la baja). */
export function slabCount(m: BuildingModel): number { return elementCount(m, "IfcSlab"); }
/** Recuento total de IfcOpeningElement (huecos de forjado). */
export function openingCount(m: BuildingModel): number { return elementCount(m, "IfcOpeningElement"); }
/** Recuento total de IfcWall (muros). */
export function wallCount(m: BuildingModel): number { return elementCount(m, "IfcWall"); }
/** Recuento de carpintería (IfcDoor + IfcWindow). */
export function carpentryCount(m: BuildingModel): number { return elementCount(m, "IfcDoor") + elementCount(m, "IfcWindow"); }
/** Recuento de escaleras (IfcStair). */
export function stairCount(m: BuildingModel): number { return elementCount(m, "IfcStair"); }
