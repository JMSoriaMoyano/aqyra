# apps/visor — el visor abierto de Aqyra

`@aqyra/visor` 0.5.0 — el núcleo del visor OpenBIM (carga IFC con web-ifc, escena 3D
con three.js, selección con Psets, árbol espacial, lectura BCF 3.0 con cámara).
Re-home del corte mínimo de aqyra-entorno (hilo 3.1; procedencia y decisiones V1–V5
en `DECISIONES.md`). El visor CONSUME lo que `services/federacion` produce
(el IFC federado DERIVADO, D26, y el árbol BCF, D12/D29); nunca lo re-genera.

## Comandos (workspace pnpm, raíz del monorepo)

    pnpm install            # una vez (lockfile anclado)
    pnpm -r typecheck       # tsc real (la Llave 1 del TS)
    pnpm -r build           # dist/
    pnpm -r test            # vitest: 11 suites, incl. el E2E del derivado congelado

## La demo (el Maestro en pantalla)

    cd apps/visor && pnpm demo

Abre el IFC federado derivado del C4-FED-06 (md5 anclado), pinta la estructura
espacial federada (EST rotado 30°, D27) y lista los topics BCF: al seleccionar el
topic con viewpoint se aplica la CÁMARA determinista (D29) y se resaltan sus
Components. Las fixtures de `fixtures/` son los artefactos anclados de la golden
C4-FED-06 (md5 por fichero).
