/** Tematización del chrome por disciplina + estado del rail (Slice A · chrome del visor v0.6).
 *  DOMINIO PURO: sin React/DOM. El chrome tiñe `--acc`/`--acc-soft` con el acento de la disciplina
 *  activa (D-CH-2) y el rail marca como bloqueadas las disciplinas que dependen de ingesta aún no
 *  soportada. Testeable headless (test/tema.test.ts). Ratificado por JM (2026-07-07): D-CH-1..5. */
import { DISCIPLINES, hexToRgba, type Discipline } from "./disciplines";

/**
 * Disciplinas que el visor sabe pintar hoy: las que tienen SKIN en `@aqyra/visor`
 * (`apps/visor/src/skins.ts`, D-SK-4 = Diseño + Estructuras). Las demás dependen de un desbloqueo
 * de ingesta (MEP: `IfcFlow*`; Obras lineales / Puentes: `IfcAlignment` + `stationMetric`) y salen
 * ATENUADAS en el rail. Al añadir una skin nueva en un slice de ingesta, se añade su id aquí.
 */
export const DISCIPLINAS_ACTIVAS: ReadonlySet<string> = new Set(["diseno", "estructuras"]);

export type EstadoDisciplina = "activa" | "bloqueada";

export interface EstadoRail {
  readonly id: string;
  readonly estado: EstadoDisciplina;
  /** motivo del bloqueo (sólo presente si `estado === "bloqueada"`). */
  readonly motivo?: string;
}

/** Estado de una disciplina en el rail: activa si el visor la sabe pintar; bloqueada si depende de
 *  ingesta aún no soportada. */
export function estadoDisciplina(id: string): EstadoRail {
  return DISCIPLINAS_ACTIVAS.has(id)
    ? { id, estado: "activa" }
    : { id, estado: "bloqueada", motivo: "ingesta" };
}

/** Estado de las 5 disciplinas del rail, en el orden de `DISCIPLINES`. */
export function railEstados(): EstadoRail[] {
  return DISCIPLINES.map((d) => estadoDisciplina(d.id));
}

/** Tema de una disciplina: acento (`--acc`) + acento suave rgba .16 (`--acc-soft`) para teñir el
 *  chrome. Un id desconocido cae en la primera disciplina (Diseño), nunca lanza. */
export interface Tema {
  readonly acc: string;
  readonly accSoft: string;
}

export function temaDisciplina(id: string): Tema {
  const d: Discipline = DISCIPLINES.find((x) => x.id === id) ?? DISCIPLINES[0];
  return { acc: d.accent, accSoft: hexToRgba(d.accent, 0.16) };
}
