// Skins del visor por disciplina (Slice 1) — DOMINIO PURO: sin three/web-ifc/estado.
// Re-viste el visor por dominio: acento de disciplina + color CATEGÓRICO por clase IFC +
// leyenda por intersección con las clases presentes en el modelo. La skin es «propone»: no
// certifica nada, no reescribe IFC, no toca la ingesta. Ratificado por JM (2026-07-06):
// D-SK-2 (color categórico, no rampa) y D-SK-4 (Diseño + Estructuras). Ver
// openspec/changes/visor-skins-disciplina/.

/** Componente de color normalizado (0..1), compatible con `Viewer.setColorByClass`. */
export interface ColorRGB {
  r: number;
  g: number;
  b: number;
}

/** Disciplinas soportadas en Slice 1 (se ampliará: instalaciones, obras-lineales, puentes). */
export type Disciplina = "diseno" | "estructuras";

/** Definición estática de una skin de disciplina. */
export interface SkinDisciplina {
  /** identificador de la disciplina. */
  readonly id: Disciplina;
  /** nombre legible (ES, con tilde). */
  readonly nombre: string;
  /** color de acento de marca (CSS): pinta la pastilla de disciplina, el dock y remates de UI. */
  readonly acento: string;
  /** clases IFC del dominio, en forma web-ifc (MAYÚSCULAS), como devuelve `Viewer.classes()`. */
  readonly clases: readonly string[];
}

/**
 * Mapa estático canónico disciplina → skin (D-SK-1: mapa de dominio, no derivado solo del
 * modelo). Clases intersecadas con `ELEMENT_TYPES` de `ifc-loader` (lo que el visor carga hoy).
 * `IFCSLAB` es compartido (forjado): su color es único por clase; la pertenencia la decide este
 * mapa, no el color.
 */
export const SKINS: Readonly<Record<Disciplina, SkinDisciplina>> = {
  diseno: {
    id: "diseno",
    nombre: "Diseño",
    acento: "#2f6bed",
    clases: [
      "IFCWALL",
      "IFCWALLSTANDARDCASE",
      "IFCSLAB",
      "IFCWINDOW",
      "IFCDOOR",
      "IFCROOF",
      "IFCCOVERING",
      "IFCCURTAINWALL",
    ],
  },
  estructuras: {
    id: "estructuras",
    nombre: "Estructuras",
    acento: "#e07a4f",
    clases: [
      "IFCCOLUMN",
      "IFCBEAM",
      "IFCSLAB",
      "IFCFOOTING",
      "IFCMEMBER",
      "IFCPILE",
      "IFCPLATE",
    ],
  },
};

/**
 * Color de reserva neutro para clases no mapeadas: gris idéntico al «sin coste» de
 * `Viewer.setCostHeatmap` (0.55, 0.55, 0.58). NO se deriva de ningún hex.
 */
const RESERVA: ColorRGB = { r: 0.55, g: 0.55, b: 0.58 };

/**
 * Mapa canónico PROVISIONAL de color por clase IFC (categórico, distinto por tipo, separado del
 * acento de disciplina — D-SK-2). Semilla de Slice 1; la versión definitiva la fija el design
 * system (Ola 3). Colores legibles sobre el fondo Pizarra fría `#12151b`.
 */
const COLOR_HEX: Readonly<Record<string, string>> = {
  // Diseño
  IFCWALL: "#c9d1d9",
  IFCWALLSTANDARDCASE: "#c9d1d9",
  IFCSLAB: "#8b9dc3",
  IFCWINDOW: "#5bc8e6",
  IFCDOOR: "#d9a05b",
  IFCROOF: "#b05be6",
  IFCCOVERING: "#7e8aa2",
  IFCCURTAINWALL: "#5be6c8",
  // Estructuras
  IFCCOLUMN: "#e0574f",
  IFCBEAM: "#e0a24f",
  IFCFOOTING: "#9e6b3f",
  IFCMEMBER: "#e0d24f",
  IFCPILE: "#a24f2a",
  IFCPLATE: "#c0c04f",
};

/** Convierte `#rrggbb` a componentes 0..1. */
function hexARgb(hex: string): ColorRGB {
  const n = parseInt(hex.slice(1), 16);
  return {
    r: ((n >> 16) & 0xff) / 255,
    g: ((n >> 8) & 0xff) / 255,
    b: (n & 0xff) / 255,
  };
}

/**
 * Color categórico canónico por clase IFC (mapa por TIPO, NO rampa del acento). Determinista y
 * estable; clase no mapeada → gris de reserva. No recibe disciplina: el mismo tipo da siempre el
 * mismo color (p. ej. `IFCSLAB` compartido).
 */
export function colorPorClase(ifcClass: string): ColorRGB {
  const hex = COLOR_HEX[ifcClass.toUpperCase()];
  return hex ? hexARgb(hex) : { ...RESERVA };
}

/** Una entrada de la leyenda de la skin: clase presente en el modelo ∩ dominio de la disciplina. */
export interface EntradaLeyenda {
  /** clase IFC (forma web-ifc, MAYÚSCULAS). */
  readonly ifcClass: string;
  /** conteo de la clase en el modelo. */
  readonly count: number;
  /** color categórico de la clase (0..1). */
  readonly color: ColorRGB;
}

/**
 * Leyenda de la skin = intersección del mapa de dominio con las clases presentes en el modelo
 * (`presentes` es la salida de `Viewer.classes()`). Orden estable: el del mapa de dominio,
 * filtrado por presencia. Las clases presentes fuera del dominio se omiten; las del dominio
 * ausentes del modelo también.
 */
export function leyendaSkin(
  d: Disciplina,
  presentes: ReadonlyArray<{ ifcType: string; count: number }>,
): EntradaLeyenda[] {
  const conteo = new Map<string, number>();
  for (const p of presentes) conteo.set(p.ifcType.toUpperCase(), p.count);
  const salida: EntradaLeyenda[] = [];
  for (const ifcClass of SKINS[d].clases) {
    const count = conteo.get(ifcClass);
    if (count === undefined) continue; // clase del dominio ausente del modelo → se omite
    salida.push({ ifcClass, count, color: colorPorClase(ifcClass) });
  }
  return salida;
}
