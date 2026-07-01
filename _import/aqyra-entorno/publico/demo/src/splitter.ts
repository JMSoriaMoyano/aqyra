/**
 * Divisores arrastrables sobre CSS grid — USABILIDAD (capa común, "lo común
 * manda"): el usuario ajusta a mano el tamaño de cada panel para corregir el
 * encuadre. Pensado para que cualquier skin (Diseño, calculista, base) lo herede.
 *
 * Modelo: un grid con tracks declarados en orden; cada track es `auto`, `flex`
 * (minmax con suelo) o `pane` (px ajustable y con mínimo). Entre tracks de
 * contenido se intercalan marcadores `handle` que se materializan como una barra
 * arrastrable. Al arrastrar, el track `pane` adyacente cambia de tamaño y el `flex`
 * (o el otro `pane`) absorbe la diferencia; nunca por debajo de su mínimo.
 *
 * Frontera C1: CERO (puro UI/UX, no toca el contrato ni alto.json). La persistencia
 * es JSON en localStorage (formato abierto) y NO es export firmable: sigue siendo
 * cebo. La IA prepara; la firma (Llave 2) es de JM.
 */

export type Axis = "rows" | "columns";

export interface Pane { el: HTMLElement; kind: "pane"; key: string; size: number; min: number; }
export interface Flex { el: HTMLElement; kind: "flex"; min: number; }
export interface Auto { el: HTMLElement; kind: "auto"; }
export interface Handle { kind: "handle"; }
export type Entry = Pane | Flex | Auto | Handle;
type Content = Pane | Flex | Auto;

export interface ResizeConfig {
  grid: HTMLElement;
  axis: Axis;
  layout: Entry[];
  storageKey?: string;
  /** Grosor de la barra (px). */ handlePx?: number;
}

// ── núcleo determinista (golden, Llave 1) ────────────────────────────────────

/** Clampa un tamaño candidato al rango [min, max]; tolera max<min (gana min). */
export function clampSize(next: number, min: number, max: number): number {
  if (max < min) max = min;
  return Math.max(min, Math.min(max, next));
}

/** Saneado de tamaños persistidos: SOLO claves conocidas con números finitos > 0.
 *  Defiende contra localStorage corrupto/manipulado sin romper la UI. */
export function sanitizeSizes(raw: unknown, keys: string[]): Record<string, number> {
  const out: Record<string, number> = {};
  if (!raw || typeof raw !== "object") return out;
  const obj = raw as Record<string, unknown>;
  for (const k of keys) {
    const v = obj[k];
    if (typeof v === "number" && Number.isFinite(v) && v > 0) out[k] = v;
  }
  return out;
}

// ── persistencia (formato abierto: JSON) ─────────────────────────────────────

function loadSizes(storageKey: string | undefined, keys: string[]): Record<string, number> {
  if (!storageKey) return {};
  try {
    return sanitizeSizes(JSON.parse(localStorage.getItem(storageKey) ?? "null"), keys);
  } catch {
    return {};
  }
}

function saveSizes(storageKey: string | undefined, sizes: Record<string, number>): void {
  if (!storageKey) return;
  try {
    localStorage.setItem(storageKey, JSON.stringify(sizes));
  } catch {
    /* cebo: si no hay storage, simplemente no se recuerda */
  }
}

// ── cableado ─────────────────────────────────────────────────────────────────

/** Activa divisores arrastrables sobre `grid` según `layout`. Idempotente por carga. */
export function makeGridResizable(cfg: ResizeConfig): void {
  const { grid, axis, layout } = cfg;
  const handlePx = cfg.handlePx ?? 6;
  const panes = layout.filter((e): e is Pane => (e as Pane).kind === "pane");
  const keys = panes.map((p) => p.key);
  const defaults = new Map(panes.map((p) => [p.key, p.size] as const));

  // Tamaños recordados (si hay) por encima de los por defecto.
  const persisted = loadSizes(cfg.storageKey, keys);
  for (const p of panes) {
    const v = persisted[p.key];
    if (v !== undefined) p.size = Math.max(p.min, v);
  }

  if (getComputedStyle(grid).position === "static") grid.style.position = "relative";

  // Materializa una barra por cada `handle`, insertándola antes del siguiente track.
  const handles: { el: HTMLElement; idx: number }[] = [];
  for (let i = 0; i < layout.length; i++) {
    if (layout[i].kind !== "handle") continue;
    const next = layout[i + 1] as Content | undefined;
    const h = document.createElement("div");
    h.className = `aq-split aq-split-${axis === "rows" ? "row" : "col"}`;
    h.setAttribute("role", "separator");
    h.setAttribute("aria-orientation", axis === "rows" ? "horizontal" : "vertical");
    if (next && "el" in next && next.el.parentElement) next.el.parentElement.insertBefore(h, next.el);
    handles.push({ el: h, idx: i });
  }

  const trackSize = (e: Entry): string =>
    e.kind === "handle" ? `${handlePx}px`
    : e.kind === "auto" ? "auto"
    : e.kind === "flex" ? `minmax(${e.min}px, 1fr)`
    : `${e.size}px`;

  const apply = (): void => {
    const tmpl = layout.map(trackSize).join(" ");
    if (axis === "rows") grid.style.gridTemplateRows = tmpl;
    else grid.style.gridTemplateColumns = tmpl;
  };
  apply();

  const persist = (): void => {
    const sizes: Record<string, number> = {};
    for (const p of panes) sizes[p.key] = p.size;
    saveSizes(cfg.storageKey, sizes);
  };

  const measure = (e: Content): number => {
    const r = e.el.getBoundingClientRect();
    return axis === "rows" ? r.height : r.width;
  };

  for (const { el, idx } of handles) {
    const before = layout[idx - 1] as Content;
    const after = layout[idx + 1] as Content;

    el.addEventListener("pointerdown", (ev) => {
      ev.preventDefault();
      el.setPointerCapture(ev.pointerId);
      el.classList.add("aq-active");
      const start = axis === "rows" ? ev.clientY : ev.clientX;
      const sBefore = before.kind === "pane" ? before.size : 0;
      const sAfter = after.kind === "pane" ? after.size : 0;
      // Holgura que puede ceder el vecino flexible (si lo hay).
      const flexE = before.kind === "flex" ? before : after.kind === "flex" ? after : null;
      const avail = flexE ? Math.max(0, measure(flexE) - flexE.min) : 0;

      const onMove = (m: PointerEvent): void => {
        const d = (axis === "rows" ? m.clientY : m.clientX) - start;
        if (before.kind === "pane" && after.kind === "flex") {
          before.size = clampSize(sBefore + d, before.min, sBefore + avail);
        } else if (before.kind === "flex" && after.kind === "pane") {
          after.size = clampSize(sAfter - d, after.min, sAfter + avail);
        } else if (before.kind === "pane" && after.kind === "pane") {
          const maxBefore = sBefore + (sAfter - after.min);
          const nb = clampSize(sBefore + d, before.min, maxBefore);
          before.size = nb;
          after.size = sAfter - (nb - sBefore);
        }
        apply();
      };
      const onUp = (u: PointerEvent): void => {
        try { el.releasePointerCapture(u.pointerId); } catch { /* ya liberado */ }
        el.classList.remove("aq-active");
        window.removeEventListener("pointermove", onMove);
        window.removeEventListener("pointerup", onUp);
        persist();
      };
      window.addEventListener("pointermove", onMove);
      window.addEventListener("pointerup", onUp);
    });

    // Doble clic: restaura los tamaños por defecto de los panes adyacentes.
    el.addEventListener("dblclick", () => {
      for (const e of [before, after]) {
        if (e.kind === "pane") e.size = defaults.get(e.key) ?? e.size;
      }
      apply();
      persist();
    });
  }
}
