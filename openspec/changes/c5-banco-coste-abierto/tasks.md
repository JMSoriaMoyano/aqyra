# Tareas · Semilla REAL de coste por la vía limpia (E5.1) — `c5-banco-coste-abierto`

> Gobernado por `docs/PROCESO_SDD.md`. **EXTIENDE** C5 (forward-open); **AÑADE un pack**. Delta de spec NULO
> (el esquema no cambia). Zona anclada intocable: motor (`engines/presupuesto` 0.5.0), adaptador
> (`engines/bc3` 0.2.0), esquema de entrada/salida C5, `GOL-PRE-01/02/03`, `GOL-CAR-01/02`, `GOL-DOC-01`,
> `GOL-PLI-01`, packs `criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1`,
> `banco-carbono/generico/v1`+`v2`, `pliego-textos/AQ-DEMO/v1` (identidad por hash). El contrato C5 está en la
> frontera CODEOWNERS → el merge es firma de JM (Llave 2). Gobierna **D-026/N-04** (vía limpia: sólo fuentes de
> licencia abierta ratificadas; BEDEC/CYPE/PREOC/IVE FUERA; Extremadura por confirmar).

## Paso 0 · Ratificación (BLOQUEA el código)
- [ ] JM ratifica la **fuente abierta + licencia** (D49): **BCCA** (CC-BY 3.0 vía portal) como primaria;
      Extremadura por confirmar (fuera de v0 salvo confirmación). Registro en
      `Aqyra-Negocio/RECONCILIACION_licencias-coste.md`.
- [ ] JM ratifica **D50** (id/version del pack + fila `versions.lock`). Recomendación: A (`banco/BCCA/v1`,
      `[packs.banco_bcca]`).
- [ ] JM ratifica **D51** (alcance: 7 partidas del criterio con precio REAL BCCA + `provenance`, vs base
      completa con criterio nativo). Recomendación: A (7 partidas, criterio intacto; base completa = forward).
- [ ] JM ratifica **D52** (golden: A = pack + parser + `GOL-PRE-04`, o B = pack + parser). Recomendación: A.
- [ ] Anclar **D49–D52** en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D48). — en este PR

## Paso 1 · Rama (primero, tras ratificar) — host
- [ ] Crear y cambiar a `feat/c5-banco-coste-abierto` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Consulta y derivación de precios (apply, texto puro) — la sustancia de E5.1
- [ ] Para cada una de las 7 partidas del criterio (`FAB010, REV010, PIN010, EHL010, EHS010, CSZ010, PPM010`):
      localizar la **unidad de obra equivalente en la BCCA ratificada**, registrar su **código BCCA de origen**,
      su **descomposición** (MO/material/maquinaria + rendimientos + precios) y su **precio**. Registrar
      fuente + licencia + edición/URI de cada uno.
- [ ] Componer el **`.bc3` semilla** (`fuente/*.bc3`, FIEBDC-3/2024, subset `~V/~C/~D/~T`) con esas 7 unidades
      recodificadas a los 7 códigos del criterio (provenance auditable, patrón `AQ-BC3-DEMO/fuente/muestra.bc3`).
- [ ] `engines/bc3/tests/` (o `packages/packs/tests`): unit-test texto puro que verifica
      `ingerir_bc3(fuente/*.bc3)` reproduce el `banco.json` anclado byte a byte (determinismo del adaptador).

## Paso 3 · Pack `banco/BCCA` real (contract-first) — apply
- [ ] `data/packs/banco/BCCA/<version>/banco.json` — 7 partidas con `componentes` + `costes_indirectos` +
      `precio` (forma de `AQ-DEMO`) + bloque **`provenance`** por partida (código BCCA, licencia, atribución,
      edición/URI). Materializado por `ingerir_bc3` del `.bc3` semilla (determinista). id/version según D50.
- [ ] `.../pack.json` — manifiesto (`familia:"banco"`, `id:"BCCA"`, `fuente` = «derivado de BCCA — CC-BY 3.0 —
      Información obtenida del Portal de la Junta de Andalucía», `contenido` con `md5_banco` + `md5_bc3` +
      `partidas` + `moneda:"EUR"` + `costes_indirectos_pct`).
- [ ] `.../fuente/*.bc3` — el `.bc3` semilla anclado (provenance).
- [ ] `.../golden/expected.json` — `content_sha256` (sha256 del bloque `contenido`) + md5(banco.json) + md5(.bc3).
- [ ] `versions.lock`: fila `[packs.banco_bcca]` según D50 (`[packs.banco]`, `[packs.banco_bc3]` intactos).
- [ ] `packages/packs/tests/test_packs.py`: golden de pack del `banco/BCCA` real (hash + md5×2) + guarda de que
      `AQ-DEMO/v1`, `AQ-BC3-DEMO/v1` y los packs anclados de coste **no se mueven**.

## Paso 4 · Golden `GOL-PRE-04` (si D52 = Opción A) — apply
- [ ] `packages/golden/C5/GOL-PRE-04/{entrada.json, expected.json, ficha.md, tolerancias.json}` — reusa las
      fixtures de `GOL-PRE-01` (`entradas_md5`) + `criterio/AQ/v1` + el pack REAL BCCA, `parametros.eje="coste"`.
      `expected.modo="coste"`; PEM/PEC reales (oráculo a mano ×2) + ≥1 proyección de coste. `GOL-PRE-01/02/03`
      **intactas**.
- [ ] `run_golden.py`: si el runner hardcodea el `banco_ref`, GENERALIZAR para leerlo del caso (servir
      `AQ-DEMO` **y** `BCCA`). Único fichero de código tocado; `GOL-PRE-01/02/03` siguen verdes.

## Paso 5 · Anclaje de decisiones + registro — apply
- [ ] `DECISIONES.md`: **D49–D52** (continúan D1–D48). `contrato.md`: nota aditiva del banco de coste real (si
      procede). Referencia cruzada a `RECONCILIACION_licencias-coste.md`.

## Paso 6 · No-regresión + verificación local (conda `mcp-bim`)
- [ ] Sandbox (texto puro): `pytest packages/packs/tests/test_packs.py` + el test del parser (`ingerir_bc3`) +
      conformidad de esquema del pack.
- [ ] Conda `mcp-bim` (ifcopenshell) — sólo si D52 = A: `pytest packages/golden` → `GOL-PRE-04` verde y
      `GOL-PRE-01/02/03` + `GOL-CAR-01/02` + `GOL-DOC-01` + `GOL-PLI-01` byte-idénticas/intactas.
- [ ] Verificar por md5 del host: `banco/AQ-DEMO/v1/banco.json` = `d63c5f4a…`; `banco/AQ-BC3-DEMO/v1/banco.json`
      = `3d6c7949…`; golden de coste intactas; esquema C5 sin tocar; motor y adaptador sin tocar.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-banco-coste-abierto`: pack conforma; `AQ-DEMO`/`AQ-BC3-DEMO`/golden de coste
      intactos; sólo `banco/BCCA` en `data/packs`; motor/adaptador/esquema/criterio sin tocar; secretos fuera
      del staged (el `.bc3` fuente es dato abierto de licencia verificada, no secreto).
- [ ] `opsx:archive` → **PR** `feat/c5-banco-coste-abierto` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release** (salvo decisión de JM).

## Fuera de estas tareas
- Reempaquetar BEDEC/CYPE/PREOC/IVE (el cliente aporta licencia) · anclar Extremadura sin confirmar su licencia
  · la base BCCA completa con `criterio` nativo (forward, D51) · tocar el eje carbono / el pliego / el motor /
  el adaptador BC3 / el esquema / las golden ancladas · el dashboard (E6.1, change hermano `visor-dashboard-valor`).
