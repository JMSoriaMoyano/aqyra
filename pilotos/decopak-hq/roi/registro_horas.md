# Decopak HQ — Registro de ROI (horas y retrabajo)

Unidades A2.1: *comprobación por elemento* y *memoria de cálculo*. Registrar coste marginal del N+1.

| Fecha | Fase | Unidad A2.1 | Esfuerzo IA | Retrabajo | Nota |
|---|---|---|---|---|---|
| 2026-06-24 | Pre-cálculo | — | Validación IFC + hipótesis acciones + plan | — | Paquete previo a la puerta de aprobación de JM. |
| 2026-06-24 | Cálculo | Comprobación por elemento (A–F) | Predimensionado estructura completa (CLT, acero, muros, cimentación, sismo) por fórmulas EC + parser STEP; 1 agente orquestador | Reinterpretación modelo costilla (S-A2) | Vía numpy/cerrada (motor FEM no instalable en sandbox: pip>45s, /sessions lleno). FEM real queda para QA. |
| 2026-06-24 | Cálculo | Memoria de cálculo | Memoria consolidada + 6 fichas golden + verificación independiente del montante (build) | — | Marcado PROPUESTA pendiente QA + firma. |

> Se completará al ejecutar el cálculo (horas por elemento, nº de iteraciones, retrabajo por fallo de QA).
