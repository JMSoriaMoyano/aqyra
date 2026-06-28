import { defineAqyraViewer, configureAqyra, TAG, dataStateStyle } from "@aqyra/embed";
import type { Combination, DataState, ResultGroup, StructuralModel } from "@aqyra/embed";
import { CalcServiceError, qaGroup, signGroup, solveModel, type ServiceMeta } from "./calc-service";

configureAqyra({ wasmPath: "/" });
defineAqyraViewer();

type RGBA = { r: number; g: number; b: number; a: number };
type Psets = Record<string, Record<string, unknown>>;
type ClassRow = { ifcType: string; count: number };
type ViewerEl = HTMLElement & {
  load(x: unknown): Promise<Array<{ name: string }>>;
  getProperties(globalId: string): Promise<{ globalId: string; psets: Psets }>;
  on(ev: string, cb: (p: unknown) => void): () => void;
  setVisibilityByClass(c: string, v: boolean): void;
  setColorByClass(c: string, color: RGBA): void;
  classes(): ClassRow[];
  showAll(): void;
  resetColors(): void;
  spatialTree(): Promise<Array<{ name: string; modelID: number; root: SNode }>>;
  isolateByExpressIds(modelID: number, ids: number[]): void;
  proposeSpatialFix(kind?: "cota" | "estacion"): Promise<SFix[]>;
  applySpatialFix(fixes: SFix[]): Promise<Array<{ name: string; bytes: Uint8Array }>>;
  countByClass(ifcClass: string, storeyQuery?: string): Promise<number>;
  // Pre-proceso (V2)
  showStructural(): Promise<{ nodes: number; members: number; surfaces: number; surfacesNonPlanar: number; surfacesThick: number; surfacesSkewed: number; coresClosed: number; coresOpen: number }>;
  memberOfSelection(): { id: string; nodeStart: string; nodeEnd: string } | undefined;
  baseNodeOf(memberId: string): string | undefined;
  setSupportAtNode(nodeId: string): void;
  addDistributedLoad(memberId: string, value: number, dir?: "x" | "y" | "z", caseId?: string): string;
  setSurfaceKindByType(ifcPrefix: string, kind: "diaphragm" | "shell"): number;
  setSurfaceKindForSelection(kind: "diaphragm" | "shell"): boolean;
  showCores(): Array<{ id: string; A: number; Agross: number; hollow: boolean; Ix: number; Iy: number; J: number; thickness: number }>;
  showCoreShells(): { closed: number; open: number };
  corePickHandler: ((coreId: string) => void) | null;
  exportStructuralIfc(): { name: string; bytes: Uint8Array } | undefined;
  // Estado de dato (V3 · D-021)
  setDataState(state: DataState | null): void;
  dataState(): DataState | null;
  // Post-proceso (V3 · D-022)
  showResultGroup(rg: ResultGroup, opts?: { scale?: number }): { critical: string[]; notPassing: string[] };
  clearResults(): void;
  pre: {
    listSupports(): unknown[];
    listLoads(): unknown[];
    listCombinations(): Array<{ id: string; name: string; expression: string }>;
    getStructuralModel(): Promise<StructuralModel>;
  };
};

type SFix = { modelID: number; expressId: number; name?: string; ifcType: string; fromStorey?: string; toStorey: string; toStoreyExpressId: number };

type SNode = { expressId: number; ifcType: string; name?: string; globalId?: string; children: SNode[] };

const $ = (id: string): HTMLElement => document.getElementById(id)!;
const app = $("app");
const hint = $("hint");
const toastEl = $("toast");
const pop = $("pop");
const propsEl = $("props");
const cmd = $("cmd") as HTMLInputElement;
const fileInput = $("file") as HTMLInputElement;
const treePanel = $("tree");
const treeBtn = $("treeBtn");

const el = document.createElement(TAG) as ViewerEl;
app.appendChild(el);

// Cartel de aviso PERSISTENTE (p. ej. superficies no-planas / núcleo sin descomponer).
// Cartel de aviso OBLIGATORIO (sin ✕): solo desaparece al RESOLVER el tipo de modelado.
const warnBanner = document.createElement("div");
warnBanner.style.cssText =
  "position:fixed;top:12px;left:50%;transform:translateX(-50%);z-index:60;background:rgba(190,40,50,.94);color:#fff;font:13px/1.4 system-ui,sans-serif;padding:8px 14px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.45);display:none;max-width:82vw;text-align:center;";
document.body.appendChild(warnBanner);
function setWarn(text: string | null): void {
  warnBanner.textContent = text ?? "";
  warnBanner.style.display = text ? "block" : "none";
}

// ── Estado de dato (V3 · D-021): chip (en el visor) + cartel persistente + leyenda ──
// El chip y la marca de agua los pinta el VISOR (cebo). Aquí la skin gobierna el
// cartel persistente (reutiliza warnBanner) y la leyenda estado→color. El verde
// «certificado» solo lo acuña el flujo de firma de privado/ (no existe en el cebo).
let dataBannerActive = false;
function setDataStateUI(state: DataState | null): void {
  el.setDataState(state);
  if (state === "computed" || state === "qa-passed") {
    const s = dataStateStyle(state);
    setWarn(`⚠ Resultado ${s.label} — cálculo sin firma de JM (D-021). El visor NUNCA lo presenta como verificado.`);
    dataBannerActive = true;
  } else if (dataBannerActive) {
    setWarn(null); // retira solo el cartel de estado, no los avisos de modelado
    dataBannerActive = false;
  }
}

const STATE_INFO: Array<{ state: DataState; desc: string }> = [
  { state: "proposal", desc: "input autorado/derivado · editable" },
  { state: "computed", desc: "el motor calculó · 0 llaves · NO es verdad" },
  { state: "qa-passed", desc: "1.ª llave: QA independiente (PyNite)" },
  { state: "verified-signed", desc: "2.ª llave: firma de JM · contractual" },
];
function showDataStateLegend(): void {
  propsEl.style.display = "block";
  let html =
    "<span class='x' id='px'>✕</span><div class='hd'>Estado de dato (dos llaves · D-021)</div>" +
    "<div class='muted'>Solo VERIFICADO·firma JM recibe el trato certificado (verde/limpio). Todo lo demás se ve provisional.</div>";
  for (const { state, desc } of STATE_INFO) {
    const s = dataStateStyle(state);
    html +=
      `<div class='crow'><span style='display:inline-block;width:14px;height:14px;border-radius:3px;background:${s.color};border:1px solid rgba(255,255,255,.3)'></span>` +
      `<span class='clabel' data-state='${state}' title='Previsualizar este estado en el chip'>${s.label}</span>` +
      `<span class='muted' style='flex:1'> · ${desc} · ISO ${s.iso}</span></div>`;
  }
  html += "<div class='muted'>Clic en una etiqueta para previsualizar su chip/marca en el visor.</div>";
  propsEl.innerHTML = html;
  $("px").addEventListener("click", () => (propsEl.style.display = "none"));
  propsEl.querySelectorAll<HTMLElement>("[data-state]").forEach((node) => {
    node.style.cursor = "pointer";
    node.addEventListener("click", () => {
      const st = node.getAttribute("data-state") as DataState;
      setDataStateUI(st);
      toast(`Previsualización: estado «${dataStateStyle(st).label}». ${st === "verified-signed" ? "Trato certificado (solo lo acuña la firma de JM)." : "Provisional: marca de agua activa."}`);
    });
  });
}

// Etiquetas PERSISTENTES por núcleo (una por columna-cajón), cerrables con ✕.
type CoreInfo = { id: string; A: number; Agross: number; hollow: boolean; Ix: number; Iy: number; J: number; thickness: number };
const coreCards = new Map<string, HTMLElement>();
function clearCoreCards(): void {
  for (const c of coreCards.values()) c.remove();
  coreCards.clear();
}
function showCoreCard(c: CoreInfo): void {
  const ex = coreCards.get(c.id);
  if (ex) {
    ex.style.outline = "2px solid #fff";
    window.setTimeout(() => (ex.style.outline = ""), 600);
    return;
  }
  const card = document.createElement("div");
  card.style.cssText =
    "position:fixed;right:12px;z-index:60;background:rgba(120,40,170,.96);color:#fff;font:12px/1.5 ui-monospace,monospace;padding:10px 28px 10px 12px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.5);max-width:46vw;white-space:pre;";
  card.style.top = 80 + coreCards.size * 132 + "px";
  const x = document.createElement("span");
  x.textContent = "✕";
  x.style.cssText = "position:absolute;top:6px;right:10px;cursor:pointer;opacity:.85;";
  x.onclick = () => {
    card.remove();
    coreCards.delete(c.id);
  };
  const body = document.createElement("div");
  body.textContent =
    `Núcleo ${c.id} — columna-cajón (PROPUESTA)\n` +
    `${c.hollow ? "sección HUECA" : "sección bruta"} · t=${c.thickness} m\n` +
    `A  = ${c.A.toFixed(2)} m²   (bruta ${c.Agross.toFixed(2)})\n` +
    `Ix = ${c.Ix.toFixed(2)}   Iy = ${c.Iy.toFixed(2)}  m⁴\n` +
    `J  = ${c.J.toFixed(2)} m⁴   (Bredt)`;
  card.appendChild(x);
  card.appendChild(body);
  document.body.appendChild(card);
  coreCards.set(c.id, card);
}
let lastCores: CoreInfo[] = [];
el.corePickHandler = (id) => {
  const c = lastCores.find((x) => x.id === id);
  if (c) showCoreCard(c);
};

let lastSel: { globalId?: string; ifcType?: string } = {};
let lastPointer: [number, number] = [window.innerWidth / 2, window.innerHeight / 2];

// Pre-proceso (V2): deriva el analítico una vez y lo cachea (idempotente).
let coresResolved = false; // true cuando el ingeniero ya eligió cómo modelar los núcleos no-planos
type Analytic = { nodes: number; members: number; surfaces: number; surfacesNonPlanar: number; surfacesThick: number; surfacesSkewed: number; coresClosed: number; coresOpen: number };
let analytic: Analytic | null = null;
async function ensureAnalytic(): Promise<Analytic> {
  if (!analytic) analytic = await el.showStructural();
  return analytic;
}

const norm = (s: string): string => s.toLowerCase().normalize("NFD").replace(/[̀-ͯ]/g, "");

const CLASS_SYN: Array<[RegExp, string]> = [
  [/vigas?|jacenas?|dinteles?/, "IFCBEAM"],
  [/pilares?|columnas?|soportes?/, "IFCCOLUMN"],
  [/muros?|paredes?|pantallas?/, "IFCWALL"],
  [/forjados?|losas?|placas?/, "IFCSLAB"],
  [/zapatas?|cimentaci|cimientos?/, "IFCFOOTING"],
  [/pilotes?/, "IFCPILE"],
  [/escaleras?/, "IFCSTAIR"],
  [/cubiertas?/, "IFCROOF"],
];

const COLORS: Record<string, [number, number, number]> = {
  rojo: [1, 0.2, 0.2], verde: [0.2, 0.8, 0.3], azul: [0.2, 0.5, 0.95], amarillo: [0.95, 0.85, 0.2],
  naranja: [1, 0.55, 0.1], gris: [0.6, 0.6, 0.6], blanco: [1, 1, 1], negro: [0.12, 0.12, 0.12], morado: [0.6, 0.3, 0.8],
};

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = parseInt(hex.slice(1), 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}
function present(): string[] {
  return el.classes().map((c) => c.ifcType);
}
function resolveClass(t: string): string | undefined {
  const p = present();
  for (const [re, cls] of CLASS_SYN) if (re.test(t) && p.includes(cls)) return cls;
  const up = t.toUpperCase();
  return p.find((c) => up.includes(c));
}

let toastTimer = 0;
function toast(msg: string): void {
  toastEl.textContent = msg;
  toastEl.style.display = "block";
  window.clearTimeout(toastTimer);
  toastTimer = window.setTimeout(() => (toastEl.style.display = "none"), 3800);
}

// --- historial de estado (deshacer) ---
type Snap = { vis: Record<string, boolean>; col: Record<string, [number, number, number] | undefined> };
let cur: Snap = { vis: {}, col: {} };
const history: Snap[] = [];
const clone = (s: Snap): Snap => ({ vis: { ...s.vis }, col: { ...s.col } });
function snapshot(): void {
  history.push(clone(cur));
  if (history.length > 60) history.shift();
}
function applyCur(): void {
  el.resetColors();
  for (const c of present()) {
    el.setVisibilityByClass(c, cur.vis[c] ?? true);
    const k = cur.col[c];
    if (k) el.setColorByClass(c, { r: k[0], g: k[1], b: k[2], a: 1 });
  }
}
function undo(): void {
  const prev = history.pop();
  if (!prev) {
    toast("No hay nada que deshacer");
    return;
  }
  cur = prev;
  applyCur();
  toast("Estado anterior");
}

// --- mutaciones (registran historial) ---
function doIsolate(cls: string): void {
  snapshot();
  for (const c of present()) {
    const v = c === cls;
    el.setVisibilityByClass(c, v);
    cur.vis[c] = v;
  }
  toast(`Aislado: ${cls}`);
}
function doHide(cls: string): void {
  snapshot();
  el.setVisibilityByClass(cls, false);
  cur.vis[cls] = false;
  toast(`Oculto: ${cls}`);
}
function doColor(cls: string, rgb: [number, number, number], name: string): void {
  snapshot();
  el.setColorByClass(cls, { r: rgb[0], g: rgb[1], b: rgb[2], a: 1 });
  cur.col[cls] = rgb;
  toast(`${cls} en ${name}`);
}
function doShowAll(): void {
  snapshot();
  el.showAll();
  for (const c of present()) cur.vis[c] = true;
  toast("Modelo completo visible");
}
function doResetColors(): void {
  snapshot();
  el.resetColors();
  cur.col = {};
  toast("Colores originales");
}
function doSetVisible(cls: string, v: boolean): void {
  snapshot();
  el.setVisibilityByClass(cls, v);
  cur.vis[cls] = v;
  toast(v ? `Visible: ${cls}` : `Oculto: ${cls}`);
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}
function openProps(sel: { globalId?: string; ifcType?: string }): void {
  if (!sel.globalId) return;
  propsEl.style.display = "block";
  const head = `<span class='x' id='px'>✕</span><div class='hd'>${sel.ifcType ?? "Elemento"}</div><div class='muted'>${sel.globalId}</div>`;
  propsEl.innerHTML = head + "<div class='muted'>cargando…</div>";
  $("px").addEventListener("click", () => (propsEl.style.display = "none"));
  el.getProperties(sel.globalId)
    .then((data) => {
      let html = head;
      const names = Object.keys(data.psets);
      for (const ps of names) {
        html += `<div class='ps'>${ps}</div>`;
        for (const k of Object.keys(data.psets[ps])) {
          html += `<div class='kv'><span>${k}</span><b>${fmt(data.psets[ps][k])}</b></div>`;
        }
      }
      if (names.length === 0) html += "<div class='muted'>Sin Psets</div>";
      propsEl.innerHTML = html;
      $("px").addEventListener("click", () => (propsEl.style.display = "none"));
    })
    .catch((e) => {
      propsEl.innerHTML = head + "<div class='muted'>Error: " + String(e) + "</div>";
      $("px").addEventListener("click", () => (propsEl.style.display = "none"));
    });
}

function showClasses(): void {
  const rows = el.classes();
  propsEl.style.display = "block";
  propsEl.innerHTML = "<span class='x' id='px'>✕</span><div class='hd'>Clases IFC (" + rows.length + ")</div>";
  $("px").addEventListener("click", () => (propsEl.style.display = "none"));
  if (rows.length === 0) {
    const m = document.createElement("div");
    m.className = "muted";
    m.textContent = "Carga un modelo primero";
    propsEl.appendChild(m);
    return;
  }
  for (const { ifcType, count } of rows) {
    const row = document.createElement("div");
    row.className = "crow";
    const col = document.createElement("input");
    col.type = "color";
    col.title = "Color";
    col.addEventListener("input", () => {
      const c = hexToRgb(col.value);
      doColor(ifcType, [c.r, c.g, c.b], col.value);
    });
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = true;
    cb.title = "Visible";
    cb.addEventListener("change", () => doSetVisible(ifcType, cb.checked));
    const label = document.createElement("span");
    label.className = "clabel";
    label.title = "Aislar esta clase";
    label.textContent = `${ifcType} (${count})`;
    label.addEventListener("click", () => doIsolate(ifcType));
    row.append(col, cb, label);
    propsEl.appendChild(row);
  }
}

// ── Post-proceso (V3 · D-022): deformada + aprovechamiento, bajo dos llaves ──────
// Los números REALES vienen del SERVICIO privado (POST /solve·/qa·/sign). El visor
// (cebo) sigue sin servidor para VER; solo este post llama por fetch. Si el servicio
// NO está arrancado, se cae a un ResultGroup ILUSTRATIVO (DEMO) para enseñar el
// render y el flujo de estado, avisando claramente de que NO es un cálculo.
let postModel: StructuralModel | null = null;       // modelo analítico serializado
let postCombos: Combination[] = [];                 // combinaciones enviadas al servicio
let postGroup: ResultGroup | null = null;           // grupo activo (estado actual de las llaves)
let postMeta: ServiceMeta | null = null;            // meta de gobierno del servicio (provisional/independiente)
let postSource: "servicio" | "demo" = "servicio";   // origen del grupo pintado
function buildDemoResultGroup(model: StructuralModel, state: DataState): ResultGroup {
  const nodes = model.nodes.map((n, i) => ({
    nodeId: n.id,
    ux: 0, uy: 0, uz: -(0.6 + (i % 5) * 0.25), // flecha ilustrativa (−Z)
    rx: 0, ry: 0, rz: 0,
  }));
  const members = model.members.map((m, i) => {
    const u = 0.45 + ((i * 37) % 80) / 100; // 0.45..1.24 determinista
    return { memberId: m.id, stations: [], utilization: u, governing: "demo", passes: u <= 1 };
  });
  return { id: `RG-DEMO-${state}`, combinationId: "ELU1", state, members, nodes, surfaces: [] };
}

const resultPanel = document.createElement("div");
resultPanel.style.cssText =
  "position:fixed;right:12px;bottom:84px;z-index:60;background:rgba(20,24,32,.96);color:#fff;font:12px/1.5 system-ui,sans-serif;padding:10px 12px;border-radius:8px;box-shadow:0 2px 12px rgba(0,0,0,.5);display:none;max-width:48vw;";
document.body.appendChild(resultPanel);

// Pinta un ResultGroup (real o demo) y cablea los botones de las dos llaves.
function renderResultPanel(rg: ResultGroup): void {
  postGroup = rg;
  setDataStateUI(rg.state);                                 // chip + marca de agua (cebo)
  const { critical, notPassing } = el.showResultGroup(rg);
  const s = dataStateStyle(rg.state);
  const key = rg.state === "computed" ? "0 llaves" : rg.state === "qa-passed" ? "1.ª llave (QA)" : rg.state === "verified-signed" ? "2.ª llaves (firma JM)" : "—";
  const origen = postSource === "servicio"
    ? `números REALES${postMeta ? " · " + postMeta.producer : ""}`
    : "datos DEMO (servicio no disponible)";
  const aviso = postSource === "servicio" && postMeta && postMeta.provisional
    ? `<div style='margin-top:4px;color:#e8b045'>⚠ ${postMeta.warning}</div>`
    : "";
  resultPanel.innerHTML =
    `<div style='font-weight:600;margin-bottom:6px'>Post-proceso · <span style='color:${s.color}'>${s.label}</span> <span style='opacity:.7'>(${key})</span></div>` +
    `<div style='opacity:.85'>Deformada coloreada por aprovechamiento · ${origen}.<br>` +
    `Al límite (&gt;0,9): <b>${critical.length}</b> · No cumplen (&gt;1): <b>${notPassing.length}</b></div>` +
    aviso +
    `<div style='margin-top:8px;display:flex;gap:6px;flex-wrap:wrap'></div>`;
  const row = resultPanel.lastElementChild as HTMLElement;
  const mkBtn = (label: string, fn: () => void, disabled = false): void => {
    const b = document.createElement("button");
    b.textContent = label;
    b.style.cssText = "cursor:pointer;border:0;border-radius:6px;padding:6px 9px;font:12px system-ui;background:#2b3442;color:#fff;" + (disabled ? "opacity:.4;cursor:default" : "");
    if (!disabled) b.onclick = fn;
    row.appendChild(b);
  };
  // Las dos llaves: QA solo desde `computed`; firma solo desde `qa-passed`. El verde
  // NUNCA se alcanza re-pintando: lo acuña /sign (servicio privado).
  mkBtn("Pasar QA · 1.ª llave", () => void passQA(), rg.state !== "computed");
  mkBtn("Firmar (JM) · 2.ª llave", () => void signResult(), rg.state !== "qa-passed");
  mkBtn("Quitar", () => { el.clearResults(); resultPanel.style.display = "none"; });
  resultPanel.style.display = "block";
}

// «deformada»/«post-proceso» → POST /solve (real). Fallback a DEMO si no hay servicio.
async function startPostproceso(): Promise<void> {
  await ensureAnalytic();
  postModel = await el.pre.getStructuralModel();
  if (!postModel.members.length) { toast("Deriva primero el modelo analítico ('modelo analítico')."); return; }
  postCombos = el.pre.listCombinations().map((c) => ({ id: c.id, name: c.name, limitState: "ULS", terms: {}, expression: c.expression }));
  try {
    const r = await solveModel(postModel, postCombos);
    postSource = "servicio";
    postMeta = r.meta;
    renderResultPanel(r.groups[0]);                          // nace `computed`: chip rojo + marca de agua
    const sm = r.summary[0];
    toast(`Post-proceso REAL (${r.meta.producer}): ${sm.notPassing} no cumplen, ${sm.atLimit} al límite. Sin firmar.`);
  } catch {
    postSource = "demo";
    postMeta = null;
    renderResultPanel(buildDemoResultGroup(postModel, "computed"));
    toast("Servicio de cálculo no disponible → datos DEMO. Arranca el servicio para números reales.");
  }
}

// 1.ª llave: POST /qa. qa-passed eleva a ámbar; qa-fail bloquea (discrepancia expuesta).
async function passQA(): Promise<void> {
  if (!postModel || !postGroup) return;
  if (postSource === "demo") { renderResultPanel(buildDemoResultGroup(postModel, "qa-passed")); return; }
  try {
    const r = await qaGroup(postModel, postCombos, postGroup);
    if (r.verdict === "qa-passed" && r.group) {
      renderResultPanel(r.group);
      toast(`QA · 1.ª llave puesta${r.meta.independent ? "" : " (provisional: QA no independiente aún)"}.`);
    } else {
      toast(`QA-FAIL — bloqueo: ${r.report.discrepancies.slice(0, 2).join(" · ")}. No se eleva; la discrepancia queda expuesta.`);
    }
  } catch (e) {
    toast(`Error en la QA: ${e instanceof Error ? e.message : String(e)}`);
  }
}

// 2.ª llave: POST /sign (firma de JM). Único camino al VERDE. Exige qa-passed (409 si no).
async function signResult(): Promise<void> {
  if (!postGroup) return;
  if (postSource === "demo") { if (postModel) renderResultPanel(buildDemoResultGroup(postModel, "verified-signed")); return; }
  try {
    const r = await signGroup(postGroup, "JM");
    renderResultPanel(r.group);
    toast(`Firmado (JM) · ${r.record.timestamp}. El viraje a VERDE solo lo acuña la firma.`);
  } catch (e) {
    const msg = e instanceof CalcServiceError && e.status === 409
      ? "no se puede firmar sin la 1.ª llave (pasa la QA primero)"
      : e instanceof Error ? e.message : String(e);
    toast(`No firmado: ${msg}`);
  }
}

// --- menú contextual ---
el.on("selection-changed", (p) => {
  const sel = p as { globalId?: string; ifcType?: string };
  lastSel = sel;
  if (!sel.globalId) {
    pop.style.display = "none";
    return;
  }
  const cls = sel.ifcType ?? "OTROS";
  pop.innerHTML = `<span class='x' id='popx'>✕</span><div class='t'>${cls}</div>`;
  $("popx").addEventListener("click", () => (pop.style.display = "none"));
  const add = (label: string, fn: (() => void) | null): void => {
    const b = document.createElement("button");
    b.textContent = label;
    if (fn) b.addEventListener("click", () => { fn(); pop.style.display = "none"; });
    else b.disabled = true;
    pop.appendChild(b);
  };
  add("Ver propiedades (Psets)", () => openProps(sel));
  add(`Aislar ${cls}`, () => doIsolate(cls));
  add(`Ocultar ${cls}`, () => doHide(cls));
  add("Esfuerzos / deformada · V3 (no firmado aún)", null);
  pop.style.left = Math.min(lastPointer[0], window.innerWidth - 210) + "px";
  pop.style.top = Math.min(lastPointer[1], window.innerHeight - 200) + "px";
  pop.style.display = "block";
});

window.addEventListener("pointerup", (e) => { lastPointer = [e.clientX, e.clientY]; });
window.addEventListener("pointerdown", (e) => {
  if (e.target instanceof Node && !pop.contains(e.target)) pop.style.display = "none";
});

// --- barra de comandos (stub NL → contrato) ---
function runCommand(raw: string): void {
  const t = norm(raw.trim());
  if (!t) return;
  if (/sanea|saneamiento|reasigna|corrige|higiene|arregla/.test(t)) {
    const kind = /estacion|\bpk\b|trazado|alineaci|alignment|infra|carretera|puente|ferrocarril/.test(t) ? "estacion" : "cota";
    void runSaneamiento(kind);
    return;
  }
  if (/cuant[oa]s/.test(t)) {
    const cls = resolveClass(t);
    if (!cls) {
      toast("¿De qué elementos? p. ej. '¿cuántas vigas hay?'");
      return;
    }
    let storey: string | undefined;
    const sm = t.match(/(?:planta|piso|nivel)\s+([\w-]+)/) ?? t.match(/\ben\s+(.+?)\??$/);
    if (sm) storey = sm[1];
    void el.countByClass(cls, storey).then((n) => toast(`${n} ${cls}${storey ? " en " + storey : ""}`));
    return;
  }
  if (/arbol|estructura|plantas?/.test(t)) {
    void toggleTree();
    return;
  }
  if (/deshacer|deshaz|vuelve|volver|retrocede|atras|estado anterior/.test(t)) {
    undo();
    return;
  }
  if (/(colores?\s+original)|original.*color|(resetea|restaura|quita).*color/.test(t)) {
    doResetColors();
    return;
  }
  if (/(muestra|ensena|ver)\s+todo|todo el modelo|modelo completo|reset|reinicia/.test(t)) {
    setWarn(null);
    coresResolved = false;
    clearCoreCards();
    doShowAll();
    return;
  }
  if (/\bais(la|lar)\b/.test(t)) {
    const c = resolveClass(t);
    if (c) doIsolate(c);
    else if (/seleccion|esto|este/.test(t) && lastSel.ifcType) doIsolate(lastSel.ifcType);
    else toast("¿Qué aíslo? p. ej. 'aísla las vigas'");
    return;
  }
  if (/(oculta|esconde|quita)/.test(t)) {
    const c = resolveClass(t);
    if (c) doHide(c);
    else toast("¿Qué oculto? p. ej. 'oculta los muros'");
    return;
  }
  if (/(colorea|pinta|color)/.test(t)) {
    const c = resolveClass(t);
    const cn = Object.keys(COLORS).find((k) => t.includes(k));
    if (c && cn) doColor(c, COLORS[cn], cn);
    else toast("Ej: 'colorea las vigas de rojo'");
    return;
  }
  if (/inventario|clases/.test(t)) {
    showClasses();
    return;
  }
  if (/propiedad|psets?|que es|informacion|info/.test(t)) {
    if (lastSel.globalId) openProps(lastSel);
    else toast("Selecciona un elemento primero");
    return;
  }
  if (/estado de dato|leyenda|dos llaves|estados? de verificaci/.test(t)) {
    showDataStateLegend();
    return;
  }
  if (/deformad|esfuerzo|aprovecha|momento|cortante|axil|tensi|flecha|combinaci|\belu\b|\bels\b|cumpl|post.?proces/.test(t)) {
    void startPostproceso(); // POST /solve (real) → chip rojo «NO VERIFICADO»; fallback DEMO si no hay servicio
    return;
  }
  // Exportar el IFC con el anejo Aqyra (write-back de cargas/apoyos).
  if (/(export|descarg|guard)/.test(t) && /(analitic|carga|apoyo|anejo|pre)/.test(t)) {
    const out = el.exportStructuralIfc();
    if (out) { downloadIfc(out.name, out.bytes); toast("IFC con el anejo Aqyra (cargas/apoyos) descargado · reábrelo y siguen ahí."); }
    else toast("Aún no hay cargas/apoyos que exportar: autora alguno primero.");
    return;
  }
  // Núcleo como 4 LÁMINAS cosidas (caras conectadas en esquinas). Antes que columna/superficies.
  if (/4\s*l[aá]minas|\bcose\b|cosid/.test(t)) {
    void ensureAnalytic().then(() => {
      const gp = el.showCoreShells();
      if (gp.closed + gp.open === 0) { toast("No hay núcleos por caras que coser en este modelo (núcleo en un solo elemento → usa 'columna-cajón')."); return; }
      coresResolved = true;
      setWarn(null);
      toast(`Núcleos cosidos en láminas: ${gp.closed} cerrados (teal), ${gp.open} abiertos/U (ámbar). Caras conectadas en las esquinas.`);
    });
    return;
  }
  // Núcleo como COLUMNA-CAJÓN equivalente (alternativa a las 4 láminas). Antes que superficies.
  if (/columna|caj[oó]n/.test(t)) {
    void ensureAnalytic().then(() => {
      lastCores = el.showCores();
      if (!lastCores.length) { toast("No hay núcleos no-planos que idealizar como columna-cajón."); return; }
      coresResolved = true; // el ingeniero ha elegido la idealización → el aviso se retira
      setWarn(null);
      toast(`${lastCores.length} núcleo(s) como columna-cajón (magenta). Clic izquierdo en un núcleo para ver su sección.`);
    });
    return;
  }
  // Superficies: idealización de muros/losas (diafragma ↔ lámina). Antes que el resto.
  if (/lamina|lámina|\bshell\b|pantalla|nucleo|núcleo|diafragma/.test(t)) {
    const toShell = /lamina|lámina|\bshell\b|pantalla|nucleo|núcleo/.test(t);
    const kind = toShell ? "shell" : "diaphragm";
    void ensureAnalytic().then(() => {
      if (el.setSurfaceKindForSelection(kind)) {
        toast(`Superficie seleccionada → ${toShell ? "lámina (shell)" : "diafragma"} (propuesta editable).`);
        return;
      }
      const tipo = toShell ? "IFCWALL" : "IFCSLAB";
      const n = el.setSurfaceKindByType(tipo, kind);
      toast(`${n} ${toShell ? "muros/pantallas → lámina (shell)" : "forjados → diafragma"} (propuesta editable).`);
    });
    return;
  }
  // Ver el modelo analítico idealizado (propuesta revisable).
  if (/analitic|idealiz|modelo estructural|esquema estructural/.test(t)) {
    void ensureAnalytic().then((r) => {
      setWarn(
        r.surfacesNonPlanar > 0 && !coresResolved
          ? `⚠ ${r.surfacesNonPlanar} superficie(s) no-plana(s) (núcleo/caja, en rojo): elige cómo modelarlas (columna-cajón o 4 láminas) antes de calcular.`
          : null,
      );
      const nuc = r.coresClosed + r.coresOpen > 0
        ? ` · Núcleos: ${r.coresClosed} cerrados (teal), ${r.coresOpen} abiertos/U (ámbar).`
        : "";
      const grueso = r.surfacesThick > 0
        ? ` · ⚠ ${r.surfacesThick} GRUESA(s) (rosa): lámina delgada no aplica.`
        : "";
      const torc = r.surfacesSkewed > 0
        ? ` · ⚠ ${r.surfacesSkewed} muro(s) TORCIDO(s) (rojo): artefacto de derivación, revisar.`
        : "";
      toast(`Idealizado (PROPUESTA revisable): ${r.members} barras, ${r.nodes} nudos, ${r.surfaces} superficies.${nuc}${grueso}${torc} Revisa antes de darlo por bueno.`);
    });
    return;
  }
  // Apoyo / empotramiento sobre el nudo del elemento seleccionado.
  if (/apoyo|empotr/.test(t)) {
    void ensureAnalytic().then(() => {
      const m = el.memberOfSelection();
      if (!m) { toast("Selecciona un pilote/pilar (clic) y repite: 'apoyo empotrado aquí'."); return; }
      const node = el.baseNodeOf(m.id) ?? m.nodeStart;
      el.setSupportAtNode(node);
      toast(`Apoyo empotrado (propuesta) en el nudo ${node}. Editable.`);
    });
    return;
  }
  // Carga / sobrecarga distribuida sobre la barra seleccionada.
  if (/carga|sobrecarga|hipotesis|\bbarra\b|\bnudo\b/.test(t)) {
    const num = t.match(/(-?\d+(?:[.,]\d+)?)\s*(?:kn|kpa|kg)?/);
    void ensureAnalytic().then(() => {
      const m = el.memberOfSelection();
      if (!m) { toast("Selecciona una viga (clic) y repite: 'añade una sobrecarga de 5 kN/m'."); return; }
      if (!num) { toast("¿De cuánto? p. ej. 'sobrecarga de 5 kN/m'."); return; }
      const val = Math.abs(parseFloat(num[1].replace(",", ".")));
      const id = el.addDistributedLoad(m.id, val, "y", "Q");
      toast(`Carga ${val} kN/m (propuesta, caso Q, sentido gravedad) en ${m.id} · ${id}. Exporta y reábrelo: sigue ahí.`);
    });
    return;
  }
  toast("No te he entendido. Prueba: 'aísla las vigas', 'oculta los muros', 'colorea los pilares de azul', 'deshacer', 'muéstrame todo el modelo'.");
}

const EXAMPLES = ["aísla las vigas", "oculta los muros", "colorea los pilares de azul", "clases", "estado de dato", "deshacer", "muéstrame todo el modelo"];
let exi = 0;
window.setInterval(() => {
  if (document.activeElement !== cmd) cmd.placeholder = "Habla con el modelo:  " + EXAMPLES[exi++ % EXAMPLES.length];
}, 2600);

cmd.addEventListener("keydown", (e) => {
  if (e.key === "Enter") { runCommand(cmd.value); cmd.value = ""; }
});
window.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== cmd) { e.preventDefault(); cmd.focus(); }
});

// --- árbol de estructura espacial ---
let treeBuilt = false;
function nodeLabel(n: SNode): string {
  return n.name && n.name.length ? n.name : n.ifcType.replace(/^ifc/i, "");
}
function collectIds(n: SNode, acc: number[]): void {
  acc.push(n.expressId);
  for (const c of n.children) collectIds(c, acc);
}
function renderNode(n: SNode, modelID: number, depth: number): HTMLElement {
  const wrap = document.createElement("div");
  const row = document.createElement("div");
  row.className = "tn";
  row.style.paddingLeft = 8 + depth * 12 + "px";
  row.textContent = (n.children.length ? "▸ " : "· ") + nodeLabel(n);
  row.addEventListener("click", (e) => {
    e.stopPropagation();
    const ids: number[] = [];
    collectIds(n, ids);
    snapshot();
    el.isolateByExpressIds(modelID, ids);
    toast(`Aislado: ${nodeLabel(n)}`);
  });
  wrap.appendChild(row);
  for (const c of n.children) wrap.appendChild(renderNode(c, modelID, depth + 1));
  return wrap;
}
async function buildTree(): Promise<void> {
  const trees = await el.spatialTree();
  treePanel.innerHTML = "<div class='hd'><span class='x' id='tx'>✕</span>Estructura</div>";
  for (const { name, modelID, root } of trees) {
    const mh = document.createElement("div");
    mh.className = "mh";
    mh.textContent = name;
    treePanel.appendChild(mh);
    treePanel.appendChild(renderNode(root, modelID, 0));
  }
  $("tx").addEventListener("click", () => (treePanel.style.display = "none"));
}
async function toggleTree(): Promise<void> {
  if (treePanel.style.display === "block") {
    treePanel.style.display = "none";
    return;
  }
  if (!treeBuilt) {
    await buildTree();
    treeBuilt = true;
  }
  treePanel.style.display = "block";
}
treeBtn.addEventListener("click", () => void toggleTree());

// --- saneamiento espacial (carril V1) ---
function downloadIfc(name: string, bytes: Uint8Array): void {
  const fn = name.replace(/\.ifc$/i, "") + "_saneado.ifc";
  const blob = new Blob([bytes as BlobPart], { type: "application/octet-stream" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = fn;
  a.click();
  window.setTimeout(() => URL.revokeObjectURL(url), 1500);
}
async function applySaneamiento(fixes: SFix[]): Promise<void> {
  toast("Aplicando y reescribiendo el IFC…");
  const results = await el.applySpatialFix(fixes);
  for (const r of results) downloadIfc(r.name, r.bytes);
  treeBuilt = false;
  if (treePanel.style.display === "block") await buildTree();
  propsEl.style.display = "none";
  toast(`Saneado · ${results.length} modelo(s) corregido(s) y descargado(s)`);
}
function showSaneamiento(fixes: SFix[]): void {
  propsEl.style.display = "block";
  const head = "<span class='x' id='px'>✕</span><div class='hd'>Saneamiento espacial</div>";
  if (fixes.length === 0) {
    propsEl.innerHTML = head + "<div class='muted'>Cada elemento ya está en su planta. Nada que corregir.</div>";
    $("px").addEventListener("click", () => (propsEl.style.display = "none"));
    return;
  }
  let html = head + `<div class='muted'>${fixes.length} elementos mal asignados (propuesta por geometría):</div>`;
  for (const f of fixes.slice(0, 200))
    html += `<div class='kv'><span>${f.ifcType}${f.name ? " · " + f.name : ""}</span><b>${f.fromStorey ?? "?"} → ${f.toStorey}</b></div>`;
  if (fixes.length > 200) html += `<div class='muted'>…y ${fixes.length - 200} más</div>`;
  html += `<button id='apply' class='applybtn'>Aplicar ${fixes.length} cambios</button>`;
  propsEl.innerHTML = html;
  $("px").addEventListener("click", () => (propsEl.style.display = "none"));
  $("apply").addEventListener("click", () => void applySaneamiento(fixes));
}
async function runSaneamiento(kind: "cota" | "estacion"): Promise<void> {
  toast("Analizando la asignación espacial…");
  try {
    showSaneamiento(await el.proposeSpatialFix(kind));
  } catch (e) {
    toast(e instanceof Error ? e.message : String(e));
  }
}

// --- carga por arrastre ---
async function loadFiles(files: FileList | File[]): Promise<void> {
  const sources: Array<{ name: string; data: ArrayBuffer }> = [];
  for (const f of Array.from(files)) {
    if (!f.name.toLowerCase().endsWith(".ifc")) continue;
    sources.push({ name: f.name, data: await f.arrayBuffer() });
  }
  if (sources.length === 0) { toast("Suelta uno o más .ifc"); return; }
  toast("Cargando…");
  try {
    await el.load(sources);
    hint.style.display = "none";
    cur = { vis: {}, col: {} };
    history.length = 0;
    treeBuilt = false;
    treePanel.style.display = "none";
    setDataStateUI("proposal"); // chip: lo cargado/autorado es PROPUESTA (D-021)
    toast("Modelo cargado · clic en un elemento, o usa la barra de comandos");
  } catch (e) {
    toast("Error: " + String(e));
  }
}
window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => { e.preventDefault(); if (e.dataTransfer?.files.length) void loadFiles(e.dataTransfer.files); });
fileInput.addEventListener("change", () => { if (fileInput.files) void loadFiles(fileInput.files); });
