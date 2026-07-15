# Cambio · Descripciones ricas del banco — `resumen` + `texto` ampliado (Slice A)

> Change-id: `c5-descripciones-ricas` · Capas: `data/packs`, `engines/presupuesto`, `documentos/` · Consume/toca: contrato `C5-presupuesto` (aditivo)
> Historia del backlog: **Slice A** del hilo *presupuesto/pliego ricos* (`INICIO-hilo` A+B+C, 2026-07-12), forward de **E6.2/PR #60** (export firmable contractual).
> Estado: **APPLY** · decisiones **D-RB-1..4 RATIFICADAS por JM 2026-07-12** (resumen/texto separados · banco propio v0 · especificaciones=forward · bump v0.2 sin release).
> Tipo: **extensión ADITIVA forward-open del motor de valoración C5** (banco pack + engine + compositores). **NO** toca el raíl de export (que ya renderiza lo que le llega), ni el coste anclado.

## Por qué

Al revisar el bundle firmable de E6.2, JM detectó que las descripciones de las partidas son de **una sola línea**, frente a los bancos reales (BEDEC/BCCA/CYPE) que llevan, además del título corto, un **texto ampliado** con la especificación de la unidad de obra (materiales, ejecución, alcance del precio y criterio de medición). Slice A cierra esa carencia: el banco gana descripción rica y el motor la **arrastra** a la salida C5, de modo que los documentos contractuales (presupuesto Word + PDF sellado del export) la rendericen.

## Qué cambia (superficie)

- **`data/packs/banco/AQ-DEMO/v1/`** — cada partida gana `resumen` (corto, = descripción actual, cambio CERO en campos existentes) + `texto` (ampliado, nuevo). Re-anclaje ADITIVO: `pack.json.contenido.md5_banco` + `golden/expected.json.content_sha256` recomputados (el **precio no se toca**: PEM/PEC intactos). `partidas` y `costes_indirectos_pct` intactos.
- **`engines/presupuesto`** 0.5.0 → **0.6.0** — `presupuestar(...)` mapea `descripcion = banco.resumen or banco.descripcion` (compatibilidad con bancos v0) y ARRASTRA `texto` a `estado_mediciones[]` (aditivo, sólo `origen=modelo`). Invisible al recompute (`_diff_presupuesto_c5` compara claves nombradas) → `GOL-PRE-01` recomputa idéntica.
- **`documentos/presupuesto`** 0.1.0 → **0.2.0** — `componer_documento` renderiza el `texto` ampliado bajo cada partida en la sección de mediciones (forward-open: sin `texto`, no imprime nada). ÚNICO toque de un paquete firmado (bump previsto, D-RB-4).
- **`documentos/export`** — `presupuesto_doc.py` (PDF sellado) renderiza el `texto` bajo la partida. El Word contractual lo hereda por envolver `componer_documento`. El `~T` del BC3 ya transporta el texto largo (INTOCABLE).
- **`packages/golden/C5/GOL-PRE-01/expected.json`** — se añade `texto` a las 7 partidas `origen=modelo` del bloque `presupuesto` (números INTACTOS; es la fuente que leen GOL-DOC-01/GOL-EXP-01). Diff de exactamente 7 líneas.
- **`packages/golden/src/aqyra_golden/run_golden.py`** — GOL-DOC-01 (`modo=documento`) y GOL-EXP-01 (`modo=export`) amplían el oráculo: el `texto` ampliado de cada partida presente en el documento/Word/PDF (comparación robusta al wrap). Determinismo intacto.
- **`engines/presupuesto/tests/test_presupuesto.py`** — dos tests nuevos: arrastre de `texto` (descripcion=resumen, texto literal, S&S sin texto) + fallback sin `resumen`.
- **`packages/packs/tests/test_packs.py`** — el md5 fijado de AQ-DEMO se actualiza al banco enriquecido (Slice A lo toca a propósito).
- **`versions.lock`** — `engine_version` 0.6.0 + nota de la clave `texto`/`resumen`; `[documentos.presupuesto]` a 0.2.0.
- **`documentos/presupuesto/DECISIONES.md`** — se anclan **D-RB-1..4**.

## Impacto — por qué NO rompe nada (verificado en local)

- **El coste NO se mueve.** `GOL-PRE-01` PEM 7 022,53 → PEC 10 111,74 idéntico (recompute reproducido byte a byte en los números; `texto`/`resumen` son claves nuevas invisibles al comparador). `GOL-PRE-02/03/04/05`, `GOL-CAR-01/02` intactas (mismo banco, precios sin cambio).
- **El contrato C5 no se re-ancla.** `partida_medida` es abierto (`additionalProperties: true`): `texto` es aditivo (patrón `traza_cantidades`), `schema_version` se mantiene.
- **El raíl de export (Nivel 1) no se toca en su núcleo.** Sólo el consumidor `presupuesto-obra` (PDF) renderiza una clave más que ya viene en el artefacto.
- **Compatibilidad con bancos v0.** Sin `resumen`, `descripcion` = la de siempre; sin `texto`, no se imprime nada.

## Fuera de alcance (fronteras honestas — forward)

- **Especificaciones estructuradas** (tipificación HA-25/B/20/IIa) y su **lectura del Pset** del modelo (D-RB-3) = slice posterior; en v0 el texto es libre en el banco.
- **Override de textos por proyecto** (D-RB-2) = forward; en v0, el usuario aporta su **propio banco** `banco/<despacho>/vN`.
- **Detalle dimensional por objeto** en la descripción = forward.
- **Sin release** en este slice (D-RB-4): el bump `documento-presupuesto-v0.2.0` lo firma JM cuando decida (Llave 2).
- Capítulos por clasificación (Slice B) y pliego firmable (Slice C) = changes separados.
