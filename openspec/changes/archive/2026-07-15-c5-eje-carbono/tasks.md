# Tareas · Eje CARBONO en C5 (E3) — `c5-eje-carbono`

> Gobernado por `docs/PROCESO_SDD.md`. **EXTIENDE** C5 (forward-open); el esquema de SALIDA no se toca.
> Zona anclada intocable: eje coste (`precio_unitario`/`importe`), `GOL-PRE-01/02/03`, `GOL-DOC-01`, packs
> `criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1` (identidad por hash). El contrato C5 está
> en la frontera CODEOWNERS → el merge es firma de JM (Llave 2). Gobierna **D-026/N-04** (banco-carbono v0
> PROPIO/sintético; semillas reales = E5.2 tras licencia).

## Paso 0 · Ratificación (BLOQUEA el código) — HECHO
- [x] JM ratifica **D39/D40** (pack `banco-carbono`: factor por código de partida + factores por etapa; el
      motor reparte con la última etapa como residuo → Σ etapas = total). Opción A.
- [x] JM ratifica **D41** (convención `id=carbono`/`unidad=kgCO2e`/etapas mínimas A1A3+A4A5; esquema de
      salida C5 intacto).
- [x] JM ratifica **D42** (trazabilidad `epd`/`generico` DIFERIDA; el `banco` ref ya la traza). Opción A.
- [x] JM ratifica **D43** (runner: rama de modo `_run_c5_carbono` bajo `run_case_c5`). Opción A.
- [x] JM ratifica **D44** (anclaje `GOL-CAR-01`: fixtures aumentadas de `GOL-PRE-03` + `criterio/AQ/v2`;
      determinismo+semántica+invariante, NO md5). Opción A.
- [ ] Anclar **D39–D44** en `packages/contracts/C5-presupuesto/DECISIONES.md` (continúan D1–D38). — en este PR

## Paso 1 · Rama (primero, tras ratificar) — PENDIENTE (host)
- [ ] Crear y cambiar a `feat/c5-eje-carbono` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Familia de pack `banco-carbono` (E3.2, contract-first) — apply
- [ ] `data/packs/pack.schema.json`: enum `familia` gana `banco-carbono` (aditivo).
- [ ] `packages/packs/src/aqyra_packs/__init__.py`: `FAMILIAS` gana `banco-carbono`.
- [ ] `data/packs/banco-carbono/generico/v1/{banco.json, pack.json, golden/expected.json}` — PROPIO/sintético
      (D-026); factores kgCO₂e por partida con etapas A1A3/A4A5; `content_sha256` + md5(banco.json).
- [ ] `versions.lock`: fila nueva `[packs.banco_carbono]` (espejo de `[packs.banco_bc3]`).
- [ ] `packages/packs/tests/test_packs.py`: golden de pack del `banco-carbono` (hash + md5).

## Paso 3 · Motor: emitir etapas (engines/presupuesto 0.5.0) — apply
- [ ] `presupuesto.py`: `_etapas_eje(bp, cantidad, total)` (reparto EN 15978, última etapa = residuo) +
      `_valor_eje(..., etapas=None)`; emitir `valores[eje].etapas` en las partidas `origen=modelo` no-coste.
      Coste (default) intacto. Guarda Σ factor_etapa ±0,01 vs `precio` (aviso).
- [ ] `__init__.py`: `__version__ = "0.5.0"`.
- [ ] `engines/presupuesto/tests/test_carbono.py`: unit-test (texto puro, Decimal) — coste intacto;
      carbono conforma esquema; `valores.carbono` + etapas + **Σ etapas = total** exacto; S&S sin etapas.

## Paso 4 · Golden `GOL-CAR-01` (E3.3, la Llave 1) — apply
- [ ] `packages/golden/C5/GOL-CAR-01/{entrada.json, expected.json, ficha.md, tolerancias.json}` — reusa las
      fixtures aumentadas de `GOL-PRE-03` (`entradas_md5`) + `criterio/AQ/v2` + `banco-carbono/generico/v1`,
      `parametros.eje="carbono"`. `expected` con `modo:"carbono"`, la valoración por partida (oráculo a mano
      ×2) y ≥1 vista de proyección de carbono.
- [ ] `packages/golden/src/aqyra_golden/run_golden.py`: rama `_run_c5_carbono` (dispatch `modo=="carbono"`).

## Paso 5 · Anclaje de decisiones + contrato — apply
- [ ] `DECISIONES.md`: **D39–D44** (continúan D1–D38). `contrato.md`: nota del eje carbono (aditiva).

## Paso 6 · No-regresión + verificación local (conda `mcp-bim`)
- [ ] Sandbox (texto puro): `pytest engines/presupuesto/tests/test_carbono.py` + conformidad de esquemas.
- [ ] Conda `mcp-bim` (ifcopenshell): `pytest packages/golden` (recompute) → `GOL-CAR-01` verde y
      `GOL-PRE-01/02/03` + `GOL-DOC-01` byte-idénticas; `pytest engines/presupuesto packages/packs`.
- [ ] Verificar que E3 NO toca el esquema de salida, ni el eje coste, ni los packs anclados (md5).

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-eje-carbono`: engine importa/compila; golden de coste intacto; ningún `expected`
      de coste alterado; esquema de salida sin tocar; packs anclados intactos; sólo `banco-carbono/` nuevo.
- [ ] `opsx:archive` → **PR** `feat/c5-eje-carbono` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release** (salvo decisión de JM).

## Fuera de estas tareas
- Semillas reales Ökobaudat/INIES/EC3 (E5.2, tras licencia D-026) · EPD verificadas `banco-carbono/epd/vN`
  + clave `origen_factor` (N-05, premium) · pliego firmable (E4, Ola 3) · dashboard (E6, Ola 4) · write-back
  6D del carbono al IFC.
