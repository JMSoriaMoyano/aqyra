/**
 * Clasificación Uniclass 2015 — la SEGUNDA cara de la doble clasificación (P1·C, hito 4).
 *
 * La URI bsDD ya vive en el modelo (model.ts → ElementInstance.uriBsdd). Aquí se añade
 * el código Uniclass 2015 de forma DETERMINISTA por `ifcClass[.PredefinedType]`, con el
 * MISMO patrón y formato que usa la maquinaria bsDD del plugin (`iso19650-openbim/
 * bsdd-clasificacion` → `enrich_bsdd.py`): clave `IfcClase` o `IfcClase.PredefinedType`,
 * valor { identificación, nombre, URI }. Una sola fuente: el modelo EMITE el código
 * llamando a `uniclassFor()` y la auditoría ESPERA el mismo valor llamando a la misma
 * función → la coherencia es por construcción (igual que `uriBsdd` ↔ `classUri`).
 *
 * ── RESERVADO A JM (regla del proyecto) ──────────────────────────────────────────
 * Los VALORES de esta tabla son normativos: igual que la golden y las tolerancias, los
 * ancla y los firma JM. Son códigos de la tabla EF (Elements/functions) de Uniclass
 * 2015; la maquinaria del plugin los obtiene en vivo de la API bsDD
 * (Class/Search/v1 · DictionaryUris=uniclass2015 · RelatedIfcEntities=IfcXxx). Aquí van
 * ANCLADOS (sin red) para que el cebo sea determinista y golden-able. La IA propone el
 * seed; JM ratifica/ajusta cada código contra bsDD. La AUDITORÍA verifica coherencia
 * (lo emitido == la tabla), no la verdad universal del string.
 */

/** Diccionario Uniclass 2015 de NBS en bsDD (versión anclada; si JM la sube, cambiar aquí). */
export const UNICLASS_DICTIONARY = "https://identifier.buildingsmart.org/uri/nbs/uniclass2015/1";

/** Referencia de clasificación Uniclass de un objeto: código + nombre + URI. */
export interface UniclassRef {
  code: string; // identificación Uniclass 2015 (p. ej. "EF_25")
  name: string; // título de la clase Uniclass
  uri: string;  // URI canónica en bsDD
}

/** URI canónica de un código Uniclass 2015 (patrón del diccionario NBS en bsDD). */
export function uniclassUri(code: string): string {
  return `${UNICLASS_DICTIONARY}/class/${code}`;
}

/**
 * Tabla ANCLADA por `ifcClass[.PredefinedType]` → { code, name } (Uniclass 2015, tabla
 * EF). Clave específica (clase.PredefinedType) gana a la genérica (clase), igual que en
 * `enrich_bsdd.py`. Cubre las clases FÍSICAS que el cebo emite hoy. Los huecos
 * (IfcOpeningElement) NO se clasifican: son un vacío, no un producto → sin entrada.
 *
 * ⚑ JM: confirmar/ajustar cada código contra bsDD (RelatedIfcEntities). Seed propuesto:
 */
const TABLE: Record<string, { code: string; name: string }> = {
  IfcColumn: { code: "EF_20", name: "Structural elements" },
  IfcSlab:   { code: "EF_30", name: "Roof, floor and paving elements" },
  IfcWall:   { code: "EF_25", name: "Wall and barrier elements" }, // bsDD-confirmado (IfcWall→EF_25)
  IfcDoor:   { code: "EF_25", name: "Wall and barrier elements" }, // puerta = elemento de barrera (grupo EF_25)
  IfcWindow: { code: "EF_25", name: "Wall and barrier elements" }, // ventana = elemento de barrera (grupo EF_25)
  IfcStair:  { code: "EF_45", name: "Circulation elements" },
  // IfcOpeningElement → sin entrada (vacío, no producto): la auditoría lo excluye de Uniclass.
};

/**
 * Devuelve la clasificación Uniclass de una clase IFC (y su PredefinedType si lo hay),
 * o `undefined` si esa clase no se clasifica con Uniclass en este slice. Determinista.
 */
export function uniclassFor(ifcClass: string, predefinedType?: string): UniclassRef | undefined {
  const hit = (predefinedType ? TABLE[`${ifcClass}.${predefinedType}`] : undefined) ?? TABLE[ifcClass];
  return hit ? { code: hit.code, name: hit.name, uri: uniclassUri(hit.code) } : undefined;
}

/** ¿Esta clase IFC DEBE llevar clasificación Uniclass? (para la regla de auditoría R3). */
export function uniclassRequired(ifcClass: string, predefinedType?: string): boolean {
  return uniclassFor(ifcClass, predefinedType) !== undefined;
}
