# packages/core

Librería compartida, agnóstica al solver, **importada** (no copiada). Fin del espejo.

**Esqueleto en Fase 0.** Se llena en **0.5**: extraer `ifc_utils` y `grafo_red` del código
actual, retirar el espejo byte-a-byte y su guardián de hash, y hacer que los engines
importen `core`. La prueba es una golden de **no-regresión**: los adaptadores que delegan en
`core` deben reproducir byte a byte el `modelo_neutro.json` previo.

No produce ni consume contratos C-; expone una **interfaz tipada**. Ver
`../../../Aqyra-Raiz/FUNDACION_core_y_gobierno-CI.md`.
