# Decisiones del shell — apps/aqyra-shell (chrome del visor v0.6)

> Registro propio del chrome de producto (React/Vite) que embebe `@aqyra/visor`. Ancla las
> decisiones D-CH del hilo «chrome del visor v0.6» (brief de Aqyra-Negocio, design-system Ola 3,
> mockup `apps/visor/mockups/Mockup_Aqyra_v0.6_visor-skins.html`). Gobernado por la spec
> `openspec/changes/visor-chrome-shell/`. Superficie `apps/` **propone puro**: re-viste y navega,
> **no certifica**; va en la **Llave 1** (gate del PR), **sin Llave 2** salvo release explícito del
> visor. La zona anclada (`apps/visor/fixtures/`, E2E, cámara D29, golden C4/C3) queda intacta. Las
> V del visor viven en `apps/visor/DECISIONES.md` (V1–V11, D-SK, D-SL2) y NO se mezclan aquí.
> Firmadas por JM.

## D-CH-1..D-CH-5 · Ratificadas por JM — 2026-07-07

- **D-CH-1 · Dónde vive el chrome = `apps/aqyra-shell` (React).** La superficie de producto que
  sobrevive; ya traía ~60 % del chrome (rail 5 disciplinas revistiendo el acento, `tokens.css`,
  topstrip con pastilla, `ViewerPane` que embebe el visor con árbol + Psets). No se duplica en el
  arnés `apps/visor/demo` ni se forka como componente vanilla en `apps/visor/src`.

- **D-CH-2 · Alcance del primer slice (A) = chrome + tematización, Diseño + Estructuras.** El acento
  de la disciplina activa tiñe el chrome (`--acc`/`--acc-soft`). Las otras 3 disciplinas
  (Instalaciones/MEP, Obras lineales, Puentes) salen **atenuadas-bloqueadas** en el rail: dependen de
  un desbloqueo de ingesta (MEP `IfcFlow*`; lineales/puentes `IfcAlignment` + `stationMetric`), epics
  aparte. Fuente de la activación = `DISCIPLINAS_ACTIVAS` en `src/tema.ts`, que sigue a `SKINS` del
  visor (D-SK-4). Token unificado a **`--acc`** (grafía del mockup); se mantiene `--accent` como
  alias para el CSS heredado del shell.

- **D-CH-3 · Dock cableado a capacidades existentes + barra de IA presente como stub.** El dock (Slice
  C) sólo conecta a lo que el viewer ya hace (Vista general, Color por clase, Psets, Coste 5D,
  Cumplimiento 6D, BCF); la barra de IA (Slice E) se pinta pero el envío se difiere a su propio epic.

- **D-CH-4 · Secciones del sidebar honestas-vacías (Slice D).** Dato real donde lo haya (contadores
  por clase reales hoy vía `Viewer.classes()`); estado-vacío honesto si el Maestro no trae estructura
  funcional (`IfcSystem`/`IfcZone`) ni clasificación (Uniclass/GuBIMClass, capacidad
  `bsdd-clasificacion`). Coherente con «la IA propone, el técnico firma».

- **D-CH-5 · Hermeticidad sin CDN.** El shell YA es hermético (iconos SVG inline propios, sin CDN;
  `font-family` con Inter → fallback `Segoe UI`, sin `@font-face` a CDN). El único pendiente es
  **vendorizar el woff2 de Inter** (drop-in en `src/assets/fonts/` + `@font-face`) para que Inter
  renderice donde no esté instalado; hasta entonces, fallback del sistema. No se vendoriza tabler.

## Slicing (a ratificar por slice; cada uno un PR, Llave 1, sin Llave 2)

A (layout 3 col + rail + tematización + hermeticidad) → B (selección flotante + chip + pastilla +
gizmo) → C (dock cableado) → D (secciones honestas-vacías) → E (barra de IA stub). Ver
`openspec/changes/visor-chrome-shell/tasks.md`.

### Slice A · commit 1 — 2026-07-07

Núcleo puro `src/tema.ts` (`temaDisciplina`, `railEstados`, `estadoDisciplina`, `DISCIPLINAS_ACTIVAS`)
con test headless `test/tema.test.ts` (vitest en Node, sin WASM). Rail con las 5 disciplinas: 2
activas, 3 atenuadas-bloqueadas (tooltip «bloqueada · ingesta»); pulsar una bloqueada no cambia el
acento. Tematización del chrome vía `--acc`/`--acc-soft` (alias `--accent`). Footer del mockup. Sin
tocar `ViewerPane` (el frame de columna única + resizer y los overlays van en commits posteriores del
Slice A y en B–E).
