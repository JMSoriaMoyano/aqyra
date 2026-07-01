// @vitest-environment node
import { describe, it, expect, beforeAll } from "vitest";
import { wasmDir } from "./_wasm.js";
import { IfcAuthor, IfcLoader, gridToMesh, type SpatialSeed } from "@aqyra/visor";

const WASM = wasmDir;

// Golden del INCREMENTO 1 de autoría (P1 · decisión JM Q1=A, Q2=C):
// "el editor crea estructura espacial + un IfcSpace, exporta IFC válido y el
//  propio IfcLoader lo reabre coherente (round-trip)". La IA prepara; JM firma.
const seed: SpatialSeed = {
  project: { name: "Can_Cabassa" },
  site: { name: "0419901DF2901H0001WW", longName: "Can Cabassa" },
  building: { name: "Edificio 2", longName: "Edificio 2 del conjunto Can Cabassa" },
  storey: { name: "AQ-NIV-P03", longName: "Planta tipo +10.60", elevation: 10.6 },
  spaces: [{ name: "AQ-ESP-HAB-P03-IZQ-01", longName: "Habitacion" }],
};

describe("IfcAuthor · incremento 1 (autoría: estructura espacial + IfcSpace)", () => {
  let author: IfcAuthor;
  let loader: IfcLoader;
  beforeAll(async () => {
    author = new IfcAuthor({ wasmPath: WASM, wasmAbsolute: true });
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await author.init();
    await loader.init();
  });

  it("autora un IFC4 válido con proyecto, jerarquía espacial y espacio", async () => {
    const r = await author.createSpatial(seed);
    expect(r.schema).toBe("IFC4");
    expect(r.ifc).toContain("FILE_SCHEMA(('IFC4'))");
    expect(r.ifc).toContain("IFCPROJECT");
    expect(r.ifc).toContain("IFCBUILDINGSTOREY");
    expect(r.ifc).toContain("AQ-ESP-HAB-P03-IZQ-01");
    // unidades SI en metros (no milímetros)
    expect(r.ifc).toContain(".LENGTHUNIT.,$,.METRE.");
    author.close(r.modelID);
  });

  it("round-trip: el IfcLoader reabre el IFC autorado con la planta +10.60", async () => {
    const r = await author.createSpatial(seed);
    author.close(r.modelID);
    const m = await loader.open({ name: "autorado", data: r.ifc });
    expect(m.schema).toBe("IFC4");
    const storeys = await loader.getStoreys(m.modelID);
    expect(storeys.length).toBe(1);
    expect(storeys[0]!.name).toBe("AQ-NIV-P03");
    expect(storeys[0]!.elevation).toBeCloseTo(10.6, 2);
    loader.close(m.modelID);
  });

  it("agrega cada espacio a su planta (IfcRelAggregates)", async () => {
    const r = await author.createSpatial({
      ...seed,
      spaces: [
        { name: "AQ-ESP-HAB-P03-IZQ-01", longName: "Habitacion" },
        { name: "AQ-ESP-HAB-P03-DER-01", longName: "Habitacion" },
      ],
    });
    // Project→Site, Site→Building, Building→Storey, Storey→[2 espacios] = 4 relaciones
    const rels = r.ifc.split("\n").filter((l) => l.includes("IFCRELAGGREGATES")).length;
    expect(rels).toBe(4);
    expect(r.ifc).toContain("AQ-ESP-HAB-P03-DER-01");
    author.close(r.modelID);
  });

  it("autora también en IFC4X3 cuando se pide", async () => {
    const r = await author.createSpatial({ ...seed, schema: "IFC4X3" });
    expect(r.ifc).toContain("FILE_SCHEMA(('IFC4X3'))");
    expect(r.schema).toBe("IFC4X3");
    author.close(r.modelID);
  });
});

// Golden de GEORREFERENCIACIÓN (P1·A · decisiones JM 2026-06-27: CRS configurable
// por proyecto, fuente Catastro INSPIRE, edificación primero). Ancla: parcela real
// 0419901DF2901H (Can Cabassa, Sant Cugat) — centroide en ETRS89/UTM 31N obtenido
// de Catastro (OVC Consulta_CPMRC): E=420286.12, N=4591705.32. La IA prepara; JM firma.
const georefSeed: SpatialSeed = {
  ...seed,
  georef: {
    epsg: "EPSG:25831",
    geodeticDatum: "ETRS89",
    mapProjection: "UTM",
    mapZone: "31N",
    eastings: 420286.12,
    northings: 4591705.32,
    orthogonalHeight: 0,
  },
};

describe("IfcAuthor · georreferenciación (IfcProjectedCRS + IfcMapConversion)", () => {
  let author: IfcAuthor;
  let loader: IfcLoader;
  beforeAll(async () => {
    author = new IfcAuthor({ wasmPath: WASM, wasmAbsolute: true });
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await author.init();
    await loader.init();
  });

  it("emite IfcProjectedCRS con el EPSG, datum, proyección y huso de la semilla", async () => {
    const r = await author.createSpatial(georefSeed);
    expect(r.ifc).toContain("IFCPROJECTEDCRS");
    expect(r.ifc).toContain("EPSG:25831");
    expect(r.ifc).toContain("ETRS89");
    expect(r.ifc).toContain("UTM");
    expect(r.ifc).toContain("31N");
    author.close(r.modelID);
  });

  it("emite IfcMapConversion con eastings/northings reales de Catastro", async () => {
    const r = await author.createSpatial(georefSeed);
    expect(r.ifc).toContain("IFCMAPCONVERSION");
    expect(r.ifc).toContain("420286.12");
    expect(r.ifc).toContain("4591705.32");
    author.close(r.modelID);
  });

  it("rotación a Norte real: rotationDeg=0 ⇒ XAxisAbscissa=1, XAxisOrdinate=0", async () => {
    const r = await author.createSpatial(georefSeed);
    const lineMC = r.ifc.split("\n").find((l) => l.includes("IFCMAPCONVERSION"))!;
    // …,OrthogonalHeight,XAxisAbscissa,XAxisOrdinate,Scale) ⇒ termina en 1.,0.,1.
    expect(lineMC).toMatch(/1\.\s*,\s*0\.\s*,\s*1\.\s*\)/);
    author.close(r.modelID);
  });

  it("round-trip: el IfcLoader reabre el IFC georreferenciado sin romper", async () => {
    const r = await author.createSpatial(georefSeed);
    author.close(r.modelID);
    const m = await loader.open({ name: "georref", data: r.ifc });
    expect(m.schema).toBe("IFC4");
    const storeys = await loader.getStoreys(m.modelID);
    expect(storeys.length).toBe(1);
    loader.close(m.modelID);
  });

  it("OPT-IN: sin `georef` NO se emite ninguna entidad de georreferenciación", async () => {
    const r = await author.createSpatial(seed);
    expect(r.ifc).not.toContain("IFCPROJECTEDCRS");
    expect(r.ifc).not.toContain("IFCMAPCONVERSION");
    author.close(r.modelID);
  });
});

// Golden del TERRENO en IFC (P1·A, decisión JM "ambos": preparado para firmar).
// createSpatial con georef + malla triangulada → IfcGeographicElement (TERRAIN) con
// IfcTriangulatedFaceSet georreferenciado. La IA prepara; JM firma (entorno→IFC).
const terrainMesh = gridToMesh({
  nx: 3, ny: 3, originE: 420266.12, originN: 4591685.32, dx: 10, dy: 10,
  heights: [100, 100.4, 100.9, 100.6, 101.1, 101.7, 101.2, 101.9, 102.6],
});

describe("IfcAuthor · terreno (IfcGeographicElement + IfcTriangulatedFaceSet)", () => {
  let author: IfcAuthor;
  let loader: IfcLoader;
  beforeAll(async () => {
    author = new IfcAuthor({ wasmPath: WASM, wasmAbsolute: true });
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await author.init();
    await loader.init();
  });

  it("emite el terreno como IfcGeographicElement TERRAIN teselado", async () => {
    const r = await author.createSpatial({ ...georefSeed, terrain: terrainMesh });
    expect(r.ifc).toContain("IFCGEOGRAPHICELEMENT");
    expect(r.ifc).toContain(".TERRAIN.");
    expect(r.ifc).toContain("IFCTRIANGULATEDFACESET");
    expect(r.ifc).toContain("IFCCARTESIANPOINTLIST3D");
    author.close(r.modelID);
  });

  it("round-trip: el IfcLoader reabre el IFC con terreno sin romper", async () => {
    const r = await author.createSpatial({ ...georefSeed, terrain: terrainMesh });
    author.close(r.modelID);
    const m = await loader.open({ name: "terreno", data: r.ifc });
    expect(m.schema).toBe("IFC4");
    loader.close(m.modelID);
  });

  it("OPT-IN: sin `terrain` NO se emite terreno", async () => {
    const r = await author.createSpatial(georefSeed);
    expect(r.ifc).not.toContain("IFCGEOGRAPHICELEMENT");
    expect(r.ifc).not.toContain("IFCTRIANGULATEDFACESET");
    author.close(r.modelID);
  });
});

// Golden del MODELO DE ESTADO (P1·A, decisión JM 2026-06-27): parcelas + vecinos
// como volúmenes extruidos (IfcExtrudedAreaSolid) en un IFC federado aparte.
const estadoVolumes = [
  { kind: "parcel" as const, name: "0419901DF2901H", height: 0.2, ring: [[420238, 4591627], [420344, 4591682], [420329, 4591783], [420238, 4591627]] },
  { kind: "building" as const, name: "vecino-1", height: 12, ring: [[420337, 4591735], [420359, 4591689], [420344, 4591682], [420337, 4591735]] },
];

describe("IfcAuthor · Modelo de Estado (volúmenes extruidos)", () => {
  let author: IfcAuthor;
  let loader: IfcLoader;
  beforeAll(async () => {
    author = new IfcAuthor({ wasmPath: WASM, wasmAbsolute: true });
    loader = new IfcLoader({ wasmPath: WASM, wasmAbsolute: true });
    await author.init();
    await loader.init();
  });

  it("emite los volúmenes como IfcBuildingElementProxy con IfcExtrudedAreaSolid", async () => {
    const r = await author.createSpatial({ ...georefSeed, volumes: estadoVolumes });
    expect(r.ifc).toContain("IFCBUILDINGELEMENTPROXY");
    expect(r.ifc).toContain("IFCEXTRUDEDAREASOLID");
    expect(r.ifc).toContain("IFCARBITRARYCLOSEDPROFILEDEF");
    author.close(r.modelID);
  });

  it("round-trip: el IfcLoader reabre el Modelo de Estado sin romper", async () => {
    const r = await author.createSpatial({ ...georefSeed, terrain: terrainMesh, volumes: estadoVolumes });
    author.close(r.modelID);
    const m = await loader.open({ name: "estado", data: r.ifc });
    expect(m.schema).toBe("IFC4");
    loader.close(m.modelID);
  });

  it("OPT-IN: sin `volumes` NO se emiten proxies", async () => {
    const r = await author.createSpatial(georefSeed);
    expect(r.ifc).not.toContain("IFCBUILDINGELEMENTPROXY");
    author.close(r.modelID);
  });
});
