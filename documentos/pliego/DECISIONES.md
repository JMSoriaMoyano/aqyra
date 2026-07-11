# documentos/pliego — DECISIONES (D1–D7)

> El **compositor del Pliego de Condiciones Técnicas**: convierte la salida AUTORITATIVA de C5
> (`salida-presupuesto` JSON — estado de mediciones trazable + `valores` por eje) más el `criterio`
> (mapeo partida→sistema) y el texto de prescripción, en el **pliego firmable** con el formato del
> despacho (Word .docx). Es **DETERMINISTA** (formatea datos ya calculados; sin LLM) y es el **segundo
> ladrillo de la capa de documentos** que el operador C7 orquestará. Cierra el trío **coste + carbono +
> prescripción** sobre la misma medición. **Ratificadas por JM 2026-07-11** (E4.1 + E5.3, Ola 3).

## D1 · Casa y API — paquete `documentos/pliego` (espejo)
El compositor vive en **`documentos/pliego`** (paquete uv `aqyra-documento-pliego`), **no** en
`engines/*` (no calcula) ni `services/*`. Espejo de `documentos/presupuesto`.
API: `componer_pliego(presupuesto: dict, criterio: dict, parametros: dict | None = None) -> Path`
(escribe el `.docx` y devuelve su ruta). Consume el `salida-presupuesto` JSON + el `criterio`; **no
recalcula nada**. **`formato.py` ESPEJADO** (copia in-repo), NO importado de `documentos/presupuesto`
(paquete firmado v0.1.0): mantiene hermeticidad, desacopla versiones y evita dependencia entre
documentos. Si aparece un tercer documento, extraer a un módulo común (forward).

## D2 · Formato de salida — `.docx`
`.docx` con el formato del despacho, **revisable por el técnico antes de firmar**. PDF queda como
**gancho forward** (render posterior), no en v0. **Sin píxeles anclados.** Estilo replicado in-repo
(`formato.py`: A4/Arial 11, tablas 9,5, cabecera azul repetida).

## D3 · Contenido del pliego por partida — el cuarteto sobre la partida
Cada partida lleva: **prescripción** (condiciones de materiales/ejecución/control/medición y abono) +
**medición** trazable (`cantidad`, `unidad`, `criterio_aplicado`, GUIDs de `trazabilidad`) + **coste**
(`importe`, `precio_unitario`) + **carbono** (`valores.carbono` con etapas A1A3/A4A5) **forward-open**
— si el `presupuesto` fuente trae `valores.carbono`, el pliego lo incluye; si no, ese bloque se omite
(nunca error). Es el cierre del trío que persigue la Ola 3.

## D4 · Fuente del texto de prescripción — cadena con *fallback*
Precedencia determinista: (1) **texto del banco** por partida (bancos reales BEDEC/CYPE / `~T` del BC3
ingerido), cuando exista; (2) **pack de textos base** (`pliego-textos/…`) por partida/tipo de unidad;
(3) **fallback por clasificación Uniclass**; (4) descripción de la partida + aviso «prescripción base
pendiente de completar». Para `GOL-PLI-01` (sobre `AQ-DEMO`, sin texto de banco) manda el paso 2,
dejando `AQ-DEMO/v1` intacto.

## D5 · Textos base (E5.3) — semilla PROPIA ahora, texto REAL por la vía limpia
Como el coste (`AQ-DEMO` propio) y el carbono (`generico/v1` sintético → `v2` real), la prescripción
arranca con una **semilla PROPIA**: `pliego-textos/AQ-DEMO/v1` (texto de Aqyra, marcado **demo**),
para no bloquear E4.1 en la puerta de licencia. El texto normativo **REAL** (PG-3/PG-4 del Ministerio
de Transportes; CTE DB del BOE) entra después como adición (`pliego-textos/<PG-3|CTE-DB>/vN`),
**verificada su licencia de redistribución** (N-04/D-026, *público ≠ ingestable*, las 4 preguntas) y
ratificada por JM — registro `Aqyra-Negocio/RECONCILIACION_licencias-pliego.md` (condición suspensiva).

## D6 · Golden `GOL-PLI-01` — por CONTENIDO (patrón GOL-DOC-01/D3)
Conformidad por **CONTENIDO extraído** (python-docx, NO OCR/bytes/píxeles). Runner: rama
**`modo="pliego"`** bajo `run_case_c5` (patrón `documento`/`carbono`), **sin runner nuevo** en
`CASE_RUNNERS`. Entrada: el `presupuesto` de **`GOL-PRE-01`** (se LEE anclado, no se re-ancla) +
`criterio/AQ/v2` + `pliego-textos/AQ-DEMO/v1`. Ancla: secciones presentes; 8 partidas con prescripción
(sin *fallback*), medición (±0,001) y coste (±0,01); trazabilidad (GUIDs); carbono forward-open;
DETERMINISMO (2× idéntico). Como `GOL-DOC-01`, **no** pasa por `medir()`.

## D7 · Anclaje y versionado
`[documentos.pliego]` en `versions.lock` (espejo de `[documentos.presupuesto]`). Pack
`pliego-textos/AQ-DEMO/v1` anclado por `content_sha256` + md5 en `versions.lock [packs.pliego_textos]`
y su golden de pack en `test_packs.py`. Nueva familia `pliego-textos` en `pack.schema.json` y en
`aqyra_packs.FAMILIAS` (aditivo). Versión **0.1.0**; tag firmado **`documento-pliego-v0.1.0`** (Llave 2,
firma humana de JM) — **sin release salvo decisión de JM**.

## Zona anclada (frontera dura)
Este paquete solo **AÑADE** `documentos/pliego` + `data/packs/pliego-textos/AQ-DEMO/v1` + el caso
`GOL-PLI-01` + edición quirúrgica de `run_golden.py` (rama `modo=pliego`) / `versions.lock` /
`pack.schema.json` / `aqyra_packs/__init__.py` / `test_packs.py` / `[tool.uv.workspace]`. **Nunca** toca
el contrato ni los golden/packs del C5 (`GOL-PRE-01/02/03`, `GOL-CAR-01/02`, `GOL-DOC-01` y sus
`expected`), ni el eje coste, ni el eje carbono, ni `engines/*`, `services/*`, `packages/core`,
`apps/visor`, ni **`documentos/presupuesto`** (paquete firmado — se **espeja**, no se importa).
