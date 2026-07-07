# Cambio · Chrome del visor v0.6 sobre el shell (rail · tematización · selección flotante · dock · IA · footer)

> Change-id: `visor-chrome-shell` · Capacidad: `shell` (`apps/aqyra-shell`, React/Vite) que
> **embebe** `@aqyra/visor` (`apps/visor`). Consume `viewer.ts` / `skins.ts` / `data-state.ts`;
> NO reimplementa el visor ni toca la ingesta.
> Procedencia: `Aqyra-Negocio` (design-system Ola 3) · mockup `apps/visor/mockups/Mockup_Aqyra_v0.6_visor-skins.html`
> (acento por disciplina, fondo Pizarra fría `#12151b`, tipografía Inter + tabler-icons).
> Continúa la línea del visor: skins Slice 1/2 + coste 5D + cumplimiento 6D (todo en `main`).
> Naturaleza: **`apps/` puro (propone).** Re-viste y navega, no certifica. Va en la **Llave 1**
> (gate del PR). **Sin Llave 2** salvo que se decida publicar un release del visor.
> Estado: spec redactada (SSD) · decisiones D-CH-1..D-CH-5 **ratificadas por JM (2026-07-07)**;
> pendiente de ratificar el desglose por slices A..E antes del código.

## Por qué

JM ha visto la demo del visor real junto al mockup v0.6 y hay una **brecha de chrome**: el visor
trae los ladrillos (viewer Z-up, skins, selección+Psets+chip de estado, coste 5D, cumplimiento 6D)
pero con un **layout funcional mínimo**, no el chrome pulido del design-system. El visor es el
**cebo** del embudo cebo-anzuelo: su trabajo es enganchar a quien mira. Cerrar la brecha —el rail
de disciplinas, la tematización por disciplina, el panel de selección flotante con chip de estado,
el dock de herramientas, la barra de IA y el footer— hace que el producto **se sienta** como el
mockup, sobre el motor real.

El chrome vive en **`apps/aqyra-shell`** (React), la superficie de producto que sobrevive
(**D-CH-1**), no en el arnés `apps/visor/demo`. El shell ya trae ~60 % del chrome (rail con las 5
disciplinas revistiendo `--accent`, `tokens.css`, topstrip con breadcrumb + pastilla, `ViewerPane`
que embebe el visor con árbol + Psets); este cambio lo lleva al v0.6 completo sin duplicar chrome.

## Qué cambia (por slices)

Baby steps: cada slice es un PR a `main` con el gate verde. Todo es `apps/`; el visor se **consume**.

**Slice A · Layout de 3 columnas + rail + tematización + hermeticidad.**
- `apps/aqyra-shell`: layout **rail 56px + sidebar 272px redimensionable + viewport** (grid del
  mockup). Rail con las **5 disciplinas** (swatch de acento + tooltip + logo Aqyra): **Diseño** y
  **Estructuras** activas; **Instalaciones / Obras lineales / Puentes** atenuadas-bloqueadas
  (dependen de ingesta MEP / `IfcAlignment`+`stationMetric`) con tooltip «bloqueada por ingesta».
- **Tematización por disciplina**: el acento (`--acc`) tiñe todo el chrome (rail, pastilla, dock,
  remates), reutilizando `SKINS`/`skins.ts` como fuente de acento (D-CH-2). Fondo Pizarra fría.
- **Hermeticidad (D-CH-5):** sin CDN. Se **auto-aloja Inter** (woff2 vendorizado) y se crea un
  **set de iconos propio mínimo** (~15 glifos SVG inline usados por rail/dock/IA), no se vendoriza
  tabler entero.

**Slice B · Panel de selección flotante + chip de estado + pastilla + gizmo.**
- Panel de Selección **flotante y arrastrable** (tag de clase, nombre, GlobalId, tabla KV de Psets)
  con el **chip de estado de color** que ya deriva `estadoDato`/`dataStateStyle` (`data-state.ts`,
  Slice 2): Propuesta / Calculado / QA golden·llave 1 / Firmado·2 llaves.
- **Pastilla de disciplina** (vppill) arriba-izquierda y **gizmo de ejes XYZ** (Z-up) sobre la
  escena. El visor ya sirve la geometría Z-up; el gizmo refleja el marco.

**Slice C · Dock de herramientas cableado (D-CH-3).**
- Dock derecho por disciplina cableado a **capacidades YA existentes** del viewer:
  Vista general (`frameAll`) · Color por clase (`setColorByClass`/`aplicarSkin`) · Psets
  (panel de selección) · Coste 5D (`readCost`/`setCostHeatmap`) · Cumplimiento 6D
  (`readCompliance`/`setCumplimientoColors`) · BCF (`bcf.ts`). Nada que no exista hoy.

**Slice D · Secciones del sidebar honestas-vacías (D-CH-4).**
- **Estructura funcional** (`IfcSystem`/`IfcZone`/`IfcDistributionSystem` con su `PredefinedType`),
  **Clasificación** (Uniclass 2015 + GuBIMClass por clase) y **contadores por clase**. Se pintan las
  secciones y se rellenan con dato **REAL** si el Maestro lo trae; **estado-vacío honesto** si no.
  Los contadores por clase son dato real hoy (`Viewer.classes()`); la clasificación depende de que
  el modelo la lleve (capacidad `bsdd-clasificacion`). El bloque de dominio cambia de nombre por
  disciplina (Topics BCF / Comprobaciones / Resultados de red / Verificaciones).

**Slice E · Barra de IA presente como stub (D-CH-3).**
- Barra de IA abajo: textarea + **chips de prompts del dominio** + selector de modelo
  («Aqyra Golden · Alto»). Se **pinta completa** pero el **envío queda diferido/stub** (no invoca
  ningún motor): enseña el chrome sin prometer IA. La IA real es su propio epic.

**Footer** (aparece desde Slice A): «Skin incluida… el muro de cobro es el export» · «La IA propone
· el técnico firma».

## Qué NO cambia / fuera de alcance

- **La zona anclada intacta:** `fixtures/federado*.ifc` (md5 LF), el E2E, la cámara D29 y los golden
  C4/C3. Este trabajo **no lee ni reescribe IFC nuevo** ni toca la ingesta.
- **El arnés `apps/visor/demo`** queda como está (banco de pruebas del paquete): el chrome rico va al
  shell, no se duplica en el demo.
- **Las 3 disciplinas bloqueadas** (Instalaciones/MEP, Obras lineales, Puentes) NO se activan aquí:
  son epics de **desbloqueo de ingesta** aparte (`ELEMENT_TYPES` no enumera `IfcFlow*`; lineales y
  puentes requieren `IfcAlignment` + `stationMetric`). En el rail salen atenuadas.
- **La IA real** (envío, tool-calling del dominio) es su propio epic; aquí solo el chrome (stub).
- **Los hex de color y el naming definitivos** los fija el design system (Ola 3); los del mockup son
  semilla (coherente con D-SK-2).
- **La certificación:** el shell **propone**; el verde (`verified-signed`) solo lo acuña el flujo de
  firma (D-021 / D-SL2-3). El chip muestra el estado, no lo certifica.

## Impacto en gobierno — propone (Llave 1), sin Llave 2

- Superficie `apps/` (shell + visor consumido): **no dispara ninguna de las dos llaves.** Va por
  revisión normal con el **gate del PR verde** (typecheck + build + tests de lo afectado).
- **Golden del visor/`core` intacta:** el E2E (`federado-e2e.test.ts`, md5 `dcb1e144…` + cámara D29 +
  árbol BCF) y los golden C4/C3 quedan sin cambios. `versions.lock` del visor solo se toca si se
  decide un **release** (Llave 2 = tag firmado `visor-vX.Y.0`), decisión reservada a JM.
- **Definición de hecho (por slice):** `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` VERDE;
  golden del visor/`core` intacta; núcleo puro nuevo (mapas/tematización/helpers) con tests headless
  (vitest, sin wasm); lo puramente visual, por revisión de la demo del shell a ojo por JM.

## Decisiones ratificadas (D-CH-1..D-CH-5 · JM · 2026-07-07)

1. **D-CH-1 · Dónde vive el chrome = `apps/aqyra-shell` (React).** La superficie de producto que
   sobrevive; ya trae ~60 % del chrome. No se duplica en el demo (arnés) ni se forka como componente
   vanilla en `apps/visor/src` (mayor trabajo, sin consumidor rico adicional).
2. **D-CH-2 · Alcance del primer slice = chrome + tematización, Diseño+Estructuras.** Las otras 3
   disciplinas atenuadas-bloqueadas en el rail (dependen de ingesta). Reutiliza `viewer`/`skins`/
   `data-state`.
3. **D-CH-3 · Dock cableado a capacidades existentes + barra de IA presente como stub.** El dock solo
   conecta a lo que el viewer ya hace; la IA se pinta pero el envío se difiere a su epic.
4. **D-CH-4 · Secciones del sidebar honestas-vacías desde el Maestro.** Dato real donde lo haya
   (contadores por clase reales hoy); estado-vacío honesto si el modelo no trae funcional/
   clasificación. Coherente con «la IA propone, el técnico firma».
5. **D-CH-5 · Hermeticidad = auto-alojar Inter + set de iconos propio mínimo** (~15 glifos SVG
   inline), sin CDN y sin vendorizar tabler entero.

## Recomendación de construcción (orden de slices)

A (layout + rail + tematización + hermeticidad) → B (selección flotante + chip + pastilla + gizmo) →
C (dock cableado) → D (secciones honestas-vacías) → E (barra de IA stub). Cada uno es un PR con el
gate verde. Las disciplinas MEP/lineales/puentes quedan para epics de ingesta previos.
