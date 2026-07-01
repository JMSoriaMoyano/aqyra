/**
 * PLAYGROUND del MODO EDICIÓN (Hito 2) — banco de pruebas en pantalla, AISLADO.
 *
 * Página aparte (`edit.html`) para probar la capa de overrides SIN tocar la skin Diseño
 * (que sigue intacta). Dos vistas sobre el MISMO modelo y la MISMA capa de datos:
 *   · 2D SVG (planta cenital) — corre YA, sin dependencias: selecciona un elemento editable
 *     y muévelo/gíralo (botones + arrastre); el dibujo sale de `buildModel` CON los overrides
 *     aplicados → ves el dato moverse de verdad.
 *   · 3D Three (gizmo) — botón que carga `EditViewport` de forma perezosa (necesita
 *     `pnpm add three`, ya declarado en package.json → `pnpm install`).
 * El override que produce cualquiera de las dos vistas es el MISMO `{dx,dy,rotDeg}` que
 * `buildModel` aplica. La IA prepara; JM prueba en pantalla y firma.
 */

import { buildModel, type BuildingInput, type ElementInstance, type Placement, type ElementOverride } from "./model";
import type { PlanContext } from "./generators";

// ── modelos de muestra (editables = rampa · puerta/ventana · escalera) ───────────
const SAMPLES: Record<string, { label: string; input: BuildingInput; ctx: PlanContext; ff: number }> = {
  parking: {
    label: "Parking SABA (rampa de acceso)",
    input: {
      project: "Parking SABA", building: "P",
      storeys: { count: 2, height: 2.5 },
      plan: { rooms: null, corridor: null, cores: [] },
      program: { generator: "parking-comb", params: { bays: 400, aisle: 6, ramps: ["N"] } },
    },
    ctx: { W: 31, D: 200 }, ff: 2.5,
  },
  residencia: {
    label: "Residencia (puerta · ventana · escalera de núcleo)",
    input: {
      project: "Residencia", building: "Bloque",
      storeys: { count: 2, height: 3 },
      plan: {
        rooms: { count: 6, layout: "both-sides" }, corridor: { width: 1.6 },
        cores: [{ orientation: "O" }],
      },
      openings: [{ kind: "door", x: 6, y: 0 }, { kind: "window", x: 18, y: 0 }],
    },
    ctx: { W: 31, D: 15.6 }, ff: 3,
  },
};
const EDITABLE = new Set(["IfcRamp", "IfcDoor", "IfcWindow", "IfcStair"]);
const NS = "http://www.w3.org/2000/svg";

// ── estado ────────────────────────────────────────────────────────────────────
let sampleKey = "parking";
let overrides: Record<string, ElementOverride> = {};
let selCode = "";

const $ = (id: string) => document.getElementById(id)!;
const svgEl = (n: string, a: Record<string, string>): SVGElement => {
  const e = document.createElementNS(NS, n);
  for (const k in a) e.setAttribute(k, a[k]);
  return e as SVGElement;
};

function model(): ReturnType<typeof buildModel> {
  const s = SAMPLES[sampleKey];
  return buildModel({ ...s.input, overrides }, s.ctx);
}
function editableElements(): ElementInstance[] {
  const seen = new Set<string>();
  const out: ElementInstance[] = [];
  for (const st of model().storeys) for (const e of st.elements) {
    if (EDITABLE.has(e.ifcClass) && !seen.has(e.code)) { seen.add(e.code); out.push(e); }
  }
  return out;
}

// ── vista 2D (planta cenital, N arriba): dibuja desde buildModel = overrides aplicados ──
const SW = 560, SH = 460, PAD = 34;
function fit(): { px: (x: number) => number; py: (y: number) => number } {
  const { W, D } = SAMPLES[sampleKey].ctx;
  const s = Math.min((SW - 2 * PAD) / W, (SH - 2 * PAD) / D);
  const ox = (SW - W * s) / 2, oy = (SH - D * s) / 2;
  return { px: (x) => ox + x * s, py: (y) => SH - (oy + y * s) };
}
function drawPlacement(svg: SVGElement, pl: Placement, hot: boolean): void {
  const { px, py } = fit();
  const col = hot ? "#ffe066" : "#e0a23a", sw = hot ? "3" : "1.6";
  if (pl.kind === "line") {
    svg.appendChild(svgEl("line", { x1: String(px(pl.start[0])), y1: String(py(pl.start[1])), x2: String(px(pl.end[0])), y2: String(py(pl.end[1])), stroke: col, "stroke-width": sw, "stroke-linecap": "round" }));
  } else if (pl.kind === "polygon") {
    svg.appendChild(svgEl("polygon", { points: pl.contour.map(([x, y]) => `${px(x)},${py(y)}`).join(" "), fill: hot ? "rgba(255,224,102,0.25)" : "rgba(224,162,58,0.18)", stroke: col, "stroke-width": sw }));
  } else {
    svg.appendChild(svgEl("rect", { x: String(px(pl.x) - 5), y: String(py(pl.y) - 5), width: "10", height: "10", fill: col, stroke: "#7a3f88", "stroke-width": "1" }));
  }
}
function render2D(): void {
  const host = $("svgbox");
  host.innerHTML = "";
  const svg = svgEl("svg", { viewBox: `0 0 ${SW} ${SH}`, width: "100%", height: "100%" });
  // contexto: huella del edificio (W×D), N arriba
  const { W, D } = SAMPLES[sampleKey].ctx;
  const { px, py } = fit();
  svg.appendChild(svgEl("rect", { x: String(px(0)), y: String(py(D)), width: String(px(W) - px(0)), height: String(py(0) - py(D)), fill: "none", stroke: "#33415588", "stroke-width": "1" }));
  svg.appendChild(svgEl("text", { x: String(SW - 12), y: "20", fill: "#9fb2c5", "font-size": "12", "text-anchor": "end" })).textContent = "N ↑";
  for (const e of editableElements()) {
    const g = svgEl("g", { "data-code": e.code, style: "cursor:grab" });
    drawPlacement(g, e.placement, e.code === selCode);
    g.addEventListener("pointerdown", (ev) => startDrag(ev as PointerEvent, e.code));
    svg.appendChild(g);
  }
  host.appendChild(svg);
}

// arrastre 2D: screen→plan por la escala del fit; actualiza dx/dy en vivo
function startDrag(ev: PointerEvent, code: string): void {
  selCode = code; syncSel();
  const { W, D } = SAMPLES[sampleKey].ctx;
  const s = Math.min((SW - 2 * PAD) / W, (SH - 2 * PAD) / D);
  const host = $("svgbox"); const rect = host.getBoundingClientRect();
  const k = SW / rect.width; // viewBox px por px de pantalla
  const start = { x: ev.clientX, y: ev.clientY };
  const base = { ...(overrides[code] ?? {}) };
  const move = (m: PointerEvent): void => {
    const ddx = (m.clientX - start.x) * k / s;     // +x pantalla → +X plan
    const ddy = -(m.clientY - start.y) * k / s;    // +y pantalla (abajo) → −Y plan (N arriba)
    overrides[code] = { ...base, dx: round2((base.dx ?? 0) + ddx), dy: round2((base.dy ?? 0) + ddy) };
    render2D(); syncReadout();
  };
  const up = (): void => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
  window.addEventListener("pointermove", move);
  window.addEventListener("pointerup", up);
}

// ── controles (botones fiables, además del arrastre) ────────────────────────────
function bump(dx: number, dy: number): void {
  if (!selCode) return;
  const o = overrides[selCode] ?? {};
  overrides[selCode] = { ...o, dx: round2((o.dx ?? 0) + dx), dy: round2((o.dy ?? 0) + dy) };
  render2D(); syncReadout(); viewport3D?.applyAndRebuild();
}
function rotate(deg: number): void {
  if (!selCode) return;
  const o = overrides[selCode] ?? {};
  overrides[selCode] = { ...o, rotDeg: round2((o.rotDeg ?? 0) + deg) };
  render2D(); syncReadout(); viewport3D?.applyAndRebuild();
}
function resetSel(): void { if (selCode) { delete overrides[selCode]; render2D(); syncReadout(); viewport3D?.applyAndRebuild(); } }

function syncSel(): void {
  ($("sel") as HTMLSelectElement).value = selCode;
  render2D(); syncReadout();
}
function syncReadout(): void {
  $("readout").textContent = JSON.stringify(overrides, null, 2) || "{}";
}
function rebuildSelect(): void {
  const sel = $("sel") as HTMLSelectElement;
  const els = editableElements();
  sel.innerHTML = els.map((e) => `<option value="${e.code}">${e.ifcClass} · ${e.code}</option>`).join("");
  if (!els.some((e) => e.code === selCode)) selCode = els[0]?.code ?? "";
  sel.value = selCode;
}

// ── vista 3D (Three) — carga perezosa para no exigir three a la vista 2D ─────────
interface Viewport3DHandle { applyAndRebuild: () => void; }
let viewport3D: Viewport3DHandle | null = null;
async function open3D(): Promise<void> {
  const box = $("threebox");
  box.style.display = "block";
  try {
    const mod = await import("./edit-viewport");
    const s = SAMPLES[sampleKey];
    const vp = new mod.EditViewport({
      input: { ...s.input, overrides }, ctx: s.ctx, ff: s.ff,
      onOverride: (code, ov) => { overrides[code] = ov; render2D(); syncReadout(); },
    });
    vp.mount(box);
    viewport3D = { applyAndRebuild: () => { /* el rebuild lo hace el panel 2D; aquí solo refresco si hiciera falta */ vp.rebuildScene(); } };
    ($("mode") as HTMLButtonElement).onclick = () => {
      const b = $("mode") as HTMLButtonElement;
      const next = b.dataset.m === "rotate" ? "translate" : "rotate";
      b.dataset.m = next; b.textContent = `Gizmo: ${next === "rotate" ? "girar" : "mover"}`;
      vp.setMode(next as "translate" | "rotate");
    };
    ($("mode") as HTMLButtonElement).style.display = "inline-block";
    $("threehint").textContent = "Three cargado · clic para seleccionar, arrastra el gizmo, suelta para fijar el override.";
  } catch (err) {
    $("threehint").textContent = "No se pudo cargar Three. Ejecuta `pnpm install` en publico/ (three ya está en package.json). Detalle: " + (err as Error).message;
  }
}

const round2 = (x: number): number => Math.round(x * 100) / 100;

// ── arranque ────────────────────────────────────────────────────────────────────
function boot(): void {
  const samp = $("sample") as HTMLSelectElement;
  samp.innerHTML = Object.entries(SAMPLES).map(([k, v]) => `<option value="${k}">${v.label}</option>`).join("");
  samp.value = sampleKey;
  samp.onchange = () => { sampleKey = samp.value; overrides = {}; viewport3D = null; $("threebox").innerHTML = ""; $("threebox").style.display = "none"; ($("mode") as HTMLElement).style.display = "none"; rebuildSelect(); render2D(); syncReadout(); };
  ($("sel") as HTMLSelectElement).onchange = (e) => { selCode = (e.target as HTMLSelectElement).value; render2D(); syncReadout(); };
  $("up").onclick = () => bump(0, 0.5);
  $("down").onclick = () => bump(0, -0.5);
  $("left").onclick = () => bump(-0.5, 0);
  $("right").onclick = () => bump(0.5, 0);
  $("rotL").onclick = () => rotate(15);
  $("rotR").onclick = () => rotate(-15);
  $("reset").onclick = resetSel;
  $("open3d").onclick = () => void open3D();
  rebuildSelect();
  render2D();
  syncReadout();
}
boot();
