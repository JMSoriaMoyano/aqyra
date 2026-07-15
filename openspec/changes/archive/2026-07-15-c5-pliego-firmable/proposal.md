# Cambio · Pliego contractual firmable — consumidor `pliego-obra` (Slice C)

> Change-id: `c5-pliego-firmable` · Capa: `documentos/export` (+ `packages/golden`) · NO toca contrato ni motor
> Historia del backlog: **Slice C** del hilo *presupuesto/pliego ricos* (A+B+C, 2026-07-12), sobre Slices A (PR #61) y B (PR #62), ambos mergeados en `main` (HEAD `0e832bd`).
> Estado: **APPLY** · decisiones **D-PL-1..3 RATIFICADAS por JM 2026-07-12**.
> Tipo: **extension ADITIVA forward-open del rail de export** (registrar un consumidor nuevo). NO toca el nucleo (manifiesto/firma/sellado) ni el compositor de pliego.

## Por que

El conjunto contractual firmable tiene dos piezas: el **presupuesto** (E6.2/PR #60, consumidor `presupuesto-obra`) ya es firmable por el rail de export; el **pliego** ya se **compone** (`documentos/pliego.componer_pliego`, golden `GOL-PLI-01`) pero **no es firmable**. Slice C lo cierra: hace firmable el pliego por el **MISMO rail** que ya firma el presupuesto, **envolviendo** el compositor que ya existe (no re-renderiza) y anadiendole el manifiesto de procedencia + sellado que faltan.

## Que cambia (superficie)

- **`documentos/export/src/aqyra_documento_export/pliego_doc.py`** (NUEVO, espejo de `presupuesto_doc.py`) — consumidor `pliego-obra`: `pliego_word` (ENVUELVE `componer_pliego`, leyendo `criterio` + `pack_textos` de la clave forward-open `descriptor["pliego"]`) + `pliego_pdf` (sellado: por partida prescripcion + medicion trazable + coste + GUIDs + carbono forward-open + cuadro de trazabilidad + manifiesto embebido) + `FORMATOS = {word, pdf}`. **Sin BC3 ni XLSX** (el `~T` del BC3 del presupuesto ya transporta la prescripcion).
- **`documentos/export/src/aqyra_documento_export/export.py`** (+`__init__.py`) — registra `"pliego-obra": PL.FORMATOS` en `_CONSUMIDORES` (import `pliego_doc as PL`). El nucleo (`componer_export`/manifiesto/firma/sellado) **no cambia**.
- **`packages/golden/C5/GOL-EXP-03/`** (NUEVO) — `expected.json` (`modo:"export"`, `consumidor:"pliego-obra"`, `fuente_presupuesto:"GOL-PRE-01"`, descriptor con `pliego={criterio_ref: AQ/v2, pack_textos_ref: pliego-textos/AQ-DEMO/v1}`) + `ficha.md` + `tolerancias.json`.
- **`packages/golden/src/aqyra_golden/run_golden.py`** — en `_run_c5_export`, despacho `consumidor=="pliego-obra"` -> `_run_export_pliego` (espejo de `_run_export_presupuesto` con las comprobaciones del pliego). Sin runner nuevo en `CASE_RUNNERS`.
- **`documentos/export/DECISIONES.md`** — se anclan **D-PL-1..3** (namespace D-PL). **`versions.lock [documentos.export]`** — nota del consumidor + GOL-EXP-03.

## Impacto — por que NO rompe nada (verificado en local, sin ifcopenshell)

- **No-regresion `GOL-PLI-01`** (VERDE): el compositor `componer_pliego` **no cambia** su comportamiento; el Word del bundle es su .docx.
- **No-regresion `GOL-EXP-01`** (VERDE, 13 checks) y `GOL-EXP-02`: el rail del presupuesto/proyeccion es indiferente a registrar un consumidor nuevo. `pliego_doc` solo depende de `documentos/comun` a nivel de modulo (imports del pliego/fpdf **perezosos**): el paquete importa aunque el pliego no este en el path.
- **Contract-first / forward-open**: el descriptor gana la clave `pliego` (aditiva; `descriptor-export.schema.json` es abierto). El nucleo sigue vertical-agnostico.
- **Consulta, no calculo**: el consumidor LEE el `salida-presupuesto` anclado + criterio + pack_textos; no re-mide ni re-valora.

## Fuera de alcance (forward)

- Firma cualificada/PAdES del cliente y textos normativos reales (PG-3/CTE, gated N-04) = forward.
- **Sin release nuevo** (D-PL-3): lo cubre `documento-export-v0.1.0`; el bump lo decide JM. Llave 2 (merge/firma) = JM.
