import { useCallback, useEffect, useRef, useState, type ReactNode, type PointerEvent as RPE } from "react";
import { IfcLoader, Viewer, aplicarSkin, estadoDato, dataStateStyle } from "@aqyra/visor";
import type { LoadedModel, SpatialNode, DataState, Disciplina } from "@aqyra/visor";

/** Mapa de Psets tal como lo entrega `IfcLoader.getProperties().psets`: nombre de Pset → (clave → valor). */
type Psets = Record<string, Record<string, unknown>>;
import { AqyraMark } from "./AqyraMark";
import type { Discipline } from "../disciplines";

/* ── iconos mínimos propios (sin CDN, D-CH-5) ─────────────────────────────── */
const PATHS: Record<string, ReactNode> = {
  eye: <><circle cx="12" cy="12" r="3" /><path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7z" /></>,
  list: <><path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01" /></>,
  ruler: <><path d="M3 8l13 13 5-5L8 3z" /><path d="M8 8l2 2M12 4l2 2M6 12l2 2" /></>,
  palette: <><circle cx="12" cy="12" r="9" /><circle cx="8" cy="10" r="1" /><circle cx="12" cy="7" r="1" /><circle cx="16" cy="10" r="1" /></>,
  msg: <><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z" /></>,
  star: <><circle cx="12" cy="5" r="2" /><circle cx="6" cy="18" r="2" /><circle cx="18" cy="18" r="2" /><path d="M12 7v6M12 13l-5 4M12 13l5 4" /></>,
  wave: <><path d="M2 12c2 0 2-6 4-6s2 12 4 12 2-12 4-12 2 6 4 6" /></>,
  check: <><path d="M9 12l2 2 4-4M7 3h10l4 4v12a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V7z" /></>,
  file: <><path d="M14 3H6a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" /><path d="M14 3v6h6" /></>,
  frame: <><path d="M4 8V4h4M20 8V4h-4M4 16v4h4M20 16v4h-4" /></>,
  send: <><path d="M12 19V5M5 12l7-7 7 7" /></>,
  chevron: <><path d="M6 9l6 6 6-6" /></>,
};
function Ico({ name }: { name: string }) {
  return (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth={1.7} strokeLinecap="round" strokeLinejoin="round">
      {PATHS[name] ?? PATHS.frame}
    </svg>
  );
}

/* ── metadatos de dominio por disciplina (mockup) ─────────────────────────── */
interface DomMeta { blockTitle: string; tools: [string, string][]; prompts: string[]; }
const DOM: Record<string, DomMeta> = {
  diseno: {
    blockTitle: "Topics BCF",
    tools: [["eye", "Describir el modelo"], ["list", "Propiedades y Psets"], ["ruler", "Medir"], ["palette", "Color por clase"], ["msg", "Incidencia BCF"]],
    prompts: ["Descríbeme la planta 1", "¿Qué muros son EI 60?"],
  },
  estructuras: {
    blockTitle: "Comprobaciones",
    tools: [["star", "Idealizar modelo"], ["wave", "Esfuerzos N·V·M"], ["check", "Comprobar EC2/EC3"], ["palette", "Color por clase"], ["file", "Memoria de cálculo"]],
    prompts: ["Comprueba el pilar más solicitado", "Redacta la memoria de cálculo"],
  },
  instalaciones: { blockTitle: "Resultados de red", tools: [["palette", "Color por clase"]], prompts: [] },
  lineales: { blockTitle: "Verificaciones", tools: [["palette", "Color por clase"]], prompts: [] },
  puentes: { blockTitle: "Comprobaciones", tools: [["palette", "Color por clase"]], prompts: [] },
};

/* color estable por clase IFC para el árbol/etiquetas */
function ifcColor(t: string): string {
  const M: Record<string, string> = {
    IFCWALL: "#c9d1d9", IFCSLAB: "#8b9dc3", IFCWINDOW: "#5bc8e6", IFCDOOR: "#d9a05b",
    IFCCOLUMN: "#e0574f", IFCBEAM: "#e0a24f", IFCFOOTING: "#9e6b3f", IFCROOF: "#b05be6",
    IFCCOVERING: "#7e8aa2", IFCSPACE: "#6fd0a0", IFCMEMBER: "#e0d24f",
  };
  const k = t.toUpperCase();
  if (M[k]) return M[k];
  let h = 0;
  for (let i = 0; i < k.length; i++) h = (h * 31 + k.charCodeAt(i)) >>> 0;
  return `hsl(${h % 360} 45% 66%)`;
}

const ACTIVAS = new Set(["diseno", "estructuras"]);

/* ── nodo del árbol espacial (plegable, clic → selección) ─────────────────── */
function TreeRow({
  node, isElement, selected, onSelect, depth,
}: {
  node: SpatialNode; isElement: (id: number) => boolean; selected: number | null;
  onSelect: (id: number) => void; depth: number;
}) {
  const [open, setOpen] = useState(depth < 2);
  const elem = isElement(node.expressId);
  const tk = node.ifcType.replace(/^IFC/i, "");
  const has = node.children.length > 0;
  return (
    <>
      <div
        className={"row" + (elem ? " clk" : has ? " clk" : "") + (selected === node.expressId ? " sel" : "")}
        onClick={() => (elem ? onSelect(node.expressId) : setOpen((o) => !o))}
      >
        <span
          className={"caret" + (has ? "" : " leaf")}
          onClick={(e) => { e.stopPropagation(); if (has) setOpen((o) => !o); }}
        >{has ? (open ? "▾" : "▸") : "·"}</span>
        <span className="tk" style={{ color: ifcColor(node.ifcType) }}>{tk}</span>
        {node.name ? <span className="rs">· {node.name}</span> : null}
      </div>
      {has && open ? (
        <div className="kids">
          {node.children.map((c) => (
            <TreeRow key={c.expressId} node={c} isElement={isElement} selected={selected} onSelect={onSelect} depth={depth + 1} />
          ))}
        </div>
      ) : null}
    </>
  );
}

interface Sel { expressId: number; ifcType: string; globalId: string; psets: Psets; estado: DataState; }

export function VisorChrome({
  file, discipline, accentInt, onHome, onOpenFile,
}: {
  file: File; discipline: Discipline; accentInt: number; onHome: () => void; onOpenFile: (f: File) => void;
}) {
  const sceneRef = useRef<HTMLDivElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const loaderRef = useRef<IfcLoader | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const modelRef = useRef<LoadedModel | null>(null);
  const infoRef = useRef<Map<number, { globalId: string; ifcType: string }>>(new Map());

  const [loading, setLoading] = useState(true);
  const [nota, setNota] = useState("");
  const [meta, setMeta] = useState("");
  const [tree, setTree] = useState<SpatialNode | null>(null);
  const [clases, setClases] = useState<{ ifcType: string; count: number }[]>([]);
  const [selected, setSelected] = useState<number | null>(null);
  const [sel, setSel] = useState<Sel | null>(null);
  const [open, setOpen] = useState({ esp: true, fun: false, cls: false, kls: false, dom: true });
  const [selPos, setSelPos] = useState<{ left: number; top: number } | null>(null);
  const [prompt, setPrompt] = useState("");

  const dom = DOM[discipline.id] ?? DOM.diseno;
  const isElement = useCallback((id: number) => infoRef.current.has(id), []);

  const select = useCallback(async (expressId: number, frame: boolean) => {
    const viewer = viewerRef.current, model = modelRef.current, loader = loaderRef.current;
    if (!viewer || !model || !loader) return;
    const info = infoRef.current.get(expressId);
    viewer.highlightSelection(model.modelID, [expressId], { accent: accentInt });
    if (frame) viewer.frameElement(model.modelID, expressId);
    setSelected(expressId);
    let psets: Psets = {};
    try {
      const rec = await loader.getProperties(model.modelID, expressId, info?.globalId ?? "");
      psets = rec.psets;
    } catch { /* honesto: sin Psets */ }
    setSel({
      expressId,
      ifcType: info?.ifcType ?? "IfcElement",
      globalId: info?.globalId ?? "—",
      psets,
      estado: estadoDato(Object.keys(psets)),
    });
  }, [accentInt]);

  // montar visor + abrir el modelo
  useEffect(() => {
    let cancelled = false;
    setLoading(true); setNota(""); setTree(null); setSelected(null); setSel(null);
    (async () => {
      const loader = new IfcLoader({ wasmPath: "/wasm-web-ifc/", wasmAbsolute: true });
      await loader.init();
      if (cancelled) return;
      const viewer = new Viewer();
      viewer.mount(sceneRef.current!);
      loaderRef.current = loader; viewerRef.current = viewer;
      const data = await file.text();
      const m: LoadedModel = await loader.open({ name: file.name, data });
      if (cancelled) return;
      modelRef.current = m;
      viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
      const info = new Map<number, { globalId: string; ifcType: string }>();
      for (const e of m.elements) info.set(e.expressId, { globalId: e.globalId, ifcType: e.ifcType });
      infoRef.current = info;
      viewer.onPick = (pi) => { void select(pi.expressId, false); };
      setMeta(`${m.schema} · ${m.elements.length} elementos · georref EPSG:25830`);
      setClases(viewer.classes().sort((a, b) => b.count - a.count));
      setTree(await loader.getSpatialTree(m.modelID));
      if (ACTIVAS.has(discipline.id)) aplicarSkin(viewer, discipline.id as Disciplina);
      setLoading(false);
      requestAnimationFrame(() => requestAnimationFrame(() => viewer.frameAll()));
      window.setTimeout(() => viewer.frameAll(), 220);
    })().catch((e) => { if (!cancelled) { setNota(`ERROR: ${e}`); setLoading(false); } });
    return () => {
      cancelled = true;
      const v = viewerRef.current as unknown as { dispose?: () => void } | null;
      v?.dispose?.(); viewerRef.current = null; modelRef.current = null;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  // re-vestir por disciplina (color categórico por clase) cuando cambia la disciplina activa
  useEffect(() => {
    const viewer = viewerRef.current;
    if (!viewer || loading) return;
    if (ACTIVAS.has(discipline.id)) aplicarSkin(viewer, discipline.id as Disciplina);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [discipline]);

  // resizer del sidebar (--side-w en :root)
  function onResize(e: RPE) {
    e.preventDefault();
    (e.target as HTMLElement).setPointerCapture?.(e.pointerId);
    const move = (ev: PointerEvent) => {
      const x = Math.max(210, Math.min(ev.clientX - 56, 560));
      document.documentElement.style.setProperty("--side-w", x + "px");
    };
    const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
  }

  // arrastre del panel de selección flotante
  function onDragSel(e: RPE) {
    e.preventDefault();
    const panel = (e.currentTarget as HTMLElement).parentElement!;
    const vp = panel.parentElement!.getBoundingClientRect();
    const r = panel.getBoundingClientRect();
    const ox = e.clientX - r.left, oy = e.clientY - r.top;
    const move = (ev: PointerEvent) => {
      const left = Math.max(6, Math.min(ev.clientX - vp.left - ox, vp.width - r.width - 6));
      const top = Math.max(6, Math.min(ev.clientY - vp.top - oy, vp.height - r.height - 6));
      setSelPos({ left, top });
    };
    const up = () => { window.removeEventListener("pointermove", move); window.removeEventListener("pointerup", up); };
    window.addEventListener("pointermove", move); window.addEventListener("pointerup", up);
  }

  function tool(nombre: string) {
    const viewer = viewerRef.current;
    if (!viewer) return;
    if (nombre === "Color por clase") {
      if (ACTIVAS.has(discipline.id)) aplicarSkin(viewer, discipline.id as Disciplina);
    }
    // Describir / Medir / EC / Memoria / BCF: stubs honestos (la IA / motores llegan por olas)
  }

  const sh = (k: keyof typeof open, label: string, extra?: ReactNode) => (
    <div className="sh" onClick={() => setOpen((o) => ({ ...o, [k]: !o[k] }))}>
      <span>{label}</span>{extra}
      <span className="cv"><Ico name="chevron" /></span>
    </div>
  );

  const st = sel ? dataStateStyle(sel.estado) : null;

  return (
    <>
      {/* ───────── SIDEBAR ───────── */}
      <aside className="side2">
        <div className="hdr">
          <div className="ttl">{file.name}</div>
          <div className="meta">{meta || "cargando…"}</div>
        </div>

        <div className={"sec" + (open.esp ? "" : " closed")}>
          {sh("esp", "Estructura espacial")}
          <div className="sb">
            {tree ? (
              <TreeRow node={tree} isElement={isElement} selected={selected} onSelect={(id) => void select(id, true)} depth={0} />
            ) : <div className="empty">cargando árbol…</div>}
          </div>
        </div>

        <div className={"sec" + (open.fun ? "" : " closed")}>
          {sh("fun", "Estructura funcional")}
          <div className="sb"><div className="empty">el modelo no trae sistemas (IfcSystem/IfcZone) — se poblará con la ingesta</div></div>
        </div>

        <div className={"sec" + (open.cls ? "" : " closed")}>
          {sh("cls", "Clases", <span className="cnt">{clases.length}</span>)}
          <div className="sb">
            {clases.length ? clases.map((c) => (
              <div key={c.ifcType} className="row">
                <span className="tk" style={{ color: ifcColor(c.ifcType) }}>{c.ifcType.replace(/^IFC/i, "")}</span>
                <span className="cnt">{c.count}</span>
              </div>
            )) : <div className="empty">—</div>}
          </div>
        </div>

        <div className={"sec" + (open.kls ? "" : " closed")}>
          {sh("kls", "Clasificación")}
          <div className="sb"><div className="empty">sin Uniclass/GuBIMClass en el modelo — capacidad bsDD (por olas)</div></div>
        </div>

        <div className={"sec" + (open.dom ? "" : " closed")}>
          {sh("dom", dom.blockTitle)}
          <div className="sb"><div className="empty">sin datos de dominio en este modelo</div></div>
        </div>
      </aside>

      {/* ───────── RESIZER ───────── */}
      <div className="resizer" onPointerDown={onResize} role="separator" aria-orientation="vertical" />

      {/* ───────── VIEWPORT ───────── */}
      <section
        className="vp"
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => { e.preventDefault(); const f = e.dataTransfer.files?.[0]; if (f) onOpenFile(f); }}
      >
        <input
          ref={fileInput} type="file" accept=".ifc" style={{ display: "none" }}
          onChange={(e) => { const f = e.target.files?.[0]; if (f) onOpenFile(f); }}
        />
        <div className="vppill"><span className="d" />{discipline.name}</div>
        <div className="vpbtns">
          <button className="vpbtn" onClick={() => fileInput.current?.click()}>Abrir IFC</button>
          <button className="vpbtn" onClick={() => viewerRef.current?.frameAll()}>Vista general</button>
          <button className="vpbtn" onClick={() => setNota("El coste 5D requiere el Maestro federado 5D (IfcCostSchedule).")}>Coste 5D</button>
          <button className="vpbtn" onClick={() => setNota("El cumplimiento 6D requiere el Maestro con Pset_Aqyra_Cumplimiento.")}>Cumplimiento 6D</button>
        </div>
        {nota ? <div className="toast" onClick={() => setNota("")}>{nota}</div> : null}

        <div className="rdock">
          {dom.tools.map(([ic, label]) => (
            <div key={label} className="rtool" onClick={() => tool(label)}>
              <Ico name={ic} /><span className="tip">{label}</span>
            </div>
          ))}
        </div>

        {sel && st ? (
          <div className="selfloat" style={selPos ? { left: selPos.left, top: selPos.top, right: "auto" } : undefined}>
            <div className="sfh" onPointerDown={onDragSel}>
              <span className="sft">Selección</span><span className="mv">⠿</span>
            </div>
            <div className="sfb">
              <span className="tagc" style={{ color: ifcColor(sel.ifcType), borderColor: ifcColor(sel.ifcType) + "66" }}>{sel.ifcType}</span>
              <span className="stt" style={{ background: st.color }}>{st.label}</span>
              <div className="gid">GlobalId · {sel.globalId}</div>
              {Object.keys(sel.psets).length ? Object.entries(sel.psets).map(([ps, kv]) => (
                <div key={ps}>
                  <div className="ptl">{ps}</div>
                  {Object.entries(kv).map(([k, v]) => (
                    <div key={k} className="kv"><span className="k">{k}</span><span className="v">{v === null || v === undefined ? "—" : String(v)}</span></div>
                  ))}
                </div>
              )) : <div className="empty">(sin Psets)</div>}
            </div>
          </div>
        ) : null}

        <div className="scwrap">
          <div className="scene" ref={sceneRef}>
            {loading ? <div className="loading"><AqyraMark size={54} thinking /></div> : null}
          </div>
          <svg className="axes" viewBox="0 0 100 100" aria-hidden="true">
            <line x1="30" y1="70" x2="86" y2="58" stroke="#c0563e" strokeWidth="2.5" /><text x="88" y="59" fill="#c0563e" fontSize="11">X</text>
            <line x1="30" y1="70" x2="46" y2="40" stroke="#5a9e57" strokeWidth="2.5" /><text x="47" y="37" fill="#5a9e57" fontSize="11">Y</text>
            <line x1="30" y1="70" x2="30" y2="20" stroke="#3f74c0" strokeWidth="2.5" /><text x="26" y="16" fill="#3f74c0" fontSize="11">Z</text>
          </svg>
        </div>

        <div className="ai">
          <textarea
            className="aii" rows={1} value={prompt} onChange={(e) => setPrompt(e.target.value)}
            placeholder="Pregúntale al modelo — escribe / para las habilidades del dominio"
          />
          <div className="aibar">
            <span className="aimodel"><b>Aqyra Golden</b> · Alto ▾</span>
            <div className="aichips">
              {dom.prompts.map((p) => (
                <span key={p} className="aichip" onClick={() => setPrompt(p)}>{p}</span>
              ))}
            </div>
            <span className="aisp" />
            <button className="aisend" aria-label="Enviar (la IA llega por olas)" title="La IA propone · el técnico firma — llega por olas"><Ico name="send" /></button>
          </div>
        </div>

        <div className="foot">
          <span><b>Skin incluida</b> en el visor abierto · sin licencia · el muro de cobro es el export</span>
          <span onClick={onHome} style={{ pointerEvents: "auto", cursor: "pointer" }}><b>La IA propone</b> · el técnico firma</span>
        </div>
      </section>
    </>
  );
}
