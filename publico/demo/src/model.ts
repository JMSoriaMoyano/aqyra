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

/** Colocación de un elemento (m). Punto (pilar) o polígono (forjado); línea con muros. */
export type Placement =
  | { kind: "point"; x: number; y: number }
  | { kind: "polygon"; contour: [number, number][] };

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

/** Intención de retícula (lo que pide el usuario/acción). */
export interface GridInput {
  sepX: number;                // separación entre ejes en X (m)
  sepY: number;                // separación entre ejes en Y (m)
  section?: ColumnSection;     // sección de pilar (def 0,40 × 0,40)
  origin?: [number, number];   // origen de la malla (def [0,0])
  material?: string;           // def HA-30
}

/** Retícula resuelta sobre la huella W×D (determinista). */
export interface GridResolved {
  origin: [number, number];
  sepX: number; sepY: number;
  nx: number; ny: number;      // nº de ejes (nudos) en cada dirección
  section: ColumnSection;
  material: string;
}

/** Un nudo de la retícula con su eje lógico, antes de asignarle código por planta. */
export interface GridNode { x: number; y: number; axis: string; ix: number; iy: number; }

export const DEFAULT_SECTION: ColumnSection = { w: 0.4, d: 0.4 };
export const DEFAULT_MATERIAL = "HA-30";
export const DEFAULT_SLAB_T = 0.3; // espesor de forjado (m), default C1
const BSDD = (cls: string): string => `https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/${cls}`;
const BSDD_COLUMN = BSDD("IfcColumn");
const BSDD_SLAB = BSDD("IfcSlab");

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
function storeyName(i: number): string { return i === 0 ? "Planta baja" : `Planta ${i}`; }

/** Etiqueta de eje en Y (filas): A, B, … Z, AA, AB… (determinista). */
function axisLetter(iy: number): string {
  let s = "", n = iy;
  do { s = String.fromCharCode(65 + (n % 26)) + s; n = Math.floor(n / 26) - 1; } while (n >= 0);
  return s;
}

/**
 * Resuelve una retícula sobre la huella W×D: nudos en origen + ix·sepX / iy·sepY
 * que CABEN dentro de W×D. Determinista (mismo input → misma malla) → golden-able.
 * El nº de ejes lo decide la huella real (el cebo es la autoridad geométrica), no
 * el usuario: éste da la intención (separación), el visor cuenta los nudos.
 */
export function resolveGrid(g: GridInput, ctx: PlanContext): GridResolved {
  const sepX = Math.max(0.1, g.sepX), sepY = Math.max(0.1, g.sepY);
  const [ox, oy] = g.origin ?? [0, 0];
  const nx = Math.max(1, Math.floor((ctx.W - ox) / sepX + 1e-9) + 1);
  const ny = Math.max(1, Math.floor((ctx.D - oy) / sepY + 1e-9) + 1);
  return {
    origin: [round2(ox), round2(oy)], sepX, sepY, nx, ny,
    section: g.section ?? DEFAULT_SECTION, material: g.material ?? DEFAULT_MATERIAL,
  };
}

/** Nudos de la retícula con su eje lógico (B2 = letra de fila Y + nº de columna X). */
export function buildGrid(grid: GridResolved): GridNode[] {
  const out: GridNode[] = [];
  const [ox, oy] = grid.origin;
  for (let iy = 0; iy < grid.ny; iy++) {
    for (let ix = 0; ix < grid.nx; ix++) {
      out.push({
        ix, iy,
        x: round2(ox + ix * grid.sepX),
        y: round2(oy + iy * grid.sepY),
        axis: `${axisLetter(iy)}${ix + 1}`,
      });
    }
  }
  return out;
}

/**
 * ¿Hay algo que mostrar? Crece con el diálogo: en cuanto se nombra proyecto/sitio/
 * edificio ya se pinta la cabecera; plantas y espacios se añaden después.
 */
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

  // retícula estructural (sistema transversal → IfcColumn). El pilar se REPITE por
  // planta. Plantas ESTRUCTURALES = todas menos la superior (el pilar nace de una
  // planta y sostiene la de arriba); con una sola planta, la baja. Espeja el `estr`
  // de C1 (expandir_reticula) para que el preview anticipe el Maestro autorado.
  const grid = inp.grid ? resolveGrid(inp.grid, ctx) : undefined;
  const gridNodes = grid ? buildGrid(grid) : [];
  const isStructural = (i: number): boolean => (n <= 1 ? i === 0 : i < n - 1);

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
    // Pilares: en plantas estructurales (todas menos la cubierta).
    const cols: ElementInstance[] = grid && isStructural(i)
      ? gridNodes.map((nd) => ({
          code: `AQ-PIL-${p}-${nd.axis}`,
          ifcClass: "IfcColumn", objectType: "Pilar", predefinedType: "COLUMN",
          placement: { kind: "point", x: nd.x, y: nd.y },
          section: grid.section, material: grid.material,
          level: storeyName(i), storeyIndex: i, axis: nd.axis, uriBsdd: BSDD_COLUMN,
        }))
      : [];

    // Forjado: automático en cada planta menos la baja (i==0 apoya en terreno);
    // incluye la cubierta. Cubre la huella del edificio. Espeja el `losa` de C1.
    const slabs: ElementInstance[] = i >= 1
      ? [{
          code: `AQ-FOR-${p}`,
          ifcClass: "IfcSlab", objectType: "Forjado", predefinedType: "FLOOR",
          placement: { kind: "polygon", contour: [[0, 0], [ctx.W, 0], [ctx.W, ctx.D], [0, ctx.D]] },
          thickness: DEFAULT_SLAB_T, material: DEFAULT_MATERIAL,
          level: storeyName(i), storeyIndex: i, uriBsdd: BSDD_SLAB,
        }]
      : [];

    const elements: ElementInstance[] = [...cols, ...slabs];

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
