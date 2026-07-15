# Diseno · export-firmable-proyeccion

## Nucleo (vertical-agnostico)
`componer_export(artefacto, descriptor, parametros?) -> Path(bundle)`:
1. `manifiesto.construir_manifiesto(artefacto, descriptor)` — procedencia DETERMINISTA. El
   `content_sha256` es la huella canonica (claves ordenadas) del artefacto autoritativo. El sello de
   tiempo viene del descriptor (NUNCA `now()`). Las versiones ancladas las aporta el caller (el nucleo
   no lee `versions.lock` — asi cualquier vertical entra sin tocarlo).
2. Escribe `manifiesto.json` (serializacion determinista).
3. Llama al compositor por formato (registro `_COMPOSITORES`) segun el `descriptor.formatos`.

## Primer consumidor (proyeccion)
- `proyeccion.informe_word` (reusa `aqyra_documento_comun.formato`) y `proyeccion.proyeccion_xlsx`
  (`openpyxl`, propiedades con fecha fija) renderizan las `vistas` del artefacto (shape de GOL-PRE-03):
  por vista, tabla grupo/valor/unidad/fuente + fila SUMA; mas la seccion/hoja de manifiesto.
- `sellado.firmable_pdf` (`fpdf2`, `creation_date` fijo, texto latin-1) produce el PDF firmable con el
  manifiesto EMBEBIDO como seccion visible (texto extraible por `pypdf` — sin pixeles).

## Firma — dos capas (reparto real de las dos llaves)
- `firma.integridad` / `manifiesto.integridad` (gate, pure-python): `content_sha256` recomputado ==
  manifiesto; `modelo_md5` == `entradas_md5` del artefacto; versiones presentes.
- `firma.estado_firmable` (espeja `isCertified`): `verified-signed` SOLO con `.asc` verificado; sin
  cripto en el gate devuelve `computed` (propone). `firma.firmar_detached` (release-time, GPG de JM):
  NO se ejecuta en el gate.

## Golden GOL-EXP-01 (modo=export en run_case_c5)
Lee el artefacto de proyeccion anclado (`GOL-PRE-03/expected.json`) + un descriptor; compone; comprueba
esquemas (descriptor + manifiesto), formatos + manifiesto presentes, cifras en Word/XLSX/PDF, manifiesto
integro (Llave 1), isCertified (sin firma != verified-signed), y determinismo. SIN ifcopenshell (patron
GOL-DOC-01/GOL-PLI-01: LEE el artefacto anclado, no re-mide).

## No-regresion / forward-open
Anade `documentos/comun` + `documentos/export` + `GOL-EXP-01` + edicion quirurgica de versions.lock,
workspace, ci.yml, release.yml, run_golden.py. No toca la proyeccion, el motor, el esquema C5, los packs,
presupuesto/pliego (frozen), emitir_bc3 ni el dashboard. BC3 / PAdES / 2.o consumidor = forward.
