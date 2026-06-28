import { IfcAPI } from "web-ifc";
import * as WI from "web-ifc";
import { deriveModel } from "./idealize.js";
import type { DerivedModel, PhysicalElement } from "./idealize.js";

export type IfcSchema = "IFC2X3" | "IFC4" | "IFC4X3";

/** Entrada genérica de un Pset (nombre → valor textual). Diff-able. */
export interface PsetEntry {
  name: string;
  value: string;
}

/** Nombre del anejo Aqyra donde se persisten apoyos/cargas/casos (D-011). */
export const AQYRA_PSET = "Pset_AqyraStructural";

/** GUID IFC (base64 comprimida, 22 chars). */
function ifcGuid(): string {
  const c = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";
  let g = "";
  for (let i = 0; i < 22; i++) g += c[Math.floor(Math.random() * 64)];
  return g;
}

/** Escapa una cadena para un literal STEP (apóstrofo IFC = ''). */
function stepStr(s: string): string {
  return s.replace(/'/g, "''");
}

/**
 * WRITE-BACK client-side SIN re-serializar (D-010): AÑADE el anejo Aqyra como
 * líneas STEP al final del bloque DATA del IFC ORIGINAL, dejando el resto del
 * fichero intacto. Así el diff es MÍNIMO (solo líneas añadidas) y de verdad
 * diff-able — a diferencia de `SaveModel`, que reescribe todo el fichero.
 * Si ya hay un anejo Aqyra, lo retira antes (idempotente).
 */
export function appendStructuralPset(ifcText: string, entries: PsetEntry[]): string {
  const cleaned = stripStructuralPset(ifcText);
  let maxId = 0;
  const re = /#(\d+)\s*=/g;
  let m: RegExpExecArray | null;
  while ((m = re.exec(cleaned)) !== null) maxId = Math.max(maxId, Number(m[1]));
  const proj = /#(\d+)\s*=\s*IFCPROJECT\b/i.exec(cleaned);
  const projId = proj ? Number(proj[1]) : undefined;

  let id = maxId;
  const lines: string[] = [];
  const propIds: number[] = [];
  for (const e of entries) {
    id += 1;
    propIds.push(id);
    lines.push(`#${id}=IFCPROPERTYSINGLEVALUE('${stepStr(e.name)}',$,IFCTEXT('${stepStr(e.value)}'),$);`);
  }
  id += 1;
  const psetId = id;
  lines.push(
    `#${psetId}=IFCPROPERTYSET('${ifcGuid()}',$,'${AQYRA_PSET}','Aqyra · entradas pre-proceso (proposal)',(${propIds.map((p) => `#${p}`).join(",")}));`,
  );
  if (projId !== undefined) {
    id += 1;
    lines.push(`#${id}=IFCRELDEFINESBYPROPERTIES('${ifcGuid()}',$,$,$,(#${projId}),#${psetId});`);
  }

  const block = "\n/* AQYRA-PRE-START (write-back diff-able; no edita el modelo original) */\n" +
    lines.join("\n") +
    "\n/* AQYRA-PRE-END */\n";
  const idx = cleaned.lastIndexOf("ENDSEC;");
  if (idx < 0) return cleaned + block;
  return cleaned.slice(0, idx) + block + cleaned.slice(idx);
}

/** Retira un anejo Aqyra previo (entre los marcadores) para reescritura idempotente. */
export function stripStructuralPset(ifcText: string): string {
  // Sustituye por "" (no "\n"): el match ya incluye el \n que `append` insertó
  // delante del bloque, así que reponer "\n" duplicaría el salto y rompería el
  // round-trip byte a byte (strip(append(x)) === x).
  return ifcText.replace(/\n?\/\* AQYRA-PRE-START[\s\S]*?AQYRA-PRE-END \*\/\n?/g, "");
}

export interface LoadedElement {
  expressId: number;
  ifcType: string;
  globalId: string;
  name?: string;
}

export interface LoadedModel {
  /** id estable del modelo dentro de la federación */
  id: string;
  name: string;
  schema: IfcSchema;
  modelID: number;
  elements: LoadedElement[];
}

export interface PsetRecord {
  globalId: string;
  psets: Record<string, Record<string, unknown>>;
}

export interface SpatialNode {
  expressId: number;
  ifcType: string;
  name?: string;
  globalId?: string;
  children: SpatialNode[];
}

export interface Storey {
  expressId: number;
  name?: string;
  elevation: number;
}

export interface SpatialFix {
  modelID: number;
  expressId: number;
  name?: string;
  ifcType: string;
  fromStorey?: string;
  toStorey: string;
  toStoreyExpressId: number;
}

export interface IfcMeshData {
  expressId: number;
  ifcType: string;
  positions: Float32Array;
  normals: Float32Array;
  indices: Uint32Array;
  color: { r: number; g: number; b: number; a: number };
  /** matriz 4x4 column-major (placement del objeto) */
  matrix: number[];
}

/** Tipos de IfcElement que F1 enumera (renderables/inventariables). Ampliable. */
const ELEMENT_TYPES: ReadonlyArray<string> = [
  "IFCWALL", "IFCWALLSTANDARDCASE", "IFCSLAB", "IFCBEAM", "IFCCOLUMN",
  "IFCDOOR", "IFCWINDOW", "IFCFOOTING", "IFCROOF", "IFCSTAIR", "IFCSTAIRFLIGHT",
  "IFCRAMP", "IFCRAMPFLIGHT", "IFCMEMBER", "IFCPLATE", "IFCCOVERING",
  "IFCCURTAINWALL", "IFCRAILING", "IFCPILE", "IFCBUILDINGELEMENTPROXY",
];

function typeConstants(): Array<{ name: string; code: number }> {
  const reg = WI as unknown as Record<string, number>;
  const out: Array<{ name: string; code: number }> = [];
  for (const t of ELEMENT_TYPES) {
    const code = reg[t];
    if (typeof code === "number") {
      out.push({ name: t, code });
    }
  }
  return out;
}

function typeNameByCode(): Map<number, string> {
  const m = new Map<number, string>();
  for (const { name, code } of typeConstants()) m.set(code, name);
  return m;
}

function toBytes(data: Uint8Array | string): Uint8Array {
  return typeof data === "string" ? new TextEncoder().encode(data) : data;
}

let _seq = 0;

/**
 * IfcLoader — carga IFC con web-ifc (cliente o Node headless). Capa de DATOS:
 * detecta esquema (IFC4 / IFC4.3), enumera elementos y lee Psets. La geometría
 * three.js (render) se construye aparte y solo corre en navegador.
 */
export class IfcLoader {
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

  async open(source: { name: string; data: Uint8Array | string }): Promise<LoadedModel> {
    await this.init();
    const modelID = this.api.OpenModel(toBytes(source.data));
    const schema = this.api.GetModelSchema(modelID) as IfcSchema;
    const elements: LoadedElement[] = [];
    for (const { name: typeName, code } of typeConstants()) {
      const ids = this.api.GetLineIDsWithType(modelID, code);
      for (let i = 0; i < ids.size(); i++) {
        const expressId = ids.get(i);
        const line = this.api.GetLine(modelID, expressId) as {
          GlobalId?: { value?: string };
          Name?: { value?: string };
        };
        const globalId = line.GlobalId?.value;
        if (!globalId) continue;
        elements.push({ expressId, ifcType: typeName, globalId, name: line.Name?.value });
      }
    }
    return { id: `m${++_seq}`, name: source.name, schema, modelID, elements };
  }

  async getProperties(modelID: number, expressId: number, globalId: string): Promise<PsetRecord> {
    await this.init();
    const raw = (await this.api.properties.getPropertySets(modelID, expressId, true)) as Array<{
      Name?: { value?: string };
      HasProperties?: Array<{ Name?: { value?: string }; NominalValue?: { value?: unknown } }>;
    }>;
    const psets: Record<string, Record<string, unknown>> = {};
    for (const ps of raw) {
      const psName = ps.Name?.value ?? "Pset";
      const bag: Record<string, unknown> = {};
      for (const p of ps.HasProperties ?? []) {
        if (p.Name?.value) bag[p.Name.value] = p.NominalValue?.value ?? null;
      }
      psets[psName] = bag;
    }
    return { globalId, psets };
  }

  /** Extrae la geometría teselada (web-ifc) como arrays neutros (sin three.js). */
  getMeshes(modelID: number): IfcMeshData[] {
    const out: IfcMeshData[] = [];
    const names = typeNameByCode();
    this.api.StreamAllMeshes(modelID, (mesh: { expressID: number; geometries: { size(): number; get(i: number): { geometryExpressID: number; color: { x: number; y: number; z: number; w: number }; flatTransformation: number[] } } }) => {
      const gs = mesh.geometries;
      for (let i = 0; i < gs.size(); i++) {
        const pg = gs.get(i);
        const g = this.api.GetGeometry(modelID, pg.geometryExpressID);
        const verts = this.api.GetVertexArray(g.GetVertexData(), g.GetVertexDataSize());
        const idx = this.api.GetIndexArray(g.GetIndexData(), g.GetIndexDataSize());
        const n = verts.length / 6;
        const positions = new Float32Array(n * 3);
        const normals = new Float32Array(n * 3);
        for (let k = 0; k < n; k++) {
          positions[k * 3] = verts[k * 6];
          positions[k * 3 + 1] = verts[k * 6 + 1];
          positions[k * 3 + 2] = verts[k * 6 + 2];
          normals[k * 3] = verts[k * 6 + 3];
          normals[k * 3 + 1] = verts[k * 6 + 4];
          normals[k * 3 + 2] = verts[k * 6 + 5];
        }
        const c = pg.color;
        out.push({
          expressId: mesh.expressID,
          ifcType: names.get(this.api.GetLineType(modelID, mesh.expressID)) ?? "OTROS",
          positions,
          normals,
          indices: new Uint32Array(idx),
          color: { r: c.x, g: c.y, b: c.z, a: c.w },
          matrix: Array.from(pg.flatTransformation),
        });
      }
    });
    return out;
  }

  /** Árbol de estructura espacial: Proyecto > Sitio > Edificio > Planta > elementos. */
  async getSpatialTree(modelID: number): Promise<SpatialNode> {
    await this.init();
    type RawNode = {
      expressID: number;
      type: unknown;
      Name?: { value?: string };
      GlobalId?: { value?: string };
      children?: RawNode[];
    };
    const raw = (await this.api.properties.getSpatialStructure(modelID, true)) as RawNode;
    const norm = (n: RawNode): SpatialNode => ({
      expressId: n.expressID,
      ifcType: String(n.type),
      name: n.Name?.value,
      globalId: n.GlobalId?.value,
      children: (n.children ?? []).map(norm),
    });
    return norm(raw);
  }

  /** GlobalId de un elemento por su expressID (para selección por clic). */
  getGlobalId(modelID: number, expressId: number): string | undefined {
    const line = this.api.GetLine(modelID, expressId) as { GlobalId?: { value?: string } };
    return line.GlobalId?.value;
  }

  /** Plantas (IfcBuildingStorey) con su cota, ordenadas por elevación. */
  async getStoreys(modelID: number): Promise<Storey[]> {
    await this.init();
    const code = (WI as unknown as Record<string, number>)["IFCBUILDINGSTOREY"];
    const ids = this.api.GetLineIDsWithType(modelID, code);
    const out: Storey[] = [];
    for (let i = 0; i < ids.size(); i++) {
      const id = ids.get(i);
      const l = this.api.GetLine(modelID, id) as { Name?: { value?: string }; Elevation?: { value?: number } };
      out.push({ expressId: id, name: l.Name?.value, elevation: l.Elevation?.value ?? 0 });
    }
    out.sort((a, b) => a.elevation - b.elevation);
    return out;
  }

  /** Mapa elemento → contenedor espacial ancestro que cumpla `isContainer` (genérico por métrica). */
  async getElementContainer(modelID: number, isContainer: (up: string) => boolean): Promise<Map<number, number>> {
    const tree = await this.getSpatialTree(modelID);
    const map = new Map<number, number>();
    const isSpatial = (up: string): boolean =>
      up.includes("PROJECT") || up.includes("SITE") || up.includes("STOREY") ||
      up.includes("SPACE") || up.includes("FACILITY") || (up.includes("BUILDING") && !up.includes("STOREY"));
    const walk = (n: SpatialNode, container: number | undefined): void => {
      const up = n.ifcType.toUpperCase();
      const cur = isContainer(up) ? n.expressId : container;
      if (!isSpatial(up) && cur !== undefined) map.set(n.expressId, cur);
      for (const c of n.children) walk(c, cur);
    };
    walk(tree, undefined);
    return map;
  }

  /** Mapa elemento → planta (caso edificación). */
  getElementStorey(modelID: number): Promise<Map<number, number>> {
    return this.getElementContainer(modelID, (up) => up.includes("BUILDINGSTOREY"));
  }

  /** Reasigna elementos a su planta editando IfcRelContainedInSpatialStructure; devuelve el IFC corregido. */
  reassignSpatial(modelID: number, fixes: Array<{ expressId: number; toStorey: number }>): Uint8Array {
    type Handle = { type: number; value: number };
    type Rel = { expressID: number; type: number; RelatingStructure: Handle; RelatedElements: Handle[] };
    const RC = (WI as unknown as Record<string, number>)["IFCRELCONTAINEDINSPATIALSTRUCTURE"];
    const ids = this.api.GetLineIDsWithType(modelID, RC);
    const relByStorey = new Map<number, Rel>();
    const relByElement = new Map<number, Rel>();
    for (let i = 0; i < ids.size(); i++) {
      const rel = this.api.GetLine(modelID, ids.get(i)) as Rel;
      relByStorey.set(rel.RelatingStructure.value, rel);
      for (const e of rel.RelatedElements) relByElement.set(e.value, rel);
    }
    const dirty = new Set<Rel>();
    let nextId = this.api.GetMaxExpressID(modelID);
    const guid = (): string => {
      const c = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz_$";
      let g = "";
      for (let i = 0; i < 22; i++) g += c[Math.floor(Math.random() * 64)];
      return g;
    };
    for (const { expressId, toStorey } of fixes) {
      const cur = relByElement.get(expressId);
      if (cur) {
        cur.RelatedElements = cur.RelatedElements.filter((h) => h.value !== expressId);
        dirty.add(cur);
      }
      let target = relByStorey.get(toStorey);
      if (!target) {
        nextId += 1;
        target = {
          expressID: nextId,
          type: RC,
          RelatingStructure: { type: 5, value: toStorey },
          RelatedElements: [],
        } as unknown as Rel;
        (target as unknown as Record<string, unknown>)["GlobalId"] = { type: 1, name: "IFCGLOBALLYUNIQUEID", value: guid() };
        (target as unknown as Record<string, unknown>)["OwnerHistory"] = null;
        (target as unknown as Record<string, unknown>)["Name"] = null;
        (target as unknown as Record<string, unknown>)["Description"] = null;
        relByStorey.set(toStorey, target);
      }
      target.RelatedElements.push({ type: 5, value: expressId });
      dirty.add(target);
    }
    for (const rel of dirty) this.api.WriteLine(modelID, rel);
    return this.api.SaveModel(modelID);
  }

  // ── Pre-proceso V2: derivación del modelo analítico + anejo Aqyra ─────────────

  /** Vértices EN MUNDO (xyz plano) agregados por expressID, desde la teselación. */
  private worldVertsByElement(modelID: number): Map<number, number[]> {
    const out = new Map<number, number[]>();
    for (const md of this.getMeshes(modelID)) {
      const M = md.matrix; // 4x4 column-major
      const acc = out.get(md.expressId) ?? [];
      const p = md.positions;
      for (let k = 0; k < p.length; k += 3) {
        const x = p[k], y = p[k + 1], z = p[k + 2];
        acc.push(
          M[0] * x + M[4] * y + M[8] * z + M[12],
          M[1] * x + M[5] * y + M[9] * z + M[13],
          M[2] * x + M[6] * y + M[10] * z + M[14],
        );
      }
      out.set(md.expressId, acc);
    }
    return out;
  }

  /** PredefinedType (enum) de un elemento, si lo tiene. */
  private predefinedType(modelID: number, expressId: number): string | undefined {
    try {
      const l = this.api.GetLine(modelID, expressId) as { PredefinedType?: { value?: string } };
      return l.PredefinedType?.value;
    } catch {
      return undefined;
    }
  }

  /**
   * Deriva el modelo analítico (nudos + ejes de barra) del FÍSICO (D-009): no
   * exige `IfcStructuralAnalysisModel` (Decopak HQ no lo trae). Resultado en
   * estado `proposal` aguas arriba; aquí solo la mecánica de derivación.
   */
  async deriveStructural(modelID: number, opts?: { tolerance?: number }): Promise<DerivedModel> {
    await this.init();
    const verts = this.worldVertsByElement(modelID);
    const names = typeNameByCode();
    const elements: PhysicalElement[] = [];
    for (const [expressId, v] of verts) {
      const ifcType = names.get(this.api.GetLineType(modelID, expressId)) ?? "OTROS";
      elements.push({
        expressId,
        globalId: this.getGlobalId(modelID, expressId),
        ifcType,
        predefinedType: this.predefinedType(modelID, expressId),
        verts: v,
      });
    }
    // DIAGNÓSTICO temporal (quitar tras depurar): elementos de superficie de entrada
    // (muros/losas) con su nº de vértices teselados — para ver si web-ifc tesela cada uno.
    const surfIn = elements.filter((e) => /^IFCWALL|^IFCSLAB/.test(e.ifcType.toUpperCase()));
    console.info(`[AQYRA] elementos superficie de entrada: ${surfIn.length}`);
    for (const e of surfIn) console.info(`[AQYRA]   in ${e.ifcType} #${e.expressId} verts=${e.verts.length / 3}`);
    // Geometría real (Revit: brep/recorte/CSG) → lámina por PLANO MEDIO (OBB),
    // robusto frente a la teselación sucia. Ver `surfaceFromBox` en idealize.ts.
    return deriveModel(elements, { tolerance: opts?.tolerance, surfaceMode: "obb" });
  }

  /** Lee el anejo Aqyra (entradas genéricas) de un modelo cargado, para el round-trip. */
  readStructuralPset(modelID: number, psetName: string = AQYRA_PSET): PsetEntry[] {
    const PS = (WI as unknown as Record<string, number>)["IFCPROPERTYSET"];
    const ids = this.api.GetLineIDsWithType(modelID, PS);
    const out: PsetEntry[] = [];
    for (let i = 0; i < ids.size(); i++) {
      const ps = this.api.GetLine(modelID, ids.get(i)) as {
        Name?: { value?: string };
        HasProperties?: Array<{ value?: number }>;
      };
      if (ps.Name?.value !== psetName) continue;
      for (const h of ps.HasProperties ?? []) {
        if (h.value === undefined) continue;
        const p = this.api.GetLine(modelID, h.value) as {
          Name?: { value?: string };
          NominalValue?: { value?: unknown };
        };
        if (p.Name?.value) out.push({ name: p.Name.value, value: String(p.NominalValue?.value ?? "") });
      }
    }
    return out;
  }

  close(modelID: number): void {
    if (this.ready) this.api.CloseModel(modelID);
  }
}
