# Diseño · c5-banco-coste-completo (E5.1b)

## Contexto y decisiones de fondo

E5.1b materializa la **vía nativa** del coste: el código de partida ES el código BCCA. Tres restricciones lo gobiernan, verificadas en el Paso 0:

1. **`engines/bc3` 0.2.0 es INTOCABLE y su subset v0 no ingiere el `.bc3` completo limpio** (34,5 % de las 8.426 unidades no cuadran; AUX/paramétricos sin resolver). → El banco de v0 es un **subconjunto NATIVO curado** (patrón semilla), no la base completa (D53). El banco completo exige extender el parser = forward.
2. **La ruta de coste del runner ancla el criterio por el pointer `[packs.criterio]` (=AQ/v1) y el banco por id+versión exactos en `[packs.banco*]`.** → Para no romper GOL-PRE-04 (ancla `BCCA/v1`), el banco nativo va en **clave de lock NUEVA** (`banco_bcca_nativo`), no un bump de `banco_bcca` (que rompería el match por versión exacta). Y el criterio v3 se ancla **por `content_sha256`** (el pointer no se mueve), replicando el patrón que la ruta de carbono ya usa para `AQ/v2`. Ambos son 2 retoques aditivos en `run_golden.py` — el único fichero de código tocado (D54/D55).
3. **La puerta (IfcDoor) no tiene medición nativa limpia.** BCCA valora `11MPP00151` por m² de **hueco** (125,37 €/m²); el modelo neutro anclado mide la puerta como `conteo=1` y su Qto solo expone el área de **hoja** (1,845 m²), no la del hueco (2,10). → La puerta queda **fuera de v0** (D54); vuelve cuando exista la medición del hueco (forward).

## Banco `BCCA-nativo/v1` — cómo se materializa

El `.bc3` curado se construye extrayendo **verbatim** del `.bc3` original de la BCCA los registros `~C`/`~D` de las 6 unidades objetivo + los `~C` de sus básicos directos (un nivel; los básicos que en el original tienen `~D` propio se aplanan a su precio declarado, como la semilla). `ingerir_bc3(fuente, ci=0)` lo reproduce **sin avisos** (los 6 códigos cuadran exactos: 28,94 / 12,98 / 4,60 / 418,01 / 433,17 / 164,18). `banco.json` = núcleo del parser + `provenance` por partida (código BCCA = código de partida, edición, licencia CC-BY 3.0, atribución) + descripción honesta (metadatos aditivos, D52-B). El golden del parser verifica el **subconjunto presupuestable** (`codigo/unidad/componentes/costes_indirectos/precio`).

## Criterio `AQ/v3` — nativo, con capítulos propios

`v3` = las reglas de medición de `v1` para 4 clases (misma unidad, magnitud, descuento de huecos, factor de caras) pero apuntando a los **códigos BCCA nativos**. Como el catálogo `CAPITULOS_DEFAULT` del motor mapea los códigos **alias**, `v3` declara su propio bloque `capitulos` (el motor es **pack-overridable**: `criterio.get("capitulos")`), mapeando los códigos nativos a C01–C04 + C06 (sin Carpintería, C05: puerta = forward). `SYS010` (S&S por ratio, `origen=regla`) se conserva.

## GOL-PRE-05 — oráculo

Reusa las fixtures de GOL-PRE-01 (mismos md5) y su modelo neutro (la puerta sigue en el modelo, solo que `v3` no la mapea). Importes = cantidad × precio del banco nativo (HALF_UP): zapata 21,02 · pilar 831,69 · losa 6.771,76 · fábrica 981,07 · enfoscado 880,04 · pintura 311,88. PEM medible 9.797,46; S&S 2 % = 195,95; **PEM 9.993,41** → (+13 % GG 1.299,14 +6 % BI 599,60) base **11.892,15** → (+21 % IVA 2.497,35) **PEC 14.389,50**. Oráculo calculado a mano ×2 y **coincidente con el recompute del engine** (`presupuestar()` en el sandbox). El recompute completo (con `medir()` de ifcopenshell) corre en el conda `mcp-bim` de JM + gate CI.

## Alternativas descartadas

- **Banco completo tal cual** (8.426 partidas): 34,5 % no cuadra → sucio/deshonesto. **Extender el engine ahora**: rompe el guardarraíl «engine intocable», hilo mucho mayor. → subconjunto nativo curado.
- **Puerta nativa m² con área de hoja (1,845 → 231,31 €)**: semánticamente la hoja, no el hueco que BCCA factura. **Puerta con convención ud ×2,10 (263,29)**: no es nativa. → puerta = forward.
- **Bump `[packs.banco_bcca]→v2`**: rompe GOL-PRE-04 (match por versión exacta). → clave de lock nueva.

## No-regresión

Zona anclada intacta por hash: motor, adaptador, esquema, `criterio/AQ/v1+v2`, semilla `banco/BCCA/v1`, ejes carbono/pliego y sus packs/goldens. Los 2 retoques de `run_golden.py` son ramas condicionales nuevas: el camino de v1/AQ-DEMO/BCCA no cambia. Verificación sandbox: 30/30 PASS (packs, parser, esquemas, aritmética del expected). Verificación conda `mcp-bim` + CI: recompute de GOL-PRE-05 + GOL-PRE-01..04 byte-idénticas.
