# Borrador de tests (test-first) · Chrome del visor v0.6 sobre el shell

> Los tests se escriben ANTES del código (TDD, `frontend-standards.md`). El núcleo puro va headless
> (vitest, **sin wasm**); lo visual, por revisión de la demo del shell a ojo por JM. La zona anclada
> (`fixtures/`, `federado-e2e.test.ts`, cámara D29, golden C4/C3) NO se toca ni se re-baseliniza.

## Slice A — tematización + rail

```ts
// apps/aqyra-shell/test/tematizacion.test.ts (headless, sin wasm)
// Fuente de acento por disciplina + estado del rail.
- temaDisciplina("diseno")      → { acc: "#2f6bed", accSoft: "rgba(47,107,237,0.16)" }
- temaDisciplina("estructuras") → { acc: "#e07a4f", ... }
- railEstados()                 → diseno/estructuras `activa`; instalaciones/lineales/puentes
                                  `bloqueada` (motivo: "ingesta")  // D-CH-2
- pulsar una disciplina bloqueada NO cambia --acc (sólo emite aviso)
```

## Slice B — panel flotante + chip de estado

```ts
// apps/aqyra-shell/test/seleccion-flotante.test.ts (headless)
- clampPanel({x:-50,y:9999}, viewport) → dentro de [6, viewport-tam-6]   // arrastre acotado
- chip de estado usa dataStateStyle(estadoDato(psetNames)):
    ["Pset_WallCommon"]        → "proposal"  (gris)
    ["Pset_AqyraStructural"]   → "computed"  (acento)
    estadoDato(...) NUNCA "verified-signed" por inferencia               // D-SL2-3
```

## Slice C — dock cableado (dobles/espías, sin wasm)

```ts
// apps/aqyra-shell/test/dock.test.ts
// El Viewer se sustituye por un espía que registra las llamadas.
- click "Vista general"   → spy.frameAll llamado 1×
- click "Color por clase" → spy.resetColors + spy.setColorByClass (≥1 clase presente)
- click "Coste 5D"        → readCost + setCostHeatmap
- click "Cumplimiento 6D" → readCompliance + setCumplimientoColors
- ninguna herramienta escribe IFC ni toca la ingesta (sin métodos de escritura)
```

## Slice D — secciones honestas-vacías

```ts
// apps/aqyra-shell/test/secciones.test.ts
- contadoresPorClase(viewer.classes()) → dato real (suma = nº elementos listados)
- estructuraFuncional(modeloSinSystems) → estado-vacío honesto (no lanza, no inventa)
- clasificacion(modeloSinClasificacion) → estado-vacío honesto
- con dato presente → se listan IfcSystem/Zone y Uniclass/GuBIMClass tal cual vienen
```

## Slice E — barra de IA (stub)

```ts
// apps/aqyra-shell/test/ia-stub.test.ts
- click en un chip de prompt → rellena el textarea con el texto del chip
- enviar() → NO invoca ningún motor (stub); estado "diferido"           // D-CH-3
```

## Invariante transversal (todos los slices)

```ts
// La golden del visor no se mueve: se re-ejecuta el E2E existente sin cambios.
- federado-e2e.test.ts VERDE: md5 "dcb1e14460f3556107ce35d6dade16c3" + cámara D29 + árbol BCF
- ningún test nuevo importa fixtures nuevos ni reescribe IFC
```
