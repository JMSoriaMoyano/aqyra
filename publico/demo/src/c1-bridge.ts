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
 * Pilar explícito en el spec de C1. Con EJES EXPLÍCITOS (no uniformes) la retícula
 * compacta `reticulas_pilares` (origen+k·sep) ya no vale; el cebo emite cada pilar
 * con su posición exacta. `pilares` YA es primitivo de C1 (passthrough en
 * `compilar_spec.py`) → frontera-CERO, y el preview coincide 1:1 con el Maestro.
 * El `nivel` referencia el nombre de planta de C1 (por eso storeyName = "Planta Baja"…).
 */
export interface AltoPilar {
  nombre: string;
  nivel: string;
  pos: [number, number];      // (x, y) en m
  seccion: [number, number];  // [ancho, canto] (m)
  altura: number;             // altura de planta (m)
  material: string;
}

/**
 * Losa (forjado) explícita en el spec de C1. El primitivo `losas` YA existe; lo
 * NUEVO es el campo `huecos` (lista de contornos a vaciar). C1 monta el void con su
 * `_voids`/`IfcOpeningElement` —ya probado en muros— extendido al bucle de losas:
 * eso es el ÚNICO cruce de frontera de este slice (bump → golden → firma JM). El
 * esquema no cambia (losas admite campos extra). El cebo toma autoridad del forjado
 * (emite la losa) y pone `forjados:false`, igual que `pilares:false` con la retícula.
 */
/** Muro explícito en el spec de C1. `muros` YA es primitivo de C1 → frontera-cero.
 *  El cebo toma autoridad de la fachada (emite los muros) y pone `muros_perimetrales:false`. */
export interface AltoMuro {
  nombre: string;
  nivel: string;
  inicio: [number, number];
  fin: [number, number];
  espesor: number;
  altura: number;
  exterior: boolean;
  material: string;
}

export interface AltoHueco { contorno: [number, number][]; }
export interface AltoLosa {
  nombre: string;
  nivel: string;
  contorno: [number, number][];
  espesor: number;
  material: string;
  huecos?: AltoHueco[];        // EXTENSIÓN de frontera (ver arriba)
}

/** Spec de alto nivel de C1 (`<m>.alto.json`) que produce el cebo. */
export interface AltoSpec {
  proyecto: string;
  esquema: "IFC4X3";
  // Niveles como LISTA (C1 resolver_niveles la acepta): plantas habitables + CUBIERTA
  // encima de la última. La cubierta es un nivel propio (cota = plantas × altura).
  niveles: Array<{ nombre: string; cota: number }>;
  edificios: Array<{
    nombre: string; origen: [number, number]; ancho: number; largo: number;
    muros_perimetrales: boolean; forjados: boolean;
    pilares: boolean;          // el edificio NO mete pilares de esquina: los pone la retícula
  }>;
  espacios: AltoEspacio[];     // extensión de frontera (ver cabecera)
  pilares?: AltoPilar[];       // pilares explícitos (ejes no uniformes); C1 YA los tiene
  losas?: AltoLosa[];          // el cebo autora los forjados (con huecos) → forjados:false
  muros?: AltoMuro[];          // el cebo autora la fachada → muros_perimetrales:false
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
  // Pilares: el cebo los AUTORA explícitos (ejes no uniformes) desde los IfcColumn del
  // modelo → el edificio no añade los suyos de esquina (pilares:false). Frontera-cero.
  const pilares: AltoPilar[] = [];
  for (const st of model.storeys) {
    for (const e of st.elements) {
      if (e.ifcClass !== "IfcColumn" || e.placement.kind !== "point") continue;
      pilares.push({
        nombre: e.code, nivel: e.level,
        pos: [round3(e.placement.x), round3(e.placement.y)],
        seccion: [round3(e.section?.w ?? 0.4), round3(e.section?.d ?? 0.4)],
        altura: round3(dims.altura), material: e.material ?? "HA-30",
      });
    }
  }

  // Forjados: el cebo los AUTORA (con sus huecos) desde los IfcSlab del modelo →
  // el edificio no los autogenera (forjados:false). Los huecos = IfcOpeningElement
  // cuyo `host` es esa losa (capa relacional → C1 los vacía con `_voids`).
  const round2D = (pts: [number, number][]): [number, number][] =>
    pts.map(([x, y]) => [round3(x), round3(y)] as [number, number]);
  const losas: AltoLosa[] = [];
  for (const st of model.storeys) {
    for (const e of st.elements) {
      if (e.ifcClass !== "IfcSlab") continue;
      if (e.placement.kind !== "polygon") continue;
      const huecos: AltoHueco[] = st.elements
        .filter((o) => o.ifcClass === "IfcOpeningElement" && o.host === e.code && o.placement.kind === "polygon")
        .map((o) => ({ contorno: round2D((o.placement as { kind: "polygon"; contour: [number, number][] }).contour) }));
      losas.push({
        nombre: e.code, nivel: e.level,
        contorno: round2D(e.placement.contour),
        espesor: round3(e.thickness ?? 0.3), material: e.material ?? "HA-30",
        ...(huecos.length ? { huecos } : {}),
      });
    }
  }

  // Muros: el cebo AUTORA la fachada (línea por planta) desde los IfcWall del modelo →
  // el edificio no la autogenera (muros_perimetrales:false). Primitivo `muros` de C1.
  const muros: AltoMuro[] = [];
  for (const st of model.storeys) {
    for (const e of st.elements) {
      if (e.ifcClass !== "IfcWall" || e.placement.kind !== "line") continue;
      muros.push({
        nombre: e.code, nivel: e.level,
        inicio: [round3(e.placement.start[0]), round3(e.placement.start[1])],
        fin: [round3(e.placement.end[0]), round3(e.placement.end[1])],
        espesor: round3(e.thickness ?? 0.25), altura: round3(e.height ?? dims.altura),
        exterior: e.exterior ?? false, material: e.material ?? "HA-30",
      });
    }
  }

  // Niveles: una cota por planta habitable + la CUBIERTA encima de la última.
  const niveles = model.storeys.map((st) => ({ nombre: st.name, cota: round3(st.elevation) }));
  niveles.push({ nombre: "Cubierta", cota: round3(model.storeys.length * dims.altura) });

  return {
    proyecto: model.project.name,
    esquema: "IFC4X3",
    niveles,
    edificios: [{
      nombre: model.building.name,
      origen: [0, 0],
      ancho: round3(dims.ancho),
      largo: round3(dims.largo),
      muros_perimetrales: muros.length === 0, // si el cebo da muros, el edificio no añade los suyos
      forjados: false,           // el cebo autora las losas (abajo); C1 no las duplica
      pilares: pilares.length === 0, // si el cebo da pilares, el edificio no añade los suyos
    }],
    espacios,
    ...(pilares.length ? { pilares } : {}),
    ...(losas.length ? { losas } : {}),
    ...(muros.length ? { muros } : {}),
  };
}

const round3 = (x: number): number => Math.round(x * 1000) / 1000;
