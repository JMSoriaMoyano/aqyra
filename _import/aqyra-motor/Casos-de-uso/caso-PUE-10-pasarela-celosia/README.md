# PUE-10 — Pasarela peatonal en celosia — L=36 m, sobrecarga peatonal, confort dinamico (modal)

Caso e2e **IFC-driven** del vertical **celosia** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-10.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-10-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.584** · f1 = 3.86 Hz.

## Archivos
`PUE-10.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-10-resultados.ifc` (write-back) ·
`memoria-PUE-10.md` · `README.md`.
