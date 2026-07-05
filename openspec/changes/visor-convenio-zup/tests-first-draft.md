# Tests-first (TDD «red») · Convenio Z-up del visor

> `frontend-standards.md`: el test se escribe ANTES que el código. Valores esperados derivados de
> la spec y **verificados numéricamente** (round-trip de la rotación). Listos para pegar en
> `apps/visor/test/` en la rama `feat/visor-convenio-zup`. NO ejecutables hasta que la rama exista
> (vitest corre en la máquina de JM / CI; el visor está en la Llave 1).

## Paso 1 · Rotación de ingesta a Z-up (unidad nueva)

La ingesta debe deshacer el swap de web-ifc con **+90° sobre X**: `(x,y,z)_yup → (x,−z,y)_ifc`.
Esto recupera el IFC Z-up (inverso exacto de `m(v)=[x,z,−y]` de `bcf.ts`).

```ts
// test/zup-ingesta.test.ts
import { describe, it, expect } from "vitest";
import { aZup } from "@aqyra/visor"; // helper NUEVO a exportar desde viewer/ifc-loader

describe("Ingesta Z-up · deshace el swap de web-ifc (+90° X)", () => {
  it("mapea un vértice Y-up de web-ifc de vuelta a IFC Z-up", () => {
    expect(aZup([1, 2, 3])).toEqual([1, -3, 2]);
  });
  it("round-trip: IFC→(web-ifc Y-up)→aZup === IFC", () => {
    const ifc: [number, number, number] = [10, 20, 30];
    const yup: [number, number, number] = [ifc[0], ifc[2], -ifc[1]]; // lo que entrega web-ifc
    expect(aZup(yup)).toEqual(ifc);
  });
});
```

## Paso 2 · Cota de elemento sobre `.z` (re-baseline / integración)

`elementElevations` toma el rango del AABB en el eje vertical de la escena. En Z-up, ese eje es
`.z` (hoy `.y`). Test de integración con el derivado congelado (misma fixture que el E2E):

```ts
// en test/spatial-tree.test.ts (o zup-cota.test.ts) — headless node + wasm helper
// GIVEN el derivado federado cargado en el Viewer en Z-up
// WHEN se piden elementElevations(modelID)
// THEN el rango de cota proviene de box.min.z / box.max.z
//      y coincide con las cotas reales de las plantas (getStoreys().elevation),
//      no con el eje horizontal. (Ancla: cota de EST monotónica con la planta.)
```

> Nota: `spatial-tree.test.ts` y `saneamiento.test.ts` que hoy anclan cota por `.y` se re-baselinan
> a `.z` en este paso.

## Paso 3 · `bcfCameraToViewer` = identidad (re-baseline de `test/bcf.test.ts` 78–84)

El bloque actual afirma la permutación `(x,y,z)→(x,z,−y)`. Con el visor en Z-up pasa a identidad:

```ts
  it("cámara BCF (IFC Z-up) = marco del visor (Z-up): identidad", () => {
    const v = parseViewpoint(VIEWPOINT);
    const c = bcfCameraToViewer(v.camera!);
    expect(c.position).toEqual([10, 20, 30]);        // antes: [10, 30, -20]
    expect(c.up[2]).toBeCloseTo(0.816497, 6);        // Z-up: el «arriba» está en .z (antes .y)
    expect(c.direction).toEqual([-0.577350, 0.577350, -0.577350]);
    expect(c.fovDeg).toBe(60);
  });
```

Y **queda igual (verde sin tocar)** `test/federado-e2e.test.ts` (95–104), que ancla la cámara
**cruda** de `parseViewpoint` en IFC Z-up → confirma que el golden C4-FED-06 (D29) no se re-firma.

## Paso 4 · Framing y gizmo (re-baseline `ux-behavior.test.ts`)

`fitToModels`/`frameElement` orientan con Z arriba (`camera.up=(0,0,1)`); el gizmo pinta Z vertical.
Re-baselinar las aserciones de cámara de `ux-behavior.test.ts` al encuadre Z-up.
