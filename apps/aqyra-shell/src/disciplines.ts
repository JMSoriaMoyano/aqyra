/** Disciplinas (estrategia de skin): al elegir una, reviste el --accent de la app. */
export interface Discipline {
  id: string;
  name: string;
  accent: string; // hex
}

export const DISCIPLINES: Discipline[] = [
  { id: "diseno", name: "Diseño", accent: "#2f6bed" },
  { id: "estructuras", name: "Estructuras", accent: "#e07a4f" },
  { id: "instalaciones", name: "Instalaciones", accent: "#33b3a6" },
  { id: "lineales", name: "Obras lineales", accent: "#a7b061" },
  { id: "puentes", name: "Puentes", accent: "#8f9bb5" },
];

/** hex "#rrggbb" → 0xRRGGBB (para el acento de selección del visor). */
export function hexToInt(hex: string): number {
  return parseInt(hex.replace("#", ""), 16);
}

/** hex + alpha → "rgba(...)" (para --accent-soft). */
export function hexToRgba(hex: string, a: number): string {
  const n = hexToInt(hex);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}
