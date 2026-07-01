# PUE-11 — Pila alta esbelta sobre 4 pilotes — H=14 m, 2.o orden relevante, cimentacion profunda

Caso e2e **IFC-driven** del vertical **pila + apoyo + cimentacion** (PT 7.3.1). El calculo arranca de
un IFC4X3; el lector estructural reconstruye el `entrada_caso` desde la geometria real.
**Predimensionado/asistencia; revisar y firmar por ICCP.**

## Flujo
`PUE-11.ifc` → lector C1 (`ifc_to_model_estructural` + `desde_ifc`) → idealizacion →
`motor-fem` → IAP-11 → comprobacion → memoria + write-back (`PUE-11-resultados.ifc`).

## Resultado
- **VEREDICTO: CUMPLE** · aprovechamiento max **0.893** · f1 = 1.90 Hz.

## Archivos
`PUE-11.ifc` (entrada) · `entrada_caso_desde_ifc.json` (reconstruido por el lector) ·
`resultado.json` · `mapping_resultado_ifc.json` · `PUE-11-resultados.ifc` (write-back) ·
`memoria-PUE-11.md` · `README.md`.
