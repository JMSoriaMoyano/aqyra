// Pipeline IFC -> fragments + indice de propiedades por GlobalId
import { IfcImporter, SingleThreadedFragmentsModel } from "@thatopen/fragments";
import { readFile, writeFile, mkdir } from "node:fs/promises";
import { dirname, resolve, basename } from "node:path";
import { fileURLToPath } from "node:url";

const __dir = dirname(fileURLToPath(import.meta.url));
const WASM_DIR = resolve(__dir, "node_modules/web-ifc/") + "/";

const [,, inPath, outDir, baseArg] = process.argv;
if (!inPath) { console.error("uso: node pipeline.mjs <input.ifc> [outdir] [basename]"); process.exit(1); }
const base = baseArg || basename(inPath).replace(/\.ifc$/i, "");
const out = outDir || ".";

function storeyElevationsFromIfc(ifcText) {
  const map = {};
  const re = /=\s*IFCBUILDINGSTOREY\s*\(\s*'([^']*)'\s*,(.*?)\)\s*;/gis;
  let m;
  while ((m = re.exec(ifcText)) !== null) {
    const guid = m[1];
    const args = m[2];
    const last = args.slice(args.lastIndexOf(",") + 1).trim();
    if (last && last !== "$") { const v = Number(last); if (Number.isFinite(v)) map[guid] = v; }
  }
  return map;
}

// Clasificaciones desde el texto STEP (fragments NO indexa HasAssociations).
// IfcRelAssociatesClassification(RelatedObjects, RelatingClassification) ->
//   IfcClassificationReference(Location, Identification, Name, ReferencedSource) ->
//   IfcClassification(Source, Edition, EditionDate, Name=sistema)
function classificationsFromIfc(ifcText) {
  const ent = new Map(); // id -> { type, args }
  const reLine = /^#(\d+)\s*=\s*([A-Z0-9_]+)\s*\((.*)\)\s*;\s*$/;
  for (const raw of ifcText.split(/\r?\n/)) {
    const m = raw.match(reLine);
    if (m) ent.set(m[1], { type: m[2].toUpperCase(), args: m[3] });
  }
  function splitArgs(s) {
    const out = []; let depth = 0, cur = "", q = false;
    for (let i = 0; i < s.length; i++) {
      const ch = s[i];
      if (q) { cur += ch; if (ch === "'") { if (s[i + 1] === "'") { cur += "'"; i++; } else q = false; } continue; }
      if (ch === "'") { q = true; cur += ch; continue; }
      if (ch === "(") { depth++; cur += ch; continue; }
      if (ch === ")") { depth--; cur += ch; continue; }
      if (ch === "," && depth === 0) { out.push(cur.trim()); cur = ""; continue; }
      cur += ch;
    }
    out.push(cur.trim());
    return out;
  }
  function ifcStrUnescape(s){
    if(s==null) return s;
    s=s.replace(/\\X2\\([0-9A-Fa-f]+)\\X0\\/g,(m,h)=>{ let o=""; for(let i=0;i+4<=h.length;i+=4) o+=String.fromCharCode(parseInt(h.substr(i,4),16)); return o; });
    s=s.replace(/\\X\\([0-9A-Fa-f]{2})/g,(m,h)=>String.fromCharCode(parseInt(h,16)));
    s=s.replace(/\\S\\(.)/g,(m,c)=>String.fromCharCode(c.charCodeAt(0)+128));
    s=s.replace(/\\\\/g,"\\");
    return s;
  }
  const unq = v => { v = (v || "").trim(); if (v === "$" || v === "*" || v === "") return null; const mm = v.match(/^'([\s\S]*)'$/); return mm ? ifcStrUnescape(mm[1].replace(/''/g, "'")) : v; };
  const refId = v => { const mm = (v || "").trim().match(/^#(\d+)$/); return mm ? mm[1] : null; };
  function systemName(id, guard = 0) {
    if (id == null || guard > 8) return null;
    const e = ent.get(id); if (!e) return null;
    if (e.type === "IFCCLASSIFICATION") { return unq(splitArgs(e.args)[3]); }
    if (e.type === "IFCCLASSIFICATIONREFERENCE") { return systemName(refId(splitArgs(e.args)[3]), guard + 1); }
    return null;
  }
  function refInfo(id) {
    const e = ent.get(id); if (!e || e.type !== "IFCCLASSIFICATIONREFERENCE") return null;
    const a = splitArgs(e.args); // Location, Identification, Name, ReferencedSource
    return { location: unq(a[0]), code: unq(a[1]), name: unq(a[2]), system: systemName(refId(a[3])) };
  }
  function guidOf(id) { const e = ent.get(id); if (!e) return null; return unq(splitArgs(e.args)[0]); }

  const guidToCl = {};
  for (const [, e] of ent) {
    if (e.type !== "IFCRELASSOCIATESCLASSIFICATION") continue;
    const a = splitArgs(e.args); // GlobalId,OwnerHistory,Name,Description,RelatedObjects,RelatingClassification
    const info = refInfo(refId(a[5])); if (!info) continue;
    const objs = (a[4] || "").replace(/^\s*\(/, "").replace(/\)\s*$/, "").split(",").map(refId).filter(Boolean);
    for (const oid of objs) {
      const g = guidOf(oid); if (!g) continue;
      (guidToCl[g] ||= []).push({ system: info.system || "Clasificación", code: info.code, name: info.name, location: info.location });
    }
  }
  return guidToCl;
}

async function main() {
  await mkdir(out, { recursive: true });
  const t0 = Date.now();
  const ifcBuf = await readFile(inPath);
  const ifcBytes = new Uint8Array(ifcBuf);
  const ifcText = ifcBuf.toString("latin1");
  const storeyElev = storeyElevationsFromIfc(ifcText);
  const guidToCl = classificationsFromIfc(ifcText);

  const imp = new IfcImporter();
  imp.wasm = { path: WASM_DIR, absolute: true };
  const frag = await imp.process({ bytes: ifcBytes });
  const fragPath = resolve(out, base + ".frag");
  await writeFile(fragPath, frag);
  const tConv = Date.now() - t0;

  const model = new SingleThreadedFragmentsModel(base, frag);

  const categories = model.getCategories().filter(c => /^IFC/i.test(c));
  const ifcCats = categories.map(c => new RegExp("^" + c + "$"));
  const byCat = model.getItemsOfCategories(ifcCats);

  const localToCat = new Map();
  for (const [cat, ids] of Object.entries(byCat)) for (const id of ids) localToCat.set(id, cat);

  const allLocalIds = [...localToCat.keys()];
  const guids = model.getGuidsByLocalIds(allLocalIds);

  const data = model.getItemsData(allLocalIds, {
    attributesDefault: true,
    relationsDefault: { attributes: true, relations: false },
    relations: { IsDefinedBy: { attributes: true, relations: true }, ContainedInStructure: { attributes: true, relations: false } },
  });

  const items = {};
  const localIdToGuid = {};
  allLocalIds.forEach((lid, i) => {
    const guid = guids[i];
    const d = data[i] || {};
    const attrs = {};
    let name = null;
    for (const [k, v] of Object.entries(d)) {
      if (Array.isArray(v)) continue;
      const val = (v && typeof v === "object" && "value" in v) ? v.value : v;
      attrs[k] = val;
      if (k === "Name") name = val;
    }
    const psets = {};
    const quantities = {};
    const defined = d.IsDefinedBy;
    if (Array.isArray(defined)) {
      for (const rel of defined) {
        const pname = rel?.Name?.value ?? rel?.Name ?? "Pset";
        const hp = rel?.HasProperties;
        if (Array.isArray(hp)) {
          const props = {};
          for (const p of hp) {
            const pn = p?.Name?.value ?? p?.Name;
            const pv = p?.NominalValue?.value ?? p?.NominalValue ?? p?.Value?.value ?? null;
            if (pn != null) props[pn] = pv;
          }
          if (Object.keys(props).length) psets[pname] = props;
        }
        const qs = rel?.Quantities;
        if (Array.isArray(qs)) {
          const qset = {};
          for (const q of qs) {
            const qn = q?.Name?.value ?? q?.Name;
            if (qn == null) continue;
            let qv = null, qkind = null;
            for (const [kk, vv] of Object.entries(q)) {
              if (/Value$/.test(kk)) {
                qv = (vv && typeof vv === "object" && "value" in vv) ? vv.value : vv;
                qkind = kk.replace(/Value$/, ""); break;
              }
            }
            if (qv != null) qset[qn] = { value: qv, kind: qkind };
          }
          if (Object.keys(qset).length) quantities[pname] = qset;
        }
      }
    }
    if (localToCat.get(lid) === "IFCBUILDINGSTOREY" && guid && guid in storeyElev) attrs.Elevation = storeyElev[guid];
    const key = guid || ("local:" + lid);
    items[key] = { localId: lid, category: localToCat.get(lid), name, attributes: attrs, psets };
    if (Object.keys(quantities).length) items[key].quantities = quantities;
    if (guid && guidToCl[guid] && guidToCl[guid].length) items[key].classifications = guidToCl[guid];
    if (guid) localIdToGuid[lid] = guid;
  });

  const spatial = model.getSpatialStructure();

  let geomIds = model.getItemsWithGeometry();
  if (geomIds && typeof geomIds.then === "function") geomIds = await geomIds;
  geomIds = Array.isArray(geomIds) ? geomIds : [...(geomIds||[])];
  const geomSet = new Set(geomIds.map(x => (x && typeof x === "object" && "localId" in x) ? x.localId : x));
  const geometryClasses = {};
  for (const lid of geomSet) { const c = localToCat.get(lid); if (c) geometryClasses[c] = (geometryClasses[c]||0)+1; }

  const nameByLocal = {};
  const elevByLocal = {};
  for (const it of Object.values(items)) {
    if (it.localId==null) continue;
    nameByLocal[it.localId] = it.name;
    if (it.category === "IFCBUILDINGSTOREY" && it.attributes && it.attributes.Elevation != null) elevByLocal[it.localId] = it.attributes.Elevation;
  }
  function elementsOf(catGroup) {
    const cat = catGroup.category;
    const res = [];
    for (const wrapper of (catGroup.children || [])) {
      const localId = wrapper.localId;
      const node = { category: cat, localId, name: localId!=null ? (nameByLocal[localId]||null) : null, children: [] };
      if (localId!=null && localId in elevByLocal) node.elevation = elevByLocal[localId];
      for (const childGroup of (wrapper.children || [])) for (const el of elementsOf(childGroup)) node.children.push(el);
      res.push(node);
    }
    return res;
  }
  const roots = elementsOf(spatial);
  const tree = roots.length === 1 ? roots[0] : { category: spatial.category || "IFCPROJECT", localId: null, name: null, children: roots };

  const countByClass = {};
  for (const [cat, ids] of Object.entries(byCat)) countByClass[cat] = ids.length;

  const nClassified = Object.values(items).filter(it => it.classifications).length;
  const index = { model: base, source: basename(inPath), generated: new Date().toISOString(),
    stats: { classes: categories.length, items: allLocalIds.length, classified: nClassified, convert_ms: tConv },
    categories, countByClass, localIdToGuid, geometryClasses, geometryLocalIds: [...geomSet], items, tree };
  const idxPath = resolve(out, base + ".props.json");
  await writeFile(idxPath, JSON.stringify(index));
  model.dispose();
  console.log(JSON.stringify({ ok:true, frag:fragPath, idx:idxPath, classes:categories.length, items:allLocalIds.length, classified:nClassified, convert_ms:tConv }, null, 2));
}
main().then(()=>process.exit(0)).catch(e => { console.error("PIPELINE ERROR:", e.stack || e.message); process.exit(1); });
