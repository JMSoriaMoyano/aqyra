# ROI — Depósito enterrado Decopak (unidades A2.1)

Registro de horas y retrabajo del flujo IFC → cálculo. **Métrica estrella A2.1: coste marginal N+1.**

## Sesión 2026-06-24 · cálculo end-to-end (productor)

| Bloque | Esfuerzo (IA) | Retrabajo / nota |
|---|---|---|
| Lectura README + gobierno + geotecnia HQ | bajo | reutilizado de HQ (datum, UG2/UG3, freático, sismo) |
| Parseo + validación IFC (ifcopenshell) | medio | 1 hallazgo: 20 cm = muretes, no compartimentación |
| Idealización + bases de acciones | medio | 1 consulta a JM (tráfico/esquema/freático) |
| Motor de cálculo (FE + Winkler) | medio | 1 retrabajo: raft mal idealizado (losa suspendida) → corregido a Winkler |
| Memoria + evidencia QA + golden | medio | — |
| **Incidencia de entorno** | — | disco lleno truncó un script (recuperado en disco local) |

## Coste marginal estimado del siguiente depósito análogo (N+1)
- Geometría y bases **reutilizables** (mismo emplazamiento, misma tipología) → el grueso del coste
  es la **idealización + autoría de acciones**, ya plantillada en `calc_deposito.py`.
- Estimación: **N+1 ≈ 30–40 % del coste de este primero** si el IFC llega con la misma estructura.
- Multiplicador del foso: cada caso verde (golden G-DEP-01..04) reduce el coste de QA del siguiente.

*(Horas absolutas a cumplimentar por JM según su instrumentación A2.1.)*
