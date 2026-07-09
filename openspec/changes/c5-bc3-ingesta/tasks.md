# Tareas · Ingesta FIEBDC-3/2024 (`.bc3`) → pack `banco` (E0.1)

> Gobernado por `docs/PROCESO_SDD.md`. **NUEVO** adaptador de frontera (no toca esquema de contrato).
> La zona anclada (golden C5 + packs `criterio/AQ/v1`+`v2` + `banco/AQ-DEMO/v1`) **no se mueve**. El
> contrato C5, `data/packs` y `versions.lock` están en la frontera CODEOWNERS → el merge es firma de JM
> (Llave 2). Gobierna **D-026 / N-04** (política 3+2; `.bc3` de muestra PROPIO).

## Paso 0 · Ratificación (BLOQUEA el código) — HECHO
- [x] JM ratifica **D30** (casa/API = `engines/bc3` releaseable `aqyra-bc3`; `ingerir_bc3`/`emitir_bc3`).
- [x] JM ratifica **D31** (subset v0 `~V/~C/~D/~T`; charset del `~V`→UTF-8; `~M` a E0.2; `~T` no emitido).
- [x] JM ratifica **D32** (precio = Σsub + CI(3% param) con guarda de consistencia ±0,01 vs el `~C`).
- [x] JM ratifica **D33** (pack `banco/AQ-BC3-DEMO/v1` + `[packs.banco_bc3]`; doble golden pack+parser).
- [x] Anclar D30–D33 en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D29).

## Paso 1 · Rama (primero, tras ratificar) — PENDIENTE (host)
- [ ] Crear y cambiar a `feat/c5-bc3-ingesta` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Adaptador (apply — texto puro) — HECHO (verificado en sandbox)
- [x] `engines/bc3/pyproject.toml` (`aqyra-bc3` 0.1.0, hatchling, sin dependencias, script CLI).
- [x] `engines/bc3/src/aqyra_bc3/__init__.py` (+ `bc3.py`: `ingerir_bc3`, `serializar_banco`, subset
      `~V/~C/~D/~T`, transcodificación, precio compuesto + guarda) + `cli.py` (`aqyra-bc3 ingerir`).
- [x] `engines/bc3/README.md`.

## Paso 3 · Pack de muestra (ingerido, determinista) — HECHO
- [x] `data/packs/banco/AQ-BC3-DEMO/v1/fuente/muestra.bc3` (PROPIO/sintético, cp1252, D-026).
- [x] `banco.json` REPRODUCIDO por `ingerir_bc3` (esquema AQ-DEMO; 3 partidas FAB010/REV010/EHL010).
- [x] `pack.json` (manifiesto: `content` con `md5_banco` `3d6c7949…` + `md5_bc3` `a63b456d…` + partidas).
- [x] `golden/expected.json` (`content_sha256` `9a7e4627…`).
- [x] `[packs.banco]=AQ-DEMO/v1` y su hash **intactos** (el pack BC3 va bajo su propia ruta).

## Paso 4 · Golden (la Llave 1 de E0.1) — HECHO (verificado en sandbox, 12/12)
- [x] `engines/bc3/tests/test_bc3.py`: reproduce el banco anclado, determinismo 2×, transcodificación
      ANSI→UTF-8, naturaleza de componentes, precio compuesto + CI, guarda de consistencia (positivo y
      negativo). **Texto puro → corre en CI.**
- [x] `packages/packs/tests/test_packs.py`: golden de pack de `banco/AQ-BC3-DEMO/v1` (manifiesto +
      versión anclada `banco_bc3` + `content_sha256` + `md5(banco.json)` + `md5(muestra.bc3)`) + guarda
      «no toca AQ-DEMO».

## Paso 5 · Anclaje e integración — HECHO
- [x] `versions.lock`: sección NUEVA `[packs.banco_bc3]` (`AQ-BC3-DEMO`/`v1`). `[packs.banco]` intacto.
- [x] `pyproject.toml` (raíz): `engines/bc3` en `[tool.uv.workspace].members`.
- [x] `.github/workflows/ci.yml`: `engines/bc3` en el `pytest` del Paso 1.
- [x] `contrato.md`: nota en «Frontera» (el `banco_ref` puede materializarse por ingesta BC3; aditivo).

## Paso 6 · No-regresión — PENDIENTE (CI)
- [x] Verificado en sandbox: E0.1 NO toca `packages/golden`, ni `entrada/salida` de C5, ni los packs
      anclados → `GOL-PRE-01/02/03` y `GOL-DOC-01` byte-idénticas.
- [ ] Gate verde en CI (Llave 1): `pytest packages/packs engines/bc3` + golden C1/C5 + esquemas.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-bc3-ingesta`: `aqyra-bc3` importa/compila; golden C5 intacto; ningún
      `expected` alterado; ningún esquema de contrato tocado; `banco/AQ-DEMO/v1` y `criterio/AQ/v1+v2`
      intactos.
- [ ] `opsx:archive` → **PR** `feat/c5-bc3-ingesta` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release**.

## Fuera de estas tareas
- Emisión `salida-presupuesto` → `.bc3` (E0.2, siguiente change del hilo) · semillas reales
  BCCA/Extremadura (E5.1, tras licencia D-026) · lectura de `~M` y del `%CI` del BC3 (ganchos forward).
