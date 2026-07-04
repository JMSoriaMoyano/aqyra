# Decisiones del visor — apps/visor (registro propio del vertical TS)

> Las D1–D30 del contrato C4 viven en `packages/contracts/C4-federacion/DECISIONES.md`
> y NO se mezclan aquí. Las D-001…D-007 de aqyra-entorno (record histórico firmado,
> `_import/aqyra-entorno/DECISIONES.md`) se citan como precedente. Este fichero ancla
> las decisiones V del vertical del visor. Firmadas por JM.

## V1 · Dónde vive el visor + corte — 2026-07-03 · Firmante: JM

- **Decisión:** re-home del visor a `apps/visor` con **corte mínimo**: el núcleo que
  abre+navega+selecciona+árbol (`viewer`, `ifc-loader`, `registry`, `spatial-metric`,
  `idealize`, `data-state`). Los módulos de autoría/contexto (`author`, `environment`,
  `solar`, `terrain`) y los paquetes `embed`/`openbim`/`demo` quedan en el record
  histórico para hilos posteriores.
- **Contexto que forzó la mano:** aqyra-entorno fue ARCHIVADO el 2026-07-01 (read-only,
  main `c40d10b` == el commit importado a `_import/aqyra-entorno`): el visor ya no puede
  evolucionar fuera. El PLAN §1 reserva `apps/visor` y pone el visor ENCIMA de services.
- **Procedencia (regla consolidada, Fase I):** árbol == frozen (diff limpio entre el
  Entorno local y `_import`, 2 pasadas) → el corte sale del FROZEN `_import/aqyra-entorno`
  (zona firmada; el tag `cebo-trazado-2026-06-29`, `433fe90`, verifica ahí).
- **Adaptaciones DECLARADAS del corte (todo lo demás es byte a byte):**
  1. `src/index.ts` — recortado a los módulos del corte + exporta `bcf.ts`.
  2. `src/viewer.ts` — gana el método público `setCamera(position, direction, up, fovDeg?)`
     (la cámara del viewpoint BCF, D29, no era aplicable sin él; la cámara era privada).
  3. `package.json` — scripts reales (build/typecheck/test/demo), versión 0.5.0.

## V2 · Qué significa "abrir el Maestro" en v0 — 2026-07-03 · Firmante: JM

- **Decisión:** flujo E2E demostrable y DETERMINISTA: reglas → `federar()` → `derivar()`
  (service 0.5.0) → el visor carga el DERIVADO (web-ifc), muestra la estructura espacial
  federada (los placements raíz por modelo de D27: EST rotado 30°) y LEE el árbol BCF —
  lista de topics; al seleccionar uno, cámara del viewpoint (D29) aplicada y GUIDs de
  Components resaltados.
- **Trabajo NUEVO de este hilo:** `src/bcf.ts` (lectura BCF 3.0: `parseMarkup`,
  `parseViewpoint`, `bcfCameraToViewer`). El BCF del visor histórico era un stub
  (`BcfAdapter` de `@aqyra/openbim` lanzaba "llega en F3"): no había nada que re-homear.
- **Mapeo de marcos (documentado):** el BCF escribe coordenadas IFC (Z-up); web-ifc
  entrega la geometría en Y-up. `bcfCameraToViewer`: (x, y, z)_IFC → (x, z, −y)_visor.
- **El visor CONSUME; JAMÁS re-genera el derivado** (fuente única = el service, PLAN §1).

## V3 · Anclaje del vertical (la Llave 1 del TS) — 2026-07-03 · Firmante: JM

- **Decisión:** typecheck + build REALES (adiós placeholder `exit 0` — la deuda anotada
  desde la publicación del repo) + test E2E HEADLESS que ancla lo ESTRUCTURAL:
  - el derivado congelado (`fixtures/federado.ifc`) es EL derivado: md5 byte a byte
    `dcb1e14460f3556107ce35d6dade16c3` == golden C4-FED-06 (D26);
  - conteos al abrirlo (IFC4X3, 1 IfcProject, 13 IfcElement en el fichero);
  - el árbol BCF (`fixtures/bcf/**`, md5s por fichero == golden) parsea: 3 topics,
    1 con viewpoint, y la CÁMARA parseada == expected verificado a mano en 2.6
    (pos = pb+(1,−1,1), dir = (−1,1,−1)/√3, up = (−1,1,2)/√6).
  - NO hay golden de píxeles (frágil, decisión explícita).
- **ci.yml:** gana el paso pnpm (la nota de gobierno de ci.yml ya lo autorizaba:
  "se re-añadirá con un tsc real filtrado a apps/** cuando exista el paquete").
  `release.yml` NO se toca. Los 132 checks Python heredados quedan intactos.
- **Hallazgo declarado (no parche silencioso):** el catálogo de clases del loader
  (corte v0.4) enumera 11 de los 13 IfcElement del derivado — no lista
  `IfcOpeningElement` (los huecos no son elementos de lista) ni `IfcTransportElement`
  (fuera del catálogo v0.4). El E2E ancla 11 + la presencia de ambos en el SPF.
  Ampliar el catálogo es decisión de un hilo posterior.

## V4 · Contrato del consumo — 2026-07-03 · Firmante: JM

- **Decisión:** el visor consume `ifc_derivado` del manifiesto (D30) + el árbol BCF
  (D12/D29) por **RUTA LOCAL** (v0): sin infraestructura nueva (PLAN §7). La interfaz
  de carga (`IfcLoader.open({name, data})` + parsers BCF sobre texto) queda preparada
  para C8/CDE después: C8 es decisión futura con su propio contrato.
- `fixtures/bcf-index.json` es plumbing de la demo (HTTP no lista carpetas), NO parte
  del contenedor BCF 3.0.

## V5 · Versionado + sello — 2026-07-03 · Firmante: JM

- **Decisión:** la versión del paquete en el monorepo **hereda del corte**: 0.4.0
  (frozen) + este hilo (lectura BCF con cámara + vertical anclado) = **0.5.0**.
  Sin resetear a 0.
- **Sello:** tag firmado `visor-v0.5.0` (grafía nueva del PLAN §0 — adiós `cebo-*`)
  al cierre, SI el vertical queda VERDE end-to-end y JM firma (Llave 2).

## V6 · Primer hilo de UX del visor (lote 1 — pulir el cebo) — 2026-07-03 · Firmante: JM

> El visor es el CEBO del embudo cebo-anzuelo: su trabajo es enganchar a quien mira.
> Este bloque ancla las decisiones U1–U5 del primer hilo de experiencia (Fase III·h4),
> que vacía por LOTES el embalse `apps/visor/UX_BACKLOG.md`. Render/DOM, sin tocar la
> zona anclada.

- **U1 · Alcance del lote.** Entran las 8 entradas de render/DOM (riesgo bajo):
  #1 (resaltado BCF con acento + ghost), #2 y #9 (árbol espacial INTERACTIVO
  bidireccional: plegar/desplegar + clic nodo → selección/scroll-to/zoom en la escena),
  #3 (Psets en el panel «Selección»), #4 (botón «vista general»), #5 (feedback de
  topics sin viewpoint), #7 (fondo OSCURO), #8 (canvas a TODO el contenedor `#escena`).
  **Fuera del lote:** #6 (re-base local de la escena por el jitter float32 de
  coordenadas EPSG ~4,6 M). Queda DIFERIDO como decisión propia (V): toca la
  transformación de coordenadas y podría rozar la precisión del dato y el E2E; NO entra
  sin OK explícito de JM en un hilo futuro.

- **U2 · Mudanza del backlog (regla 6) — CUMPLIDA.** `_operativo/UX_BACKLOG_visor.md`
  (gitignored) → **`apps/visor/UX_BACKLOG.md`** (trackeado); desde aquí viaja con el
  paquete. Las 8 entradas del lote quedan `en-hilo-4` y pasan a `hecha (PR #n)` al cierre.

- **U3 · Versionado + sello.** `@aqyra/visor` **0.5.0 → 0.6.0** (mejoras de UX; sin
  cambio de contrato ni de la zona anclada). `versions.lock [apps.visor].version` se
  actualiza a 0.6.0. Al cierre, tag firmado **`visor-v0.6.0`** (Llave 2, patrón
  `visor-v0.5.0`) SI el vertical queda VERDE end-to-end y JM firma.

- **U4 · Frontera dura (regla 5).** Ninguna entrada toca la ZONA ANCLADA: `fixtures/`,
  el E2E (`fixtures/federado.ifc` md5 `dcb1e14460f3556107ce35d6dade16c3` + la CÁMARA
  D29 == expected + los md5 del árbol BCF), los contratos C1/C3/C4 ni los OCHO golden.
  El visor CONSUME el derivado y el árbol BCF (V4); jamás los re-genera. Si una mejora
  exigiera tocar la zona anclada, se PARA y se convierte en decisión (V) con JM — el
  E2E no se afloja nunca.

- **U5 · Cómo se prueba la UX (sin golden de píxeles).**
  1. El E2E headless estructural (`test/federado-e2e.test.ts`) sigue VERDE con los
     MISMOS anclajes (md5 del derivado + cámara D29 + conteos + árbol BCF).
  2. Tests de COMPORTAMIENTO donde aplique: resize → el renderer adopta el tamaño del
     contenedor; `frameElement`/`frameAll` mueven la cámara al elemento/al modelo;
     `highlightSelection` con ghost atenúa lo no seleccionado; el panel lista Psets.
  3. Revisión VISUAL de la demo a ojo por JM para lo puramente visual (#7 fondo oscuro,
     #8 canvas a pantalla completa, #1 acento/ghost).

## V7 · El visor pinta el coste (5D) — 2026-07-04 · Firmante: JM

> El cebo enseña lo que el anzuelo produjo: el write-back 5D (C5 Fase IV·h3) metió el coste
> en el modelo con el modelo de coste nativo de OpenBIM; el visor lo LEE y lo PINTA. La
> demostración visible del embudo cebo-anzuelo: coste hasta el objeto, en 3D.

- **V7 · Fixture 5D + anclaje.** `apps/visor/fixtures/federado_5d.ifc` = el **mismo 5D que
  produce `GOL-PRE-02`** (federar las fixtures con `Qto` + `engines/presupuesto.escribir_coste`),
  generado una vez con ifcopenshell y anclado por md5 **`3e302e5fac409212632ae3fcd3c816ec`**
  (determinista). NO se deriva de `federado.ifc` (dcb1e144) porque sus GUIDs podrían no casar
  con la trazabilidad del presupuesto; el 5D de GOL-PRE-02 ya está probado (7 asignaciones).
  `federado.ifc` (dcb1e144) y su E2E quedan **INTACTOS** (frontera dura, U4): se AÑADE el 5D.

- **V8 · Lectura del coste (dato).** `src/cost.ts` lee `IfcCostSchedule` / `IfcCostItem` /
  `IfcRelAssignsToControl` / `IfcMonetaryUnit` con web-ifc → por elemento: las **partidas
  asignadas** (código + importe de la partida) y un **`costeAsignado`** = Σ (importe_partida /
  nº elementos de la partida) — reparto UNIFORME entre los elementos de la partida (v0; el
  reparto por cantidad es mejora futura, el Qto está en el modelo). Más totales (PEM/GG/BI/
  base/IVA/PEC del `IfcCostItem` RESUMEN + parciales por capítulo). Invariante: **Σ costeAsignado
  = PEM medible (6884,83)**. Puro dato, **testeable headless** (como el resto del vertical).

- **V9 · Visualización (opción a).** Modo "coste": **heatmap** por `costeAsignado` (rampa
  documentada) + el coste/partidas del objeto en el panel de Selección + un panel de **totales**
  (PEM/PEC + por capítulo). Solo render/DOM; no toca la zona anclada.

- **V10 · E2E.** `test/coste-5d-e2e.test.ts` ancla el **md5** del fixture (`3e302e5f…`) + el
  **mapa de coste** (importe por partida, `costeAsignado` por elemento, Σ = PEM medible, moneda
  EUR, 15 `IfcCostItem`, 7 asignaciones). Estructural, sin píxeles (patrón del E2E del derivado).

- **V11 · UX_BACKLOG.** El lote 1 (0.6.0, PR #26) ya cerró #1–5, #7–9 (V6/U1 los incluía
  todos); se marcan `hecha (PR #26)`. #6 (re-base local por jitter float32) sigue **diferido**.
  Sin nuevo trabajo de UX en este hilo.

- **V12 · Versionado + sello.** `@aqyra/visor` **0.6.0 → 0.7.0** (feature 5D; sin cambio de la
  zona anclada). `versions.lock [apps.visor].version` → 0.7.0. Al cierre, tag firmado
  **`visor-v0.7.0`** (Llave 2, patrón `visor-v0.6.0`) si el vertical queda VERDE y JM firma.
