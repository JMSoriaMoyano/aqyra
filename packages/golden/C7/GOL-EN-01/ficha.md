# Golden GOL-EN-01 — OPERADOR DE ENTREGA C7 (services/entrega)

> El caso que cierra el arco «de sellar UN entregable a orquestar una ENTREGA». El operador
> DETERMINISTA `componer_entrega` toma una `solicitud-entrega` YA CONFORMADA (el paquete contractual
> **presupuesto + pliego**, ambos sobre el MISMO `salida-presupuesto` autoritativo anclado en
> `C5/GOL-PRE-01` — se LEE), **envuelve** `documentos/export.componer_export` sobre cada entregable
> (no reimplementa el sellado/firma) y emite UN `manifiesto-entrega` maestro que ata los N bundles al
> mismo paquete/Maestro por un **roll-up** (hash canonico de la lista ordenada de los sha256 de los
> manifiestos individuales). Sin LLM: el companero IA propone la solicitud desde fuera; C7 la valida y
> la ejecuta reproducible. No certifica (dos llaves).

## Entrada (se LEE, no se re-ancla)
`entrada.json` = la `solicitud-entrega` ALMACENADA (2 entregables con `artefacto_ref: C5/GOL-PRE-01`
+ descriptor; el pliego porta `pliego={criterio_ref: AQ/v2, pack_textos_ref: pliego-textos/AQ-DEMO/v1}`).
El arnes `run_case_c7` juega el papel del companero IA: resuelve el `salida-presupuesto` anclado de
`C5/GOL-PRE-01` (se LEE, no se re-ancla) y las refs de packs del pliego (como `GOL-EXP-03`), y
construye la solicitud de ejecucion con el **artefacto INLINE + los dicts resueltos** antes de invocar
a `componer_entrega`. Los dos entregables descienden del MISMO artefacto — el roll-up los ata al mismo
Maestro.

## Que ancla (conformidad por ESTRUCTURA + INTEGRIDAD — patron GOL-EXP-01/03/D3; NO bytes ni pixeles; SIN ifcopenshell)
El runner (`run_case_c7`, despacho por `CASE_RUNNERS["C7"]`) compone el paquete y comprueba:
1. la `solicitud-entrega` almacenada conforma `solicitud-entrega.schema.json`;
2. el `manifiesto-entrega` conforma `manifiesto-entrega.schema.json`;
3. el paquete trae los 2 bundles, cada uno con sus formatos declarados (presupuesto = Word/PDF/BC3/XLSX;
   pliego = Word/PDF, **sin BC3**) + su `manifiesto.json`, y el `manifiesto-entrega` en la raiz;
4. cada `manifiesto.json` individual es INTEGRO (`documentos/export.manifiesto.integridad` recomputa su
   `content_sha256` contra el `salida-presupuesto` + versiones);
5. el `content_sha256_manifiesto` de cada entregable == sha256 del `manifiesto.json` de su bundle;
6. **roll-up**: `paquete_sha256` == hash canonico de la lista ORDENADA de esos sha256 (Llave 1);
7. **mismo Maestro**: los 2 bundles anclan el MISMO `artefacto.content_sha256`;
8. **isCertified**: el paquete SIN firmar NO es `verified-signed` (los bundles quedan `computed`; no hay
   `.asc` del manifiesto-entrega) — solo la firma GPG de JM en el release (Llave 2) lo acuna;
9. **DETERMINISMO**: componer 2x => manifiesto-entrega + manifiestos de bundle identicos (sello fijo,
   parametro, nunca `now()`).

## Regla de oro
Un fallo NO se arregla aflojando esta golden. Se investiga en el **operador** (`services/entrega`). El
contenido PROFUNDO de cada bundle (partidas, PEC, prescripcion, medicion, justificacion) ya lo guardan
`GOL-EXP-01` (presupuesto) y `GOL-EXP-03` (pliego); aqui C7 ancla que el PAQUETE ata los N bundles al
mismo Maestro por un roll-up determinista, integro y sin firmar. El paquete solo cambia si cambia el
`salida-presupuesto` fuente (GOL-PRE-01, zona anclada), la solicitud, o el diseno del manifiesto-entrega
(bump de version del service). No-regresion: GOL-EXP-01/03, GOL-PLI-01 y el rail de export INTACTOS.
