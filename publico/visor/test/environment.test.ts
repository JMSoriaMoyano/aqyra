// @vitest-environment node
import { describe, it, expect } from "vitest";
import { readFileSync } from "node:fs";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";
import {
  parseParcels,
  parseBuildings,
  parseRoads,
  toCollection,
  toSnapshot,
  DEFAULT_FLOOR_HEIGHT,
  ENV_CRS,
} from "@aqyra/visor";

// Golden del ENTORNO (P1·A). Parcelas con FIXTURE REAL capturado de Catastro WFS
// (GetNeighbourParcel, Can Cabassa, EPSG:25831). Edificios/viales con fixtures
// sintéticos a la espera del GML real de BU/CartoCiudad. La IA prepara; JM firma.
const here = dirname(fileURLToPath(import.meta.url));
const fx = (n: string) => readFileSync(resolve(here, "fixtures", n), "utf8");
const parcelsGml = fx("catastro_parcels_cancabassa.xml");
const buildingsGml = fx("catastro_buildings_cancabassa.xml");

describe("environment · parseParcels (fixture real Can Cabassa)", () => {
  const fs = parseParcels(parcelsGml);

  it("extrae las 3 parcelas (propia + 2 vecinas)", () => {
    expect(fs.length).toBe(3);
    expect(fs.every((f) => f.properties.kind === "parcel")).toBe(true);
    expect(fs.every((f) => f.properties.source === "catastro-cp")).toBe(true);
  });

  it("lee refcat y área reales", () => {
    const own = fs.find((f) => f.properties.refcat === "0419901DF2901H");
    expect(own).toBeTruthy();
    expect(own!.properties.areaValue).toBe(11884);
    const refs = fs.map((f) => f.properties.refcat).sort();
    expect(refs).toEqual(["0419901DF2901H", "0419902DF2901H", "0419912DF2901H"]);
  });

  it("geometría: polígono con anillo cerrado y coordenadas E-N del 25831", () => {
    const own = fs.find((f) => f.properties.refcat === "0419901DF2901H")!;
    expect(own.geometry.type).toBe("Polygon");
    const ring = (own.geometry as { coordinates: number[][][] }).coordinates[0];
    expect(ring.length).toBe(58);
    expect(ring[0]).toEqual(ring[ring.length - 1]); // cerrado
    const [E, N] = ring[0];
    expect(E).toBeGreaterThan(400000); // easting UTM 31N
    expect(N).toBeGreaterThan(4000000); // northing
  });
});

describe("environment · parseBuildings (fixture real: Building con patios + piscina)", () => {
  const fs = parseBuildings(buildingsGml);
  it("incluye el Building y descarta la OtherConstruction (piscina)", () => {
    expect(fs.length).toBe(1);
    expect(fs[0]!.properties.refcat).toBe("0419901DF2901H");
  });
  it("toma los anillos EXTERIORES (2 PolygonPatch → MultiPolygon), ignora el hueco", () => {
    expect(fs[0]!.geometry.type).toBe("MultiPolygon");
    expect((fs[0]!.geometry as { coordinates: number[][][][] }).coordinates.length).toBe(2);
  });
  it("plantas nil a nivel Building ⇒ sin altura (se toma de BuildingPart)", () => {
    expect(fs[0]!.properties.floorsAbove).toBeUndefined();
    expect(fs[0]!.properties.heightEstimate).toBeUndefined();
  });
});

describe("environment · parseBuildings (BuildingPart con nº de plantas → altura)", () => {
  const partGml = `
  <gml:FeatureCollection xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:bu-ext2d="http://inspire.jrc.ec.europa.eu/schemas/bu-ext2d/2.0" xmlns:base="urn:x-inspire:specification:gmlas:BaseTypes:3.2">
  <gml:featureMember><bu-ext2d:BuildingPart>
    <base:localId>0419901DF2901H_PART.1</base:localId>
    <bu-ext2d:numberOfFloorsAboveGround>4</bu-ext2d:numberOfFloorsAboveGround>
    <gml:Surface><gml:patches><gml:PolygonPatch><gml:exterior><gml:LinearRing>
    <gml:posList srsDimension="2" count="5">420300 4591700 420320 4591700 420320 4591720 420300 4591720 420300 4591700</gml:posList>
    </gml:LinearRing></gml:exterior></gml:PolygonPatch></gml:patches></gml:Surface>
  </bu-ext2d:BuildingPart></gml:featureMember>
  </gml:FeatureCollection>`;

  it("estima altura = plantas × altura tipo (3,0 m por defecto)", () => {
    const fs = parseBuildings(partGml);
    expect(fs.length).toBe(1);
    expect(fs[0]!.properties.floorsAbove).toBe(4);
    expect(fs[0]!.properties.heightEstimate).toBeCloseTo(4 * DEFAULT_FLOOR_HEIGHT, 6);
  });
  it("respeta una altura tipo configurable", () => {
    const fs = parseBuildings(partGml, 3.2);
    expect(fs[0]!.properties.heightEstimate).toBeCloseTo(4 * 3.2, 6);
  });
});

describe("environment · parseRoads", () => {
  const roadGml = `
  <wfs:FeatureCollection xmlns:wfs="http://www.opengis.net/wfs/2.0" xmlns:gml="http://www.opengis.net/gml/3.2" xmlns:tn="x">
  <wfs:member><tn:RoadLink>
    <tn:geometry><gml:LineString>
    <gml:posList srsDimension="2" count="3">420280 4591700 420300 4591710 420320 4591720</gml:posList>
    </gml:LineString></tn:geometry>
  </tn:RoadLink></wfs:member>
  </wfs:FeatureCollection>`;

  it("extrae una polilínea de vial", () => {
    const fs = parseRoads(roadGml);
    expect(fs.length).toBe(1);
    expect(fs[0]!.properties.kind).toBe("road");
    expect(fs[0]!.geometry.type).toBe("LineString");
    expect((fs[0]!.geometry as { coordinates: number[][] }).coordinates.length).toBe(3);
  });
});

describe("environment · snapshot (frontera abierta GeoJSON)", () => {
  it("empaqueta y serializa con el CRS del entorno", () => {
    const fc = toCollection(parseParcels(parcelsGml));
    expect(fc.type).toBe("FeatureCollection");
    expect(fc.crs).toBe(ENV_CRS);
    const json = JSON.parse(toSnapshot(fc));
    expect(json.features.length).toBe(3);
    expect(json.crs).toBe("EPSG:25831");
  });
});
