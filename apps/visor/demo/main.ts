/** Demo del vertical 3.4 (UX lote 1 — pulir el cebo): el visor abierto abre el IFC
 *  federado DERIVADO del C4-FED-06 y aplica la cámara BCF del viewpoint (D29). Añade:
 *  árbol espacial INTERACTIVO (árbol ↔ escena, #2/#9), Psets en el panel (#3), resaltado
 *  BCF con acento + ghost (#1), botón «vista general» (#4) y feedback de topics sin
 *  viewpoint (#5). Fondo oscuro (#7) y canvas a pantalla completa (#8) van en index.html
 *  + el ResizeObserver del Viewer. El visor solo LEE el BCF/derivado (PLAN §1). */
import {
  IfcLoader, Viewer, parseMarkup, parseViewpoint, bcfCameraToViewer, costHeatColor,
  SKINS, aplicarSkin, estadoDato, dataStateStyle,
  colorPorResultado, leyendaCumplimiento,
} from "@aqyra/visor";
import type { BcfTopic, LoadedModel, SpatialNode, Disciplina, DataState } from "@aqyra/visor";

const ACENTO = 0xff8a3d;
const $ = (id: string): HTMLElement => document.getElementById(id)!;

async function textoDe(url: string): Promise<string> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.text();
}

/** Escapa texto para inyectarlo como HTML sin romper el marcado (Psets vienen del modelo). */
function escapaHtml(s: string): string {
  return s.replace(/[&<>]/g, (c) => (c === "&" ? "&amp;" : c === "<" ? "&lt;" : "&gt;"));
}

async function main(): Promise<void> {
  const loader = new IfcLoader({ wasmPath: "/wasm-web-ifc/", wasmAbsolute: true });
  await loader.init();

  const viewer = new Viewer();
  viewer.mount($("escena"));

  // V9 · modo coste 5D (por query ?5d): abre el Maestro CON el presupuesto y colorea por coste.
  if (new URLSearchParams(window.location.search).has("5d")) {
    await modoCoste(loader, viewer);
    return;
  }
  // 6D · modo cumplimiento (por query ?6d): abre el Maestro CON el veredicto y colorea por resultado.
  if (new URLSearchParams(window.location.search).has("6d")) {
    await modoCumplimiento(loader, viewer);
    return;
  }
  $("btn-coste").onclick = (): void => { window.location.search = "?5d"; };
  $("btn-6d").onclick = (): void => { window.location.search = "?6d"; };

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
    let estado: DataState = "proposal";
    try {
      const rec = await loader.getProperties(m.modelID, expressId, globalId);
      const nombres = Object.keys(rec.psets);
      estado = estadoDato(nombres); // Slice 2 (D-SL2-1): computed si hay Pset de resultado
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
    // Chip de estado de dato (D-021): color/etiqueta de dataStateStyle; el verde solo lo da
    // verified-signed (isCertified). El visor MUESTRA el estado, no lo certifica.
    const st = dataStateStyle(estado);
    const chip =
      `<span style="display:inline-block;padding:1px 8px;border-radius:999px;` +
      `font:600 10px system-ui,sans-serif;color:#fff;background:${st.color}">${st.label}</span>`;
    $("props").innerHTML =
      `<div style="margin-bottom:6px">${chip}</div>` +
      `<div style="white-space:pre-wrap">${escapaHtml(txt)}</div>`;
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

  // ── Skins por disciplina (Slice 1): re-viste el modelo por dominio ────────────
  // acento de disciplina + color CATEGÓRICO por clase (D-SK-2) sobre el MISMO IFC.
  // `aplicarSkin` es propone puro: revierte al color base y pinta por clase; reversible.
  function montaSkins(): void {
    const cont = $("skins");
    const leg = $("leyenda-skin");
    const rgbCss = (c: { r: number; g: number; b: number }): string =>
      `rgb(${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)})`;
    // Pastilla de disciplina flotante sobre la escena (acento de la skin activa), como el mockup.
    const pastilla = document.createElement("div");
    pastilla.style.cssText =
      "position:absolute;top:10px;left:10px;z-index:40;padding:4px 12px;border-radius:999px;" +
      "font:600 12px system-ui,sans-serif;background:rgba(28,34,43,.9);border:1px solid var(--border)";
    $("escena").appendChild(pastilla);
    const pinta = (d: Disciplina): void => {
      const leyenda = aplicarSkin(viewer, d);
      const skin = SKINS[d];
      pastilla.textContent = `● ${skin.nombre}`;
      pastilla.style.color = skin.acento;
      pastilla.style.borderColor = skin.acento;
      cont.querySelectorAll("button").forEach((b) => {
        const activo = b.dataset.disc === d;
        b.style.borderColor = activo ? skin.acento : "var(--border)";
        b.style.color = activo ? "#fff" : "var(--fg)";
      });
      const filas = leyenda
        .map((e) =>
          `<div style="display:flex;align-items:center;gap:6px;padding:1px 0">` +
          `<span style="width:12px;height:12px;border-radius:3px;background:${rgbCss(e.color)};` +
          `display:inline-block"></span>${e.ifcClass.replace("IFC", "")} · ${e.count}</div>`)
        .join("");
      leg.innerHTML =
        `<div style="margin:6px 0;color:${skin.acento};font-weight:600">${skin.nombre}</div>` +
        (filas || `<small>(ninguna clase de esta disciplina en el modelo)</small>`);
    };
    (["diseno", "estructuras"] as Disciplina[]).forEach((d) => {
      const b = document.createElement("button");
      b.textContent = SKINS[d].nombre;
      b.dataset.disc = d;
      b.style.cssText =
        "margin:2px 4px 2px 0;padding:4px 10px;border:1px solid var(--border);" +
        "border-radius:4px;background:var(--panel2);color:var(--fg);cursor:pointer";
      b.onclick = (): void => pinta(d);
      cont.appendChild(b);
    });
    pinta("diseno"); // skin por defecto al cargar: la demo entra ya coloreada (como el mockup)
  }
  montaSkins();

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

/** V9 · Modo coste 5D: abre `federado_5d.ifc` (Maestro con IfcCostSchedule), colorea los
 *  elementos por su coste asignado (heatmap) y muestra totales (PEM…PEC + por capítulo) y el
 *  coste/partidas del objeto al seleccionarlo. Self-contained (recarga con ?5d, escena limpia). */
async function modoCoste(loader: IfcLoader, viewer: Viewer): Promise<void> {
  $("leyenda").style.display = "block";
  const data = await textoDe("/federado_5d.ifc");
  const m: LoadedModel = await loader.open({ name: "federado_5d", data });
  viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));

  const coste = loader.readCost(m.modelID);
  if (!coste) { $("estado").textContent = "El modelo no trae IfcCostSchedule (no es 5D)."; return; }
  $("estado").textContent =
    `Maestro 5D · ${m.elements.length} elementos · coste OpenBIM (IfcCostSchedule) · ${coste.moneda}`;

  const exprPorGuid = new Map<string, number>();
  const guidPorExpr = new Map<number, string>();
  for (const e of m.elements) { exprPorGuid.set(e.globalId, e.expressId); guidPorExpr.set(e.expressId, e.globalId); }

  const span = (coste.maxCoste - coste.minCoste) || 1;
  const colorPorExpress = new Map<number, { r: number; g: number; b: number }>();
  for (const [guid, ec] of coste.porElemento) {
    const ex = exprPorGuid.get(guid);
    if (ex !== undefined) colorPorExpress.set(ex, costHeatColor((ec.costeAsignado - coste.minCoste) / span));
  }
  viewer.setCostHeatmap(m.modelID, colorPorExpress);
  viewer.frameAll();

  const eur = (n: number | undefined): string => `${(n ?? 0).toFixed(2)} €`;
  let html = `<b>PEM</b> ${eur(coste.totales.PEM)} → <b>PEC</b> ${eur(coste.totales.PEC)}<br><br>`;
  for (const c of coste.capitulos) html += `${c.codigo} · ${c.descripcion ?? ""}: ${eur(c.importe)}<br>`;
  $("totales").innerHTML = html;

  viewer.onPick = (info): void => {
    const guid = guidPorExpr.get(info.expressId) ?? "";
    const ec = coste.porElemento.get(guid);
    viewer.highlightSelection(m.modelID, [info.expressId], { accent: ACENTO });
    $("props").textContent = ec
      ? `${guid}\ncoste asignado: ${ec.costeAsignado.toFixed(2)} €\npartidas: ${ec.partidas.join(", ")}`
      : `${guid}\n(elemento sin coste asignado)`;
  };
  $("vista-general").onclick = (): void => { viewer.frameAll(); };
  const btn = $("btn-coste") as HTMLButtonElement;
  btn.textContent = "Volver (BCF)";
  btn.onclick = (): void => { window.location.search = ""; };
}

/** 6D · Modo cumplimiento: abre `federado_6d.ifc` (Maestro con Pset_Aqyra_Cumplimiento), colorea los
 *  elementos por su `Resultado` (D-6D-4), muestra la leyenda de 4 con conteo y el veredicto del objeto
 *  al seleccionarlo. Self-contained (recarga con ?6d, escena limpia). Reversible con «Volver». */
async function modoCumplimiento(loader: IfcLoader, viewer: Viewer): Promise<void> {
  const data = await textoDe("/federado_6d.ifc");
  const m: LoadedModel = await loader.open({ name: "federado_6d", data });
  viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));

  const cump = loader.readCompliance(m.modelID);
  if (!cump) { $("estado").textContent = "El modelo no trae Pset_Aqyra_Cumplimiento (no es 6D)."; return; }
  $("estado").textContent =
    `Maestro 6D · ${m.elements.length} elementos · cumplimiento (Pset_Aqyra_Cumplimiento) · CTE/2019`;

  const guidPorExpr = new Map<number, string>();
  const exprPorGuid = new Map<string, number>();
  for (const e of m.elements) { guidPorExpr.set(e.expressId, e.globalId); exprPorGuid.set(e.globalId, e.expressId); }

  const colorPorExpress = new Map<number, { r: number; g: number; b: number }>();
  for (const [guid, ec] of cump.porElemento) {
    const ex = exprPorGuid.get(guid);
    if (ex !== undefined) colorPorExpress.set(ex, colorPorResultado(ec.resultado));
  }
  viewer.setCumplimientoColors(m.modelID, colorPorExpress);
  viewer.frameAll();

  // Leyenda categórica de 4 (D-6D-4) con el conteo del resumen.
  const rgbCss = (c: { r: number; g: number; b: number }): string =>
    `rgb(${Math.round(c.r * 255)},${Math.round(c.g * 255)},${Math.round(c.b * 255)})`;
  const leg = $("leyenda-6d");
  leg.style.display = "block";
  leg.innerHTML =
    `<div style="margin-bottom:4px;color:var(--fg-dim)">cumplimiento por elemento</div>` +
    leyendaCumplimiento(cump)
      .map((e) => `<div class="fila"><span class="sw" style="background:${rgbCss(e.color)}"></span>${e.etiqueta} · ${e.count}</div>`)
      .join("");
  $("totales").innerHTML = leyendaCumplimiento(cump).map((e) => `${e.etiqueta}: ${e.count}`).join("<br>");

  viewer.onPick = (info): void => {
    const guid = guidPorExpr.get(info.expressId) ?? "";
    const ec = cump.porElemento.get(guid);
    viewer.highlightSelection(m.modelID, [info.expressId], { accent: ACENTO });
    $("props").textContent = ec
      ? `${guid}\nResultado: ${ec.resultado}\nExigencia: ${ec.exigencia ?? "—"} (${ec.documentoBasico ?? "—"} ${ec.apartado ?? ""})` +
        `\nPack: ${ec.pack ?? "—"}${ec.motivo ? `\nMotivo: ${ec.motivo}` : ""}`
      : `${guid}\n(elemento sin resultado de cumplimiento)`;
  };
  $("vista-general").onclick = (): void => { viewer.frameAll(); };
  const btn = $("btn-6d") as HTMLButtonElement;
  btn.textContent = "Volver (BCF)";
  btn.onclick = (): void => { window.location.search = ""; };
}

main().catch((e) => { $("estado").textContent = `ERROR: ${e}`; console.error(e); });
