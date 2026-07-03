// @vitest-environment node
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcLoader } from "@aqyra/visor";
import type { SpatialNode } from "@aqyra/visor";

const WASM = wasmDir;
const IFC = `ISO-10303-21;
HEADER;
FILE_DESCRIPTION((''),'2;1');
FILE_NAME('s.ifc','2026-06-24T00:00:00',(''),(''),'web-ifc','aqyra','');
FILE_SCHEMA(('IFC4'));
ENDSEC;
DATA;
#1=IFCPROJECT('0proyectoAAAAAAAAAAAAA',$,'Proyecto',$,$,$,$,(#20),#10);
#10=IFCUNITASSIGNMENT((#11));
#11=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#20=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#21,$);
#21=IFCAXIS2PLACEMENT3D(#22,$,$);
#22=IFCCARTESIANPOINT((0.,0.,0.));
#40=IFCSITE('1sitioAAAAAAAAAAAAAAAA',$,'Parcela',$,$,#41,$,$,.ELEMENT.,$,$,$,$,$);
#41=IFCLOCALPLACEMENT($,#21);
#50=IFCBUILDING('2edificioAAAAAAAAAAAAA',$,'Edificio',$,$,#51,$,$,.ELEMENT.,$,$,$);
#51=IFCLOCALPLACEMENT(#41,#21);
#60=IFCBUILDINGSTOREY('3planta1AAAAAAAAAAAAA',$,'Planta 1',$,$,#61,$,$,.ELEMENT.,0.);
#61=IFCLOCALPLACEMENT(#51,#21);
#70=IFCWALL('4muro1AAAAAAAAAAAAAAAA',$,'Muro 1',$,$,#71,$,$,$);
#71=IFCLOCALPLACEMENT(#61,#21);
#100=IFCRELAGGREGATES('5relagg1AAAAAAAAAAAAA',$,$,$,#1,(#40));
#101=IFCRELAGGREGATES('6relagg2AAAAAAAAAAAAA',$,$,$,#40,(#50));
#102=IFCRELAGGREGATES('7relagg3AAAAAAAAAAAAA',$,$,$,#50,(#60));
#110=IFCRELCONTAINEDINSPATIALSTRUCTURE('8relcont1AAAAAAAAAAAA',$,$,$,(#70),#60);
ENDSEC;
END-ISO-10303-21;`;

function find(n: SpatialNode, pred: (x: SpatialNode) => boolean): SpatialNode | undefined {
  if (pred(n)) return n;
  for (const c of n.children) {
    const r = find(c, pred);
    if (r) return r;
  }
  return undefined;
}

describe("Árbol espacial · F2 (headless)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await loader.init();
  });

  it("construye Proyecto > Sitio > Edificio > Planta > Muro", async () => {
    const m = await loader.open({ name: "s", data: IFC });
    const root = await loader.getSpatialTree(m.modelID);
    expect(root.ifcType.toUpperCase()).toContain("IFCPROJECT");
    const storey = find(root, (x) => x.ifcType.toUpperCase().includes("BUILDINGSTOREY"));
    expect(storey?.name).toBe("Planta 1");
    const wall = find(root, (x) => x.ifcType.toUpperCase().includes("IFCWALL"));
    expect(wall?.name).toBe("Muro 1");
    loader.close(m.modelID);
  });
});
