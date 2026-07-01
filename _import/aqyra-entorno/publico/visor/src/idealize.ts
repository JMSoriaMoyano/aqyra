// Idealización ENCHUFABLE (estilo `SpatialMetric`): deriva el modelo analítico
// (nudos + ejes de barra) del modelo FÍSICO. Decopak HQ es solo físico y NO
// trae representación `'Axis'` (ver HILO-V2_evidencia-modelo-analitico.md), así
// que el eje se reconstruye de la GEOMETRÍA teselada del elemento: eje principal
// (PCA) de la nube de vértices en coordenadas de mundo → la dirección larga del
// miembro. Es MECÁNICA abierta (cebo); el CRITERIO (qué cargas/combinaciones
// tocan) es anzuelo y NO vive aquí.
//
// Todo lo derivado es PROPUESTA revisable por un humano (luz/apoyos/coacciones
// editables), nunca hecho cerrado: la lección del cálculo de Decopak HQ es que
// los errores nacen de la IDEALIZACIÓN, no de leer la geometría (D-008).

/** Nudo idealizado (forma compatible con `StructuralNode` de @aqyra/openbim). */
export interface DerivedNode {
  id: string;
  x: number;
  y: number;
  z: number;
}

/** Miembro idealizado (forma compatible con `StructuralMember` de @aqyra/openbim). */
export interface DerivedMember {
  id: string;
  kind: "beam" | "column" | "brace" | "chord" | "post" | "member" | "slab" | "wall" | "other";
  nodeStart: string;
  nodeEnd: string;
  section?: { profile: string; material?: string };
  ifcGlobalId?: string;
  /** longitud del eje derivado (m) — útil para diagnóstico/QA. */
  length: number;
}

/** Superficie idealizada (losa/muro) derivada del físico. PROPUESTA revisable. */
export interface DerivedSurface {
  id: string;
  kind: "diaphragm" | "shell";
  ifcType: string;
  ifcGlobalId?: string;
  /** 4 esquinas del rectángulo de contorno en el plano del elemento (orden de anillo). */
  outline: Vec3[];
  /** centroide del plano = nudo maestro del diafragma. */
  center: Vec3;
  /** normal unitaria del plano. */
  normal: Vec3;
  /** rejilla de placas (solo kind="shell"): nudos + cuadriláteros por índice. */
  mesh?: { nodes: Vec3[]; quads: Array<[number, number, number, number]> };
  /** área REAL de la planta (envolvente convexa, m²) — la que reparte carga (Indicación A). */
  area: number;
  /** área del rectángulo envolvente (extensión dibujada, m²) — solo para diafragma-rigidez. */
  extentArea: number;
  /** false = el elemento NO es un plano (caja/núcleo): no se debe colapsar a una lámina (Indicación B). */
  planar: boolean;
  /** espesor estimado (extensión perpendicular al plano, m). */
  thickness: number;
  /** true = GRUESO (t/luz alto): la lámina delgada no aplica → sólido/placa gruesa (Indicación C). */
  thick: boolean;
  /** true = plano TORCIDO: muro cuyo plano derivado está ladeado de la vertical → artefacto de derivación a revisar (Indicación C). */
  skewed: boolean;
  /** id del grupo-núcleo si esta cara forma parte de un núcleo (caras unidas por esquinas). */
  group?: string;
  /** true si el grupo-núcleo es una caja CERRADA; false si es abierto (U/L). */
  groupClosed?: boolean;
  /** true = lámina derivada por PLANO MEDIO/OBB (espesor real), no por el plano PCA único heredado. */
  decomposed?: boolean;
}

/** Grupo de caras (muros planos) que forman un NÚCLEO unido por esquinas. */
export interface DerivedCoreGroup {
  id: string;
  members: string[]; // ids de las superficies-cara
  closed: boolean; // caja cerrada (todas las caras con ≥2 vecinas) vs abierta (U/L)
  /** malla shell UNIFICADA de las caras, COSIDA en las aristas de esquina (nudos compartidos). */
  mesh?: { nodes: Vec3[]; quads: Array<[number, number, number, number]> };
}

/** Columna-cajón equivalente: idealiza un núcleo (caja de muros) como UNA barra
 * vertical con las propiedades de la sección cerrada. Alternativa a las 4 láminas.
 * Las propiedades son BRUTAS (sección sólida del contorno) + J de Bredt con espesor
 * supuesto: PROPUESTA para comparar; la precisión la calcula el motor (V3). */
export interface DerivedCore {
  id: string;
  ifcType: string;
  ifcGlobalId?: string;
  axis: { a: Vec3; b: Vec3 };
  /** contorno de la sección (en la base), para dibujar. */
  sectionOutline: Vec3[];
  A: number; // área de la sección CONSIDERADA (hueca si se pudo; si no, bruta) (m²)
  Agross: number; // área BRUTA del contorno exterior (sólido) (m²)
  hollow: boolean; // true ⇒ A/Ix/Iy son de la sección HUECA (exterior − interior)
  Awall: number; // área de pared = perímetro × espesor (m²)
  Ix: number; // inercia de la sección considerada, respecto al centro (m⁴)
  Iy: number;
  J: number; // rigidez torsional (Bredt, sección cerrada) (m⁴)
  perimeter: number;
  thickness: number;
}

export interface DerivedModel {
  nodes: DerivedNode[];
  members: DerivedMember[];
  surfaces: DerivedSurface[];
  cores: DerivedCore[];
  coreGroups: DerivedCoreGroup[];
}

/** Elemento físico de entrada para la derivación. `verts` = xyz EN MUNDO, planos. */
export interface PhysicalElement {
  expressId: number;
  globalId?: string;
  ifcType: string;
  predefinedType?: string;
  section?: { profile: string; material?: string };
  verts: ArrayLike<number>;
}

/**
 * Estrategia de idealización enchufable. La mecánica (clustering de nudos,
 * ensamblaje) es común; solo cambia CÓMO se obtiene el eje de cada elemento.
 */
export interface IdealizationStrategy {
  readonly kind: string;
  /** Eje del miembro (extremos en mundo) o `null` si el elemento no es una barra. */
  axisOf(el: PhysicalElement): { a: Vec3; b: Vec3 } | null;
}

export type Vec3 = [number, number, number];

// ── Tipos físicos que SÍ idealizamos como barra (1D) en el primer corte ────────
// Slabs/walls/footings tienen geometría 2D/3D: su idealización (lámina/resorte)
// llega después; aquí se omiten para no fabricar ejes espurios.
const BAR_TYPES = new Set(["IFCBEAM", "IFCCOLUMN", "IFCMEMBER", "IFCPILE"]);

function kindOf(ifcType: string, predef?: string): DerivedMember["kind"] {
  const p = (predef ?? "").toUpperCase();
  switch (ifcType.toUpperCase()) {
    case "IFCBEAM":
      return "beam";
    case "IFCCOLUMN":
      return "column";
    case "IFCPILE":
      return "post";
    case "IFCMEMBER":
      if (p === "CHORD") return "chord";
      if (p === "POST") return "post";
      if (p.includes("BRACE")) return "brace";
      return "member";
    default:
      return "other";
  }
}

// ── Álgebra mínima (sin dependencias) ──────────────────────────────────────────
function sub(a: Vec3, b: Vec3): Vec3 {
  return [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
}
function dot(a: Vec3, b: Vec3): number {
  return a[0] * b[0] + a[1] * b[1] + a[2] * b[2];
}
function norm(a: Vec3): Vec3 {
  const m = Math.hypot(a[0], a[1], a[2]) || 1;
  return [a[0] / m, a[1] / m, a[2] / m];
}
function cross(a: Vec3, b: Vec3): Vec3 {
  return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
}
function add(a: Vec3, b: Vec3): Vec3 {
  return [a[0] + b[0], a[1] + b[1], a[2] + b[2]];
}
function scale(a: Vec3, k: number): Vec3 {
  return [a[0] * k, a[1] * k, a[2] * k];
}

/**
 * Eje principal de una nube de puntos por ITERACIÓN DE POTENCIA sobre la matriz
 * de covarianza (eigenvector dominante = dirección de mayor varianza = eje largo
 * del miembro prismático). Determinista; sin solver de eigen externo.
 */
function principalAxis(verts: ArrayLike<number>): { centroid: Vec3; dir: Vec3 } {
  const n = Math.floor(verts.length / 3);
  const c: Vec3 = [0, 0, 0];
  for (let i = 0; i < n; i++) {
    c[0] += verts[i * 3];
    c[1] += verts[i * 3 + 1];
    c[2] += verts[i * 3 + 2];
  }
  c[0] /= n || 1;
  c[1] /= n || 1;
  c[2] /= n || 1;
  // Covarianza 3x3 simétrica.
  let xx = 0, xy = 0, xz = 0, yy = 0, yz = 0, zz = 0;
  for (let i = 0; i < n; i++) {
    const dx = verts[i * 3] - c[0];
    const dy = verts[i * 3 + 1] - c[1];
    const dz = verts[i * 3 + 2] - c[2];
    xx += dx * dx; xy += dx * dy; xz += dx * dz;
    yy += dy * dy; yz += dy * dz; zz += dz * dz;
  }
  const mul = (v: Vec3): Vec3 => [
    xx * v[0] + xy * v[1] + xz * v[2],
    xy * v[0] + yy * v[1] + yz * v[2],
    xz * v[0] + yz * v[1] + zz * v[2],
  ];
  // Arranque no alineado con los ejes para evitar puntos fijos degenerados.
  let v: Vec3 = norm([0.572, 0.518, 0.636]);
  for (let it = 0; it < 32; it++) {
    const nv = mul(v);
    const m = Math.hypot(nv[0], nv[1], nv[2]);
    if (m < 1e-12) break;
    v = [nv[0] / m, nv[1] / m, nv[2] / m];
  }
  return { centroid: c, dir: norm(v) };
}

/** Eje por defecto: PCA de la geometría teselada (no requiere `'Axis'`). */
export const pcaAxisStrategy: IdealizationStrategy = {
  kind: "pca-geometria",
  axisOf(el) {
    if (!BAR_TYPES.has(el.ifcType.toUpperCase())) return null;
    if (el.verts.length < 6) return null;
    const { centroid, dir } = principalAxis(el.verts);
    let tMin = Infinity;
    let tMax = -Infinity;
    const n = Math.floor(el.verts.length / 3);
    for (let i = 0; i < n; i++) {
      const p: Vec3 = [el.verts[i * 3], el.verts[i * 3 + 1], el.verts[i * 3 + 2]];
      const t = dot(sub(p, centroid), dir);
      if (t < tMin) tMin = t;
      if (t > tMax) tMax = t;
    }
    const a: Vec3 = [centroid[0] + dir[0] * tMin, centroid[1] + dir[1] * tMin, centroid[2] + dir[2] * tMin];
    const b: Vec3 = [centroid[0] + dir[0] * tMax, centroid[1] + dir[1] * tMax, centroid[2] + dir[2] * tMax];
    return { a, b };
  },
};

/** Redondeo a rejilla de tolerancia para fundir nudos coincidentes. */
function nodeKey(p: Vec3, tol: number): string {
  const q = (x: number): number => Math.round(x / tol);
  return `${q(p[0])},${q(p[1])},${q(p[2])}`;
}

/**
 * Deriva el modelo analítico (nudos con CONECTIVIDAD real + miembros) del
 * conjunto físico. `tol` (m) funde extremos coincidentes en un mismo nudo
 * (decisión D-014; por defecto 150 mm — los extremos derivados de la geometría
 * concurren separados por el canto de los elementos, no exactamente en el eje).
 */
export function deriveModel(
  elements: PhysicalElement[],
  opts?: { tolerance?: number; strategy?: IdealizationStrategy; splitAtIntersections?: boolean; connectCrossings?: boolean; shellCell?: number; coreThickness?: number; coreGroupTolerance?: number; surfaceMode?: "plane" | "obb"; minSurfaceSpan?: number },
): DerivedModel {
  const tol = opts?.tolerance ?? 0.15;
  const strategy = opts?.strategy ?? pcaAxisStrategy;
  const nodeByKey = new Map<string, DerivedNode>();
  let nodeSeq = 0;
  const nodeFor = (p: Vec3): string => {
    const k = nodeKey(p, tol);
    const ex = nodeByKey.get(k);
    if (ex) return ex.id;
    const id = `N${++nodeSeq}`;
    nodeByKey.set(k, { id, x: p[0], y: p[1], z: p[2] });
    return id;
  };
  const members: DerivedMember[] = [];
  for (const el of elements) {
    const axis = strategy.axisOf(el);
    if (!axis) continue;
    const len = Math.hypot(axis.b[0] - axis.a[0], axis.b[1] - axis.a[1], axis.b[2] - axis.a[2]);
    if (len < 1e-3) continue; // descarta solo ejes nulos (independiente de la tolerancia de nudos)
    members.push({
      id: `B${el.expressId}`,
      kind: kindOf(el.ifcType, el.predefinedType),
      nodeStart: nodeFor(axis.a),
      nodeEnd: nodeFor(axis.b),
      section: el.section,
      ifcGlobalId: el.globalId,
      length: len,
    });
  }

  const surfaces = deriveSurfaces(elements, opts);
  const cores = deriveCores(elements, opts);
  // Agrupa caras planas que forman un núcleo (unidas por esquinas). Tag in-place.
  const coreGroups = groupCores(surfaces, opts?.coreGroupTolerance ?? 0.7);
  // 4 láminas COSIDAS: malla shell unificada por grupo, compartiendo nudos de esquina.
  const surfById = new Map(surfaces.map((s) => [s.id, s]));
  for (const grp of coreGroups) {
    const outs = grp.members.map((id) => surfById.get(id)?.outline).filter((o): o is Vec3[] => !!o);
    grp.mesh = buildCoreShell(outs, opts?.shellCell ?? 1.5, opts?.coreGroupTolerance ?? 0.7);
  }
  if (opts?.splitAtIntersections === false) {
    return { nodes: [...nodeByKey.values()], members, surfaces, cores, coreGroups };
  }
  // Inserta nudos en CRUCES interiores (tirante×forjado, rejilla de forjado)
  // antes de partir; el partido (abajo) divide ambas barras en ese nudo.
  if (opts?.connectCrossings !== false) {
    const byId = new Map<string, DerivedNode>([...nodeByKey.values()].map((n) => [n.id, n]));
    const getPos = (id: string): Vec3 => {
      const n = byId.get(id)!;
      return [n.x, n.y, n.z];
    };
    connectCrossings(members, getPos, nodeFor, tol);
  }
  const nodes = [...nodeByKey.values()];
  return { nodes, members: splitAtIntersections(members, nodes, tol), surfaces, cores, coreGroups };
}

/**
 * PARTE las barras en las intersecciones interiores: si un NUDO (extremo de
 * otro elemento) cae sobre el VANO de una barra (a distancia ≤ tol del eje y sin
 * estar en sus extremos), la barra se divide ahí insertando ese nudo. Así un
 * tirante o una vigueta que acomete a mitad de un forjado/viga queda CONECTADO
 * (comparten nudo), y un pilar pasante se parte en cada planta. No inventa nudos
 * en cruces sin extremo (p. ej. el aspa de un arriostramiento): solo usa nudos
 * existentes → conservador.
 */
function splitAtIntersections(members: DerivedMember[], nodes: DerivedNode[], tol: number): DerivedMember[] {
  const pos = new Map<string, Vec3>(nodes.map((n) => [n.id, [n.x, n.y, n.z]]));
  const out: DerivedMember[] = [];
  for (const m of members) {
    const a = pos.get(m.nodeStart);
    const b = pos.get(m.nodeEnd);
    if (!a || !b) {
      out.push(m);
      continue;
    }
    const ab = sub(b, a);
    const L2 = dot(ab, ab);
    const len = Math.sqrt(L2);
    const cuts: Array<{ id: string; t: number }> = [];
    if (L2 > 1e-9) {
      for (const n of nodes) {
        if (n.id === m.nodeStart || n.id === m.nodeEnd) continue;
        const p: Vec3 = [n.x, n.y, n.z];
        const t = dot(sub(p, a), ab) / L2;
        if (t <= 0 || t >= 1) continue;
        if (t * len <= tol || (1 - t) * len <= tol) continue; // no en los extremos
        const foot: Vec3 = [a[0] + ab[0] * t, a[1] + ab[1] * t, a[2] + ab[2] * t];
        if (Math.hypot(p[0] - foot[0], p[1] - foot[1], p[2] - foot[2]) > tol) continue;
        cuts.push({ id: n.id, t });
      }
    }
    if (!cuts.length) {
      out.push(m);
      continue;
    }
    cuts.sort((x, y) => x.t - y.t);
    const seq = [m.nodeStart, ...cuts.map((c) => c.id), m.nodeEnd];
    for (let i = 0; i < seq.length - 1; i++) {
      const pa = pos.get(seq[i])!;
      const pb = pos.get(seq[i + 1])!;
      const l = Math.hypot(pb[0] - pa[0], pb[1] - pa[1], pb[2] - pa[2]);
      if (l < 1e-3) continue;
      out.push({ ...m, id: `${m.id}/${i + 1}`, nodeStart: seq[i], nodeEnd: seq[i + 1], length: l });
    }
  }
  return out;
}

/** Eje global dominante (0=x,1=y,2=z) si la barra es ~paralela a un eje; si no, -1. */
function dominantAxis(u: Vec3): number {
  const ax = Math.abs(u[0]), ay = Math.abs(u[1]), az = Math.abs(u[2]);
  const mx = Math.max(ax, ay, az);
  if (mx < 0.95) return -1; // inclinada (p. ej. diagonal de cercha) → no se trata como cruce
  return ax === mx ? 0 : ay === mx ? 1 : 2;
}

/**
 * Inserta un nudo en el CRUCE interior de dos barras cuando AMBAS son paralelas a
 * un eje global y ORTOGONALES entre sí (tirante vertical × viga horizontal, o
 * rejilla de forjado). Conservador: excluye barras inclinadas, así que NO conecta
 * las aspas de un arriostramiento/cercha (que cruzan sin nudo real). El nudo se
 * registra vía `nodeFor`; el partido posterior divide ambas barras en él.
 */
function connectCrossings(
  members: DerivedMember[],
  getPos: (id: string) => Vec3,
  nodeFor: (p: Vec3) => string,
  tol: number,
): void {
  const seg = members.map((m) => {
    const a = getPos(m.nodeStart);
    const b = getPos(m.nodeEnd);
    const d = sub(b, a);
    const L = Math.hypot(d[0], d[1], d[2]);
    const u: Vec3 = L > 1e-9 ? [d[0] / L, d[1] / L, d[2] / L] : [0, 0, 0];
    return { a, d, L, axis: dominantAxis(u) };
  });
  for (let i = 0; i < seg.length; i++) {
    const A = seg[i];
    if (A.axis < 0) continue;
    for (let j = i + 1; j < seg.length; j++) {
      const B = seg[j];
      if (B.axis < 0 || B.axis === A.axis) continue; // inclinada o paralela → no es cruce ortogonal
      const p = closestInteriorPoint(A, B, tol);
      if (p) nodeFor(p);
    }
  }
}

/** Punto medio entre dos segmentos si su mínima distancia ≤ tol y el pie es INTERIOR a ambos. */
function closestInteriorPoint(
  A: { a: Vec3; d: Vec3; L: number },
  B: { a: Vec3; d: Vec3; L: number },
  tol: number,
): Vec3 | null {
  const r = sub(A.a, B.a);
  const a = dot(A.d, A.d), e = dot(B.d, B.d);
  const b = dot(A.d, B.d), c = dot(A.d, r), f = dot(B.d, r);
  const den = a * e - b * b;
  if (den < 1e-9) return null; // paralelos
  const s = (b * f - c * e) / den;
  const t = (a * f - b * c) / den;
  if (s * A.L <= tol || (1 - s) * A.L <= tol) return null; // no interior en A
  if (t * B.L <= tol || (1 - t) * B.L <= tol) return null; // no interior en B
  const ca: Vec3 = [A.a[0] + A.d[0] * s, A.a[1] + A.d[1] * s, A.a[2] + A.d[2] * s];
  const cb: Vec3 = [B.a[0] + B.d[0] * t, B.a[1] + B.d[1] * t, B.a[2] + B.d[2] * t];
  if (Math.hypot(ca[0] - cb[0], ca[1] - cb[1], ca[2] - cb[2]) > tol) return null;
  return [(ca[0] + cb[0]) / 2, (ca[1] + cb[1]) / 2, (ca[2] + cb[2]) / 2];
}

// ── Superficies (losas/muros): idealización 2D ─────────────────────────────────
// Diafragma (losas) / lámina (muros, p. ej. el núcleo de Decopak HQ). En V2 es una
// PROPUESTA: contorno + plano (+ malla para lámina). La PRECISIÓN FE del shell la
// calcula el motor-fem (V3, C5); aquí solo la mecánica abierta y revisable.
const SURFACE_TYPES = new Set(["IFCSLAB", "IFCWALL", "IFCWALLSTANDARDCASE"]);

/**
 * Plano de mejor ajuste de una nube de puntos: dos ejes principales en el plano
 * (PCA con deflación) y la normal = u1×u2. Determinista (iteración de potencia).
 */
function principalPlane(verts: ArrayLike<number>): { centroid: Vec3; u1: Vec3; u2: Vec3; normal: Vec3 } {
  const n = Math.floor(verts.length / 3);
  const c: Vec3 = [0, 0, 0];
  for (let i = 0; i < n; i++) {
    c[0] += verts[i * 3];
    c[1] += verts[i * 3 + 1];
    c[2] += verts[i * 3 + 2];
  }
  c[0] /= n || 1; c[1] /= n || 1; c[2] /= n || 1;
  let xx = 0, xy = 0, xz = 0, yy = 0, yz = 0, zz = 0;
  for (let i = 0; i < n; i++) {
    const dx = verts[i * 3] - c[0], dy = verts[i * 3 + 1] - c[1], dz = verts[i * 3 + 2] - c[2];
    xx += dx * dx; xy += dx * dy; xz += dx * dz; yy += dy * dy; yz += dy * dz; zz += dz * dz;
  }
  const mul = (v: Vec3): Vec3 => [
    xx * v[0] + xy * v[1] + xz * v[2],
    xy * v[0] + yy * v[1] + yz * v[2],
    xz * v[0] + yz * v[1] + zz * v[2],
  ];
  const power = (m: (v: Vec3) => Vec3): Vec3 => {
    let v: Vec3 = norm([0.572, 0.518, 0.636]);
    for (let it = 0; it < 32; it++) {
      const nv = m(v);
      const mg = Math.hypot(nv[0], nv[1], nv[2]);
      if (mg < 1e-12) break;
      v = [nv[0] / mg, nv[1] / mg, nv[2] / mg];
    }
    return norm(v);
  };
  const u1 = power(mul);
  const lam1 = dot(u1, mul(u1));
  // Deflación: quita la componente de u1 para obtener el 2.º eje principal.
  const mul2 = (v: Vec3): Vec3 => {
    const mv = mul(v);
    const k = lam1 * dot(u1, v);
    return [mv[0] - k * u1[0], mv[1] - k * u1[1], mv[2] - k * u1[2]];
  };
  const u2 = power(mul2);
  return { centroid: c, u1, u2, normal: norm(cross(u1, u2)) };
}

// ── PLANO MEDIO POR CAJA ORIENTADA (OBB) ───────────────────────────────────────
// La descomposición por teselación (1.ª versión del item 2) se afinó sobre cajas
// sintéticas perfectas y NO sobrevive a la geometría real de Revit: muros como
// IfcFacetedBrep / IfcBooleanClippingResult y losas CSG se fragmentan en decenas de
// parches y el relleno rectangular sobresale del muro. El enfoque robusto es derivar
// UNA lámina por elemento como su SUPERFICIE MEDIA: caja orientada (OBB) de la nube
// de vértices → el eje de MENOR extensión es el ESPESOR y su plano medio es la
// lámina, con espesor y orientación REALES, sin clustering frágil. (El contorno
// poligonal exacto desde IfcExtrudedAreaSolid es una capa posterior; necesita leer
// el perfil vía web-ifc y no se ha podido verificar en sandbox.)

/**
 * Lámina (superficie media) de UN elemento por caja orientada (OBB): de los 3 ejes
 * principales de la nube, el de MENOR extensión es el ESPESOR y su plano medio es la
 * lámina. SESGO por tipo: un MURO da lámina VERTICAL (normal horizontal); una LOSA,
 * lámina HORIZONTAL (normal vertical). El contorno es el rectángulo del OBB en el
 * plano medio: real para muros/losas rectangulares; para formas en L/recortadas es
 * una PROPUESTA envolvente revisable. Determinista (PCA por iteración de potencia).
 */
function surfaceFromBox(el: PhysicalElement, cell: number, minSpanThresh: number): DerivedSurface | null {
  if (el.verts.length < 12) return null;
  const isSlab = el.ifcType.toUpperCase() === "IFCSLAB";
  const pl = principalPlane(el.verts);
  const cen = pl.centroid;
  const n = Math.floor(el.verts.length / 3);
  const extentOf = (ax: Vec3): { lo: number; hi: number } => {
    let lo = Infinity, hi = -Infinity;
    for (let i = 0; i < n; i++) {
      const t = dot(sub([el.verts[i * 3], el.verts[i * 3 + 1], el.verts[i * 3 + 2]], cen), ax);
      if (t < lo) lo = t;
      if (t > hi) hi = t;
    }
    return { lo, hi };
  };
  // 3 ejes principales (u1,u2 = mayores; normal = menor) con su extensión.
  const axes = [pl.u1, pl.u2, pl.normal].map((a) => {
    const e = extentOf(a);
    return { a, span: e.hi - e.lo, lo: e.lo, hi: e.hi };
  });
  // Normal de la lámina = eje de MENOR extensión (el ESPESOR), SIN sesgo por tipo.
  // Forzar la normal a horizontal (muro) o vertical (losa) descartaba el eje de
  // espesor REAL cuando la PCA del mesh salía algo ladeada (muros con talud, breps
  // ruidosos): metía el espesor (~0,5 m) en el plano y la lámina se filtraba por
  // minSpan → así caían muros y TODAS las losas (8/10 elementos del depósito real).
  // El eje más fino es el espesor de forma robusta; su orientación sale sola.
  const nAx = axes.reduce((m, c) => (c.span < m.span ? c : m));
  const normal = norm(nAx.a);
  const plane = axes.filter((c) => c !== nAx);
  const e1 = plane[0]!.a, e2 = plane[1]!.a;
  const mid = (nAx.lo + nAx.hi) / 2;
  const ctr = add(cen, scale(normal, mid)); // origen de la lámina sobre el plano medio
  let sMin = Infinity, sMax = -Infinity, tMin = Infinity, tMax = -Infinity;
  for (let i = 0; i < n; i++) {
    const d = sub([el.verts[i * 3], el.verts[i * 3 + 1], el.verts[i * 3 + 2]], cen);
    const s = dot(d, e1), t = dot(d, e2);
    if (s < sMin) sMin = s; if (s > sMax) sMax = s;
    if (t < tMin) tMin = t; if (t > tMax) tMax = t;
  }
  const corner = (s: number, t: number): Vec3 => add(ctr, add(scale(e1, s), scale(e2, t)));
  const outline: Vec3[] = [corner(sMin, tMin), corner(sMax, tMin), corner(sMax, tMax), corner(sMin, tMax)];
  const thickness = nAx.span;
  const area = (sMax - sMin) * (tMax - tMin);
  const minSpan = Math.min(sMax - sMin, tMax - tMin) || 1;
  // Descarta elementos DEGENERADOS como superficie: si la dimensión menor en el
  // plano es diminuta (canto, bordillo, junta o upstand de pocos cm — p. ej. los
  // "muros de 20 cm" del depósito salen de 22 m × 0,1–0,7 m), no es una lámina
  // estructural sino un borde casi-1D. Idealizarlo como lámina produce tiras
  // larguísimas y finísimas (y, por t/luz alto, marcadas grueso/rosa). Se omite.
  if (minSpan < minSpanThresh) return null;
  const thick = thickness > 0.25 && thickness / minSpan > 0.1;
  const kind: DerivedSurface["kind"] = isSlab ? "diaphragm" : "shell";
  const surf: DerivedSurface = {
    id: `S${el.expressId}`,
    kind,
    ifcType: el.ifcType,
    ifcGlobalId: el.globalId,
    outline,
    center: ctr,
    normal,
    area,
    extentArea: area,
    planar: true, // el plano medio SIEMPRE es plano → no hay falso no-plano (rojo)
    thickness,
    thick,
    skewed: false, // la normal es la del eje de espesor → sin tilt del conjunto
    decomposed: true, // marca: derivado por OBB (plano medio), no por PCA único
  };
  if (kind === "shell") surf.mesh = meshRect(ctr, e1, e2, sMin, sMax, tMin, tMax, cell);
  return surf;
}

/** Deriva losas/muros como superficie idealizada (contorno + plano + malla si lámina). */
export function deriveSurfaces(
  elements: PhysicalElement[],
  opts?: { shellCell?: number; surfaceMode?: "plane" | "obb"; minSurfaceSpan?: number },
): DerivedSurface[] {
  const cell = opts?.shellCell ?? 1.5;
  const out: DerivedSurface[] = [];
  for (const el of elements) {
    if (!SURFACE_TYPES.has(el.ifcType.toUpperCase())) continue;
    if (el.verts.length < 9) continue;
    // Modo OBB (geometría real): una lámina limpia por elemento como su plano medio
    // (espesor y orientación reales). Modo "plane" (heredado, por defecto): plano PCA
    // único + flags planar/grueso/torcido — se conserva para los tests sintéticos.
    if (opts?.surfaceMode === "obb") {
      const s = surfaceFromBox(el, cell, opts?.minSurfaceSpan ?? 1.0);
      if (s) {
        out.push(s);
        continue;
      }
      continue; // OBB activo: si el elemento es degenerado, NO se cae al plano PCA
    }
    const plane = principalPlane(el.verts);
    const centroid = plane.centroid;
    let u1 = plane.u1;
    let u2 = plane.u2;
    let normal = plane.normal;
    // VERTICALIZA muros: un IfcWall es vertical en realidad. Si el plano PCA sale
    // ligeramente ladeado (artefacto de geometría facetada), se fuerza el plano a
    // vertical (normal horizontal) para que la lámina no salga torcida (PROPUESTA).
    // Solo si el ladeo es moderado (|normal·Z|<0,7); muros muy tumbados se dejan y
    // se marcan `skewed` para revisión (podrían ser reales o un artefacto grueso).
    if (el.ifcType.toUpperCase().startsWith("IFCWALL") && Math.abs(normal[2]) < 0.7) {
      normal = norm([normal[0], normal[1], 0]);
      u1 = [0, 0, 1];
      u2 = norm(cross(normal, u1));
    }
    let sMin = Infinity, sMax = -Infinity, tMin = Infinity, tMax = -Infinity, dMin = Infinity, dMax = -Infinity;
    const n = Math.floor(el.verts.length / 3);
    const pts2: Array<{ s: number; t: number }> = [];
    for (let i = 0; i < n; i++) {
      const p: Vec3 = [el.verts[i * 3], el.verts[i * 3 + 1], el.verts[i * 3 + 2]];
      const d = sub(p, centroid);
      const s = dot(d, u1), t = dot(d, u2), dn = dot(d, normal);
      pts2.push({ s, t });
      if (s < sMin) sMin = s; if (s > sMax) sMax = s;
      if (t < tMin) tMin = t; if (t > tMax) tMax = t;
      if (dn < dMin) dMin = dn; if (dn > dMax) dMax = dn;
    }
    const corner = (s: number, t: number): Vec3 => add(add(centroid, scale(u1, s)), scale(u2, t));
    // Indicación A: contorno REAL (envolvente convexa) y su ÁREA, no el rectángulo.
    const hull = convexHull2(pts2);
    const ring = hull.length >= 3 ? hull : [{ s: sMin, t: tMin }, { s: sMax, t: tMin }, { s: sMax, t: tMax }, { s: sMin, t: tMax }];
    const outline: Vec3[] = ring.map((h) => corner(h.s, h.t));
    const area = polyArea2(ring);
    const extentArea = (sMax - sMin) * (tMax - tMin);
    // Indicación B: si el espesor perpendicular al plano es grande, NO es un plano (caja/núcleo).
    const perp = dMax - dMin;
    const inPlane = Math.max(sMax - sMin, tMax - tMin) || 1;
    const planar = perp <= Math.max(0.6, 0.1 * inPlane);
    // Indicación C: si el espesor es grande frente a la luz (lado menor en el plano),
    // la teoría de lámina delgada (Kirchhoff) no aplica → sólido / placa gruesa.
    const minSpan = Math.min(sMax - sMin, tMax - tMin) || 1;
    const thickness = perp;
    const thick = thickness > 0.25 && thickness / minSpan > 0.1;
    // Indicación C: un MURO cuyo plano sale ladeado de la vertical (normal con
    // componente vertical apreciable) suele ser un ARTEFACTO de derivación
    // ("muro torcido"), p. ej. de geometría facetada. Se marca para revisión.
    const isWall = el.ifcType.toUpperCase().startsWith("IFCWALL");
    const skewed = isWall && Math.abs(normal[2]) > 0.4;
    const isSlab = el.ifcType.toUpperCase() === "IFCSLAB";
    const kind: DerivedSurface["kind"] = isSlab ? "diaphragm" : "shell"; // losa→diafragma, muro→lámina (editable)
    const surf: DerivedSurface = {
      id: `S${el.expressId}`,
      kind,
      ifcType: el.ifcType,
      ifcGlobalId: el.globalId,
      outline,
      center: centroid,
      normal,
      area,
      extentArea,
      planar,
      thickness,
      thick,
      skewed,
    };
    // Malla solo si es lámina PLANA; un núcleo no-plano se marca y no se falsea como un plano.
    if (kind === "shell" && planar) surf.mesh = meshRect(centroid, u1, u2, sMin, sMax, tMin, tMax, cell);
    out.push(surf);
  }
  return out;
}

/** Envolvente convexa 2D (monotone chain). Devuelve el anillo en orden. */
function convexHull2(pts: Array<{ s: number; t: number }>): Array<{ s: number; t: number }> {
  const p = pts.slice().sort((a, b) => a.s - b.s || a.t - b.t);
  if (p.length < 3) return p;
  const crs = (o: { s: number; t: number }, a: { s: number; t: number }, b: { s: number; t: number }): number =>
    (a.s - o.s) * (b.t - o.t) - (a.t - o.t) * (b.s - o.s);
  const lower: Array<{ s: number; t: number }> = [];
  for (const q of p) {
    while (lower.length >= 2 && crs(lower[lower.length - 2], lower[lower.length - 1], q) <= 0) lower.pop();
    lower.push(q);
  }
  const upper: Array<{ s: number; t: number }> = [];
  for (let i = p.length - 1; i >= 0; i--) {
    const q = p[i];
    while (upper.length >= 2 && crs(upper[upper.length - 2], upper[upper.length - 1], q) <= 0) upper.pop();
    upper.push(q);
  }
  lower.pop();
  upper.pop();
  return lower.concat(upper);
}

/** Área de un anillo 2D (fórmula del cordón). */
function polyArea2(ring: Array<{ s: number; t: number }>): number {
  let a = 0;
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i];
    const q = ring[(i + 1) % ring.length];
    a += p.s * q.t - q.s * p.t;
  }
  return Math.abs(a) / 2;
}

// ── Columna-cajón equivalente (alternativa B para núcleos no-planos) ────────────
const WALL_TYPES = new Set(["IFCWALL", "IFCWALLSTANDARDCASE"]);

/** Dos vectores unitarios perpendiculares a `n` (base del plano de sección). */
function basisPerp(n: Vec3): { v1: Vec3; v2: Vec3 } {
  const a: Vec3 = Math.abs(n[0]) < 0.9 ? [1, 0, 0] : [0, 1, 0];
  const v1 = norm(cross(n, a));
  const v2 = norm(cross(n, v1));
  return { v1, v2 };
}

/** Propiedades de sección de un polígono 2D: área, centroide e inercias respecto al centro. */
function polygonMoments(ring: Array<{ s: number; t: number }>): { A: number; cx: number; cy: number; Ix: number; Iy: number } {
  let A2 = 0, cx = 0, cy = 0, Ixx = 0, Iyy = 0;
  for (let i = 0; i < ring.length; i++) {
    const p = ring[i];
    const q = ring[(i + 1) % ring.length];
    const cr = p.s * q.t - q.s * p.t;
    A2 += cr;
    cx += (p.s + q.s) * cr;
    cy += (p.t + q.t) * cr;
    Ixx += (p.t * p.t + p.t * q.t + q.t * q.t) * cr; // ∫ t² dA (inercia respecto a eje s)
    Iyy += (p.s * p.s + p.s * q.s + q.s * q.s) * cr; // ∫ s² dA (inercia respecto a eje t)
  }
  const A = A2 / 2;
  cx /= 6 * A;
  cy /= 6 * A;
  const IxO = Ixx / 12;
  const IyO = Iyy / 12;
  // Traslado al centroide (Steiner).
  const Ix = IxO - A * cy * cy;
  const Iy = IyO - A * cx * cx;
  return { A: Math.abs(A), cx, cy, Ix: Math.abs(Ix), Iy: Math.abs(Iy) };
}

/** Área firmada de un anillo 2D (signo = sentido de giro). */
function signedArea2(r: Array<{ s: number; t: number }>): number {
  let a = 0;
  for (let i = 0; i < r.length; i++) {
    const p = r[i];
    const q = r[(i + 1) % r.length];
    a += p.s * q.t - q.s * p.t;
  }
  return a / 2;
}

/** Contorno interior: desplaza cada lado del polígono CONVEXO hacia dentro `t`. null si degenera. */
function offsetInward(ring: Array<{ s: number; t: number }>, t: number): Array<{ s: number; t: number }> | null {
  let r = ring;
  if (signedArea2(r) < 0) r = r.slice().reverse(); // asegurar CCW (interior a la izquierda)
  const n = r.length;
  type L = { s: number; t: number; dx: number; dy: number };
  const lines: L[] = [];
  for (let i = 0; i < n; i++) {
    const p = r[i];
    const q = r[(i + 1) % n];
    const dx = q.s - p.s, dy = q.t - p.t;
    const len = Math.hypot(dx, dy);
    if (len < 1e-9) return null;
    const ux = dx / len, uy = dy / len;
    const nx = -uy, ny = ux; // normal izquierda = hacia el interior (CCW)
    lines.push({ s: p.s + nx * t, t: p.t + ny * t, dx: ux, dy: uy });
  }
  const inner: Array<{ s: number; t: number }> = [];
  for (let i = 0; i < n; i++) {
    const a = lines[(i - 1 + n) % n];
    const b = lines[i];
    const den = a.dx * b.dy - a.dy * b.dx;
    if (Math.abs(den) < 1e-9) return null; // lados paralelos
    const u = ((b.s - a.s) * b.dy - (b.t - a.t) * b.dx) / den;
    inner.push({ s: a.s + a.dx * u, t: a.t + a.dy * u });
  }
  if (Math.abs(signedArea2(inner)) <= 1e-6) return null;
  return inner;
}

/**
 * Agrupa caras de muro que forman un NÚCLEO: dos caras son adyacentes si sus
 * contornos tienen esquinas a menos de `tol` (se tocan en una esquina vertical).
 * Por componentes conexas (union-find). Una caja es CERRADA si todas sus caras
 * tienen ≥2 vecinas (sin extremos libres); una U/L es abierta. Etiqueta las
 * superficies in-place con su grupo. Resuelve el caso "núcleo autorado por caras
 * sueltas" (p. ej. NC1 Sur/Este/Norte/Oeste), que por elemento parecería 4
 * láminas independientes. (El cosido FE de nudos de malla es del motor, V3.)
 */
function groupCores(surfaces: DerivedSurface[], tol: number): DerivedCoreGroup[] {
  const walls = surfaces.filter((s) => s.ifcType.toUpperCase().startsWith("IFCWALL"));
  const n = walls.length;
  if (n < 2) return [];
  const minCornerDist = (A: Vec3[], B: Vec3[]): number => {
    let m = Infinity;
    for (const a of A) for (const b of B) {
      const d = Math.hypot(a[0] - b[0], a[1] - b[1], a[2] - b[2]);
      if (d < m) m = d;
    }
    return m;
  };
  const adj: Array<Set<number>> = walls.map(() => new Set<number>());
  for (let i = 0; i < n; i++) {
    for (let j = i + 1; j < n; j++) {
      if (minCornerDist(walls[i].outline, walls[j].outline) < tol) {
        adj[i].add(j);
        adj[j].add(i);
      }
    }
  }
  const parent = walls.map((_, i) => i);
  const find = (x: number): number => {
    while (parent[x] !== x) {
      parent[x] = parent[parent[x]];
      x = parent[x];
    }
    return x;
  };
  for (let i = 0; i < n; i++) for (const j of adj[i]) parent[find(i)] = find(j);
  const comp = new Map<number, number[]>();
  for (let i = 0; i < n; i++) {
    const r = find(i);
    const arr = comp.get(r) ?? [];
    arr.push(i);
    comp.set(r, arr);
  }
  const groups: DerivedCoreGroup[] = [];
  let gid = 0;
  for (const idxs of comp.values()) {
    if (idxs.length < 2) continue; // cara suelta = pantalla aislada, no es núcleo
    const closed = idxs.length >= 3 && idxs.every((i) => adj[i].size >= 2);
    const id = `G${++gid}`;
    for (const i of idxs) {
      walls[i].group = id;
      walls[i].groupClosed = closed;
    }
    groups.push({ id, members: idxs.map((i) => walls[i].id), closed });
  }
  return groups;
}

/**
 * Cose las caras de un núcleo en una malla shell ÚNICA: malla cada cara (rectángulo
 * del contorno) en una rejilla y FUNDE los nudos coincidentes por posición (tol).
 * Las aristas de esquina compartidas → nudos compartidos → las 4 láminas trabajan
 * como caja conectada. (La precisión FE la calcula el motor, V3; aquí el modelo cosido.)
 */
function buildCoreShell(outlines: Vec3[][], cell: number, tol: number): { nodes: Vec3[]; quads: Array<[number, number, number, number]> } {
  const nodes: Vec3[] = [];
  const byKey = new Map<string, number>();
  const key = (p: Vec3): string => `${Math.round(p[0] / tol)},${Math.round(p[1] / tol)},${Math.round(p[2] / tol)}`;
  const nodeFor = (p: Vec3): number => {
    const k = key(p);
    let id = byKey.get(k);
    if (id === undefined) {
      id = nodes.length;
      nodes.push(p);
      byKey.set(k, id);
    }
    return id;
  };
  const quads: Array<[number, number, number, number]> = [];
  for (const o of outlines) {
    if (o.length < 4) continue;
    const o0 = o[0], o1 = o[1], o3 = o[o.length - 1];
    const uDir = sub(o1, o0);
    const vDir = sub(o3, o0);
    const nu = Math.max(1, Math.round(Math.hypot(uDir[0], uDir[1], uDir[2]) / cell));
    const nv = Math.max(1, Math.round(Math.hypot(vDir[0], vDir[1], vDir[2]) / cell));
    const grid: number[][] = [];
    for (let j = 0; j <= nv; j++) {
      const row: number[] = [];
      for (let i = 0; i <= nu; i++) {
        const p = add(add(o0, scale(uDir, i / nu)), scale(vDir, j / nv));
        row.push(nodeFor(p));
      }
      grid.push(row);
    }
    for (let j = 0; j < nv; j++) {
      for (let i = 0; i < nu; i++) {
        quads.push([grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]);
      }
    }
  }
  return { nodes, quads };
}

/** Idealiza los muros NO-PLANOS (cajas/núcleos) como columna-cajón equivalente. */
export function deriveCores(elements: PhysicalElement[], opts?: { coreThickness?: number }): DerivedCore[] {
  const t = opts?.coreThickness ?? 0.3;
  const out: DerivedCore[] = [];
  for (const el of elements) {
    if (!WALL_TYPES.has(el.ifcType.toUpperCase())) continue;
    if (el.verts.length < 12) continue;
    // ¿no-plano? (mismo criterio que deriveSurfaces: espesor perpendicular grande)
    const pl = principalPlane(el.verts);
    let dMin = Infinity, dMax = -Infinity, e1Min = Infinity, e1Max = -Infinity, e2Min = Infinity, e2Max = -Infinity;
    const n = Math.floor(el.verts.length / 3);
    for (let i = 0; i < n; i++) {
      const d = sub([el.verts[i * 3], el.verts[i * 3 + 1], el.verts[i * 3 + 2]], pl.centroid);
      const dn = dot(d, pl.normal), a1 = dot(d, pl.u1), a2 = dot(d, pl.u2);
      if (dn < dMin) dMin = dn; if (dn > dMax) dMax = dn;
      if (a1 < e1Min) e1Min = a1; if (a1 > e1Max) e1Max = a1;
      if (a2 < e2Min) e2Min = a2; if (a2 > e2Max) e2Max = a2;
    }
    const inPlane = Math.max(e1Max - e1Min, e2Max - e2Min) || 1;
    if (dMax - dMin <= Math.max(0.6, 0.1 * inPlane)) continue; // plano → no es caja

    // Eje vertical = eje principal mayor de la nube; sección = plano perpendicular.
    const { centroid, dir } = principalAxis(el.verts);
    const { v1, v2 } = basisPerp(dir);
    let aMin = Infinity, aMax = -Infinity;
    const pts2: Array<{ s: number; t: number }> = [];
    for (let i = 0; i < n; i++) {
      const d = sub([el.verts[i * 3], el.verts[i * 3 + 1], el.verts[i * 3 + 2]], centroid);
      const a = dot(d, dir);
      if (a < aMin) aMin = a; if (a > aMax) aMax = a;
      pts2.push({ s: dot(d, v1), t: dot(d, v2) });
    }
    const hull = convexHull2(pts2);
    if (hull.length < 3) continue;
    const mOuter = polygonMoments(hull);
    let perimeter = 0;
    for (let i = 0; i < hull.length; i++) {
      const p = hull[i], q = hull[(i + 1) % hull.length];
      perimeter += Math.hypot(p.s - q.s, p.t - q.t);
    }
    // Sección HUECA: exterior − interior (contorno desplazado hacia dentro el espesor).
    let A = mOuter.A, Ix = mOuter.Ix, Iy = mOuter.Iy, hollow = false;
    const inner = offsetInward(hull, t);
    if (inner) {
      const mIn = polygonMoments(inner);
      if (mIn.A > 0 && mIn.A < mOuter.A) {
        A = mOuter.A - mIn.A;
        Ix = Math.max(0, mOuter.Ix - mIn.Ix);
        Iy = Math.max(0, mOuter.Iy - mIn.Iy);
        hollow = true;
      }
    }
    const axisCenter = add(add(centroid, scale(v1, mOuter.cx)), scale(v2, mOuter.cy));
    const lower = add(axisCenter, scale(dir, aMin));
    const upper = add(axisCenter, scale(dir, aMax));
    const sectionOutline = hull.map((h) => add(add(lower, scale(v1, h.s - mOuter.cx)), scale(v2, h.t - mOuter.cy)));
    const J = perimeter > 0 ? (4 * mOuter.A * mOuter.A * t) / perimeter : 0; // Bredt (área encerrada ≈ exterior)
    out.push({
      id: `K${el.expressId}`,
      ifcType: el.ifcType,
      ifcGlobalId: el.globalId,
      axis: { a: lower, b: upper },
      sectionOutline,
      A,
      Agross: mOuter.A,
      hollow,
      Awall: perimeter * t,
      Ix,
      Iy,
      J,
      perimeter,
      thickness: t,
    });
  }
  return out;
}

/** Rejilla regular de cuadriláteros sobre el rectángulo del plano (para lámina). */
function meshRect(c: Vec3, u1: Vec3, u2: Vec3, sMin: number, sMax: number, tMin: number, tMax: number, cell: number): { nodes: Vec3[]; quads: Array<[number, number, number, number]> } {
  const ns = Math.min(20, Math.max(1, Math.round((sMax - sMin) / cell)));
  const nt = Math.min(20, Math.max(1, Math.round((tMax - tMin) / cell)));
  const nodes: Vec3[] = [];
  for (let j = 0; j <= nt; j++) {
    for (let i = 0; i <= ns; i++) {
      const s = sMin + ((sMax - sMin) * i) / ns;
      const t = tMin + ((tMax - tMin) * j) / nt;
      nodes.push(add(add(c, scale(u1, s)), scale(u2, t)));
    }
  }
  const quads: Array<[number, number, number, number]> = [];
  const idx = (i: number, j: number): number => j * (ns + 1) + i;
  for (let j = 0; j < nt; j++) {
    for (let i = 0; i < ns; i++) {
      quads.push([idx(i, j), idx(i + 1, j), idx(i + 1, j + 1), idx(i, j + 1)]);
    }
  }
  return { nodes, quads };
}
