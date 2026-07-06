# Tareas · Skins del visor por disciplina (Slice 1)

> Gobernado por `docs/frontend-standards.md` (TDD: el test se escribe ANTES que el código; pnpm,
> TS 5.5 ESM, three ^0.169, web-ifc 0.0.68 exacto, vitest+jsdom) y por
> `docs/openspec-tasks-mandatory-steps.md`. El visor está DENTRO de la Llave 1. Baby steps: un
> paso revisable cada vez; solo lo afectado (`tools/affected.py`).

## Paso 0 · Rama (primero)
- [ ] Crear y cambiar a `feat/visor-skins-disciplina` desde `origin/main` (con la capa SSD ya en
      main). git por `.bat` en Windows; JM ejecuta y fusiona el PR.

## Paso 1 · Mapa estático + acento (test-first)
- [ ] Test (`test/skins.test.ts`, unidad pura): `SKINS.diseno.acento === "#2f6bed"`,
      `SKINS.estructuras.acento === "#e07a4f"`; cada skin incluye sus clases ancla
      (Diseño: IFCWALL/IFCSLAB/IFCWINDOW; Estructuras: IFCCOLUMN/IFCBEAM/IFCFOOTING).
- [ ] Código: `apps/visor/src/skins.ts` con `type Disciplina`, `SkinDisciplina`, `SKINS`.

## Paso 2 · Color categórico por clase (test-first)
- [ ] Test: `colorPorClase` determinista (misma clase → mismo color), distinción entre clases,
      componentes en `0..1`, reserva gris para clase no mapeada, e independencia de disciplina
      para `IFCSLAB`.
- [ ] Código: tabla canónica provisional en `skins.ts` + `colorPorClase(ifcClass)`.

## Paso 3 · Leyenda por intersección (test-first)
- [ ] Test: `leyendaSkin("estructuras", presentes)` lista solo las clases del dominio presentes
      (con conteo y color), omite las presentes fuera del dominio y las del dominio ausentes;
      orden estable.
- [ ] Código: `EntradaLeyenda` + `leyendaSkin(d, presentes)`; consume la forma de
      `viewer.classes()` (`Array<{ ifcType; count }>`).

## Paso 4 · Superficie pública
- [ ] Exportar `SKINS`, `colorPorClase`, `leyendaSkin` y sus tipos desde `src/index.ts`.
- [ ] Test: import desde `@aqyra/visor` resuelve los símbolos (smoke de superficie).

## Paso 5 · Cableado + verificación visual (demo)
- [ ] Cablear en la capa de UI/demo: aplicar la skin componiendo `leyendaSkin(d, viewer.classes())`
      con `setColorByClass`; el acento a la CSS var de la pastilla/dock; conmutar = `resetColors` +
      re-pintar. NO tocar la ingesta ni `skins.ts` (dominio puro).
- [ ] Verificación visual (demo): abrir un IFC de edificio, conmutar Diseño↔Estructuras y
      confirmar acento + color por clase + reversibilidad.

## Pasos obligatorios (Llave 1)
- [ ] Ejecutar `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` VERDE (documentar salida).
- [ ] Confirmar golden del visor/`core` INTACTA: `federado-e2e.test.ts` y el derivado C4-FED-06
      sin cambios (la skin no reescribe IFC).
- [ ] `versions.lock` inalterado; `pnpm-lock.yaml` intacto (o justificado en el PR).
- [ ] Actualizar `apps/visor/DECISIONES.md` con V-nuevas (D-SK-1..D-SK-4) y `UX_BACKLOG.md` si
      procede.
- [ ] PR `feat/visor-skins-disciplina` → `main`; gate verde. **No requiere Llave 2** (propone
      puro, sin release — ver proposal).
