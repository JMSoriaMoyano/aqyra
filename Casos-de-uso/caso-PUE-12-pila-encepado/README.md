# PUE-12 — Pila sobre encepado de 2 pilotes — cimentacion profunda en grupo (biela-tirante)

Caso e2e **IFC-driven** del vertical **pila + apoyo + cimentacion** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-12.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-12-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.563** · f1 = 4.51 Hz.

## Archivos
`PUE-12.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-12-resultados.ifc` (write-back) ·
`memoria-PUE-12.md` · `README.md`.
