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
*Regla de oro heredada: un fallo no se arregla aflojando la golden. El CI nunca certifica
(Llave 2 = JM).*
