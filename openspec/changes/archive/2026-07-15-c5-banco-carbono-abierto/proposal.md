# Cambio · Semilla REAL de carbono por la VÍA LIMPIA — pack `banco-carbono` derivado de fuentes abiertas (E5.2)

> Change-id: `c5-banco-carbono-abierto` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E5.2** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E5.2, §3 Ola 2)
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_E5.2-semilla-abierta.md`, 2026-07-09) + verificación de licencias 2026-07-09/2026-07-10.
> Estado: **PROPUESTA** · decisiones **D45–D48 a ratificar** por JM (continúan D1–D44).
> Tipo: **EXTIENDE** una capacidad viva (C5) — forward-open; **AÑADE un pack nuevo**. NO se toca contrato, esquema, motor ni golden de coste/carbono existente.
> Gobierna: **D-025/N-03** (carbono = extensión de C5), **D-027/N-05** (genéricos v0 + EPD premium), **D-026/N-04** (política 3+2: la ingesta/redistribución de cada fuente pública queda supeditada a la verificación de su licencia por JM), **vía limpia** (JM, opción c, 2026-07-09).

## Por qué

El núcleo del eje carbono ya está dentro (E3, PR #54): el motor `presupuestar(..., eje="carbono")` reparte etapas A1A3/A4A5 con Σ etapas = total (D40), y `proyectar` agrega el carbono por cualquier corte. Lo único que E3 dejó **de demostración** es el **dato**: `banco-carbono/generico/v1` es un banco **PROPIO/SINTÉTICO** (D-026), con factores inventados alineados sólo en *forma* con EN 15804.

E5.2 sustituye ese dato de demostración por una **semilla REAL**: factores kgCO₂e por partida **derivados por Aqyra** de fuentes con licencia **explícitamente abierta**, sin tocar Ökobaudat/INIES/EC3. No cambia el motor ni la forma: mejora la **calidad y la trazabilidad** del banco. Cada factor pasa de "inventado" a "derivable y trazable a su fuente abierta (fuente + licencia + cálculo documentados)".

Las fuentes abiertas quedaron **verificadas y ratificadas por JM (2026-07-10)** — registro en `Aqyra-Negocio/RECONCILIACION_licencias-carbono.md`:

| Fuente | Licencia | Papel |
|---|---|---|
| **ADEME Base Empreinte / Base Carbone** (FR) | Licence Ouverte / Etalab 2.0 | primaria (factor material) |
| **ProBas — Umweltbundesamt** (DE) | dl-de/by-2.0 | primaria (proceso LCA material) |
| **UK GHG Conversion Factors** (DESNZ/DEFRA) | Open Government Licence v3.0 | complemento (transporte A4, algún material) |
| **USLCI — NREL / Federal LCA Commons** (US) | dominio público probable (por confirmar dataset a dataset) | secundaria / contraste |

Las tres primeras permiten a la vez **uso comercial + obra derivada + redistribución con atribución** (verificado). La cuarta se usa sólo como contraste, con su licencia confirmada antes de anclar cualquier factor de ella. Excluidas por licencia (necesitan permiso escrito): **Ökobaudat, INIES, EC3** e **ICE Database (Bath)**.

## Qué cambia (superficie)

- **`data/packs/banco-carbono/<id>/<version>/`** (NUEVO) — pack de carbono **REAL**: 7 partidas (`FAB010, REV010, PIN010, EHL010, EHS010, CSZ010, PPM010`) con factor kgCO₂e + etapas `A1A3`/`A4A5`, **derivadas** de las fuentes abiertas ratificadas, con un bloque **`provenance` por partida** (material × factor por kg/volumen × cantidad por unidad de partida → kgCO₂e/ud; reparto A1A3/A4A5; fuente + licencia + cálculo). `banco.json` + `pack.json` + `golden/expected.json` (`content_sha256` + md5 del `banco.json`). El **id/version exacto** se ratifica (D46; recomendación `generico/v2`).
- **`versions.lock`** — fila `[packs.banco_carbono]`: actualización/coexistencia del pack real (D46). `banco-carbono/generico/v1` **intacto** (lo ancla `GOL-CAR-01`).
- **`packages/packs/tests/test_packs.py`** — golden de pack del `banco-carbono` real (hash `content_sha256` + md5(banco.json)) + guarda de no-regresión del `v1` intocable.
- **`packages/golden/C5/GOL-CAR-02/`** (NUEVO, si D48 = Opción A) — caso ligero que valora la MISMA medición de `GOL-PRE-01` con el pack REAL por el runner `_run_c5_carbono` ya existente; oráculo del eje calculado a mano y verificado ×2. `GOL-CAR-01` (sintético) **intacta**.
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D45–D48** (continúan D1–D44).

## Impacto — por qué NO rompe nada (forward-open verificable)

- **El motor no se toca.** `engines/presupuesto` 0.5.0 ya emite `valores.carbono.etapas` (D40); un banco-carbono nuevo se consume **sin bump de engine**.
- **El esquema de salida C5 no se mueve.** La forma `valores.carbono` + `etapas` + el `componente` `tipo:"material"` ya la fijó E3; el pack real usa la misma forma. `schema_version` intacto.
- **`banco-carbono/generico/v1` y `GOL-CAR-01` intactos** (identidad por hash: `banco.json` md5 `47fb4787…`, `content_sha256 44d0cd3f…`). E5.2 **AÑADE** un pack (y, si D48=A, `GOL-CAR-02`); no reescribe el sintético.
- **`GOL-PRE-01/02/03` y `GOL-DOC-01` byte-idénticas.** El eje coste no se toca; los packs anclados de coste (`criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1`) intactos.
- **El carbono sigue siendo traducción determinista.** Mismo modelo + criterio + banco-carbono → misma salida; el kgCO₂e es convención banco+criterio (estatuto del PEM), **pero ahora cada factor es DERIVABLE y TRAZABLE** a su fuente abierta.

## Fuera de alcance (fronteras honestas)

- **No** se reempaquetan Ökobaudat/INIES/EC3/ICE (necesitan permiso escrito; verificado 2026-07-09/10). Si JM quiere ir por permiso, es un hilo aparte.
- **No** entran las EPD/DAP verificadas (`banco-carbono/epd/vN`, premium N-05) ni la clave `origen_factor` (diferida, D42).
- **No** se toca el eje coste, ni las golden de coste, ni el esquema de salida, ni el motor, ni el pliego (E4) ni el dashboard (E6).
- **Sin release** salvo que JM lo decida. Git por `.bat` en el host; merge/firma = JM (Llave 2).
