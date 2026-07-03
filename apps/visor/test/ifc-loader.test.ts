// @vitest-environment node
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, ModelRegistry } from "@aqyra/visor";

const WASM = wasmDir;

const ifc = (schema: string, wallGuid: string): string => `ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('t.ifc','2026-06-24T00:00:00',(''),(''),'web-ifc','aqyra','');
FILE_SCHEMA(('${schema}'));
ENDSEC;
DATA;
#1=IFCPROJECT('0YvhhKM7r0kugbFTuMU0AB',$,'Proj',$,$,$,$,$,$);
#10=IFCWALL('${wallGuid}',$,'Muro 1',$,$,$,$,$,$);
#20=IFCPROPERTYSINGLEVALUE('IsExternal',$,IFCBOOLEAN(.T.),$);
#21=IFCPROPERTYSET('1kTvXnbbzCWw8lcMd1dR4o',$,'Pset_WallCommon',$,(#20));
#22=IFCRELDEFINESBYPROPERTIES('2kTvXnbbzCWw8lcMd1dR4p',$,$,$,(#10),#21);
ENDSEC;
END-ISO-10303-21;`;

const GEOM = `ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('g.ifc','2026-06-24T00:00:00',(''),(''),'web-ifc','aqyra','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0YvhhKM7r0kugbFTuMU0AB',$,'Proj',$,$,$,$,(#20),#10);
#10=IFCUNITASSIGNMENT((#11));
#11=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#20=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#21,$);
#21=IFCAXIS2PLACEMENT3D(#22,$,$);
#22=IFCCARTESIANPOINT((0.,0.,0.));
#30=IFCWALL('3vB2YO$MX4xv5uCqZZG05x',$,'Muro 1',$,$,#40,#50,$,$);
#40=IFCLOCALPLACEMENT($,#41);
#41=IFCAXIS2PLACEMENT3D(#22,$,$);
#50=IFCPRODUCTDEFINITIONSHAPE($,$,(#51));
#51=IFCSHAPEREPRESENTATION(#20,'Body','SweptSolid',(#60));
#60=IFCEXTRUDEDAREASOLID(#61,#64,#67,3.0);
#61=IFCRECTANGLEPROFILEDEF(.AREA.,$,#62,4.0,0.3);
#62=IFCAXIS2PLACEMENT2D(#63,$);
#63=IFCCARTESIANPOINT((0.,0.));
#64=IFCAXIS2PLACEMENT3D(#65,$,$);
#65=IFCCARTESIANPOINT((0.,0.,0.));
#67=IFCDIRECTION((0.,0.,1.));
ENDSEC;
END-ISO-10303-21;`;

describe("IfcLoader · F1 (carga IFC headless)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await loader.init();
  });

  it("detecta IFC4 y enumera elementos con GlobalId", async () => {
    const m = await loader.open({ name: "a", data: ifc("IFC4", "3vB2YO$MX4xv5uCqZZG05x") });
    expect(m.schema).toBe("IFC4");
    expect(m.elements.length).toBe(1);
    expect(m.elements[0].ifcType).toBe("IFCWALL");
    expect(m.elements[0].globalId).toBe("3vB2YO$MX4xv5uCqZZG05x");
    loader.close(m.modelID);
  });

  it("soporta IFC4.3 (IFC4X3)", async () => {
    const m = await loader.open({ name: "b", data: ifc("IFC4X3", "1aaaaaaaaaaaaaaaaaaaaa") });
    expect(m.schema).toBe("IFC4X3");
    loader.close(m.modelID);
  });

  it("federa ≥2 modelos con índice por GlobalId", async () => {
    const reg = new ModelRegistry();
    const a = await loader.open({ name: "torre", data: ifc("IFC4", "3vB2YO$MX4xv5uCqZZG05x") });
    const b = await loader.open({ name: "cimentacion", data: ifc("IFC4X3", "9bbbbbbbbbbbbbbbbbbbbb") });
    reg.add(a);
    reg.add(b);
    expect(reg.list().length).toBe(2);
    expect(reg.findByGlobalId("9bbbbbbbbbbbbbbbbbbbbb")?.model.name).toBe("cimentacion");
    loader.close(a.modelID);
    loader.close(b.modelID);
  });

  it("lee Psets del elemento", async () => {
    const m = await loader.open({ name: "c", data: ifc("IFC4", "3vB2YO$MX4xv5uCqZZG05x") });
    const e = m.elements[0]!;
    const props = await loader.getProperties(m.modelID, e.expressId, e.globalId);
    expect(props.psets["Pset_WallCommon"]).toBeDefined();
    expect("IsExternal" in props.psets["Pset_WallCommon"]!).toBe(true);
    loader.close(m.modelID);
  });

  it("tesela geometría (web-ifc → arrays neutros)", async () => {
    const m = await loader.open({ name: "g", data: GEOM });
    const meshes = loader.getMeshes(m.modelID);
    expect(meshes.length).toBeGreaterThan(0);
    expect(meshes[0]!.positions.length).toBeGreaterThan(0);
    const idxCount = meshes.reduce((a, x) => a + x.indices.length, 0);
    expect(idxCount).toBe(36);
    loader.close(m.modelID);
  });
});
