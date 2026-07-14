# Diseño · c7-entrega-v0 (operador de ENTREGA C7)

## Principio — envolver, no re-implementar; determinista, sin LLM
La maquinaria de sellado+firma (`documentos/export.componer_export`) ya produce un BUNDLE firmable +
`manifiesto.json` a partir de un artefacto autoritativo + un descriptor. C7 **no re-implementa** nada:
orquesta un PAQUETE de entregables llamando a `componer_export` por cada uno y emite UN
`manifiesto-entrega` maestro. El no-determinismo (interpretar «prepara la entrega del proyecto básico»,
construir la solicitud) vive **FUERA**, en el compañero IA (Cowork/skills/agentes); C7 recibe una
`solicitud-entrega` ya conformada, la valida y la ejecuta reproducible.

## Operador `componer_entrega(solicitud, parametros?) -> Path(paquete)`
Por cada `entregable` de la solicitud: toma el `artefacto` inline (v0: la resolución de `artefacto_ref`
es del compañero IA), propaga el `sello_tiempo` del paquete al descriptor si no lo trae, y llama
`componer_export(artefacto, descriptor, {salida: paquete/<consumidor>})`. Recoge el `manifiesto.json` de
cada bundle, calcula `content_sha256_manifiesto = sha256(bytes del manifiesto.json)` y ensambla el
`manifiesto-entrega`.

## Manifiesto-entrega y roll-up (`manifiesto_entrega.py`)
`{esquema: "manifiesto-entrega/v0", generador, version_generador, sello_tiempo, proyecto, hito?,
maestro_ref?, entregables:[{consumidor, nombre_bundle, content_sha256_manifiesto}], paquete_sha256,
versiones_ancladas}`. `paquete_sha256 = sha256(json canónico de la lista ORDENADA de
content_sha256_manifiesto)` — ordenada lexicográficamente para ser independiente del orden de entrada.
`integridad(manifiesto, sha_por_bundle)` recomputa cada sha256 y el roll-up (Llave 1, pure-python, sin
GPG). Determinista: sello = parámetro, nunca `now()`; `serializar` con claves ordenadas.

## Contrato (2 esquemas forward-open, ANTES del módulo)
`solicitud-entrega.schema.json`: `entregables[]` con `anyOf` `artefacto`|`artefacto_ref`, `descriptor`
requerido (es un descriptor-export ya conformado; para pliego porta la clave `pliego`). `C7 no lee el
repo`: descriptores pre-resueltos (D-C7-2). `manifiesto-entrega.schema.json`: `paquete_sha256` y
`content_sha256_manifiesto` con patrón `^[0-9a-f]{64}$`.

## Golden GOL-EN-01 (`run_case_c7`, `CASE_RUNNERS["C7"]`)
El arnés juega el papel del compañero IA: lee la solicitud almacenada (`entrada.json`, con
`artefacto_ref: C5/GOL-PRE-01` + refs de packs del pliego), resuelve el `salida-presupuesto` anclado y
`criterio/AQ/v2` + `pliego-textos/AQ-DEMO/v1` (como `GOL-EXP-03`), construye la solicitud de ejecución
con el artefacto INLINE + los dicts resueltos y llama `componer_entrega`. Comprueba: esquemas (solicitud
+ manifiesto-entrega); paquete = 2 bundles (formatos + `manifiesto.json`) + `manifiesto-entrega`; pliego
sin BC3; cada manifiesto individual íntegro; `content_sha256_manifiesto` == sha256 del `manifiesto.json`;
roll-up (`paquete_sha256`); mismo Maestro (los 2 anclan el mismo artefacto); isCertified (sin firma !=
verified-signed); DETERMINISMO. SIN ifcopenshell.

## No-regresión / forward-open
Añade contrato + service + golden + `run_case_c7`. No toca el núcleo de export, `componer_export`, los
consumidores, `componer_documento`/`componer_pliego`, `emitir_bc3`, GOL-EXP-01/02/03, GOL-PLI-01,
GOL-PRE-*, los motores, los esquemas existentes ni los packs. Nuevos consumidores, CDE (C8), maestro_ref,
LOIN/hito, re-entrega y PAdES = forward.
