# Tareas · Convenio Z-up del visor

> Gobernado por `docs/frontend-standards.md` (TDD: el test se escribe ANTES que el código;
> pnpm, TS 5.5 ESM, three ^0.169, web-ifc 0.0.68 exacto, vitest+jsdom) y por
> `docs/openspec-tasks-mandatory-steps.md`. El visor está DENTRO de la Llave 1.

## Paso 0 · Rama (primero)
- [ ] Crear y cambiar a `feat/visor-convenio-zup` desde `origin/main` (con la capa SSD ya en main).

## Paso 0-bis · Dependencia slice-1 (decisión Q-Zup-2)
- [ ] Aterrizar slice-1 (`apps/aqyra-shell`, gizmo, fix de layout, cambios de `viewer.ts`) en su
      PR propia ANTES de este cambio, o acordar integrarlo aquí. Sin esto, el gizmo/escena que
      este cambio migra no están en `origin/main`.

## Paso 1 · Geometría Z-up en la ingesta (test-first)
- [ ] Test: al añadir un IFC, un vértice conocido cae en Z-up (rotación +90° X aplicada).
- [ ] Código: rotar las mallas en `viewer.addIfcModel`; `camera.up=(0,0,1)` + OrbitControls Z-up.
- [ ] Verificación visual (demo): abrir un IFC y confirmar Z vertical.

## Paso 2 · Cota = eje Z (test-first)
- [ ] Test: `elementElevations` usa `box.*.z`; `elevationMetric` refleja la cota real.
- [ ] Código: `viewer.elementElevations` `.y`→`.z`; revisar `spatial-metric`.
- [ ] Re-baseline de tests de cota: `spatial-tree.test.ts`, `saneamiento.test.ts`.

## Paso 3 · Mapeo BCF → identidad (test-first)
- [ ] Re-baseline `test/bcf.test.ts` (78–84): `bcfCameraToViewer` devuelve la terna IFC sin
      permutar (position=[10,20,30]; up[2]≈0.816497).
- [ ] Código: `bcfCameraToViewer` = identidad; actualizar el comentario de `bcf.ts`.
- [ ] Confirmar que `federado-e2e.test.ts` (cámara IFC cruda) sigue VERDE sin cambios.

## Paso 4 · Framing y gizmo Z-up (test-first)
- [ ] Re-baseline `ux-behavior.test.ts` (cámara) para el framing Z-up.
- [ ] Código: vectores de `fitToModels`/`frameElement`; gizmo con Z vertical; comentario
      «MARCO DEL VISOR (Y-up)» → Z-up.

## Paso 5 · Idealización consistente
- [ ] Verificar `idealize.ts` (glifos/idealizado) con la geometría en Z-up; test si aplica.

## Pasos obligatorios (Llave 1)
- [ ] Ejecutar `pnpm -r typecheck` + `pnpm -r build` + `pnpm -r test` VERDE (documentar salida).
- [ ] `pnpm-lock.yaml` intacto (o el cambio va en el PR, justificado).
- [ ] Actualizar `apps/visor/DECISIONES.md` (V*) y el convenio en comentarios.
- [ ] PR `feat/visor-convenio-zup` → `main`; gate verde. (No requiere Llave 2 — ver proposal.)
