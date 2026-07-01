# PUE-08 — Losa postesada ancha de un vano — 16 x 14 m, t=0,80 m, postesado biaxial

Caso e2e **IFC-driven** del vertical **losa postesada** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-08.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-08-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.999** · f1 = 5.98 Hz.

## Archivos
`PUE-08.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-08-resultados.ifc` (write-back) ·
`memoria-PUE-08.md` · `README.md`.
