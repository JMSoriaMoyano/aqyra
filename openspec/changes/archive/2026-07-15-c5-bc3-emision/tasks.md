# Tareas · Emisión `salida-presupuesto` → FIEBDC-3/2024 (`.bc3`) + round-trip (E0.2)

> Gobernado por `docs/PROCESO_SDD.md`. **ADITIVO** sobre `engines/bc3` (no toca esquema de contrato).
> La zona anclada (golden C5 + packs `criterio/AQ/v1`+`v2` + `banco/AQ-DEMO/v1` + `banco/AQ-BC3-DEMO/v1`)
> **no se mueve**. El contrato C5 está en la frontera CODEOWNERS → el merge es firma de JM (Llave 2).
> Gobierna **D-026 / N-04** (no se redistribuye ninguna base pública).

## Paso 0 · Ratificación (BLOQUEA el código) — HECHO
- [x] JM ratifica **D34** (API `emitir_bc3` + re-lector `leer_bc3_presupuesto` en `aqyra_bc3`).
- [x] JM ratifica **D35** (subset emitido `~V/~C/~D/~M/~T`; `~M` por **desglose por objeto**, línea única sin traza).
- [x] JM ratifica **D36** (charset salida **UTF-8** parametrizable a ANSI; sello de fecha determinista del `~V`).
- [x] JM ratifica **D37** (anclaje del round-trip por **identidad de importes** ±0,01 / cantidades ±0,5%; NO md5).
- [x] JM ratifica **D38** (pliego `~T` mínimo desde la descripción; gancho E4-pliego).
- [ ] Anclar D34–D38 en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D33). — en este PR

## Paso 1 · Rama (primero, tras ratificar) — PENDIENTE (host)
- [ ] Crear y cambiar a `feat/c5-bc3-emision` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Emisor + re-lector (apply — texto puro) — HECHO (verificado en sandbox)
- [x] `engines/bc3/src/aqyra_bc3/bc3.py`: `emitir_bc3` (`~V/~C/~D/~M/~T`, determinista, sello de fecha) +
      `leer_bc3_presupuesto` (reconstruye `estado_mediciones`; importe = cantidad × precio_unitario).
- [x] `__init__.py`: exporta `emitir_bc3`/`leer_bc3_presupuesto`; **versión 0.2.0**.
- [x] `cli.py`: subcomando `aqyra-bc3 emitir` (`--salida`/`--charset`/`--fecha`; desenvuelve `{presupuesto}`).
- [x] `README.md`: documenta emisión + round-trip.

## Paso 3 · Golden de round-trip (la Llave 1 de E0.2) — HECHO (verificado en sandbox, 8/8)
- [x] `engines/bc3/tests/test_emision.py`: consume `GOL-PRE-01/expected.json` (anclado), emite → re-lee →
      identidad de importes (±0,01) + cantidades (±0,5%) + PEM 7 022,53; determinismo 2×; sello de fecha =
      único no-determinismo; subset `~V/~C/~D/~M/~T`; charset ANSI; **desglose por objeto** (traza) y línea única.

## Paso 4 · Anclaje de decisiones — HECHO (en este PR)
- [x] `DECISIONES.md`: **D34–D38** (continúan D1–D33). `contrato.md`: nota en «Frontera» (emisión a `.bc3`).

## Paso 5 · No-regresión — PENDIENTE (CI)
- [x] Verificado en sandbox: E0.2 NO toca `packages/golden`, ni `entrada/salida` de C5, ni los packs
      anclados, ni `ingerir_bc3` → `GOL-PRE-01/02/03` y `GOL-DOC-01` byte-idénticas. `pytest engines/bc3` = 16 passed.
- [ ] Gate verde en CI (Llave 1): `pytest packages/packs engines/bc3` + golden C1/C5 + esquemas.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-bc3-emision`: `aqyra-bc3` importa/compila; golden C5 intacto; ningún `expected`
      alterado; ningún esquema de contrato tocado; packs anclados intactos; `ingerir_bc3` intacto.
- [ ] `opsx:archive` → **PR** `feat/c5-bc3-emision` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release** (salvo decisión de JM al cerrar la interop).

## Fuera de estas tareas
- Semillas reales BCCA/Extremadura (E5.1, tras licencia D-026) · banco-carbono (Ola 2) · pliego firmable
  (E4) · dashboard (E6) · lectura del `%CI` del BC3 (gancho forward).
