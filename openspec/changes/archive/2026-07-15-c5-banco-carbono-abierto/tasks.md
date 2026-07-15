# Tareas · Semilla REAL de carbono por la vía limpia (E5.2) — `c5-banco-carbono-abierto`

> Gobernado por `docs/PROCESO_SDD.md`. **EXTIENDE** C5 (forward-open); **AÑADE un pack**. Delta de spec NULO
> (el esquema no cambia). Zona anclada intocable: motor (`engines/presupuesto` 0.5.0), esquema de salida C5,
> eje coste, `GOL-PRE-01/02/03`, `GOL-DOC-01`, **`GOL-CAR-01`**, packs `criterio/AQ/v1`+`v2`,
> `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1`, **`banco-carbono/generico/v1`** (identidad por hash). El contrato
> C5 está en la frontera CODEOWNERS → el merge es firma de JM (Llave 2). Gobierna **D-026/N-04** (vía limpia:
> sólo fuentes de licencia abierta ratificadas; Ökobaudat/INIES/EC3/ICE FUERA).

## Paso 0 · Ratificación (BLOQUEA el código)
- [x] JM ratifica las **fuentes abiertas** (D45): ADEME Base Empreinte (Licence Ouverte 2.0), ProBas/UBA
      (dl-de/by-2.0), UK GHG factors (OGL v3.0), USLCI (NREL, por confirmar). Registro en
      `Aqyra-Negocio/RECONCILIACION_licencias-carbono.md`. — HECHO 2026-07-10.
- [ ] JM ratifica **D46** (id/version del pack real + estatuto de `generico/v1`). Recomendación: A (`generico/v2`).
- [ ] JM ratifica **D47** (método de derivación material×factor×cantidad + bloque `provenance` por partida).
- [ ] JM ratifica **D48** (golden: A = pack + `GOL-CAR-02`, o B = sólo pack). Recomendación: A.
- [ ] Anclar **D45–D48** en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D44). — en este PR

## Paso 1 · Rama (primero, tras ratificar) — host
- [ ] Crear y cambiar a `feat/c5-banco-carbono-abierto` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Consulta y derivación de factores (apply, texto puro) — la sustancia de E5.2
- [ ] Para cada una de las 7 partidas: fijar la **composición de material por unidad** (hipótesis de despacho) y
      **consultar los factores** en las fuentes ratificadas (ADEME/ProBas A1A3; UK transporte A4; USLCI sólo con
      licencia confirmada). Registrar fuente + licencia + URI + valor de cada factor.
- [ ] Calcular `A1A3`, `A4A5` y `precio = A1A3 + A4A5` por partida (Decimal, guarda Σ etapas = precio ±0,01).
      Verificar la aritmética ×2 (oráculo del banco).
- [ ] `engines/presupuesto/tests/test_derivacion_carbono.py` (o en `packages/packs/tests`): unit-test texto puro
      que reproduce cada `precio`/`etapas` desde el `provenance` (material × factor × cantidad) — el pack no
      inventa: todo número es derivable.

## Paso 3 · Pack `banco-carbono` real (contract-first) — apply
- [ ] `data/packs/banco-carbono/<id>/<version>/banco.json` — 7 partidas con `precio` + `etapas` A1A3/A4A5 +
      **un** `componente` `tipo:"material"` (forma de D39) + bloque **`provenance`** por partida (composición,
      fuentes, licencias, cálculo). id/version según D46.
- [ ] `.../pack.json` — manifiesto (`familia:"banco-carbono"`, `fuente` = derivación abierta + atribución,
      `contenido` con `md5_banco`, `partidas`, `unidad_eje:"kgCO2e"`).
- [ ] `.../golden/expected.json` — `content_sha256` (sha256 del bloque `contenido`) + md5(banco.json).
- [ ] `versions.lock`: fila `[packs.banco_carbono]` según D46 (`generico/v1` intacto por hash).
- [ ] `packages/packs/tests/test_packs.py`: golden de pack del banco-carbono real (hash + md5) + guarda de que
      `generico/v1` y los packs de coste anclados **no se mueven**.

## Paso 4 · Golden `GOL-CAR-02` (si D48 = Opción A) — apply
- [ ] `packages/golden/C5/GOL-CAR-02/{entrada.json, expected.json, ficha.md, tolerancias.json}` — reusa las
      fixtures de `GOL-PRE-01` (`entradas_md5`) + `criterio/AQ/v1|v2` + el pack REAL, `parametros.eje="carbono"`.
      `expected.modo="carbono"`; valoración por partida (oráculo a mano ×2) + ≥1 proyección de carbono.
      `GOL-CAR-01` **intacta**.
- [ ] `run_golden.py`: GENERALIZAR `_run_c5_carbono` (leer version del `banco_ref` del caso, no hardcodear v1) para servir v1+v2. Unico fichero de codigo tocado; GOL-CAR-01 sigue verde.

## Paso 5 · Anclaje de decisiones + registro — apply
- [ ] `DECISIONES.md`: **D45–D48** (continúan D1–D44). `contrato.md`: nota aditiva del banco-carbono real (si
      procede). Referencia cruzada a `RECONCILIACION_licencias-carbono.md`.

## Paso 6 · No-regresión + verificación local (conda `mcp-bim`)
- [ ] Sandbox (texto puro): `pytest packages/packs/tests/test_packs.py` + el test de derivación + conformidad de
      esquema del pack.
- [ ] Conda `mcp-bim` (ifcopenshell) — sólo si D48 = A: `pytest packages/golden` → `GOL-CAR-02` verde y
      `GOL-PRE-01/02/03` + `GOL-DOC-01` + `GOL-CAR-01` byte-idénticas/intactas.
- [ ] Verificar por md5 del host: `banco-carbono/generico/v1/banco.json` = `47fb4787…`; `GOL-CAR-01` intacta;
      packs de coste anclados intactos; esquema de salida C5 sin tocar; motor sin tocar.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-banco-carbono-abierto`: pack conforma; `generico/v1`/`GOL-CAR-01` intactos; sólo
      `banco-carbono/<nuevo>` en `data/packs`; motor/esquema/eje-coste sin tocar; secretos fuera del staged.
- [ ] `opsx:archive` → **PR** `feat/c5-banco-carbono-abierto` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release** (salvo decisión de JM).

## Fuera de estas tareas
- Reempaquetar Ökobaudat/INIES/EC3/ICE (permiso escrito; hilo aparte) · EPD verificadas `banco-carbono/epd/vN`
  + clave `origen_factor` (N-05, premium) · pliego firmable (E4, Ola 3) · dashboard (E6, Ola 4) · tocar el eje
  coste / las golden de coste / el esquema de salida / el motor.
