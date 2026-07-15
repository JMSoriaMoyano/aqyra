# Tareas · Descripciones ricas del banco (Slice A)

## Paso 0 · Decisiones (BLOQUEA el código)
- [x] D-RB-1..4 ratificadas por JM (2026-07-12) y ancladas en `documentos/presupuesto/DECISIONES.md`.

## Contract-first · banco + engine
- [x] `data/packs/banco/AQ-DEMO/v1/banco.json` — `resumen` (= descripción actual) + `texto` ampliado en las 7 partidas.
- [x] Re-anclaje: `pack.json.contenido.md5_banco` + `golden/expected.json.content_sha256` recomputados; `test_packs.py` md5 fijado actualizado.
- [x] `engines/presupuesto` — `descripcion = resumen or descripcion`; arrastre de `texto` (aditivo); bump 0.6.0.

## Compositores
- [x] `documentos/presupuesto` 0.2.0 — `componer_documento` renderiza el `texto` ampliado bajo cada partida.
- [x] `documentos/export/presupuesto_doc.py` — PDF sellado renderiza el `texto`; el Word lo hereda.

## Golden (Llave 1)
- [x] `GOL-PRE-01/expected.json` — `texto` en las 7 partidas `origen=modelo` (números intactos).
- [x] `run_golden.py` — GOL-DOC-01 + GOL-EXP-01 amplían el oráculo (texto ampliado presente; determinismo).
- [x] `engines/presupuesto/tests/test_presupuesto.py` — tests de arrastre + fallback.
- [ ] Gate VERDE en CI (recompute C5 con ifcopenshell + doc/export sin ifcopenshell).

## Anclaje / versión
- [x] `versions.lock` — `engine_version` 0.6.0 + nota `texto`/`resumen`; `[documentos.presupuesto]` 0.2.0.
- [ ] Verificación local (hecha en el contenedor): PEM/PEC intactos, `texto` en documento/Word/PDF, determinismo, re-anclaje del banco consistente.

## Cierre (Llave 2 = JM)
- [ ] adversarial-review → `opsx:archive` → PR → gate verde → merge (JM).
- [ ] Release `documento-presupuesto-v0.2.0` sólo si JM lo decide (D-RB-4).
