# Tareas · El visor pinta el veredicto de cumplimiento (6D)

> Gobernado por `docs/backend-standards.md` (Python/uv, TDD) para el engine y
> `docs/frontend-standards.md` (pnpm, TS 5.5 ESM, web-ifc 0.0.68 exacto, vitest) para el visor,
> y por `docs/openspec-tasks-mandatory-steps.md`. Baby steps: un paso revisable cada vez; solo lo
> afectado (`tools/affected.py`). Dos llaves: gate verde (L1) + firma JM (L2). git por `.bat` en
> el host; Claude prepara y lanza el `.bat`, JM revisa y fusiona.

## Paso 0 · Rama (primero) — BLOQUEADO por ratificación
- [ ] Crear y cambiar a `feat/visor-cumplimiento-6d` desde `origin/main`.
- [ ] **Ratificar D-6D-1..4** con JM (OK explícito) antes de tocar código — patrón C3 (D1–D10) /
      C5 (D11–D15). Anclar en `packages/contracts/C3-cumplimiento/DECISIONES.md` (bloque 6D) y
      `apps/visor/DECISIONES.md` (color).

## Paso 1 · Engine: `escribir_cumplimiento` (test-first)
- [ ] Test (`engines/cumplimiento/tests/test_escribir.py`): sobre el derivado del C4-FED-06 +
      veredicto de GOL-CTE-01, `escribir_cumplimiento` deja un `Pset_Aqyra_Cumplimiento` en cada
      elemento con el `Resultado` de peor caso esperado; escribir 2× → bytes idénticos.
- [ ] Código: `engines/cumplimiento/src/.../escribir.py` (espeja `escribir_coste`): mapea
      `por_modelo` → elementos vía manifiesto, agrega peor caso, escribe Pset. Abre el derivado,
      no federa.

## Paso 2 · Golden: caso 6D anclado
- [x] `packages/golden/C3/GOL-CTE-6D-01` (caso separado, patrón GOL-PRE-02/5D): fixtures de
      GOL-CTE-01 byte a byte; `run_case_c3` despacha por `modo:"6d"` → `_run_c3_6d` que
      federa+deriva+verifica+escribe y ancla por DETERMINISMO (2× = bytes) + SEMÁNTICA (proyección
      peor caso INDEPENDIENTE del runner) + conteos. Conserva íntegros los 22 checks de GOL-CTE-01.
- [x] Verificar en local (runner standalone, python mcp-bim) VERDE: GOL-CTE-01 (22) +
      GOL-CTE-6D-01 (14) → VERDE. n_elementos=13 (todos no-cumple, E-SI-RF-DECL domina), md5
      determinista `d9b68d468ee8…`.

## Paso 3 · Visor: `compliance.ts` (test-first)
- [x] Test (`apps/visor/test/compliance.test.ts`): `leerCumplimiento` sobre la fixture 6D →
      `porElemento` (13) todos `no-cumple` + `resumen` correcto + muro con exigencia dominante
      `E-SI-RF-DECL`; helpers de color/leyenda puros (D-6D-4); modelo base (sin Pset) → `null`.
- [x] Código: `apps/visor/src/compliance.ts` (`leerCumplimiento` lee `Pset_Aqyra_Cumplimiento` con
      web-ifc, como `cost.ts`; `colorPorResultado`/`leyendaCumplimiento`). Loader `readCompliance`.
      Tipos/símbolos exportados desde `src/index.ts`.

## Paso 4 · Visor: color + demo
- [x] Cableado: `viewer.setCumplimientoColors` (mismo mecanismo que el heatmap 5D, reversible con
      `resetColors`); demo con flag `?6d`, botón, leyenda de 4 con conteo (D-6D-4), panel de
      selección con Resultado/Exigencia/Pack. NO se toca `cost.ts` ni la ingesta.
- [x] E2E anclado (`apps/visor/test/cumplimiento-6d-e2e.test.ts`): md5 LF de la fixture
      (`fffeb26f…`, raw determinista `d9b68d46…` == golden) + color por elemento (los renderables
      reciben el rojo de `no-cumple`). Patrón del E2E del coste 5D.
- [x] Verificado en local (host, node_modules del visor): typecheck + build + **92/92 vitest** VERDE.

## Paso 5 · Unit tests + estado (MANDATORY)
- [ ] Engine: `uv run pytest` targeted + suite; report en
      `specs/visor-cumplimiento-6d/reports/YYYY-MM-DD-step5-unit-test.md`.
- [ ] Visor: `pnpm -C apps/visor test` + `typecheck` + `build` verdes (gate Paso 4/5).

## Paso 6 · Documentación técnica (MANDATORY)
- [ ] `packages/contracts/C3-cumplimiento/contrato.md` + `DECISIONES.md` (bloque 6D, D-6D-1..3).
- [ ] `apps/visor/DECISIONES.md` (color, V-siguiente). `openspec/changes/visor-cumplimiento-6d/`
      actualizado si cambia el diseño.

## Paso 7 · versions.lock + releases (Llave 2)
- [ ] `versions.lock`: bump `engine_version` de `[contracts.C3]` (write-back) y `[apps.visor]`.
- [ ] Releases firmados `cumplimiento-vX.Y.0` y `visor-vX.Y.0` (tag GPG de JM — Llave 2).

## Paso 8 · adversarial-review + archive + commit
- [ ] `adversarial-review`: verificación mecánica (tests/lint/typecheck/build/tasks) + pase
      adversarial.
- [ ] `opsx:archive` el change + `commit` (PR). CODEOWNERS si toca `packages/contracts`/golden.

> Nota curl/Playwright de los pasos obligatorios: **N/A** — no hay endpoint HTTP nuevo (engine de
> librería + visor estático). La verificación equivalente es el runner de golden (engine) y el
> E2E vitest anclado (visor), ejecutados por el agente.
