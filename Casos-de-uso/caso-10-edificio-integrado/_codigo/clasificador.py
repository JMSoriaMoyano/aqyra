"""
Clasificador / enrutador MULTI-ELEMENTO (caso 10, cierre de INC-03).

Recibe un IFC ortodoxo con VARIOS sistemas estructurales en un mismo
IfcStructuralAnalysisModel, ITERA TODOS los elementos (no by_type[0]), y
clasifica/enruta CADA uno a su modulo del motor por la combinacion de:

  geometria (vertical/horizontal, barra/superficie)
  + seccion del perfil (I-shape de acero / rectangular de hormigon)
  + material (S* acero / C* hormigon)
  + presencia de lecho (IfcBoundaryNodeCondition con rigidez) / carga de cabeza
  + asociaciones viga<->losa (proximidad en planta) y pilar<->zapata (pie comun)

El Pset marcador (Portico/Mixta/MuroCarga/Suelo/Zapata) se usa solo como
CONFIRMACION/respaldo; la clasificacion primaria es geometrica (sin Pset).

Reglas:
  barra vertical de acero I               -> barras       (pilar EC3)
  barra horizontal de acero I aislada     -> barras       (viga/dintel EC3)
  barra horizontal de acero I + losa C    -> mixtas       (viga mixta EC4)
  superficie vertical de hormigon + Naxil -> laminas      (muro de carga EC2)
  superficie horizontal de hormigon+lecho -> cimentaciones(zapata EC2+EC7)
  barra vertical de hormigon rectangular  -> cimentaciones(cadena pilar->zapata)

Ademas EXTRAE un sub-IFC por subsistema (solo sus curve/surface members y sus
acciones), de modo que cada run_all* del motor se ejecuta sobre su PORCION del
IFC reproduciendo las condiciones de sistema unico de los casos 1/5/6/7 (y
evitando los by_type[0] de cada parser, que en un IFC multi-elemento cogerian el
elemento equivocado).

Uso:
  python3 clasificador.py <archivo.ifc> [salida_dir]
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "laminas"))
sys.path.insert(0, os.path.join(HERE, "barras"))
import ifc_to_model_3d
import ifcopenshell

TOL = 1e-3


def _es_acero(mat):
    return bool(mat) and str(mat).strip().upper().startswith("S")


def _es_hormigon(mat):
    return bool(mat) and str(mat).strip().upper().startswith("C")


def _es_I(secname):
    s = (secname or "").upper()
    return ("IPE" in s) or ("HEB" in s) or ("HEA" in s) or ("HEM" in s) or ("IPN" in s)


def _orient_barra(nd_i, nd_j):
    dz = abs(nd_i["z"] - nd_j["z"])
    dxy = abs(nd_i["x"] - nd_j["x"]) + abs(nd_i["y"] - nd_j["y"])
    return "vertical" if (dz > 1e-6 and dxy < 1e-6) else "horizontal"


def _orient_superficie(coords):
    zs = [c[2] for c in coords]
    return "horizontal" if (max(zs) - min(zs)) < 1e-6 else "vertical"


def _bbox_xy(coords):
    xs = [c[0] for c in coords]; ys = [c[1] for c in coords]
    return min(xs), max(xs), min(ys), max(ys)


def _psets_member(el):
    out = {}
    for rel in getattr(el, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet"):
                out[pdef.Name] = {p.Name: getattr(p.NominalValue, "wrappedValue", None)
                                  for p in pdef.HasProperties
                                  if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None}
    return out


def clasificar(ifc_path):
    mn = ifc_to_model_3d.parse(ifc_path)
    ifc = ifcopenshell.open(ifc_path)
    nodos = mn["nodos"]; secs = mn["secciones"]

    # --- nodos con lecho (rigidez Z): definen la huella de la zapata/raft ---
    nodos_lecho = set()
    for c in ifc.by_type("IfcStructuralPointConnection"):
        bc = c.AppliedCondition
        if bc is None:
            continue
        kz = getattr(bc, "TranslationalStiffnessZ", None)
        kzv = getattr(kz, "wrappedValue", kz)
        # rigidez real (numerica) -> lecho elastico; True/None no es lecho
        if isinstance(kzv, (int, float)) and not isinstance(kzv, bool) and kzv > 0:
            nodos_lecho.add(c.Name)

    # --- mapas IFC: member por nombre, acciones por elemento conectado ---
    curve_by_name = {m.Name: m for m in ifc.by_type("IfcStructuralCurveMember")}
    surf_by_name = {m.Name: m for m in ifc.by_type("IfcStructuralSurfaceMember")}
    # action -> nombre del elemento (node/member) al que se conecta
    act_conn = {}
    for rel in ifc.by_type("IfcRelConnectsStructuralActivity"):
        el = rel.RelatingElement; act = rel.RelatedStructuralActivity
        if el is not None and act is not None:
            act_conn[act.Name] = el.Name

    def _acciones_en_zona(x0, x1, y0, y1, zmin, zmax):
        """acciones cuyo nodo conectado cae en la caja (x,y) dada y z en [zmin,zmax].
        Captura cargas de cabeza aplicadas en nodos que no son esquina de la
        superficie (p. ej. el punto medio del borde superior de un muro)."""
        out = []
        for act_name, el_name in act_conn.items():
            nd = nodos.get(el_name)
            if nd is None:
                continue
            if (x0 - TOL <= nd["x"] <= x1 + TOL and y0 - TOL <= nd["y"] <= y1 + TOL
                    and zmin - TOL <= nd["z"] <= zmax + TOL):
                out.append(act_name)
        return out

    # ----- clasificar SUPERFICIES -----
    superficies = {}
    for s in mn["superficies"]:
        coords = s.get("esquinas_coords") or []
        nombre = s["nombre"]
        orient = _orient_superficie(coords) if coords else "?"
        mat = s.get("material")
        esquinas = s.get("esquinas") or []
        tiene_lecho = any(n in nodos_lecho for n in esquinas)
        ps = _psets_member(surf_by_name.get(nombre)) if surf_by_name.get(nombre) else {}
        superficies[nombre] = {"orient": orient, "material": mat, "coords": coords,
                               "bbox": _bbox_xy(coords) if coords else None,
                               "espesor": s.get("espesor"), "tiene_lecho": tiene_lecho,
                               "psets": list(ps.keys()), "esquinas": esquinas}

    # ----- clasificar BARRAS -----
    barras = {}
    for bid, b in mn["barras"].items():
        ni = nodos.get(b["ni"]); nj = nodos.get(b["nj"])
        orient = _orient_barra(ni, nj) if (ni and nj) else "?"
        mat = b.get("material"); sec = b.get("seccion")
        es_I = _es_I(sec)
        ps = _psets_member(curve_by_name.get(bid)) if curve_by_name.get(bid) else {}
        base = min((ni, nj), key=lambda n: n["z"]) if (ni and nj) else (ni or nj)
        barras[bid] = {"orient": orient, "material": mat, "seccion": sec, "es_I": es_I,
                       "ni": b["ni"], "nj": b["nj"], "tipo": b.get("tipo"),
                       "pie": (base["x"], base["y"]) if base else None,
                       "psets": list(ps.keys())}

    # ----- ASOCIACIONES -----
    # 1) viga horizontal de acero I  <->  losa horizontal de hormigon (mixta)
    asoc_mixta = {}   # bar_name -> surf_name
    for bid, b in barras.items():
        if b["orient"] != "horizontal" or not (_es_acero(b["material"]) and b["es_I"]):
            continue
        ni = nodos.get(b["ni"]); nj = nodos.get(b["nj"])
        if not (ni and nj):
            continue
        xc = 0.5 * (ni["x"] + nj["x"]); yc = 0.5 * (ni["y"] + nj["y"])
        for sname, s in superficies.items():
            if s["orient"] != "horizontal" or not _es_hormigon(s["material"]):
                continue
            if s["tiene_lecho"]:
                continue   # esa es una zapata/raft, no una losa de forjado
            x0, x1, y0, y1 = s["bbox"]
            if x0 - TOL <= xc <= x1 + TOL and y0 - TOL <= yc <= y1 + TOL:
                asoc_mixta[bid] = sname
                break

    # 2) pilar vertical de hormigon  <->  zapata horizontal con lecho (pie comun)
    asoc_cim = {}     # bar_name -> surf_name
    for bid, b in barras.items():
        if b["orient"] != "vertical" or not _es_hormigon(b["material"]):
            continue
        if b["pie"] is None:
            continue
        xp, yp = b["pie"]
        for sname, s in superficies.items():
            if s["orient"] != "horizontal" or not s["tiene_lecho"]:
                continue
            x0, x1, y0, y1 = s["bbox"]
            if x0 - TOL <= xp <= x1 + TOL and y0 - TOL <= yp <= y1 + TOL:
                asoc_cim[bid] = sname
                break

    # ----- componentes conexas de barras de ACERO (porticos) -----
    acero_bars = [bid for bid, b in barras.items()
                  if _es_acero(b["material"]) and b["es_I"] and bid not in asoc_mixta]
    adj = {bid: set() for bid in acero_bars}
    for i in acero_bars:
        for j in acero_bars:
            if i >= j:
                continue
            ni = {barras[i]["ni"], barras[i]["nj"]}
            nj = {barras[j]["ni"], barras[j]["nj"]}
            if ni & nj:
                adj[i].add(j); adj[j].add(i)
    comp = {}; seen = set(); cid = 0
    for bid in acero_bars:
        if bid in seen:
            continue
        stack = [bid]; grupo = []
        while stack:
            x = stack.pop()
            if x in seen:
                continue
            seen.add(x); grupo.append(x)
            stack.extend(adj[x] - seen)
        comp[cid] = grupo; cid += 1

    # ----- construir SUBSISTEMAS + routing por elemento -----
    subsistemas = []
    elementos = []

    def _acciones_de(nombres_elem):
        """acciones cuyo elemento conectado esta en el conjunto dado (members o nodos)."""
        out = []
        for act_name, el_name in act_conn.items():
            if el_name in nombres_elem:
                out.append(act_name)
        return out

    # A) porticos (componentes de acero con al menos un pilar)
    for cid, grupo in comp.items():
        tiene_pilar = any(barras[b]["orient"] == "vertical" for b in grupo)
        # nodos del portico (extremos de sus barras) para captar cargas de linea
        nodos_grp = set()
        for b in grupo:
            nodos_grp.add(barras[b]["ni"]); nodos_grp.add(barras[b]["nj"])
        acts = _acciones_de(set(grupo) | nodos_grp)
        nombre_sub = "portico" if tiene_pilar else ("viga_acero_%d" % cid)
        for b in grupo:
            clase = "pilar EC3" if barras[b]["orient"] == "vertical" else "viga/dintel EC3"
            elementos.append({"elemento": b, "tipo": "barra", "clase": clase,
                              "modulo": "barras", "run_all": "barras/run_all.py",
                              "subsistema": nombre_sub})
        subsistemas.append({"id": nombre_sub, "modulo": "barras",
                            "run_all": "barras/run_all.py",
                            "curves": list(grupo), "surfaces": [], "actions": acts,
                            "descripcion": "Portico de acero (EC3)"})

    # B) vigas mixtas (acero I horizontal + losa)
    for bid, sname in asoc_mixta.items():
        nodos_b = {barras[bid]["ni"], barras[bid]["nj"]}
        acts = _acciones_de({bid, sname} | nodos_b | set(superficies[sname]["esquinas"]))
        sub = "mixta_%s" % bid
        elementos.append({"elemento": bid, "tipo": "barra", "clase": "viga mixta EC4",
                          "modulo": "mixtas", "run_all": "mixtas/run_all_mixta.py",
                          "subsistema": sub, "asociado_a": sname})
        elementos.append({"elemento": sname, "tipo": "superficie", "clase": "losa colaborante EC4",
                          "modulo": "mixtas", "run_all": "mixtas/run_all_mixta.py",
                          "subsistema": sub, "asociado_a": bid})
        subsistemas.append({"id": sub, "modulo": "mixtas",
                            "run_all": "mixtas/run_all_mixta.py",
                            "curves": [bid], "surfaces": [sname], "actions": acts,
                            "descripcion": "Forjado mixto / viga mixta (EC4)"})

    # C) muros de carga (superficie vertical de hormigon con carga de cabeza)
    for sname, s in superficies.items():
        if s["orient"] != "vertical" or not _es_hormigon(s["material"]):
            continue
        # nodos de cabeza = esquinas superiores
        zmax = max(c[2] for c in s["coords"]); zmin = min(c[2] for c in s["coords"])
        x0, x1, y0, y1 = s["bbox"]
        acts = sorted(set(_acciones_de({sname} | set(s["esquinas"]))) |
                      set(_acciones_en_zona(x0, x1, y0, y1, zmin, zmax)))
        sub = "muro_%s" % sname
        elementos.append({"elemento": sname, "tipo": "superficie", "clase": "muro de carga EC2",
                          "modulo": "laminas", "run_all": "laminas/run_all_muro.py",
                          "subsistema": sub})
        subsistemas.append({"id": sub, "modulo": "laminas",
                            "run_all": "laminas/run_all_muro.py",
                            "curves": [], "surfaces": [sname], "actions": acts,
                            "descripcion": "Muro de carga / nucleo (EC2 esbeltez)"})

    # D) cimentaciones (zapata horizontal con lecho + su pilar)
    for sname, s in superficies.items():
        if s["orient"] != "horizontal" or not s["tiene_lecho"]:
            continue
        pilares = [bid for bid, sn in asoc_cim.items() if sn == sname]
        nodos_pil = set()
        for p in pilares:
            nodos_pil.add(barras[p]["ni"]); nodos_pil.add(barras[p]["nj"])
        acts = _acciones_de(set(pilares) | nodos_pil | {sname} | set(s["esquinas"]))
        sub = "cimentacion_%s" % sname
        for p in pilares:
            elementos.append({"elemento": p, "tipo": "barra", "clase": "pilar->cimiento (EC2)",
                              "modulo": "cimentaciones", "run_all": "cimentaciones/run_all_zapata.py",
                              "subsistema": sub, "asociado_a": sname})
        elementos.append({"elemento": sname, "tipo": "superficie", "clase": "zapata EC2+EC7",
                          "modulo": "cimentaciones", "run_all": "cimentaciones/run_all_zapata.py",
                          "subsistema": sub})
        subsistemas.append({"id": sub, "modulo": "cimentaciones",
                            "run_all": "cimentaciones/run_all_zapata.py",
                            "curves": list(pilares), "surfaces": [sname], "actions": acts,
                            "descripcion": "Cimentacion superficial: pilar->zapata (EC2+EC7)"})

    return {"ifc": os.path.abspath(ifc_path),
            "n_barras": len(barras), "n_superficies": len(superficies),
            "barras": barras, "superficies": superficies,
            "asociaciones": {"mixta": asoc_mixta, "pilar_zapata": asoc_cim},
            "elementos": elementos, "subsistemas": subsistemas,
            "modelo_neutro": mn}


def extraer_subifc(ifc_path, keep_curves, keep_surfaces, keep_actions, out_path):
    """Escribe un sub-IFC con solo los miembros y acciones indicados (porcion de
    un subsistema). Quita los demas curve/surface members y TODAS las acciones no
    listadas (con sus IfcRelConnectsStructuralActivity), dejando los nodos."""
    ifc = ifcopenshell.open(ifc_path)
    keep_curves = set(keep_curves); keep_surfaces = set(keep_surfaces)
    keep_actions = set(keep_actions)
    # 1) acciones a quitar (y sus rels de conexion)
    for rel in list(ifc.by_type("IfcRelConnectsStructuralActivity")):
        act = rel.RelatedStructuralActivity
        if act is not None and act.Name not in keep_actions:
            ifc.remove(rel)
    for act in list(ifc.by_type("IfcStructuralActivity")):
        if act.Name not in keep_actions:
            # quitar de los grupos de carga
            for rel in list(ifc.by_type("IfcRelAssignsToGroup")):
                if act in (rel.RelatedObjects or []):
                    objs = [o for o in rel.RelatedObjects if o != act]
                    if objs:
                        rel.RelatedObjects = objs
                    else:
                        ifc.remove(rel)
            load = act.AppliedLoad
            ifc.remove(act)
            if load is not None:
                try:
                    ifc.remove(load)
                except Exception:
                    pass
    # 2) miembros a quitar
    for m in list(ifc.by_type("IfcStructuralCurveMember")):
        if m.Name not in keep_curves:
            for rel in list(ifc.by_type("IfcRelConnectsStructuralMember")):
                if getattr(rel, "RelatingStructuralMember", None) == m:
                    ifc.remove(rel)
            ifc.remove(m)
    for m in list(ifc.by_type("IfcStructuralSurfaceMember")):
        if m.Name not in keep_surfaces:
            ifc.remove(m)

    # 3) nodos: conservar SOLO los referenciados por los miembros/acciones que
    #    quedan (por coordenadas). Evita nodos huerfanos que desestabilizan el
    #    solver de barras (PyNite marca inestables los nodos sin elemento/apoyo).
    def _coords_of_conn(conn):
        for r in conn.Representation.Representations:
            for it in r.Items:
                if it.is_a("IfcVertexPoint"):
                    c = it.VertexGeometry.Coordinates
                    return (float(c[0]), float(c[1]), float(c[2]))
        return None

    conn_coord = {}
    for conn in ifc.by_type("IfcStructuralPointConnection"):
        conn_coord[conn.Name] = _coords_of_conn(conn)

    def _match_node(xyz):
        if xyz is None:
            return None
        for nm, c in conn_coord.items():
            if c is not None and all(abs(c[k] - xyz[k]) < 1e-4 for k in range(3)):
                return nm
        return None

    needed = set()
    # endpoints de las barras que quedan (IfcEdge)
    for mb in ifc.by_type("IfcStructuralCurveMember"):
        if not getattr(mb, "Representation", None):
            continue
        for r in mb.Representation.Representations:
            for it in r.Items:
                if it.is_a("IfcEdge"):
                    for vp in (it.EdgeStart, it.EdgeEnd):
                        try:
                            c = vp.VertexGeometry.Coordinates
                            needed.add(_match_node((float(c[0]), float(c[1]), float(c[2]))))
                        except Exception:
                            pass
    # esquinas de las superficies que quedan (incluye nodos de lecho de la zapata)
    for sm in ifc.by_type("IfcStructuralSurfaceMember"):
        if not getattr(sm, "Representation", None):
            continue
        for r in sm.Representation.Representations:
            for it in r.Items:
                for fb in getattr(it, "Bounds", []) or []:
                    loop = fb.Bound
                    for pt in getattr(loop, "Polygon", []) or []:
                        c = pt.Coordinates
                        needed.add(_match_node((float(c[0]), float(c[1]), float(c[2]))))
    # nodos conectados a las acciones que quedan
    for rel in ifc.by_type("IfcRelConnectsStructuralActivity"):
        el = rel.RelatingElement
        if el is not None and el.is_a("IfcStructuralPointConnection"):
            needed.add(el.Name)
    needed.discard(None)

    for conn in list(ifc.by_type("IfcStructuralPointConnection")):
        if conn.Name not in needed:
            for rel in list(ifc.by_type("IfcRelConnectsStructuralActivity")):
                if rel.RelatingElement == conn:
                    ifc.remove(rel)
            for rel in list(ifc.by_type("IfcRelConnectsStructuralMember")):
                if getattr(rel, "RelatedStructuralConnection", None) == conn:
                    ifc.remove(rel)
            bc = conn.AppliedCondition
            ifc.remove(conn)
            if bc is not None:
                try:
                    ifc.remove(bc)
                except Exception:
                    pass
    ifc.write(out_path)
    return out_path


def main():
    ifc_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else os.path.dirname(os.path.abspath(ifc_path))
    os.makedirs(out_dir, exist_ok=True)
    res = clasificar(ifc_path)
    print("CLASIFICACION / ENRUTADO MULTI-ELEMENTO")
    print("  IFC: %s" % res["ifc"])
    print("  barras=%d  superficies=%d  subsistemas=%d" % (
        res["n_barras"], res["n_superficies"], len(res["subsistemas"])))
    print("\n  %-18s %-22s %-14s %s" % ("ELEMENTO", "CLASE", "MODULO", "SUBSISTEMA"))
    for e in res["elementos"]:
        print("  %-18s %-22s %-14s %s" % (e["elemento"], e["clase"], e["modulo"], e["subsistema"]))
    print("\n  ASOCIACIONES:")
    print("   viga<->losa (mixta):", res["asociaciones"]["mixta"])
    print("   pilar<->zapata     :", res["asociaciones"]["pilar_zapata"])
    # volcar routing a json
    out = {k: res[k] for k in ("ifc", "n_barras", "n_superficies",
                               "asociaciones", "elementos", "subsistemas")}
    rp = os.path.join(out_dir, "clasificacion.json")
    json.dump(out, open(rp, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("\n  routing -> %s" % rp)


if __name__ == "__main__":
    main()
