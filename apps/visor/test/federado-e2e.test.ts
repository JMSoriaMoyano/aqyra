// @vitest-environment node
/** E2E headless del vertical del visor (V3, hilo 3.1): el visor abre el IFC
 *  federado DERIVADO congelado (identidad por md5 — el MISMO que ancla la golden
 *  C4-FED-06, D26) y lee su árbol BCF con la cámara del viewpoint (D29).
 *  Se ancla lo ESTRUCTURAL (conteos + cámara parseada == expected verificado a
 *  mano); nada de golden de píxeles. */
import { createHash } from "node:crypto";
import { readFileSync, readdirSync, existsSync } from "node:fs";
import { join, dirname } from "node:path";
import { fileURLToPath } from "node:url";
import { describe, it, expect, beforeAll } from "vitest";
import { JSDOM } from "jsdom";
import { wasmDir } from "./_wasm.js";
import { IfcLoader, parseMarkup, parseViewpoint } from "@aqyra/visor";
import type { SpatialNode } from "@aqyra/visor";

const aqui = dirname(fileURLToPath(import.meta.url));
const FIX = join(aqui, "..", "fixtures");

// Identidad del derivado — la MISMA que packages/golden/C4/C4-FED-06 (D26).
const MD5_DERIVADO = "dcb1e14460f3556107ce35d6dade16c3";
// Cámara del viewpoint del 06, verificada A MANO en 2.6 (D29):
// pos = pb_EST + (1,−1,1)·d, dir = (−1,1,−1)/√3, up = (−1,1,2)/√6.
const CAM_POS = [337013.5, 4609986.5, 702.25];
const CAM_DIR = [-0.57735, 0.57735, -0.57735];
const CAM_UP = [-0.408248, 0.408248, 0.816497];
const SELECTION = ["3OM3R50xH9rQrxdF_D157W", "1_IR0JcG90ghN9CC8WB7E9"];

const md5 = (b: Buffer): string => createHash("md5").update(b).digest("hex");

describe("E2E · el visor abre el Maestro (derivado C4-FED-06 + BCF con cámara)", () => {
  let loader: IfcLoader;
  beforeAll(async () => {
    // DOMParser para el parser BCF en entorno node (web-ifc exige node env).
    const dom = new JSDOM();
    (globalThis as unknown as { DOMParser: unknown }).DOMParser = dom.window.DOMParser;
    loader = new IfcLoader({ wasmPath: wasmDir, wasmAbsolute: true });
    await loader.init();
  });

  it("el derivado congelado ES el derivado (md5 byte a byte == golden C4-FED-06)", () => {
    const bytes = readFileSync(join(FIX, "federado.ifc"));
    expect(md5(bytes)).toBe(MD5_DERIVADO);
  });

  it("abre el derivado: IFC4X3, 1 IfcProject federado, los 13 IfcElement dentro", async () => {
    const data = readFileSync(join(FIX, "federado.ifc"), "utf-8");
    const m = await loader.open({ name: "federado", data });
    expect(m.schema.startsWith("IFC4X3")).toBe(true);
    // El derivado trae 13 IfcElement (ancla md5 == golden C4-FED-06). El catálogo del
    // loader (corte v0.4, byte a byte) enumera 11: NO lista IfcOpeningElement (los huecos
    // no son elementos de lista) ni IfcTransportElement (fuera del catálogo v0.4 —
    // HALLAZGO declarado del hilo 3.1; ampliarlo es decisión nueva, no parche silencioso).
    expect(m.elements.length).toBe(11);
    expect((data.match(/=IFCOPENINGELEMENT\(/g) ?? []).length).toBe(1);
    expect((data.match(/=IFCTRANSPORTELEMENT\(/g) ?? []).length).toBe(1);

    const root = await loader.getSpatialTree(m.modelID);
    expect(root.ifcType.toUpperCase()).toContain("IFCPROJECT");
    let proyectos = 0;
    const walk = (n: SpatialNode): void => {
      if (n.ifcType.toUpperCase().includes("IFCPROJECT")) proyectos += 1;
      n.children.forEach(walk);
    };
    walk(root);
    expect(proyectos).toBe(1);

    // la geometría federada tesela (los placements raíz de D27 no rompen la escena)
    expect(loader.getMeshes(m.modelID).length).toBeGreaterThan(0);
    loader.close(m.modelID);
  });

  it("lee el árbol BCF: 3 topics, solo el de elementos lleva viewpoint", () => {
    const raiz = join(FIX, "bcf");
    const topics = readdirSync(raiz, { withFileTypes: true })
      .filter((d) => d.isDirectory())
      .map((d) => d.name)
      .sort();
    expect(topics.length).toBe(3);
    let conViewpoint = 0;
    for (const t of topics) {
      const topic = parseMarkup(readFileSync(join(raiz, t, "markup.bcf"), "utf-8"));
      expect(topic.guid).toBe(t);
      if (topic.viewpointFile) {
        conViewpoint += 1;
        expect(existsSync(join(raiz, t, topic.viewpointFile))).toBe(true);
      }
    }
    expect(conViewpoint).toBe(1);
  });

  it("la cámara del viewpoint == expected (D29, verificada a mano)", () => {
    const vpPath = join(FIX, "bcf", "ae44673e-01e9-558f-b678-b55be81255f8", "viewpoint.bcfv");
    const vp = parseViewpoint(readFileSync(vpPath, "utf-8"));
    expect(vp.selection).toEqual(SELECTION);
    expect(vp.camera).toBeDefined();
    const c = vp.camera!;
    for (let i = 0; i < 3; i += 1) {
      expect(c.viewPoint[i]).toBeCloseTo(CAM_POS[i]!, 6);
      expect(c.direction[i]).toBeCloseTo(CAM_DIR[i]!, 5);
      expect(c.up[i]).toBeCloseTo(CAM_UP[i]!, 5);
    }
    expect(c.fovDeg).toBeCloseTo(60, 6);
    expect(c.aspect).toBeCloseTo(16 / 9, 5);
  });
});
