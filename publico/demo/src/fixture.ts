/**
 * Mecanismo "caso real → fixture golden" (decisión JM).
 *
 * Cada caso que validamos en pantalla se puede CONGELAR como fixture: su entrada
 * (BuildingInput + contexto de planta) + un SNAPSHOT determinista de la salida
 * (cuentas por objectType, zonas, totales, códigos de muestra). Un test golden
 * vuelve a construir el modelo y comprueba que el snapshot no cambia → la capacidad
 * acumulada (generadores) nunca regresiona. La IA prepara; JM firma el golden.
 *
 * Flujo: en el cebo, `window.aqyraFixture("nombre")` devuelve el JSON del fixture →
 * se guarda en `demo/fixtures/<nombre>.json` → el test golden lo replica con checkFixture.
 */

import { buildModel, columnCount, slabCount, type BuildingInput } from "./model";
import type { PlanContext } from "./generators";

export interface CaseSnapshot {
  storeys: number;
  spacesPerStorey: number;
  totalSpaces: number;
  byObjectType: Record<string, number>;            // recuento en la planta baja
  zones: Array<{ code: string; kind: string; members: number }>;
  sampleCodes: string[];                            // primeros códigos (orden estable)
  // Capa de elementos (Inc núcleo). Opcionales: los fixtures antiguos no los traen.
  totalColumns?: number;                            // IfcColumn en todo el edificio
  columnsPerStorey?: number;                        // IfcColumn en la planta baja (estructural)
  sampleColumnCodes?: string[];                     // primeros códigos AQ-PIL (orden estable)
  totalSlabs?: number;                              // IfcSlab (forjados) en todo el edificio
}

export interface CaseFixture {
  name: string;
  input: BuildingInput;
  ctx: PlanContext;
  snapshot: CaseSnapshot;
}

/** Snapshot determinista del modelo que produce (input, ctx). */
export function snapshot(input: BuildingInput, ctx: PlanContext): CaseSnapshot {
  const m = buildModel(input, ctx);
  const st0 = m.storeys[0];
  const byObjectType: Record<string, number> = {};
  if (st0) for (const s of st0.spaces) byObjectType[s.objectType] = (byObjectType[s.objectType] ?? 0) + 1;
  return {
    storeys: m.storeys.length,
    spacesPerStorey: st0 ? st0.spaces.length : 0,
    totalSpaces: m.storeys.reduce((a, s) => a + s.spaces.length, 0),
    byObjectType,
    zones: m.zones.map((z) => ({ code: z.code, kind: z.kind, members: z.members.length })),
    sampleCodes: st0 ? st0.spaces.slice(0, 6).map((s) => s.code) : [],
    totalColumns: columnCount(m),
    columnsPerStorey: st0 ? st0.elements.filter((e) => e.ifcClass === "IfcColumn").length : 0,
    sampleColumnCodes: st0 ? st0.elements.filter((e) => e.ifcClass === "IfcColumn").slice(0, 6).map((e) => e.code) : [],
    totalSlabs: slabCount(m),
  };
}

/** Congela un caso como fixture (input + snapshot actual). */
export function makeFixture(name: string, input: BuildingInput, ctx: PlanContext): CaseFixture {
  return { name, input, ctx, snapshot: snapshot(input, ctx) };
}

/** Replica el fixture y comprueba que el snapshot sigue igual (golden anti-regresión). */
export function checkFixture(fx: CaseFixture): { ok: boolean; diffs: string[] } {
  const now = snapshot(fx.input, fx.ctx);
  const diffs: string[] = [];
  const cmp = (label: string, exp: unknown, got: unknown): void => {
    if (JSON.stringify(exp) !== JSON.stringify(got)) {
      diffs.push(`${label}: esperado ${JSON.stringify(exp)} · obtenido ${JSON.stringify(got)}`);
    }
  };
  cmp("storeys", fx.snapshot.storeys, now.storeys);
  cmp("spacesPerStorey", fx.snapshot.spacesPerStorey, now.spacesPerStorey);
  cmp("totalSpaces", fx.snapshot.totalSpaces, now.totalSpaces);
  cmp("byObjectType", fx.snapshot.byObjectType, now.byObjectType);
  cmp("zones", fx.snapshot.zones, now.zones);
  cmp("sampleCodes", fx.snapshot.sampleCodes, now.sampleCodes);
  // Columnas: tolerante con fixtures congelados antes del Inc núcleo (sin estos campos).
  cmp("totalColumns", fx.snapshot.totalColumns ?? 0, now.totalColumns ?? 0);
  cmp("columnsPerStorey", fx.snapshot.columnsPerStorey ?? 0, now.columnsPerStorey ?? 0);
  cmp("sampleColumnCodes", fx.snapshot.sampleColumnCodes ?? [], now.sampleColumnCodes ?? []);
  cmp("totalSlabs", fx.snapshot.totalSlabs ?? 0, now.totalSlabs ?? 0);
  return { ok: diffs.length === 0, diffs };
}
