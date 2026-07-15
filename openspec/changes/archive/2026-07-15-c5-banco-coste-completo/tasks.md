# Tareas · c5-banco-coste-completo (E5.1b)

> Flujo SDD (`docs/PROCESO_SDD.md`): Paso 0 (ratificar) → apply → adversarial-review → archive → PR.
> Baby steps; solo lo afectado; artefactos en español; dos llaves (Llave 1 = gate verde; Llave 2 = JM).

## Paso 0 — Decisiones (BLOQUEA el código) — HECHO
- [x] D53 (alcance + identidad del banco) RATIFICADA: subconjunto NATIVO curado; id `banco/BCCA-nativo/v1` + clave `[packs.banco_bcca_nativo]`.
- [x] D54 (estrategia del criterio nativo) RATIFICADA: corte nativo de 4 clases; puerta = forward.
- [x] D55 (golden) RATIFICADA: GOL-PRE-05 sin puerta; oráculo a mano ×2.
- [x] Anclar D53–D55 en `packages/contracts/C5-presupuesto/DECISIONES.md`.

## Paso 1 — Rama
- [ ] `feat/c5-banco-coste-completo` desde `origin/main` (git por `.bat` en el host).

## Paso 2 — Banco BCCA nativo (`banco/BCCA-nativo/v1`)
- [x] `.bc3` curado `fuente/BCCA-nativo.bc3` (6 unidades BCCA nativas + básicos, aplanado sin AUX; cp1252/CRLF; extraído verbatim del `.bc3` original).
- [x] `banco.json` = núcleo de `ingerir_bc3(..., ci=0)` + `provenance` por partida (código BCCA = código de partida) + descripción honesta.
- [x] `pack.json` (`md5_banco`, `md5_bc3`, partidas nativas) + `golden/expected.json` (`content_sha256`).
- [x] `versions.lock` → fila `[packs.banco_bcca_nativo]` (NUEVA; no mueve las ancladas).
- [x] Golden de pack (`test_packs.py`) + golden del parser (`test_bc3.py`, `ingerir_bc3` reproduce el núcleo presupuestable).

## Paso 3 — Criterio nativo (`criterio/AQ/v3`)
- [x] `criterio.json`: 4 clases → códigos BCCA nativos, misma medición que v1, + `capitulos` nativos. Sin IfcDoor.
- [x] `pack.json` + `golden/expected.json` (`content_sha256`). `[packs.criterio]` sigue en v1.
- [x] Golden de pack de v3 (`test_packs.py`).

## Paso 4 — GOL-PRE-05
- [x] `entrada.json` (reusa la medición de GOL-PRE-01; `criterio_ref=AQ/v3`, `banco_ref=BCCA-nativo/v1`).
- [x] `expected.json` (oráculo a mano ×2 = recompute del engine): 6 partidas nativas + S&S; PEM 9.993,41 → PEC 14.389,50.
- [x] `ficha.md` + `tolerancias.json` (= GOL-PRE-04).
- [x] `run_golden.py`: (a) `banco_bcca_nativo` en la tupla de `_banco_anclado_en_lock`; (b) criterio no-pointer (v3) anclado por `content_sha256`.

## Paso 5 — No-regresión + cierre (Llave 1)
- [x] Sandbox (texto puro): packs + parser + esquemas + coherencia aritmética del expected → 30/30 PASS.
- [ ] Conda `mcp-bim` de JM (ifcopenshell): recompute de GOL-PRE-05 (`medir()`+`presupuestar()`) == expected + no-regresión byte-idéntica de GOL-PRE-01..04 y GOL-CAR/DOC/PLI.
- [ ] `adversarial-review c5-banco-coste-completo` → `opsx:archive` → PR `feat/c5-banco-coste-completo` → `main`, gate verde.
- [ ] Llave 2 = JM (merge/firma). SIN release salvo decisión de JM.
