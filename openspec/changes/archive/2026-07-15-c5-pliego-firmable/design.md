# Diseno · c5-pliego-firmable (Slice C)

## Principio — envolver, no re-renderizar
El pliego ya se compone (`documentos/pliego.componer_pliego`, `GOL-PLI-01`). Slice C **no re-implementa**
el pliego: registra un consumidor `pliego-obra` en el rail de export que **envuelve** ese compositor y le
anade el sellado + manifiesto que ya usa el presupuesto. El nucleo `componer_export` (descriptor + manifiesto
+ sellado + firma) es VERTICAL-AGNOSTICO y **no se toca**: un consumidor entra registrandose en
`_CONSUMIDORES` (patron D-EX-2/D-EX-4).

## Consumidor `pliego-obra` (`pliego_doc.py`, espejo de `presupuesto_doc.py`)
- `pliego_word(artefacto, descriptor, manifiesto, salida)` — ENVUELVE `componer_pliego(artefacto, criterio,
  {salida, fecha, pack_textos, titulo})`. El `criterio` y el `pack_textos` (dicts resueltos) los porta el
  descriptor en la clave forward-open `descriptor["pliego"] = {criterio, pack_textos}` (patron
  vertical-agnostico: el consumidor no lee `versions.lock` ni el repo, como las `versiones_ancladas`).
- `pliego_pdf(...)` — PDF firmable sellado (fpdf2, `creation_date` fijo, texto latin-1). Por partida:
  encabezado (codigo + descripcion + sistema del criterio) + **prescripcion** (reusa `compositor._prescripcion`,
  MISMA cadena que el Word) + **medicion** (cantidad/criterio/origen) + **coste** (precio unitario/importe) +
  **carbono** forward-open + **trazabilidad** (GUIDs). Cierra con el cuadro de trazabilidad y el **manifiesto
  de procedencia EMBEBIDO** (content_sha256 + versiones) — texto extraible por pypdf, sin pixeles.
- `FORMATOS = {word: ("Pliego.docx", ...), pdf: ("Pliego-firmable.pdf", ...)}`. **Sin BC3 ni XLSX** (D-PL-1).

## Artefacto y descriptor
Artefacto autoritativo = el mismo `salida-presupuesto` (C5). El consumidor se selecciona por
`descriptor.artefacto.tipo = "pliego-obra"`. El manifiesto (content_sha256 del `salida-presupuesto` +
versiones + sello determinista) es el MISMO nucleo; el `pliego` es una clave que el manifiesto ignora
(forward-open).

## Golden GOL-EXP-03 (`_run_export_pliego`, despacho por consumidor en `_run_c5_export`)
Lee el `salida-presupuesto` anclado (`GOL-PRE-01`) + el descriptor; resuelve `criterio/AQ/v2` +
`pliego-textos/AQ-DEMO/v1` del repo (como `GOL-PLI-01`) y los inyecta en el descriptor; compone el bundle y
comprueba: esquemas (descriptor + manifiesto); bundle = Word + PDF + manifiesto (sin BC3); Word del pliego
(secciones + 8 partidas con prescripcion sin fallback + medicion +-0,001 + coste +-0,01); PDF sellado
(partidas + prescripcion sin fallback + criterio + GUIDs + content_sha256); carbono forward-open; manifiesto
integro (Llave 1); isCertified (sin firma != verified-signed); DETERMINISMO. SIN ifcopenshell.

## No-regresion / forward-open
Anade `pliego_doc.py` + registro + `GOL-EXP-03` + `_run_export_pliego`. No toca `componer_pliego`/`GOL-PLI-01`,
el nucleo de export, `presupuesto_doc`/`GOL-EXP-01`, `proyeccion`/`GOL-EXP-02`, `emitir_bc3`, el motor/esquema
C5, los packs ni el dashboard. BC3/XLSX del pliego, PAdES y textos normativos reales = forward.
