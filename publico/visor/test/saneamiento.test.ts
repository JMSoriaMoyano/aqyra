// @vitest-environment node
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, Viewer } from "@aqyra/visor";
import type { Storey } from "@aqyra/visor";

const WASM = wasmDir;

// Muro con geometría centrada en Y≈4 (planta a cota 3), pero CONTENIDO en la planta a cota 0.
const IFC = `ISO-10303-21;
HEADER;FILE_DESCRIPTION((''),'2;1');FILE_NAME('s.ifc','',(''),(''),'web-ifc','aqyra','');FILE_SCHEMA(('IFC4'));ENDSEC;
DATA;
#1=IFCPROJECT('0pr',$,'P',$,$,$,$,(#20),#10);#10=IFCUNITASSIGNMENT((#11));#11=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#20=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#21,$);#21=IFCAXIS2PLACEMENT3D(#22,$,$);#22=IFCCARTESIANPOINT((0.,0.,0.));
#40=IFCSITE('0si',$,'S',$,$,$,$,$,.ELEMENT.,$,$,$,$,$);
#50=IFCBUILDING('0bl',$,'B',$,$,$,$,$,.ELEMENT.,$,$,$);
#60=IFCBUILDINGSTOREY('0st1',$,'Planta 0',$,$,$,$,$,.ELEMENT.,0.);
#62=IFCBUILDINGSTOREY('0st2',$,'Planta 1',$,$,$,$,$,.ELEMENT.,3.0);
#70=IFCWALL('0wl',$,'Muro 1',$,$,#71,#80,$,$);
#71=IFCLOCALPLACEMENT($,#72);#72=IFCAXIS2PLACEMENT3D(#73,$,$);#73=IFCCARTESIANPOINT((0.,0.,3.5));
#80=IFCPRODUCTDEFINITIONSHAPE($,$,(#81));#81=IFCSHAPEREPRESENTATION(#20,'Body','SweptSolid',(#90));
#90=IFCEXTRUDEDAREASOLID(#91,#94,#97,1.0);#91=IFCRECTANGLEPROFILEDEF(.AREA.,$,#92,4.0,0.3);#92=IFCAXIS2PLACEMENT2D(#93,$);#93=IFCCARTESIANPOINT((0.,0.));
#94=IFCAXIS2PLACEMENT3D(#95,$,$);#95=IFCCARTESIANPOINT((0.,0.,0.));#97=IFCDIRECTION((0.,0.,1.));
#100=IFCRELAGGREGATES('0ra1',$,$,$,#1,(#40));#101=IFCRELAGGREGATES('0ra2',$,$,$,#40,(#50));#102=IFCRELAGGREGATES('0ra3',$,$,$,#50,(#60,#62));
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('0rc1',$,$,$,(#70),#60);
ENDSEC;END-ISO-10303-21;`;

function storeyFor(y: number, storeys: Storey[]): Storey {
  let chosen = storeys[0]!;
  for (const s of storeys) {
    if (y >= s.elevation - 1e-6) chosen = s;
    else break;
  }
  return chosen;
}

describe("Saneamiento espacial · V1 carril (headless)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await loader.init();
  });

  it("detecta el muro mal asignado y lo corrige en el IFC reescrito", async () => {
    const m = await loader.open({ name: "s", data: IFC });
    const viewer = new Viewer();
    viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));

    const storeys = await loader.getStoreys(m.modelID);
    expect(storeys.map((s) => s.elevation)).toEqual([0, 3]);
    const p0 = storeys.find((s) => s.name === "Planta 0")!;
    const p1 = storeys.find((s) => s.name === "Planta 1")!;

    const elev = viewer.elementElevations(m.modelID);
    const wallY = elev.get(70)!;
    expect(wallY).toBeGreaterThan(3.4); // ~4

    const current = await loader.getElementStorey(m.modelID);
    expect(current.get(70)).toBe(p0.expressId); // mal: contenido en Planta 0

    const target = storeyFor(wallY, storeys);
    expect(target.expressId).toBe(p1.expressId); // debería ir a Planta 1

    const bytes = loader.reassignSpatial(m.modelID, [{ expressId: 70, toStorey: p1.expressId }]);
    loader.close(m.modelID);

    const m2 = await loader.open({ name: "s2", data: bytes });
    const fixed = await loader.getElementStorey(m2.modelID);
    expect(fixed.get(70)).toBe(p1.expressId); // ya en Planta 1
    loader.close(m2.modelID);
  });
});
