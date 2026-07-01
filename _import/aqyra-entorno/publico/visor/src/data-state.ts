// Estado de dato del visor — las DOS LLAVES, visibles y APLICADAS (D-021). El
// visor NUNCA pinta como verificado lo no firmado. Este módulo es la MECÁNICA
// (cebo, publico/): el vocabulario visual + la regla dura + la guarda de
// exportación. NO produce el estado `verified-signed`: ese lo acuña solo el flujo
// de firma de `privado/` (dos llaves). Espeja `DataState` del contrato (@aqyra/openbim).

/** Estado de dato (idéntico a `DataState`/`PreDataState` del contrato). */
export type DataState = "proposal" | "computed" | "qa-passed" | "verified-signed";

/** Código ISO 19650 alineado con el CDE Aqyra (skill cde-audit). */
export type Iso19650Code = "S0" | "S3" | "A";

export interface DataStateStyle {
  /** etiqueta para el chip. */
  label: string;
  /** color del chip (CSS). */
  color: string;
  /** SOLO `verified-signed` = certificado (regla binaria D-021·B.2). */
  certified: boolean;
  /** estampar la marca de agua «provisional» sobre los overlays de resultado. */
  watermark: boolean;
  /** código ISO 19650 del estado. */
  iso: Iso19650Code;
}

const STYLES: Record<DataState, DataStateStyle> = {
  proposal: { label: "PROPUESTA", color: "#6b7280", certified: false, watermark: false, iso: "S0" },
  computed: { label: "NO VERIFICADO", color: "#be2832", certified: false, watermark: true, iso: "S0" },
  "qa-passed": { label: "QA OK · SIN FIRMAR", color: "#d98a00", certified: false, watermark: true, iso: "S3" },
  "verified-signed": { label: "VERIFICADO · firma JM", color: "#1f9d55", certified: true, watermark: false, iso: "A" },
};

/** Estilo visual de un estado. */
export function dataStateStyle(state: DataState): DataStateStyle {
  return STYLES[state];
}

/**
 * REGLA DURA (D-021·B.4): el trato «certificado» (verde/limpio) está condicionado
 * a `verified-signed`. Esta función es la ÚNICA fuente de verdad del verde; el
 * camino de render público pregunta aquí y NUNCA devuelve true para otro estado.
 */
export function isCertified(state: DataState): boolean {
  return state === "verified-signed";
}

/**
 * Guarda de exportación (D-021·C.2): toda salida NO firmada lleva su marca, para
 * que no circule como certificada fuera de la pantalla. Devuelve la leyenda a
 * estampar, o `null` si está firmada (no necesita marca).
 */
export function exportStamp(state: DataState): string | null {
  if (isCertified(state)) return null;
  const s = STYLES[state];
  return `AQYRA · NO VERIFICADO (${s.label}) · ISO 19650 ${s.iso} · sin firma de JM`;
}

/**
 * Estampa un texto IFC con la marca de estado si NO está firmado, como comentario
 * STEP `/* … *\/` insertado tras el token `DATA;` (válido en ISO-10303-21, no
 * rompe el parseo). Idempotente: no duplica la marca. Si está firmado, devuelve
 * el texto intacto.
 */
export function stampIfcText(text: string, state: DataState): string {
  const stamp = exportStamp(state);
  if (stamp === null) return text;
  if (text.includes("AQYRA · NO VERIFICADO")) return text; // ya estampado
  const comment = `\n/* ${stamp} */\n`;
  const i = text.indexOf("DATA;");
  if (i === -1) return comment + text; // sin sección DATA: marca al principio
  return text.slice(0, i + "DATA;".length) + comment + text.slice(i + "DATA;".length);
}
