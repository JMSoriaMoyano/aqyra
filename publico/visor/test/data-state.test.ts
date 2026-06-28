// Estado de dato (D-021) — la MECÁNICA de las dos llaves: regla dura del verde,
// vocabulario visual y guarda de exportación. La frontera de confianza es BINARIA:
// solo `verified-signed` recibe el trato certificado.
import { describe, it, expect } from "vitest";
import { dataStateStyle, isCertified, exportStamp, stampIfcText } from "@aqyra/visor";
import type { DataState } from "@aqyra/visor";

const ALL: DataState[] = ["proposal", "computed", "qa-passed", "verified-signed"];

describe("estado de dato · regla dura del verde (D-021)", () => {
  it("isCertified es true SOLO para verified-signed", () => {
    expect(ALL.filter(isCertified)).toEqual(["verified-signed"]);
  });

  it("un layer `computed` NUNCA recibe el trato certificado", () => {
    const s = dataStateStyle("computed");
    expect(s.certified).toBe(false);
    expect(s.watermark).toBe(true); // se ve provisional
    expect(isCertified("computed")).toBe(false);
  });

  it("qa-passed (1.ª llave) sigue sin ser certificado y lleva marca", () => {
    const s = dataStateStyle("qa-passed");
    expect(s.certified).toBe(false);
    expect(s.watermark).toBe(true);
    expect(s.iso).toBe("S3");
  });

  it("verified-signed es el único certificado, limpio y sin marca", () => {
    const s = dataStateStyle("verified-signed");
    expect(s.certified).toBe(true);
    expect(s.watermark).toBe(false);
    expect(s.iso).toBe("A");
  });
});

describe("estado de dato · guarda de exportación (D-021·C.2)", () => {
  it("exportStamp marca toda salida no firmada y NO la firmada", () => {
    expect(exportStamp("computed")).toContain("NO VERIFICADO");
    expect(exportStamp("proposal")).toContain("NO VERIFICADO");
    expect(exportStamp("qa-passed")).toContain("NO VERIFICADO");
    expect(exportStamp("verified-signed")).toBeNull();
  });

  it("stampIfcText inserta el comentario STEP tras DATA; si no está firmado", () => {
    const ifc = "ISO-10303-21;\nHEADER;\nENDSEC;\nDATA;\n#1=IFCPROJECT();\nENDSEC;\nEND-ISO-10303-21;\n";
    const out = stampIfcText(ifc, "computed");
    expect(out).toContain("/* AQYRA · NO VERIFICADO");
    expect(out.indexOf("AQYRA")).toBeGreaterThan(out.indexOf("DATA;")); // tras DATA;
    expect(out).toContain("#1=IFCPROJECT();"); // no destruye el contenido
  });

  it("stampIfcText es idempotente y respeta el texto firmado", () => {
    const ifc = "ISO-10303-21;\nDATA;\n#1=IFCPROJECT();\nENDSEC;\n";
    const once = stampIfcText(ifc, "proposal");
    const twice = stampIfcText(once, "proposal");
    expect(twice).toBe(once); // no duplica la marca
    expect(stampIfcText(ifc, "verified-signed")).toBe(ifc); // firmado: intacto
  });
});
