# Cambio · Capítulos por clasificación — `estructura_capitulos` (Slice B)

> Change-id: `c5-capitulos-clasificacion` · Capas: `engines/presupuesto`, `data/packs`, `packages/golden` · Toca contrato `C5-presupuesto` (aditivo)
> Historia del backlog: **Slice B** del hilo *presupuesto/pliego ricos* (A+B+C, 2026-07-12), sobre Slice A (PR #61, mergeado).
> Estado: **APPLY** · decisiones **D-RB-5..8 RATIFICADAS por JM 2026-07-12** (parámetro+tabla anclada · grupo EF 2º nivel · clasificacion_gubim en AQ-DEMO · GOL-PRE-06).
> Tipo: **extensión ADITIVA forward-open del engine C5** (un parámetro nuevo + tabla embebida). El **coste anclado NO se mueve**.

## Por qué

Al revisar el bundle de E6.2, JM detectó que los capítulos del presupuesto salen de un **catálogo fijo del engine** (C01 Cimentación … C06 S&S). El modelo ya porta la **doble clasificación Uniclass + GuBIMClass** por objeto; el presupuesto debería poder **estructurarse por esa clasificación**. Slice B lo hace sin tocar la medición ni el coste: es solo una forma distinta de **agrupar** las mismas partidas.

## Qué cambia (superficie)

- **`engines/presupuesto`** 0.6.0 → **0.7.0** — `presupuestar(...)` acepta `parametros.estructura_capitulos ∈ {catalogo, uniclass, gubim}` (default **`catalogo`** → salida byte-idéntica). Con `uniclass`/`gubim` construye el catálogo AGRUPANDO las partidas por su **grupo de clasificación** (`_catalogo_por_clasificacion` / `_grupo_clasif`): Uniclass por grupo **EF de 2.º nivel** (EF_20/EF_25/EF_30); GuBIM por **1.er segmento** (10/20/30/40/50). Tabla código→título **embebida y anclada** (`_GRUPOS_TITULO`, como `CAPITULOS_DEFAULT`). S&S y partidas alzadas (sin clasificación) → capítulo **`SIN`**.
- **`data/packs/banco/AQ-DEMO/v1/`** — cada partida gana **`clasificacion_gubim`** (D-RB-7; códigos DEMO representativos, banco ya marcado demo). Aditivo: **no re-ancla el coste** (PEM/PEC intactos). Re-anclaje del pack (`md5_banco` + `content_sha256`; `test_packs.py` md5 actualizado).
- **`packages/golden/C5/GOL-PRE-06/`** (NUEVO) — `expected.json` (`modo:"capitulos"`, `fuente_presupuesto:"GOL-PRE-01"`, `ejes:[uniclass,gubim]`) + `ficha.md` + `tolerancias.json`. Ancla por cada eje: conformidad + PEM/PEC idénticos a GOL-PRE-01 + Σ capítulos == PEM + capítulos == grupos esperados + determinismo. Corre **sin ifcopenshell** (LEE el modelo pre-medido de GOL-PRE-01 y presupuesta; `presupuestar` es puro).
- **`packages/golden/src/aqyra_golden/run_golden.py`** — rama `modo="capitulos"` (`_run_c5_capitulos`) en `run_case_c5` (patrón `documento`/`export`). Sin runner nuevo en `CASE_RUNNERS`.
- **`engines/presupuesto/tests/test_presupuesto.py`** — tests: default = catálogo; uniclass (EF); gubim; el reagrupar no mueve el coste.
- **`versions.lock`** — `engine_version` 0.7.0 + nota. **`engines/presupuesto/DECISIONES.md`** (NUEVO) — se anclan **D-RB-5..8**.

## Impacto — por qué NO rompe nada (verificado en local)

- **El coste NO se mueve.** Cada partida cae en un único capítulo ⇒ Σ capítulos == PEM; PEM 7 022,53 → PEC 10 111,74 idéntico en los tres modos. `GOL-PRE-01..05`, `GOL-CAR-01/02` intactas (usan el default `catalogo`; `clasificacion_gubim` es una clave que el default ignora).
- **El contrato C5 no se re-ancla.** `partida.capitulo` y `resumen.capitulos[].codigo` ya son strings; los códigos de grupo (EF_20, "10", SIN) conforman el esquema sin cambios.
- **Compatibilidad.** Sin `estructura_capitulos` (o `catalogo`), comportamiento idéntico al previo. Un banco sin `clasificacion_gubim` en la ruta `gubim` cae a `SIN` (no rompe).

## Fuera de alcance (forward)

- Nivel de agrupación **fino** de Uniclass y el eje **Ss** (sistemas) = forward (v0 = grupo EF).
- Mover la tabla código→título a un **pack `capitulos/<sistema>/vN`** = forward (v0 = semilla embebida, como `CAPITULOS_DEFAULT`).
- Códigos GuBIM **oficiales/completos** = forward (v0 = demo representativo en AQ-DEMO).
- **Sin release** (engine sin release desde 0.3.0, política vigente). Llave 2 (merge) = JM.
