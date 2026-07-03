/** Demo del vertical 3.1: el visor abierto abre el IFC federado DERIVADO del
 *  C4-FED-06 y aplica la cámara BCF del viewpoint (D29) al seleccionar el topic. */
import {
  IfcLoader, Viewer, parseMarkup, parseViewpoint, bcfCameraToViewer,
} from "@aqyra/visor";
import type { BcfTopic, LoadedModel, SpatialNode } from "@aqyra/visor";

const $ = (id: string): HTMLElement => document.getElementById(id)!;

async function textoDe(url: string): Promise<string> {
  const r = await fetch(url);
  if (!r.ok) throw new Error(`${url}: ${r.status}`);
  return r.text();
}

function pintaArbol(n: SpatialNode, cont: HTMLElement): void {
  const div = document.createElement("div");
  div.className = "nodo";
  div.textContent = `${n.ifcType.replace("IFC", "")} · ${n.name ?? "(sin nombre)"}`;
  cont.appendChild(div);
  for (const c of n.children) pintaArbol(c, div);
}

async function main(): Promise<void> {
  const loader = new IfcLoader({ wasmPath: "/node_modules/web-ifc/", wasmAbsolute: true });
  await loader.init();

  const viewer = new Viewer();
  viewer.mount($("escena"));

  const data = await textoDe("/federado.ifc");
  const m: LoadedModel = await loader.open({ name: "federado", data });
  viewer.addIfcModel(m.modelID, loader.getMeshes(m.modelID));
  $("estado").textContent =
    `${m.schema} · ${m.elements.length} elementos · georref EPSG:25830 · EST rotado 30° (D27)`;

  pintaArbol(await loader.getSpatialTree(m.modelID), $("arbol"));

  viewer.onPick = (info) => {
    const el = m.elements.find((e) => e.expressId === info.expressId);
    $("props").textContent = el
      ? `${el.ifcType}\nGlobalId: ${el.globalId}\nexpressId: ${el.expressId}`
      : "(sin elemento)";
  };

  // Árbol BCF (emitido por services/federacion — el visor solo LEE, PLAN §1)
  const indice: { topics: string[] } = JSON.parse(await textoDe("/bcf-index.json"));
  const cont = $("topics");
  for (const guid of indice.topics) {
    const topic: BcfTopic = parseMarkup(await textoDe(`/bcf/${guid}/markup.bcf`));
    const div = document.createElement("div");
    div.className = "topic";
    div.innerHTML = `<span class="prio">[${topic.priority ?? "?"}]</span> ${topic.title}` +
      `<br><small>${topic.labels.join(" · ")}${topic.viewpointFile ? " · 📷" : ""}</small>`;
    div.onclick = async () => {
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
        for (const g of vp.selection) {
          const el = m.elements.find((e) => e.globalId === g);
          if (el) viewer.highlightByExpressId(m.modelID, el.expressId);
        }
        detalle += `\nComponents: ${vp.selection.join(", ")}`;
      }
      $("props").textContent = detalle;
    };
    cont.appendChild(div);
  }
}

main().catch((e) => { $("estado").textContent = `ERROR: ${e}`; console.error(e); });
