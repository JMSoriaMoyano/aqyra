# PUE-07 — Paso superior de vigas artesa pretensadas — L=30 m, 5 vigas, HP-45, 2 carriles LM1

Caso e2e **IFC-driven** del vertical **vigas pretensadas (artesa)** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-07.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-07-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.807** · f1 = 2.87 Hz.

## Archivos
`PUE-07.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-07-resultados.ifc` (write-back) ·
`memoria-PUE-07.md` · `README.md`.
