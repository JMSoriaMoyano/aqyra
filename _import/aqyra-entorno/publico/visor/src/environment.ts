/**
 * Reconstrucción del ENTORNO (P1·A) — proveedor de geodato público.
 *
 * Decisiones de JM (2026-06-27): backbone estatal (Catastro + CartoCiudad) con
 * ICGC como plugin futuro; el entorno es CONTEXTO VISUAL (no se autora al IFC del
 * activo); altura de vecinos por nº de plantas de Catastro × altura tipo (3,0 m
 * por defecto, configurable); flujo híbrido (explorar en vivo + congelar snapshot
 * GeoJSON versionado/diff-able); solo fuentes oficiales CC-BY/abiertas.
 *
 * Módulo PURO en su núcleo (parser GML→GeoJSON sin dependencias, con golden); la
 * parte de red usa un PROXY server-side (`/__aqyra/geo`) que resuelve CORS y el
 * que el `web_fetch`/navegador no surfacea el GML de Catastro. La frontera abierta
 * es GeoJSON normalizado en EPSG:25831 (coherente con la georreferencia).
 *
 * Alcance v0 del parser: geometrías basadas en `gml:posList` (polígonos de parcela
 * y huella de edificio; polilíneas de vial). Los huecos (anillos interiores) y los
 * arcos `gml:Curve` se tratan de forma simplificada — suficiente para contexto
 * visual; se endurece en incrementos posteriores con golden delante.
 */

export const DEFAULT_FLOOR_HEIGHT = 3.0;
export const ENV_CRS = "EPSG:25831";

export type EnvKind = "parcel" | "building" | "road";

export interface EnvProps {
  kind: EnvKind;
  /** Origen del dato: "catastro-cp" | "catastro-bu" | "cartociudad". */
  source: string;
  /** Referencia catastral (parcelas/edificios) o id de origen. */
  refcat?: string;
  /** Superficie en m² (parcelas). */
  areaValue?: number;
  /** Nº de plantas sobre rasante (edificios, Catastro BuildingPart). */
  floorsAbove?: number;
  /** Altura estimada (m) = floorsAbove × altura tipo (edificios). */
  heightEstimate?: number;
  /** Nombre del vial (CartoCiudad), si está. */
  roadName?: string;
}

export type Geom =
  | { type: "Polygon"; coordinates: number[][][] }
  | { type: "MultiPolygon"; coordinates: number[][][][] }
  | { type: "LineString"; coordinates: number[][] }
  | { type: "MultiLineString"; coordinates: number[][][] };

export interface EnvFeature {
  type: "Feature";
  properties: EnvProps;
  geometry: Geom;
}

export interface EnvFeatureCollection {
  type: "FeatureCollection";
  /** CRS del snapshot (frontera abierta). */
  crs: string;
  features: EnvFeature[];
}

// ── helpers de parseo (sin dependencias; regex sobre el GML de los WFS) ──────────
// Soporta los dos envoltorios reales: `wfs:member` (CP, WFS 2.0) y
// `gml:featureMember` (BU/IGN, GML 3.2).
function members(gml: string): string[] {
  return gml
    .split(/<(?:\w+:)?(?:featureMember|member)\b[^>]*>/)
    .slice(1)
    .map((s) => s.split(/<\/(?:\w+:)?(?:featureMember|member)>/)[0]);
}

function first(seg: string, re: RegExp): string | undefined {
  const m = seg.match(re);
  return m ? m[1].trim() : undefined;
}

function ringFromPosList(text: string): number[][] {
  const nums = text.trim().split(/\s+/).map(Number).filter((n) => Number.isFinite(n));
  const ring: number[][] = [];
  for (let i = 0; i + 1 < nums.length; i += 2) ring.push([nums[i], nums[i + 1]]);
  return ring;
}

/** Anillos EXTERIORES (uno por `gml:exterior`) → [[E,N],…]. Ignora huecos interiores
 *  (patios) — suficiente para contexto visual. Soporta múltiples PolygonPatch. */
function exteriorRings(seg: string): number[][][] {
  const rings: number[][][] = [];
  for (const ex of seg.matchAll(/<gml:exterior>([\s\S]*?)<\/gml:exterior>/g)) {
    const pm = ex[1].match(/<gml:posList[^>]*>([\s\S]*?)<\/gml:posList>/);
    if (!pm) continue;
    const ring = ringFromPosList(pm[1]);
    if (ring.length > 0) rings.push(ring);
  }
  return rings;
}

/** Todas las `gml:posList` de un fragmento → polilíneas [[E,N],…] (viales). */
function posLists(seg: string): number[][][] {
  const rings: number[][][] = [];
  for (const m of seg.matchAll(/<gml:posList[^>]*>([\s\S]*?)<\/gml:posList>/g)) {
    const ring = ringFromPosList(m[1]);
    if (ring.length > 0) rings.push(ring);
  }
  return rings;
}

function polygonGeom(rings: number[][][]): Geom {
  // v0: cada posList = un polígono (exterior). Multi → MultiPolygon.
  return rings.length === 1
    ? { type: "Polygon", coordinates: [rings[0]] }
    : { type: "MultiPolygon", coordinates: rings.map((r) => [r]) };
}

/** Parsea parcelas catastrales (WFS CP) → features con refcat y área. */
export function parseParcels(gml: string): EnvFeature[] {
  const out: EnvFeature[] = [];
  for (const seg of members(gml)) {
    if (!/CadastralParcel/.test(seg)) continue;
    const rings = exteriorRings(seg);
    if (rings.length === 0) continue;
    const refcat = first(seg, /<cp:nationalCadastralReference>([^<]+)/);
    const area = first(seg, /<cp:areaValue[^>]*>([\d.]+)/);
    out.push({
      type: "Feature",
      properties: {
        kind: "parcel",
        source: "catastro-cp",
        refcat,
        areaValue: area ? Number(area) : undefined,
      },
      geometry: polygonGeom(rings),
    });
  }
  return out;
}

/**
 * Parsea edificios/partes (WFS BU) → huellas con nº de plantas y altura estimada.
 * floorHeight: altura tipo por planta (m). Si una parte no declara plantas, queda
 * sin `heightEstimate` (el render le da una altura mínima de contexto).
 */
export function parseBuildings(gml: string, floorHeight = DEFAULT_FLOOR_HEIGHT): EnvFeature[] {
  const out: EnvFeature[] = [];
  for (const seg of members(gml)) {
    // Solo Building / BuildingPart; se ignoran OtherConstruction (piscinas, etc.).
    if (!/:(Building|BuildingPart)\b/.test(seg)) continue;
    const rings = exteriorRings(seg);
    if (rings.length === 0) continue;
    // nº plantas: poblado en BuildingPart; en Building suele venir nil (sin dígito).
    const fm = seg.match(/numberOfFloorsAboveGround[^>]*>(\d+)</);
    const floors = fm ? Number(fm[1]) : undefined;
    const refcat = first(seg, /<base:localId>([^<]+)/) ?? first(seg, /localId>([^<]+)/);
    out.push({
      type: "Feature",
      properties: {
        kind: "building",
        source: "catastro-bu",
        refcat,
        floorsAbove: floors,
        heightEstimate: floors !== undefined ? floors * floorHeight : undefined,
      },
      geometry: polygonGeom(rings),
    });
  }
  return out;
}

/** Parsea viales (CartoCiudad / INSPIRE tn-ro:RoadLink) → polilíneas con nombre. */
export function parseRoads(gml: string): EnvFeature[] {
  const out: EnvFeature[] = [];
  for (const seg of members(gml)) {
    const rings = posLists(seg);
    if (rings.length === 0) continue;
    const name =
      first(seg, /<tn:[^>]*[Nn]ame[^>]*>([^<]+)/) ?? first(seg, /[Nn]ombre>([^<]+)/);
    const geometry: Geom =
      rings.length === 1
        ? { type: "LineString", coordinates: rings[0] }
        : { type: "MultiLineString", coordinates: rings };
    out.push({
      type: "Feature",
      properties: { kind: "road", source: "cartociudad", roadName: name },
      geometry,
    });
  }
  return out;
}

/** Empaqueta features en una FeatureCollection normalizada (frontera abierta). */
export function toCollection(features: EnvFeature[]): EnvFeatureCollection {
  return { type: "FeatureCollection", crs: ENV_CRS, features };
}

/** Serializa el snapshot del entorno (GeoJSON, diff-able) para congelar por proyecto. */
export function toSnapshot(fc: EnvFeatureCollection): string {
  return JSON.stringify(fc, null, 2);
}

// ── proveedor estatal (cliente): construye las URLs del proxy `/__aqyra/geo` ─────
// El proxy reenvía a Catastro/CartoCiudad (CORS + el GML no se surfacea directo).
export interface EnvProvider {
  parcels(refcat: string): Promise<EnvFeature[]>;
  buildings(refcat: string): Promise<EnvFeature[]>;
  roads(bbox: [number, number, number, number]): Promise<EnvFeature[]>;
}

export interface StateProviderOpts {
  /** Base del proxy. Por defecto el endpoint del dev server. */
  proxyBase?: string;
  floorHeight?: number;
  srs?: string;
  fetchFn?: typeof fetch;
}

/** Proveedor estatal: Catastro (parcelas/edificios) + CartoCiudad (viales) vía proxy. */
export class StateEnvProvider implements EnvProvider {
  private base: string;
  private floorHeight: number;
  private srs: string;
  private f: typeof fetch;
  constructor(o: StateProviderOpts = {}) {
    this.base = o.proxyBase ?? "/__aqyra/geo";
    this.floorHeight = o.floorHeight ?? DEFAULT_FLOOR_HEIGHT;
    this.srs = o.srs ?? "EPSG::25831";
    this.f = o.fetchFn ?? fetch;
  }
  private async text(params: Record<string, string>): Promise<string> {
    const q = new URLSearchParams(params).toString();
    const r = await this.f(`${this.base}?${q}`);
    return r.text();
  }
  async parcels(refcat: string): Promise<EnvFeature[]> {
    return parseParcels(await this.text({ src: "cp-neighbour", refcat, srs: this.srs }));
  }
  async buildings(refcat: string): Promise<EnvFeature[]> {
    return parseBuildings(await this.text({ src: "bu-all", refcat, srs: this.srs }), this.floorHeight);
  }
  async roads(bbox: [number, number, number, number]): Promise<EnvFeature[]> {
    return parseRoads(await this.text({ src: "roads", bbox: bbox.join(","), srs: this.srs }));
  }
}
