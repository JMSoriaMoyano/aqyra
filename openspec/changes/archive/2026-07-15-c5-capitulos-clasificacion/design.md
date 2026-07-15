# Diseño · Capítulos por clasificación (Slice B) — decisiones D-RB-5..8

> RATIFICADAS por JM 2026-07-12. Namespace **D-RB**. Se anclan en `engines/presupuesto/DECISIONES.md`.

## D-RB-5 · Mecanismo — parámetro + tabla anclada
`parametros.estructura_capitulos ∈ {catalogo, uniclass, gubim}` (default **`catalogo`**; con default, `GOL-PRE-01..05` idénticas). Con `uniclass`/`gubim` el engine agrupa las partidas por su **grupo de clasificación** usando una **tabla código→título anclada** (`_GRUPOS_TITULO`, semilla embebida en el engine como `CAPITULOS_DEFAULT`). Se descarta derivar `criterio["capitulos"]` (gancho existente): exige declarar los capítulos a mano por pack, no auto-agrupa por la clasificación que el modelo porta.

## D-RB-6 · Nivel de agrupación Uniclass — grupo EF de 2.º nivel
Uniclass agrupa por el **grupo EF de 2.º nivel** (EF_20 estructura, EF_25 cerramientos/particiones/carpintería, EF_30 forjados): `EF_25_10 → EF_25`. Uniclass **EF** (el banco lo trae) frente a **Ss** (sistemas) = EF en v0; el nivel fino y Ss = forward.

## D-RB-7 · GuBIMClass — añadir `clasificacion_gubim` a AQ-DEMO
Se añade `clasificacion_gubim` a las 7 partidas de AQ-DEMO (aditivo, **no re-ancla el coste**: PEM/PEC intactos) para habilitar y anclar la ruta `gubim`. Códigos **DEMO representativos** (el banco ya es demo/propio); GuBIM agrupa por el **1.er segmento** (`30.30.10 → 30`). Los códigos GuBIM oficiales/completos = forward.

## D-RB-8 · Golden — `GOL-PRE-06`
Caso NUEVO `GOL-PRE-06` (`modo:"capitulos"`), que verifica para cada eje (`uniclass`, `gubim`): Σ capítulos == PEM, capítulos == grupos de clasificación, y **PEM/PEC idénticos a `GOL-PRE-01`**. `GOL-PRE-01..05` intactas.

## Costura técnica (verificada en local, sin ifcopenshell)

- **`presupuestar` es puro** (no usa ifcopenshell; solo `medir` abre el IFC). `GOL-PRE-06` LEE el **modelo pre-medido** de `GOL-PRE-01/entrada.json` + los packs anclados (criterio/AQ/v1 + banco/AQ-DEMO/v1) y presupuesta con `estructura_capitulos` en cada eje. El parser (medir) lo ancla `GOL-PRE-01`; aquí se prueba la AGRUPACIÓN.
- **El coste no se mueve**: la agrupación solo reasigna el campo `capitulo` de cada partida; los importes de partida y PEM/PEC son idénticos entre `catalogo`/`uniclass`/`gubim` (verificado: importes de partida byte a byte iguales).
- **Grupos resultantes**: uniclass = {EF_20: EHS010+CSZ010 (566,65), EF_25: FAB010+REV010+PIN010+PPM010 (2 563,83), EF_30: EHL010 (3 754,35), SIN: SYS010 (137,70)} → Σ 7 022,53. gubim = {10, 20, 30, 40, 50, SIN} → Σ 7 022,53.
- **Anclaje del banco**: como en Slice A, enriquecer `banco.json` ⇒ recomputar `md5_banco` (pack.json) + `content_sha256` (golden) + `test_packs.py` (md5 fijado). `versions.lock [packs.banco]` no guarda hash.
- **Esquema C5**: sin cambios. `partida.capitulo` y `resumen.capitulos[].codigo` ya son strings libres → EF_20 / "10" / SIN conforman.
