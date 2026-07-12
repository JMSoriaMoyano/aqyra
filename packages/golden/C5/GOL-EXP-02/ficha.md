> **[SECUNDARIO/gestion]** Este caso ancla el export de la PROYECCION de valor (vista de gestion, no
> contractual). El entregable CONTRACTUAL firmable es GOL-EXP-01 (presupuesto). Se conserva porque valida
> el nucleo vertical-agnostico con un 2.o consumidor (regla de tres).

# Golden GOL-EXP-01 — conformidad del EXPORT FIRMABLE de la proyeccion (capa documentos/export, C5)

> El primer caso de la **capa transversal de export firmable** (el muro de cobro, E6.2). Hace
> **FIRMABLE** lo que GOL-PRE-03 hizo proyectable: el JSON AUTORITATIVO de proyeccion (`vistas`) ->
> el **bundle firmable** (Word + XLSX + **PDF sellado** + `manifiesto.json`). El nucleo
> `documentos/export.componer_export` es **DETERMINISTA** (formatea; sin LLM) y **VERTICAL-AGNOSTICO**
> (consume cualquier artefacto autoritativo + descriptor). Primer consumidor: la proyeccion (regla de
> tres — el 2.o consumidor validara el contrato y extraera mas).

## Entrada (se LEE, no se re-ancla)
El nucleo lee el **artefacto de proyeccion ANCLADO** de `GOL-PRE-03/expected.json` (D-EX-4: se LEE, no
se re-ancla) y un **descriptor** (formatos + procedencia + sello determinista). El `content_sha256` del
manifiesto es la huella canonica de ese artefacto anclado; la zona anclada del C5 queda intacta.

## Qué ancla (conformidad por CONTENIDO — patron GOL-DOC-01/GOL-PLI-01/D3; NO bytes ni pixeles)
El runner (`run_case_c5`, rama `modo="export"`) compone el bundle, extrae **texto/tablas/celdas** con
python-docx/openpyxl/pypdf (no OCR) y comprueba:

1. **Contract-first**: el `descriptor` conforma `descriptor-export.schema.json` y el `manifiesto`
   conforma `manifiesto-export.schema.json` (esquemas forward-open del nucleo).
2. el nucleo **genera** el bundle: los **formatos declarados** (Word/XLSX/PDF) + `manifiesto.json`.
3. **cifras**: en Word/XLSX/PDF, cada **grupo** y cada **Sigma** de las 3 vistas de GOL-PRE-03 se
   reproducen (`valor_total == JSON +-0,01`), invariante Sigma incluido.
4. **manifiesto INTEGRO (Llave 1)**: `content_sha256 == ` hash canonico recomputado del artefacto;
   `modelo_md5 == entradas_md5` de GOL-PRE-03; versiones ancladas presentes.
5. **isCertified (D-EX-5)**: el bundle **SIN firmar** NO es `verified-signed` (estado `computed`). Solo
   la **firma GPG de JM en el release** (Llave 2) lo acuna; el hook `firmar_detached` esta presente pero
   el gate **no** lo ejecuta (la clave privada de JM no entra en CI).
6. **DETERMINISMO**: componer **2x** => Word/XLSX/PDF (texto/celdas) + `manifiesto.json` identicos
   (sello de fecha fijo, parametro — nunca now()).

Corre en el gate **SIN ifcopenshell** (LEE la proyeccion anclada, no re-mide) — como GOL-DOC-01/GOL-PLI-01.

## Regla de oro
Un fallo NO se arregla aflojando esta golden ni el formato. Se investiga en el **nucleo/compositor**
(`documentos/export`). El bundle solo cambia si cambia el artefacto fuente (GOL-PRE-03, zona anclada —
decision explicita con JM), el descriptor o el diseno del formato (bump de version del paquete).
