# Diseño · Descripciones ricas del banco (Slice A) — decisiones D-RB-1..4

> Decisiones **RATIFICADAS por JM 2026-07-12**. Namespace **D-RB** (Rico Banco). La IA propone; JM ratifica y firma (dos llaves). Se anclan en `documentos/presupuesto/DECISIONES.md`.

## D-RB-1 · Forma de la descripción rica — `resumen` + `texto` separados
El banco gana **dos campos** (patrón BEDEC/BCCA/CYPE): `resumen` (corto, para tablas y cuadro nº1) + `texto` (ampliado, para la partida detallada de mediciones). El engine mapea `descripcion = banco.get("resumen") or banco.get("descripcion")` (compatibilidad: sin `resumen`, la `descripcion` de siempre) y añade `texto` a `estado_mediciones` (aditivo). En AQ-DEMO/v1, `resumen` = copia LITERAL de la `descripcion` actual (cambio cero en campos existentes). Alternativa descartada: una sola descripción larga (mezcla texto de tabla con detalle).

## D-RB-2 · Descripciones propias del usuario — banco propio (v0)
El usuario aporta sus textos por su **propio banco** `banco/<despacho>/vN` (mecanismo ya probado con BCCA). Un **override por proyecto** (pack `descripciones/<id>` o clave del criterio) para retocar textos sin duplicar el banco queda **forward**. v0 = banco propio.

## D-RB-3 · Especificaciones estructuradas + lectura del Pset — FORWARD
El bloque `especificaciones` estructurado (tipificación HA-25/B/20/IIa: ambiente, consistencia, árido, acero, cuantía) y su **composición desde el Pset del IFC** (diferenciador de Aqyra) = slice posterior con su propia decisión. v0 = **texto libre** en el banco (suficiente; viaja en el `~T` del BC3).

## D-RB-4 · Compositor y release — bump v0.2 SIN release en el slice
`componer_documento` sube a **0.2.0** (renderiza el `texto` ampliado en mediciones); `presupuesto_doc` (export) idem. `GOL-DOC-01`/`GOL-EXP-01` amplían el oráculo (texto ampliado presente, determinismo). El release firmado `documento-presupuesto-v0.2.0` (Llave 2) **NO** se crea en este slice: se decide/firma después (el código y los golden suben; el slice queda ligero).

## Costura técnica (verificada en local, sin ifcopenshell para los compositores)

- **Anclaje del banco**: `content_hash(pack) = sha256(json.dumps(pack["contenido"], sort_keys, compact))`, y `contenido.md5_banco = md5(banco.json)`. Enriquecer `banco.json` ⇒ recomputar `md5_banco` (pack.json) ⇒ recomputar `content_sha256` (golden/expected.json). `versions.lock [packs.banco]` no guarda el hash (sólo descripción) → intacto. `test_packs.py` fija el md5 de AQ-DEMO por valor → se actualiza (Slice A lo toca a propósito).
- **Invisibilidad al recompute**: `_diff_presupuesto_c5` compara sólo `capitulo/unidad/origen/cantidad/precio_unitario/importe/trazabilidad`; `descripcion`, `resumen` y `texto` NO se comparan → `GOL-PRE-01` verde. El `texto` en `GOL-PRE-01/expected.json` es la FUENTE que leen (estáticamente) los runners de documento/export.
- **Render**: en el documento, `texto` va como párrafo bajo cada partida (tras la tabla del capítulo); en el PDF sellado, bajo la línea de justificación. El Word del export hereda por envolver `componer_documento`.
- **Oráculo robusto**: comparación por prefijo normalizado (colapso de espacios) para resistir el ajuste de línea del PDF.
