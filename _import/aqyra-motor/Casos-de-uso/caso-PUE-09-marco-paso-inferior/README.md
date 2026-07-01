# PUE-09 — Marco de paso inferior bajo terraplen — empuje K0 en reposo, 2 carriles

Caso e2e **IFC-driven** del vertical **portico/marco** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-09.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-09-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.738** · f1 = 3.16 Hz.

## Archivos
`PUE-09.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-09-resultados.ifc` (write-back) ·
`memoria-PUE-09.md` · `README.md`.
