# Tareas · Capítulos por clasificación (Slice B)

## Paso 0 · Decisiones (BLOQUEA el código)
- [x] D-RB-5..8 ratificadas por JM (2026-07-12) y ancladas en `engines/presupuesto/DECISIONES.md`.

## Engine
- [x] `presupuestar` acepta `parametros.estructura_capitulos ∈ {catalogo, uniclass, gubim}` (default catalogo, byte-idéntico).
- [x] `_catalogo_por_clasificacion` + `_grupo_clasif` + `_GRUPOS_TITULO` (tabla EF/GuBIM embebida y anclada); S&S → `SIN`.
- [x] Bump 0.6.0 → 0.7.0.

## Banco
- [x] `data/packs/banco/AQ-DEMO/v1/banco.json` — `clasificacion_gubim` en las 7 partidas (D-RB-7; demo). Re-anclaje: `pack.json.md5_banco` + `golden/expected.json.content_sha256` + `test_packs.py` md5.

## Golden (Llave 1)
- [x] `packages/golden/C5/GOL-PRE-06/` — expected.json (modo=capitulos, ejes uniclass+gubim) + ficha + tolerancias.
- [x] `run_golden.py` — rama `modo=capitulos` (`_run_c5_capitulos`) en `run_case_c5`.
- [x] `engines/presupuesto/tests/test_presupuesto.py` — tests default/uniclass/gubim/coste-intacto.
- [ ] Gate VERDE en CI (recompute C5 de GOL-PRE-01..05 con ifcopenshell + GOL-PRE-06 sin ifcopenshell + tests).

## Anclaje / versión
- [x] `versions.lock` — engine 0.7.0 + nota; `engines/presupuesto/DECISIONES.md` (D-RB-5..8).
- [x] Verificación local: default idéntico a GOL-PRE-01; uniclass/gubim agrupan; PEM/PEC intactos; Σ==PEM; determinismo; réplica de GOL-PRE-06 (11/11).

## Cierre (Llave 2 = JM)
- [ ] adversarial-review → `opsx:archive` → PR → gate verde → merge (JM). Engine SIN release (política vigente).
