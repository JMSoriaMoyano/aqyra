// Slice 2 · estado de dato por elemento (SSD, test antes que código). Dominio PURO: sin
// three/web-ifc/WASM. Ratificado por JM (2026-07-07): D-SL2-1 = estado por presencia de Pset de
// resultado. El visor NUNCA acuña el verde (isCertified manda, D-021).
import { describe, it, expect } from "vitest";
import { estadoDato, dataStateStyle, isCertified } from "@aqyra/visor";

describe("estadoDato · deriva el estado del elemento por sus Psets (D-SL2-1)", () => {
  it("con Pset de resultado → computed", () => {
    expect(estadoDato(["Pset_BeamCommon", "Pset_AqyraStructural"])).toBe("computed");
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
