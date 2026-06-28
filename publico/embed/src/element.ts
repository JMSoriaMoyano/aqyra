import { Viewer, IfcLoader, IfcAuthor, ModelRegistry, appendStructuralPset, stampIfcText } from "@aqyra/visor";
import type { SpatialNode, SpatialFix, Container, DerivedModel, DataState, SpatialSeed } from "@aqyra/visor";
import { elevationMetric, stationMetric } from "@aqyra/visor";
import { BcfAdapter, IdsAdapter, PreAdapter } from "@aqyra/openbim";
import type {
  AqyraViewer,
  Handler,
  IFCSource,
  ModelHandle,
  PsetData,
  RGBA,
  Unsubscribe,
  ViewerEvent,
} from "./contract.js";
import type { BcfApi, IdsApi, PreApi, StructuralProvider, Restraints, Load, SurfaceKind, ResultGroup } from "@aqyra/openbim";

type Vec3 = [number, number, number];
const EMPOTRADO: Restraints = { ux: true, uy: true, uz: true, rx: true, ry: true, rz: true };

/** Config global del cebo: ruta del WASM de web-ifc (host lo sirve estático). */
let config: { wasmPath?: string; wasmAbsolute?: boolean } = {};
export function configureAqyra(cfg: { wasmPath?: string; wasmAbsolute?: boolean }): void {
  config = { ...config, ...cfg };
}

function toBytes(data: ArrayBuffer | string): Uint8Array | string {
  return data instanceof ArrayBuffer ? new Uint8Array(data) : data;
}

/**
 * <aqyra-viewer> — Web Component estándar. F1: carga IFC (4/4.3), federa varios
 * modelos, expone Psets. F2: selección por clic, Psets del elemento y control de
 * visibilidad/color por clase IFC.
 */
export class AqyraViewerElement extends HTMLElement implements AqyraViewer {
  private readonly viewer = new Viewer();
  private readonly registry = new ModelRegistry();
  private loader?: IfcLoader;
  private author?: IfcAuthor;
  private selected: string | null = null;
  private readonly picked = new Map<string, { modelID: number; expressId: number }>();
  private readonly handlers = new Map<ViewerEvent, Set<Handler>>();
  private mounted = false;

  readonly bcf: BcfApi = new BcfAdapter();
  readonly ids: IdsApi = new IdsAdapter();
  readonly pre: PreApi;

  // ── Pre-proceso (V2) ──────────────────────────────────────────────────────
  /** Texto IFC ORIGINAL por modelo (para el write-back por append, diff-able). */
  private readonly sourceText = new Map<number, string>();
  /** Texto IFC con el anejo Aqyra ya escrito (último write-back), para exportar. */
  private readonly writtenText = new Map<number, string>();
  /** Modelo activo del pre-proceso (el primero cargado). */
  private activeModelID?: number;
  /** Modelo analítico derivado cacheado (posiciones de nudos/miembros para glifos). */
  private derived?: DerivedModel;
  /** Handler de clic sobre un núcleo (columna-cajón) — lo cablea la superficie. */
  corePickHandler: ((coreId: string) => void) | null = null;

  constructor() {
    super();
    const provider: StructuralProvider = {
      deriveModel: async () => {
        const modelID = this.activeModelID;
        if (modelID === undefined) throw new Error("[Aqyra] carga un modelo antes de derivar el analítico");
        const dm = await this.getLoader().deriveStructural(modelID);
        this.derived = dm;
        // DIAGNÓSTICO temporal (quitar tras depurar el depósito): qué superficies
        // se derivan realmente del modelo cargado. Filtra por "AQYRA" en la consola.
        console.info(`[AQYRA] superficies derivadas: ${dm.surfaces.length}`);
        for (const s of dm.surfaces) {
          console.info(`[AQYRA]   ${s.id} ${s.kind} ${s.ifcType} n=[${s.normal.map((x) => x.toFixed(2)).join(",")}] t=${s.thickness.toFixed(2)} área=${Math.round(s.area)} grupo=${s.group ?? "-"}`);
        }
        if (this.mounted) {
          const npos = new Map(dm.nodes.map((n) => [n.id, [n.x, n.y, n.z] as Vec3]));
          const segs = dm.members
            .map((m) => ({ a: npos.get(m.nodeStart), b: npos.get(m.nodeEnd) }))
            .filter((s): s is { a: Vec3; b: Vec3 } => !!s.a && !!s.b);
          this.viewer.setIdealization(segs);
          this.viewer.setNodeGlyphs(dm.nodes.map((n) => [n.x, n.y, n.z] as Vec3));
          this.viewer.setSurfaceGlyphs(dm.surfaces);
          this.viewer.ghostPhysical(true); // atenúa el físico para que el idealizado se lea
        }
        return { nodes: dm.nodes, members: dm.members, surfaces: dm.surfaces, cores: dm.cores, coreGroups: dm.coreGroups };
      },
      persist: (entries) => {
        const modelID = this.activeModelID;
        if (modelID === undefined) return;
        const original = this.sourceText.get(modelID);
        if (original === undefined) return; // sin texto fuente (p. ej. cargado por URL): se omite el write-back
        this.writtenText.set(modelID, appendStructuralPset(original, entries));
        if (this.mounted) this.renderAuthored();
      },
    };
    this.pre = new PreAdapter(provider);
  }

  connectedCallback(): void {
    if (this.mounted) return;
    if (!this.style.display) this.style.display = "block";
    this.viewer.mount(this);
    this.viewer.onCorePick = (id) => this.corePickHandler?.(id);
    this.viewer.onPick = (info) => {
      const globalId = this.getLoader().getGlobalId(info.modelID, info.expressId);
      this.selected = globalId ?? null;
      if (globalId) this.picked.set(globalId, { modelID: info.modelID, expressId: info.expressId });
      this.emit("selection-changed", {
        globalId,
        ifcType: info.ifcType,
        modelID: info.modelID,
        expressId: info.expressId,
      });
    };
    this.mounted = true;
  }

  disconnectedCallback(): void {
    this.viewer.dispose();
    this.mounted = false;
  }

  private getLoader(): IfcLoader {
    if (!this.loader) this.loader = new IfcLoader(config);
    return this.loader;
  }

  private getAuthor(): IfcAuthor {
    if (!this.author) this.author = new IfcAuthor(config);
    return this.author;
  }

  /**
   * AUTORÍA (incremento 1, decisión JM P1·Q1=A/Q2=C): crea con web-ifc la
   * estructura espacial (Project→Site→Building→Storey) + los espacios indicados,
   * y carga el IFC resultante en el visor. El editor crea, no solo lee. La salida
   * es texto IFC abierto; el árbol espacial se consulta con `spatialTree()`.
   */
  async createSpatial(seed: SpatialSeed, name = "modelo autorado"): Promise<ModelHandle[]> {
    const { ifc } = await this.getAuthor().createSpatial(seed);
    return this.load([{ name, data: ifc }]);
  }

  /** Carga uno o varios modelos (array ⇒ federación). Todo entra como `proposal`. */
  async load(models: IFCSource | IFCSource[]): Promise<ModelHandle[]> {
    const sources = Array.isArray(models) ? models : [models];
    const loader = this.getLoader();
    const handles: ModelHandle[] = [];
    for (const s of sources) {
      const m = await loader.open({ name: s.name, data: toBytes(s.data) });
      this.registry.add(m);
      if (typeof s.data === "string") this.sourceText.set(m.modelID, s.data);
      else if (s.data instanceof ArrayBuffer) this.sourceText.set(m.modelID, new TextDecoder().decode(new Uint8Array(s.data)));
      this.activeModelID ??= m.modelID;
      if (this.mounted) this.viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
      handles.push({ id: m.id, name: m.name, state: "proposal" });
    }
    this.emit("model-loaded", handles);
    return handles;
  }

  select(globalId: string): void {
    const hit = this.registry.findByGlobalId(globalId);
    if (!hit) throw new Error(`[Aqyra] sin elemento con GlobalId ${globalId}`);
    if (this.selected === globalId) return;
    this.selected = globalId;
    this.emit("selection-changed", { globalId });
  }

  async getProperties(globalId: string): Promise<PsetData> {
    const hit = this.registry.findByGlobalId(globalId);
    const loc = hit ? { modelID: hit.model.modelID, expressId: hit.expressId } : this.picked.get(globalId);
    if (!loc) throw new Error(`[Aqyra] sin elemento con GlobalId ${globalId}`);
    return this.getLoader().getProperties(loc.modelID, loc.expressId, globalId);
  }

  setVisibilityByClass(ifcClass: string, visible: boolean): void {
    this.viewer.setVisibilityByClass(ifcClass, visible);
  }
  setColorByClass(ifcClass: string, color: RGBA): void {
    this.viewer.setColorByClass(ifcClass, color);
  }

  /** Clases IFC presentes (helper de UI; no forma parte del contrato). */
  classes(): Array<{ ifcType: string; count: number }> {
    return this.viewer.classes();
  }

  /** Helpers de UI (no forman parte del contrato). */
  showAll(): void {
    this.viewer.showAll();
  }
  resetColors(): void {
    this.viewer.resetColors();
  }

  /** Árbol espacial por modelo federado (helper de UI). */
  async spatialTree(): Promise<Array<{ name: string; modelID: number; root: SpatialNode }>> {
    const loader = this.getLoader();
    const out: Array<{ name: string; modelID: number; root: SpatialNode }> = [];
    for (const m of this.registry.list()) {
      out.push({ name: m.name, modelID: m.modelID, root: await loader.getSpatialTree(m.modelID) });
    }
    return out;
  }

  isolateByExpressIds(modelID: number, ids: number[]): void {
    this.viewer.isolateByExpressIds(modelID, new Set(ids));
  }

  private containerFor(p: number, containers: Container[]): Container {
    let chosen = containers[0]!;
    for (const c of containers) {
      if (p >= c.key - 1e-6) chosen = c;
      else break;
    }
    return chosen;
  }

  /** Propone reasignar elementos a su contenedor correcto por la MÉTRICA elegida.
   * `kind="cota"` (edificación) o `kind="estacion"` (infraestructura, IfcAlignment). */
  async proposeSpatialFix(kind: "cota" | "estacion" = "cota"): Promise<SpatialFix[]> {
    const metric = kind === "estacion" ? stationMetric : elevationMetric;
    const loader = this.getLoader();
    const out: SpatialFix[] = [];
    for (const model of this.registry.list()) {
      const containers = (await metric.containers(loader, model.modelID)).slice().sort((a, b) => a.key - b.key);
      if (containers.length < 2) continue;
      const pos = metric.positions(this.viewer, model.modelID);
      const current = await metric.currentContainer(loader, model.modelID);
      const types = this.viewer.elementTypes(model.modelID);
      const nameById = new Map(containers.map((c) => [c.expressId, c.name ?? `pos ${c.key}`]));
      const elemByGid = new Map(model.elements.map((e) => [e.expressId, e]));
      for (const [expressId, p] of pos) {
        const cur = current.get(expressId);
        if (cur === undefined) continue;
        const target = this.containerFor(p, containers);
        if (target.expressId === cur) continue;
        out.push({
          modelID: model.modelID,
          expressId,
          name: elemByGid.get(expressId)?.name,
          ifcType: types.get(expressId) ?? "OTROS",
          fromStorey: nameById.get(cur),
          toStorey: target.name ?? `pos ${target.key}`,
          toStoreyExpressId: target.expressId,
        });
      }
    }
    return out;
  }

  /** Aplica el saneamiento: reescribe el IFC, recarga el modelo corregido y devuelve los bytes para descargar. */
  async applySpatialFix(fixes: SpatialFix[]): Promise<Array<{ name: string; bytes: Uint8Array }>> {
    const loader = this.getLoader();
    const byModel = new Map<number, SpatialFix[]>();
    for (const f of fixes) {
      const a = byModel.get(f.modelID) ?? [];
      a.push(f);
      byModel.set(f.modelID, a);
    }
    const results: Array<{ name: string; bytes: Uint8Array }> = [];
    for (const [modelID, fs] of byModel) {
      const old = this.registry.list().find((m) => m.modelID === modelID);
      const name = old?.name ?? "modelo";
      const bytes = loader.reassignSpatial(modelID, fs.map((f) => ({ expressId: f.expressId, toStorey: f.toStoreyExpressId })));
      this.viewer.removeModel(modelID);
      if (old) this.registry.remove(old.id);
      const nm = await loader.open({ name, data: bytes });
      this.registry.add(nm);
      if (this.mounted) this.viewer.addIfcModel(nm.modelID, loader.getMeshes(nm.modelID));
      results.push({ name, bytes });
    }
    return results;
  }

  /** Consulta simple (Opción 4): cuántos elementos de una clase, opcionalmente en una planta. */
  async countByClass(ifcClass: string, storeyQuery?: string): Promise<number> {
    const loader = this.getLoader();
    let count = 0;
    for (const model of this.registry.list()) {
      const types = this.viewer.elementTypes(model.modelID);
      const cls = ifcClass.toUpperCase();
      let storeyName: Map<number, string> | undefined;
      let elStorey: Map<number, number> | undefined;
      if (storeyQuery) {
        const storeys = await loader.getStoreys(model.modelID);
        storeyName = new Map(storeys.map((s) => [s.expressId, (s.name ?? "").toLowerCase()]));
        elStorey = await loader.getElementStorey(model.modelID);
      }
      for (const [eid, t] of types) {
        if (t.toUpperCase() !== cls) continue;
        if (storeyQuery && elStorey && storeyName) {
          const sn = storeyName.get(elStorey.get(eid) ?? -1) ?? "";
          if (!sn.includes(storeyQuery.toLowerCase())) continue;
        }
        count += 1;
      }
    }
    return count;
  }

  // ── Helpers de pre-proceso para la superficie (no son del contrato) ──────────

  /** Deriva y pinta el modelo IDEALIZADO (proposal). Devuelve un resumen revisable. */
  async showStructural(): Promise<{ nodes: number; members: number; surfaces: number; surfacesNonPlanar: number; surfacesThick: number; surfacesSkewed: number; coresClosed: number; coresOpen: number }> {
    const model = await this.pre.getStructuralModel();
    const nonPlanar = model.surfaces.filter((s) => s.planar === false).length;
    const thick = model.surfaces.filter((s) => s.thick).length;
    const skewed = model.surfaces.filter((s) => s.skewed).length;
    const coresClosed = model.coreGroups.filter((g) => g.closed).length;
    const coresOpen = model.coreGroups.filter((g) => !g.closed).length;
    return { nodes: model.nodes.length, members: model.members.length, surfaces: model.surfaces.length, surfacesNonPlanar: nonPlanar, surfacesThick: thick, surfacesSkewed: skewed, coresClosed, coresOpen };
  }

  private refreshSurfaces(): void {
    if (this.mounted) this.viewer.setSurfaceGlyphs(this.pre.listSurfaces());
  }

  /** Pinta las columnas-cajón equivalentes de los núcleos y devuelve sus propiedades. */
  showCores(): Array<{ id: string; A: number; Agross: number; hollow: boolean; Ix: number; Iy: number; J: number; thickness: number }> {
    const cores = this.pre.listCores();
    if (this.mounted) this.viewer.setCoreGlyphs(cores);
    return cores.map((c) => ({ id: c.id, A: c.A, Agross: c.Agross, hollow: c.hollow, Ix: c.Ix, Iy: c.Iy, J: c.J, thickness: c.thickness }));
  }

  /** Pinta las 4 láminas COSIDAS de los núcleos reconocidos por caras. */
  showCoreShells(): { closed: number; open: number } {
    const groups = this.pre.listCoreGroups();
    if (this.mounted) this.viewer.setCoreShellGlyphs(groups);
    return { closed: groups.filter((g) => g.closed).length, open: groups.filter((g) => !g.closed).length };
  }

  /** Cambia la idealización de todas las superficies de un tipo IFC (p. ej. IFCWALL→lámina). */
  setSurfaceKindByType(ifcPrefix: string, kind: SurfaceKind): number {
    let count = 0;
    for (const s of this.pre.listSurfaces()) {
      if (s.ifcType.toUpperCase().startsWith(ifcPrefix.toUpperCase())) {
        this.pre.setSurfaceKind(s.id, kind);
        count += 1;
      }
    }
    this.refreshSurfaces();
    return count;
  }

  /** Cambia la idealización de la superficie del elemento seleccionado. */
  setSurfaceKindForSelection(kind: SurfaceKind): boolean {
    if (!this.selected) return false;
    const s = this.pre.listSurfaces().find((x) => x.ifcGlobalId === this.selected);
    if (!s) return false;
    this.pre.setSurfaceKind(s.id, kind);
    this.refreshSurfaces();
    return true;
  }

  /** Miembro idealizado que corresponde al elemento físico seleccionado (por GlobalId). */
  memberOfSelection(): { id: string; nodeStart: string; nodeEnd: string } | undefined {
    if (!this.selected || !this.derived) return undefined;
    return this.derived.members.find((m) => m.ifcGlobalId === this.selected);
  }

  /** Autora un apoyo empotrado en un nudo (por defecto, el extremo inferior del miembro seleccionado). */
  setSupportAtNode(nodeId: string, restraints: Restraints = EMPOTRADO): void {
    this.pre.setSupport(nodeId, restraints);
  }

  /** Extremo inferior (menor cota Z, frame Z-up D-018) del miembro: nudo natural de apoyo de pilote/zapata. */
  baseNodeOf(memberId: string): string | undefined {
    const m = this.derived?.members.find((x) => x.id === memberId);
    if (!m || !this.derived) return undefined;
    const a = this.derived.nodes.find((n) => n.id === m.nodeStart);
    const b = this.derived.nodes.find((n) => n.id === m.nodeEnd);
    if (!a || !b) return undefined;
    return a.z <= b.z ? a.id : b.id;
  }

  /** Autora una carga distribuida sobre un miembro (kN·m⁻¹). Devuelve su id. */
  addDistributedLoad(memberId: string, value: number, direction: "x" | "y" | "z" = "z", caseId = "Q"): string {
    return this.pre.addLoad({ kind: "distributed", target: memberId, value, direction, case: caseId } as Omit<Load, "id" | "state">);
  }

  /** Repinta los glifos de apoyos/cargas autorados a partir del modelo derivado cacheado. */
  private renderAuthored(): void {
    if (!this.derived) return;
    const npos = new Map(this.derived.nodes.map((n) => [n.id, [n.x, n.y, n.z] as Vec3]));
    const mids = new Map(
      this.derived.members.map((m) => {
        const a = npos.get(m.nodeStart);
        const b = npos.get(m.nodeEnd);
        const mid: Vec3 = a && b ? [(a[0] + b[0]) / 2, (a[1] + b[1]) / 2, (a[2] + b[2]) / 2] : [0, 0, 0];
        return [m.id, mid];
      }),
    );
    // Frame global Z-up (D-018): la GRAVEDAD actúa según −Z. El default (carga
    // vertical sin dirección explícita, o eje "z") apunta hacia −Z, no −Y.
    const dirVec = (d?: "x" | "y" | "z"): Vec3 => (d === "x" ? [1, 0, 0] : d === "y" ? [0, 1, 0] : [0, 0, -1]);
    this.viewer.setSupportGlyphs(this.pre.listSupports().map((s) => npos.get(s.nodeId)).filter((p): p is Vec3 => !!p));
    this.viewer.setLoadGlyphs(
      this.pre.listLoads().map((l) => {
        const at = l.kind === "distributed" ? mids.get(l.target) : npos.get(l.target);
        return { at: at ?? ([0, 0, 0] as Vec3), dir: dirVec(l.direction) };
      }),
    );
  }

  // ── Post-proceso (V3): render de resultados sobre el modelo (D-022) ──────────

  /** Rampa de aprovechamiento: 0→verde, ~0.9→ámbar, >1→rojo. */
  private static utilizationColor(u: number): [number, number, number] {
    if (u > 1) return [0.9, 0.18, 0.18]; // NO cumple → rojo
    if (u > 0.9) return [0.96, 0.62, 0.1]; // al límite → ámbar
    if (u > 0.6) return [0.95, 0.85, 0.2]; // medio → amarillo
    return [0.2, 0.78, 0.34]; // holgado → verde
  }

  /**
   * Pinta un `ResultGroup` sobre el modelo: DEFORMADA (nudos desplazados) coloreada
   * por APROVECHAMIENTO, con su estado de dato (chip + marca, D-021). El verde de
   * «certificado» SOLO aparece si `rg.state==="verified-signed"` (lo acuña la firma).
   * Devuelve los elementos «al límite» (>0.9) y los que «no cumplen» (>1).
   */
  showResultGroup(rg: ResultGroup, opts: { scale?: number } = {}): { critical: string[]; notPassing: string[] } {
    if (!this.derived) throw new Error("[Aqyra] deriva el modelo analítico antes de pintar resultados");
    const base = new Map(this.derived.nodes.map((n) => [n.id, [n.x, n.y, n.z] as Vec3]));
    const disp = new Map(rg.nodes.map((n) => [n.nodeId, [n.ux, n.uy, n.uz] as Vec3]));
    const util = new Map(rg.members.map((m) => [m.memberId, m]));

    // Escala automática: la flecha máxima ≈ 5% de la diagonal del modelo.
    let maxD = 0;
    for (const d of disp.values()) maxD = Math.max(maxD, Math.hypot(d[0], d[1], d[2]));
    let diag = 1;
    {
      const xs = this.derived.nodes;
      if (xs.length) {
        const minv: Vec3 = [Infinity, Infinity, Infinity];
        const maxv: Vec3 = [-Infinity, -Infinity, -Infinity];
        for (const n of xs) {
          minv[0] = Math.min(minv[0], n.x); maxv[0] = Math.max(maxv[0], n.x);
          minv[1] = Math.min(minv[1], n.y); maxv[1] = Math.max(maxv[1], n.y);
          minv[2] = Math.min(minv[2], n.z); maxv[2] = Math.max(maxv[2], n.z);
        }
        diag = Math.hypot(maxv[0] - minv[0], maxv[1] - minv[1], maxv[2] - minv[2]) || 1;
      }
    }
    const scale = opts.scale ?? (maxD > 0 ? (0.05 * diag) / maxD : 1);

    const moved = (id: string): Vec3 | undefined => {
      const b = base.get(id);
      if (!b) return undefined;
      const d = disp.get(id) ?? [0, 0, 0];
      return [b[0] + d[0] * scale, b[1] + d[1] * scale, b[2] + d[2] * scale];
    };

    const segments: Array<{ a: Vec3; b: Vec3; color: [number, number, number] }> = [];
    for (const m of this.derived.members) {
      const a = moved(m.nodeStart);
      const b = moved(m.nodeEnd);
      if (!a || !b) continue;
      const mr = util.get(m.id);
      const color = mr ? AqyraViewerElement.utilizationColor(mr.utilization) : ([0.6, 0.6, 0.6] as [number, number, number]);
      segments.push({ a, b, color });
    }
    if (this.mounted) {
      this.viewer.setDeformed(segments);
      this.viewer.ghostPhysical(true);
      this.viewer.setDataState(rg.state); // chip + marca de agua según estado (D-021)
    }
    return {
      critical: rg.members.filter((m) => m.utilization > 0.9).map((m) => m.memberId),
      notPassing: rg.members.filter((m) => !m.passes || m.utilization > 1).map((m) => m.memberId),
    };
  }

  /** Limpia la deformada y restaura el físico. */
  clearResults(): void {
    if (!this.mounted) return;
    this.viewer.clearDeformed();
    this.viewer.ghostPhysical(false);
    this.viewer.setDataState(null);
  }

  // ── Estado de dato (D-021): el visor muestra el estado; nunca lo mina ─────────

  /** Fija el estado de dato del resultado a la vista (`null` = sin resultado).
   * El verde (`verified-signed`) solo debe acuñarlo el flujo de firma de `privado/`. */
  setDataState(state: DataState | null): void {
    this.viewer.setDataState(state);
  }

  /** Estado de dato del resultado a la vista. */
  dataState(): DataState | null {
    return this.viewer.getDataState();
  }

  /** IFC con el anejo Aqyra ya escrito (write-back), listo para descargar/reabrir.
   * GUARDA DE EXPORTACIÓN (D-021·C.2): si el dato NO está firmado, el texto sale
   * estampado «NO VERIFICADO» para que no circule como certificado. */
  exportStructuralIfc(): { name: string; bytes: Uint8Array } | undefined {
    if (this.activeModelID === undefined) return undefined;
    const text = this.writtenText.get(this.activeModelID);
    if (text === undefined) return undefined;
    const name = this.registry.list().find((m) => m.modelID === this.activeModelID)?.name ?? "modelo";
    // El anejo autorado es `proposal` salvo que un resultado firmado esté activo.
    const state: DataState = this.viewer.getDataState() ?? "proposal";
    return { name, bytes: new TextEncoder().encode(stampIfcText(text, state)) };
  }

  on(event: ViewerEvent, cb: Handler): Unsubscribe {
    let set = this.handlers.get(event);
    if (!set) {
      set = new Set();
      this.handlers.set(event, set);
    }
    set.add(cb);
    return () => set.delete(cb);
  }

  private emit(event: ViewerEvent, payload: unknown): void {
    this.handlers.get(event)?.forEach((cb) => cb(payload));
  }

  /** Diagnóstico (no forma parte del contrato): nº de mallas renderizadas. */
  debugMeshCount(): number {
    return this.viewer.meshCount();
  }
}

export const TAG = "aqyra-viewer";

export function defineAqyraViewer(): void {
  if (!customElements.get(TAG)) {
    customElements.define(TAG, AqyraViewerElement);
  }
}
