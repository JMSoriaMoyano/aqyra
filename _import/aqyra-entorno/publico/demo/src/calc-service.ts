// Cliente del SERVICIO DE CÁLCULO (anzuelo · D-019·C.4).
//
// El visor (cebo) sigue SIN servidor para VER. SOLO el post-proceso llama aquí por
// `fetch`: este módulo es un cliente HTTP "tonto" (POST + JSON); el cálculo, la QA,
// el criterio EC y la firma viven en el servicio PRIVADO. Mover la frontera aquí es
// lo que la decisión del hilo V3-CONEXIÓN aprobó (productor PyNite provisional).
//
// Las DOS LLAVES viajan como `state` en el ResultGroup: el visor nunca pinta verde
// lo que no sea `verified-signed` (lo acuña /sign).
import type { Combination, ResultGroup, StructuralModel } from "@aqyra/embed";

// URL del servicio local; configurable con `globalThis.AQYRA_CALC_URL`.
const BASE: string = (globalThis as unknown as { AQYRA_CALC_URL?: string }).AQYRA_CALC_URL ?? "http://127.0.0.1:8765";

export interface ServiceMeta {
  producer: string;       // p. ej. "pynite-provisional"
  provisional: boolean;   // productor provisional (PyNite) en lugar de motor-fem
  independent: boolean;   // ¿es la 2.ª llave (QA) independiente del productor?
  warning: string;        // aviso de gobierno (vacío si no aplica)
}
export interface GroupSummary {
  combinationId: string;
  state: string;
  atLimit: number;
  atLimitIds: string[];
  notPassing: number;
  notPassingIds: string[];
}
export interface SolveResponse {
  groups: ResultGroup[];
  summary: GroupSummary[];
  meta: ServiceMeta;
}
export interface QaResponse {
  verdict: "qa-passed" | "qa-fail";
  report: { verdict: string; equilibrium_ok: boolean; discrepancies: string[]; detail: Record<string, unknown> };
  group: ResultGroup | null;   // null = bloqueo (qa-fail): nada que elevar
  meta: ServiceMeta;
}
export interface SignResponse {
  group: ResultGroup;          // verified-signed
  record: { signer: string; timestamp: string; combinationId: string; resultGroupId: string };
}
export interface HealthResponse {
  ok: boolean;
  pyniteAvailable: boolean;
  meta: ServiceMeta;
}

export class CalcServiceError extends Error {
  constructor(message: string, readonly status: number, readonly body: unknown) {
    super(message);
    this.name = "CalcServiceError";
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  let res: Response;
  try {
    res = await fetch(BASE + path, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
  } catch (e) {
    // Servicio caído/no arrancado: el llamador hará fallback a DEMO.
    throw new CalcServiceError(`servicio de cálculo no disponible (${BASE}${path}): ${String(e)}`, 0, null);
  }
  const data = (await res.json().catch(() => ({}))) as Record<string, unknown>;
  if (!res.ok) {
    throw new CalcServiceError(String(data.error ?? `HTTP ${res.status}`), res.status, data);
  }
  return data as T;
}

/** GET /health — para sondear si el servicio está arriba (y si PyNite está). */
export async function health(): Promise<HealthResponse> {
  const res = await fetch(BASE + "/health");
  if (!res.ok) throw new CalcServiceError(`HTTP ${res.status}`, res.status, null);
  return (await res.json()) as HealthResponse;
}

/** POST /solve — modelo → grupos `computed` (aprovechamiento EC3 ya relleno). */
export function solveModel(model: StructuralModel, combinations: Combination[] = []): Promise<SolveResponse> {
  return post<SolveResponse>("/solve", { model, combinations });
}

/** POST /qa — 1.ª llave: gate de equilibrio + QA + reconciliación. */
export function qaGroup(model: StructuralModel, combinations: Combination[], group: ResultGroup): Promise<QaResponse> {
  return post<QaResponse>("/qa", { model, combinations, group });
}

/** POST /sign — 2.ª llave (firma de JM). Exige `qa-passed` (si no, 409). */
export function signGroup(group: ResultGroup, signer: string): Promise<SignResponse> {
  return post<SignResponse>("/sign", { group, signer });
}
