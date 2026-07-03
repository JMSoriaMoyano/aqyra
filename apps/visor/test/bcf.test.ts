import { describe, it, expect } from "vitest";
import { parseMarkup, parseViewpoint, bcfCameraToViewer } from "@aqyra/visor";

const MARKUP = `<?xml version="1.0" encoding="utf-8"?>
<Markup>
  <Topic Guid="ae44673e-01e9-558f-b678-b55be81255f8" TopicType="Issue" TopicStatus="Open">
    <Title>R5-PLANTAS no conforme en EST (P1 / P2)</Title>
    <Priority>menor</Priority>
    <Labels>
      <Label>R5-PLANTAS</Label>
      <Label>modelo:EST</Label>
    </Labels>
    <CreationDate>2026-07-03T00:00:00Z</CreationDate>
    <CreationAuthor>services/federacion 0.5.0</CreationAuthor>
    <Description>Requisito R5-PLANTAS no conforme en el modelo EST.</Description>
    <Viewpoints>
      <ViewPoint Guid="47ad952d-e171-51fa-845c-dc7c8d62b660">
        <Viewpoint>viewpoint.bcfv</Viewpoint>
      </ViewPoint>
    </Viewpoints>
  </Topic>
</Markup>`;

const MARKUP_SIN_VP = `<?xml version="1.0" encoding="utf-8"?>
<Markup>
  <Topic Guid="x" TopicType="Issue" TopicStatus="Open">
    <Title>R4-GEORREF</Title>
    <Priority>mayor</Priority>
    <CreationDate>2026-07-03T00:00:00Z</CreationDate>
    <CreationAuthor>a</CreationAuthor>
  </Topic>
</Markup>`;

const VIEWPOINT = `<?xml version="1.0" encoding="utf-8"?>
<VisualizationInfo Guid="47ad952d-e171-51fa-845c-dc7c8d62b660">
  <Components>
    <Selection>
      <Component IfcGuid="3OM3R50xH9rQrxdF_D157W"/>
      <Component IfcGuid="1_IR0JcG90ghN9CC8WB7E9"/>
    </Selection>
    <Visibility DefaultVisibility="true"/>
  </Components>
  <PerspectiveCamera>
    <CameraViewPoint><X>10.000000</X><Y>20.000000</Y><Z>30.000000</Z></CameraViewPoint>
    <CameraDirection><X>-0.577350</X><Y>0.577350</Y><Z>-0.577350</Z></CameraDirection>
    <CameraUpVector><X>-0.408248</X><Y>0.408248</Y><Z>0.816497</Z></CameraUpVector>
    <FieldOfView>60.000000</FieldOfView>
    <AspectRatio>1.777778</AspectRatio>
  </PerspectiveCamera>
</VisualizationInfo>`;

describe("BCF 3.0 · lectura (markup + viewpoint + cámara)", () => {
  it("parsea el topic con labels, prioridad y ref al viewpoint", () => {
    const t = parseMarkup(MARKUP);
    expect(t.guid).toBe("ae44673e-01e9-558f-b678-b55be81255f8");
    expect(t.title).toContain("R5-PLANTAS");
    expect(t.priority).toBe("menor");
    expect(t.labels).toEqual(["R5-PLANTAS", "modelo:EST"]);
    expect(t.viewpointFile).toBe("viewpoint.bcfv");
    expect(t.viewpointGuid).toBe("47ad952d-e171-51fa-845c-dc7c8d62b660");
  });

  it("topic sin viewpoint (regla de módulo a nivel de proyecto)", () => {
    const t = parseMarkup(MARKUP_SIN_VP);
    expect(t.viewpointFile).toBeUndefined();
    expect(t.priority).toBe("mayor");
  });

  it("parsea el viewpoint: selección + PerspectiveCamera (D29)", () => {
    const v = parseViewpoint(VIEWPOINT);
    expect(v.selection).toEqual(["3OM3R50xH9rQrxdF_D157W", "1_IR0JcG90ghN9CC8WB7E9"]);
    expect(v.camera).toBeDefined();
    expect(v.camera!.viewPoint).toEqual([10, 20, 30]);
    expect(v.camera!.fovDeg).toBeCloseTo(60, 6);
    expect(v.camera!.aspect).toBeCloseTo(16 / 9, 5);
  });

  it("mapea IFC (Z-up) → visor (Y-up): (x,y,z) → (x,z,−y)", () => {
    const v = parseViewpoint(VIEWPOINT);
    const c = bcfCameraToViewer(v.camera!);
    expect(c.position).toEqual([10, 30, -20]);
    expect(c.up[1]).toBeCloseTo(0.816497, 6);
    expect(c.fovDeg).toBe(60);
  });
});
