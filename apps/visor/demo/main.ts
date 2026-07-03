/** Demo del vertical 3.4 (UX lote 1 — pulir el cebo): el visor abierto abre el IFC
 *  federado DERIVADO del C4-FED-06 y aplica la cámara BCF del viewpoint (D29). Añade:
 *  árbol espacial INTERACTIVO (árbol ↔ escena, #2/#9), Psets en el panel (#3), resaltado
 *  BCF con acento + ghost (#1), botón «vista general» (#4) y feedback de topics sin
 *  viewpoint (#5). Fondo oscuro (#7) y canvas a pantalla completa (#8) van en index.html
 *  + el ResizeObserver del Viewer. El visor solo LEE el BCF/derivado (PLAN §1). */
import {
  IfcLoader, Viewer, parseMarkup, parseViewpoint, bcfCameraToViewer,
} from "@aqyra/visor";
import type { BcfTopic, LoadedModel, SpatialNode } from "@aqyra/visor";

const ACENTO = 0xff8a3d;
const $ = (id: string): HTMLElement => document.getElementById(id)!;

async function textoDe(url: string): Promise<string> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.text();
}

async function main(): Promise<void> {
  const loader = new IfcLoader({ wasmPath: "/wasm-web-ifc/", wasmAbsolute: true });
  await loader.init();

  const viewer = new Viewer();
  viewer.mount($("escena"));

  const data = await textoDe("/federado.ifc");
  const m: LoadedModel = await loader.open({ name: "federado", data });
  viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
  $("estado").textContent =
    `${m.schema} · ${m.elements.length} elementos · georref EPSG:25830 · EST rotado 30° (D27)`;

  const porExpress = new Map<number, { globalId: string; ifcType: string }>();
  for (const e of m.elements) porExpress.set(e.expressId, { globalId: e.globalId, ifcType: e.ifcType });
  const filaPorExpress = new Map<number, HTMLElement>();

  // Panel «Selección»: tipo/ids + PSets (#3, el gancho de valor OpenBIM).
  async function muestraElemento(expressId: number, ifcType: string, globalId: string): Promise<void> {
    let txt = `${ifcType}\nGlobalId: ${globalId}\nexpressId: ${expressId}`;
    try {
      const rec = await loader.getProperties(m.modelID, expressId, globalId);
      const nombres = Object.keys(rec.psets);
      if (nombres.length) {
        txt += "\n\nPsets:";
        for (const ps of nombres) {
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
    $("props").textContent = txt;
  }

  function marcaNodoArbol(expressId: number): void {
    for (const f of filaPorExpress.values()) f.classList.remove("sel");
    const fila = filaPorExpress.get(expressId);
    if (fila) {
      fila.classList.add("sel");
      fila.scrollIntoView({ block: "nearest" });
    }
  }

  // Selección de un elemento (clic en escena o en el árbol): acento en la escena + panel.
  function seleccionaElemento(expressId: number, opts?: { frame?: boolean }): void {
    const info = porExpress.get(expressId);
    const ifcType = info?.ifcType ?? "IfcElement";
    const globalId = info?.globalId ?? "";
    viewer.highlightSelection(m.modelID, [expressId], { accent: ACENTO });
    if (opts?.frame) viewer.frameElement(m.modelID, expressId);
    marcaNodoArbol(expressId);
    void muestraElemento(expressId, ifcType, globalId);
  }

  // ── Árbol espacial INTERACTIVO (#2/#9): plegar/desplegar + clic → escena ──────
  function pintaArbol(n: SpatialNode, cont: HTMLElement): void {
    const row = document.createElement("div");
    row.className = "nodo-row";
    const caret = document.createElement("span");
    caret.className = "caret";
    const etq = document.createElement("span");
    etq.className = "etq " + (porExpress.has(n.expressId) ? "elem" : "espacio");
    etq.textContent = `${n.ifcType.replace("IFC", "")} · ${n.name ?? "(sin nombre)"}`;
    row.append(caret, etq);
    cont.appendChild(row);
    filaPorExpress.set(n.expressId, row);

    let hijos: HTMLElement | undefined;
    if (n.children.length) {
      hijos = document.createElement("div");
      hijos.className = "hijos";
      caret.textContent = "▾";
      const toggle = (ev: Event): void => {
        ev.stopPropagation();
        const plegado = hijos!.classList.toggle("plegado");
        caret.textContent = plegado ? "▸" : "▾";
      };
      caret.onclick = toggle;
      cont.appendChild(hijos);
      for (const c of n.children) pintaArbol(c, hijos);
    } else {
      caret.classList.add("leaf");
    }

    if (porExpress.has(n.expressId)) {
      etq.onclick = (): void => seleccionaElemento(n.expressId, { frame: true });
    } else if (hijos) {
      const h = hijos;
      etq.style.cursor = "pointer";
      etq.onclick = (): void => {
        const plegado = h.classList.toggle("plegado");
        caret.textContent = plegado ? "▸" : "▾";
      };
    }
  }

  pintaArbol(await loader.getSpatialTree(m.modelID), $("arbol"));

  // Clic en la escena → selecciona el elemento (sin re-encuadrar).
  viewer.onPick = (info): void => { seleccionaElemento(info.expressId, { frame: false }); };

  // #4 — «Vista general»: quita acento/ghost y re-encuadra el modelo completo.
  $("vista-general").onclick = (): void => {
    document.querySelectorAll(".topic").forEach((t) => t.classList.remove("sel"));
    for (const f of filaPorExpress.values()) f.classList.remove("sel");
    viewer.frameAll();
    $("props").textContent = "(vista general — modelo completo)";
  };

  // Árbol BCF (emitido por services/federacion — el visor solo LEE, PLAN §1).
  const indice: { topics: string[] } = JSON.parse(await textoDe("/bcf-index.json"));
  const cont = $("topics");
  for (const guid of indice.topics) {
    const topic: BcfTopic = parseMarkup(await textoDe(`/bcf/${guid}/markup.bcf`));
    const div = document.createElement("div");
    div.className = "topic";
    div.innerHTML = `<span class="prio">[${topic.priority ?? "?"}]</span> ${topic.title}` +
      `<br><small>${topic.labels.join(" · ")}${topic.viewpointFile ? " · 📷" : " · sin cámara"}</small>`;
    div.onclick = async (): Promise<void> => {
      document.querySelectorAll(".topic").forEach((t) => t.classList.remove("sel"));
      div.classList.add("sel");
      let detalle = `${topic.title}\n${topic.description ?? ""}`;
      if (topic.viewpointFile) {
        const vp = parseViewpoint(await textoDe(`/bcf/${guid}/${topic.viewpointFile}`));
        if (vp.camera) {
          const c = bcfCameraToViewer(vp.camera);
          viewer.setCamera(c.position, c.direction, c.up, c.fovDeg);
          detalle += `\n\nCámara D29 aplicada:\n  pos IFC = ${vp.camera.viewPoint.join(", ")}`;
        }
        // #1 — acento + ghost: deja OBVIO qué señala el topic.
        const ids: number[] = [];
        for (const g of vp.selection) {
          const el = m.elements.find((e) => e.globalId === g);
          if (el) ids.push(el.expressId);
        }
        viewer.highlightSelection(m.modelID, ids, { ghost: true, accent: ACENTO });
        detalle += `\nComponents (acento): ${vp.selection.join(", ")}`;
      } else {
        // #5 — feedback de topic sin viewpoint (R4-GEORREF).
        viewer.clearSelectionAccent();
        viewer.showAll();
        detalle += `\n\n(Topic a nivel de proyecto — sin cámara / R4-GEORREF)`;
      }
      $("props").textContent = detalle;
    };
    cont.appendChild(div);
  }
}

main().catch((e) => { $("estado").textContent = `ERROR: ${e}`; console.error(e); });
