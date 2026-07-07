# Diseño técnico · Chrome del visor v0.6 sobre el shell

> Complementa `proposal.md`. Fija la superficie del chrome, el mapeo a capacidades reales del visor,
> la frontera de gobierno (todo `apps/`, propone) y la hermeticidad (sin CDN). Gobernado por
> `docs/frontend-standards.md` (visor/shell `apps/`, TDD, Llave 1). No fija hex definitivos: los del
> mockup son semilla (Ola 3).

## 1. Superficie del chrome (`apps/aqyra-shell`, acento por disciplina)

Layout del mockup v0.6, fondo Pizarra fría `#12151b`, tematización por disciplina. Tres columnas:

```
┌──────┬───────────────┬──────────────────────────────────────┐
│ rail │  sidebar 272  │  viewport (ViewerPane + escena 3D)    │
│ 56px │  (redim.)     │  · pastilla disciplina (arr-izq)      │
│      │  ┌─────────┐  │  · botones Vista general / Coste 5D / │
│ logo │  │ header  │  │    Cumplimiento 6D (arr-der)          │
│ ●Dis │  ├─────────┤  │  · dock de herramientas (der)         │
│ ●Est │  │ Esp.esp │  │  · panel de selección FLOTANTE        │
│ ○Ins │  │ Esp.fun │  │  · gizmo ejes XYZ (Z-up, abajo-izq)   │
│ ○Lin │  │ Clases  │  │  · barra de IA (abajo, stub)          │
│ ○Pue │  │ Clasif. │  │  · footer                             │
│      │  │ Dominio │  │                                       │
│      │  └─────────┘  │                                       │
└──────┴───────────────┴──────────────────────────────────────┘
```

- **Rail (56px):** logo Aqyra (`AqyraMark`, ya existe y «piensa» al abrir) + 5 swatches de
  disciplina. `on` en la activa (barra de acento a la izquierda). Diseño/Estructuras clicables;
  Instalaciones/Lineales/Puentes atenuadas (`opacity` + `cursor:not-allowed` + tooltip «bloqueada por
  ingesta»). El swatch usa el `acento` de `SKINS`/`DISCIPLINES`.
- **Sidebar (272px, redimensionable):** header (título del modelo + meta) + secciones plegables
  (Estructura espacial · Estructura funcional · Clases · Clasificación · bloque de dominio). El
  resizer arrastra `--side-w` (200–600px), patrón del mockup.
- **Viewport:** `ViewerPane` (ya embebe `@aqyra/visor`). Añade pastilla, dock, panel flotante, gizmo,
  barra de IA y footer como overlays sobre `#escena`.

## 2. Mapeo a la capacidad real del visor (todo ✅, se consume)

| Superficie del chrome | Capacidad real (`@aqyra/visor`) | Estado | Slice |
|---|---|---|---|
| Escena 3D Z-up, órbita/zoom, encuadre | `viewer.ts` `frameAll`/`frameElement`/`mount` | ✅ | A (ya) |
| Tematización por disciplina (acento) | `skins.ts` `SKINS[d].acento` | ✅ | A |
| Color por clase (categórico) | `skins.ts` `aplicarSkin` + `viewer.setColorByClass`/`resetColors` | ✅ | C |
| Selección + resaltado + ghost | `viewer.highlightSelection`/`ghostExcept` | ✅ | B |
| Chip de estado de dato | `data-state.ts` `estadoDato`/`dataStateStyle` (D-021/D-SL2-1) | ✅ | B |
| Psets del elemento (tabla KV) | `ifc-loader.getProperties` | ✅ | B |
| Árbol espacial (interactivo) | `ifc-loader.getSpatialTree` + `SpatialNode` | ✅ | A/D |
| Estructura funcional (IfcSystem/Zone) | `ifc-loader` (según lo que traiga el Maestro) | ⚠ honesto-vacío | D |
| Clasificación Uniclass/GuBIMClass | del modelo (capacidad `bsdd-clasificacion`) | ⚠ honesto-vacío | D |
| Contadores por clase | `viewer.classes()` | ✅ | D |
| Coste 5D (heatmap + totales) | `cost.ts` `readCost` + `viewer.setCostHeatmap` | ✅ | C |
| Cumplimiento 6D (color + leyenda) | `compliance.ts` `readCompliance` + `viewer.setCumplimientoColors` | ✅ | C |
| BCF (topics + cámara D29) | `bcf.ts` `parseMarkup`/`parseViewpoint`/`bcfCameraToViewer` | ✅ lectura | C |
| Barra de IA (chips + modelo) | — (stub, sin motor) | 🟡 stub | E |

Regla: el chrome **invoca** lo que el visor ya expone; **no** añade capacidad de dato nueva ni toca
la ingesta. Lo que hoy no existe (funcional/clasificación en el Maestro, IA) se pinta **honesto**:
sección con estado-vacío o barra deshabilitada, nunca dato inventado.

## 3. Tematización por disciplina (D-CH-2)

Fuente de verdad del acento = `SKINS` (`skins.ts`) para Diseño/Estructuras; `DISCIPLINES`
(`apps/aqyra-shell/src/disciplines.ts`) ya lista las 5 con su hex. Al elegir disciplina:
`document.documentElement.style.setProperty('--acc', acento)` + `--acc-soft` (rgba .16) — patrón que
el shell ya aplica hoy sobre `--accent`. Se unifica a `--acc`/`--acc-soft` (nombres del mockup) o se
mantiene `--accent` (nombre del shell) — **decisión de detalle D-CH-2·a**, sin efecto de gobierno.
Las 3 disciplinas bloqueadas conservan su swatch pero no cambian el acento del chrome (no hay modelo
que teñir); al pulsarlas se muestra el aviso de bloqueo.

## 4. Panel de selección flotante (D-CH-3, Slice B)

Overlay `position:absolute` sobre `#escena`, **arrastrable** por su cabecera (patrón `pointerdown`
+ `setPointerCapture` + clamp al viewport, como el mockup). Contenido: tag de clase (color
categórico), nombre, GlobalId, **chip de estado** (`dataStateStyle(estadoDato(psetNames))`) y tabla
KV de Psets (`getProperties`). El chip NUNCA pinta verde por inferencia (D-SL2-3): solo
`verified-signed` explícito. Sustituye al `#props` estático de texto plano; el dato es el mismo.

## 5. Hermeticidad — sin CDN (D-CH-5, Slice A)

El mockup carga tabler-icons e Inter por CDN; el gate no tiene CDN. Se resuelve:

- **Inter:** vendorizar los woff2 (peso 400/500/600) bajo `apps/aqyra-shell/src/assets/fonts/` y
  `@font-face` en `tokens.css`. `font-synthesis:none` como el mockup. Fallback a `-apple-system`.
- **Iconos:** **set propio mínimo** — sólo los ~15 glifos que usan rail/dock/IA (inicio, nuevo,
  describir, medir, color, psets, bcf, coste, cumplimiento, ruler, palette, message, flame, send,
  chevron). Componente `Icon` React con `<svg>` inline (el shell ya tiene un `Icon` así en `Rail`).
  No se vendoriza el paquete tabler entero (peso y licencia innecesarios).

## 6. Frontera de gobierno — todo `apps/`, propone (Llave 1)

- **`apps/` (revisión normal, Llave 1 del PR):** todo el chrome (rail, sidebar, secciones, panel
  flotante, dock, IA-stub, footer, tematización, hermeticidad). No toca `packages/contracts`,
  `packages/golden`, `_import/` ni la ingesta.
- **Sin Llave 2:** no hay release. Si al cierre JM decide publicar, sería un tag firmado
  `visor-vX.Y.0` (release del visor) — decisión reservada a JM, fuera de este change salvo aviso.
- **Golden intacta:** el E2E del visor (`federado-e2e.test.ts`, md5 `dcb1e14460f3556107ce35d6dade16c3`
  + cámara D29 + árbol BCF) y los golden C4/C3 no se tocan. Si cualquier slice exigiera rozar la zona
  anclada, se PARA y se convierte en decisión (V) con JM.

## 7. Cómo se prueba (sin golden de píxeles)

- **Núcleo puro nuevo** (helpers de tematización, mapeo disciplina→acento, agregados de secciones
  honestas, formateadores) → tests headless vitest **sin wasm**, en `apps/aqyra-shell/test/` (o
  `apps/visor/test/` si el helper vive en `skins.ts`/`data-state.ts`).
- **Comportamiento** donde aplique: el resizer cambia `--side-w` dentro de límites; el panel flotante
  arrastra y clampa; el dock invoca el método correcto del viewer (doble/espía sin wasm); el rail
  atenúa las 3 bloqueadas y no cambia el acento al pulsarlas.
- **E2E estructural del visor** sigue VERDE con los mismos anclajes (no se toca).
- **Revisión VISUAL** de la demo del shell (`pnpm --filter @aqyra/shell dev`) a ojo por JM para lo
  puramente estético (tematización, Inter, iconos, panel flotante, footer).
