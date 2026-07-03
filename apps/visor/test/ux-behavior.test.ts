// @vitest-environment node
/** Comportamiento de la UX del lote 1 (Fase III·h4), headless y SIN WebGL (sin
 *  mount()). Ancla el CONTRATO de comportamiento de los métodos nuevos del Viewer:
 *  acento (#1/#9), ghost del resto (#1), encuadre a elemento (#9) y vista general
 *  (#4). No hay golden de píxeles (V6·U5): se asevera el efecto observable sobre la
 *  escena three.js, que se construye igual en Node. */
import { describe, it, expect, beforeAll } from "vitest";
import * as THREE from "three";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, Viewer } from "@aqyra/visor";

const WASM = wasmDir;
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

/** Acceso de solo lectura al estado interno de la escena (props de runtime; no
 *  amplía la API pública — TS `private` es una propiedad normal en JS). */
interface ViewerInternals {
  camera: THREE.PerspectiveCamera;
  models: THREE.Group;
}
function meshesDe(v: Viewer): THREE.Mesh[] {
  const grp = (v as unknown as ViewerInternals).models;
  const out: THREE.Mesh[] = [];
  grp.traverse((o) => { if ((o as THREE.Mesh).isMesh) out.push(o as THREE.Mesh); });
  return out;
}
function camDe(v: Viewer): THREE.PerspectiveCamera {
  return (v as unknown as ViewerInternals).camera;
}

describe("UX lote 1 · comportamiento del Viewer (headless, sin GPU)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await loader.init();
  });

  it("highlightSelection pinta ACENTO y clearSelectionAccent lo restaura (#1/#9)", async () => {
    const m = await loader.open({ name: "g", data: GEOM });
    const v = new Viewer();
    v.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
    const mesh = meshesDe(v)[0]!;
    const id = mesh.userData.expressId as number;
    const emisivo0 = (mesh.material as THREE.MeshLambertMaterial).emissive.getHex();

    v.highlightSelection(m.modelID, [id], { accent: 0xff8a3d });
    expect((mesh.material as THREE.MeshLambertMaterial).emissive.getHex()).toBe(0xff8a3d);

    v.clearSelectionAccent();
    expect((mesh.material as THREE.MeshLambertMaterial).emissive.getHex()).toBe(emisivo0);
    loader.close(m.modelID);
  });

  it("ghost atenúa lo NO seleccionado; showAll lo restaura (#1)", async () => {
    const m = await loader.open({ name: "g", data: GEOM });
    const v = new Viewer();
    v.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
    const mesh = meshesDe(v)[0]!;
    const opacidad0 = (mesh.material as THREE.MeshLambertMaterial).opacity;

    // conjunto vacío ⇒ el muro NO está en `keep` ⇒ queda fantasma.
    v.highlightSelection(m.modelID, [], { ghost: true });
    const mat = mesh.material as THREE.MeshLambertMaterial;
    expect(mat.opacity).toBeLessThan(1);
    expect(mat.transparent).toBe(true);

    v.showAll();
    expect((mesh.material as THREE.MeshLambertMaterial).opacity).toBe(opacidad0);
    loader.close(m.modelID);
  });

  it("frameElement mueve la cámara al elemento; frameAll re-encuadra (#4/#9)", async () => {
    const m = await loader.open({ name: "g", data: GEOM });
    const v = new Viewer();
    v.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
    const mesh = meshesDe(v)[0]!;
    const id = mesh.userData.expressId as number;
    const cam = camDe(v);
    const antes = cam.position.clone();

    v.frameElement(m.modelID, id);
    const finito = Number.isFinite(cam.position.x) && Number.isFinite(cam.position.y) && Number.isFinite(cam.position.z);
    expect(finito).toBe(true);
    // se movió respecto a la posición previa (addIfcModel ya encuadró; frameElement acerca).
    expect(cam.position.distanceTo(antes)).toBeGreaterThan(0);

    v.frameAll();
    expect(Number.isFinite(cam.position.x)).toBe(true);
    loader.close(m.modelID);
  });
});
