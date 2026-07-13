# Tareas · Pliego contractual firmable (Slice C)

## Paso 0 · Decisiones (BLOQUEA el codigo)
- [x] D-PL-1..3 ratificadas por JM (2026-07-12) y ancladas en `documentos/export/DECISIONES.md` (namespace D-PL).

## Consumidor (documentos/export)
- [x] `pliego_doc.py` (NUEVO, espejo de `presupuesto_doc.py`): `pliego_word` (envuelve `componer_pliego`) + `pliego_pdf` (sellado) + `FORMATOS = {word, pdf}`. Sin BC3/XLSX (D-PL-1). Imports del pliego/fpdf perezosos.
- [x] `export.py` (+`__init__.py`): registrar `"pliego-obra": PL.FORMATOS` en `_CONSUMIDORES`. Nucleo intacto.

## Golden (Llave 1)
- [x] `packages/golden/C5/GOL-EXP-03/` — expected.json (modo=export, consumidor=pliego-obra, descriptor con `pliego={criterio_ref, pack_textos_ref}`) + ficha + tolerancias.
- [x] `run_golden.py` — `_run_export_pliego` + despacho `consumidor=="pliego-obra"` en `_run_c5_export`.
- [x] Verificacion local (sin ifcopenshell): GOL-EXP-03 VERDE (17/17); no-regresion GOL-PLI-01 + GOL-EXP-01 VERDES; el paquete importa sin el pliego en el path.
- [ ] Gate VERDE en CI.

## Anclaje
- [x] `versions.lock [documentos.export]` — nota del consumidor pliego-obra + GOL-EXP-03. Sin bump de version (D-PL-3).

## Cierre (Llave 2 = JM)
- [ ] adversarial-review -> `opsx:archive` -> PR `feat/export-pliego-firmable` -> gate verde -> merge (JM). Release `documento-export-v0.1.0` si JM lo decide (D-PL-3).
