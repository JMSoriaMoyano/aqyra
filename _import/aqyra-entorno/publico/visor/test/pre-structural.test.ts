// @vitest-environment node
// Pre-proceso V2 sobre web-ifc headless: (1) DERIVAR el analítico de un físico
// con IfcExtrudedAreaSolid (sin 'Axis'); (2) WRITE-BACK del anejo Aqyra como
// texto diff-able y round-trip (reabrir → sigue ahí). Mismo harness que
// ifc-loader.test.ts (web-ifc en Node con el WASM de node_modules).
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, appendStructuralPset, stripStructuralPset, AQYRA_PSET } from "@aqyra/visor";

const WASM = wasmDir;

// Viga (IfcBeam) con geometría por extrusión: perfil 0.3×0.3 extruido 4.0 m en Z.
// La barra NO trae representación 'Axis' → el eje se DERIVA de la teselación.
const BEAM = `ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('beam.ifc','2026-06-24T00:00:00',(''),(''),'web-ifc','aqyra','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0YvhhKM7r0kugbFTuMU0AB',$,'Proj',$,$,$,$,(#20),#10);
#10=IFCUNITASSIGNMENT((#11));
#11=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#20=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#21,$);
#21=IFCAXIS2PLACEMENT3D(#22,$,$);
#22=IFCCARTESIANPOINT((0.,0.,0.));
#30=IFCBEAM('3vB2YO$MX4xv5uCqZZG05x',$,'Viga 1',$,$,#40,#50,$,$);
#40=IFCLOCALPLACEMENT($,#41);
#41=IFCAXIS2PLACEMENT3D(#22,$,$);
#50=IFCPRODUCTDEFINITIONSHAPE($,$,(#51));
#51=IFCSHAPEREPRESENTATION(#20,'Body','SweptSolid',(#60));
#60=IFCEXTRUDEDAREASOLID(#61,#64,#67,4.0);
#61=IFCRECTANGLEPROFILEDEF(.AREA.,$,#62,0.3,0.3);
#62=IFCAXIS2PLACEMENT2D(#63,$);
#63=IFCCARTESIANPOINT((0.,0.));
#64=IFCAXIS2PLACEMENT3D(#65,$,$);
#65=IFCCARTESIANPOINT((0.,0.,0.));
#67=IFCDIRECTION((0.,0.,1.));
ENDSEC;
END-ISO-10303-21;`;

describe("pre · derivación + write-back (V2 primer corte)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await loader.init();
  });

  it("deriva el modelo analítico de un físico con extrusión (sin 'Axis')", async () => {
    const m = await loader.open({ name: "beam", data: BEAM });
    const model = await loader.deriveStructural(m.modelID);
    expect(model.members.length).toBeGreaterThanOrEqual(1);
    expect(model.members[0]!.kind).toBe("beam");
    expect(model.members[0]!.length).toBeGreaterThan(1);
    expect(model.nodes.length).toBeGreaterThanOrEqual(2);
    loader.close(m.modelID);
  });

  it("write-back diff-able: append + strip restaura el original byte a byte", () => {
    const entries = [{ name: "load:L1", value: "kind=distributed;target=B30;value=5;dir=y;case=Q;state=proposal" }];
    const written = appendStructuralPset(BEAM, entries);
    expect(written).toContain(AQYRA_PSET);
    expect(written).toContain("target=B30");
    expect(written).not.toBe(BEAM);
    // El original queda intacto: retirar el anejo lo restaura exactamente.
    expect(stripStructuralPset(written)).toBe(BEAM);
  });

  it("round-trip: la carga persistida sigue ahí al reabrir el IFC", async () => {
    const entries = [{ name: "load:L1", value: "kind=distributed;target=B30;value=5;dir=y" }];
    const written = appendStructuralPset(BEAM, entries);
    const m = await loader.open({ name: "beam+anejo", data: written });
    const read = loader.readStructuralPset(m.modelID);
    expect(read.some((e) => e.name === "load:L1" && e.value.includes("target=B30"))).toBe(true);
    loader.close(m.modelID);
  });

  it("write-back idempotente: reescribir no duplica el anejo", () => {
    const w1 = appendStructuralPset(BEAM, [{ name: "load:L1", value: "value=5" }]);
    const w2 = appendStructuralPset(w1, [{ name: "load:L1", value: "value=8" }]);
    expect((w2.match(/AQYRA-PRE-START/g) ?? []).length).toBe(1);
    expect(w2).toContain("value=8");
    expect(w2).not.toContain("value=5");
  });
});
