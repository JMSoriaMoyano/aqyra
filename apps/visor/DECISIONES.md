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
