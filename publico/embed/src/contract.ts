import type { RGBA } from "@aqyra/visor";
// Mecánica de estado de dato (D-021) — el vocabulario visual + la regla dura +
// la guarda de exportación viven en el visor (cebo); se re-exportan en el contrato.
export { dataStateStyle, isCertified, exportStamp, stampIfcText } from "@aqyra/visor";
export type { DataStateStyle, Iso19650Code } from "@aqyra/visor";
import type {
  BcfApi,
  IdsApi,
  PreApi,
  StructuralModel,
  StructuralNode,
  StructuralMember,
  StructuralSurface,
  StructuralCore,
  StructuralCoreGroup,
  SurfaceKind,
  SurfaceAreaLoad,
  SectionRef,
  SectionProps,
  MaterialProps,
  LocalAxis,
  MemberEndRelease,
  MemberReleases,
  MemberStiffness,
  Support,
  Restraints,
  Load,
  LoadKind,
  LoadCase,
  Combination,
  // Esquema de resultados del contrato C5 (salida, D-019·B.3)
  MemberStation,
  MemberResult,
  NodeReaction,
  NodeResult,
  SurfaceResult,
  ResultGroup,
  EnvelopeEntry,
  ResultEnvelope,
} from "@aqyra/openbim";

export type {
  RGBA,
  BcfApi,
  IdsApi,
  PreApi,
  StructuralModel,
  StructuralNode,
  StructuralMember,
  StructuralSurface,
  StructuralCore,
  StructuralCoreGroup,
  SurfaceKind,
  SurfaceAreaLoad,
  SectionRef,
  SectionProps,
  MaterialProps,
  LocalAxis,
  MemberEndRelease,
  MemberReleases,
  MemberStiffness,
  Support,
  Restraints,
  Load,
  LoadKind,
  LoadCase,
  Combination,
  MemberStation,
  MemberResult,
  NodeReaction,
  NodeResult,
  SurfaceResult,
  ResultGroup,
  EnvelopeEntry,
  ResultEnvelope,
};

/**
 * Estado de un dato que el visor muestra — las DOS LLAVES del gobierno, explícitas
 * (D-021). El visor NUNCA pinta como `verified-signed` lo que no está certificado
 * y firmado por JM.
 *
 * | Estado            | Significado                                   | Llaves | ISO 19650 |
 * |-------------------|-----------------------------------------------|:------:|-----------|
 * | `proposal`        | Input autorado/derivado, editable             |   —    | WIP / S0  |
 * | `computed`        | El motor calculó, sin verificar (no es verdad)|   0    | WIP / S0  |
 * | `qa-passed`       | 1.ª llave: QA independiente (PyNite, D-023)    |   1    | Compartido/S3 |
 * | `verified-signed` | 2.ª llave: firma de JM. Contractual           |   2    | Publicado/A |
 *
 * Regla visual BINARIA: solo `verified-signed` recibe el trato «certificado»
 * (verde/limpio); todo lo demás se ve provisional. El verde solo lo acuña el flujo
 * de firma de `privado/`; el camino de render público nunca lo produce.
 */
export type DataState = "proposal" | "computed" | "qa-passed" | "verified-signed";

/** Fuente de un modelo IFC: bytes (texto/STEP) o URL al activo. */
export interface IFCSource {
  name: string;
  data: ArrayBuffer | string;
}

/** Handle de un modelo cargado. Federación = varios handles. */
export interface ModelHandle {
  id: string;
  name: string;
  state: DataState;
}

export interface PsetData {
  globalId: string;
  psets: Record<string, Record<string, unknown>>;
}

export type ViewerEvent = "model-loaded" | "selection-changed";
export type Handler = (payload: unknown) => void;
export type Unsubscribe = () => void;

/**
 * Contrato público de Aqyra — versionado SemVer (MAJOR = rotura). v0.
 * Es lo que se "declara, testea y congela": la superficie estable del cebo
 * embebible. En F0 solo existe la superficie; las fases la van implementando.
 */
export interface AqyraViewer {
  /** Carga uno o varios modelos. Array ⇒ federación. */
  load(models: IFCSource | IFCSource[]): Promise<ModelHandle[]>;
  select(globalId: string): void;
  getProperties(globalId: string): Promise<PsetData>;
  setVisibilityByClass(ifcClass: string, visible: boolean): void;
  setColorByClass(ifcClass: string, color: RGBA): void;
  readonly bcf: BcfApi;
  readonly ids: IdsApi;
  /** Pre-proceso estructural (V2): modelo analítico idealizado, apoyos y cargas (`proposal`). */
  readonly pre: PreApi;
  on(event: ViewerEvent, cb: Handler): Unsubscribe;
}
