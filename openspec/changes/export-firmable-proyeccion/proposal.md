# Change · export-firmable-proyeccion (E6.2 · el muro de cobro)

## Por que
Forward de E6.1/D-DV-5: la VISTA de proyeccion (dashboard) «se siente gratis»; el **muro de cobro** es
el **export firmable** del valor. El patron «JSON autoritativo -> compositor determinista del despacho
-> golden por contenido -> release firmado» ya esta probado dos veces (`documentos/presupuesto`,
`documentos/pliego`). E6.2 lo **generaliza a una capa transversal** y le anade lo que falta para ser el
muro de cobro: **manifiesto de procedencia + sellado + firma**, con un contrato **vertical-agnostico**.

## Que (dos niveles)
- **Nivel 1 · Nucleo transversal** `documentos/export`: `componer_export(artefacto, descriptor) ->
  bundle`. Manifiesto (procedencia + `content_sha256` del artefacto + sello determinista), sellado
  (PDF pure-python con el manifiesto embebido), firma en dos capas (integridad en el gate / GPG de JM
  en el release), contrato forward-open (`descriptor-export` + `manifiesto-export`).
- **Nivel 2 · Consumidor PRIMARIO (CONTRACTUAL, redireccion JM 2026-07-12)**: el **presupuesto de obra**.
  ENVUELVE los compositores existentes (no re-renderiza): Word=`componer_documento` (partidas del banco +
  cuadros n1/n2 + estado de mediciones + PEM->PEC) + PDF sellado (con la justificacion de medicion:
  criterio + GUIDs) + BC3=`emitir_bc3` (licitacion) + XLSX (mediciones). La **proyeccion de valor** queda
  como consumidor de GESTION (secundario). El **pliego** entra como slice siguiente (envuelve
  `componer_pliego`).
- **Formato compartido** `documentos/comun` (D-EX-1 A): se extrae el formato del despacho al aparecer el
  3.er consumidor; presupuesto/pliego siguen con su espejo congelado.

## Decisiones (ratificadas por JM 2026-07-12)
D-EX-1 (paquete nuevo + modulo comun) · D-EX-2 (Word+XLSX+PDF pure-python, BC3 forward) · D-EX-3
(integridad en el gate, firma GPG de JM en el release) · D-EX-4 (esquemas descriptor+manifiesto,
vertical-agnostico) · D-EX-5 (muro de cobro; CON release `documento-export-v0.1.0`). Ver
`documentos/export/DECISIONES.md`.

## Dos llaves
- **Llave 1** (gate): `GOL-EXP-01` VERDE (conformidad por contenido; integridad del manifiesto;
  determinismo; SIN ifcopenshell — LEE la proyeccion anclada). No-regresion: `GOL-PRE-03`,
  `GOL-DOC-01`, `GOL-PLI-01`, `documentos/presupuesto`, `documentos/pliego`, dashboard E6.1 INTACTOS.
- **Llave 2** (release): firma GPG de JM (`documento-export-v0.1.0`).

## Fuera de alcance (forward)
Firma cualificada/PAdES del cliente; BC3 de la proyeccion (conectar `emitir_bc3`); 2.o consumidor
(cumplimiento/calculo) que validara el contrato y extraera mas (regla de tres); unificacion de los
exports Word dispersos de las skills de calculo.
