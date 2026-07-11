// Dashboard de valor (E6.1) — LÓGICA PURA de presentación de la proyección. DOMINIO PURO:
// sin three/web-ifc/estado. La skin es CONSULTA, no cálculo (N-06): consume el índice de
// proyección PRECOMPUTADO (la salida de `proyectar(presupuesto, modelo, eje, corte)` de E2.2,
// anclada por GOL-PRE-03) y produce el modelo de vista que la UI pinta. NO re-mide, NO re-valora,
// NO re-proyecta: los `valor_total` son los del índice, tal cual. La skin es «propone»: no
// certifica (regla `isCertified` de data-state, D-021). Ratificado por JM (2026-07-11):
// D-DV-1..D-DV-5. Ver openspec/changes/visor-dashboard-valor/.
import type { DataState } from "./data-state.js";

/** Traza honesta de la fuente del grupo (fallback E2.1/D22): dato IFC nativo, fallback del
 *  criterio, partida sin geometría (regla), o sin clasificar (`—`). No se oculta (invariante Σ). */
export type FuenteValor = "ifc" | "criterio" | "regla" | "—";

/** Fila de un grupo de la proyección, tal como la emite `proyectar` (E2.2). El visor la LEE. */
export interface GrupoProyeccion {
  /** nombre del grupo del corte (p. ej. `…/Planta Baja`, `Estructura`, `(sin geometría)`). */
  readonly grupo: string;
  /** valor agregado del eje para el grupo. NO se recalcula en el cliente. */
  readonly valor_total: number;
  /** unidad del eje (`EUR`, `kgCO2e`). */
  readonly unidad: string;
  /** nº de partidas que aportan al grupo. */
  readonly n_partidas: number;
  /** GlobalIds de los objetos del grupo (para el resaltado en 3D). */
  readonly guids: readonly string[];
  /** fuente del grupo (traza del fallback, D22). */
  readonly fuente: FuenteValor;
}

/** Una vista de la proyección = una combinación `(eje, corte)` (lo que `proyectar` produce). */
export interface VistaProyeccion {
  /** eje de valor (`coste`, `carbono`). */
  readonly eje: string;
  /** corte/clasificación (`espacial`, `funcional`, `uniclass`). */
  readonly corte: string;
  /** Σ del eje declarada por el índice (== `suma_proyeccion` del engine). */
  readonly suma: number;
  /** grupos de la vista, en orden de primera aparición (determinista). */
  readonly grupos: readonly GrupoProyeccion[];
}

/** Total de un eje (invariante Σ de referencia). */
export interface TotalEje {
  readonly valor: number;
  readonly unidad: string;
}

/** Índice de proyección PRECOMPUTADO que el visor consume (emitido por el engine, D-DV-3). */
export interface IndiceProyeccion {
  /** id/hash de la medición de la que sale la proyección. */
  readonly presupuesto: string;
  /** totales por eje (referencia del invariante Σ). */
  readonly totales: Readonly<Record<string, TotalEje>>;
  /** todas las vistas `(eje, corte)` del índice. */
  readonly vistas: readonly VistaProyeccion[];
}

/** Fila del modelo de vista (una fila de la tabla + una barra de la gráfica). */
export interface FilaVista {
  readonly grupo: string;
  /** valor del índice, SIN alterar (lectura, no cálculo). */
  readonly valor: number;
  readonly unidad: string;
  readonly n_partidas: number;
  readonly fuente: FuenteValor;
  readonly guids: readonly string[];
  /** escala de la barra ∈ [0,1] = |valor| / máx(|valor|) de la vista (geometría de la fila). */
  readonly escala: number;
}

/** Modelo de vista que la UI pinta (tabla + gráfica + pastilla Σ + chip de fuente). */
export interface ModeloVista {
  readonly eje: string;
  readonly corte: string;
  readonly unidad: string;
  /** Σ declarada por el índice. */
  readonly suma: number;
  /** Σ de los `valor` de las filas (comprobación de presentación, no re-valoración). */
  readonly sumaGrupos: number;
  /** el invariante casa (|sumaGrupos − suma| ≤ 0,01): la presentación no pierde ni inventa valor. */
  readonly invarianteOk: boolean;
  readonly filas: readonly FilaVista[];
}

/**
 * ESTADO de la proyección mostrada (D-DV-5, regla dura «propone»). La proyección es CONSULTA: dato
 * firmado aguas arriba (`GOL-PRE-03`), mostrado como PROPUESTA en la skin. La skin NUNCA acuña el
 * verde: `isCertified(ESTADO_PROYECCION)` es `false`. El muro de cobro (export firmable, dos llaves)
 * llega como acción forward, no como estado de la vista.
 */
export const ESTADO_PROYECCION: DataState = "proposal";

/** Tolerancia del invariante Σ (== la de la golden de proyección, ±0,01). */
const TOL_SIGMA = 0.01;

/** Redondeo a 2 decimales para la comprobación del invariante (no altera los valores mostrados). */
function r2(x: number): number {
  return Math.round((x + Number.EPSILON) * 100) / 100;
}

/** Ejes disponibles en el índice, en orden de aparición. */
export function ejesDe(indice: IndiceProyeccion): string[] {
  const vistos: string[] = [];
  for (const v of indice.vistas) if (!vistos.includes(v.eje)) vistos.push(v.eje);
  return vistos;
}

/** Cortes disponibles para un eje, en orden de aparición. */
export function cortesDe(indice: IndiceProyeccion, eje: string): string[] {
  const vistos: string[] = [];
  for (const v of indice.vistas) if (v.eje === eje && !vistos.includes(v.corte)) vistos.push(v.corte);
  return vistos;
}

/** La vista `(eje, corte)` del índice, o `undefined` si no está. */
export function vistaDe(indice: IndiceProyeccion, eje: string, corte: string): VistaProyeccion | undefined {
  return indice.vistas.find((v) => v.eje === eje && v.corte === corte);
}

/**
 * Σ de los `valor_total` de una vista (comprobación del invariante). Recorre la vista y suma; NO
 * re-proyecta ni re-valora — sólo verifica que la presentación conserva el total del índice.
 */
export function sumaVista(vista: VistaProyeccion): number {
  return r2(vista.grupos.reduce((s, g) => s + g.valor_total, 0));
}

/**
 * Modelo de vista para la UI: una fila por grupo (mismo orden, mismos valores del índice) con la
 * escala de barra por |valor| / máx(|valor|), la unidad y el chip de fuente; la pastilla del
 * invariante (Σ grupos == suma del índice, ±0,01). DETERMINISTA: el mismo índice da las mismas
 * filas y el mismo orden. Operación de LECTURA: no altera ningún `valor_total`.
 */
export function modeloVista(vista: VistaProyeccion): ModeloVista {
  const maxAbs = vista.grupos.reduce((m, g) => Math.max(m, Math.abs(g.valor_total)), 0);
  const filas: FilaVista[] = vista.grupos.map((g) => ({
    grupo: g.grupo,
    valor: g.valor_total,
    unidad: g.unidad,
    n_partidas: g.n_partidas,
    fuente: g.fuente,
    guids: g.guids,
    escala: maxAbs > 0 ? Math.abs(g.valor_total) / maxAbs : 0,
  }));
  const unidad = vista.grupos[0]?.unidad ?? "";
  const sumaGrupos = sumaVista(vista);
  return {
    eje: vista.eje,
    corte: vista.corte,
    unidad,
    suma: vista.suma,
    sumaGrupos,
    invarianteOk: Math.abs(sumaGrupos - vista.suma) <= TOL_SIGMA,
    filas,
  };
}

/**
 * GUIDs del grupo seleccionado (selección → resaltado en 3D). Devuelve EXACTAMENTE los `guids[]`
 * de ese grupo en la vista (operación de presentación: ni reescribe el modelo ni la geometría). Si
 * el grupo no está, lista vacía.
 */
export function guidsDeGrupo(vista: VistaProyeccion, grupo: string): readonly string[] {
  return vista.grupos.find((g) => g.grupo === grupo)?.guids ?? [];
}
