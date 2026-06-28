# Piloto · Decopak — Depósito enterrado

- **Tipo:** interno · **Track:** A (uso interno, prueba E2E del ecosistema)
- **Emplazamiento:** Rubí (Barcelona) — mismo que Decopak HQ.
- **Modelo:** `modelo/DepositoDecopakEnterrado.ifc` (IFC2X3, export Revit 2026, vista de coordinación).
- **Estado:** cálculo en curso (Fase 0). **Todo lo producido aquí es PROPUESTA pendiente de verificación QA independiente + firma de JM.** La IA opera; JM firma.

## Carpetas

```
modelo/             · IFC y datos de partida
calculo/            · idealización, acciones y cálculo por elemento (memoria)
qa-evidencia/       · evidencia para la QA de dos llaves (entrada→versión→norma→resultado→oráculo)
golden-candidatos/  · casos que este piloto propone a la suite golden
roi/                · registro de horas y retrabajo (unidades A2.1)
```

## Gobierno

Se ejecuta según `GOBIERNO_QA_Y_VERSIONES.md`: rol **build** (produce el cálculo);
la **verificación** la hace un agente de QA en ejecución separada con su propio oráculo.
Versiones consumidas: `versions.lock` (núcleo en `0.0.0` → **versión NO anclada**, ver evidencia).
