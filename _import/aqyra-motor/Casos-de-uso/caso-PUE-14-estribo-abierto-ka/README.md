# PUE-14 — Estribo abierto alto con gran sobrecarga — empuje activo Ka

Caso e2e **IFC-driven** del vertical **estribo** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-14.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-14-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.999** · f1 = 0.00 Hz.

## Archivos
`PUE-14.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-14-resultados.ifc` (write-back) ·
`memoria-PUE-14.md` · `README.md`.
