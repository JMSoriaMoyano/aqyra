import { IfcAPI, Handle } from "web-ifc";
import * as WI from "web-ifc";
import type { IfcSchema } from "./ifc-loader.js";
import type { TerrainMesh } from "./terrain.js";

/**
 * IfcAuthor — AUTORÍA de IFC en el editor (incremento 1: estructura espacial +
 * IfcSpace). Mecanismo HÍBRIDO (decisión de JM, P1·Q2=C): web-ifc CREA y
 * SERIALIZA entidades nativas aquí; las ediciones incrementales diff-able sobre
 * un modelo ya abierto siguen viviendo en `ifc-loader.ts` (`appendStructuralPset`).
 *
 * Formato abierto en la frontera: la salida es texto IFC (STEP), reabrible por el
 * propio `IfcLoader` (round-trip). El editor es el espinazo: este módulo es la
 * base sobre la que crecerán muros, losas, carpintería y MEP del IFC Maestro.
 *
 * P1·B (esbozo, decisión JM: "solo preparar"): el mapeo de la PLANTA TIPO del skin
 * Diseño a IFC. Los espacios pueden llevar `kind` (room/corridor/core → IfcSpace.
 * ObjectType) y agruparse en `zones` (IfcZone privado/comunes vía IfcRelAssignsTo-
 * Group). Todo es OPT-IN: sin `kind`/`zones` la salida es byte-idéntica al incre-
 * mento 1. El cable diálogo→IFC todavía NO se conecta; queda listo para que un
 * incremento posterior lo enchufe con golden delante y firma de JM.
 */

/** Tipo de espacio de la planta tipo (alcance P1·B, decisión JM: 3 tipos). */
export type SpaceKind = "room" | "corridor" | "core";

/** ObjectType IFC por tipo de espacio (texto abierto en la frontera). */
export const SPACE_OBJECT_TYPE: Record<SpaceKind, string> = {
  room: "Habitacion",
  corridor: "Pasillo",
  core: "Nucleo",
};

/** Semilla de un espacio (una habitación, un pasillo, un núcleo…). */
export interface SpaceSeed {
  name: string;
  longName?: string;
  globalId?: string;
  /**
   * Tipo de espacio. Si se da, se vuelca a IfcSpace.ObjectType (P1·B). Si se omite,
   * el espacio se autora como hasta ahora (retrocompatible con el golden incr. 1).
   */
  kind?: SpaceKind;
}

/**
 * Semilla de una zona (IfcZone) que agrupa espacios por su uso (P1·B, decisión JM:
 * IfcZone "habitaciones"/privado vs "comunes"). Los miembros se referencian por el
 * `name` de sus SpaceSeed. Agrupa con IfcRelAssignsToGroup (no IfcRelAggregates).
 */
export interface ZoneSeed {
  name: string;
  longName?: string;
  globalId?: string;
  /** Nombres de los SpaceSeed que pertenecen a esta zona. */
  members: string[];
}

/**
 * Georreferenciación del emplazamiento (P1·A). Sitúa y orienta el modelo en el
 * mundo real: se serializa como entidades IFC REALES (IfcProjectedCRS +
 * IfcMapConversion sobre el contexto geométrico), NO como ayuda visual.
 *
 * Decisiones de JM (2026-06-27): el CRS es CONFIGURABLE por proyecto (sin default
 * del despacho cableado aquí: el `epsg` es siempre obligatorio en la semilla); la
 * fuente del dato real es Catastro INSPIRE (de la ref. catastral → eastings/
 * northings en el CRS elegido). Frontera abierta y diff-able.
 *
 * OPT-IN: sin `georef`, la salida es byte-idéntica al incremento previo y el
 * golden anterior queda intacto.
 */
export interface GeoRef {
  /** Código EPSG del CRS proyectado, configurable por proyecto. P.ej. "EPSG:25831". */
  epsg: string;
  /** Datum geodésico → IfcProjectedCRS.GeodeticDatum. P.ej. "ETRS89". */
  geodeticDatum?: string;
  /** Datum vertical → IfcProjectedCRS.VerticalDatum. P.ej. "EVRF2000". */
  verticalDatum?: string;
  /** Proyección cartográfica → IfcProjectedCRS.MapProjection. P.ej. "UTM". */
  mapProjection?: string;
  /** Huso/zona → IfcProjectedCRS.MapZone. P.ej. "31N". */
  mapZone?: string;
  /** Coordenada Este (m) del origen del modelo en el mapa → IfcMapConversion.Eastings. */
  eastings: number;
  /** Coordenada Norte (m) del origen del modelo en el mapa → IfcMapConversion.Northings. */
  northings: number;
  /** Cota ortométrica (m) del origen → IfcMapConversion.OrthogonalHeight. Por defecto 0. */
  orthogonalHeight?: number;
  /**
   * Rotación a NORTE REAL: ángulo (grados, CCW positivo) del eje +X del proyecto
   * respecto al Este de la cuadrícula del mapa. 0 ⇒ +X→Este, +Y→Norte (modelo
   * alineado con el mapa). Se serializa como XAxisAbscissa=cos(θ), XAxisOrdinate=
   * sin(θ), la convención de IfcMapConversion.
   */
  rotationDeg?: number;
  /** Factor de escala mapa/terreno → IfcMapConversion.Scale. Por defecto 1. */
  scale?: number;
}

/** Tipo de zona funcional (P1·B·2). */
export type ZoneKind = "privado" | "comunes";

/** Espacio dentro de una planta (P1·B·2). */
export interface BuildingSpaceSeed {
  name: string;
  longName?: string;
  kind?: SpaceKind;
  globalId?: string;
}
/** Planta con sus espacios (P1·B·2). */
export interface BuildingStoreySeed {
  name: string;
  longName?: string;
  elevation: number;
  globalId?: string;
  spaces: BuildingSpaceSeed[];
}
/** Zona (IfcZone) por uso, miembros por nombre de espacio (P1·B·2). */
export interface BuildingZoneSeed {
  name: string;
  longName?: string;
  kind?: ZoneKind;
  members: string[];
  globalId?: string;
}
/** Referencia de clasificación bsDD por clase IFC (URI resuelta en vivo por el visor). */
export interface ClassificationRef {
  ifcClass: string;
  uri: string;
  name: string;
}
/**
 * Semilla del MODELO COMPLETO multi-planta (P1·B·2, decisión JM: materializar IFC
 * real). N IfcBuildingStorey, sus IfcSpace tipados, IfcZone por uso, Psets estándar
 * y clasificación bsDD. Es el modelo del árbol del editor serializado a IFC.
 */
export interface BuildingModelSeed {
  schema?: IfcSchema;
  project: { name: string; globalId?: string };
  site: { name: string; longName?: string; globalId?: string };
  building: { name: string; longName?: string; globalId?: string };
  storeys: BuildingStoreySeed[];
  zones?: BuildingZoneSeed[];
  classifications?: ClassificationRef[];
  classificationSource?: { name?: string; source?: string; edition?: string };
}

/**
 * Volumen del Modelo de Estado: un anillo (E,N) extruido en altura. Las parcelas y
 * viales usan una altura pequeña (lámina); los edificios vecinos, su altura real.
 */
export interface SiteVolume {
  /** Anillo exterior [[E,N],…] en el CRS del proyecto (se cierra solo). */
  ring: number[][];
  /** Altura de extrusión (m). */
  height: number;
  /** Naturaleza del volumen (informativa; va al Name del proxy). */
  kind: "parcel" | "building" | "road";
  /** Nombre del elemento (p. ej. refcat). */
  name?: string;
}

/** Semilla de la estructura espacial mínima a autorar. */
export interface SpatialSeed {
  schema?: IfcSchema;
  project: { name: string; globalId?: string };
  site: { name: string; longName?: string; globalId?: string };
  building: { name: string; longName?: string; globalId?: string };
  storey: { name: string; longName?: string; elevation: number; globalId?: string };
  spaces?: SpaceSeed[];
  /**
   * Georreferenciación opcional (P1·A). Si se omite, el modelo "flota en el origen"
   * (0,0,0) como hasta ahora y la salida es idéntica al incremento previo.
   */
  georef?: GeoRef;
  /**
   * Terreno triangulado opcional (P1·A, decisión JM "ambos"). Si se da, se autora un
   * IfcGeographicElement (TERRAIN) con IfcTriangulatedFaceSet georreferenciado (coords
   * localizadas respecto al origen del MapConversion). Opt-in: sin `terrain`, salida
   * idéntica. Volcado a IFC = entorno→IFC (revisita decisión 2): IA prepara, JM firma.
   */
  terrain?: TerrainMesh;
  /**
   * Volúmenes del Modelo de Estado (P1·A, decisión JM 2026-06-27): parcelas, edificios
   * vecinos y viales como sólidos extruidos (IfcExtrudedAreaSolid) sobre IfcBuilding-
   * ElementProxy, georreferenciados (coords locales respecto al origen del MapConversion).
   * Opt-in. Es el contenido del IFC de ESTADO federado (separado del IFC del activo).
   */
  volumes?: SiteVolume[];
  /**
   * Zonas opcionales (IfcZone). Si se omiten, no se autora ninguna IfcZone y el
   * resultado es idéntico al incremento 1. El cable diálogo→IFC NO está conectado
   * todavía: el skin Diseño produce el esquema (acciones `space`) y este mapeo está
   * listo para que un incremento posterior, con golden y firma de JM, lo enchufe.
   */
  zones?: ZoneSeed[];
}

/** Resultado de autorar: IFC serializado (texto) + el modelo web-ifc abierto. */
export interface AuthoredModel {
  ifc: string;
  modelID: number;
  schema: IfcSchema;
}

/** GUID IFC (base64 comprimida, 22 chars). */
function ifcGuid(): string {
  const c = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";
  let g = "";
  for (let i = 0; i < 22; i++) g += c[Math.floor(Math.random() * 64)];
  return g;
}

/** Representación de un valor de enumeración STEP para web-ifc (type=3). */
function enumVal(value: string): { type: number; value: string } {
  return { type: 3, value };
}

/**
 * IfcAuthor — crea modelos IFC nuevos con web-ifc. Mismo patrón de init/wasm que
 * `IfcLoader` para poder compartir el wasm en cliente y en Node (tests headless).
 */
export class IfcAuthor {
  private api = new IfcAPI();
  private ready = false;
  private readonly wasmPath?: string;
  private readonly wasmAbsolute: boolean;

  constructor(opts?: { wasmPath?: string; wasmAbsolute?: boolean }) {
    this.wasmPath = opts?.wasmPath;
    this.wasmAbsolute = opts?.wasmAbsolute ?? false;
  }

  async init(): Promise<void> {
    if (this.ready) return;
    if (this.wasmPath) this.api.SetWasmPath(this.wasmPath, this.wasmAbsolute);
    await this.api.Init();
    this.ready = true;
  }

  /**
   * Crea un modelo nuevo con la estructura espacial (Project → Site → Building →
   * Storey) y los espacios indicados, agregados a la planta (IfcRelAggregates).
   * Devuelve el IFC serializado (texto) y el modelo abierto.
   */
  async createSpatial(seed: SpatialSeed): Promise<AuthoredModel> {
    await this.init();
    const schema: IfcSchema = seed.schema ?? "IFC4";
    const mid = this.api.CreateModel({ schema });

    let nextId = 0;
    const nid = () => ++nextId;
    const api = this.api;
    const label = (s: string) => api.CreateIfcType(mid, WI.IFCLABEL, s);
    const ident = (s: string) => api.CreateIfcType(mid, WI.IFCIDENTIFIER, s);
    const len = (x: number) => api.CreateIfcType(mid, WI.IFCLENGTHMEASURE, x);
    const real = (x: number) => api.CreateIfcType(mid, WI.IFCREAL, x);
    const guid = (s?: string) =>
      api.CreateIfcType(mid, WI.IFCGLOBALLYUNIQUEID, s ?? ifcGuid());
    const ref = (e: { expressID: number }) => new Handle(e.expressID);

    // crea una entidad, le asigna expressID estable y la escribe; la devuelve.
    const write = <T extends { expressID: number }>(
      type: number,
      ...args: unknown[]
    ): T => {
      const e = api.CreateIfcEntity(mid, type, ...args) as unknown as T;
      e.expressID = nid();
      api.WriteLine(mid, e as never);
      return e;
    };

    // --- unidades SI (m, m²) ---
    const metre = write(WI.IFCSIUNIT, enumVal("LENGTHUNIT"), null, enumVal("METRE"));
    const sqm = write(WI.IFCSIUNIT, enumVal("AREAUNIT"), null, enumVal("SQUARE_METRE"));
    const units = write(WI.IFCUNITASSIGNMENT, [ref(metre), ref(sqm)]);

    // --- contexto geométrico ---
    const origin = write(WI.IFCCARTESIANPOINT, [real(0), real(0), real(0)]);
    const axis = write(WI.IFCAXIS2PLACEMENT3D, ref(origin), null, null);
    const ctx = write(
      WI.IFCGEOMETRICREPRESENTATIONCONTEXT,
      null,
      label("Model"),
      api.CreateIfcType(mid, WI.IFCDIMENSIONCOUNT, 3),
      real(1e-5),
      ref(axis),
      null,
    );

    // --- georreferenciación (P1·A): IfcProjectedCRS + IfcMapConversion ---
    // Sitúa y orienta el modelo en el mundo real. El IfcMapConversion enlaza el
    // contexto geométrico (SourceCRS) con el CRS proyectado (TargetCRS) y aporta
    // origen (eastings/northings/cota), rotación a Norte real y escala. Opt-in:
    // sin `seed.georef` no se emite nada y la salida es idéntica al increm. previo.
    // Nota: probado para IFC4; el georref de IfcFacility/IfcAlignment (IFC4X3, obra
    // lineal) llega en un incremento posterior (decisión JM: edificación primero).
    if (seed.georef) {
      const g = seed.georef;
      const projectedCRS = write(
        WI.IFCPROJECTEDCRS,
        label(g.epsg),
        null,
        g.geodeticDatum ? ident(g.geodeticDatum) : null,
        g.verticalDatum ? ident(g.verticalDatum) : null,
        g.mapProjection ? ident(g.mapProjection) : null,
        g.mapZone ? ident(g.mapZone) : null,
        null,
      );
      const rot = ((g.rotationDeg ?? 0) * Math.PI) / 180;
      write(
        WI.IFCMAPCONVERSION,
        ref(ctx),
        ref(projectedCRS),
        len(g.eastings),
        len(g.northings),
        len(g.orthogonalHeight ?? 0),
        real(Math.cos(rot)),
        real(Math.sin(rot)),
        real(g.scale ?? 1),
      );
    }

    // --- proyecto ---
    const project = write(
      WI.IFCPROJECT,
      guid(seed.project.globalId),
      null,
      label(seed.project.name),
      null,
      null,
      null,
      null,
      [ref(ctx)],
      ref(units),
    );

    // --- jerarquía espacial ---
    const site = write(
      WI.IFCSITE,
      guid(seed.site.globalId),
      null,
      label(seed.site.name),
      null,
      null,
      null,
      null,
      seed.site.longName ? label(seed.site.longName) : null,
      enumVal("ELEMENT"),
      null,
      null,
      null,
      null,
      null,
    );
    const building = write(
      WI.IFCBUILDING,
      guid(seed.building.globalId),
      null,
      label(seed.building.name),
      null,
      null,
      null,
      null,
      seed.building.longName ? label(seed.building.longName) : null,
      enumVal("ELEMENT"),
      null,
      null,
      null,
    );
    const storey = write(
      WI.IFCBUILDINGSTOREY,
      guid(seed.storey.globalId),
      null,
      label(seed.storey.name),
      null,
      null,
      null,
      null,
      seed.storey.longName ? label(seed.storey.longName) : null,
      enumVal("ELEMENT"),
      real(seed.storey.elevation),
    );

    // IfcSpace: si la semilla trae `kind`, se vuelca a ObjectType (P1·B). Sin
    // `kind` (golden incr. 1) ObjectType queda null → salida byte-idéntica.
    const spaceByName = new Map<string, { expressID: number }>();
    const spaces = (seed.spaces ?? []).map((s) => {
      const e = write<{ expressID: number }>(
        WI.IFCSPACE,
        guid(s.globalId),
        null,
        label(s.name),
        null,
        s.kind ? label(SPACE_OBJECT_TYPE[s.kind]) : null,
        null,
        null,
        s.longName ? label(s.longName) : null,
        enumVal("ELEMENT"),
        enumVal("INTERNAL"),
        null,
      );
      spaceByName.set(s.name, e);
      return e;
    });

    // --- agregaciones (IfcRelAggregates) ---
    const aggregate = (parent: { expressID: number }, kids: { expressID: number }[]) =>
      write(
        WI.IFCRELAGGREGATES,
        guid(),
        null,
        null,
        null,
        ref(parent),
        kids.map(ref),
      );
    aggregate(project, [site]);
    aggregate(site, [building]);
    aggregate(building, [storey]);
    if (spaces.length > 0) aggregate(storey, spaces);

    // --- zonas (IfcZone) agrupadas con IfcRelAssignsToGroup (P1·B) ---
    // Solo si la semilla aporta zonas; sin ellas no se autora ninguna IfcZone y la
    // salida es idéntica al incremento 1 (golden intacto). IfcZone agrupa por uso
    // (privado/comunes) y es ortogonal a la jerarquía espacial (IfcRelAggregates).
    for (const z of seed.zones ?? []) {
      const members = z.members
        .map((n) => spaceByName.get(n))
        .filter((e): e is { expressID: number } => !!e);
      if (members.length === 0) continue;
      const zone = write(
        WI.IFCZONE,
        guid(z.globalId),
        null,
        label(z.name),
        null,
        null,
        z.longName ? label(z.longName) : null,
      );
      write(
        WI.IFCRELASSIGNSTOGROUP,
        guid(),
        null,
        null,
        null,
        members.map(ref),
        null,
        ref(zone),
      );
    }

    // --- terreno (P1·A): IfcGeographicElement TERRAIN con IfcTriangulatedFaceSet ---
    // Opt-in (decisión JM "ambos"). Coords LOCALIZADAS respecto al origen del
    // MapConversion (eastings/northings/cota) → el terreno cae cerca del origen del
    // proyecto y la georreferencia lo sitúa en el mapa. Sin `terrain` no se emite nada.
    const terr = seed.terrain;
    if (terr && terr.positions.length >= 3 && terr.triangles.length >= 1) {
      const ox = seed.georef?.eastings ?? 0;
      const oy = seed.georef?.northings ?? 0;
      const oz = seed.georef?.orthogonalHeight ?? 0;
      const coordList = terr.positions.map((p) => [len(p[0] - ox), len(p[1] - oy), len(p[2] - oz)]);
      const ptList = write(WI.IFCCARTESIANPOINTLIST3D, coordList, null);
      // CoordIndex de IfcTriangulatedFaceSet es 1-based.
      const posInt = (n: number) => api.CreateIfcType(mid, WI.IFCPOSITIVEINTEGER, n);
      const coordIndex = terr.triangles.map((tr) => [posInt(tr[0] + 1), posInt(tr[1] + 1), posInt(tr[2] + 1)]);
      const tfs = write(WI.IFCTRIANGULATEDFACESET, ref(ptList), null, null, coordIndex, null);
      const shapeRep = write(
        WI.IFCSHAPEREPRESENTATION,
        ref(ctx),
        label("Body"),
        label("Tessellation"),
        [ref(tfs)],
      );
      const prodShape = write(WI.IFCPRODUCTDEFINITIONSHAPE, null, null, [ref(shapeRep)]);
      const placement = write(WI.IFCLOCALPLACEMENT, null, ref(axis));
      const terrainEl = write(
        WI.IFCGEOGRAPHICELEMENT,
        guid(),
        null,
        label("Terreno"),
        null,
        null,
        ref(placement),
        ref(prodShape),
        null,
        enumVal("TERRAIN"),
      );
      write(
        WI.IFCRELCONTAINEDINSPATIALSTRUCTURE,
        guid(),
        null,
        null,
        null,
        [ref(terrainEl)],
        ref(site),
      );
    }

    // --- volúmenes del Modelo de Estado (P1·A): parcelas/vecinos/viales extruidos ---
    // Cada uno es un IfcBuildingElementProxy con IfcExtrudedAreaSolid (perfil = anillo
    // localizado respecto al origen del MapConversion). Opt-in.
    const ox2 = seed.georef?.eastings ?? 0;
    const oy2 = seed.georef?.northings ?? 0;
    for (const v of seed.volumes ?? []) {
      if (!v.ring || v.ring.length < 3) continue;
      const r0 = v.ring[0], rn = v.ring[v.ring.length - 1];
      const ring = r0[0] === rn[0] && r0[1] === rn[1] ? v.ring.slice(0, -1) : v.ring;
      const pts = ring.map((p) =>
        write(WI.IFCCARTESIANPOINT, [real(p[0] - ox2), real(p[1] - oy2)]),
      );
      // IfcPolyline cerrado: repetir el primer punto al final.
      const poly = write(WI.IFCPOLYLINE, [...pts.map(ref), ref(pts[0])]);
      const profile = write(WI.IFCARBITRARYCLOSEDPROFILEDEF, enumVal("AREA"), null, ref(poly));
      const dir = write(WI.IFCDIRECTION, [real(0), real(0), real(1)]);
      const solid = write(
        WI.IFCEXTRUDEDAREASOLID,
        ref(profile),
        ref(axis),
        ref(dir),
        real(Math.max(0.05, v.height)),
      );
      const rep = write(
        WI.IFCSHAPEREPRESENTATION,
        ref(ctx),
        label("Body"),
        label("SweptSolid"),
        [ref(solid)],
      );
      const pds = write(WI.IFCPRODUCTDEFINITIONSHAPE, null, null, [ref(rep)]);
      const placement = write(WI.IFCLOCALPLACEMENT, null, ref(axis));
      const proxy = write(
        WI.IFCBUILDINGELEMENTPROXY,
        guid(),
        null,
        label(v.name ?? v.kind),
        null,
        label(v.kind),
        ref(placement),
        ref(pds),
        null,
        null,
      );
      write(
        WI.IFCRELCONTAINEDINSPATIALSTRUCTURE,
        guid(),
        null,
        null,
        null,
        [ref(proxy)],
        ref(site),
      );
    }

    const bytes = api.SaveModel(mid);
    const ifc = new TextDecoder().decode(bytes);
    return { ifc, modelID: mid, schema };
  }

  /**
   * Autora el MODELO COMPLETO multi-planta (P1·B·2, decisión JM: materializar IFC
   * real). Crea N IfcBuildingStorey, sus IfcSpace tipados (ObjectType), IfcZone por
   * uso (IfcRelAssignsToGroup), Psets estándar (Pset_BuildingStoreyCommon /
   * Pset_SpaceCommon) y clasificación bsDD (IfcClassification + IfcClassification-
   * Reference + IfcRelAssociatesClassification). Es el árbol del editor serializado a
   * IFC, round-trippable por IfcLoader.
   *
   * Cebo: este método produce el MODELO interno (y su round-trip para tests); el visor
   * NO ofrece export firmable — el muro de cobro vive en el anzuelo.
   *
   * DoD: pendiente de golden verde (Llave 1) + firma de JM (Llave 2). La IA prepara.
   */
  async createBuildingModel(seed: BuildingModelSeed): Promise<AuthoredModel> {
    await this.init();
    const schema: IfcSchema = seed.schema ?? "IFC4";
    const mid = this.api.CreateModel({ schema });

    let nextId = 0;
    const nid = () => ++nextId;
    const api = this.api;
    const label = (s: string) => api.CreateIfcType(mid, WI.IFCLABEL, s);
    const ident = (s: string) => api.CreateIfcType(mid, WI.IFCIDENTIFIER, s);
    const real = (x: number) => api.CreateIfcType(mid, WI.IFCREAL, x);
    const uriRef = (s: string) => api.CreateIfcType(mid, WI.IFCURIREFERENCE, s);
    const boolean = (b: boolean) => api.CreateIfcType(mid, WI.IFCBOOLEAN, b);
    const guid = (s?: string) => api.CreateIfcType(mid, WI.IFCGLOBALLYUNIQUEID, s ?? ifcGuid());
    const ref = (e: { expressID: number }) => new Handle(e.expressID);
    const write = <T extends { expressID: number }>(type: number, ...args: unknown[]): T => {
      const e = api.CreateIfcEntity(mid, type, ...args) as unknown as T;
      e.expressID = nid();
      api.WriteLine(mid, e as never);
      return e;
    };

    // índice por clase IFC (para la clasificación bsDD masiva por clase)
    const byClass = new Map<string, { expressID: number }[]>();
    const tag = (cls: string, e: { expressID: number }): void => {
      const a = byClass.get(cls) ?? [];
      a.push(e); byClass.set(cls, a);
    };

    // unidades SI + contexto geométrico (idéntico a createSpatial)
    const metre = write(WI.IFCSIUNIT, enumVal("LENGTHUNIT"), null, enumVal("METRE"));
    const sqm = write(WI.IFCSIUNIT, enumVal("AREAUNIT"), null, enumVal("SQUARE_METRE"));
    const units = write(WI.IFCUNITASSIGNMENT, [ref(metre), ref(sqm)]);
    const origin = write(WI.IFCCARTESIANPOINT, [real(0), real(0), real(0)]);
    const axis = write(WI.IFCAXIS2PLACEMENT3D, ref(origin), null, null);
    const ctx = write(
      WI.IFCGEOMETRICREPRESENTATIONCONTEXT,
      null, label("Model"),
      api.CreateIfcType(mid, WI.IFCDIMENSIONCOUNT, 3), real(1e-5), ref(axis), null,
    );

    const project = write(
      WI.IFCPROJECT, guid(seed.project.globalId), null, label(seed.project.name),
      null, null, null, null, [ref(ctx)], ref(units),
    );
    tag("IfcProject", project);
    const site = write(
      WI.IFCSITE, guid(seed.site.globalId), null, label(seed.site.name),
      null, null, null, null, seed.site.longName ? label(seed.site.longName) : null,
      enumVal("ELEMENT"), null, null, null, null, null,
    );
    tag("IfcSite", site);
    const building = write(
      WI.IFCBUILDING, guid(seed.building.globalId), null, label(seed.building.name),
      null, null, null, null, seed.building.longName ? label(seed.building.longName) : null,
      enumVal("ELEMENT"), null, null, null,
    );
    tag("IfcBuilding", building);

    const aggregate = (parent: { expressID: number }, kids: { expressID: number }[]) =>
      write(WI.IFCRELAGGREGATES, guid(), null, null, null, ref(parent), kids.map(ref));

    // Pset estándar como cualquier objeto del modelo (Pset_*).
    const propSV = (pname: string, value: unknown) =>
      write(WI.IFCPROPERTYSINGLEVALUE, label(pname), null, value, null);
    const pset = (owner: { expressID: number }, psetName: string, props: { expressID: number }[]): void => {
      const ps = write(WI.IFCPROPERTYSET, guid(), null, label(psetName), null, props.map(ref));
      write(WI.IFCRELDEFINESBYPROPERTIES, guid(), null, null, null, [ref(owner)], ref(ps));
    };

    const spaceByName = new Map<string, { expressID: number }>();
    const storeyEnts: { expressID: number }[] = [];

    for (const st of seed.storeys) {
      const storey = write(
        WI.IFCBUILDINGSTOREY, guid(st.globalId), null, label(st.name),
        null, null, null, null, st.longName ? label(st.longName) : null,
        enumVal("ELEMENT"), real(st.elevation),
      );
      tag("IfcBuildingStorey", storey);
      storeyEnts.push(storey);
      pset(storey, "Pset_BuildingStoreyCommon", [propSV("Reference", ident(st.name))]);

      const spaceEnts: { expressID: number }[] = [];
      for (const sp of st.spaces) {
        const objType = sp.kind ? SPACE_OBJECT_TYPE[sp.kind] : undefined;
        const space = write(
          WI.IFCSPACE, guid(sp.globalId), null, label(sp.name),
          null, objType ? label(objType) : null, null, null,
          sp.longName ? label(sp.longName) : null,
          enumVal("ELEMENT"), enumVal("INTERNAL"), null,
        );
        tag("IfcSpace", space);
        spaceByName.set(sp.name, space);
        spaceEnts.push(space);
        pset(space, "Pset_SpaceCommon", [
          propSV("Reference", ident(objType ?? "Space")),
          propSV("IsExternal", boolean(false)),
          propSV("PubliclyAccessible", boolean(sp.kind !== "room")),
        ]);
      }
      if (spaceEnts.length > 0) aggregate(storey, spaceEnts);
    }

    aggregate(project, [site]);
    aggregate(site, [building]);
    if (storeyEnts.length > 0) aggregate(building, storeyEnts);

    // zonas (IfcZone por uso) con IfcRelAssignsToGroup
    for (const z of seed.zones ?? []) {
      const members = z.members
        .map((n) => spaceByName.get(n))
        .filter((e): e is { expressID: number } => !!e);
      if (members.length === 0) continue;
      const zone = write(
        WI.IFCZONE, guid(z.globalId), null, label(z.name), null, null,
        z.longName ? label(z.longName) : null,
      );
      tag("IfcZone", zone);
      write(WI.IFCRELASSIGNSTOGROUP, guid(), null, null, null, members.map(ref), null, ref(zone));
    }

    // clasificación bsDD: una IfcClassification (fuente) + una referencia por clase,
    // asociada a TODOS los objetos de esa clase (URIs resueltas en vivo por el visor).
    if (seed.classifications && seed.classifications.length > 0) {
      const src = seed.classificationSource;
      const classification = write(
        WI.IFCCLASSIFICATION,
        label(src?.source ?? "buildingSMART Data Dictionary (bsDD)"),
        label(src?.edition ?? "IFC 4.3"),
        null,
        label(src?.name ?? "bSDD"),
        null, null, null,
      );
      for (const c of seed.classifications) {
        const objs = byClass.get(c.ifcClass);
        if (!objs || objs.length === 0) continue;
        const reference = write(
          WI.IFCCLASSIFICATIONREFERENCE,
          uriRef(c.uri), ident(c.ifcClass), label(c.name), ref(classification), null, null,
        );
        write(WI.IFCRELASSOCIATESCLASSIFICATION, guid(), null, null, null, objs.map(ref), ref(reference));
      }
    }

    const bytes = api.SaveModel(mid);
    const ifc = new TextDecoder().decode(bytes);
    return { ifc, modelID: mid, schema };
  }

  /** Cierra un modelo autorado para liberar memoria del wasm. */
  close(modelID: number): void {
    this.api.CloseModel(modelID);
  }
}
