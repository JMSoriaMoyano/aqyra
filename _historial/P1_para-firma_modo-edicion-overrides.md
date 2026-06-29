# P1 · Hito 2 (modo edición) — Para firma de JM · capa de overrides

**Slice cerrado por JM:** overrides primero · viewport Three híbrido · familias con identidad
propia · gesto = trasladar + girar.

## Lo construido (esta entrega — solo la PIEZA 1, datos)

La **capa de overrides** = manipulación directa como DATO, render-agnóstica. No toca píxeles.

- `model.ts`
  - `BuildingInput.overrides?: Record<code, {dx?, dy?, rotDeg?}>` — entrada nueva.
  - `ElementOverride` + `applyOverride(placement, ov)` puro: gira sobre el centroide, luego
    traslada. Línea y polígono giran transformando sus coordenadas; el punto es invariante al
    giro (su rotación con identidad —escalera— iría por `giro`, no aquí).
  - Aplicación como ÚLTIMO paso de `buildModel`, global, por código.
  - `ElementInstance.derivedFrom` — **acoplamiento**: el hueco que perfora la rampa lleva el
    código de su rampa; un override sobre la rampa **arrastra el hueco** (si no, la rampa se
    mueve y el agujero se queda). Mismo driver → coherencia.
- `test/overrides.golden.test.ts` — arnés golden nuevo.

## Hallazgo de frontera (importante)

**El giro de esta familia es FRONTERA-CERO; no requiere bump de C1.** Rampa y carpintería se
colocan como **línea** (`inicio/fin`) y forjados/huecos como **polígono** (`contorno`): la
orientación ya vive en las coordenadas que el cebo autora explícitas, así que girar = mover esos
puntos. La cota **z no se incluye** (es derivada del nivel `storeyIndex·altura`, no del placement
2D): mover en vertical sería otro mecanismo (override de cota) → diferido.
*El único caso que pediría dato nuevo en `alto.json` sería el giro de un elemento PUNTUAL con
sección (pilar), y está fuera de la familia editable.*

## Estado de las dos llaves

- **Llave 1 (golden verde):** el **núcleo geométrico** (`applyOverride`) se ejecutó **verbatim,
  6/6 verde** (traslación, giro 90°/180°, pureza, invariancia del punto, hueco acoplado, pivote
  común). **El golden completo con vitest no se pudo correr en el sandbox** (vista Linux del repo
  *stale/truncada* — el desfase de sync conocido—, disco lleno y git inoperativo). **Pendiente de
  correr en Windows:**
  ```
  pnpm --filter @aqyra/demo test            # toda la suite (nuevo + 10 existentes)
  # o solo el nuevo:
  publico/demo/node_modules/.bin/vitest run --root publico/demo test/overrides.golden.test.ts
  ```
- **No-regresión (argumento):** sin `overrides` el camino es idéntico; `derivedFrom` es un campo
  nuevo **invisible al snapshot** (los fixtures cuentan `totalOpenings`, `host`, `placement.kind`,
  no campos extra del hueco) → los 10 golden vigentes no deberían moverse. A confirmar con el run.
- **Llave 2:** tu firma. La IA preparó; **no certifica**.

## PIEZA 2 — el viewport (arrancada)

**Puente gesto→datos (datos, Llave 1 verde):** `model.ts` → `deriveOverride(base, observado)`,
INVERSO de `applyOverride`. El gizmo no inventa el dato: lo deriva del antes/después, y la
**ida-y-vuelta es golden** (`test/derive-override.golden.test.ts`). Es el contrato que cualquier
renderer debe cumplir.

**Módulo Three (`publico/demo/proposals/edit-viewport.ts`) — PREPARADO, NO verificado en pantalla.**
`EditViewport`: escena Three, picking con raycaster, `TransformControls` (trasladar/girar), y al
soltar el gizmo emite el `{dx,dy,rotDeg}` que se escribe en `overrides` → rebuild. GL solo en
`mount()` (instanciable sin WebGL, como `visor/viewer.ts`). Toda la matemática delegada al núcleo
golden. **Está FUERA de `src/` a propósito** (importa `three`, aún no dep del demo) para no romper
el typecheck/bundle. **Para montarlo:** (1) `pnpm add three @types/three` en `publico/demo`;
(2) mover a `src/`; (3) cablear en `diseno.ts` (botón "editar" → monta `EditViewport`, `onOverride`
escribe `bInput.overrides` + `render()`/`refreshTree()`); (4) **probar en pantalla** (no se pudo
aquí: sandbox sin GL). Nota r0.169: `TransformControls` ya no es `Object3D` → `scene.add(control.getHelper())`.

**PROBARLO EN PANTALLA — playground aislado (`edit.html`).** Para que JM lo pruebe SIN tocar la
skin Diseño (intacta), hay una página de banco de pruebas que vite sirve en dev: las DOS vistas
sobre el mismo modelo y la misma capa de overrides.

Pasos:
1. **Vista 2D (corre ya, sin instalar nada):**
   ```
   cd C:\…\Entorno\publico\demo
   pnpm dev        # abre el navegador en  /edit.html
   ```
   Elige modelo (parking con rampa · residencia con puerta/ventana/escalera), selecciona un
   elemento y muévelo (arrastre o flechas ±0,5 m) y gíralo (±15°). El dibujo sale de `buildModel`
   CON los overrides → ves el dato moverse y el JSON de `overrides` en vivo.
2. **Vista 3D (gizmo Three):** una sola vez, `cd C:\…\Entorno\publico && pnpm install` (añade
   `three`+`@types/three`, ya declarados). Luego en `/edit.html` pulsa «Vista 3D (Three)»:
   picking + `TransformControls` (botón mover/girar); al soltar, escribe el override.

Archivos: `publico/demo/edit.html` + `src/edit-playground.ts` (vista 2D, sin deps) + `src/edit-viewport.ts`
(gizmo Three, carga perezosa). **No verificado en pantalla por la IA** (sandbox sin GL); listo para tu prueba.

**Pendiente real de Pieza 2:** tras validar en el playground, cablear el gesto DENTRO de la skin
Diseño (`diseno.ts`) y **coordinar con el hilo de usabilidad de skins** (un gesto = lo mismo en todas
las skins); y el residual del núcleo-como-driver.

## Decisión de diseño que te reservo (alcance de "edición")

La **rampa** y la **carpintería** son elementos de UN código → override limpio. El **núcleo** es
COMPOSITE (espacio + 4 muros + escalera + huecos) que deriva de una huella-driver: moverlo "como
unidad" no es un código, es mover su driver. Dos caminos para v1: (a) editar solo elementos de
código único ahora y dejar el núcleo-como-grupo para un override de driver (Pieza 2b); o (b)
implementar ya el override de driver. **Reservado a JM.**
