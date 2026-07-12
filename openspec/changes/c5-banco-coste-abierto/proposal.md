# Cambio · Semilla REAL de coste por la VÍA LIMPIA — pack `banco/BCCA` ingerido de fuente abierta (E5.1)

> Change-id: `c5-banco-coste-abierto` · Capacidad: `presupuesto` (contrato `C5-presupuesto`)
> Historia del backlog: **E5.1** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E5.1, §3 Ola 4)
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_Ola4-dashboard.md`, 2026-07-11) + verificación de licencias 2026-07-11.
> Estado: **PROPUESTA** · decisiones **D49–D52 a ratificar** por JM (continúan D1–D48).
> Tipo: **EXTIENDE** una capacidad viva (C5) — forward-open; **AÑADE un pack nuevo**. NO se toca contrato, esquema, motor ni golden de coste/carbono/pliego existente. NO se toca el adaptador `engines/bc3` (salvo bug).
> Gobierna: **D-026/N-04** (política 3+2: la ingesta/redistribución de cada fuente pública queda supeditada a la verificación de su licencia por JM), **vía limpia** (sólo fuentes de licencia abierta ratificadas), **D-a** (semillas abiertas). Espejo estructural de **E0.1** (ingesta BC3, `c5-bc3-ingesta`) y **E5.2** (semilla carbono abierta, `c5-banco-carbono-abierto`).

## Por qué

La Ola 1 dejó el eje coste **conectado** (BC3 entra/sale, `valores{}`, cortes, `proyectar`), pero el dato de producción sigue siendo de **demostración**: `banco/AQ-DEMO/v1` y `banco/AQ-BC3-DEMO/v1` son bancos **PROPIOS/SINTÉTICOS** (D-026), con precios redactados para las golden, no de mercado.

E5.1 sustituye ese dato de demostración por una **semilla REAL**: precios descompuestos **derivados por Aqyra** de una base pública con licencia **explícitamente abierta** (BCCA — Junta de Andalucía, ≈6.600 precios, BC3 nativo), sin tocar bases licenciadas (BEDEC/CYPE/PREOC). No cambia el motor ni la forma del banco: mejora la **calidad y la trazabilidad** del precio. Cada partida pasa de "inventada" a "derivable y trazable a su fuente abierta (código BCCA + descomposición + licencia documentados)". Es exactamente el patrón que E5.2 aplicó al carbono (`generico/v1` sintético → `v2` real derivado de ADEME/ProBas/UK).

La fuente quedó **verificada y propuesta a ratificación de JM (2026-07-11)** — registro en `Aqyra-Negocio/RECONCILIACION_licencias-coste.md`:

| Fuente | Licencia | Papel |
|---|---|---|
| **BCCA — Base de Costes de la Construcción de Andalucía** (Junta de Andalucía) | Creative Commons Reconocimiento 3.0 (CC-BY 3.0), vía aviso legal del portal | **primaria** (precio unitario descompuesto) |
| **Base de Precios de Extremadura** (GOBEX) | por confirmar (sin licencia con nombre verificada) | secundaria / contraste — **NO anclar sin confirmar** |

BCCA permite a la vez **uso comercial + obra derivada + redistribución con atribución** (verificado). Atribución exigida: «Información obtenida del Portal de la Junta de Andalucía», sin logotipos/escudos, sin desnaturalizar. Excluidas por licencia (el cliente aporta): BEDEC, CYPE, PREOC, IVE.

## Qué cambia (superficie)

- **`data/packs/banco/BCCA/<version>/`** (NUEVO) — pack de coste **REAL**: las **7 partidas del criterio** (`FAB010, REV010, PIN010, EHL010, EHS010, CSZ010, PPM010`, D50/D51) con precio + descomposición (MO/material/maquinaria + indirectos) **derivadas de BCCA**, cada una con un bloque **`provenance`** (código BCCA de origen + descomposición + edición/URI + licencia). Estructura de tres ficheros como `AQ-BC3-DEMO`: `banco.json` + `pack.json` + `golden/expected.json` (`content_sha256` + md5 de `banco.json`) + `fuente/` con el `.bc3` de origen anclado (provenance auditable). id/version exacto según D50 (recomendación `banco/BCCA/v1`).
- **`versions.lock`** — fila **`[packs.banco_bcca]`** (NUEVA, espejo de `[packs.banco_bc3]`, D50). `[packs.banco]=AQ-DEMO/v1` y `[packs.banco_bc3]=AQ-BC3-DEMO/v1` **intactos**.
- **`packages/packs/tests/test_packs.py`** — golden de pack del `banco/BCCA` real (hash `content_sha256` + md5(banco.json) + md5(.bc3 fuente)) + guarda de no-regresión de los packs de coste anclados.
- **`engines/bc3/tests/`** — golden del parser: `ingerir_bc3(fuente/*.bc3)` reproduce el `banco.json` anclado (determinismo del adaptador), como `AQ-BC3-DEMO`. **El adaptador `engines/bc3` NO se toca** (se consume tal cual, 0.2.0).
- **`packages/golden/C5/GOL-PRE-04/`** (NUEVO, si D52 = Opción A) — caso ligero que valora la MISMA medición de `GOL-PRE-01` con el pack REAL BCCA por `run_case_c5` (modo coste); oráculo del PEM real calculado a mano y verificado ×2. `GOL-PRE-01/02/03` **intactas** (usan `AQ-DEMO`).
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D49–D52** (continúan D1–D48).

## Impacto — por qué NO rompe nada (forward-open verificable)

- **El motor no se toca.** `engines/presupuesto` 0.5.0 ya consume cualquier `banco` con la forma de `AQ-DEMO` (D1–D5); un banco de coste nuevo se consume **sin bump de engine**.
- **El adaptador `engines/bc3` no se toca.** `ingerir_bc3` (0.2.0, D30–D33) ya materializa `.bc3 → banco.json` de forma determinista; E5.1 lo **usa**, no lo modifica.
- **El esquema de entrada/salida C5 no se mueve.** El pack real usa la forma exacta de `AQ-DEMO` (`partidas[].{codigo,unidad,descripcion,componentes[],costes_indirectos,precio}`). `schema_version` intacto.
- **`AQ-DEMO/v1`, `AQ-BC3-DEMO/v1` y todos los packs anclados intactos** (identidad por hash). E5.1 **AÑADE** un pack; no reescribe los de demostración (los usan `GOL-PRE-01/02/03`, `GOL-CAR-01/02`, `GOL-DOC-01`, `GOL-PLI-01`).
- **`GOL-PRE-01/02/03`, `GOL-CAR-01/02`, `GOL-DOC-01`, `GOL-PLI-01` byte-idénticas.** El eje coste de las golden ancladas sigue en `AQ-DEMO`; `GOL-PRE-04` (si D52=A) es un caso NUEVO con el banco real.
- **El coste sigue siendo traducción determinista.** Mismo modelo + criterio + banco → misma salida; el precio es convención banco+criterio, **pero ahora cada partida es DERIVABLE y TRAZABLE** a su fuente abierta (código BCCA + descomposición + licencia).

## Fuera de alcance (fronteras honestas)

- **No** se reempaquetan BEDEC/CYPE/PREOC/IVE (licenciados; el cliente aporta). **No** se ancla nada de Extremadura sin confirmar su licencia (queda como contraste/forward).
- **No** entra la **base BCCA completa** (≈6.600 precios con códigos nativos): eso exige un criterio que mapee clases IFC → códigos nativos BCCA (`criterio` nuevo), y es **gancho forward** (D51). v0 = las 7 partidas del criterio con precio REAL BCCA + provenance.
- **No** se toca el eje carbono, ni el pliego, ni el motor, ni el adaptador BC3, ni el esquema, ni las golden ancladas.
- **No** se construye el dashboard (E6.1 — change hermano `visor-dashboard-valor`, mismo hilo).
- **Sin release** salvo que JM lo decida. Git por `.bat` en el host; merge/firma = JM (Llave 2).
