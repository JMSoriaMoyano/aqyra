/**
 * Cliente bsDD EN VIVO (decisión JM, P1·B). El árbol enlaza cada entidad IFC con su
 * clase del buildingSMART Data Dictionary (URI real) y muestra sus Psets por defecto.
 *
 * Estrategia (honesta con el coste real): se consulta POR CLASE, no por instancia.
 * Solo hay ~5 clases distintas (IfcProject/Site/Building/BuildingStorey/Space/Zone),
 * así que sus 100+ instancias comparten el resultado. Dos niveles, ambos cacheados:
 *   - bsddClass:      ficha "lean" (uri, name, definición) — ~1,5 KB, al pintar el nodo.
 *   - bsddProperties: classProperties (Pset_*) — ~100 KB, PEREZOSO al desplegar el nodo.
 * Si no hay red/CORS, degrada a null/[] sin romper el árbol (el visor sigue siendo cebo).
 */

const BASE = "https://api.bsdd.buildingsmart.org";
/** Diccionario IFC 4.3 de bsDD (versión anclada; si JM la sube, cambiar aquí). */
export const IFC_DICTIONARY = "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3";

/**
 * URI bsDD (IFC 4.3) de CUALQUIER clase IFC. La URI es determinista (patrón del
 * diccionario), así que no hace falta una tabla: se construye para cualquier
 * `IfcXxx` válido y se valida al consultarla (bsddClass devuelve null si no existe).
 * Inc 2: bsDD por clase a demanda, ya no solo las 6 de antes.
 */
export function classUri(ifcClass: string): string | undefined {
  return /^Ifc[A-Za-z0-9]+$/.test(ifcClass) ? `${IFC_DICTIONARY}/class/${ifcClass}` : undefined;
}

export interface BsddClass {
  uri: string;
  name: string;
  code: string;
  definition?: string;
  dictionaryUri?: string;
}
export interface BsddProperty {
  name: string;
  propertySet?: string;
  dataType?: string;
}

type Json = Record<string, unknown>;
const str = (v: unknown): string | undefined => (typeof v === "string" ? v : undefined);

async function getJson(url: string): Promise<Json | null> {
  try {
    const r = await fetch(url, { headers: { accept: "application/json" } });
    if (!r.ok) return null;
    return (await r.json()) as Json;
  } catch {
    return null; // sin red/CORS → degradación elegante
  }
}

const leanCache = new Map<string, Promise<BsddClass | null>>();
const propsCache = new Map<string, Promise<BsddProperty[]>>();

/** Ficha lean de la clase bsDD (cacheada por clase IFC). */
export function bsddClass(ifcClass: string): Promise<BsddClass | null> {
  const uri = classUri(ifcClass);
  if (!uri) return Promise.resolve(null);
  let p = leanCache.get(ifcClass);
  if (!p) {
    const url = `${BASE}/api/Class/v1?Uri=${encodeURIComponent(uri)}` +
      `&IncludeClassProperties=false&IncludeChildClassReferences=false`;
    p = getJson(url).then((d) =>
      d ? {
        uri: str(d.uri) ?? uri,
        name: str(d.name) ?? ifcClass,
        code: str(d.code) ?? ifcClass,
        definition: str(d.definition),
        dictionaryUri: str(d.dictionaryUri),
      } : null,
    );
    leanCache.set(ifcClass, p);
  }
  return p;
}

/** Psets/propiedades por defecto de la clase (cacheado, perezoso). */
export function bsddProperties(ifcClass: string): Promise<BsddProperty[]> {
  const uri = classUri(ifcClass);
  if (!uri) return Promise.resolve([]);
  let p = propsCache.get(ifcClass);
  if (!p) {
    const url = `${BASE}/api/Class/v1?Uri=${encodeURIComponent(uri)}&IncludeClassProperties=true`;
    p = getJson(url).then((d) => {
      const arr = d?.classProperties;
      if (!Array.isArray(arr)) return [];
      return (arr as Json[])
        .map((c) => ({ name: str(c.name) ?? "", propertySet: str(c.propertySet), dataType: str(c.dataType) }))
        .filter((x) => x.name);
    });
    propsCache.set(ifcClass, p);
  }
  return p;
}
