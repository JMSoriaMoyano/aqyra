# C4 — Decisiones de contrato (ancladas)

> Resueltas con JM el **2026-07-02** (OK explícito), antes de tocar código. Complementan los
> ADRs de la ficha (`../../../../Aqyra-Raiz/C4_federacion.md §2.5`), que **no se reabren**:
> QA por IDS estándar · preservar procedencia/GUIDs · EPSG + punto base DECLARADO ·
> clash fuera de C4 v1 · parser sucio = tarea 1.3.

## D1 · Forma del Maestro — AMBOS, manifiesto como fuente de verdad

El artefacto autoritativo del Maestro es el **manifiesto de federación**
(`maestro-manifiesto.schema.json`): refs a los IFC fuente (por hash), transformación
EPSG/punto-base por modelo, procedencia por disciplina y política de GUIDs. Es lo único
esquematizable y lo único honesto con los ADRs (no fundir GUIDs, preservar procedencia).
El **IFC federado** se declara en el contrato como **derivado determinista** del manifiesto —
su "esquema" es IFC4X3, no JSON — y su identidad la cubrirá la golden cuando exista el
service (tarea 1.1). El visor navega el IFC; la verdad vive en el manifiesto.

## D2 · Alcance del esquema v0.1 — 3 esquemas propios + BCF por referencia

`reglas-federacion.schema.json` (entrada) · `maestro-manifiesto.schema.json` (salida) ·
`informe-qa.schema.json` (salida: pass/fail por requisito IDS + estados S0–S7 + incidencias).
El **BCF no se re-esquematiza**: se referencia **BCF 3.0** de buildingSMART y se fija la
versión aquí y en `versions.lock`. Re-esquematizar un estándar es deuda gratuita.

## D3 · Golden C4-FED-01 — sintético con narración→IFC

Dos disciplinas del mismo edificio pequeño (**ARQ**: muros+losa+ascensor · **EST**:
pilares+losa+zapatas), compiladas con `engines/ifc` y **congeladas byte a byte** como
entrada. Determinista, sin dependencias externas. El IFC sucio es la tarea 1.3 — no entra
aquí. El caso incluye **requisitos IDS que fallan adrede** para que el informe esperado
tenga pass Y fail (y el futuro BCF tenga materia).

## D4 · Runner — extender `aqyra_golden` con dispatch por contrato; C4 nace ANCLADO

Hallazgo que lo hace obligatorio: `discover_cases()` hace glob de `C*` — un caso C4 sería
recogido por el runner actual y tratado como C1 (compile) → ROJO. Refactor mínimo:
`--schema-only` descubre y meta-valida **todos** los `packages/contracts/*/*.schema.json`;
los casos se despachan por carpeta (`C1/` → compile+recompute, intacto; `C4/` → **modo
anclado**). El modo anclado, sin service, verifica lo verificable: los ficheros del caso
conforman sus esquemas, los IFC congelados coinciden con sus hashes declarados, y la
coherencia interna (requisitos del informe ⊆ requisitos del IDS; modelos del manifiesto =
modelos de las reglas = ficheros de entrada). El recompute contra el service se conecta en
1.1 **contra el mismo expected** (misma costura que C1 en Fase 0 → Fase I).

## D5 · IDS del golden — pack nuevo `data/packs/ids/`

Fichero `.ids` (**IDS 1.0** estándar, versión fijada) + `pack.json` conforme a
`data/packs/pack.schema.json` (familia `ids` ya prevista) + golden de pack por hash, según
`FUNDACION_C6_golden_y_packs.md`. 5 requisitos comprobables sobre el caso, de los que
1–2 fallan adrede. Anclado en `versions.lock [packs.ids]`.

---

> Bloque del hilo 2.2 (service v0, tarea 1.1). Resueltas con JM el **2026-07-02**
> (OK explícito), antes de tocar código. D1–D5 no se reabren.

## D6 · IFC federado derivado — NO en v0 (v0 = manifiesto + informe)

La golden anclada no ancla ningún IFC derivado; emitir una salida sin oráculo rompe el
espíritu contract-first. El esquema deja `ifc_derivado` opcional adrede (D1: la verdad
vive en el manifiesto). El IFC derivado llega en v0.x como tarea propia, con su anclaje
decidido entonces (md5 en expected: decisión explícita con JM).

## D7 · Motor de validación IDS — implementación PROPIA mínima sobre ifcopenshell

Solo se necesitan 4 facets (entity, classification, property, attribute+pattern) y el
terreno ya está mapeado por el oráculo manual (material en
`Pset_Estructurando_Spec.Material`, no como asociación IfcMaterial; `IsExternal` en
`Pset_WallCommon`). `ifctester` sería superficie ajena que anclar y cuya semántica podría
discrepar del oráculo en los bordes — un desajuste obligaría a investigar SU comportamiento,
no el nuestro. R4-GEORREF (`origen='modulo'`) va aparte en ambos casos: presencia de
`IfcMapConversion` + `IfcProjectedCRS`. Puerta abierta a adoptar ifctester en v1 si el
pack crece más allá de estos facets.

## D8 · BCF en v0 — `bcf.emitido=false` (la emisión de topics es 1.2)

El informe declara las incidencias (con GUIDs) y el bloque `bcf` queda como en el expected
congelado: `version 3.0, emitido: false`. La emisión de topics BCF 3.0 reales es la tarea
1.2 (QA/IDS→BCF). Cambiarlo ahora obligaría a tocar el expected (prohibido).

## D9 · Empaquetado — paquete uv del workspace `aqyra-federacion`

`services/federacion/` con `src/aqyra_federacion/` + `tests/` + CLI mínimo, consumido por
el runner por import de path (mismo patrón que `engines/ifc`). Sus pytest entran al gate
añadiendo `services/federacion` al Paso 1 de `ci.yml` — una única edición quirúrgica en la
línea que ya lista los paths explícitos. Nada más de `ci.yml` se toca.

## D10 · Recompute en el runner — anclado + recompute en el MISMO `run_case_c4`

Los checks anclados actuales se conservan íntegros y se ANTEPONE el recompute:
`federar(entradas, reglas)` + `validar(maestro, ids_pack)` → comparación de manifiesto e
informe recomputados contra el MISMO `expected.json` con `tolerancias.json` (conteos y
estados exactos; traslación ±1e-6 m, rotación ±1e-9°). Más checks, nunca menos — la
costura idéntica a la que cerró C1 en Fase I·h1.

---
*Regla de oro heredada: un fallo no se arregla aflojando la golden. El CI nunca certifica
(Llave 2 = JM).*
