# apps/aqyra-shell — el shell de Aqyra (React/Vite)

Slice 1 del ecosistema: el **chrome del mockup v0.5** (rail de iconos, caja de entrada,
skins por disciplina, logo-apertura que dobla como «pensando») hecho app React, que **embebe
el visor real** (`@aqyra/visor`) para **abrir un IFC suelto** — sin gestor de proyectos todavía.

Es el primer puente mockup ↔ repo: valida que el diseño encaja con el motor real antes de
construir el resto de superficies (ver `Aqyra-Negocio/MAPA_mockup-a-repo_y_roadmap.md`).

## Qué hace hoy

- Home estilo Claude: saludo + caja de entrada (maqueta) + chips + **zona para arrastrar un `.ifc`**.
- Al abrir el IFC: monta el visor abierto (web-ifc + three), pinta la **estructura espacial**,
  permite **seleccionar** (escena ↔ árbol) y muestra **Psets** de la selección.
- Las **disciplinas** del rail revisten el `--accent` de la app (estrategia de skin) y el color
  de selección del visor.
- El **logo** «piensa» (ensamblaje aleatorio) mientras se abre el modelo.

## Arranque

Desde la raíz del monorepo:

```bash
corepack pnpm install                 # instala react + @vitejs/plugin-react (primera vez)
corepack pnpm --filter @aqyra/shell dev
```

Abre el navegador en la URL que imprime Vite (por defecto http://localhost:5173) y arrastra
un `.ifc`. El `.wasm` de web-ifc se sirve por middleware desde el paquete real (igual que la
demo del visor).

Otros comandos:

```bash
corepack pnpm --filter @aqyra/shell typecheck   # tsc --noEmit
corepack pnpm --filter @aqyra/shell build        # typecheck + vite build → dist/
```

## Frontera (coherencia con el repo)

- El shell **consume** `@aqyra/visor` desde su fuente (alias de Vite), no lo re-implementa.
  El visor solo LEE modelos; no federa ni genera (eso es `services/federacion`, C4).
- No toca la zona firmada (`packages/contracts`, `packages/golden`, `_import/`).
- Tokens provisionales en `src/tokens.css` (azul `#2f6bed` pendiente del hex exacto de JM);
  el design system (paso 3 del roadmap) los formaliza cuando haya ≥2 superficies.

## Próximas olas (no en este slice)

Skins de disciplina reales sobre el visor · puente al entregable firmable (memoria/presupuesto,
las dos llaves) · caja conversacional + gestor de proyectos · federación UI + Estado del CDE (C8).
