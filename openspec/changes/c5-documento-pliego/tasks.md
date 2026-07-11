# Tareas · Compositor de PLIEGO (E4.1) + textos base (E5.3) — `c5-documento-pliego`

> Gobernado por `docs/PROCESO_SDD.md`. **NUEVO documento** (capa `documentos/`, patrón `documento-presupuesto`); **CONSUME** C5. Delta de spec del contrato **NULO**. Zona anclada intocable: motor (`engines/presupuesto` 0.5.0), esquema de salida C5, eje coste, eje carbono, `documentos/presupuesto` 0.1.0, `GOL-PRE-01/02/03`, `GOL-DOC-01`, `GOL-CAR-01/02`, packs `criterio/AQ/v1`+`v2`, `banco/AQ-DEMO/v1`, `banco/AQ-BC3-DEMO/v1`, `banco-carbono/generico/v1`+`v2` (identidad por hash). Gobierna **N-04/D-026** (E5.3 real supeditado a licencia verificada).

## Paso 0 · Ratificación (BLOQUEA el código) — RATIFICADO por JM 2026-07-11
- [x] JM ratifica **D1** (casa/API + `formato.py` **espejado** — opción A).
- [x] JM ratifica **D3** (contenido por partida: **cuarteto** prescripción + medición + coste + carbono forward-open).
- [x] JM ratifica **D4** (**cadena con fallback**: banco → pack de textos base → descripción).
- [x] JM ratifica **D5** (semilla **PROPIA** `pliego-textos/AQ-DEMO/v1` ahora; PG-3/CTE real por la vía limpia, licencia N-04). Registro `Aqyra-Negocio/RECONCILIACION_licencias-pliego.md`.
- [x] JM ratifica **D6** (golden por contenido, rama `modo="pliego"`; entrada = presupuesto de `GOL-PRE-01`).
- [x] JM ratifica **D2/D7** (`.docx` forward-PDF; anclaje `[documentos.pliego]` + `[packs.pliego_textos]`; nueva familia `pliego-textos`).
- [x] Anclar **D1–D7** en `documentos/pliego/DECISIONES.md` (escrito). — en este PR

## Paso 1 · Rama (primero, tras ratificar) — host
- [ ] Crear y cambiar a `feat/c5-documento-pliego` desde `origin/main` (git por `.bat` en el host).

## Paso 2 · Semilla PROPIA de textos base (E5.3 v0, contract-first) — apply
- [ ] `data/packs/pliego-textos/AQ-DEMO/v1/textos.json` — texto de prescripción PROPIO de Aqyra (condiciones de material/ejecución/control/medición y abono) por partida/tipo de unidad de las 7 medibles (`FAB010, REV010, PIN010, EHL010, EHS010, CSZ010, PPM010`) + clave por Uniclass Ss (de `reglas_sistema`). Marcado **demo** en metadatos.
- [ ] `.../pack.json` — manifiesto (`familia:"pliego-textos"`, `fuente`="Aqyra propio (demo)", `contenido` con `md5_textos`, claves de mapeo).
- [ ] `.../golden/expected.json` — `content_sha256` + md5(textos.json).
- [ ] `pack.schema.json` — añadir `pliego-textos` al enum de familias (aditivo).
- [ ] `packages/packs/tests/test_packs.py` — golden de pack de `pliego-textos` (hash + md5) + guarda de que los packs anclados NO se mueven.

## Paso 3 · Compositor `documentos/pliego` (espejo de `documentos/presupuesto`) — apply
- [ ] `documentos/pliego/pyproject.toml` — paquete `aqyra-documento-pliego` 0.1.0 (dep `python-docx>=1.1`); alta en `[tool.uv.workspace]` raíz.
- [ ] `documentos/pliego/src/aqyra_documento_pliego/formato.py` — **espejo** del formato del despacho in-repo (D1-A).
- [ ] `.../compositor.py` — `componer_pliego(presupuesto, criterio, parametros?)`: carátula · condiciones generales · prescripciones particulares por capítulo/sistema (prescripción + medición + coste + carbono forward-open) · trazabilidad. Cadena de fuente de texto (D4). Determinista, sin LLM, NO recalcula.
- [ ] `.../cli.py`, `.../__init__.py` (versión 0.1.0, API pública).
- [ ] `documentos/pliego/tests/test_compositor.py` — unit-test texto puro (sandbox): compone sobre el presupuesto de `GOL-PRE-01` + `pliego-textos/AQ-DEMO/v1`; extrae con python-docx y verifica secciones, 8 partidas con prescripción/medición/coste, trazabilidad, carbono forward-open, y **determinismo** (2× idéntico).

## Paso 4 · Golden `GOL-PLI-01` (por contenido) — apply
- [ ] `packages/golden/C5/GOL-PLI-01/{expected.json, ficha.md, tolerancias.json}` — `modo:"pliego"`, `fuente_presupuesto:"GOL-PRE-01"`, `pack_textos:"pliego-textos/AQ-DEMO/v1"`, `criterio:"AQ/v2"`. Oráculo por CONTENIDO (D6). `GOL-PRE-01` se LEE, no se re-ancla.
- [ ] `packages/golden/src/aqyra_golden/run_golden.py` — AÑADIR rama `modo=="pliego"` en `run_case_c5` (patrón de la rama `documento`): carga el presupuesto anclado + criterio + pack de textos, compone, extrae y verifica. Único fichero de código del runner tocado; `GOL-DOC-01`/`GOL-CAR-*`/`GOL-PRE-*` siguen verdes.

## Paso 5 · Anclaje + registro — apply
- [ ] `versions.lock` — filas `[documentos.pliego]` (espejo de `[documentos.presupuesto]`) + `[packs.pliego_textos]`. `[documentos.presupuesto]` y anclas existentes intactas.
- [ ] `documentos/pliego/DECISIONES.md` — D1–D7 ancladas.
- [ ] `Aqyra-Negocio/RECONCILIACION_licencias-pliego.md` — abrir el registro de licencia de PG-3/PG-4 + CTE DB (las 4 preguntas), estado «pendiente de verificación por JM»; condición suspensiva de E5.3 real.

## Paso 6 · No-regresión + verificación local (conda `mcp-bim`)
- [ ] Sandbox (texto puro): `pytest documentos/pliego/tests` + `pytest packages/packs/tests/test_packs.py` + conformidad de esquema del pack.
- [ ] Conda `mcp-bim` (ifcopenshell / runner completo): `pytest packages/golden` → `GOL-PLI-01` verde y `GOL-PRE-01/02/03` + `GOL-DOC-01` + `GOL-CAR-01/02` **byte-idénticas/intactas**.
- [ ] Verificar por md5 del host: packs anclados intactos; esquema de salida C5 sin tocar; motor sin tocar; `documentos/presupuesto` sin tocar.

## Pasos obligatorios (Llave 1)
- [ ] `adversarial-review c5-documento-pliego`: el pliego conforma; solo `documentos/pliego` en `documentos`; solo `GOL-PLI-01` en golden nuevo; solo `pliego-textos/*` en `data/packs`; motor/esquema/eje-coste/eje-carbono/`documentos/presupuesto` sin tocar; secretos fuera del staged.
- [ ] `opsx:archive` → **PR** `feat/c5-documento-pliego` → `main`; gate verde (Llave 1).
- [ ] **Llave 2 = JM** (merge/firma). **SIN release** (salvo decisión de JM).

## Fuera de estas tareas
- Reempaquetar PG-3/PG-4/CTE DB sin licencia verificada (E5.3 real; hilo/adición aparte tras N-04) · write-back del pliego al IFC · dashboard (E6, Ola 4) · tocar el eje coste/carbono, sus golden/packs, el esquema de salida, el motor o `documentos/presupuesto`.
