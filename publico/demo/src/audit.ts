/**
 * Motor de AUDITORÍA BÁSICA del cebo (P1·C, hito 4 — «auditoría IFC básica»).
 *
 * Recorre el `BuildingModel` del cebo y REPORTA no-conformidades contra el primer juego
 * de reglas OpenBIM cerrado por JM (28-jun): nomenclatura `AQ-*` + doble clasificación
 * (bsDD + Uniclass). NO certifica — la auditoría prepara y propone; las dos llaves
 * (golden verde + firma de JM) deciden. Frontera C1 = CERO: es LECTURA pura, no añade
 * primitivos ni toca `alto.json`.
 *
 * ── Reglas (la «básica», sobre el MODELO del cebo) ───────────────────────────────
 *   AQ-NMB-01  Nomenclatura · formato      — todo objeto con código `AQ-…` válido.
 *   AQ-NMB-02  Nomenclatura · unicidad     — ningún código repetido en el modelo.
 *   AQ-CLS-01  Clasificación bsDD          — uriBsdd coherente con su ifcClass (==classUri).
 *   AQ-CLS-02  Clasificación Uniclass      — código Uniclass presente y coherente (==uniclassFor).
 *
 * Determinismo: mismo modelo → mismo informe (orden estable de recorrido). Golden-able.
 * La COHERENCIA estructural (host/container/nivel) y las reglas CTE (DB-SUA escalera)
 * NO entran en este slice (JM 28-jun): segundo slice. Aquí, solo OpenBIM en el cebo.
 */

import type { BuildingModel, ElementInstance } from "./model";
import { classUri } from "./bsdd";
import { uniclassFor } from "./uniclass";

export type Severity = "error" | "warning";

/** Una no-conformidad concreta (objeto + regla incumplida). */
export interface NonConformance {
  ruleId: string;     // AQ-NMB-01 | AQ-NMB-02 | AQ-CLS-01 | AQ-CLS-02
  rule: string;       // etiqueta legible de la regla
  severity: Severity; // error (incumple) | warning (revisar)
  ifcClass: string;   // clase IFC del objeto
  code: string;       // código AQ del objeto (o "—" si falta)
  message: string;    // qué falla, en claro
}

/** Informe de auditoría: recuentos + lista de no-conformidades por regla. */
export interface AuditReport {
  audited: number;                       // nº de objetos recorridos
  conformant: number;                    // objetos sin ninguna no-conformidad
  nonConformances: NonConformance[];     // todas, en orden de recorrido
  byRule: Record<string, number>;        // recuento por ruleId (incluye reglas con 0)
  ok: boolean;                           // sin no-conformidades
}

/** Catálogo de reglas de la auditoría básica (para la UI y el informe). */
export const RULES: ReadonlyArray<{ id: string; label: string }> = [
  { id: "AQ-NMB-01", label: "Nomenclatura · formato AQ-*" },
  { id: "AQ-NMB-02", label: "Nomenclatura · unicidad" },
  { id: "AQ-CLS-01", label: "Clasificación bsDD coherente" },
  { id: "AQ-CLS-02", label: "Clasificación Uniclass coherente" },
];
const RULE_LABEL: Record<string, string> = Object.fromEntries(RULES.map((r) => [r.id, r.label]));

/** Código AQ válido: prefijo AQ + uno o más segmentos [A-Z0-9] separados por guion. */
const AQ_CODE = /^AQ(?:-[A-Z0-9]+)+$/;

/** Un objeto auditable del modelo: clase IFC, código y (si es físico) el elemento. */
interface Auditable {
  ifcClass: string;
  code: string;
  element?: ElementInstance; // presente solo para IfcElement (habilita CLS-01/02)
}

/** Aplana el modelo a la lista ORDENADA de objetos auditables (recorrido determinista). */
function collect(model: BuildingModel): Auditable[] {
  const out: Auditable[] = [];
  out.push({ ifcClass: "IfcProject", code: model.project.code });
  for (const s of model.storeys) {
    out.push({ ifcClass: s.ifcClass, code: s.code });
    for (const sp of s.spaces) out.push({ ifcClass: sp.ifcClass, code: sp.code });
    for (const e of s.elements) out.push({ ifcClass: e.ifcClass, code: e.code, element: e });
  }
  for (const z of model.zones) out.push({ ifcClass: z.ifcClass, code: z.code });
  return out;
}

/**
 * Audita el modelo del cebo contra la regla básica. Determinista y de SOLO LECTURA.
 * Reporta no-conformidades; NO certifica (eso son las dos llaves).
 */
export function auditModel(model: BuildingModel): AuditReport {
  const objects = collect(model);
  const ncs: NonConformance[] = [];
  const byRule: Record<string, number> = Object.fromEntries(RULES.map((r) => [r.id, 0]));
  const seen = new Set<string>();
  const flagged = new Set<number>(); // índices de objetos con ≥1 no-conformidad

  const add = (i: number, ruleId: string, ifcClass: string, code: string, message: string, severity: Severity = "error"): void => {
    ncs.push({ ruleId, rule: RULE_LABEL[ruleId] ?? ruleId, severity, ifcClass, code: code || "—", message });
    byRule[ruleId] = (byRule[ruleId] ?? 0) + 1;
    flagged.add(i);
  };

  objects.forEach((o, i) => {
    // AQ-NMB-01 · formato del código
    if (!o.code || !AQ_CODE.test(o.code)) {
      add(i, "AQ-NMB-01", o.ifcClass, o.code, `Código «${o.code || "(vacío)"}» no respeta el patrón AQ-*.`);
    }
    // AQ-NMB-02 · unicidad (la 2.ª y siguientes apariciones son la no-conformidad)
    if (o.code) {
      if (seen.has(o.code)) add(i, "AQ-NMB-02", o.ifcClass, o.code, `Código «${o.code}» duplicado en el modelo.`);
      else seen.add(o.code);
    }
    // Clasificación: solo objetos físicos (IfcElement) llevan doble clasificación en el cebo.
    const e = o.element;
    if (e) {
      // AQ-CLS-01 · bsDD coherente con la clase
      const wantBsdd = classUri(e.ifcClass);
      if (wantBsdd) {
        if (!e.uriBsdd) add(i, "AQ-CLS-01", e.ifcClass, e.code, "Falta la URI bsDD.");
        else if (e.uriBsdd !== wantBsdd) add(i, "AQ-CLS-01", e.ifcClass, e.code, `URI bsDD incoherente con ${e.ifcClass}.`);
      }
      // AQ-CLS-02 · Uniclass coherente (solo clases que DEBEN llevarla; los huecos no)
      const wantUni = uniclassFor(e.ifcClass, e.predefinedType);
      if (wantUni) {
        if (!e.uniclass) add(i, "AQ-CLS-02", e.ifcClass, e.code, "Falta el código Uniclass 2015.");
        else if (e.uniclass.code !== wantUni.code || e.uniclass.uri !== wantUni.uri) {
          add(i, "AQ-CLS-02", e.ifcClass, e.code, `Código Uniclass «${e.uniclass.code}» incoherente con ${e.ifcClass} (esperado ${wantUni.code}).`);
        }
      }
    }
  });

  return {
    audited: objects.length,
    conformant: objects.length - flagged.size,
    nonConformances: ncs,
    byRule,
    ok: ncs.length === 0,
  };
}
