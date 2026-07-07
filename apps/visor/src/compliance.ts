/** compliance.ts — lectura del cumplimiento normativo 6D (vertical visor-cumplimiento-6d).
 *
 * El write-back 6D del C3 (engines/cumplimiento.escribir_cumplimiento) escribe en cada elemento
 * un `Pset_Aqyra_Cumplimiento` (D-6D-1) con su `Resultado` de peor caso (D-6D-2) + la exigencia
 * dominante y su referencia. Este módulo lo LEE con web-ifc (capa de DATOS, como `cost.ts` lee el
 * IfcCostSchedule) y produce el mapa por elemento que el viewer colorea (D-6D-4), más el resumen
 * por resultado. Puro dato: no toca geometría ni render.
 */
import type { IfcAPI } from "web-ifc";
import * as WI from "web-ifc";

export type ResultadoCumplimiento = "cumple" | "no-cumple" | "no-aplica" | "no-verificable";

/** Taxonomía CERRADA del resultado (D4/D-6D-1), en orden de leyenda. */
export const RESULTADOS_CUMPLIMIENTO: readonly ResultadoCumplimiento[] = [
  "cumple", "no-cumple", "no-aplica", "no-verificable",
];

/** Colores del visor por resultado (D-6D-4). */
export const HEX_CUMPLIMIENTO: Record<ResultadoCumplimiento, string> = {
  "cumple": "#2e9e5b",
  "no-cumple": "#d64545",
  "no-aplica": "#8a8f98",
  "no-verificable": "#e0a43a",
};

/** Etiqueta humana por resultado (leyenda). */
export const ETIQUETA_CUMPLIMIENTO: Record<ResultadoCumplimiento, string> = {
  "cumple": "Cumple",
  "no-cumple": "No cumple",
  "no-aplica": "No aplica",
  "no-verificable": "No verificable",
};

/** Gris neutro para elementos sin resultado (sin Pset de cumplimiento). */
export const GRIS_SIN_DATO: { r: number; g: number; b: number } = { r: 0.55, g: 0.55, b: 0.58 };

/** Nombre del Pset de marca que lleva el veredicto por elemento (D-6D-1). */
export const PSET_CUMPLIMIENTO = "Pset_Aqyra_Cumplimiento";

export interface ElementoCumplimiento {
  globalId: string;
  resultado: ResultadoCumplimiento;
  /** id de la exigencia DOMINANTE (la que fija el peor caso), si consta */
  exigencia?: string;
  documentoBasico?: string;
  apartado?: string;
  pack?: string;
  /** motivo, solo si `resultado === "no-verificable"` (D4) */
  motivo?: string;
}

export interface CumplimientoModelo {
  porElemento: Map<string, ElementoCumplimiento>;
  /** conteo por resultado (las 4 claves siempre presentes) */
  resumen: Record<ResultadoCumplimiento, number>;
}

function reg(): Record<string, number> {
  return WI as unknown as Record<string, number>;
}

function strOf(v: unknown): string | undefined {
  const w = v as { value?: unknown } | null;
  return w && w.value != null ? String(w.value) : undefined;
}

/** #id (o número) de un handle web-ifc → expressID; 0 si no es referencia. */
function idOf(v: unknown): number {
  if (typeof v === "number") return v;
  const w = v as { value?: unknown } | null;
  const n = Number(w?.value ?? 0);
  return Number.isFinite(n) ? n : 0;
}

/** Handles de un atributo lista/único de web-ifc → array de expressIDs. */
function refIds(attr: unknown): number[] {
  if (Array.isArray(attr)) return attr.map(idOf).filter((n) => n > 0);
  const one = idOf(attr);
  return one > 0 ? [one] : [];
}

function esResultado(v: string | undefined): v is ResultadoCumplimiento {
  return v === "cumple" || v === "no-cumple" || v === "no-aplica" || v === "no-verificable";
}

/** #rrggbb → {r,g,b} normalizado 0..1. */
function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const h = hex.replace("#", "");
  return {
    r: parseInt(h.slice(0, 2), 16) / 255,
    g: parseInt(h.slice(2, 4), 16) / 255,
    b: parseInt(h.slice(4, 6), 16) / 255,
  };
}

/** Color del visor (0..1) por resultado (D-6D-4); gris neutro si el resultado no es de la taxonomía. */
export function colorPorResultado(resultado: string): { r: number; g: number; b: number } {
  return esResultado(resultado) ? hexToRgb(HEX_CUMPLIMIENTO[resultado]) : { ...GRIS_SIN_DATO };
}

/** Una entrada de la leyenda: resultado, etiqueta, color y conteo. */
export interface EntradaLeyendaCumplimiento {
  resultado: ResultadoCumplimiento;
  etiqueta: string;
  color: { r: number; g: number; b: number };
  count: number;
}

/** Leyenda de 4 entradas (D-6D-4) con el conteo del `resumen`, en orden de taxonomía. */
export function leyendaCumplimiento(m: CumplimientoModelo): EntradaLeyendaCumplimiento[] {
  return RESULTADOS_CUMPLIMIENTO.map((r) => ({
    resultado: r,
    etiqueta: ETIQUETA_CUMPLIMIENTO[r],
    color: hexToRgb(HEX_CUMPLIMIENTO[r]),
    count: m.resumen[r],
  }));
}

/**
 * Lee `Pset_Aqyra_Cumplimiento` del modelo (o `null` si el modelo NO es 6D — no hay ningún Pset de
 * cumplimiento). Determinista y puro dato: no toca geometría ni render.
 */
export function leerCumplimiento(api: IfcAPI, modelID: number): CumplimientoModelo | null {
  const R = reg();

  // 1 · Psets de cumplimiento (por expressID) → sus props leídas.
  type Bag = { resultado?: string; exigencia?: string; documentoBasico?: string;
    apartado?: string; pack?: string; motivo?: string };
  const psetBag = new Map<number, Bag>();
  const psIds = api.GetLineIDsWithType(modelID, R["IFCPROPERTYSET"]!);
  for (let i = 0; i < psIds.size(); i++) {
    const id = psIds.get(i);
    const ps = api.GetLine(modelID, id) as { Name?: { value?: string }; HasProperties?: unknown };
    if (ps.Name?.value !== PSET_CUMPLIMIENTO) continue;
    const bag: Bag = {};
    for (const pid of refIds(ps.HasProperties)) {
      const p = api.GetLine(modelID, pid) as { Name?: { value?: string }; NominalValue?: unknown };
      const nombre = p.Name?.value;
      const valor = strOf(p.NominalValue);
      if (!nombre) continue;
      if (nombre === "Resultado") bag.resultado = valor;
      else if (nombre === "Exigencia") bag.exigencia = valor;
      else if (nombre === "DocumentoBasico") bag.documentoBasico = valor;
      else if (nombre === "Apartado") bag.apartado = valor;
      else if (nombre === "Pack") bag.pack = valor;
      else if (nombre === "MotivoNoVerificable") bag.motivo = valor;
    }
    psetBag.set(id, bag);
  }
  if (psetBag.size === 0) return null; // el modelo no es 6D

  // 2 · IfcRelDefinesByProperties: pset → elementos (por GlobalId).
  const porElemento = new Map<string, ElementoCumplimiento>();
  const relIds = api.GetLineIDsWithType(modelID, R["IFCRELDEFINESBYPROPERTIES"]!);
  for (let i = 0; i < relIds.size(); i++) {
    const rel = api.GetLine(modelID, relIds.get(i)) as {
      RelatingPropertyDefinition?: unknown; RelatedObjects?: unknown;
    };
    const bag = psetBag.get(idOf(rel.RelatingPropertyDefinition));
    if (!bag || !esResultado(bag.resultado)) continue;
    for (const eid of refIds(rel.RelatedObjects)) {
      const el = api.GetLine(modelID, eid) as { GlobalId?: { value?: string } };
      const g = el.GlobalId?.value;
      if (!g) continue;
      porElemento.set(g, {
        globalId: g,
        resultado: bag.resultado,
        exigencia: bag.exigencia,
        documentoBasico: bag.documentoBasico,
        apartado: bag.apartado,
        pack: bag.pack,
        motivo: bag.motivo,
      });
    }
  }

  const resumen: Record<ResultadoCumplimiento, number> = {
    "cumple": 0, "no-cumple": 0, "no-aplica": 0, "no-verificable": 0,
  };
  for (const e of porElemento.values()) resumen[e.resultado] += 1;

  return { porElemento, resumen };
}
