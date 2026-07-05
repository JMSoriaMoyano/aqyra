// @vitest-environment node
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, Viewer, elevationMetric } from "@aqyra/visor";

const WASM = wasmDir;

// Convenio Z-up (paso 2): la cota vertical de un elemento se toma del eje Z de la
// escena (box.*.z), no del eje horizontal. Muro extruido a lo largo de Z con su
// centro geométrico en IFC z ≈ 4 (colocación z=3.5 + media altura 0.5); su otro
// eje (IFC y del perfil 4.0 x 0.3) queda ≈ 0. Así, leer la cota por Z da ≈4 y
// leerla por el eje horizontal daría ≈0: el test DISTINGUE el convenio.
const IFC = `ISO-10303-21;
HEADER;FILE_DESCRIPTION((''),'2;1');FILE_NAME('c.ifc','',(''),(''),'web-ifc','aqyra','');FILE_SCHEMA(('IFC4'));ENDSEC;
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

describe("Cota Z-up · elementElevations toma la cota del eje Z (paso 2)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await loader.init();
  });

  it("la cota del elemento sale de box.*.z (≈4), no del eje horizontal (≈0)", async () => {
    const m = await loader.open({ name: "c", data: IFC });
    const viewer = new Viewer();
    viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));

    const cota = viewer.elementElevations(m.modelID).get(70)!;
    expect(cota).toBeGreaterThan(3.4); // ≈4: cota real por Z
    expect(cota).toBeLessThan(4.6);
    // Si se leyera el eje horizontal (perfil ≈0) la cota caería < 1: lo descartamos.
    expect(cota).toBeGreaterThan(1);
    loader.close(m.modelID);
  });

  it("elevationMetric refleja la cota real: positions delega en la cota Z y containers usa IfcStorey.Elevation", async () => {
    const m = await loader.open({ name: "c2", data: IFC });
    const viewer = new Viewer();
    viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));

    // positions() = la cota Z del elemento (contrato del metric).
    const pos = elevationMetric.positions(viewer, m.modelID).get(70)!;
    const cotaZ = viewer.elementElevations(m.modelID).get(70)!;
    expect(pos).toBeCloseTo(cotaZ, 6);
    expect(pos).toBeGreaterThan(3.4);

    // containers() = cotas de las plantas (dato IFC, independiente del marco).
    const cont = await elevationMetric.containers(loader, m.modelID);
    expect(cont.map((c) => c.key)).toEqual([0, 3]);
    loader.close(m.modelID);
  });
});
