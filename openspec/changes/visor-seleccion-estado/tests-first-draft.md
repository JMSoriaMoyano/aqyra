# Tests-first (TDD «red») · Selección + estado de dato (Slice 2)

> `estadoDato` es dominio PURO (sin three/web-ifc/WASM): tests headless directos. Listos para
> pegar en `apps/visor/test/estado-dato.test.ts` en la rama `feat/visor-seleccion-estado`.

```ts
// test/estado-dato.test.ts
import { describe, it, expect } from "vitest";
import { estadoDato, dataStateStyle, isCertified } from "@aqyra/visor";

describe("estadoDato · deriva el estado del elemento por sus Psets", () => {
  it("con Pset de resultado → computed", () => {
    expect(estadoDato(["Pset_WallCommon", "Pset_AqyraStructural"])).toBe("computed");
    expect(estadoDato(["Pset_Estructurando_ResultadoViga"])).toBe("computed");
  });
  it("sin Pset de resultado → proposal", () => {
    expect(estadoDato(["Pset_WallCommon"])).toBe("proposal");
    expect(estadoDato([])).toBe("proposal");
  });
  it("nunca infiere verified-signed", () => {
    expect(estadoDato(["Pset_AqyraStructural"])).not.toBe("verified-signed");
  });
  it("respeta un estado explícito provisto por el dato", () => {
    expect(estadoDato(["Pset_WallCommon"], "verified-signed")).toBe("verified-signed");
    expect(estadoDato([], "qa-passed")).toBe("qa-passed");
  });
});

describe("el chip usa el estilo y la regla dura del estado (D-021)", () => {
  it("computed = NO VERIFICADO (rojo), no certificado", () => {
    const st = dataStateStyle(estadoDato(["Pset_AqyraStructural"]));
    expect(st.label).toBe("NO VERIFICADO");
    expect(isCertified("computed")).toBe(false);
  });
  it("solo verified-signed es certificado", () => {
    expect(isCertified("verified-signed")).toBe(true);
    expect(isCertified("qa-passed")).toBe(false);
  });
});
```

> El cableado del chip al panel (`demo/main.ts`) se verifica visualmente en la demo (Paso 2);
> la lógica del estado queda cubierta por estos tests puros (la «red» del TDD).
