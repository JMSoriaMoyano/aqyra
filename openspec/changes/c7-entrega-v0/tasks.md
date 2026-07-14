# Tareas · Operador de ENTREGA C7 v0 (c7-entrega-v0)

## Paso 0 · Decisiones (BLOQUEA el código)
- [x] D-C7-1..6 ratificadas por JM (2026-07-13), incluidas las sub-decisiones (D-C7-2 «C7 no lee el repo»; D-C7-4 «content_sha256_manifiesto = sha256 del manifiesto.json entero»). Ancladas en `packages/contracts/C7-entrega/DECISIONES.md`.

## Contrato (contract-first, ANTES del módulo)
- [x] `packages/contracts/C7-entrega/contrato.md` (ficha 6 campos + reconciliación con la ficha de Aqyra-Raiz).
- [x] `solicitud-entrega.schema.json` + `manifiesto-entrega.schema.json` (forward-open, JSON Schema 2020-12).
- [x] `DECISIONES.md` (D-C7-1..6).

## Operador (services/entrega)
- [x] `manifiesto_entrega.py` — construir + serializar determinista + integridad + roll-up `paquete_sha256`.
- [x] `entrega.py` — `componer_entrega(solicitud, parametros?)`: valida, itera envolviendo `componer_export`, ensambla el manifiesto-entrega. `__init__.py` + `cli.py` + `pyproject.toml` (dep `aqyra-documento-export`).
- [x] `tests/test_entrega.py` — paquete 2 bundles + roll-up/integridad + mismo Maestro + determinismo + isCertified + artefacto_ref sin inline falla.

## Golden (Llave 1)
- [x] `packages/golden/C7/GOL-EN-01/` — `entrada.json` (solicitud presupuesto+pliego) + `expected.json` + `ficha.md` + `tolerancias.json`.
- [x] `run_golden.py` — `run_case_c7` + `CASE_RUNNERS["C7"]` + helper `_resolver_artefacto_ref`.
- [ ] Verificación local (sin ifcopenshell): GOL-EN-01 VERDE + no-regresión GOL-EXP-01/03 + GOL-PLI-01 VERDES + tests de `services/entrega`.
- [ ] Gate VERDE en CI.

## Anclaje
- [x] `versions.lock [contracts.C7]` + `[services.entrega]`.
- [x] `pyproject [tool.uv.workspace]` (+`services/entrega`) + `ci.yml` (pytest +`services/entrega`).

## Cierre (Llave 2 = JM)
- [ ] adversarial-review -> `opsx:archive` -> PR `feat/c7-entrega-v0` -> gate verde -> merge (JM). Release `entrega-v0.1.0` si JM lo decide (D-C7-6).
