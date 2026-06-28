/**
 * Skin Diseño — cuadro de diálogo con OPERADOR IA real (Claude API).
 *
 * El skin manda el historial de la conversación a `POST /__aqyra/llm` (endpoint del
 * servidor de desarrollo, clave server-side en .env) y recibe `{ reply, actions }`
 * que Claude genera por tool-calling. Lenguaje libre e instantáneo. Las acciones
 * rellenan el resumen de estructura espacial y mueven la maqueta volumétrica; la
 * estructura espacial es IFC y la caja de volumen es ayuda visual (Q2·A). El panel
 * izquierdo es el ÁRBOL de instancias IFC (model.ts) con enlace bsDD en vivo (bsdd.ts);
 * el mismo modelo alimenta la autoría IFC real. Motor/clave/futuro: ver demo/LLM.md.
 */

import { bsddClass, bsddProperties, classUri } from "./bsdd";
import { residenceGenerator, GENERATORS } from "./generators";
import { toAltoSpec } from "./c1-bridge";
import { makeFixture } from "./fixture";
import {
  buildModel, hasModel, spaceCount, columnCount, slabCount, openingCount, wallCount, stairCount, resolveGrid, buildGrid, spaceBoundaryWalls,
  type BuildingInput, type BuildingModel, type StoreyInstance, type SpaceInstance,
  type ZoneInstance, type ElementInstance, type GridResolved, type GridNode,
} from "./model";

const $ = (id: string) => document.getElementById(id)!;
const log = $("log");
const chipsBox = $("chips");
const input = $("text") as HTMLTextAreaElement;
const sendBtn = $("send") as HTMLButtonElement;
const stage = $("stage");
const emptyHint = $("emptyHint");
const NS = "http://www.w3.org/2000/svg";

// ── maqueta volumétrica (SVG isométrico con cámara) ──────────────────────────
// Dimensiones del edificio: AHORA son ESTADO que el diálogo actualiza (volumetría
// + plantas), no constantes. La caja, las plantas y la planta tipo se redibujan.
//   W = ancho (eje X) · D = fondo (eje Y) · H = alto total (eje Z)
//   NF = nº de plantas · FF = altura de piso a piso
let W = 31, D = 15.6, H = 16.5, FF = 3.2, NF = 5;
const CX = 480, CY = 410;
const COS = Math.cos(Math.PI / 6), SIN = Math.sin(Math.PI / 6);
let az = -0.5, elevK = 1.0, panX = 0, panY = 0, zoom = 1;
/** Escala base auto-encuadre: el edificio cabe en el lienzo sea cual sea su tamaño. */
function baseScale(): number {
  return Math.min(560 / Math.max(W + D, 1), 360 / Math.max(H, 1), 18);
}
const iso = (x: number, y: number, z: number): [number, number] => {
  const dx = x - W / 2, dy = y - D / 2;
  const xr = dx * Math.cos(az) - dy * Math.sin(az);
  const yr = dx * Math.sin(az) + dy * Math.cos(az);
  const s = baseScale() * zoom;
  return [CX + panX + (xr - yr) * COS * s, CY + panY + (xr + yr) * SIN * s * elevK - z * s];
};
const view = { volume: false, levels: false, grid: false, plan: false };

// ── selección: el nodo elegido en el árbol se RESALTA en el dibujo ────────────
// El árbol es la verdad IFC; al seleccionar un nodo, identificamos su geometría en
// la planta 2D y/o en la maqueta 3D. La selección es independiente de la planta
// (el footprint/posición se repite en todas), así que se casa por geometría.
type Selection =
  | { kind: "none" }
  | { kind: "space"; footprint: { x: number; y: number; w: number; d: number } }
  | { kind: "zone"; zone: string }
  | { kind: "element"; x: number; y: number; storey: number }
  | { kind: "slab"; storey: number }
  | { kind: "opening"; storey: number; cx: number; cy: number }
  | { kind: "wall"; storey: number; cx: number; cy: number }
  | { kind: "storey"; index: number };
let selected: Selection = { kind: "none" };
const HILITE = "#ffe066";
const near = (a: number, b: number, e = 1e-3): boolean => Math.abs(a - b) < e;
const sameFp = (f: { x: number; y: number; w: number; d: number }, g: { x: number; y: number; w: number; d: number }): boolean =>
  near(f.x, g.x) && near(f.y, g.y) && near(f.w, g.w) && near(f.d, g.d);
/** Área de un polígono (fórmula del agrimensor), m². */
const polyArea = (pts: [number, number][]): number => {
  let a = 0;
  for (let i = 0; i < pts.length; i++) {
    const [x1, y1] = pts[i], [x2, y2] = pts[(i + 1) % pts.length];
    a += x1 * y2 - x2 * y1;
  }
  return Math.abs(a) / 2;
};

/** Retícula estructural resuelta sobre la huella actual (o null si no hay). */
function currentGrid(): { grid: GridResolved; nodes: GridNode[] } | null {
  if (!bInput.grid) return null;
  const grid = resolveGrid(bInput.grid, { W, D });
  return { grid, nodes: buildGrid(grid) };
}

type Fp = { x: number; y: number; w: number; d: number };
/** Footprints de la planta tipo (generador activo): fuente común de planta y 3D. */
function placedSpaces(): { objectType: string; footprint: Fp; sideTag?: string }[] {
  return bInput.program
    ? (GENERATORS[bInput.program.generator]?.generate(bInput.program.params, { W, D }) ?? [])
    : residenceGenerator.generate(plan, { W, D });
}
/** Anillo (4 esquinas) de una huella proyectado a la cota z de la maqueta 3D. */
function footprintRing(f: Fp, z: number): [number, number][] {
  return [iso(f.x, f.y, z), iso(f.x + f.w, f.y, z), iso(f.x + f.w, f.y + f.d, z), iso(f.x, f.y + f.d, z)];
}

// ── planta tipo (esquema 2D acumulado a partir de acciones `space`) ───────────
type Orient = "N" | "S" | "E" | "O" | "NE" | "NO" | "SE" | "SO";
interface CoreSeed { orientation: Orient; detail?: string; }
interface PlanState {
  rooms: { count: number; layout: "both-sides" | "single-side" } | null;
  corridor: { width: number } | null;
  cores: CoreSeed[];
}
const plan: PlanState = { rooms: null, corridor: null, cores: [] };
function resetPlan(): void { plan.rooms = null; plan.corridor = null; plan.cores = []; }

function svg(name: string, attrs: Record<string, string>): SVGElement {
  const n = document.createElementNS(NS, name);
  for (const k in attrs) n.setAttribute(k, attrs[k]);
  return n as SVGElement;
}
function poly(pts: [number, number][], fill: string, stroke: string, sw = 1.2, dash = ""): void {
  stage.appendChild(svg("polygon", {
    points: pts.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" "),
    fill, stroke, "stroke-width": String(sw), "stroke-dasharray": dash, "stroke-linejoin": "round",
  }));
}
function seg(a: [number, number], b: [number, number], stroke: string, sw = 1, dash = ""): void {
  stage.appendChild(svg("line", {
    x1: a[0].toFixed(1), y1: a[1].toFixed(1), x2: b[0].toFixed(1), y2: b[1].toFixed(1),
    stroke, "stroke-width": String(sw), "stroke-dasharray": dash,
  }));
}
/** Polígono con agujeros: varios anillos (exterior + huecos), relleno con regla
 *  evenodd → los anillos interiores quedan vacíos. Cada anillo = puntos de pantalla. */
function polyPath(rings: [number, number][][], fill: string, stroke: string, sw = 1): void {
  const d = rings
    .filter((r) => r.length >= 3)
    .map((r) => "M" + r.map((p) => `${p[0].toFixed(1)},${p[1].toFixed(1)}`).join(" L") + " Z")
    .join(" ");
  stage.appendChild(svg("path", {
    d, fill, "fill-rule": "evenodd", stroke, "stroke-width": String(sw), "stroke-linejoin": "round",
  }));
}
function axisBubble(x: number, y: number, label: string, color: string): void {
  const p = iso(x, y, 0);
  stage.appendChild(svg("circle", {
    cx: p[0].toFixed(1), cy: p[1].toFixed(1), r: "10",
    fill: "#0e1116", stroke: color, "stroke-width": "1.3",
  }));
  const t = svg("text", {
    x: p[0].toFixed(1), y: p[1].toFixed(1), "text-anchor": "middle",
    "dominant-baseline": "central", fill: color, "font-size": "11", "font-weight": "700",
  });
  t.textContent = label;
  stage.appendChild(t);
}
/** Etiqueta de texto en un punto 3D (sin círculo). */
function textAt(x: number, y: number, z: number, txt: string, color: string, size = 12): void {
  const p = iso(x, y, z);
  const t = svg("text", {
    x: p[0].toFixed(1), y: p[1].toFixed(1), "text-anchor": "middle",
    "dominant-baseline": "central", fill: color, "font-size": String(size), "font-weight": "700",
  });
  t.textContent = txt;
  stage.appendChild(t);
}
/** Triada de ejes espaciales X (rojo), Y (verde, =Norte), Z (azul) en el origen. */
function drawAxes(): void {
  const L = 4.5;
  const axis = (tx: number, ty: number, tz: number, col: string, lab: string): void => {
    seg(iso(0, 0, 0), iso(tx, ty, tz), col, 2.2);
    textAt(tx, ty, tz, lab, col, 12);
  };
  axis(L, 0, 0, "#e2554f", "X");
  axis(0, L, 0, "#56b36a", "Y");
  axis(0, 0, L, "#5b8fe0", "Z");
}
/** Puntos cardinales coherentes con los ejes: +Y=N, -Y=S, +X=E, -X=O. */
function drawCardinals(): void {
  const mc = 4.5, c = "#9fb2c5";
  textAt(W / 2, D + mc, 0, "N", c, 13);
  textAt(W / 2, -mc, 0, "S", c, 13);
  textAt(W + mc, D / 2, 0, "E", c, 13);
  textAt(-mc, D / 2, 0, "O", c, 13);
}
function render(): void {
  stage.innerHTML = "";
  const empty = !view.volume && !view.plan;
  emptyHint.style.display = empty ? "flex" : "none";
  if (empty) return;
  if (view.volume) drawVolume();
  if (view.plan) renderPlan();
}

/** Maqueta volumétrica isométrica (caja + plantas + ejes), ayuda visual. */
function drawVolume(): void {
  const GLASS = "rgba(120,170,235,0.10)", EDGE = "#6f9fd8", FAINT = "#3c5170";
  const slab = (z: number, col: string, sw: number, dash = ""): void =>
    poly([iso(0, 0, z), iso(W, 0, z), iso(W, D, z), iso(0, D, z)], "none", col, sw, dash);
  poly([iso(0, 0, H), iso(W, 0, H), iso(W, D, H), iso(0, D, H)], GLASS, EDGE);
  poly([iso(0, 0, 0), iso(0, D, 0), iso(0, D, H), iso(0, 0, H)], GLASS, EDGE);
  poly([iso(0, D, 0), iso(W, D, 0), iso(W, D, H), iso(0, D, H)], GLASS, EDGE);
  for (const [x, y] of [[0, 0], [W, 0], [W, D], [0, D]] as [number, number][])
    seg(iso(x, y, 0), iso(x, y, H), EDGE, 1.2);
  slab(0, EDGE, 1.2);
  drawAxes();
  drawCardinals();
  if (view.levels) { drawFacade(); drawPartitions(); drawDivisions(); drawCores(); drawCarpentry(); drawStairs(); } // muros + carpintería + escaleras
  // forjados (IfcSlab): SUELO de cada planta 1..NF-1 (con sus huecos de núcleo, path
  // evenodd) y la CUBIERTA en NF (techo, sin huecos: cierra por arriba). Forjado/hueco
  // seleccionado, resaltado.
  const holes = placedSpaces().filter((s) => s.objectType === "Nucleo").map((s) => s.footprint);
  if (view.levels) for (let i = 1; i <= NF; i++) {
    const z = i * FF;
    const isRoof = i === NF;
    const fHoles = isRoof ? [] : holes;
    const hotSlab = selected.kind === "slab" && selected.storey === i;
    const fill = hotSlab ? "rgba(255,224,102,0.28)" : isRoof ? "rgba(150,170,205,0.18)" : "rgba(120,170,235,0.12)";
    const rings = [footprintRing({ x: 0, y: 0, w: W, d: D }, z), ...fHoles.map((f) => footprintRing(f, z))];
    polyPath(rings, fill, hotSlab ? HILITE : FAINT, hotSlab ? 2 : 1);
    for (const f of fHoles) {
      const hot = selected.kind === "opening" && selected.storey === i
        && near(selected.cx, f.x + f.w / 2) && near(selected.cy, f.y + f.d / 2);
      poly(footprintRing(f, z), "none", hot ? HILITE : "#b98a3a", hot ? 2.6 : 1, hot ? "" : "3 2");
    }
  }
  if (selected.kind === "storey") slab(selected.index * FF, HILITE, 2.4); // planta seleccionada
  const g = currentGrid();
  if (g) drawGrid3D(g.grid, g.nodes);
  else if (view.grid) drawGridSchematic();
}

/** Muros de fachada: un paño vertical por planta y lado de la huella; el seleccionado, resaltado. */
function drawFacade(): void {
  const edges: [[number, number], [number, number]][] = [
    [[0, 0], [W, 0]], [[W, 0], [W, D]], [[W, D], [0, D]], [[0, D], [0, 0]],
  ];
  for (let i = 0; i < NF; i++) {
    const z0 = i * FF, z1 = (i + 1) * FF;
    for (const [a, b] of edges) {
      const hot = selected.kind === "wall" && selected.storey === i
        && near(selected.cx, (a[0] + b[0]) / 2) && near(selected.cy, (a[1] + b[1]) / 2);
      poly(
        [iso(a[0], a[1], z0), iso(b[0], b[1], z0), iso(b[0], b[1], z1), iso(a[0], a[1], z1)],
        hot ? "rgba(255,224,102,0.32)" : "rgba(154,141,122,0.10)",
        hot ? HILITE : "#6b6354", hot ? 2 : 0.8,
      );
    }
  }
}

/** Tabiques interiores (divisorias): un paño vertical por planta a lo largo de la línea dada. */
function drawPartitions(): void {
  for (let i = 0; i < NF; i++) {
    const z0 = i * FF, z1 = (i + 1) * FF;
    for (const d of bInput.partitions ?? []) {
      const hot = selected.kind === "wall" && selected.storey === i
        && near(selected.cx, (d.start[0] + d.end[0]) / 2) && near(selected.cy, (d.start[1] + d.end[1]) / 2);
      poly(
        [iso(d.start[0], d.start[1], z0), iso(d.end[0], d.end[1], z0), iso(d.end[0], d.end[1], z1), iso(d.start[0], d.start[1], z1)],
        hot ? "rgba(255,224,102,0.32)" : "rgba(120,150,180,0.14)", hot ? HILITE : "#5a7088", hot ? 2 : 1,
      );
    }
  }
}

/** Divisorias por LINDES: paño por planta en cada arista compartida entre espacios. */
function drawDivisions(): void {
  if (bInput.program) return; // no en parking
  const lines = spaceBoundaryWalls(placedSpaces().filter((s) => s.objectType !== "Nucleo").map((s) => s.footprint));
  for (let i = 0; i < NF; i++) {
    const z0 = i * FF, z1 = (i + 1) * FF;
    for (const d of lines) {
      const hot = selected.kind === "wall" && selected.storey === i
        && near(selected.cx, (d.start[0] + d.end[0]) / 2) && near(selected.cy, (d.start[1] + d.end[1]) / 2);
      poly(
        [iso(d.start[0], d.start[1], z0), iso(d.end[0], d.end[1], z0), iso(d.end[0], d.end[1], z1), iso(d.start[0], d.start[1], z1)],
        hot ? "rgba(255,224,102,0.32)" : "rgba(120,150,180,0.12)", hot ? HILITE : "#5a7088", hot ? 2 : 0.9,
      );
    }
  }
}

/** Escaleras: un tramo por planta en cada núcleo (marca de huella + diagonal del tramo). */
function drawStairs(): void {
  for (const f of placedSpaces().filter((s) => s.objectType === "Nucleo").map((s) => s.footprint)) {
    for (let i = 0; i < NF; i++) {
      const z0 = i * FF, z1 = (i + 1) * FF;
      const hot = selected.kind === "element" && selected.storey === i && near(selected.x, f.x) && near(selected.y, f.y);
      const col = hot ? HILITE : "#8fb98f";
      poly([iso(f.x, f.y, z0), iso(f.x + f.w, f.y, z0), iso(f.x + f.w, f.y + f.d, z0), iso(f.x, f.y + f.d, z0)],
        hot ? "rgba(255,224,102,0.30)" : "rgba(143,185,143,0.12)", col, hot ? 2 : 0.8);
      seg(iso(f.x, f.y, z0), iso(f.x + f.w, f.y + f.d, z1), col, hot ? 2.4 : 1.4); // diagonal del tramo
    }
  }
}

/** Carpintería (puertas/ventanas): paño del vano (alféizar..alféizar+alto) sobre su muro. */
function drawCarpentry(): void {
  if (!(bInput.openings?.length)) return;
  const m = buildModel(bInput, { W, D });
  for (const st of m.storeys) {
    for (const e of st.elements) {
      if ((e.ifcClass !== "IfcDoor" && e.ifcClass !== "IfcWindow") || e.placement.kind !== "line") continue;
      const z0 = e.storeyIndex * FF + (e.sill ?? 0), z1 = z0 + (e.height ?? 2);
      const a = e.placement.start, b = e.placement.end;
      const hot = selected.kind === "wall" && selected.storey === e.storeyIndex
        && near(selected.cx, (a[0] + b[0]) / 2) && near(selected.cy, (a[1] + b[1]) / 2);
      const col = e.ifcClass === "IfcDoor" ? "rgba(200,150,90,0.45)" : "rgba(150,200,235,0.40)";
      poly(
        [iso(a[0], a[1], z0), iso(b[0], b[1], z0), iso(b[0], b[1], z1), iso(a[0], a[1], z1)],
        hot ? "rgba(255,224,102,0.50)" : col, hot ? HILITE : "#caa46a", hot ? 2 : 1,
      );
    }
  }
}

/** Muros de núcleo PASANTES: paño continuo de suelo a cubierta por cada lado del núcleo. */
function drawCores(): void {
  const top = NF * FF;
  for (const f of placedSpaces().filter((s) => s.objectType === "Nucleo").map((s) => s.footprint)) {
    const sides: [[number, number], [number, number]][] = [
      [[f.x, f.y], [f.x + f.w, f.y]], [[f.x + f.w, f.y], [f.x + f.w, f.y + f.d]],
      [[f.x + f.w, f.y + f.d], [f.x, f.y + f.d]], [[f.x, f.y + f.d], [f.x, f.y]],
    ];
    for (const [a, b] of sides) {
      const hot = selected.kind === "wall"
        && near(selected.cx, (a[0] + b[0]) / 2) && near(selected.cy, (a[1] + b[1]) / 2);
      poly(
        [iso(a[0], a[1], 0), iso(b[0], b[1], 0), iso(b[0], b[1], top), iso(a[0], a[1], top)],
        hot ? "rgba(255,224,102,0.34)" : "rgba(110,140,170,0.20)", hot ? HILITE : "#5a7a98", hot ? 2.2 : 1.2,
      );
    }
  }
}

/** Retícula esquemática (sin parámetros): ayuda visual de ejes 6×A/B/C. */
function drawGridSchematic(): void {
  const GU = "#e0a23a", GV = "#56b3a0", bays = 6, m = 2.8;
  for (let i = 0; i <= bays; i++) {
    const x = (W / bays) * i;
    seg(iso(x, -m, 0), iso(x, D + m, 0), GU, 1, "3 3");
    axisBubble(x, -m, String(i + 1), GU);
  }
  const letters = ["A", "B", "C"];
  [0, D / 2, D].forEach((y, idx) => {
    seg(iso(-m, y, 0), iso(W + m, y, 0), GV, 1, "3 3");
    axisBubble(-m, y, letters[idx], GV);
  });
}

/** Retícula REAL de pilares: ejes a separación real + UNA vertical por nudo (el
 *  pilar pasa las plantas). Las cabezas de pilar se marcan en la base. */
function drawGrid3D(grid: GridResolved, nodes: GridNode[]): void {
  const GU = "#e0a23a", GV = "#56b3a0", COL = "#cf7be0", m = 2.8;
  const xs = grid.axesX, ys = grid.axesY;
  const x0 = xs[0] ?? 0, x1 = xs[xs.length - 1] ?? 0, y0 = ys[0] ?? 0, y1 = ys[ys.length - 1] ?? 0;
  xs.forEach((x, ix) => {
    seg(iso(x, y0 - m, 0), iso(x, y1 + m, 0), GU, 0.8, "3 3");
    axisBubble(x, y0 - m, String(ix + 1), GU);
  });
  ys.forEach((y, iy) => {
    seg(iso(x0 - m, y, 0), iso(x1 + m, y, 0), GV, 0.8, "3 3");
    axisBubble(x0 - m, y, String.fromCharCode(65 + (iy % 26)), GV);
  });
  // pilares SEGMENTADOS por planta: un tramo por planta (TODAS, hasta la cubierta en
  // NF·FF). El resaltado ilumina SOLO el tramo de la planta del IfcColumn seleccionado.
  const nStruct = Math.max(1, NF);
  for (const nd of nodes) {
    const sel = selected.kind === "element" && near(nd.x, selected.x) && near(nd.y, selected.y) ? selected : null;
    for (let i = 0; i < nStruct; i++) {
      const hot = sel !== null && sel.storey === i;
      seg(iso(nd.x, nd.y, i * FF), iso(nd.x, nd.y, (i + 1) * FF), hot ? HILITE : COL, hot ? 3.2 : 1.4);
      if (hot) for (const z of [i * FF, (i + 1) * FF]) {
        const p = iso(nd.x, nd.y, z);
        stage.appendChild(svg("circle", { cx: p[0].toFixed(1), cy: p[1].toFixed(1), r: "4.5", fill: "none", stroke: HILITE, "stroke-width": "2" }));
      }
    }
    const base = iso(nd.x, nd.y, 0);
    stage.appendChild(svg("circle", { cx: base[0].toFixed(1), cy: base[1].toFixed(1), r: "2.2", fill: COL, stroke: "none" }));
  }
}

// ── planta tipo 2D (esquema cenital, screen-space, independiente de la cámara) ─
// Fuente de verdad determinista del esquema: la instrucción del usuario → acciones
// `space` → esta planta. N arriba (coherente con +Y=Norte). Alcance v0 firmado por
// JM: esquema en planta 2D; el mapeo a IfcSpace/IfcZone vive en visor/src/author.ts.
function rectS(x: number, y: number, w: number, h: number, fill: string, stroke: string, sw = 1): void {
  stage.appendChild(svg("rect", {
    x: x.toFixed(1), y: y.toFixed(1), width: Math.max(0, w).toFixed(1), height: Math.max(0, h).toFixed(1),
    rx: "2", fill, stroke, "stroke-width": String(sw),
  }));
}
function txtS(x: number, y: number, txt: string, color: string, size = 12, weight = "600", anchor = "start"): void {
  const t = svg("text", {
    x: x.toFixed(1), y: y.toFixed(1), "text-anchor": anchor,
    "dominant-baseline": "middle", fill: color, "font-size": String(size), "font-weight": weight,
  });
  t.textContent = txt;
  stage.appendChild(t);
}
function fmtM(m: number): string { return m.toFixed(2).replace(".", ",") + " m"; }

function renderPlan(): void {
  // panel contenedor en la esquina inferior izquierda
  const PX = 36, PY = 442, PW = 430, PH = 250;
  rectS(PX, PY, PW, PH, "rgba(14,17,22,0.86)", "#2a313c", 1);
  txtS(PX + 16, PY + 22, "Planta tipo", "#cfd8e3", 14, "700");
  txtS(PX + PW - 16, PY + 22, "N ↑", "#9fb2c5", 12, "700", "end");

  // huella del edificio (proporción W:D), N arriba
  const fx = PX + 24, fy = PY + 42, fw = PW - 48, fh = fw * (D / W);

  // los footprints los coloca el generador ACTIVO (residencia o el del programa)
  const placed = bInput.program
    ? (GENERATORS[bInput.program.generator]?.generate(bInput.program.params, { W, D }) ?? [])
    : residenceGenerator.generate(plan, { W, D });
  const grid = currentGrid();
  // la planta tipo representa lo que haya en el nivel: espacios y/o retícula
  if (placed.length === 0 && !grid) {
    rectS(fx, fy, fw, fh, "none", "#3a4759", 1.2);
    txtS(fx + fw / 2, fy + fh / 2, "describe la planta tipo o coloca la retícula…", "#5a6573", 12, "600", "middle");
    return;
  }
  rectS(fx, fy, fw, fh, "none", "#6f9fd8", 1.4); // contorno de la huella

  // dibuja cada footprint escalando [0..W]×[0..D] → inset (N arriba ⇒ Y invertida)
  const W2 = W, D2 = D;
  for (const g of placed) {
    const f = g.footprint;
    const sx = fx + (f.x / W2) * fw;
    const sw = (f.w / W2) * fw;
    const sy = fy + (1 - (f.y + f.d) / D2) * fh;
    const sh = (f.d / D2) * fh;
    const [fill, stroke] = PLAN_PAL[g.objectType] ?? PLAN_DEF;
    rectS(sx, sy, sw, sh, fill, stroke, g.objectType === "Nucleo" ? 1.4 : 1);
    // resaltado: el espacio seleccionado (por footprint) o toda su zona
    const hotSpace = selected.kind === "space" && sameFp(selected.footprint, f);
    const hotZone = selected.kind === "zone" && g.zone === selected.zone;
    if (hotSpace || hotZone) rectS(sx, sy, sw, sh, "none", HILITE, hotSpace ? 2.6 : 1.8);
    if (g.objectType === "Pasillo") {
      txtS(sx + sw / 2, sy + sh / 2, fmtM(plan.corridor?.width ?? 0), "#9fb2c5", 10.5, "600", "middle");
    } else if (g.objectType === "Nucleo" && g.sideTag) {
      txtS(sx + sw / 2, sy + sh / 2, g.sideTag, "#e7c98a", 11, "700", "middle");
    }
  }

  // retícula estructural: marca cada pilar como un cuadradito a escala en la huella
  if (grid) {
    const COL = "#cf7be0";
    const half = Math.max(2, (grid.grid.section.w / W2) * fw / 2);
    for (const nd of grid.nodes) {
      const px = fx + (nd.x / W2) * fw;
      const py = fy + (1 - nd.y / D2) * fh;
      rectS(px - half, py - half, half * 2, half * 2, COL, "#7a3f88", 0.8);
      if (selected.kind === "element" && near(nd.x, selected.x) && near(nd.y, selected.y)) {
        rectS(px - half * 1.9, py - half * 1.9, half * 3.8, half * 3.8, "none", HILITE, 2);
      }
    }
  }

  // tabiques interiores (divisorias): línea a escala en la huella
  for (const d of bInput.partitions ?? []) {
    const mid = near(selected.kind === "wall" ? selected.cx : NaN, (d.start[0] + d.end[0]) / 2)
      && near(selected.kind === "wall" ? selected.cy : NaN, (d.start[1] + d.end[1]) / 2);
    seg(
      [fx + (d.start[0] / W2) * fw, fy + (1 - d.start[1] / D2) * fh],
      [fx + (d.end[0] / W2) * fw, fy + (1 - d.end[1] / D2) * fh],
      mid ? HILITE : "#7e96b0", mid ? 3 : 2,
    );
  }

  // leyenda por objectType presente
  const present = [...new Set(placed.map((g) => g.objectType))];
  const ly = PY + PH - 14;
  let lx = PX + 16;
  for (const ot of present) {
    const [fill, stroke] = PLAN_PAL[ot] ?? PLAN_DEF;
    rectS(lx, ly - 7, 12, 12, fill, stroke, 1);
    txtS(lx + 17, ly, ot, "#8b96a5", 10.5, "500");
    lx += 17 + ot.length * 6.5 + 14;
  }
}
// paleta de planta por objectType (genérica, con color por defecto)
const PLAN_PAL: Record<string, [string, string]> = {
  Habitacion: ["rgba(120,170,235,0.14)", "#3c5170"],
  Pasillo: ["rgba(159,178,197,0.10)", "#5a6573"],
  Nucleo: ["rgba(224,162,58,0.22)", "#e0a23a"],
  PlazaAparcamiento: ["rgba(120,200,160,0.16)", "#4a8f6e"],
  Vial: ["rgba(159,178,197,0.10)", "#5a6573"],
  Rampa: ["rgba(224,162,58,0.22)", "#e0a23a"],
};
const PLAN_DEF: [string, string] = ["rgba(140,150,165,0.12)", "#5a6573"];

// ── árbol de estructura espacial (instancias IFC) ────────────────────────────
const treebody = $("treebody");
const detail = $("detail");

// El modelo se materializa de (nombres + nº plantas + planta tipo). `plan` se
// comparte por referencia con la maqueta 2D: una sola fuente de verdad.
// (Ojo: `input` es el textarea del chat; este es el modelo → `bInput`.)
const bInput: BuildingInput = { plan };
const GROUP_LABEL: Record<string, string> = { Habitacion: "Habitaciones", Pasillo: "Pasillos", Nucleo: "Núcleos" };
const EMPTY_TREE =
  `<div id="treeEmpty">El árbol de instancias IFC aparecerá aquí a medida que describas el edificio →` +
  `<br />Cada planta, habitación, pasillo, núcleo y zona será un nodo desplegable con sus atributos, Psets y enlace bsDD.</div>`;

type NodeRef =
  | { t: "project"; ifcClass: "IfcProject"; code: string; name: string }
  | { t: "site"; ifcClass: "IfcSite"; code: string; name: string; longName?: string }
  | { t: "building"; ifcClass: "IfcBuilding"; code: string; name: string; longName?: string }
  | { t: "storey"; ifcClass: "IfcBuildingStorey"; data: StoreyInstance }
  | { t: "space"; ifcClass: "IfcSpace"; data: SpaceInstance }
  | { t: "element"; ifcClass: string; data: ElementInstance }
  | { t: "zone"; ifcClass: "IfcZone"; data: ZoneInstance };

let selToken = 0;

function clsSpan(ifcClass: string): string {
  const k = ifcClass === "IfcZone" ? "zone"
    : ifcClass === "IfcSpace" ? "space"
    : ifcClass.startsWith("Ifc") && ifcClass !== "IfcBuildingStorey" && !ifcClass.startsWith("IfcProject") && !ifcClass.startsWith("IfcSite") && !ifcClass.startsWith("IfcBuilding") ? "elem"
    : "";
  return `<span class="cls ${k}">${ifcClass}</span>`;
}

/** Nodo agrupador (con triángulo y contenedor de hijos). */
function groupNode(ref: NodeRef, label: string, open: boolean): { el: HTMLDetailsElement; kids: HTMLElement } {
  const d = document.createElement("details");
  d.className = "node";
  d.open = open;
  const s = document.createElement("summary");
  s.innerHTML = `<span class="tw"></span>${clsSpan(ref.ifcClass)} <span class="nm">${escapeHtml(label)}</span>`;
  s.addEventListener("click", () => selectNode(ref, s));
  const kids = document.createElement("div");
  kids.className = "kids";
  d.appendChild(s);
  d.appendChild(kids);
  return { el: d, kids };
}

/** Sub-grupo simple (sin entidad propia), p. ej. "Habitaciones (20)". */
function plainGroup(label: string, open: boolean): { el: HTMLDetailsElement; kids: HTMLElement } {
  const d = document.createElement("details");
  d.className = "node";
  d.open = open;
  const s = document.createElement("summary");
  s.innerHTML = `<span class="tw"></span><span class="ct">${escapeHtml(label)}</span>`;
  const kids = document.createElement("div");
  kids.className = "kids";
  d.appendChild(s);
  d.appendChild(kids);
  return { el: d, kids };
}

/** Hoja clicable (instancia sin hijos). */
function leafNode(ref: NodeRef, label: string, sub: string): HTMLElement {
  const el = document.createElement("div");
  el.className = "leaf";
  el.innerHTML = `${clsSpan(ref.ifcClass)} <span class="nm">${escapeHtml(label)}</span>` + (sub ? ` <span class="ct">${escapeHtml(sub)}</span>` : "");
  el.addEventListener("click", () => selectNode(ref, el));
  return el;
}

/** Agrupa los espacios de una planta por objectType (genérico, cualquier tipología). */
function addSpaceGroups(parent: HTMLElement, spaces: SpaceInstance[]): void {
  const groups = new Map<string, SpaceInstance[]>();
  for (const sp of spaces) {
    const a = groups.get(sp.objectType) ?? [];
    a.push(sp); groups.set(sp.objectType, a);
  }
  for (const [ot, list] of groups) {
    const label = `${GROUP_LABEL[ot] ?? ot} (${list.length})`;
    const g = plainGroup(label, list.length <= 6);
    parent.appendChild(g.el);
    for (const sp of list) {
      g.kids.appendChild(leafNode({ t: "space", ifcClass: "IfcSpace", data: sp }, sp.code, sp.sideTag ?? ""));
    }
  }
}

/** Agrupa los elementos físicos de una planta por ifcClass → rama "IfcColumn (N)". */
function addElementGroups(parent: HTMLElement, elements: ElementInstance[]): void {
  if (elements.length === 0) return;
  const byClass = new Map<string, ElementInstance[]>();
  for (const e of elements) {
    const a = byClass.get(e.ifcClass) ?? [];
    a.push(e); byClass.set(e.ifcClass, a);
  }
  const wrap = plainGroup(`Elementos (${elements.length})`, true);
  parent.appendChild(wrap.el);
  for (const [cls, list] of byClass) {
    const g = plainGroup(`${cls} (${list.length})`, list.length <= 8);
    wrap.kids.appendChild(g.el);
    for (const e of list) {
      g.kids.appendChild(leafNode({ t: "element", ifcClass: e.ifcClass, data: e }, e.code, e.axis ?? ""));
    }
  }
}

function renderTree(model: BuildingModel): void {
  treebody.innerHTML = "";
  const proj = groupNode({ t: "project", ifcClass: "IfcProject", code: model.project.code, name: model.project.name }, model.project.name, true);
  treebody.appendChild(proj.el);
  const site = groupNode({ t: "site", ifcClass: "IfcSite", code: "AQ-SOL", name: model.site.name, longName: model.site.longName }, model.site.name, true);
  proj.kids.appendChild(site.el);
  const nSpaces = spaceCount(model);
  const nCols = columnCount(model);
  const nSlabs = slabCount(model);
  const nOpen = openingCount(model);
  const nWalls = wallCount(model);
  const tags = [
    nSpaces > 0 ? `${nSpaces} IfcSpace` : "",
    nCols > 0 ? `${nCols} IfcColumn` : "",
    nSlabs > 0 ? `${nSlabs} IfcSlab` : "",
    nWalls > 0 ? `${nWalls} IfcWall` : "",
    stairCount(model) > 0 ? `${stairCount(model)} IfcStair` : "",
    nOpen > 0 ? `${nOpen} IfcOpening` : "",
  ].filter(Boolean);
  const bldLabel = tags.length ? `${model.building.name} · ${tags.join(" · ")}` : model.building.name;
  const bld = groupNode({ t: "building", ifcClass: "IfcBuilding", code: "AQ-EDI", name: model.building.name, longName: model.building.longName }, bldLabel, true);
  site.kids.appendChild(bld.el);

  for (const s of model.storeys) {
    const st = groupNode({ t: "storey", ifcClass: "IfcBuildingStorey", data: s }, `${s.code} · ${s.name}`, model.storeys.length <= 3);
    bld.kids.appendChild(st.el);
    addSpaceGroups(st.kids, s.spaces);
    addElementGroups(st.kids, s.elements);
  }
  if (model.zones.length) {
    const zg = plainGroup("Zonas (IfcZone)", true);
    bld.kids.appendChild(zg.el);
    for (const z of model.zones) {
      zg.kids.appendChild(leafNode({ t: "zone", ifcClass: "IfcZone", data: z }, z.code, `${z.kind} · ${z.members.length} esp.`));
    }
  }
}

function refreshTree(): void {
  if (!hasModel(bInput)) { treebody.innerHTML = EMPTY_TREE; return; }
  renderTree(buildModel(bInput, { W, D }));
}
function resetTree(): void {
  bInput.project = bInput.site = bInput.siteLong = bInput.building = bInput.buildingLong = undefined;
  bInput.storeys = undefined;
  bInput.program = undefined;
  bInput.grid = undefined;
  bInput.partitions = undefined;
  bInput.openings = undefined;
  selected = { kind: "none" };
  treebody.innerHTML = EMPTY_TREE;
  detail.innerHTML = `<div id="detailEmpty">Selecciona un nodo del árbol para ver sus atributos, Psets y clasificación bsDD (en vivo).</div>`;
}

// ── panel de detalle del nodo + bsDD en vivo ─────────────────────────────────
function drow(k: string, v: string): string {
  return `<div class="drow"><span class="k">${escapeHtml(k)}</span><span class="v">${escapeHtml(v)}</span></div>`;
}
/** Traduce el nodo del árbol a una selección geométrica para resaltar en el dibujo. */
function selectionFor(ref: NodeRef): Selection {
  if (ref.t === "space") return { kind: "space", footprint: { ...ref.data.footprint } };
  if (ref.t === "zone") return { kind: "zone", zone: ref.data.kind };
  if (ref.t === "storey") return { kind: "storey", index: ref.data.index };
  if (ref.t === "element") {
    const pl = ref.data.placement;
    if (pl.kind === "point") return { kind: "element", x: pl.x, y: pl.y, storey: ref.data.storeyIndex };
    if (pl.kind === "line") return { kind: "wall", storey: ref.data.storeyIndex, cx: (pl.start[0] + pl.end[0]) / 2, cy: (pl.start[1] + pl.end[1]) / 2 };
    if (ref.data.ifcClass === "IfcOpeningElement") {
      const c = pl.contour;
      return { kind: "opening", storey: ref.data.storeyIndex, cx: (c[0][0] + c[2][0]) / 2, cy: (c[0][1] + c[2][1]) / 2 };
    }
    return { kind: "slab", storey: ref.data.storeyIndex };
  }
  return { kind: "none" };
}

function selectNode(ref: NodeRef, el: HTMLElement): void {
  document.querySelectorAll(".leaf.sel, summary.sel").forEach((n) => n.classList.remove("sel"));
  el.classList.add("sel");
  const token = ++selToken;

  let rows = "";
  if (ref.t === "project") rows = drow("Clase", "IfcProject") + drow("Name", ref.name) + drow("Código", ref.code);
  else if (ref.t === "site") rows = drow("Clase", "IfcSite") + drow("Name", ref.name) + (ref.longName ? drow("LongName", ref.longName) : "");
  else if (ref.t === "building") rows = drow("Clase", "IfcBuilding") + drow("Name", ref.name) + (ref.longName ? drow("LongName", ref.longName) : "");
  else if (ref.t === "storey") {
    const s = ref.data;
    rows = drow("Clase", "IfcBuildingStorey") + drow("Name", s.code) + drow("LongName", s.name) +
      drow("Elevation", `${s.elevation.toFixed(2)} m`) + drow("Espacios", String(s.spaces.length)) +
      (s.elements.length ? drow("Elementos", String(s.elements.length)) : "");
  } else if (ref.t === "space") {
    const s = ref.data;
    rows = drow("Clase", "IfcSpace") + drow("Name", s.code) + drow("LongName", s.longName) +
      drow("ObjectType", s.objectType) +
      (s.sideTag ? drow("Lado/Orient.", s.sideTag) : "") +
      drow("Zona", s.zone) +
      drow("Footprint", `${s.footprint.w.toFixed(2)}×${s.footprint.d.toFixed(2)} m`);
  } else if (ref.t === "element") {
    const e = ref.data;
    rows = drow("Clase", e.ifcClass) + drow("Name", e.code) +
      (e.predefinedType ? drow("PredefinedType", e.predefinedType) : "") +
      drow("ObjectType", e.objectType) +
      (e.axis ? drow("Eje", e.axis) : "") +
      (e.section ? drow("Sección", `${e.section.w.toFixed(2)}×${e.section.d.toFixed(2)} m`) : "") +
      (e.thickness ? drow("Espesor", `${e.thickness.toFixed(2)} m`) : "") +
      (e.width ? drow("Ancho", `${e.width.toFixed(2)} m`) : "") +
      (e.height ? drow("Altura", `${e.height.toFixed(2)} m`) : "") +
      (e.sill ? drow("Alféizar", `${e.sill.toFixed(2)} m`) : "") +
      (e.spans && e.spans[1] - e.spans[0] > 1 ? drow("Extensión", `pasante · ${e.spans[1] - e.spans[0]} plantas`) : "") +
      (e.exterior !== undefined ? drow("IsExternal", e.exterior ? "sí (fachada)" : "no (interior)") : "") +
      (e.material ? drow("Material", e.material) : "") +
      drow("Nivel", e.level) +
      (e.host ? drow("Anfitrión", e.host) : "") +
      (e.placement.kind === "point"
        ? drow("Posición", `x=${e.placement.x.toFixed(2)} · y=${e.placement.y.toFixed(2)} m`)
        : e.placement.kind === "line"
        ? drow("Longitud", `${Math.hypot(e.placement.end[0] - e.placement.start[0], e.placement.end[1] - e.placement.start[1]).toFixed(2)} m`)
        : drow("Área", `${polyArea(e.placement.contour).toFixed(1)} m²`));
  } else {
    const z = ref.data;
    rows = drow("Clase", "IfcZone") + drow("Name", z.code) + drow("LongName", z.longName) +
      drow("Uso", z.kind) + drow("Miembros", `${z.members.length} IfcSpace`);
  }

  // Resalta la selección en el dibujo y asegura que su vista esté visible.
  selected = selectionFor(ref);
  if (selected.kind === "space" || selected.kind === "zone") view.plan = true;
  else if (selected.kind === "storey" || selected.kind === "slab" || selected.kind === "opening" || selected.kind === "wall") view.volume = true;
  else if (selected.kind === "element") { view.volume = true; if (bInput.grid) view.plan = true; }
  render();

  const uri = classUri(ref.ifcClass);
  const bsddBlock = uri
    ? `<div class="sub">bsDD · clasificación (en vivo)</div>` +
      `<div class="drow"><span class="k">URI</span><span class="v"><a href="${uri}" target="_blank" rel="noopener">${ref.ifcClass}</a></span></div>` +
      `<div id="bsddDef" class="drow"><span class="k">bsDD</span><span class="v loading">consultando…</span></div>` +
      `<div class="sub">Psets por defecto (bsDD) <span id="psetState" class="loading">cargando…</span></div><div id="psets"></div>`
    : `<div class="sub none">Sin clase bsDD mapeada.</div>`;

  detail.innerHTML = `<div class="dh">${escapeHtml(ref.ifcClass)}</div>${rows}${bsddBlock}`;
  if (uri) void fillBsdd(ref.ifcClass, token);
}

async function fillBsdd(ifcClass: string, token: number): Promise<void> {
  const cls = await bsddClass(ifcClass);
  if (token !== selToken) return; // el usuario ya cambió de nodo
  const def = document.getElementById("bsddDef");
  if (def) {
    const v = def.querySelector(".v") as HTMLElement;
    v.classList.remove("loading");
    v.textContent = cls ? `${cls.name} — ${cls.definition ? cls.definition.slice(0, 90) + (cls.definition.length > 90 ? "…" : "") : "(sin definición)"}` : "no disponible (sin red/CORS)";
  }
  const props = await bsddProperties(ifcClass);
  if (token !== selToken) return;
  const state = document.getElementById("psetState");
  const box = document.getElementById("psets");
  if (state) state.textContent = props.length ? `${props.length} props` : "—";
  if (state) state.classList.remove("loading");
  if (box) {
    if (!props.length) { box.innerHTML = `<span class="none">sin propiedades por defecto disponibles</span>`; return; }
    const bySet = new Map<string, string[]>();
    for (const p of props) {
      const set = p.propertySet ?? "(sin Pset)";
      if (!bySet.has(set)) bySet.set(set, []);
      bySet.get(set)!.push(p.name);
    }
    let html = "";
    for (const [set, names] of bySet) {
      html += `<div class="sub">${escapeHtml(set)}</div>` + names.map((n) => `<span class="pill">${escapeHtml(n)}</span>`).join("");
    }
    box.innerHTML = html;
  }
}

// ── chat ─────────────────────────────────────────────────────────────────────
function bubble(text: string, who: "ai" | "user"): void {
  const m = document.createElement("div");
  m.className = `msg ${who}`;
  m.innerHTML = `<span class="who">${who === "ai" ? "Copiloto Aqyra · Claude" : "Tú"}</span>${escapeHtml(text)}`;
  log.appendChild(m);
  log.scrollTop = log.scrollHeight;
}
function escapeHtml(s: string): string {
  return s.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]!));
}
function waiting(on: boolean): void {
  let t = document.getElementById("waiting");
  if (on && !t) {
    t = document.createElement("div");
    t.id = "waiting";
    t.className = "typing";
    t.innerHTML = "Esperando al copiloto (Claude) <b>•</b><b>•</b><b>•</b>";
    log.appendChild(t);
    log.scrollTop = log.scrollHeight;
  } else if (!on && t) { t.remove(); }
}

// ── bucle de auto-revisión: lo SOLICITADO vs lo realmente COLOCADO ───────────
// El visor es la autoridad geométrica: tras dibujar, compara lo que el LLM pidió
// con lo que de verdad cupo/colocó y, si hay discrepancia, lo dice y se lo devuelve
// al LLM (entra en `messages`) para que se corrija o admita el límite.
function visorNote(text: string): void {
  const m = document.createElement("div");
  m.className = "msg ai";
  m.innerHTML = `<span class="who">🔎 Visor · comprobación</span>${escapeHtml(text)}`;
  log.appendChild(m);
  log.scrollTop = log.scrollHeight;
  messages.push({ role: "user", content: "[Visor · comprobación] " + text });
}
function selfCheck(): void {
  if (!hasModel(bInput)) return;
  const m = buildModel(bInput, { W, D });
  const st0 = m.storeys[0];
  if (!st0) return;
  const notes: string[] = [];
  const countType = (s: StoreyInstance, t: string): number => s.spaces.filter((x) => x.objectType === t).length;

  if (bInput.program?.generator === "parking-comb") {
    const params = bInput.program.params as { bays?: number; ramps?: string[]; aisle?: number; disposition?: string; bay?: { w: number; d: number } };
    const reqBays = params.bays ?? 0;
    const plazas = st0.spaces.filter((s) => s.objectType === "PlazaAparcamiento");
    const placedBays = plazas.length;
    const reqRamps = params.ramps?.length ?? 0;
    const placedRamps = countType(st0, "Rampa");
    const total = m.storeys.reduce((a, s) => a + countType(s, "PlazaAparcamiento"), 0);
    const rows = new Set(plazas.map((s) => s.footprint.y.toFixed(2))).size;
    // fondo que ocupa una fila según la disposición (en línea la plaza va girada 90°)
    const stallW = params.bay?.w ?? 2.5, stallD = params.bay?.d ?? 5.0;
    const bd = (params.disposition === "linea") ? stallW : stallD, aisle = params.aisle ?? 5.5;
    if (reqBays && placedBays < reqBays) {
      const needD = (rows + 1) * bd + rows * aisle;
      notes.push(`Pediste ${reqBays} plazas/planta; en la huella (${W}×${D} m${reqRamps ? `, ${reqRamps} rampa(s)` : ""}) caben ${placedBays} en ${rows} fila(s). Real: ${total} en ${m.storeys.length} plantas. Para ${rows + 1} filas el fondo debe ser ≥ ${needD.toFixed(1)} m.`);
    }
    if (reqRamps !== placedRamps) {
      notes.push(`Rampas pedidas ${reqRamps}, colocadas ${placedRamps}.`);
    }
  }
  if (notes.length) visorNote(notes.join(" "));
}

// ── acciones que devuelve Claude (outbox.actions) ────────────────────────────
interface Action {
  type: "summary" | "view" | "space" | "storeys" | "program" | "volume" | "columns" | "partition" | "clear" | "carpentry";
  target?: "cores" | "corridor" | "rooms" | "grid" | "partitions" | "openings" | "program"; // type=clear
  carp?: "door" | "window"; cw?: number; ch?: number;                         // type=carpentry
  key?: string; value?: string;
  show?: "volume" | "levels" | "grid" | "plan" | "reset";
  kind?: "room" | "corridor" | "core";
  count?: number; width?: number; depth?: number; height?: number;
  layout?: "both-sides" | "single-side";
  orientation?: Orient; detail?: string;
  zone?: string;
  generator?: string; bays?: number; aisle?: number; ramps?: Orient[]; // type=program
  disposition?: "bateria" | "linea";                                   // type=program (parking)
  sepX?: number; sepY?: number; secW?: number; secD?: number;          // type=columns (atajo)
  axesX?: number[]; axesY?: number[];                                  // type=columns (ejes explícitos)
  x1?: number; y1?: number; x2?: number; y2?: number;                  // type=partition (línea del tabique)
}
function runAction(a: Action): void {
  if (a.type === "summary" && a.key) {
    if (a.key === "project") bInput.project = a.value;
    else if (a.key === "site") bInput.site = a.value;
    else if (a.key === "building") bInput.building = a.value;
    refreshTree();
  }
  if (a.type === "volume") {
    if (a.width) W = a.width;     // ancho (X)
    if (a.depth) D = a.depth;     // fondo (Y)
    if (a.height) H = a.height;   // alto total (Z)
    view.volume = true;
    render();
    refreshTree();                // los footprints se reescalan a las nuevas dimensiones
  }
  if (a.type === "storeys") {
    const count = Math.max(1, Math.round(a.count ?? 1));
    const ff = a.height && a.height > 0 ? a.height : H / count;
    bInput.storeys = { count, height: ff };
    NF = count; FF = ff;
    H = NF * FF;                  // altura del edificio = plantas × altura (cubierta arriba)
    view.volume = true; view.levels = true;
    render();
    refreshTree();
  }
  if (a.type === "space") {
    bInput.program = undefined; // describir espacios de planta tipo ⇒ tipología residencia
    if (a.kind === "room") plan.rooms = { count: a.count ?? 0, layout: a.layout ?? "both-sides" };
    else if (a.kind === "corridor") plan.corridor = { width: a.width ?? 0 };
    else if (a.kind === "core") plan.cores.push({ orientation: a.orientation ?? "N", detail: a.detail });
    view.plan = true;
    render();
    refreshTree();
  }
  if (a.type === "program") {
    const ramps = a.ramps ?? (a.orientation ? [a.orientation] : undefined);
    bInput.program = {
      generator: a.generator ?? "parking-comb",
      params: { bays: a.bays ?? 0, aisle: a.aisle, ramps, disposition: a.disposition },
    };
    view.plan = view.volume = view.levels = true;
    render();
    refreshTree();
  }
  if (a.type === "columns") {
    // Ejes explícitos (axesX/axesY) ganan; si no, atajo uniforme (sepX/sepY).
    bInput.grid = {
      sepX: a.sepX, sepY: a.sepY,
      axesX: a.axesX && a.axesX.length ? a.axesX : undefined,
      axesY: a.axesY && a.axesY.length ? a.axesY : undefined,
      section: (a.secW || a.secD) ? { w: a.secW ?? 0.4, d: a.secD ?? 0.4 } : undefined,
    };
    view.volume = view.grid = view.plan = true;
    render();
    refreshTree();
  }
  if (a.type === "partition" && a.x1 !== undefined && a.y1 !== undefined && a.x2 !== undefined && a.y2 !== undefined) {
    (bInput.partitions ??= []).push({ start: [a.x1, a.y1], end: [a.x2, a.y2] });
    view.volume = view.plan = true;
    render();
    refreshTree();
  }
  if (a.type === "carpentry" && a.carp && a.x1 !== undefined && a.y1 !== undefined) {
    (bInput.openings ??= []).push({ kind: a.carp, x: a.x1, y: a.y1, width: a.cw, height: a.ch });
    view.volume = view.plan = true;
    render();
    refreshTree();
  }
  if (a.type === "clear") {
    // QUITAR (edición no solo aditiva): borra una categoría de lo ya colocado.
    if (a.target === "cores") plan.cores = [];
    else if (a.target === "corridor") plan.corridor = null;
    else if (a.target === "rooms") plan.rooms = null;
    else if (a.target === "grid") bInput.grid = undefined;
    else if (a.target === "partitions") bInput.partitions = undefined;
    else if (a.target === "openings") bInput.openings = undefined;
    else if (a.target === "program") bInput.program = undefined;
    render();
    refreshTree();
  }
  if (a.type === "view") {
    if (a.show === "reset") {
      view.volume = view.levels = view.grid = view.plan = false;
      W = 31; D = 15.6; H = 16.5; NF = 5; FF = 3.2; // dimensiones por defecto
      zoom = 1; panX = panY = 0;
      bInput.grid = undefined;
      bInput.partitions = undefined;
      selected = { kind: "none" };
      resetPlan(); resetTree();
    }
    else if (a.show === "volume") view.volume = true;
    else if (a.show === "levels") { view.volume = true; view.levels = true; }
    else if (a.show === "grid") { view.volume = true; view.grid = true; }
    else if (a.show === "plan") view.plan = true;
    render();
  }
}

// ── operador IA: el visor consulta a Claude vía /__aqyra/llm ─────────────────
interface Msg { role: "user" | "assistant"; content: string; }
const messages: Msg[] = [];
async function send(text: string): Promise<void> {
  if (!text.trim()) return;
  chipsBox.innerHTML = "";
  input.value = "";
  input.style.height = "auto";
  input.style.overflowY = "hidden";
  bubble(text, "user");
  messages.push({ role: "user", content: text });
  waiting(true);
  try {
    const r = await fetch("/__aqyra/llm", {
      method: "POST",
      headers: { "content-type": "application/json" },
      body: JSON.stringify({ messages }),
    });
    const o = await r.json();
    waiting(false);
    const reply = String(o.reply ?? "(sin respuesta)");
    bubble(reply, "ai");
    messages.push({ role: "assistant", content: reply });
    for (const a of (o.actions ?? []) as Action[]) runAction(a);
    selfCheck();
  } catch (e) {
    waiting(false);
    bubble("No pude contactar con el copiloto (¿servidor de desarrollo en marcha?): " + String(e), "ai");
  }
}
function boot(): void {
  bubble(
    "Hola 👋 Soy el copiloto de diseño de Aqyra. " +
    "Cuéntame qué edificio quieres diseñar y dónde está, y empezamos a crearlo.",
    "ai",
  );
}

// ── cámara: GIRAR (botón izq.), TRASLADAR (botón der.), zoom (rueda) ──────────
let drag: "rotate" | "pan" | null = null, lastX = 0, lastY = 0;
stage.addEventListener("mousedown", (e) => {
  const ev = e as MouseEvent;
  drag = ev.button === 2 ? "pan" : "rotate";
  lastX = ev.clientX; lastY = ev.clientY;
  ev.preventDefault();
});
stage.addEventListener("contextmenu", (e) => e.preventDefault());
window.addEventListener("mouseup", () => { drag = null; });
window.addEventListener("mousemove", (e) => {
  if (!drag) return;
  const ev = e as MouseEvent;
  const ddx = ev.clientX - lastX, ddy = ev.clientY - lastY;
  if (drag === "rotate") {
    az += ddx * 0.01;
    elevK = Math.min(1.5, Math.max(0.2, elevK - ddy * 0.004));
  } else { panX += ddx; panY += ddy; }
  lastX = ev.clientX; lastY = ev.clientY;
  render();
});
stage.addEventListener("wheel", (e) => {
  const ev = e as WheelEvent;
  ev.preventDefault();
  zoom = Math.min(3, Math.max(0.4, zoom * (ev.deltaY < 0 ? 1.1 : 0.9)));
  render();
}, { passive: false });

// textarea que crece con el texto (multilínea); Enter envía, Mayús+Enter salta línea
function autogrow(): void {
  input.style.height = "auto";
  input.style.height = Math.min(input.scrollHeight, 150) + "px";
  input.style.overflowY = input.scrollHeight > 150 ? "auto" : "hidden";
}
input.addEventListener("input", autogrow);
autogrow();
sendBtn.addEventListener("click", () => void send(input.value));
input.addEventListener("keydown", (e) => {
  const ev = e as KeyboardEvent;
  if (ev.key === "Enter" && !ev.shiftKey) { ev.preventDefault(); void send(input.value); }
});

// botones de previsión en la barra de diálogo (sin funcionalidad todavía)
$("cde").addEventListener("click", () => bubble("📁 Acceder a una carpeta del CDE — próximamente.", "ai"));
$("attach").addEventListener("click", () => bubble("📎 Adjuntar un fichero — próximamente.", "ai"));

// Hooks de desarrollo (consola del navegador). NO son export firmable (regla CEBO):
//  - aqyraToC1():   handoff del modelo al spec de alto nivel de C1 (Inc 3).
//  - aqyraFixture(): congela el caso actual como fixture golden ("caso → golden").
Object.assign(window, {
  aqyraToC1: () => toAltoSpec(buildModel(bInput, { W, D }), { ancho: W, largo: D, altura: FF }),
  aqyraFixture: (name = "caso") => makeFixture(name, structuredClone(bInput), { W, D }),
});

void boot();
