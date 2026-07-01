import { defineAqyraViewer, configureAqyra, TAG, type SpatialSeed } from "@aqyra/embed";

configureAqyra({ wasmPath: "/" });
defineAqyraViewer();

type ClassRow = { ifcType: string; count: number };
type RGBA = { r: number; g: number; b: number; a: number };
type Psets = Record<string, Record<string, unknown>>;
type TreeNode = { expressId: number; ifcType: string; name?: string; globalId?: string; children: TreeNode[] };
type ViewerEl = HTMLElement & {
  load(x: unknown): Promise<Array<{ name: string }>>;
  createSpatial(seed: SpatialSeed, name?: string): Promise<Array<{ name: string }>>;
  spatialTree(): Promise<Array<{ name: string; modelID: number; root: TreeNode }>>;
  getProperties(globalId: string): Promise<{ globalId: string; psets: Psets }>;
  on(ev: string, cb: (p: unknown) => void): () => void;
  setVisibilityByClass(c: string, v: boolean): void;
  setColorByClass(c: string, color: RGBA): void;
  classes(): ClassRow[];
};

/** Semilla de la planta tipo de Can Cabassa (Edificio 2) para el incremento 1. */
const CAN_CABASSA_SEED: SpatialSeed = {
  project: { name: "Can_Cabassa" },
  site: { name: "0419901DF2901H0001WW", longName: "Can Cabassa" },
  building: { name: "Edificio 2", longName: "Edificio 2 del conjunto Can Cabassa" },
  storey: { name: "AQ-NIV-P03", longName: "Planta tipo +10.60", elevation: 10.6 },
  spaces: [
    { name: "AQ-ESP-HAB-P03-IZQ-01", longName: "Habitacion IZQ 01" },
    { name: "AQ-ESP-HAB-P03-DER-01", longName: "Habitacion DER 01" },
    { name: "AQ-ESP-COR-P03-01", longName: "Corredor" },
  ],
};

const app = document.getElementById("app")!;
const hint = document.getElementById("hint")!;
const status = document.getElementById("status")!;
const input = document.getElementById("file") as HTMLInputElement;
const classesPanel = document.getElementById("classes")!;
const propsPanel = document.getElementById("props")!;
const treePanel = document.getElementById("tree")!;
const crearBtn = document.getElementById("crear")!;

const el = document.createElement(TAG) as ViewerEl;
app.appendChild(el);

function hexToRgb(hex: string): { r: number; g: number; b: number } {
  const n = parseInt(hex.slice(1), 16);
  return { r: ((n >> 16) & 255) / 255, g: ((n >> 8) & 255) / 255, b: (n & 255) / 255 };
}

function fmt(v: unknown): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "object") return JSON.stringify(v);
  return String(v);
}

function renderClasses(): void {
  const rows = el.classes();
  classesPanel.innerHTML = "<div class='hd'>Clases IFC</div>";
  for (const { ifcType, count } of rows) {
    const row = document.createElement("div");
    row.className = "row";
    const cb = document.createElement("input");
    cb.type = "checkbox";
    cb.checked = true;
    cb.addEventListener("change", () => el.setVisibilityByClass(ifcType, cb.checked));
    const col = document.createElement("input");
    col.type = "color";
    col.addEventListener("input", () => el.setColorByClass(ifcType, { ...hexToRgb(col.value), a: 1 }));
    const label = document.createElement("span");
    label.textContent = `${ifcType} (${count})`;
    row.append(cb, col, label);
    classesPanel.appendChild(row);
  }
  classesPanel.style.display = rows.length ? "block" : "none";
}

el.on("selection-changed", (p) => {
  const sel = p as { globalId?: string; ifcType?: string };
  if (!sel.globalId) {
    propsPanel.style.display = "none";
    return;
  }
  propsPanel.style.display = "block";
  const head = `<div class='hd'>${sel.ifcType ?? "Elemento"}</div><div class='muted'>${sel.globalId}</div>`;
  propsPanel.innerHTML = head + "<div class='muted'>cargando propiedades…</div>";
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
      propsPanel.innerHTML = html;
    })
    .catch((e) => {
      propsPanel.innerHTML = head + "<div class='muted'>Error: " + String(e) + "</div>";
    });
});

async function loadFiles(files: FileList | File[]): Promise<void> {
  const sources: Array<{ name: string; data: ArrayBuffer }> = [];
  for (const f of Array.from(files)) {
    if (!f.name.toLowerCase().endsWith(".ifc")) continue;
    sources.push({ name: f.name, data: await f.arrayBuffer() });
  }
  if (sources.length === 0) {
    status.textContent = "Suelta uno o más archivos .ifc";
    return;
  }
  status.textContent = "Cargando…";
  try {
    const handles = await el.load(sources);
    hint.style.display = "none";
    renderClasses();
    status.textContent = `Cargado: ${handles.map((h) => h.name).join(", ")} · clic en un elemento para ver Psets`;
  } catch (e) {
    status.textContent = "Error: " + String(e);
  }
}

window.addEventListener("dragover", (e) => e.preventDefault());
window.addEventListener("drop", (e) => {
  e.preventDefault();
  if (e.dataTransfer?.files.length) void loadFiles(e.dataTransfer.files);
});
input.addEventListener("change", () => {
  if (input.files) void loadFiles(input.files);
});

/** Pinta el árbol de estructura espacial (Proyecto › Sitio › Edificio › Planta › Espacios). */
async function renderTree(): Promise<void> {
  const trees = await el.spatialTree();
  if (trees.length === 0) {
    treePanel.style.display = "none";
    return;
  }
  const node = (n: TreeNode): string => {
    const label = n.name && n.name.trim() ? n.name : "(sin nombre)";
    const kids = n.children.map(node).join("");
    return `<div class="tnode">• ${label}${kids ? `<div style="margin-left:12px">${kids}</div>` : ""}</div>`;
  };
  treePanel.innerHTML = "<div class='hd'>Árbol espacial</div>" + trees.map((t) => node(t.root)).join("");
  treePanel.style.display = "block";
}

/** Incremento 1 de autoría: el editor CREA un IFC (estructura espacial + espacios) y lo carga. */
async function crearEstructura(): Promise<void> {
  status.textContent = "Creando estructura con el editor…";
  try {
    const handles = await el.createSpatial(CAN_CABASSA_SEED, "Can Cabassa (autorado)");
    hint.style.display = "none";
    renderClasses();
    await renderTree();
    status.textContent =
      `Estructura creada por el editor: ${handles.map((h) => h.name).join(", ")} · ` +
      "árbol espacial a la izquierda · 3D vacío (sin geometría todavía: llega con el primer muro)";
  } catch (e) {
    status.textContent = "Error al crear: " + String(e);
  }
}

crearBtn.addEventListener("click", () => void crearEstructura());
