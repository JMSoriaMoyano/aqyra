import { useCallback, useEffect, useRef, useState } from "react";
import { IfcLoader, Viewer } from "@aqyra/visor";
import type { LoadedModel, SpatialNode } from "@aqyra/visor";
import { AqyraMark } from "./AqyraMark";

/** Color por clase IFC (para distinguir el tipo en el árbol). */
const IFC_COLORS: Record<string, string> = {
  IfcWall: "#6ea8ff", IfcSlab: "#c98a5b", IfcColumn: "#e07a4f", IfcBeam: "#e0a94f",
  IfcMember: "#d0b34f", IfcStairFlight: "#a7b061", IfcSpace: "#8090a8", IfcRoof: "#c07a7a",
  IfcDoor: "#b57fd4", IfcWindow: "#7fd4c4", IfcPile: "#cf6a52", IfcFooting: "#b98a73",
  IfcFlowSegment: "#33b3a6", IfcTransportElement: "#9b7fd4", IfcCovering: "#8a9bb5",
};
function ifcColor(t: string): string {
  if (IFC_COLORS[t]) return IFC_COLORS[t];
  let h = 0;
  for (let i = 0; i < t.length; i++) h = (h * 31 + t.charCodeAt(i)) >>> 0;
  return `hsl(${h % 360} 52% 68%)`;
}

/** Nodo del árbol espacial (recursivo, plegable). */
function TreeNode({
  node,
  isElement,
  selected,
  onSelect,
}: {
  node: SpatialNode;
  isElement: (id: number) => boolean;
  selected: number | null;
  onSelect: (id: number) => void;
}) {
  const [open, setOpen] = useState(true);
  const elem = isElement(node.expressId);
  return (
    <div className="tnode">
      <div
        className={"trow" + (selected === node.expressId ? " sel" : "")}
        onClick={() => (elem ? onSelect(node.expressId) : setOpen((o) => !o))}
      >
        <span className="caret" onClick={(e) => { e.stopPropagation(); if (node.children.length) setOpen((o) => !o); }}>
          {node.children.length ? (open ? "▾" : "▸") : "·"}
        </span>
        <span className={"etq" + (elem ? " elem" : "")}>
          <span className="ty" style={{ color: ifcColor(node.ifcType) }}>{node.ifcType.replace("IFC", "")}</span>
          {node.name ? ` · ${node.name}` : ""}
        </span>
      </div>
      {open && node.children.length > 0 && (
        <div style={{ marginLeft: 12 }}>
          {node.children.map((c) => (
            <TreeNode key={c.expressId} node={c} isElement={isElement} selected={selected} onSelect={onSelect} />
          ))}
        </div>
      )}
    </div>
  );
}

export function ViewerPane({ file, accentInt }: { file: File; accentInt: number }) {
  const sceneRef = useRef<HTMLDivElement>(null);
  const loaderRef = useRef<IfcLoader | null>(null);
  const viewerRef = useRef<Viewer | null>(null);
  const modelRef = useRef<LoadedModel | null>(null);
  const infoRef = useRef<Map<number, { globalId: string; ifcType: string }>>(new Map());
  const reframeRef = useRef<() => void>(() => {});

  const [status, setStatus] = useState("Abriendo el modelo…");
  const [loading, setLoading] = useState(true);
  const [tree, setTree] = useState<SpatialNode | null>(null);
  const [selected, setSelected] = useState<number | null>(null);
  const [props, setProps] = useState("Selecciona un elemento en la escena o en el árbol.");

  const isElement = useCallback((id: number) => infoRef.current.has(id), []);

  const select = useCallback(
    async (expressId: number, frame: boolean) => {
      const viewer = viewerRef.current;
      const model = modelRef.current;
      const loader = loaderRef.current;
      if (!viewer || !model || !loader) return;
      const info = infoRef.current.get(expressId);
      viewer.highlightSelection(model.modelID, [expressId], { accent: accentInt });
      if (frame) viewer.frameElement(model.modelID, expressId);
      setSelected(expressId);
      let txt = `${info?.ifcType ?? "IfcElement"}\nGlobalId: ${info?.globalId ?? "—"}\nexpressId: ${expressId}`;
      try {
        const rec = await loader.getProperties(model.modelID, expressId, info?.globalId ?? "");
        const names = Object.keys(rec.psets);
        if (names.length) {
          txt += "\n\nPsets:";
          for (const ps of names) {
            txt += `\n  ${ps}`;
            for (const [k, v] of Object.entries(rec.psets[ps])) {
              txt += `\n    ${k}: ${v === null || v === undefined ? "—" : String(v)}`;
            }
          }
        } else {
          txt += "\n\n(sin Psets)";
        }
      } catch (err) {
        txt += `\n\n(Psets no disponibles: ${err})`;
      }
      setProps(txt);
    },
    [accentInt],
  );

  // montar visor + abrir el IFC suelto
  useEffect(() => {
    let cancelled = false;
    setLoading(true);
    setStatus("Abriendo el modelo…");
    setTree(null);
    setSelected(null);
    (async () => {
      const loader = new IfcLoader({ wasmPath: "/wasm-web-ifc/", wasmAbsolute: true });
      await loader.init();
      if (cancelled) return;
      const viewer = new Viewer();
      viewer.mount(sceneRef.current!);
      loaderRef.current = loader;
      viewerRef.current = viewer;

      const data = await file.text();
      const m: LoadedModel = await loader.open({ name: file.name, data });
      if (cancelled) return;
      modelRef.current = m;
      viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
      // El visor ya encuadra en iso (fitToModels mejorado); reusable en «Vista general».
      reframeRef.current = () => viewer.frameAll();

      const info = new Map<number, { globalId: string; ifcType: string }>();
      for (const e of m.elements) info.set(e.expressId, { globalId: e.globalId, ifcType: e.ifcType });
      infoRef.current = info;

      viewer.onPick = (pi) => { void select(pi.expressId, false); };

      setStatus(`${file.name} · ${m.schema} · ${m.elements.length} elementos`);
      setTree(await loader.getSpatialTree(m.modelID));
      setLoading(false);
      // Encuadrar en el siguiente frame, ya con el lienzo medido.
      requestAnimationFrame(() => requestAnimationFrame(() => reframeRef.current()));
      window.setTimeout(() => reframeRef.current(), 200);
    })().catch((e) => {
      if (!cancelled) { setStatus(`ERROR: ${e}`); setLoading(false); }
    });
    return () => {
      cancelled = true;
      const v = viewerRef.current as unknown as { dispose?: () => void } | null;
      v?.dispose?.();
      viewerRef.current = null;
      modelRef.current = null;
    };
    // select se re-crea con accentInt; no re-montamos el visor por eso
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [file]);

  return (
    <div className="viewer">
      <div className="vcol vleft">
        <div className="vlabel">Estructura espacial</div>
        {tree ? (
          <TreeNode node={tree} isElement={isElement} selected={selected} onSelect={(id) => void select(id, true)} />
        ) : (
          <div className="props">Cargando árbol…</div>
        )}
      </div>

      <div className="scene" ref={sceneRef}>
        <div className="overlay-status">{status}</div>
        {!loading && (
          <button
            className="vbtn"
            style={{ position: "absolute", top: 12, right: 12, zIndex: 4 }}
            onClick={() => reframeRef.current()}
          >
            Vista general
          </button>
        )}
        {loading && (
          <div className="loading">
            <AqyraMark size={54} thinking />
          </div>
        )}
      </div>

      <div className="vcol vright">
        <div className="vlabel">Propiedades · selección</div>
        <div className="props">{props}</div>
      </div>
    </div>
  );
}
