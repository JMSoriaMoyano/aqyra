import { defineAqyraViewer, configureAqyra, TAG } from "@aqyra/embed";

configureAqyra({ wasmPath: "/" });
defineAqyraViewer();

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

type Diag = HTMLElement & { load(x: unknown): Promise<unknown>; debugMeshCount(): number };
const el = document.createElement(TAG) as Diag;
el.style.cssText = "display:block;width:800px;height:600px";
document.getElementById("app")!.appendChild(el);

const win = window as unknown as Record<string, unknown>;
el.load({ name: "g", data: GEOM })
  .then(() => requestAnimationFrame(() => {
    win.__aqyraMeshes = el.debugMeshCount();
    win.__aqyraReady = true;
  }))
  .catch((e: unknown) => {
    win.__aqyraError = String(e);
    win.__aqyraReady = true;
  });
