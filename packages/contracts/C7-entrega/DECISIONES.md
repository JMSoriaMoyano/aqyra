# C7-entrega — DECISIONES (D-C7-1 … D-C7-6)

> El **operador de ENTREGA** (C7): orquesta la ENTREGA de un PAQUETE de entregables firmables como una
> unidad, con un manifiesto-entrega maestro (roll-up). Contract-first (ficha + esquemas ANTES del
> módulo, patrón C4/C5). **Ratificadas por JM 2026-07-13** (D-C7-1..6, incluidas las dos sub-decisiones
> subrayadas). Namespace propio **D-C7**. La IA propone; JM ratifica y firma (dos llaves).

> **Reconciliación (D-C7-1) con la ficha `Aqyra-Raiz/C7_operador.md`:** esa ficha describe C7 como el
> operador IA NO determinista. La decisión de JM 2026-07-13 lo parte en dos capas — el **cerebro**
> conversacional (Cowork + skills + subagentes, YA existe) que PROPONE la solicitud, y las **manos
> deterministas** (este service) que la ejecutan. Las 4 garantías de la ficha se conservan y se
> refuerzan; el foso (entregable firmable) vive dentro de C7-entrega. Ver `contrato.md §Reconciliación`.

## D-C7-1 · Casa y naturaleza
Service NUEVO `services/entrega` (uv `aqyra-entrega`), hermano de `services/federacion` (C4). C7 es un
**OPERADOR DETERMINISTA PURO (sin LLM)**: el compañero IA lo conduce desde fuera. API
`componer_entrega(solicitud: dict, parametros?: dict) -> Path(paquete)`. Consume artefactos YA anclados;
**no recalcula**; **envuelve** `documentos/export.componer_export` (no reimplementa el sellado/firma).
Contrato/carpeta = `C7-entrega`.

## D-C7-2 · Contrato contract-first (2 esquemas NUEVOS, forward-open, JSON Schema 2020-12, ANTES del módulo)
`solicitud-entrega.schema.json` (entrada: `{proyecto, hito?, entregables:[{consumidor,
artefacto|artefacto_ref, descriptor}], sello_tiempo, versiones_ancladas}`) +
`manifiesto-entrega.schema.json` (salida: `{esquema, generador, sello_tiempo, proyecto, maestro_ref?,
entregables:[{consumidor, nombre_bundle, content_sha256_manifiesto}], paquete_sha256,
versiones_ancladas}`).
**Sub-decisión ratificada: C7 NO lee el repo ni `versions.lock`** — recibe descriptores PRE-RESUELTOS
(el compañero IA resuelve las refs de packs antes de llamar), igual que el núcleo de export es
vertical-agnóstico y espera que el caller resuelva. En `GOL-EN-01` el arnés `run_case_c7` juega el papel
del compañero IA y resuelve `criterio`+`pack_textos` del repo como el runner de `GOL-EXP-03`.

## D-C7-3 · Alcance v0
El paquete contractual **presupuesto + pliego** (consumidores `presupuesto-obra` + `pliego-obra`), ambos
sobre el **MISMO** `salida-presupuesto` anclado de `GOL-PRE-01` (el roll-up los ata al mismo Maestro).
Sin nuevos consumidores (cumplimiento/cálculo/coordinación/carbono = **forward**). Sin colocación en el
CDE por estado ISO 19650 S0–S7 (C8 = **forward**). `maestro_ref` **opcional/ausente en v0**. El operador
compone SOLO desde `entregable['artefacto']` inline; `artefacto_ref` es traza (lo resuelve el compañero IA).

## D-C7-4 · Determinismo + roll-up
`manifiesto-entrega` DETERMINISTA (mismos artefactos + misma solicitud + mismo sello ⇒ byte a byte; sello
= parámetro, **nunca `now()`**). Integridad en dos niveles: (a) cada `manifiesto.json` individual íntegro
vía `documentos/export.manifiesto.integridad` (recomputa el `content_sha256` del artefacto).
**Sub-decisión ratificada (b): `content_sha256_manifiesto` por entregable = sha256 de la forma serializada
del `manifiesto.json` individual entero** (no solo el campo `artefacto.content_sha256` interno), y
`paquete_sha256` = sha256 de la lista **ordenada** (lexicográfica, independiente del orden de entrada) de
esos `content_sha256_manifiesto`. Así el maestro ata todo el contenido de cada manifiesto, no solo el
artefacto.

## D-C7-5 · Golden `GOL-EN-01` (Llave 1)
Contrato `C7-entrega`, rama `run_case_c7` registrada en `CASE_RUNNERS["C7"]` (los 2 esquemas entran
solos en el Paso 1 por el glob `C*/*.schema.json`; el caso `packages/golden/C7/GOL-EN-01/` entra solo
por el glob `C*/` con `expected.json`). Lee la `solicitud-entrega` (presupuesto+pliego, fuente
`C5/GOL-PRE-01`); compone el paquete; comprueba: solicitud + manifiesto-entrega conforman sus esquemas;
el paquete trae los 2 bundles (formatos + `manifiesto.json`) + el `manifiesto-entrega`; cada manifiesto
individual íntegro; `content_sha256_manifiesto` == sha256 del `manifiesto.json` del bundle;
`paquete_sha256` == roll-up; mismo Maestro (los N anclan el mismo artefacto); `isCertified`: paquete SIN
firmar NO es `verified-signed` (`computed`); DETERMINISMO (componer 2×). Corre **SIN ifcopenshell** (LEE
el `salida-presupuesto` anclado; los compositores son puros). No-regresión: GOL-EXP-01/03, GOL-PLI-01, el
núcleo de export y los motores **INTACTOS**.

## D-C7-6 · Dos llaves + frontera con el compañero IA
Llave 1 = `GOL-EN-01` verde. Llave 2 = firma GPG de JM del `manifiesto-entrega` (release `entrega-v0.1.0`
= decisión de JM; **por defecto SIN release nuevo en el slice**). El compañero IA **propone** la
`solicitud-entrega` (puede apoyarse en la matriz LOIN); el operador la valida y ejecuta; el LLM **no** se
invoca dentro de `componer_entrega`.

## Zona anclada (frontera dura)
Este hilo solo **AÑADE**: `packages/contracts/C7-entrega/` (ficha + 2 esquemas + este `DECISIONES.md`) +
`services/entrega/` (`entrega.py` + `manifiesto_entrega.py` + `__init__`/`cli`/`pyproject` + tests) +
`packages/golden/C7/GOL-EN-01/` + `run_case_c7` y `CASE_RUNNERS["C7"]` en `run_golden.py` + anclaje
(`versions.lock [contracts.C7]`/`[services.entrega]`, `pyproject [tool.uv.workspace]`, `ci.yml`) +
`openspec/changes/c7-entrega-v0/`. **Nunca** toca el núcleo de export (descriptor/manifiesto/sellado/
firma), `componer_export`, los consumidores `presupuesto-obra`/`pliego-obra`/`proyeccion-valor`, los
compositores (`componer_documento`/`componer_pliego`), `emitir_bc3`, los golden GOL-EXP-01/02/03,
GOL-PLI-01, GOL-PRE-*, los motores, los esquemas de contrato existentes ni los packs anclados. Todo es
AÑADIR.
