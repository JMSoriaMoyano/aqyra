# Golden GOL-PRE-06 — estructura de capítulos por CLASIFICACIÓN (Slice B, C5)

> Hace que el presupuesto pueda **estructurarse por la clasificación que el modelo ya porta**
> (Uniclass EF / GuBIMClass) en lugar de por el catálogo del engine. Forward de la doble
> clasificación que el modelo trae por objeto (Uniclass + GuBIM). Ratificado D-RB-5..8 (2026-07-12).

## Entrada (se LEE, no se re-ancla)
El runner (`run_case_c5`, rama `modo="capitulos"`) LEE el **modelo pre-medido** y los packs anclados de
`GOL-PRE-01` (`fuente_presupuesto`): `entrada.json` (modelo neutro) + `criterio/AQ/v1` + `banco/AQ-DEMO/v1`.
**No re-mide** (el parser lo ancla `GOL-PRE-01`): `presupuestar(...)` es puro (sin ifcopenshell). Corre el
motor con `parametros.estructura_capitulos` en cada eje declarado (`uniclass`, `gubim`).

## Qué ancla (por cada eje: uniclass, gubim)
1. el presupuesto **conforma** `salida-presupuesto.schema.json`;
2. **PEM/PEC idénticos a `GOL-PRE-01`** (7 022,53 → 10 111,74): el coste NO se mueve al reagrupar;
3. **Σ capítulos == PEM** (cada partida cae en un único capítulo);
4. los **capítulos == los grupos de clasificación esperados** (código, título, importe, partidas):
   Uniclass por grupo EF de 2.º nivel (**EF_20**, **EF_25**, **EF_30**); GuBIM por 1.er segmento
   (**10/20/30/40/50**); S&S (sin clasificación) → capítulo **SIN**;
5. **DETERMINISMO**: `presupuestar` 2× ⇒ salida idéntica.

## No-regresión
El modo **`catalogo`** (default) reproduce el presupuesto de `GOL-PRE-01` byte a byte (capítulos
C01..C06). `GOL-PRE-01..05` y `GOL-CAR-01/02` quedan intactas: la clave `estructura_capitulos` es un
parámetro nuevo con default que reproduce lo anclado; `clasificacion_gubim` se añade al banco de forma
aditiva (no re-ancla el coste; PEM/PEC intactos).

## Regla de oro
Un fallo NO se arregla aflojando la golden. Se investiga en el **engine** (`_catalogo_por_clasificacion`
/ `_grupo_clasif`). La tabla código→título es una **semilla embebida** en el engine (como
`CAPITULOS_DEFAULT`); mover a un pack `capitulos/<sistema>/vN` y el nivel fino / Uniclass Ss = forward.
