# Tareas · Chrome del visor v0.6 sobre el shell

> Gobernado por `docs/frontend-standards.md` (shell/visor `apps/`, TDD, Llave 1) y
> `docs/openspec-tasks-mandatory-steps.md`. Naturaleza **`apps/` puro (propone)**: revisión normal,
> **sin Llave 2** (salvo release explícito de JM). Baby steps: cada slice es un PR a `main` con el
> gate verde; solo lo afectado (`apps/aqyra-shell/**`, y `apps/visor/src/**` solo si un helper puro
> se añade a `skins.ts`/`data-state.ts`). Git por `.bat` en Windows; JM ejecuta y fusiona el PR.

## Paso 0 · Rama (primero)
- [ ] Crear y cambiar a `feat/visor-chrome-shell` desde `origin/main` (patrón v2: rama desde
      `origin/main`). Guarda de PR en el `.bat`: `git diff --cached --name-only` + `findstr /v /b`
      para abortar si se cuela algo fuera de `apps/`.

## Slice A · Layout 3 columnas + rail + tematización + hermeticidad (PR #A)
- [ ] Test-first (headless, sin wasm): helper de tematización disciplina→`{acc, accSoft}` y helper
      de estado del rail (activa vs. bloqueada) — determinismo + las 3 bloqueadas marcadas.
- [ ] `tokens.css`: `@font-face` de **Inter** (400/500/600, woff2 vendorizados en
      `src/assets/fonts/`), variables Pizarra fría del mockup, `--acc`/`--acc-soft`.
- [ ] Set de **iconos propio mínimo** (~15 glifos): componente `Icon` con `<svg>` inline.
- [ ] Layout grid **rail 56 + sidebar 272 (redimensionable) + viewport**; resizer `--side-w`
      (200–600). Rail con 5 disciplinas (2 activas, 3 atenuadas-bloqueadas con tooltip). Tematización
      del chrome por disciplina reutilizando `SKINS`/`DISCIPLINES`. **Footer** del mockup.
- [ ] Verificación: la demo del shell abre un IFC, tiñe el chrome por disciplina, atenúa las 3
      bloqueadas; revisión visual de JM.

## Slice B · Panel de selección flotante + chip de estado + pastilla + gizmo (PR #B)
- [ ] Test-first: el panel arrastrable clampa al viewport; el chip usa
      `dataStateStyle(estadoDato(psetNames))` y **nunca** verde por inferencia (D-SL2-3).
- [ ] Panel flotante arrastrable (tag de clase + nombre + GlobalId + chip + tabla KV de Psets),
      reutilizando `getProperties`/`data-state.ts`. Pastilla de disciplina (vppill) + gizmo de ejes
      XYZ (Z-up) como overlays sobre `#escena`.
- [ ] Verificación: seleccionar en escena/árbol mueve el panel y pinta el chip correcto; revisión
      visual.

## Slice C · Dock de herramientas cableado (PR #C)
- [ ] Test-first: cada botón del dock invoca el método correcto del viewer (doble/espía sin wasm).
- [ ] Dock derecho por disciplina cableado a capacidades **existentes**: Vista general (`frameAll`),
      Color por clase (`aplicarSkin`/`setColorByClass`), Psets (panel), Coste 5D (`readCost`/
      `setCostHeatmap`), Cumplimiento 6D (`readCompliance`/`setCumplimientoColors`), BCF (`bcf.ts`).
- [ ] Verificación: cada herramienta responde; revisión visual.

## Slice D · Secciones del sidebar honestas-vacías (PR #D)
- [ ] Test-first: los contadores por clase salen de `viewer.classes()` (dato real); funcional y
      clasificación muestran **estado-vacío honesto** cuando el Maestro no los trae.
- [ ] Secciones: Estructura funcional (`IfcSystem`/`IfcZone`/`IfcDistributionSystem`+PredefinedType),
      Clasificación (Uniclass/GuBIMClass), contadores por clase. Bloque de dominio renombrado por
      disciplina (Topics BCF / Comprobaciones / Resultados de red / Verificaciones).
- [ ] Verificación: con `federado.ifc`, contadores reales + secciones honestas-vacías donde no hay
      dato; revisión visual.

## Slice E · Barra de IA presente como stub (PR #E)
- [ ] Test-first: los chips rellenan el textarea; el **envío no invoca ningún motor** (stub) y la
      barra queda visualmente deshabilitada para envío.
- [ ] Barra de IA: textarea + chips de prompts del dominio + selector de modelo («Aqyra Golden ·
      Alto»). Envío diferido/stub con aviso «la IA propone · el técnico firma».
- [ ] Verificación: chips y textarea funcionan; el envío no hace nada silenciosamente peligroso;
      revisión visual.

## Pasos obligatorios (por PR)
- [ ] **Llave 1 (apps/):** `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` VERDE; **golden del
      visor/`core` intacta** (`C4-FED-06`, `federado-e2e.test.ts` sin cambios; md5 `dcb1e144…` +
      cámara D29). Reporte en `openspec/changes/visor-chrome-shell/reports/AAAA-MM-DD-unit-test.md`.
- [ ] `versions.lock`/`pnpm-lock.yaml` **inalterados** salvo dependencia nueva justificada
      (Inter/iconos son assets locales, no dependencias npm nuevas).
- [ ] Actualizar `apps/visor/DECISIONES.md` (o `apps/aqyra-shell/DECISIONES.md` si se crea) con las
      V-nuevas que anclan **D-CH-1..D-CH-5**.
- [ ] Actualizar `apps/aqyra-shell/README.md` (chrome v0.5 → v0.6) y el `UX_BACKLOG` si procede.
- [ ] PRs por slice → `main`; gate verde. **Sin Llave 2** (no hay release en este change). Si al
      cierre JM decide publicar el visor, tag firmado `visor-vX.Y.0` como decisión aparte.
