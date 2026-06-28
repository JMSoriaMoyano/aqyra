/**
 * Puente DSL → C1 (Inc 3, decisión JM: híbrido cebo-preview + C1-autoritativo).
 *
 * El cebo dibuja el preview al vuelo (web-ifc); el IFC AUTORITATIVO (el que será el
 * Maestro y pasa por auditoría) lo compila C1 (`iso19650-openbim/narracion-a-ifc`)
 * desde su "spec de alto nivel" (`<m>.alto.json`). Este módulo serializa el modelo
 * del cebo a ESE formato. No escribe IFC aquí (regla CEBO: sin export firmable); solo
 * produce el HANDOFF estructurado que C1 consume.
 *
 *   modelo del cebo  --toAltoSpec()-->  alto.json  --[C1] compilar_spec.py + spec_to_ifc.py-->  IFC4X3 autoritativo
 *
 * FRONTERA C1: el formato `alto.json` es el CONTRATO. `niveles`/`edificios`/`rampas`/
 * `escaleras` ya existen en C1; el primitivo `espacios` (IfcSpace con footprint, zona y
 * URI bsDD) es la EXTENSIÓN que C1 debe adoptar → bump + golden + anclar en versions.lock.
 * La IA prepara este adaptador; el cruce de frontera lo firma JM.
 */

import type { BuildingModel } from "./model";

const BSDD_SPACE = "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/IfcSpace";

/** Espacio en el spec de C1 (EXTENSIÓN propuesta: primitivo `espacios`). */
export interface AltoEspacio {
  nombre: string;            // código AQ-ESP-…
  nivel: string;             // nombre de la planta
  clase: "IfcSpace";
  objectType: string;        // Habitacion | Pasillo | Nucleo | PlazaAparcamiento | …
  zona: string;              // privado | comunes | aparcamiento | …
  contorno: [number, number][]; // polígono en planta (m), X=ancho Y=fondo
  uri_bsdd: string;          // clasificación bsDD (IFC 4.3)
}

/**
 * Retícula de pilares en el spec de C1. A DIFERENCIA de `espacios`, este primitivo
 * `reticulas_pilares` YA lo consume C1 (`compilar_spec.py` → `expandir_reticula`):
 * no es extensión de frontera, no requiere bump. El cebo entrega la retícula COMPACTA
 * (no las columnas sueltas); C1 expande el pilar por planta estructural con su `estr`.
 */
export interface AltoReticula {
  nombre: string;
  origen: [number, number];
  nx: number; ny: number;
  sep_x: number; sep_y: number;
  seccion: [number, number]; // [ancho, canto] (m)
  material: string;
  niveles?: "todas";          // C1 decide las plantas estructurales
}

/** Spec de alto nivel de C1 (`<m>.alto.json`) que produce el cebo. */
export interface AltoSpec {
  proyecto: string;
  esquema: "IFC4X3";
  niveles: { plantas: number; altura: number; base: number };
  edificios: Array<{
    nombre: string; origen: [number, number]; ancho: number; largo: number;
    muros_perimetrales: boolean; forjados: boolean;
    pilares: boolean;          // el edificio NO mete pilares de esquina: los pone la retícula
  }>;
  espacios: AltoEspacio[];     // extensión de frontera (ver cabecera)
  reticulas_pilares?: AltoReticula[]; // primitivo que C1 YA tiene (sin frontera)
}

export interface BridgeDims { ancho: number; largo: number; altura: number; }

/**
 * Serializa el modelo del cebo al spec de alto nivel de C1. Determinista (mismo
 * modelo → mismo spec): apto para golden del puente.
 */
export function toAltoSpec(model: BuildingModel, dims: BridgeDims): AltoSpec {
  const espacios: AltoEspacio[] = [];
  for (const st of model.storeys) {
    for (const s of st.spaces) {
      const f = s.footprint;
      espacios.push({
        nombre: s.code,
        nivel: st.name,
        clase: "IfcSpace",
        objectType: s.objectType,
        zona: s.zone,
        contorno: [
          [round3(f.x), round3(f.y)],
          [round3(f.x + f.w), round3(f.y)],
          [round3(f.x + f.w), round3(f.y + f.d)],
          [round3(f.x), round3(f.y + f.d)],
        ],
        uri_bsdd: BSDD_SPACE,
      });
    }
  }
  // Si hay retícula, ella es la AUTORIDAD de los pilares → el edificio no añade los
  // suyos de esquina (evita duplicar/solapar). Sin retícula, comportamiento previo.
  const grid = model.grid;
  const reticulas_pilares: AltoReticula[] | undefined = grid
    ? [{
        nombre: `${model.building.name}_Reticula`,
        origen: grid.origin,
        nx: grid.nx, ny: grid.ny,
        sep_x: round3(grid.sepX), sep_y: round3(grid.sepY),
        seccion: [round3(grid.section.w), round3(grid.section.d)],
        material: grid.material,
        niveles: "todas",
      }]
    : undefined;

  return {
    proyecto: model.project.name,
    esquema: "IFC4X3",
    niveles: { plantas: model.storeys.length, altura: round3(dims.altura), base: 0 },
    edificios: [{
      nombre: model.building.name,
      origen: [0, 0],
      ancho: round3(dims.ancho),
      largo: round3(dims.largo),
      muros_perimetrales: true,
      forjados: true,
      pilares: !grid,
    }],
    espacios,
    ...(reticulas_pilares ? { reticulas_pilares } : {}),
  };
}

const round3 = (x: number): number => Math.round(x * 1000) / 1000;
