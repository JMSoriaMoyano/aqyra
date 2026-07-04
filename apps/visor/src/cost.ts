/** cost.ts — lectura del modelo de coste 5D (V8, Fase IV·h4).
 *
 * El write-back 5D del C5 (engines/presupuesto.escribir_coste) escribe el modelo de coste
 * NATIVO de OpenBIM: IfcCostSchedule (BUDGET) → IfcRelNests → IfcCostItem por capítulo → por
 * partida (IfcCostValue=importe, CostQuantities), + IfcRelAssignsToControl a los elementos, +
 * IfcCostItem RESUMEN (PEM…PEC) + IfcMonetaryUnit. Este módulo lo LEE con web-ifc (capa de DATOS,
 * como ifc-loader) y produce el mapa por elemento que el viewer pinta (V9).
 *
 * `costeAsignado` por elemento = Σ (importe_partida / nº elementos de la partida): reparto
 * UNIFORME entre los elementos de cada partida (v0). Invariante: Σ costeAsignado = PEM medible.
 */
import type { IfcAPI } from "web-ifc";
import * as WI from "web-ifc";

export interface PartidaCoste {
  /** código de partida (IfcCostItem.Identification) — p. ej. FAB010 */
  codigo: string;
  descripcion?: string;
  importe: number;
  /** código de capítulo contenedor (IfcCostItem.Identification del padre en IfcRelNests) */
  capitulo?: string;
  /** GlobalIds de los elementos asignados (IfcRelAssignsToControl) */
  guids: string[];
}

export interface ElementoCoste {
  globalId: string;
  /** Σ (importe_partida / nº elementos) de las partidas que tocan este elemento */
  costeAsignado: number;
  /** códigos de partida que tocan este elemento */
  partidas: string[];
}

export interface CapituloCoste {
  codigo: string;
  descripcion?: string;
  importe: number;
  partidas: string[];
}

export interface TotalesCoste {
  moneda: string;
  PEM?: number;
  gg?: number;
  bi?: number;
  base?: number;
  iva?: number;
  PEC?: number;
}

export interface CosteModelo {
  moneda: string;
  partidas: PartidaCoste[];
  porElemento: Map<string, ElementoCoste>;
  capitulos: CapituloCoste[];
  totales: TotalesCoste;
  /** rango de costeAsignado (para normalizar el heatmap, V9) */
  minCoste: number;
  maxCoste: number;
}

function reg(): Record<string, number> {
  return WI as unknown as Record<string, number>;
}

/** Rampa de calor del heatmap de coste (V9): t∈[0,1] → azul → verde → amarillo → rojo.
 *  `t = (costeAsignado − min) / (max − min)`. Pura y determinista (testeable). */
export function costHeatColor(t: number): { r: number; g: number; b: number } {
  const x = Math.max(0, Math.min(1, Number.isFinite(t) ? t : 0));
  const stops: Array<{ p: number; c: [number, number, number] }> = [
    { p: 0.0, c: [0.20, 0.45, 0.90] },
    { p: 0.34, c: [0.20, 0.80, 0.45] },
    { p: 0.67, c: [0.95, 0.85, 0.25] },
    { p: 1.0, c: [0.90, 0.22, 0.18] },
  ];
  for (let i = 1; i < stops.length; i++) {
    const a = stops[i - 1]!, b = stops[i]!;
    if (x <= b.p) {
      const f = (x - a.p) / (b.p - a.p || 1);
      return { r: a.c[0] + (b.c[0] - a.c[0]) * f, g: a.c[1] + (b.c[1] - a.c[1]) * f, b: a.c[2] + (b.c[2] - a.c[2]) * f };
    }
  }
  const last = stops[stops.length - 1]!.c;
  return { r: last[0], g: last[1], b: last[2] };
}

/** Valor numérico de un IfcValue/medida envuelto por web-ifc (o número directo). */
function numOf(v: unknown): number {
  if (typeof v === "number") return v;
  const w = v as { value?: unknown } | null;
  return w && typeof w.value === "number" ? w.value : Number(w?.value ?? 0);
}

function strOf(v: unknown): string | undefined {
  const w = v as { value?: unknown } | null;
  return w && w.value != null ? String(w.value) : undefined;
}

/** Handles de un atributo lista/único de web-ifc → array de expressIDs. */
function refIds(attr: unknown): number[] {
  if (Array.isArray(attr)) return attr.map((h) => numOf(h)).filter((n) => Number.isFinite(n) && n > 0);
  const one = numOf(attr);
  return Number.isFinite(one) && one > 0 ? [one] : [];
}

const CLAVES_RESUMEN: Record<string, keyof TotalesCoste> = {
  PEM: "PEM", GG: "gg", BI: "bi", BASE: "base", IVA: "iva", PEC: "PEC",
};

/**
 * Lee el cost schedule del modelo (o `null` si el modelo NO es 5D — no hay IfcCostSchedule).
 * Determinista y puro dato: no toca geometría ni render.
 */
export function readCostModel(api: IfcAPI, modelID: number): CosteModelo | null {
  const R = reg();
  const schedIds = api.GetLineIDsWithType(modelID, R["IFCCOSTSCHEDULE"]!);
  if (schedIds.size() === 0) return null;
  const schedId = schedIds.get(0);

  // moneda
  let moneda = "EUR";
  const muIds = api.GetLineIDsWithType(modelID, R["IFCMONETARYUNIT"]!);
  if (muIds.size() > 0) {
    const u = api.GetLine(modelID, muIds.get(0)) as { Currency?: { value?: string } };
    moneda = u.Currency?.value ?? moneda;
  }

  // cost items indexados por expressID
  type RawItem = {
    Identification?: { value?: string };
    Name?: { value?: string };
    CostValues?: unknown;
  };
  const items = new Map<number, { codigo?: string; descripcion?: string; valores: Array<{ importe: number; categoria?: string }> }>();
  const ciIds = api.GetLineIDsWithType(modelID, R["IFCCOSTITEM"]!);
  for (let i = 0; i < ciIds.size(); i++) {
    const id = ciIds.get(i);
    const l = api.GetLine(modelID, id) as RawItem;
    const valores: Array<{ importe: number; categoria?: string }> = [];
    for (const cvId of refIds(l.CostValues)) {
      const cv = api.GetLine(modelID, cvId) as { AppliedValue?: unknown; Category?: { value?: string } };
      valores.push({ importe: numOf(cv.AppliedValue), categoria: cv.Category?.value });
    }
    items.set(id, { codigo: strOf(l.Identification), descripcion: strOf(l.Name), valores });
  }

  // jerarquía por IfcRelNests: schedule → capítulos → partidas
  const hijosDe = new Map<number, number[]>();
  const nestIds = api.GetLineIDsWithType(modelID, R["IFCRELNESTS"]!);
  for (let i = 0; i < nestIds.size(); i++) {
    const rel = api.GetLine(modelID, nestIds.get(i)) as { RelatingObject?: unknown; RelatedObjects?: unknown };
    const padre = numOf(rel.RelatingObject);
    if (padre) hijosDe.set(padre, refIds(rel.RelatedObjects));
  }
  const rootItems = hijosDe.get(schedId) ?? [];
  const capituloDePartida = new Map<number, number>(); // partidaId → capituloId
  const capituloIds: number[] = [];
  for (const rid of rootItems) {
    const hijos = hijosDe.get(rid);
    if (hijos && hijos.length) {
      capituloIds.push(rid);
      for (const pid of hijos) capituloDePartida.set(pid, rid);
    }
  }

  // asignaciones: partida (RelatingControl) → GUIDs de elementos (RelatedObjects)
  const guidsDeItem = new Map<number, string[]>();
  const asgIds = api.GetLineIDsWithType(modelID, R["IFCRELASSIGNSTOCONTROL"]!);
  for (let i = 0; i < asgIds.size(); i++) {
    const rel = api.GetLine(modelID, asgIds.get(i)) as { RelatingControl?: unknown; RelatedObjects?: unknown };
    const itemId = numOf(rel.RelatingControl);
    const guids: string[] = [];
    for (const eid of refIds(rel.RelatedObjects)) {
      const el = api.GetLine(modelID, eid) as { GlobalId?: { value?: string } };
      if (el.GlobalId?.value) guids.push(el.GlobalId.value);
    }
    if (itemId) guidsDeItem.set(itemId, guids);
  }

  // partidas (los items hijos de un capítulo)
  const partidas: PartidaCoste[] = [];
  const porElemento = new Map<string, ElementoCoste>();
  for (const [pid, capId] of capituloDePartida) {
    const it = items.get(pid);
    if (!it || !it.codigo) continue;
    const importe = it.valores[0]?.importe ?? 0;
    const guids = guidsDeItem.get(pid) ?? [];
    const capItem = items.get(capId);
    partidas.push({ codigo: it.codigo, descripcion: it.descripcion, importe, capitulo: capItem?.codigo, guids });
    const cuota = guids.length ? importe / guids.length : 0;
    for (const g of guids) {
      const e = porElemento.get(g) ?? { globalId: g, costeAsignado: 0, partidas: [] };
      // sin redondeo intermedio: Σ costeAsignado = Σ importes asignados = PEM medible (invariante)
      e.costeAsignado += cuota;
      e.partidas.push(it.codigo);
      porElemento.set(g, e);
    }
  }

  // capítulos (importe = Σ de sus partidas)
  const capitulos: CapituloCoste[] = [];
  for (const capId of capituloIds) {
    const capItem = items.get(capId);
    const hijos = hijosDe.get(capId) ?? [];
    const codigosHijos = hijos.map((h) => items.get(h)?.codigo).filter((c): c is string => !!c);
    const importe = Math.round(hijos.reduce((s, h) => s + (items.get(h)?.valores[0]?.importe ?? 0), 0) * 100) / 100;
    if (capItem?.codigo) capitulos.push({ codigo: capItem.codigo, descripcion: capItem.descripcion, importe, partidas: codigosHijos });
  }

  // totales: del IfcCostItem RESUMEN (CostValues categorizados)
  const totales: TotalesCoste = { moneda };
  for (const [, it] of items) {
    if (it.codigo === "RESUMEN") {
      for (const v of it.valores) {
        const k = CLAVES_RESUMEN[(v.categoria ?? "").toUpperCase()];
        if (k && k !== "moneda") totales[k] = v.importe;
      }
    }
  }

  const costes = [...porElemento.values()].map((e) => e.costeAsignado);
  return {
    moneda,
    partidas,
    porElemento,
    capitulos,
    totales,
    minCoste: costes.length ? Math.min(...costes) : 0,
    maxCoste: costes.length ? Math.max(...costes) : 0,
  };
}
