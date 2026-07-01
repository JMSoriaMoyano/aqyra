// Adaptadores OpenBIM — superficie pública (cebo). En F0 solo el contrato y
// stubs; la implementación se apoya en @thatopen/components: BCFTopics (F3),
// IDSSpecifications (F4). El criterio que el copiloto recupera NO vive aquí
// (eso es privado/): aquí solo el transporte estándar abierto.

export interface Topic {
  guid: string;
  title: string;
}
export interface NewTopic {
  title: string;
  description?: string;
}
export interface IdsSpec {
  name: string;
}
export interface IdsReport {
  passed: boolean;
  checks: Array<{ requirement: string; passed: boolean }>;
}

export interface BcfApi {
  list(): Topic[];
  create(topic: NewTopic): Topic;
  exportZip(): Blob;
  importZip(zip: Blob): void;
}
export interface IdsApi {
  loadSpec(xml: string): IdsSpec;
  validate(): IdsReport;
}

const later = (what: string): Error =>
  new Error(`[Aqyra/openbim] "${what}" llega en una fase posterior (BCF→F3, IDS→F4, pre→primer corte V2).`);

/** Adaptador BCF sobre @thatopen/components BCFTopics (cableado en F3). */
export class BcfAdapter implements BcfApi {
  list(): Topic[] {
    return [];
  }
  create(_topic: NewTopic): Topic {
    throw later("bcf.create");
  }
  exportZip(): Blob {
    throw later("bcf.exportZip");
  }
  importZip(_zip: Blob): void {
    throw later("bcf.importZip");
  }
}

/** Adaptador IDS sobre @thatopen/components IDSSpecifications (cableado en F4). */
export class IdsAdapter implements IdsApi {
  loadSpec(_xml: string): IdsSpec {
    throw later("ids.loadSpec");
  }
  validate(): IdsReport {
    throw later("ids.validate");
  }
}

// ── Pre-proceso estructural (V2) ──────────────────────────────────────────────
// Superficie de la sub-API `pre` (decisión D-012). Datos en estado `proposal`:
// el modelo analítico se DERIVA del físico (D-009) y los apoyos/cargas se
// AUTORAN (D-011) — nunca son resultados verificados. El CRITERIO (qué cargas
// tocan según norma/corpus) es anzuelo (privado/), NO vive aquí: aquí solo la
// mecánica abierta (leer/derivar geometría, autorar, persistir como texto).

/**
 * Estado de dato del pre/post-proceso (espeja `DataState` del contrato). Las DOS
 * LLAVES, explícitas (D-021): `proposal` (input autorado/derivado, editable) y
 * `computed` (el motor calculó, 0 llaves) no son verdad; `qa-passed` lleva la 1.ª
 * llave (QA independiente PyNite, D-023); `verified-signed` la 2.ª (firma de JM).
 * En pantalla la frontera es BINARIA: solo `verified-signed` recibe el trato
 * «certificado». Mapeo ISO 19650: S0 / S0 / S3 / A. El verde solo lo acuña el
 * flujo de firma de `privado/`; el render público nunca lo produce.
 */
export type PreDataState = "proposal" | "computed" | "qa-passed" | "verified-signed";

/** Nudo idealizado del modelo analítico. */
export interface StructuralNode {
  id: string;
  x: number;
  y: number;
  z: number;
}

/**
 * Ejes locales de barra por ROL, nunca por letra (D-018). El adaptador C5
 * (`privado/`) traduce `strong`/`weak` a las letras de PyNite (z/y) y del
 * Eurocódigo (y-y/z-z). `axis` = longitudinal i→j.
 */
export type LocalAxis = "axis" | "strong" | "weak";

/**
 * Propiedades NUMÉRICAS de sección resueltas en el lado Aqyra (D-019·C.1.a): el
 * modelo analítico llega al motor con los números listos; el motor no necesita el
 * catálogo de Aqyra. Ejes por rol (D-018): `I_strong` = mayor inercia.
 * Unidades SI del proyecto: A en m², I/J en m⁴.
 */
export interface SectionProps {
  A: number; // área (m²)
  I_strong: number; // inercia de eje fuerte / mayor (m⁴)
  I_weak: number; // inercia de eje débil / menor (m⁴)
  J: number; // constante de torsión (m⁴)
  Av_strong?: number; // área de cortante en plano fuerte (m²)
  Av_weak?: number; // área de cortante en plano débil (m²)
  // Módulos resistentes (m³) para la comprobación EC3 (D-022). Por rol; opcionales:
  // si faltan, el checker omite la flexión y lo advierte.
  Wel_strong?: number; // módulo elástico eje fuerte
  Wpl_strong?: number; // módulo plástico eje fuerte (clase 1/2)
  Wel_weak?: number; // módulo elástico eje débil
  Wpl_weak?: number; // módulo plástico eje débil
}

/**
 * Propiedades NUMÉRICAS de material resueltas en el lado Aqyra (D-019·C.1.a).
 * Unidades: E/G y fy_or_fck en kN/m²; density (peso específico) en kN/m³.
 */
export interface MaterialProps {
  E: number; // módulo de elasticidad (kN/m²)
  G: number; // módulo de cortante (kN/m²)
  density: number; // peso específico (kN/m³)
  fy_or_fck: number; // límite elástico (acero) o resistencia característica (hormigón) (kN/m²)
}

/** Sección/material de un miembro idealizado (del `…ProfileDef` del físico). */
export interface SectionRef {
  profile: string;
  material?: string;
  /** Propiedades numéricas de sección resueltas en Aqyra para el motor (D-019·C.1.a). */
  props?: SectionProps;
  /** Propiedades numéricas de material resueltas en Aqyra para el motor (D-019·C.1.a). */
  materialProps?: MaterialProps;
}

/**
 * Liberación de extremo de barra (D-020), 6 GdL en ejes locales por ROL (D-018),
 * **true = GdL LIBERADO** (polaridad invertida frente a `Restraints`, true =
 * restringido). El adaptador C5 invierte al traducir a `def_releases` de PyNite.
 * Rótula estándar = liberar `mStrong` + `mWeak` (los dos flectores).
 * Regla de estabilidad (PyNite): no liberar `axial` ni `torsion` en AMBOS extremos.
 */
export interface MemberEndRelease {
  axial: boolean; // libera N (eje axis)
  vStrong: boolean; // libera cortante en plano fuerte
  vWeak: boolean; // libera cortante en plano débil
  torsion: boolean; // libera momento torsor T
  mStrong: boolean; // libera flector de eje fuerte (pin estándar)
  mWeak: boolean; // libera flector de eje débil (pin estándar)
}

/** Releases por extremo i (nudo inicial) y j (nudo final). Ausente = nudo RÍGIDO. */
export interface MemberReleases {
  i?: MemberEndRelease;
  j?: MemberEndRelease;
}

/**
 * RESERVADO V3 (no usado): rigidez rotacional por GdL para SEMIRRÍGIDO (resortes
 * de nudo), por extremo. El `AppliedCondition` de IFC lo admite; V3 solo
 * implementa el release booleano. La clasificación de nudos EC3 es criterio → V4.
 */
export interface MemberStiffness {
  i?: Partial<Record<keyof MemberEndRelease, number>>;
  j?: Partial<Record<keyof MemberEndRelease, number>>;
}

/** Miembro idealizado (eje derivado del físico; D-009). */
export interface StructuralMember {
  id: string;
  kind: "beam" | "column" | "brace" | "chord" | "post" | "member" | "slab" | "wall" | "other";
  nodeStart: string;
  nodeEnd: string;
  section?: SectionRef;
  /** Liberaciones de extremo (D-020). Ausente = nudo rígido (transmite N/V/M/T). */
  releases?: MemberReleases;
  /** Reservado (semirrígido); no usado en V3. */
  stiffness?: MemberStiffness;
  /** Trazabilidad al elemento físico del IFC. */
  ifcGlobalId?: string;
}

/** Coacciones de un apoyo (6 GdL; true = restringido). */
export interface Restraints {
  ux: boolean;
  uy: boolean;
  uz: boolean;
  rx: boolean;
  ry: boolean;
  rz: boolean;
}

/** Apoyo autorado sobre un nudo (D-011). */
export interface Support {
  id: string;
  nodeId: string;
  restraints: Restraints;
  state: PreDataState;
}

export type LoadKind = "point" | "distributed";

/** Carga autorada (puntual en nudo o distribuida en miembro). Valor en kN / kN·m⁻¹. */
export interface Load {
  id: string;
  kind: LoadKind;
  /** id de nudo (puntual) o de miembro (distribuida). */
  target: string;
  value: number;
  direction?: "x" | "y" | "z";
  /** id del caso de carga al que pertenece. */
  case?: string;
  state: PreDataState;
}

/** Caso de carga (naturaleza según EC0/EC1). */
export interface LoadCase {
  id: string;
  name: string;
  nature: "permanent" | "use" | "wind" | "snow" | "seismic" | "thermal";
}

/**
 * Combinación de acciones. `terms` es el mapa estructurado `{caso: factor}` que
 * consume el motor (≅ `IfcRelAssignsToGroupByFactor`; D-019·C.2.a): el motor NO
 * parsea texto. `expression` se conserva SOLO para mostrar. El criterio normativo
 * de qué combinar/qué γ-ψ aplicar es anzuelo → V4; aquí solo el contenedor.
 */
export interface Combination {
  id: string;
  name: string;
  limitState: "ULS" | "SLS" | "seismic";
  /** Mapa {caseId: factor} — lo que resuelve el motor. */
  terms: Record<string, number>;
  /** Expresión legible (p. ej. «1.35·G + 1.50·Q»), solo para mostrar. */
  expression: string;
}

/** Idealización de una superficie (losa→diafragma, muro→lámina). Editable. */
export type SurfaceKind = "diaphragm" | "shell";

/**
 * Carga por área sobre una superficie (D-019·C.3.a, ≅ Indicación A): q (kN/m²)
 * sobre el ÁREA REAL de la planta. El adaptador C5 la reparte por área tributaria
 * real a vigas de borde o nudos (separando diafragma-rigidez de superficie-carga).
 * Autorada → `state: proposal`.
 */
export interface SurfaceAreaLoad {
  /** carga superficial (kN/m²). */
  q: number;
  /** caso de carga al que pertenece. */
  case?: string;
  /** objetivo de reparto: vigas de borde o nudos por área tributaria. */
  distributeTo?: "edges" | "nodes";
}

/** Superficie idealizada (losa/muro), PROPUESTA revisable. La geometría se DERIVA
 * del físico; lo AUTORADO es el `kind` (diafragma/lámina). La precisión FE de la
 * lámina la calcula el motor (V3). */
export interface StructuralSurface {
  id: string;
  kind: SurfaceKind;
  ifcType: string;
  ifcGlobalId?: string;
  outline: Array<[number, number, number]>;
  center: [number, number, number];
  normal: [number, number, number];
  mesh?: { nodes: Array<[number, number, number]>; quads: Array<[number, number, number, number]> };
  /** área REAL de la planta (m²) que reparte carga; NO la extensión del diafragma (Indicación A). */
  area?: number;
  /** área del rectángulo envolvente (m²) — extensión dibujada. */
  extentArea?: number;
  /** false = caja/núcleo no-plano: no idealizar como una sola lámina (Indicación B). */
  planar?: boolean;
  /** espesor estimado (m). */
  thickness?: number;
  /** true = GRUESO (t/luz alto): lámina delgada no aplica → sólido/placa gruesa (Indicación C). */
  thick?: boolean;
  /** true = plano TORCIDO (muro ladeado de la vertical): artefacto de derivación a revisar (Indicación C). */
  skewed?: boolean;
  /** id del grupo-núcleo si la cara forma parte de un núcleo (caras unidas por esquinas). */
  group?: string;
  /** true si ese grupo-núcleo es una caja cerrada. */
  groupClosed?: boolean;
  /** carga por área autorada (kN/m²) sobre el área real (D-019·C.3.a). */
  areaLoad?: SurfaceAreaLoad;
  state?: PreDataState;
}

/** Grupo de caras planas que forman un NÚCLEO (unidas por esquinas). El cosido FE
 * de los nudos de esquina lo realiza el motor (V3); aquí se RECONOCE el grupo. */
export interface StructuralCoreGroup {
  id: string;
  members: string[];
  closed: boolean;
  /** malla shell unificada de las caras, COSIDA en las esquinas (4 láminas conectadas). */
  mesh?: { nodes: Array<[number, number, number]>; quads: Array<[number, number, number, number]> };
  state?: PreDataState;
}

/** Columna-cajón equivalente de un núcleo (alternativa a las 4 láminas). Propiedades
 * BRUTAS + J de Bredt: PROPUESTA para comparar; la precisión la da el motor (V3). */
export interface StructuralCore {
  id: string;
  ifcType: string;
  ifcGlobalId?: string;
  axis: { a: [number, number, number]; b: [number, number, number] };
  sectionOutline: Array<[number, number, number]>;
  A: number; // sección considerada (hueca si se pudo) (m²)
  Agross: number; // sección bruta exterior (m²)
  hollow: boolean; // true ⇒ A/Ix/Iy son de la sección HUECA
  Awall: number;
  Ix: number;
  Iy: number;
  J: number;
  perimeter: number;
  thickness: number;
  state?: PreDataState;
}

/** Modelo analítico idealizado completo, en estado `proposal`. */
export interface StructuralModel {
  nodes: StructuralNode[];
  members: StructuralMember[];
  surfaces: StructuralSurface[];
  cores: StructuralCore[];
  coreGroups: StructuralCoreGroup[];
  supports: Support[];
  loads: Load[];
  state: PreDataState;
}

// ── Esquema de RESULTADOS del contrato C5 (salida pública; D-019·B.3) ──────────
// Tipos PÚBLICOS que el visor consume para pintar; el ADAPTADOR que los produce
// (motor FEM, traducción rol→PyNite→EC, QA) es PRIVADO (anzuelo). Convenio de
// signos D-018: N>0 = TRACCIÓN; V/M/T canónicos de PyNite; ejes locales por ROL
// (`strong`/`weak`), nunca por letra. Cada grupo nace `computed` (0 llaves) y
// solo el flujo de firma de `privado/` lo lleva a `verified-signed`.

/**
 * Estación a lo largo de una barra (x de i→j, en m) con sus esfuerzos y la
 * deformada local. Signos D-018: N>0 tracción; momentos/cortantes por rol.
 */
export interface MemberStation {
  x: number; // posición a lo largo del eje, 0..L (m)
  N: number; // axil (kN); N>0 = tracción
  V_strong: number; // cortante en plano fuerte (kN)
  V_weak: number; // cortante en plano débil (kN)
  M_strong: number; // flector de eje fuerte (kN·m)
  M_weak: number; // flector de eje débil (kN·m)
  T: number; // torsor (kN·m)
  dx: number; // deformada local axial (m)
  dy: number; // deformada local en plano fuerte (m)
  dz: number; // deformada local en plano débil (m)
}

/** Resultado por barra: esfuerzos por estación + aprovechamiento + «qué no cumple». */
export interface MemberResult {
  memberId: string;
  stations: MemberStation[];
  /** aprovechamiento (ratio de comprobación); > 1 = NO cumple. */
  utilization: number;
  /** comprobación gobernante (texto descriptivo), p. ej. «pandeo eje fuerte». */
  governing?: string;
  /** utilization ≤ 1. */
  passes: boolean;
}

/** Reacción en un apoyo (componentes globales) ≅ `IfcStructuralReaction` (D-018). */
export interface NodeReaction {
  fx: number;
  fy: number;
  fz: number;
  mx: number;
  my: number;
  mz: number;
}

/** Resultado por nudo: desplazamientos globales (6 GdL) y, en apoyos, reacciones. */
export interface NodeResult {
  nodeId: string;
  ux: number; // desplazamiento global X (m)
  uy: number; // desplazamiento global Y (m)
  uz: number; // desplazamiento global Z (m); vertical (D-018, Z-up)
  rx: number; // giro global X (rad)
  ry: number; // giro global Y (rad)
  rz: number; // giro global Z (rad)
  /** presente solo en nudos con apoyo. */
  reaction?: NodeReaction;
}

/** Resultado por lámina/núcleo: esfuerzos de membrana y de placa por metro (plano local). */
export interface SurfaceResult {
  surfaceId: string;
  /** esfuerzos de membrana por metro (kN/m). */
  membrane: { nx: number; ny: number; nxy: number };
  /** esfuerzos de placa por metro (kN·m/m). */
  plate: { mx: number; my: number; mxy: number };
}

/**
 * Grupo de resultados de UNA combinación (≅ `IfcStructuralResultGroup`,
 * `ResultGroupFor` → modelo de análisis). Nace `computed`; el estado lo eleva el
 * flujo de dos llaves (D-021/D-023). El visor pinta según `state`.
 */
export interface ResultGroup {
  id: string;
  combinationId: string;
  state: PreDataState; // nace "computed"
  members: MemberResult[];
  nodes: NodeResult[];
  surfaces: SurfaceResult[];
}

/** Entrada de envolvente: extremo de aprovechamiento + combinación gobernante. */
export interface EnvelopeEntry {
  memberId: string;
  maxUtilization: number;
  /** id de la combinación que gobierna (PyNite lo da por `combo_tags`). */
  governingCombination: string;
  passes: boolean;
}

/** Envolvente sobre un conjunto de combinaciones (max/min + combinación gobernante). */
export interface ResultEnvelope {
  id: string;
  combinationIds: string[];
  state: PreDataState;
  entries: EnvelopeEntry[];
}

/**
 * Sub-API de pre-proceso (solo lectura del contrato; las mutaciones autoran
 * entradas `proposal`). El write-back se persiste client-side con web-ifc como
 * Pset Aqyra diff-able (D-010/D-011).
 */
export interface PreApi {
  /** Modelo analítico idealizado: derivado del físico (D-009) o leído si la entrada trae dominio de análisis. */
  getStructuralModel(): Promise<StructuralModel>;
  listSupports(): Support[];
  setSupport(nodeId: string, restraints: Restraints): Support;
  listLoads(): Load[];
  addLoad(load: Omit<Load, "id" | "state">): string;
  removeLoad(id: string): void;
  listLoadCases(): LoadCase[];
  listCombinations(): Combination[];
  listSurfaces(): StructuralSurface[];
  /** Cambia la idealización de una superficie (diafragma↔lámina). Decisión del ingeniero. */
  setSurfaceKind(id: string, kind: SurfaceKind): void;
  /** Autora una carga por área (kN/m²) sobre una superficie (D-019·C.3.a); `null` la retira. */
  setSurfaceAreaLoad(id: string, areaLoad: SurfaceAreaLoad | null): void;
  /** Releases autorados por barra (D-020). */
  listReleases(): Array<{ memberId: string; releases: MemberReleases }>;
  /** Libera/empotra un extremo (i|j) de una barra (D-020); `null` lo deja rígido. */
  setRelease(memberId: string, end: "i" | "j", release: MemberEndRelease | null): void;
  /** Columnas-cajón equivalentes de los núcleos no-planos (alternativa para comparar). */
  listCores(): StructuralCore[];
  /** Núcleos reconocidos como grupos de caras (cajas cerradas / U abiertas). */
  listCoreGroups(): StructuralCoreGroup[];
}

/**
 * Proveedor de geometría/persistencia que inyecta el host (el Web Component):
 * DERIVA el modelo analítico del físico (web-ifc, D-009) y PERSISTE el anejo
 * Aqyra como texto diff-able (D-010). Mantiene `openbim` desacoplado de `visor`.
 */
export interface StructuralProvider {
  deriveModel(): Promise<{ nodes: StructuralNode[]; members: StructuralMember[]; surfaces: StructuralSurface[]; cores: StructuralCore[]; coreGroups: StructuralCoreGroup[] }>;
  persist(entries: Array<{ name: string; value: string }>): void;
}

// ── Codificación diff-able del anejo (clave=valor;…) ───────────────────────────
type KV = Record<string, string | number | boolean>;
const enc = (o: KV): string =>
  Object.entries(o)
    .map(([k, v]) => `${k}=${String(v).replace(/[;]/g, ",")}`)
    .join(";");

const b = (x: boolean): number => (x ? 1 : 0);

/**
 * Adaptador de pre-proceso (PRIMER CORTE V2). Deriva el analítico vía el
 * `StructuralProvider` (D-009) y AUTORA apoyos/cargas como entradas `proposal`
 * (D-011) — nunca resultados verificados (dos llaves). El write-back se delega
 * al proveedor como anejo diff-able (D-010). El CRITERIO normativo (qué
 * combinaciones/γ/ψ tocan) NO vive aquí: es anzuelo (privado/, V4); aquí solo
 * contenedores editables y la EXPRESIÓN genérica como propuesta.
 */
export class PreAdapter implements PreApi {
  private readonly provider?: StructuralProvider;
  private supports: Support[] = [];
  private loads: Load[] = [];
  private surfaces: StructuralSurface[] = [];
  private cores: StructuralCore[] = [];
  private coreGroups: StructuralCoreGroup[] = [];
  private readonly surfaceKind = new Map<string, SurfaceKind>(); // overrides del ingeniero
  private readonly surfaceAreaLoad = new Map<string, SurfaceAreaLoad>(); // carga por área autorada (D-019·C.3.a)
  private readonly releases = new Map<string, MemberReleases>(); // releases autorados por barra (D-020)
  private cases: LoadCase[];
  private combinations: Combination[];
  private seq = 0;

  constructor(provider?: StructuralProvider) {
    this.provider = provider;
    // Contenedores genéricos (mecánica abierta): un caso permanente y uno
    // variable de uso. La SELECCIÓN normativa de casos es criterio → privado/.
    this.cases = [
      { id: "G", name: "Permanente", nature: "permanent" },
      { id: "Q", name: "Uso", nature: "use" },
    ];
    // Combinación ELU genérica EDITABLE: `terms` es el mapa {caso: factor} que
    // consume el motor (D-019·C.2.a); `expression` solo se muestra. Qué γ/ψ y qué
    // combinaciones aplican por norma es criterio → privado/, V4.
    this.combinations = [
      { id: "ELU1", name: "ELU (genérica, editable)", limitState: "ULS", terms: { G: 1.35, Q: 1.5 }, expression: "1.35·G + 1.50·Q" },
    ];
  }

  async getStructuralModel(): Promise<StructuralModel> {
    if (!this.provider) throw later("pre.getStructuralModel");
    const { nodes, members, surfaces, cores, coreGroups } = await this.provider.deriveModel();
    // Aplica los overrides del ingeniero sobre lo derivado: idealización (kind),
    // carga por área (D-019·C.3.a) y releases de extremo (D-020).
    this.surfaces = surfaces.map((s) => ({
      ...s,
      kind: this.surfaceKind.get(s.id) ?? s.kind,
      areaLoad: this.surfaceAreaLoad.get(s.id) ?? s.areaLoad,
      state: "proposal" as PreDataState,
    }));
    const membersWithReleases = members.map((m) => {
      const r = this.releases.get(m.id);
      return r ? { ...m, releases: r } : m;
    });
    this.cores = cores.map((c) => ({ ...c, state: "proposal" as PreDataState }));
    this.coreGroups = coreGroups.map((g) => ({ ...g, state: "proposal" as PreDataState }));
    return { nodes, members: membersWithReleases, surfaces: this.surfaces, cores: this.cores, coreGroups: this.coreGroups, supports: this.supports, loads: this.loads, state: "proposal" };
  }

  listSurfaces(): StructuralSurface[] {
    return this.surfaces;
  }
  listCores(): StructuralCore[] {
    return this.cores;
  }
  listCoreGroups(): StructuralCoreGroup[] {
    return this.coreGroups;
  }
  setSurfaceKind(id: string, kind: SurfaceKind): void {
    this.surfaceKind.set(id, kind);
    this.surfaces = this.surfaces.map((s) => (s.id === id ? { ...s, kind } : s));
    this.persist();
  }

  setSurfaceAreaLoad(id: string, areaLoad: SurfaceAreaLoad | null): void {
    if (areaLoad === null) this.surfaceAreaLoad.delete(id);
    else this.surfaceAreaLoad.set(id, areaLoad);
    this.surfaces = this.surfaces.map((s) => (s.id === id ? { ...s, areaLoad: areaLoad ?? undefined } : s));
    this.persist();
  }

  listReleases(): Array<{ memberId: string; releases: MemberReleases }> {
    return [...this.releases.entries()].map(([memberId, releases]) => ({ memberId, releases }));
  }

  setRelease(memberId: string, end: "i" | "j", release: MemberEndRelease | null): void {
    const current: MemberReleases = { ...(this.releases.get(memberId) ?? {}) };
    if (release === null) delete current[end];
    else current[end] = release;
    if (current.i === undefined && current.j === undefined) this.releases.delete(memberId);
    else this.releases.set(memberId, current);
    this.persist();
  }

  listSupports(): Support[] {
    return this.supports;
  }
  setSupport(nodeId: string, restraints: Restraints): Support {
    const support: Support = { id: `S${++this.seq}`, nodeId, restraints, state: "proposal" };
    this.supports = this.supports.filter((s) => s.nodeId !== nodeId).concat(support);
    this.persist();
    return support;
  }

  listLoads(): Load[] {
    return this.loads;
  }
  addLoad(load: Omit<Load, "id" | "state">): string {
    const id = `L${++this.seq}`;
    this.loads.push({ ...load, id, state: "proposal" });
    this.persist();
    return id;
  }
  removeLoad(id: string): void {
    this.loads = this.loads.filter((l) => l.id !== id);
    this.persist();
  }

  listLoadCases(): LoadCase[] {
    return this.cases;
  }
  listCombinations(): Combination[] {
    return this.combinations;
  }

  /** Serializa el estado autorado al anejo diff-able y lo persiste vía proveedor. */
  private persist(): void {
    if (!this.provider) return;
    const entries: Array<{ name: string; value: string }> = [];
    for (const s of this.supports) {
      const r = s.restraints;
      entries.push({
        name: `support:${s.id}`,
        value: enc({ node: s.nodeId, ux: b(r.ux), uy: b(r.uy), uz: b(r.uz), rx: b(r.rx), ry: b(r.ry), rz: b(r.rz), state: s.state }),
      });
    }
    for (const l of this.loads) {
      entries.push({
        name: `load:${l.id}`,
        value: enc({ kind: l.kind, target: l.target, value: l.value, dir: l.direction ?? "z", case: l.case ?? "", state: l.state }),
      });
    }
    // Releases de extremo (D-020), true=liberado; el adaptador C5 invierte la
    // polaridad al traducir a `def_releases` de PyNite (D-018).
    for (const [memberId, r] of this.releases) {
      const flags = (e?: MemberEndRelease): string =>
        e ? `${b(e.axial)}${b(e.vStrong)}${b(e.vWeak)}${b(e.torsion)}${b(e.mStrong)}${b(e.mWeak)}` : "------";
      entries.push({ name: `release:${memberId}`, value: enc({ i: flags(r.i), j: flags(r.j) }) });
    }
    // Solo persistimos la DECISIÓN (kind + carga por área) por superficie; la geometría se re-deriva.
    for (const sf of this.surfaces) {
      const kv: KV = { kind: sf.kind, ifc: sf.ifcType };
      if (sf.areaLoad) {
        kv.q = sf.areaLoad.q;
        kv.qcase = sf.areaLoad.case ?? "";
        kv.qto = sf.areaLoad.distributeTo ?? "";
      }
      entries.push({ name: `surface:${sf.id}`, value: enc(kv) });
    }
    for (const c of this.cases) entries.push({ name: `case:${c.id}`, value: enc({ name: c.name, nature: c.nature }) });
    for (const k of this.combinations) {
      // `terms` (mapa {caso:factor}) es lo que consume el motor (D-019·C.2.a);
      // se serializa como «G:1.35|Q:1.5». `expr` se conserva solo para mostrar.
      const terms = Object.entries(k.terms)
        .map(([cs, f]) => `${cs}:${f}`)
        .join("|");
      entries.push({ name: `comb:${k.id}`, value: enc({ name: k.name, ls: k.limitState, terms, expr: k.expression }) });
    }
    this.provider.persist(entries);
  }
}
