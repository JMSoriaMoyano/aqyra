# Tareas · Selección + estado de dato (Slice 2)

> Gobernado por `docs/frontend-standards.md` (TDD: test antes que código) y
> `docs/openspec-tasks-mandatory-steps.md`. El visor está DENTRO de la Llave 1. Baby steps.

## Paso 0 · Rama (primero)
- [ ] Crear y cambiar a `feat/visor-seleccion-estado` desde `origin/main`. git por `.bat`.

## Paso 1 · `estadoDato` (test-first)
- [ ] Test (`test/data-state.test.ts` o `test/estado-dato.test.ts`, unidad pura): `computed` con
      Pset de resultado; `proposal` sin él; nunca `verified-signed` por inferencia; respeta `explicito`.
- [ ] Código: `estadoDato(psetNames, explicito?)` en `src/data-state.ts`; export en `src/index.ts`.

## Paso 2 · Chip en el panel (cableado demo)
- [ ] Cablear en `demo/main.ts` (`muestraElemento`): calcular `estadoDato(Object.keys(rec.psets))`,
      pintar el chip con `dataStateStyle`, encima de los Psets; conservar el resalte ámbar.
- [ ] Verificación visual (demo): seleccionar un muro (proposal) y un elemento con resultado
      (computed) y ver el chip cambiar de color/etiqueta.

## Pasos obligatorios (Llave 1)
- [ ] `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` VERDE.
- [ ] Golden del visor/`core` intacta; `versions.lock` sin tocar.
- [ ] `apps/visor/DECISIONES.md` con la V-nueva (D-SL2-1..3).
- [ ] PR `feat/visor-seleccion-estado` → `main`; gate verde. **Sin Llave 2** (propone puro).
