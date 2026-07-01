/**
 * GEOMETRÍA POR ALINEACIONES (P1·B — familia de TRAZADO, primer slice).
 *
 * TERCER paradigma geométrico del cebo (no "más elementos"): la ALINEACIÓN, una
 * directriz 1D con sección barrida. En IFC 4.3 = `IfcAlignment`. Este módulo modela
 * la DIRECTRIZ HORIZONTAL del primer slice: RECTA + ARCO (clotoide/alzado/sección →
 * slices siguientes; el contrato C1 ya los soporta enteros).
 *
 * REPRESENTACIÓN = la de C1 (frontera-cero): una alineación es un PUNTO DE ARRANQUE
 * (`inicio`: x, y, acimut, cota) + una secuencia de SEGMENTOS por LONGITUD y radio
 * (estación-céntrica, = IfcAlignmentHorizontal). NO se autora por coordenadas
 * absolutas de cada vértice: se INTEGRA desde el arranque. Así el preview del cebo
 * coincide 1:1 con el Maestro que compila C1 desde `alineaciones[]`.
 *
 * CONVENCIÓN (tomada del propio C1, `scripts/lineal/generate_test_ifc_lineal.py`):
 *   · heading (tangente) = (cos acimut, sin acimut); acimut 0 = +X (Este), CCW.
 *   · curvatura k = 1/radio ; `radio` con SIGNO: + = giro a IZQUIERDA, 0/∞ = recta.
 *   · un arco de longitud L gira el acimut Δ = L/radio (con el signo del radio).
 * Misma ley que el integrador de `validacion_alineacion.py` → continuidad y
 * tangencia las da el modelo por construcción.
 *
 * DOS LLAVES: este módulo es DETERMINISTA (mismo input → misma salida) y se congela
 * con su golden (Llave 1). La IA prepara/propone; la firma (Llave 2) es de JM.
 *
 * Alcance del slice: recta + arco. SIN clotoide, SIN alzado/rampa, SIN sección
 * barrida, SIN reorganizar la circulación del parking (esos son los clones
 * siguientes; el contrato C1 0.10.0 ya los contempla).
 */

const round3 = (x: number): number => Math.round(x * 1000) / 1000;
const DEG = Math.PI / 180;

// ── Modelo de autoría (estación-céntrico, = C1) ──────────────────────────────

/** Arranque de la alineación: posición, acimut (grados) y cota (alzado, m). */
export interface AlineacionInicio {
  x: number;
  y: number;
  acimut_deg: number;       // 0 = +X (Este), CCW positivo
  cota?: number;            // cota de arranque (m); el slice horizontal no la usa
}

/** Segmento RECTA: solo longitud (curvatura 0). */
export interface SegRecta { tipo: "recta"; longitud: number; }
/** Segmento ARCO (curva circular): longitud + radio con SIGNO (+ = izquierda). */
export interface SegCurva { tipo: "curva"; longitud: number; radio: number; }
/**
 * Segmento CLOTOIDE (curva de transición): la curvatura VARÍA LINEALMENTE con el
 * recorrido s, de 1/radio_ini a 1/radio_fin. Un extremo AUSENTE = recto (curvatura 0).
 * Parámetro A = √(|radio|·longitud). Radio con SIGNO (+ = izquierda), igual que el arco.
 */
export interface SegClotoide { tipo: "clotoide"; longitud: number; radio_ini?: number; radio_fin?: number; }
/** Segmento de planta: recta | curva (arco circular) | clotoide (transición). */
export type Segmento = SegRecta | SegCurva | SegClotoide;

/**
 * Segmento de ALZADO (perfil longitudinal): por LONGITUD de estación, con la PENDIENTE
 * (tanto por uno) en cada extremo. `rampa` = pendiente constante (ini = fin); `acuerdo` =
 * curva vertical (parábola) que pasa de una pendiente a otra. La cota se integra a lo
 * largo de la estación, independiente de la planta — igual que C1 (golden C1-APERTURA-01).
 * Habilita la HÉLICE (planta = arco · alzado = rampa) y cualquier rasante de obra lineal.
 */
export interface AlzadoSeg { tipo: "rampa" | "acuerdo"; longitud: number; pendiente_ini: number; pendiente_fin: number; }

/** Alineación = objeto propio (`IfcAlignment`), no una 4.ª variante de Placement. */
export interface Alineacion {
  nombre: string;
  /** Infraestructura que soporta la directriz (IfcRoad por defecto del slice). */
  infraestructura?: { clase: string; nombre?: string };
  /** Ancho de referencia de la plataforma (m), informativo en este slice. */
  ancho_ref?: number;
  inicio: AlineacionInicio;
  /** Planta = secuencia de segmentos por longitud (estación-céntrica, como C1). */
  planta: Segmento[];
  /** Alzado (rasante) opcional: perfil de cota por estación. Sin él, la directriz es plana. */
  alzado?: AlzadoSeg[];
}

// ── Resolución geométrica (integración exacta de la directriz) ────────────────

/** Pose en una estación: posición y acimut (rad). */
export interface Pose { x: number; y: number; az: number; }

/** Geometría resuelta de un segmento (para render y self-check). */
export interface SegmentoResuelto {
  tipo: "recta" | "curva" | "clotoide";
  longitud: number;
  radio?: number;              // con signo (solo curva)
  radioIni?: number;           // radio inicial (solo clotoide; ausente = recto)
  radioFin?: number;           // radio final (solo clotoide; ausente = recto)
  inicio: Pose;
  fin: Pose;
  centro?: [number, number];   // centro del arco (solo curva)
  puntos: [number, number][];  // discretización en planta (m), incluye extremos
}

export interface AlineacionResuelta {
  nombre: string;
  segmentos: SegmentoResuelto[];
  /** Polilínea continua de toda la directriz (vértices compartidos sin duplicar). */
  puntos: [number, number][];
  longitudTotal: number;
  /** Pose final (cierra la traza); útil para encadenar / depurar. */
  fin: Pose;
  /** Polilínea 3D (x, y, cota) si hay alzado: la directriz que SUBE (hélice, rampa…). */
  puntos3D?: [number, number, number][];
  /** Cota final (m) tras integrar el alzado. */
  cotaFin?: number;
}

/** Curvatura de un radio con signo (radio ausente/0 = recto → 0). */
function kappa(radio?: number): number { return radio ? 1 / radio : 0; }

/**
 * Perfil de ALZADO: dada la lista de segmentos (rampa/acuerdo) y la cota inicial, devuelve
 * una función cota(estación). En cada segmento la pendiente varía LINEALMENTE de `ini` a
 * `fin` → cota cuadrática (parábola del acuerdo); la rampa (ini = fin) sale lineal. La cota
 * encadena entre segmentos. Misma ley que C1.
 */
function perfilAlzado(alzado: AlzadoSeg[], cota0: number): (st: number) => number {
  const segs: { s0: number; L: number; c0: number; pi: number; pf: number }[] = [];
  let s = 0, c = cota0;
  for (const a of alzado) {
    segs.push({ s0: s, L: a.longitud, c0: c, pi: a.pendiente_ini, pf: a.pendiente_fin });
    c += ((a.pendiente_ini + a.pendiente_fin) / 2) * a.longitud;
    s += a.longitud;
  }
  return (st: number): number => {
    if (segs.length === 0) return cota0;
    let seg = segs[0];
    for (const g of segs) { if (st >= g.s0 - 1e-9) seg = g; else break; }
    const sl = Math.max(0, Math.min(st - seg.s0, seg.L));
    return seg.c0 + seg.pi * sl + ((seg.pf - seg.pi) / (2 * seg.L)) * sl * sl;
  };
}

/**
 * Integra una CLOTOIDE (curvatura LINEAL en s, de k0 a k1) con la MISMA ley que C1
 * (`scripts/lineal/validacion_alineacion.py`): n pasos, regla del punto medio. Así el
 * preview del cebo coincide con el Maestro que compila C1. Devuelve puntos + pose final.
 */
function integraClotoide(p: Pose, L: number, k0: number, k1: number, n: number): { puntos: [number, number][]; fin: Pose } {
  const pts: [number, number][] = [[round3(p.x), round3(p.y)]];
  if (L <= 0) return { puntos: pts, fin: { ...p } };
  const ds = L / n;
  let x = p.x, y = p.y, az = p.az;
  for (let i = 0; i < n; i++) {
    const s = i * ds;
    const k = k0 + (k1 - k0) * (s / L);
    const azm = az + k * (ds / 2);
    x += Math.cos(azm) * ds;
    y += Math.sin(azm) * ds;
    az += k * ds + ((k1 - k0) / L) * ds * (ds / 2);
    pts.push([round3(x), round3(y)]);
  }
  return { puntos: pts, fin: { x, y, az } };
}

/**
 * Pasos de integración de una CLOTOIDE, INDEPENDIENTES del `paso` de render. Clave para la
 * frontera-cero: la MISMA ley de pasos se usa al RESOLVER la traza y al DIMENSIONAR el cambio
 * de carril (la bisección de `cambioDeCarrilClotoide`), de modo que la longitud resuelta
 * produce el aterrizaje EXACTO al integrarse — sin la deriva (~mm) que aparecía cuando la
 * bisección integraba con una discretización distinta a la del resolver. Convergida (≤ 0,5 m
 * por paso, mínimo 64). Determinista.
 */
function pasosClotoide(L: number): number { return Math.max(64, Math.ceil(L / 0.5)); }

/** Pose final de un segmento RECTA/CURVA integrando exactamente desde una pose inicial. */
function integrarFin(p: Pose, s: SegRecta | SegCurva): Pose {
  const L = s.longitud;
  if (s.tipo === "recta" || s.radio === 0) {
    return { x: p.x + Math.cos(p.az) * L, y: p.y + Math.sin(p.az) * L, az: p.az };
  }
  const k = 1 / s.radio;                       // curvatura con signo
  const az1 = p.az + k * L;                     // Δacimut = L/radio
  const x = p.x + (Math.sin(az1) - Math.sin(p.az)) / k;
  const y = p.y - (Math.cos(az1) - Math.cos(p.az)) / k;
  return { x, y, az: az1 };
}

/**
 * Discretiza UN segmento en puntos (m) desde su pose inicial. Recta = 2 puntos;
 * arco = muestreo EXACTO del círculo (no una recta) a paso ~`paso` m. Determinista
 * (nº de tramos = ceil(L/paso)); coords redondeadas a mm.
 */
function muestrear(p: Pose, s: SegRecta | SegCurva, paso: number): [number, number][] {
  const L = s.longitud;
  const n = Math.max(1, Math.ceil(L / paso));
  if (s.tipo === "recta" || s.radio === 0) {
    return [
      [round3(p.x), round3(p.y)],
      [round3(p.x + Math.cos(p.az) * L), round3(p.y + Math.sin(p.az) * L)],
    ];
  }
  const k = 1 / s.radio;
  const out: [number, number][] = [];
  for (let i = 0; i <= n; i++) {
    const ss = (L * i) / n;
    const az = p.az + k * ss;
    const x = p.x + (Math.sin(az) - Math.sin(p.az)) / k;
    const y = p.y - (Math.cos(az) - Math.cos(p.az)) / k;
    out.push([round3(x), round3(y)]);
  }
  return out;
}

/** Centro del arco (a la izquierda del heading si radio>0): P0 + (1/k)·(−sin,cos). */
function centroArco(p: Pose, radio: number): [number, number] {
  const k = 1 / radio;
  return [round3(p.x - Math.sin(p.az) / k), round3(p.y + Math.cos(p.az) / k)];
}

/**
 * Resuelve la alineación: integra la directriz desde `inicio` y discretiza cada
 * segmento. Determinista. `paso` = longitud objetivo entre puntos del arco (m).
 */
export function resolverAlineacion(al: Alineacion, paso = 1.0): AlineacionResuelta {
  let pose: Pose = { x: al.inicio.x, y: al.inicio.y, az: al.inicio.acimut_deg * DEG };
  const segmentos: SegmentoResuelto[] = [];
  const puntos: [number, number][] = [[round3(pose.x), round3(pose.y)]];
  let longitudTotal = 0;

  for (const s of al.planta) {
    const inicio = { ...pose };
    let pts: [number, number][];
    let fin: Pose;
    let extra: Partial<SegmentoResuelto> = {};
    if (s.tipo === "clotoide") {
      const n = pasosClotoide(s.longitud);
      const c = integraClotoide(pose, s.longitud, kappa(s.radio_ini), kappa(s.radio_fin), n);
      pts = c.puntos; fin = c.fin;
      extra = {
        ...(s.radio_ini !== undefined ? { radioIni: s.radio_ini } : {}),
        ...(s.radio_fin !== undefined ? { radioFin: s.radio_fin } : {}),
      };
    } else {
      pts = muestrear(pose, s, paso);
      fin = integrarFin(pose, s);
      if (s.tipo === "curva" && s.radio !== 0) extra = { radio: s.radio, centro: centroArco(pose, s.radio) };
    }
    segmentos.push({ tipo: s.tipo, longitud: s.longitud, ...extra, inicio, fin: { ...fin }, puntos: pts });
    // encadena la polilínea sin duplicar el vértice compartido
    for (let i = 1; i < pts.length; i++) puntos.push(pts[i]);
    longitudTotal += s.longitud;
    pose = fin;
  }

  // ALZADO: si hay rasante, eleva la polilínea a 3D integrando la cota por ESTACIÓN
  // (longitud acumulada de la polilínea ≈ estación). Habilita la hélice y las rampas reales.
  let puntos3D: [number, number, number][] | undefined;
  let cotaFin: number | undefined;
  if (al.alzado && al.alzado.length) {
    const cota = perfilAlzado(al.alzado, al.inicio.cota ?? 0);
    // El alzado se muestrea por ESTACIÓN a paso fino, INDEPENDIENTE de la densidad en planta:
    // una recta larga es solo 2 puntos en planta, pero su rasante varía (rampa/acuerdo) y hay
    // que capturarla — si no, el perfil 3D se "salta" el acuerdo y la cota no sube. Subdivide
    // cada arista de la polilínea a paso `paso`, interpolando x,y (la arista es la cuerda real;
    // en arcos ya viene densa → sub=1, sin cambio). Así la hélice y las rampas SUBEN de verdad.
    const pasoZ = Math.max(paso, 1e-6);
    puntos3D = [[puntos[0][0], puntos[0][1], round3(cota(0))]];
    let st = 0;
    for (let i = 1; i < puntos.length; i++) {
      const [x0, y0] = puntos[i - 1], [x1, y1] = puntos[i];
      const edge = Math.hypot(x1 - x0, y1 - y0);
      const sub = Math.max(1, Math.ceil(edge / pasoZ));
      for (let j = 1; j <= sub; j++) {
        const t = j / sub;
        puntos3D.push([round3(x0 + (x1 - x0) * t), round3(y0 + (y1 - y0) * t), round3(cota(st + edge * t))]);
      }
      st += edge;
    }
    cotaFin = round3(cota(longitudTotal));
  }

  return {
    nombre: al.nombre,
    segmentos,
    puntos,
    longitudTotal: round3(longitudTotal),
    fin: { x: round3(pose.x), y: round3(pose.y), az: pose.az },
    ...(puntos3D ? { puntos3D } : {}),
    ...(cotaFin !== undefined ? { cotaFin } : {}),
  };
}

/** Polilínea de la directriz (atajo: solo los puntos, para el render). */
export function discretizar(al: Alineacion, paso = 1.0): [number, number][] {
  return resolverAlineacion(al, paso).puntos;
}

/**
 * CAMBIO DE CARRIL entre dos alineaciones PARALELAS (mismo rumbo, desfase lateral
 * `lateral` m perpendicular al rumbo) como S simétrica de 4 CLOTOIDES — curvatura
 * 0→+κ→0→−κ→0: rumbo neto 0 (sale paralelo) y curvatura CONTINUA en todo el recorrido
 * (sin el salto de volante de una reversa de arcos). `Rt` = radio mínimo de la transición
 * (paramétrico; el dimensionado fino 3.1-IC es de obras-lineales). `lateral` con signo:
 * + = a la IZQUIERDA del rumbo, − = a la derecha. Resuelve la longitud de cada clotoide
 * (bisección) para aterrizar el desfase EXACTO. Devuelve los segmentos y la pose final
 * LOCAL (desde el origen, rumbo `rumboDeg`), para encadenarlos. Determinista.
 */
export function cambioDeCarrilClotoide(rumboDeg: number, lateral: number, Rt: number): { segmentos: SegClotoide[]; fin: Pose } {
  const sentido = lateral >= 0 ? 1 : -1;
  const az0 = rumboDeg * DEG;
  const k = sentido / Rt;                              // curvatura máxima con signo
  const nl: [number, number] = [-Math.sin(az0), Math.cos(az0)]; // normal IZQUIERDA del rumbo
  const endFor = (L: number): Pose => {
    const n = pasosClotoide(L);                          // misma discretización que el resolver
    let p: Pose = { x: 0, y: 0, az: az0 };
    p = integraClotoide(p, L, 0, k, n).fin;
    p = integraClotoide(p, L, k, 0, n).fin;
    p = integraClotoide(p, L, 0, -k, n).fin;
    p = integraClotoide(p, L, -k, 0, n).fin;
    return p;
  };
  const offsetFor = (L: number): number => { const p = endFor(L); return (p.x * nl[0] + p.y * nl[1]) * sentido; };
  // offset crece monótono con L → bisección
  let lo = 1e-4, hi = Rt * 2;
  for (let it = 0; it < 60; it++) { const mid = (lo + hi) / 2; if (offsetFor(mid) < Math.abs(lateral)) lo = mid; else hi = mid; }
  const L = (lo + hi) / 2;
  const Rs = sentido * Rt;
  const segmentos: SegClotoide[] = [
    { tipo: "clotoide", longitud: L, radio_fin: Rs },
    { tipo: "clotoide", longitud: L, radio_ini: Rs },
    { tipo: "clotoide", longitud: L, radio_fin: -Rs },
    { tipo: "clotoide", longitud: L, radio_ini: -Rs },
  ];
  return { segmentos, fin: endFor(L) };
}

// ── Asistencia de radios (self-check, patrón del parking) ────────────────────
// Mínimo PARAMETRIZABLE en este slice + self-check; la consulta real a
// `obras-lineales` (3.1-IC: radio mínimo según Vp, peralte, fricción) llega después.
// La IA AVISA; no certifica: el dimensionado lo firma técnico competente (ICCP).

export interface AvisoRadio {
  indice: number;        // posición del segmento en la planta
  radio: number;         // radio con signo del arco
  minimo: number;        // mínimo aplicado
}

/** Comprueba el radio de cada arco/clotoide frente a un mínimo. Para la clotoide se
 *  controla el extremo MÁS CERRADO (menor radio). Devuelve los que NO cumplen. */
export function selfCheckRadios(al: Alineacion, radioMinimo: number): AvisoRadio[] {
  const avisos: AvisoRadio[] = [];
  al.planta.forEach((s, i) => {
    if (s.tipo === "curva" && s.radio !== 0) {
      if (Math.abs(s.radio) < radioMinimo - 1e-9) avisos.push({ indice: i, radio: s.radio, minimo: radioMinimo });
    } else if (s.tipo === "clotoide") {
      const radios = [s.radio_ini, s.radio_fin].filter((r): r is number => r !== undefined && r !== 0);
      if (radios.length) {
        const tight = radios.reduce((a, b) => (Math.abs(b) < Math.abs(a) ? b : a)); // el más cerrado
        if (Math.abs(tight) < radioMinimo - 1e-9) avisos.push({ indice: i, radio: tight, minimo: radioMinimo });
      }
    }
  });
  return avisos;
}

// ── Puente C1: handoff `alineaciones[]` (frontera-cero, C1 0.10.0 lo compila) ──
// El formato es EL de C1 (golden C1-APERTURA-01): inicio + planta por longitud/radio.
// El cebo PREVISUALIZA; el IFC autoritativo lo compila C1 (regla CEBO: sin export
// firmable aquí). En este slice emitimos solo `recta`/`curva` (la clotoide es passthrough
// del mismo esquema en el clon siguiente).

export interface AltoSegPlanta {
  tipo: "recta" | "curva" | "clotoide";
  longitud: number;
  radio?: number;            // solo curva (con signo)
  radio_ini?: number;        // solo clotoide (extremo presente = no recto)
  radio_fin?: number;        // solo clotoide
}
/** Segmento de alzado en el spec de C1: rampa (pendiente cte) o acuerdo (curva vertical, kv). */
export interface AltoSegAlzado { tipo: "rampa" | "acuerdo"; longitud: number; pendiente_ini: number; pendiente_fin: number; kv?: number; }
export interface AltoAlineacion {
  nombre: string;
  infraestructura?: { clase: string; nombre?: string };
  ancho_ref?: number;
  inicio: { x: number; y: number; acimut_deg: number; cota: number };
  planta: AltoSegPlanta[];
  alzado?: AltoSegAlzado[];   // rasante (opcional): habilita la hélice y las rampas reales
}

/** Serializa una alineación al primitivo `alineaciones[]` de C1 (determinista). */
export function alineacionToAlto(al: Alineacion): AltoAlineacion {
  return {
    nombre: al.nombre,
    ...(al.infraestructura ? { infraestructura: al.infraestructura } : { infraestructura: { clase: "IfcRoad" } }),
    ...(al.ancho_ref !== undefined ? { ancho_ref: round3(al.ancho_ref) } : {}),
    inicio: {
      x: round3(al.inicio.x), y: round3(al.inicio.y),
      acimut_deg: round3(al.inicio.acimut_deg), cota: round3(al.inicio.cota ?? 0),
    },
    planta: al.planta.map((s): AltoSegPlanta => {
      if (s.tipo === "curva" && s.radio !== 0) return { tipo: "curva", longitud: round3(s.longitud), radio: round3(s.radio) };
      if (s.tipo === "clotoide") return {
        tipo: "clotoide", longitud: round3(s.longitud),
        ...(s.radio_ini !== undefined ? { radio_ini: round3(s.radio_ini) } : {}),
        ...(s.radio_fin !== undefined ? { radio_fin: round3(s.radio_fin) } : {}),
      };
      return { tipo: "recta", longitud: round3(s.longitud) };
    }),
    ...(al.alzado && al.alzado.length ? {
      alzado: al.alzado.map((a): AltoSegAlzado => ({
        tipo: a.tipo, longitud: round3(a.longitud),
        pendiente_ini: round3(a.pendiente_ini), pendiente_fin: round3(a.pendiente_fin),
        // kv = parámetro de la curva vertical (L / Δpendiente); solo en acuerdos
        ...(a.tipo === "acuerdo" && a.pendiente_fin !== a.pendiente_ini
          ? { kv: round3(a.longitud / (a.pendiente_fin - a.pendiente_ini)) } : {}),
      })),
    } : {}),
  };
}

// ── Snapshot determinista para el golden ("caso real → fixture", como el parking) ─

export interface AlineacionSnapshot {
  nombre: string;
  nSegmentos: number;
  nRectas: number;
  nCurvas: number;
  longitudTotal: number;
  fin: [number, number, number];   // x, y, acimut(rad redondeado)
  nPuntos: number;                  // tamaño de la discretización (con `paso` del fixture)
  muestraPuntos: [number, number][]; // primeros puntos (orden estable)
  avisosRadio: number;              // nº de arcos por debajo del mínimo
  alto: AltoAlineacion;             // handoff exacto a C1
}

export interface AlineacionFixture {
  name: string;
  alineacion: Alineacion;
  paso: number;
  radioMinimo: number;
  snapshot: AlineacionSnapshot;
}

const round6 = (x: number): number => Math.round(x * 1e6) / 1e6;

/** Snapshot determinista de (alineación, paso, radioMínimo). */
export function snapshotAlineacion(al: Alineacion, paso: number, radioMinimo: number): AlineacionSnapshot {
  const r = resolverAlineacion(al, paso);
  return {
    nombre: al.nombre,
    nSegmentos: al.planta.length,
    nRectas: al.planta.filter((s) => s.tipo === "recta").length,
    nCurvas: al.planta.filter((s) => s.tipo === "curva").length,
    longitudTotal: r.longitudTotal,
    fin: [r.fin.x, r.fin.y, round6(r.fin.az)],
    nPuntos: r.puntos.length,
    muestraPuntos: r.puntos.slice(0, 6),
    avisosRadio: selfCheckRadios(al, radioMinimo).length,
    alto: alineacionToAlto(al),
  };
}

/** Congela un caso como fixture golden (alineación + snapshot actual). */
export function makeAlineacionFixture(name: string, al: Alineacion, paso: number, radioMinimo: number): AlineacionFixture {
  return { name, alineacion: al, paso, radioMinimo, snapshot: snapshotAlineacion(al, paso, radioMinimo) };
}

/** Replica el fixture y comprueba que el snapshot no cambia (anti-regresión). */
export function checkAlineacionFixture(fx: AlineacionFixture): { ok: boolean; diffs: string[] } {
  const now = snapshotAlineacion(fx.alineacion, fx.paso, fx.radioMinimo);
  const diffs: string[] = [];
  const cmp = (label: string, exp: unknown, got: unknown): void => {
    if (JSON.stringify(exp) !== JSON.stringify(got)) {
      diffs.push(`${label}: esperado ${JSON.stringify(exp)} · obtenido ${JSON.stringify(got)}`);
    }
  };
  cmp("nombre", fx.snapshot.nombre, now.nombre);
  cmp("nSegmentos", fx.snapshot.nSegmentos, now.nSegmentos);
  cmp("nRectas", fx.snapshot.nRectas, now.nRectas);
  cmp("nCurvas", fx.snapshot.nCurvas, now.nCurvas);
  cmp("longitudTotal", fx.snapshot.longitudTotal, now.longitudTotal);
  cmp("fin", fx.snapshot.fin, now.fin);
  cmp("nPuntos", fx.snapshot.nPuntos, now.nPuntos);
  cmp("muestraPuntos", fx.snapshot.muestraPuntos, now.muestraPuntos);
  cmp("avisosRadio", fx.snapshot.avisosRadio, now.avisosRadio);
  cmp("alto", fx.snapshot.alto, now.alto);
  return { ok: diffs.length === 0, diffs };
}
