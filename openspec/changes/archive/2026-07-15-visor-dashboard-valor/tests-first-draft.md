# Tests-first (TDD «red») · Skin del visor · Dashboard de valor (E6.1)

> El dashboard es `apps/` puro: presentación de la proyección precomputada. La lógica (consumo del índice,
> invariante Σ, orden, selección→GUIDs, regla `isCertified`) se aísla en `dashboard.ts` (sin three/web-ifc) y
> corre en `vitest` headless. La aceptación **reproduce `GOL-PRE-03`** desde una fixture emitida del engine
> (no un oráculo propio). El visor está en la Llave 1; el loop TS corre en la máquina de JM. Base:
> `apps/visor/test/`.

## Consumo del índice + invariante Σ (lógica pura, `dashboard.ts`)

```ts
import { describe, it, expect } from "vitest";
// import { modeloVista, sumaVista } from "@aqyra/visor"; // dashboard.ts, NUEVO

describe("dashboard · consume la proyección, no la calcula", () => {
  it.todo("dada una vista (coste, espacial), produce una fila por grupo con valor_total/unidad/fuente del índice");
  it.todo("no altera ningún valor_total (la presentación es lectura, no cálculo)");
  it.todo("dos renders del mismo índice → mismas filas y mismo orden (determinismo)");
});

describe("dashboard · invariante Σ", () => {
  it.todo("Σ valor_total(grupos) == suma de la vista (±0,01)");
  it.todo("muestra los grupos residuales (sin geometría)/(sin clasificar) con su fuente, sin ocultarlos");
});
```

## Reproducción de `GOL-PRE-03` (aceptación, contra fixture emitida del engine)

```ts
// La fixture es el índice de proyección de la muestra, emitido por el engine (patrón derivado/BCF).
// Sus valores DEBEN casar con packages/golden/C5/GOL-PRE-03/expected.json.

describe("dashboard · reproduce GOL-PRE-03 (coste)", () => {
  it.todo("(coste, espacial): '…/Planta Baja'=3815.28 (ifc), '…/Nivel 01'=2502.9 (ifc), '(sin geometría)'=137.7 (regla); Σ=7022.53");
  it.todo("(coste, uniclass): '(sin clasificar)'=6884.83 (—) + '(sin geometría)'=137.7 (regla); Σ=7022.53");
  it.todo("(coste, funcional): 'Estructura'=3754.35 (criterio), 'Aulas'=1820.66 (ifc), 'Sys-Portico'=543.84 (ifc); Σ=7022.53");
  it.todo("un desajuste se corrige re-emitiendo la fixture del engine, NUNCA editando el cliente");
});
```

## Selección → GUIDs (integración con la selección del `Viewer`)

```ts
describe("dashboard · selección → 3D", () => {
  it.todo("seleccionar una fila expone exactamente los guids[] de ese grupo");
  it.todo("el resaltado no reescribe el modelo ni la geometría (operación de presentación)");
});
```

## Regla dura «propone» (reutiliza `data-state.ts`, test real hoy)

```ts
import { isCertified } from "@aqyra/visor";

describe("la vista de proyección no certifica", () => {
  it("ninguna proyección mostrada es 'verified-signed'", () => {
    // la proyección es consulta; el export firmable (dos llaves) llega como acción, no como estado de la vista
    expect(isCertified("proposal")).toBe(false);
    expect(isCertified("computed")).toBe(false);
    expect(isCertified("verified-signed")).toBe(true); // sólo el export firmado, forward
  });
});
```

## Fuera de vitest (forward)

> El **export firmable de la proyección** (dos llaves, muro de cobro) es forward: su tests-first será su
> **golden con oráculo** (runner `aqyra-golden`) cuando JM lo abra, no vitest. En v0 la skin sólo presenta.
