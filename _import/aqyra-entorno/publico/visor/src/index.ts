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
export { sunPosition, trueNorthInProject, shadow } from "./solar.js";
export type { SunPosition } from "./solar.js";
export { gridToMesh, localize, elevationRange } from "./terrain.js";
export type { TerrainGrid, TerrainMesh } from "./terrain.js";
export {
  parseParcels, parseBuildings, parseRoads, toCollection, toSnapshot,
  StateEnvProvider, DEFAULT_FLOOR_HEIGHT, ENV_CRS,
} from "./environment.js";
export type { EnvKind, EnvProps, Geom, EnvFeature, EnvFeatureCollection, EnvProvider, StateProviderOpts } from "./environment.js";
export { IfcAuthor, SPACE_OBJECT_TYPE } from "./author.js";
export type {
  SpatialSeed, SpaceSeed, ZoneSeed, SpaceKind, ZoneKind, GeoRef, SiteVolume, AuthoredModel,
  BuildingModelSeed, BuildingStoreySeed, BuildingSpaceSeed, BuildingZoneSeed, ClassificationRef,
} from "./author.js";
