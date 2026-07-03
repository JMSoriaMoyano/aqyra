/** Lectura BCF 3.0 (buildingSMART) — markup.bcf + viewpoint.bcfv.
 *
 * El visor CONSUME el árbol BCF que emite services/federacion (D12: el árbol
 * descomprimido es el artefacto; D29: PerspectiveCamera determinista en el
 * viewpoint). NUNCA lo re-genera: la fuente única es el service (regla de
 * dependencias del PLAN §1). Parser sobre DOMParser (navegador y jsdom).
 */

/** Terna XYZ en coordenadas IFC (Z-up), como las escribe el BCF. */
export type BcfVec3 = [number, number, number];

/** Topic de markup.bcf (subconjunto que emite el service — BCF 3.0). */
export interface BcfTopic {
  guid: string;
  title: string;
  type?: string;
  status?: string;
  priority?: string;
  labels: string[];
  creationDate?: string;
  creationAuthor?: string;
  description?: string;
  /** Fichero del viewpoint (p. ej. "viewpoint.bcfv") si el topic lo tiene. */
  viewpointFile?: string;
  viewpointGuid?: string;
}

/** PerspectiveCamera del viewpoint (D29), en coordenadas IFC (Z-up). */
export interface BcfCamera {
  viewPoint: BcfVec3;
  direction: BcfVec3;
  up: BcfVec3;
  fovDeg: number;
  aspect: number;
}

/** viewpoint.bcfv: selección de componentes + cámara opcional. */
export interface BcfViewpoint {
  guid: string;
  /** IfcGuid de los Components/Selection (los elementos del topic). */
  selection: string[];
  camera?: BcfCamera;
}

function xml(texto: string): Document {
  const doc = new DOMParser().parseFromString(texto, "text/xml");
  const err = doc.querySelector("parsererror");
  if (err) throw new Error(`BCF: XML mal formado — ${err.textContent ?? ""}`);
  return doc;
}

function texto(padre: Element, tag: string): string | undefined {
  for (const el of Array.from(padre.children)) {
    if (el.tagName === tag) return el.textContent ?? undefined;
  }
  return undefined;
}

/** Parsea un markup.bcf (BCF 3.0) → topic. Lanza si no hay <Topic>. */
export function parseMarkup(textoXml: string): BcfTopic {
  const doc = xml(textoXml);
  const topic = doc.querySelector("Markup > Topic");
  if (!topic) throw new Error("BCF: markup.bcf sin <Topic>");
  const labels: string[] = [];
  const labelsEl = Array.from(topic.children).find((e) => e.tagName === "Labels");
  if (labelsEl) {
    for (const l of Array.from(labelsEl.children)) {
      if (l.tagName === "Label" && l.textContent) labels.push(l.textContent);
    }
  }
  const out: BcfTopic = {
    guid: topic.getAttribute("Guid") ?? "",
    title: texto(topic, "Title") ?? "(sin título)",
    labels,
  };
  const type = topic.getAttribute("TopicType");
  if (type) out.type = type;
  const status = topic.getAttribute("TopicStatus");
  if (status) out.status = status;
  const priority = texto(topic, "Priority");
  if (priority) out.priority = priority;
  const creationDate = texto(topic, "CreationDate");
  if (creationDate) out.creationDate = creationDate;
  const creationAuthor = texto(topic, "CreationAuthor");
  if (creationAuthor) out.creationAuthor = creationAuthor;
  const description = texto(topic, "Description");
  if (description) out.description = description;
  const vp = topic.querySelector("Viewpoints > ViewPoint");
  if (vp) {
    const vpGuid = vp.getAttribute("Guid");
    if (vpGuid) out.viewpointGuid = vpGuid;
    const vpFile = texto(vp, "Viewpoint");
    if (vpFile) out.viewpointFile = vpFile;
  }
  return out;
}

function terna(padre: Element, tag: string): BcfVec3 {
  const el = Array.from(padre.children).find((e) => e.tagName === tag);
  if (!el) throw new Error(`BCF: PerspectiveCamera sin <${tag}>`);
  const v = (n: string): number => {
    const t = texto(el, n);
    if (t === undefined) throw new Error(`BCF: <${tag}> sin <${n}>`);
    return Number(t);
  };
  return [v("X"), v("Y"), v("Z")];
}

/** Parsea un viewpoint.bcfv (BCF 3.0) → selección + cámara (si la hay). */
export function parseViewpoint(textoXml: string): BcfViewpoint {
  const doc = xml(textoXml);
  const root = doc.querySelector("VisualizationInfo");
  if (!root) throw new Error("BCF: viewpoint.bcfv sin <VisualizationInfo>");
  const selection: string[] = [];
  for (const c of Array.from(root.querySelectorAll("Components > Selection > Component"))) {
    const g = c.getAttribute("IfcGuid");
    if (g) selection.push(g);
  }
  const out: BcfViewpoint = { guid: root.getAttribute("Guid") ?? "", selection };
  const cam = root.querySelector("PerspectiveCamera");
  if (cam) {
    out.camera = {
      viewPoint: terna(cam, "CameraViewPoint"),
      direction: terna(cam, "CameraDirection"),
      up: terna(cam, "CameraUpVector"),
      fovDeg: Number(texto(cam, "FieldOfView") ?? "60"),
      aspect: Number(texto(cam, "AspectRatio") ?? "1"),
    };
  }
  return out;
}

/** Mapea la cámara BCF (coordenadas IFC, Z-up) al marco del visor (Y-up de
 *  web-ifc/three): (x, y, z)_IFC → (x, z, −y)_visor. Es el mismo cambio de eje
 *  que aplica web-ifc a la geometría, así la cámara cae donde los meshes. */
export function bcfCameraToViewer(c: BcfCamera): {
  position: BcfVec3; direction: BcfVec3; up: BcfVec3; fovDeg: number;
} {
  const m = (v: BcfVec3): BcfVec3 => [v[0], v[2], -v[1]];
  return { position: m(c.viewPoint), direction: m(c.direction), up: m(c.up), fovDeg: c.fovDeg };
}
