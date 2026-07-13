# Golden GOL-EXP-03 — EXPORT FIRMABLE del PLIEGO CONTRACTUAL (capa documentos/export, C5)

> Tercera y ultima pieza del **conjunto contractual firmable** (Slice C, forward de GOL-EXP-01
> —presupuesto— y GOL-PLI-01 —pliego—). Hace **FIRMABLE** el pliego por el **mismo rail de export** que
> ya firma el presupuesto (E6.2): el `salida-presupuesto` autoritativo (C5) -> el **bundle contractual
> del pliego** = **Word** (ENVUELVE `documentos/pliego.componer_pliego`, el .docx del despacho) + **PDF
> sellado** (por partida: prescripcion + medicion trazable + coste + GUIDs + carbono forward-open + cuadro
> de trazabilidad + manifiesto embebido) + `manifiesto.json`. **SIN BC3 ni XLSX** (D-PL-1): el texto de
> prescripcion ya viaja en el `~T` del BC3 del presupuesto. El nucleo `componer_export` es DETERMINISTA y
> VERTICAL-AGNOSTICO; **no re-renderiza** lo que ya existe: **envuelve** el compositor de pliego. El
> consumidor `pliego-obra` se registra en `_CONSUMIDORES` **sin tocar** el manifiesto/firma/sellado.

## Entrada (se LEE, no se re-ancla)
El nucleo lee el `salida-presupuesto` ANCLADO de `GOL-PRE-01/expected.json` (se LEE, no se re-ancla) y un
descriptor con `artefacto.tipo="pliego-obra"`. El descriptor PORTA, en la clave **forward-open** `pliego`,
las **refs** del `criterio` (`AQ/v2`) y del `pack_textos` (`pliego-textos/AQ-DEMO/v1`); el runner las
resuelve del repo (como `GOL-PLI-01`) y las inyecta como dicts para componer (patron vertical-agnostico: el
nucleo no lee `versions.lock`). El `content_sha256` del manifiesto es la huella canonica del
`salida-presupuesto`; la zona anclada del C5 queda intacta.

## Que ancla (conformidad por CONTENIDO — patron GOL-PLI-01/GOL-EXP-01/D3; NO bytes ni pixeles; SIN ifcopenshell)
El runner (`run_case_c5` -> `modo=export` -> despacho por `consumidor` -> `_run_export_pliego`) compone el
bundle y comprueba:
1. el `salida-presupuesto` fuente conforma su esquema; el descriptor + el manifiesto conforman sus esquemas;
2. el bundle trae **Word + PDF sellado + `manifiesto.json`** (y **NO** trae BC3, D-PL-1);
3. **Word del pliego** (el .docx de `componer_pliego`): las secciones (caratula, generales, particulares,
   trazabilidad); las **8 partidas** con **prescripcion** (texto base, sin *fallback*); **medicion**
   (cantidad == JSON +-0,001) y **coste** (importe == JSON +-0,01) por partida;
4. **PDF sellado**: por partida el codigo, la **prescripcion** (sin *fallback*), la **justificacion de
   medicion** (criterio + GUIDs trazados al modelo) y el `content_sha256`;
5. **carbono forward-open**: presente sii el `salida-presupuesto` trae `valores.carbono` (si no, ausencia
   sin error);
6. **manifiesto INTEGRO** (`content_sha256` == hash canonico del `salida-presupuesto` + versiones) = Llave 1;
7. **isCertified**: el bundle SIN firmar NO es `verified-signed` (estado `computed`) — solo la firma GPG de
   JM en el release (Llave 2) lo acuna; el hook `firmar_detached` esta presente pero el gate no lo ejecuta;
8. **DETERMINISMO**: componer 2x => Word/PDF/manifiesto identicos (sello de fecha fijo, parametro).

## Regla de oro
Un fallo NO se arregla aflojando esta golden ni el formato. Se investiga en el **nucleo/consumidor**
(`documentos/export/pliego_doc`). El Word del pliego lo guarda ademas `GOL-PLI-01` (no-regresion: el
compositor `componer_pliego` **no cambia**). El bundle solo cambia si cambia el `salida-presupuesto` fuente
(GOL-PRE-01, zona anclada), el criterio, el pack de textos, el descriptor o el diseno del formato (bump de
version del paquete).
