/** @aqyra/visor — núcleo del visor OpenBIM de Aqyra (corte mínimo del re-home 3.1).
 *
 * Corte: abre+navega+selecciona+árbol (viewer, ifc-loader, registry,
 * spatial-metric, idealize, data-state) + lectura BCF 3.0 con cámara (bcf, NUEVO).
 * Los módulos de autoría/contexto (author, environment, solar, terrain) quedan en
 * el record histórico firmado (_import/aqyra-entorno) para hilos posteriores.
 */

/** Color RGBA normalizado (0..1). */
export type RGBA = { r: number; g: number; b: number; a: number };

export { Viewer } from "./viewer.js";
export type { PickInfo } from "./viewer.js";
export { IfcLoader, appendStructuralPset, stripStructuralPset, AQYRA_PSET } from "./ifc-loader.js";
export type { IfcSchema, LoadedElement, LoadedModel, PsetRecord, IfcMeshData, SpatialNode, Storey, SpatialFix, PsetEntry } from "./ifc-loader.js";
export { ModelRegistry } from "./registry.js";
export { elevationMetric, stationMetric } from "./spatial-metric.js";
export type { SpatialMetric, Container } from "./spatial-metric.js";
export { deriveModel, pcaAxisStrategy } from "./idealize.js";
export type { DerivedModel, DerivedNode, DerivedMember, PhysicalElement, IdealizationStrategy, Vec3 } from "./idealize.js";
export { dataStateStyle, isCertified, exportStamp, stampIfcText } from "./data-state.js";
export type { DataState, DataStateStyle, Iso19650Code } from "./data-state.js";
export { parseMarkup, parseViewpoint, bcfCameraToViewer } from "./bcf.js";
export type { BcfVec3, BcfTopic, BcfCamera, BcfViewpoint } from "./bcf.js";
export { readCostModel, costHeatColor } from "./cost.js";
export type { CosteModelo, PartidaCoste, ElementoCoste, CapituloCoste, TotalesCoste } from "./cost.js";
