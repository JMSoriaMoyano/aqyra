# Cambio · Coste REAL NATIVO — pack `banco/BCCA-nativo` (códigos BCCA) + `criterio/AQ/v3` (E5.1b)

> Change-id: `c5-banco-coste-completo` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E5.1b** — forward explícito de **E5.1/D51** (semilla REAL de coste, PR #58 mergeado 2026-07-12).
> Procedencia: handoff negocio → desarrollo (`Aqyra-Negocio/INICIO-hilo_Aqyra-Raiz_motor-valoracion_E5.1b-BCCA-completa-criterio-nativo.md`, 2026-07-12).
> Estado: **PROPUESTA** · decisiones **D53–D55 RATIFICADAS por JM (2026-07-12)** (continúan D1–D52).
> Tipo: **EXTIENDE** una capacidad viva (C5) — forward-open; **AÑADE** un pack de banco nuevo + un pack de criterio nuevo + un golden nuevo. NO se toca contrato, esquema, motor (`engines/presupuesto`) ni adaptador (`engines/bc3`). El único fichero de código tocado es el runner de golden.

## Por qué

E5.1 dejó el coste REAL, pero **recodificado**: la semilla `banco/BCCA/v1` guarda las 7 unidades BCCA bajo los **códigos alias del criterio** (`FAB010`…), con el código BCCA real relegado a `provenance`. E5.1b ejecuta el gancho forward de D51: el precio **deja de ser «alias del criterio» y pasa a ser «la unidad de obra BCCA nativa»** — el código de partida ES el código BCCA (`06LPC80000`…), trazable sin capa de traducción.

## Hallazgo que acota el alcance (Paso 0)

Ingerir el `.bc3` **completo** de la BCCA (`BCCA2023_V02`, ~6.600 precios) con `aqyra_bc3.ingerir_bc3` produce **8.426 partidas pero el 34,5 % no cuadra** (precio recompuesto ≠ declarado) y 845 quedan sin componentes: el fichero completo usa registros FIEBDC (`AUX#`, paramétricos, coeficientes) que el subset v0 del parser (`~V/~C/~D/~T`, un nivel) no resuelve. Un banco **completo limpio exigiría EXTENDER `engines/bc3`**, que es INTOCABLE por guardarraíl. Por tanto el v0 honesto es un **subconjunto NATIVO curado** (patrón semilla, engine intocable); la base completa queda como forward caracterizado.

## Qué cambia (superficie)

- **`data/packs/banco/BCCA-nativo/v1/`** (NUEVO) — pack de coste REAL **NATIVO**: 6 unidades de obra BCCA (`06LPC80000, 10CEE00001, 13IPP90016, 05HRL80010, 05HRP80010, 03HRZ80000`) con su **código BCCA nativo** como código de partida, precio + descomposición REALES + `provenance` por partida. Tres ficheros como `BCCA/v1`: `banco.json` + `pack.json` + `golden/expected.json` + `fuente/BCCA-nativo.bc3` (curado, aplanado sin AUX, anclado). D53.
- **`data/packs/criterio/AQ/v3/`** (NUEVO) — criterio **nativo**: mapea IfcWall/IfcSlab/IfcColumn/IfcFooting a los códigos BCCA nativos con la MISMA medición que v1, + catálogo `capitulos` nativo (pack-overridable). `v1`/`v2` INTACTOS; `[packs.criterio]` sigue en v1; v3 se ancla por su `content_sha256`. D54.
- **`versions.lock`** — fila **`[packs.banco_bcca_nativo]`** (NUEVA). `[packs.banco]`, `[packs.banco_bc3]`, `[packs.banco_bcca]=BCCA/v1` (semilla) **intactos**.
- **`packages/golden/C5/GOL-PRE-05/`** (NUEVO) — valora la MISMA medición de `GOL-PRE-01` con `criterio/AQ/v3` + `banco/BCCA-nativo/v1` por `run_case_c5` (modo coste). Oráculo a mano ×2 (coincide con el recompute del engine): PEM **9.993,41** → base 11.892,15 → **PEC 14.389,50 EUR**. D55.
- **`packages/golden/src/aqyra_golden/run_golden.py`** — 2 retoques quirúrgicos, aditivos: (a) `_banco_anclado_en_lock` acepta la nueva clave `banco_bcca_nativo`; (b) la ruta de coste ancla un criterio que NO es el pointer (`AQ/v3`) por su `content_sha256` (patrón `AQ/v2` de la ruta de carbono). GOL-PRE-01..04 verdes.
- **`packages/packs/tests/test_packs.py`** + **`engines/bc3/tests/test_bc3.py`** — golden de pack (banco nativo + criterio v3) + golden del parser (`ingerir_bc3` reproduce el núcleo presupuestable) + guardas de no-regresión.
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D53–D55**.

## Impacto — por qué NO rompe nada

- **Motor y adaptador intactos.** `engines/presupuesto` 0.5.0 y `engines/bc3` 0.2.0 se consumen tal cual. Esquema C5 sin mover.
- **Semilla y packs anclados intactos** (identidad por hash). E5.1b AÑADE; no reescribe. La semilla `BCCA/v1` la sigue anclando `GOL-PRE-04` (por su `banco_ref` explícito, bajo `[packs.banco_bcca]`).
- **`GOL-PRE-01/02/03/04`, `GOL-CAR-01/02`, `GOL-DOC-01`, `GOL-PLI-01` byte-idénticas.** Los 2 retoques de `run_golden.py` son ramas nuevas condicionales; el camino de v1/AQ-DEMO/BCCA no cambia.
- **La puerta NO se falsea.** Se deja FUERA de v0 (D54) porque su unidad nativa BCCA (11MPP00151) es m² de hueco y el modelo neutro anclado no expone el área del hueco.

## Fuera de alcance (fronteras honestas)

- **NO** la base BCCA completa (~6.600) — exige extender `engines/bc3` al subset FIEBDC de auxiliares/paramétricos: forward.
- **NO** la puerta (11MPP00151, m² de hueco): forward (D54). **NO** el selector por propiedades del criterio (Pset), ni el eje carbono nativo BCCA: forward.
- **NO** BEDEC/CYPE/PREOC/IVE (licenciados). Extremadura fuera (licencia por confirmar).
- **Sin release** salvo decisión de JM. Git por `.bat` en el host; merge/firma = JM (Llave 2).
