# Golden GOL-EXP-01 — EXPORT FIRMABLE del PRESUPUESTO CONTRACTUAL (capa documentos/export, C5)

> El caso PRIMARIO de la capa de export firmable (el muro de cobro, E6.2, redireccion 2026-07-12). Hace
> **FIRMABLE** el entregable CONTRACTUAL: el `salida-presupuesto` autoritativo (C5) -> el **bundle
> contractual** = **Word** (envuelve `documentos/presupuesto.componer_documento`, el .docx del despacho) +
> **PDF sellado** (mediciones + justificacion, cuadros n1/n2, PEM->PEC, manifiesto embebido) + **BC3**
> (conecta `engines/bc3.emitir_bc3`, licitacion publica) + **XLSX** (mediciones) + `manifiesto.json`. El
> nucleo `componer_export` es DETERMINISTA y VERTICAL-AGNOSTICO; **no re-renderiza** lo que ya existe:
> **envuelve** los compositores contractuales. La proyeccion (GOL-EXP-02) queda como export de gestion.

## Entrada (se LEE, no se re-ancla)
El nucleo lee el `salida-presupuesto` ANCLADO de `GOL-PRE-01/expected.json` (se LEE, no se re-ancla) y un
descriptor con `artefacto.tipo="presupuesto-obra"`. El `content_sha256` del manifiesto es la huella
canonica de ese `salida-presupuesto`; la zona anclada del C5 queda intacta.

## Que ancla (conformidad por CONTENIDO — patron GOL-DOC-01/D3; NO bytes ni pixeles; SIN ifcopenshell)
El runner (`run_case_c5` -> `modo=export` -> `_run_export_presupuesto`) compone el bundle y comprueba:
1. el `salida-presupuesto` fuente conforma su esquema; el descriptor + el manifiesto conforman sus esquemas;
2. el bundle trae los formatos declarados (Word/PDF/BC3/XLSX) + `manifiesto.json`;
3. **Word contractual** (el .docx de `componer_documento`): las 8 partidas y el PEC presentes;
4. **PDF firmable**: las partidas, el PEC, la **JUSTIFICACION de medicion** (criterio + GUIDs trazados al
   modelo) y el `content_sha256`;
5. **BC3** (FIEBDC-3): los codigos de partida presentes (licitacion);
6. **XLSX**: las cantidades por partida;
7. **manifiesto INTEGRO** (`content_sha256` == hash canonico del `salida-presupuesto` + versiones) = Llave 1;
8. **isCertified**: el bundle SIN firmar NO es `verified-signed` (estado `computed`) — solo la firma GPG de
   JM en el release (Llave 2) lo acuna; el hook `firmar_detached` esta presente pero el gate no lo ejecuta;
9. **DETERMINISMO**: componer 2x => Word/PDF/BC3/XLSX/manifiesto identicos (sello de fecha fijo, parametro).

Justificacion de medicion v0 = **cantidad + criterio + origen + GUIDs** (lo que el `salida-presupuesto` ya
trae, anclado en GOL-PRE-01). El detalle dimensional por objeto (traza_cantidades del engine) = **forward**.

## Regla de oro
Un fallo NO se arregla aflojando esta golden ni el formato. Se investiga en el **nucleo/compositor**
(`documentos/export`). El Word contractual lo guarda ademas `GOL-DOC-01`; el BC3, la golden de `engines/bc3`.
El bundle solo cambia si cambia el `salida-presupuesto` fuente (GOL-PRE-01, zona anclada), el descriptor o
el diseno del formato (bump de version del paquete).
