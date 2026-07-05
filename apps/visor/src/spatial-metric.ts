import type { IfcLoader } from "./ifc-loader.js";
import type { Viewer } from "./viewer.js";

/** Contenedor espacial destino del saneamiento, con su clave de posición (cota o PK). */
export interface Container {
  expressId: number;
  name?: string;
  key: number;
}

/**
 * Métrica espacial enchufable: define CÓMO se decide la planta/parte correcta de
 * un elemento. La mecánica del saneamiento (reasignar contención + reescribir) es
 * común; solo cambia la métrica según el tipo de activo.
 */
export interface SpatialMetric {
  readonly kind: string;
  containers(loader: IfcLoader, modelID: number): Promise<Container[]>;
  positions(viewer: Viewer, modelID: number): Map<number, number>;
  currentContainer(loader: IfcLoader, modelID: number): Promise<Map<number, number>>;
}

const INFRA =
  "[Aqyra] Saneamiento de infraestructura (PK sobre IfcAlignment → IfcFacilityPart) — llega en el incremento de obra lineal. El motor ya está preparado para enchufar esta métrica.";

/** Edificación: posición = cota (eje Z, convenio Z-up), contenedor = IfcBuildingStorey. */
export const elevationMetric: SpatialMetric = {
  kind: "cota",
  async containers(loader, modelID) {
    const st = await loader.getStoreys(modelID);
    return st.map((s) => ({ expressId: s.expressId, name: s.name, key: s.elevation }));
  },
  positions(viewer, modelID) {
    return viewer.elementElevations(modelID);
  },
  currentContainer(loader, modelID) {
    return loader.getElementContainer(modelID, (up) => up.includes("BUILDINGSTOREY"));
  },
};

/** Infraestructura: posición = estación (PK) sobre el alignment, contenedor = IfcFacilityPart. Hook (pendiente). */
export const stationMetric: SpatialMetric = {
  kind: "estacion",
  containers() {
    return Promise.reject(new Error(INFRA));
  },
  positions() {
    throw new Error(INFRA);
  },
  currentContainer() {
    return Promise.reject(new Error(INFRA));
  },
};
