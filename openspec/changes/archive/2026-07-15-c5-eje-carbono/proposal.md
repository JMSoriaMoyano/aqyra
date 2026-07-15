# Cambio · Eje CARBONO en C5 — `valores.carbono` + etapas + pack `banco-carbono` + `GOL-CAR-01` (E3)

> Change-id: `c5-eje-carbono` · Capacidad: `presupuesto` (contrato `C5-presupuesto`) · **abre la Ola 2**
> Historia del backlog: **E3.1 + E3.2 + E3.3** (`Aqyra-Negocio/BACKLOG_motor-valoracion_para-Aqyra-Raiz.md` §2·E3, §3 Ola 2)
> Procedencia: handoff negocio → desarrollo (`INICIO-hilo_Aqyra-Raiz_motor-valoracion_Ola2-carbono.md`, 2026-07-09)
> Estado: **PROPUESTA** · decisiones **D39–D44 ratificadas** por JM (2026-07-09).
> Tipo: **EXTIENDE** una capacidad viva (C5) — forward-open, no se crea contrato nuevo (D-b / N-03, Opción A).
> Gobierna: **D-025/N-03** (carbono = extensión de C5), **D-027/N-05** (genéricos v0 + EPD premium), **D-026/N-04** (política 3+2: el banco-carbono v0 es PROPIO/sintético; las semillas reales Ökobaudat/INIES esperan a la verificación de licencia por JM = E5.2, fuera de alcance).

## Por qué

La huella de carbono embebido comparte **exactamente la misma tubería** que el coste: *objeto → `Qto` →
factor de un banco versionado → valor firmable*. El mapeo objeto→partida del criterio **no cambia**; lo
único distinto es que el banco devuelve **kgCO₂e con etapas A1–A3/A4–A5 (EN 15978)** en vez de €. Un motor,
varios ejes. Es el diferenciador ESG con calendario legal (CPR ene-2026; GWP obligatorio para edificios
nuevos >1.000 m² en 2028 y todos en 2030; futuro CTE DB-SA).

La Ola 1 ya dejó casi todo hecho: `valores.carbono` **ya cabe** en la salida C5 (E1.1/D16–D18, con la forma
de `etapas` fijada); el motor **ya rellena** `valores[eje]` etiquetado con unidad + banco para un eje
no-coste (E1.2/D19); `proyectar` **ya lee** `valores[eje].total` → la **proyección de carbono sale gratis**
(E2.2). Este cambio entrega el **núcleo de la Ola 2** con la mínima superficie nueva posible.

## Qué cambia (superficie)

- **`data/packs/pack.schema.json`** — el enum `familia` gana **`banco-carbono`** (aditivo, junto a
  `codigos/normativa/banco/criterio/ids`). `packages/packs/src/aqyra_packs/__init__.py`: el set `FAMILIAS`
  gana `banco-carbono`.
- **`data/packs/banco-carbono/generico/v1/`** (NUEVO) — pack **PROPIO/sintético** (D-026): factores kgCO₂e
  por **código de partida** con desglose por etapas `A1A3`/`A4A5`, alineado en **forma** con EN 15804 /
  Level(s) (NO copiado de Ökobaudat/INIES — eso es E5.2). `banco.json` + `pack.json` + `golden/expected.json`
  (`content_sha256` + md5 del `banco.json`). Fila nueva **`[packs.banco_carbono]`** en `versions.lock`.
- **`engines/presupuesto/`** (0.4.0 → **0.5.0**, aditivo) — el motor, para un eje no-coste, EMITE
  `valores[eje].etapas` repartiendo el factor del banco por etapas (D40) con invariante **Σ etapas = total**.
  `medir`/`presupuestar` (coste)/`escribir_coste`/`proyectar` **intactos** para el eje coste.
- **`packages/golden/C5/GOL-CAR-01/`** (NUEVO) — la Llave 1 del hilo: valora la MISMA medición de
  `GOL-PRE-01` (sobre las fixtures aumentadas de `GOL-PRE-03` + `criterio/AQ/v2`, D44) en el eje carbono →
  `valores.carbono` por partida (unitario × cantidad = total, `etapas` A1A3/A4A5, Σ etapas = total) + un
  resumen del eje + una **proyección de carbono** por un corte (reusa `proyectar`, invariante Σ). Oráculo
  calculado a mano y verificado ×2.
- **`packages/golden/src/aqyra_golden/run_golden.py`** — rama de modo **`_run_c5_carbono`** (dispatch por
  `expected.modo == "carbono"` dentro de `run_case_c5`, como 5d/documento/proyección; D43).
- **`packages/contracts/C5-presupuesto/DECISIONES.md`** — se anclan **D39–D44** (continúan D1–D38).
  `contrato.md`: nota aditiva del eje carbono. **El esquema de SALIDA C5 NO se toca** (D18 ya fijó la forma).

## Impacto — por qué NO rompe nada (forward-open verificable)

- **El esquema de salida C5 no se mueve.** `valores.carbono` + `etapas` ya caben (E1.1/D16–D18); verificado:
  la salida de carbono **conforma `salida-presupuesto.schema.json` sin editarlo**. `schema_version` intacto.
- **`GOL-PRE-01` byte-idéntica.** El run de coste sigue sin emitir `valores` (D16/D19) → PEM 7 022,53 → PEC
  10 111,74 intactos; el `expected` no se toca. `GOL-PRE-02`/`GOL-PRE-03`/`GOL-DOC-01` **intactas** (E3 sólo
  AÑADE `GOL-CAR-01`).
- **Packs anclados intactos.** `criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1` no se tocan
  (identidad por hash). `data/packs` sólo crece bajo `banco-carbono/`.
- **El carbono es traducción determinista, no cálculo.** El kgCO₂e sale del factor del banco-carbono anclado
  (mismo modelo + criterio + banco-carbono → misma salida); el invariante Σ etapas = total se comprueba. El
  kgCO₂e es convención banco+criterio, **no verdad física** (mismo estatuto que el PEM).

## Fuera de alcance (fronteras honestas)

- **No** se siembran las bases reales (Ökobaudat/INIES/EC3) → **E5.2**, tras la verificación de licencia por
  JM (D-026). El banco-carbono v0 es PROPIO/sintético.
- **No** entran las EPD/DAP verificadas (`banco-carbono/epd/vN`, capa premium, N-05) ni la clave de
  trazabilidad `epd`/`generico` en la salida (diferida, D42: el `banco` ref ya la traza).
- **No** el pliego firmable (E4, Ola 3) ni el dashboard (E6, Ola 4) ni el write-back 6D del carbono al IFC.
- **Sin release** salvo que JM lo decida. El git va por `.bat` en el host; el merge/firma es de JM (Llave 2).
