# engines/presupuesto — DECISIONES

> El **engine C5** (`presupuestar(modelo, criterio, banco, parametros) → salida-presupuesto`). La
> medición NACE del modelo (`medir`, D7); el criterio es un PACK anclado (primitivas finitas, D8).
> Contract-first: reproduce `GOL-PRE-01` (PEM 7 022,53 → PEC 10 111,74). Las decisiones fundacionales
> D6–D10 (adopción del engine) y las de ejes/proyección/carbono viven en el contrato C5
> (`packages/contracts/C5-presupuesto/DECISIONES.md`). Aquí se anclan las decisiones **D-RB** del hilo
> *presupuesto/pliego ricos* que tocan el motor. La IA propone; JM ratifica y firma (dos llaves).

---

# CAPÍTULOS POR CLASIFICACIÓN — Slice B (D-RB-5..8, RATIFICADAS por JM 2026-07-12)

> El presupuesto puede estructurarse por la **clasificación que el modelo ya porta** (Uniclass EF /
> GuBIMClass) en vez de por el catálogo del engine. Extensión ADITIVA forward-open; el **coste anclado
> NO se mueve** (solo se reagrupan las mismas partidas).

## D-RB-5 · Mecanismo — parámetro + tabla anclada
`parametros.estructura_capitulos ∈ {catalogo, uniclass, gubim}` (default **`catalogo`**; con default,
salida byte-idéntica → `GOL-PRE-01..05` intactas). Con `uniclass`/`gubim`, `_catalogo_por_clasificacion`
agrupa las partidas por su **grupo de clasificación** con una tabla código→título **embebida y anclada**
(`_GRUPOS_TITULO`, como `CAPITULOS_DEFAULT`). Se descarta derivar `criterio["capitulos"]` (no auto-agrupa).

## D-RB-6 · Nivel Uniclass — grupo EF de 2.º nivel
Uniclass agrupa por el **grupo EF de 2.º nivel** (EF_20/EF_25/EF_30): `EF_25_10 → EF_25`. El nivel fino y
el eje **Ss** (sistemas) = forward.

## D-RB-7 · GuBIMClass — `clasificacion_gubim` en AQ-DEMO
Se añade `clasificacion_gubim` a las 7 partidas de AQ-DEMO (aditivo, **no re-ancla el coste**), con códigos
**DEMO representativos** (banco ya demo). GuBIM agrupa por el **1.er segmento** (`30.30.10 → 30`). Códigos
GuBIM oficiales/completos = forward.

## D-RB-8 · Golden `GOL-PRE-06`
Caso NUEVO `GOL-PRE-06` (`modo:"capitulos"`, sin ifcopenshell — LEE el modelo pre-medido de `GOL-PRE-01`):
por cada eje (`uniclass`, `gubim`) verifica Σ capítulos == PEM, capítulos == grupos de clasificación, y
**PEM/PEC idénticos a `GOL-PRE-01`**. `GOL-PRE-01..05` intactas.

## Zona anclada (frontera dura)
Slice B solo **AÑADE**: `estructura_capitulos` + `_catalogo_por_clasificacion`/`_grupo_clasif`/`_GRUPOS_TITULO`
en el engine (con default que reproduce lo anclado); `clasificacion_gubim` en `banco/AQ-DEMO/v1` (aditivo);
el caso `GOL-PRE-06` + rama `modo=capitulos` en `run_golden.py`; tests; `versions.lock` (engine 0.7.0).
**Nunca** cambia la medición (`medir`/`proyectar`), el motor económico (importe/PEM→PEC), los cuadros nº1/nº2,
el esquema C5, ni el comportamiento del modo `catalogo` (default). Engine **sin release** (política vigente).
