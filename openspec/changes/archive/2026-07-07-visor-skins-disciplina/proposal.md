# Cambio · Skins del visor por disciplina (Slice 1)

> Change-id: `visor-skins-disciplina` · Capacidad: `visor` (`apps/visor`, `@aqyra/visor`)
> Procedencia: `Aqyra-Negocio/BRIEF_visor-skins-por-disciplina.md` (+ mockup `v0.6`) · Ola 1.
> Naturaleza: **`apps/` (UI)** — re-viste y navega. No toca contratos ni arquitectura, no
> requiere ADR. Gobernado por `docs/frontend-standards.md` (TDD, Llave 1) y `CLAUDE.md`/`AGENTS.md`.
> Estado: spec redactada (SSD) · pendiente de ratificar el alcance (Slice 1: Diseño + Estructuras)
> y las decisiones D-SK-1..D-SK-4 antes del código.

## Por qué

Los visores abiertos son genéricos: pintan todas las clases IFC igual y no hablan el lenguaje
de cada disciplina. El técnico o paga un entorno cerrado (CYPE/Revit) para ver «su» modelo o se
conforma con un visor plano. Aqyra quiere que **el mismo IFC se lea con los ojos de cada
dominio** sin cambiar de herramienta ni pagar licencia: acento de disciplina + color por clase +
árbol + herramientas del dominio. Este cambio aterriza el **primer escalón** de esa superficie —
el re-vestido visual básico — sobre el visor real, para las dos disciplinas ya soportadas por
`ELEMENT_TYPES` (**Diseño** y **Estructuras**).

Es la cuña de adopción: cada disciplina bien vestida acerca al técnico a su motor (cálculo,
cumplimiento, presupuesto) y, por tanto, al export firmable donde vive el muro de cobro. La skin
se siente gratis por diseño.

## Qué cambia (Slice 1 · mínimo)

Se AÑADE un módulo puro de dominio y su cableado ligero al visor, sin tocar la ingesta ni el
modelo neutro:

- **Mapa estático disciplina → clases IFC** (`skins.ts`, módulo NUEVO): estructura de datos que
  asocia cada disciplina (`diseno`, `estructuras`) con su acento de marca y su lista canónica de
  clases IFC del dominio. Es dato, no cálculo.
- **Re-skin del acento**: cada disciplina expone su color de acento (Diseño `#2f6bed`,
  Estructuras `#e07a4f`) para pintar la pastilla de disciplina, el dock y los remates de UI.
- **Color por clase IFC — mapa categórico** (`colorPorClase`): un color propio y estable por
  **tipo** IFC (distinto por clase), **separado del acento** de disciplina. No es una rampa del
  color de disciplina (resuelve la decisión §6.7 del brief).
- **Leyenda de la skin = intersección** (`leyendaSkin`): las clases del dominio que **realmente
  están presentes** en el modelo cargado (mapa estático ∩ `viewer.classes()`), cada una con su
  conteo y su color categórico. Es la fuente de la sección «Clases · color / visibilidad» del
  árbol y alimenta `setColorByClass` / `setVisibilityByClass` ya existentes.

El núcleo (`skins.ts`) son funciones **puras y deterministas** (sin three.js ni WASM):
unit-testables en `vitest` headless. El cableado al `Viewer` reutiliza la superficie pública que
ya existe (`classes()`, `setColorByClass`, `setVisibilityByClass`), sin nuevos parámetros en la
ingesta.

## Qué NO cambia (fuera de alcance de Slice 1)

- **Panel de Selección + Propiedades/Psets** con selección ámbar y chip de estado de dato → es el
  **Slice 2** (reutiliza `ifc-loader`/`data-state`).
- **Instalaciones (MEP)**, **Obras lineales** y **Puentes** → Slices 3 y 4 (dependen de que el
  visor cargue/coloree `IfcFlowSegment`/`IfcDistributionSystem` y de `stationMetric`/PK).
- **Dock de herramientas del dominio que invoca engines** → no se cablea aquí; la skin de Slice 1
  es re-vestido visual, no navegación al motor (§6.2 del brief; el cálculo vive en los engines).
- **Ventana de IA anclada**, **árbol funcional/sistemas** y **clasificación bsDD** → posteriores.
- **Naming de Psets de resultado** (§6.1), **tono de fondo `#12151b`** (§6.6) y **mapa de color
  del design system** (§6.7, versión definitiva) → se fijan en el design system (Ola 3), no aquí.
- No se toca `packages/contracts` ni `packages/golden`: no entra CODEOWNERS ni contract-first.

## Impacto en gobierno — propone puro, sin llaves

La skin es **propone / ver / describir**: no certifica nada y **no dispara ninguna de las dos
llaves**. En esta superficie:

- **Llave 1 (golden / CI):** el cambio es `apps/visor` puro. La **golden del visor / `core`
  permanece intacta** (identidad byte a byte del modelo neutro): `skins.ts` no lee ni reescribe
  IFC, no toca la ingesta, no altera `federado-e2e.test.ts` ni el derivado congelado C4-FED-06.
  El PR debe dejar `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` **verdes**.
- **Llave 2 (firma GPG de JM):** **no aplica** — no hay release ni adopción que firmar; la skin no
  produce estado `verified-signed`, solo puede *mostrarlo* (Slice 2, vía `data-state`).
- **`versions.lock`:** inalterado por esta skin (no invoca plugins todavía).
- **`pnpm-lock.yaml`:** sin dependencias nuevas (three/web-ifc/vitest ya presentes). Si cambiara,
  va justificado en el PR.

**Definición de hecho (Slice 1):** tests/typecheck/build de lo afectado en verde · golden del
visor/`core` intacta · `versions.lock` sin tocar · `apps/visor/DECISIONES.md` actualizado con
las V-nuevas · sin ficha de contrato ni golden nuevas.

## Fuera de alcance / frontera de gobierno

Si en un slice posterior se cablea el **dock de herramientas** y se define un **contrato de
invocación visor↔engine** (decisión abierta §6.2 del brief), *ese* sí sería contract-first (ficha
de contrato + golden con oráculo + CODEOWNERS) — pero queda fuera de este cambio.
