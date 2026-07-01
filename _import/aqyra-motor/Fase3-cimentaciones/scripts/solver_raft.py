"""
Solver de LOSA DE CIMENTACION (raft) sobre lecho elastico (Winkler).
 - Placa (quad MITC4) horizontal sobre muelles verticales (k = ks * area trib).
 - Reticula de pilares: cada carga (N) repartida en la HUELLA del pilar.
 - Presion del terreno = ks * asiento ; momentos de placa (dos direcciones) ; asientos.
Extension directa del solver de la zapata (un pilar -> varios pilares).
SI (N, m).
"""
import sys
import os
import json
import numpy as np
from collections import defaultdict
import ifcopenshell
from Pynite import FEModel3D
from combinaciones import build_combos


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        mats[mp.Material.Name] = {"E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fck": d.get("CompressiveStrength"), "fctm": d.get("TensileStrength")}
    fm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = {}
    for rel in getattr(fm, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
            pd = rel.RelatingPropertyDefinition
            ps[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                           if p.is_a("IfcPropertySingleValue") and p.NominalValue}
    g = ps["Pset_Estructurando_Losa"]
    pilares = []
    for n, p in ps.items():
        if n.startswith("Pset_Estructurando_Pilar_"):
            pilares.append({"x": p["x"], "y": p["y"], "lado": p["Lado"],
                            "N_G": p["N_G_N"], "N_Q": p["N_Q_N"]})
    matn = None
    for rel in getattr(fm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matn = rel.RelatingMaterial.Name
    return {"materiales": mats, "losa": {
        "BX": g["BX"], "LY": g["LY"], "espesor": g["Espesor"], "malla": g["TamanoMalla"],
        "material": matn or g.get("Material"), "lado_pilar": g["LadoPilar"],
        "ks": g["ModuloBalasto_N_m3"], "Rd": g["Rd_suelo_Pa"], "pilares": pilares}}


def solve(model):
    z = model["losa"]; mat = z["material"]; mp = model["materiales"][mat]
    t = z["espesor"]; BX = z["BX"]; LY = z["LY"]; mesh = z["malla"]; ks = z["ks"]
    pilares = z["pilares"]

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_rectangle_mesh("R", mesh, BX, LY, t, mat, origin=(0, 0, 0), plane="XY")
    m.meshes["R"].generate()

    # area tributaria por nodo
    trib = defaultdict(float)
    for q in m.quads.values():
        P = [np.array([n.X, n.Y, n.Z]) for n in (q.i_node, q.j_node, q.m_node, q.n_node)]
        a = 0.5 * np.linalg.norm(np.cross(P[2] - P[0], P[3] - P[1]))
        for n in (q.i_node, q.j_node, q.m_node, q.n_node):
            trib[n.name] += a / 4
    # muelles Winkler (DZ) + drilling; estabilizacion en plano (2 nodos)
    for nm, nd in m.nodes.items():
        m.def_support(nm, False, False, False, False, False, True)
        m.def_support_spring(nm, "DZ", ks * trib[nm])
    n0 = min(m.nodes.values(), key=lambda n: (n.X, n.Y))
    m.def_support(n0.name, True, True, False, False, False, True)
    n1 = max(m.nodes.values(), key=lambda n: (n.X - n0.X) ** 2 + (n.Y - n0.Y) ** 2)
    m.def_support(n1.name, False, True, False, False, False, True)

    # cargas por pilar repartidas en su huella
    col_nodes = []
    for ip, pil in enumerate(pilares):
        c = pil["lado"]; xp = pil["x"]; yp = pil["y"]
        patch = [nd for nd in m.nodes.values()
                 if abs(nd.X - xp) <= c / 2 + 1e-9 and abs(nd.Y - yp) <= c / 2 + 1e-9]
        if not patch:
            patch = [min(m.nodes.values(), key=lambda n: (n.X - xp) ** 2 + (n.Y - yp) ** 2)]
        col_nodes.append([nd.name for nd in patch])
        for nd in patch:
            m.add_node_load(nd.name, "FZ", pil["N_G"] / len(patch), case="G")
            m.add_node_load(nd.name, "FZ", pil["N_Q"] / len(patch), case="Q")

    combos, meta = build_combos(["G", "Q"])
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    # clasificacion de posicion de cada pilar (interior/borde/esquina)
    def posicion(xp, yp):
        ex = min(xp, BX - xp); ey = min(yp, LY - yp)
        borde_x = ex <= 1.5; borde_y = ey <= 1.5
        if borde_x and borde_y:
            return "corner"
        if borde_x or borde_y:
            return "edge"
        return "interior"

    res = {"combos_meta": meta, "info": {"BX": BX, "LY": LY, "espesor": t, "material": mat,
           "lado_pilar": z["lado_pilar"], "ks": ks, "Rd": z["Rd"], "area": BX * LY,
           "n_pilares": len(pilares),
           "pilares": [{"x": p["x"], "y": p["y"], "lado": p["lado"],
                        "N_G_kN": -p["N_G"] / 1e3, "N_Q_kN": -p["N_Q"] / 1e3,
                        "pos": posicion(p["x"], p["y"])} for p in pilares]},
           "losa": {}}
    for combo in combos:
        quads = []
        for q in m.quads.values():
            M = q.moment(0, 0, True, combo)
            cx = (q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4
            cy = (q.i_node.Y + q.j_node.Y + q.m_node.Y + q.n_node.Y) / 4
            quads.append({"x": cx, "y": cy, "Mx": float(M[0, 0]), "My": float(M[1, 0])})
        pres = [{"x": nd.X, "y": nd.Y, "p": -ks * nd.DZ[combo], "w": -nd.DZ[combo]}
                for nd in m.nodes.values()]
        res["losa"][combo] = {"quads": quads, "presion": pres}

    # asiento por pilar (ELS_car) y presion local (para punzonamiento)
    elscombo = "ELS_car" if "ELS_car" in combos else "ELU"
    for ip, pil in enumerate(res["info"]["pilares"]):
        nodes = col_nodes[ip]
        w_els = np.mean([-m.nodes[nn].DZ[elscombo] for nn in nodes])
        w_elu = np.mean([-m.nodes[nn].DZ["ELU"] for nn in nodes])
        pil["asiento_mm"] = float(w_els * 1e3)
        pil["p_local_ELU_kPa"] = float(ks * w_elu / 1e3)

    # equilibrio (ELU): suma reacciones muelles = carga aplicada
    Rz = sum((-ks * m.nodes[nm].DZ["ELU"]) * trib[nm] for nm in m.nodes)
    Napl = sum(abs(p["N_G"]) * combos["ELU"].get("G", 0) + abs(p["N_Q"]) * combos["ELU"].get("Q", 0)
               for p in pilares)
    res["equilibrio"] = {"aplicada_ELU_kN": Napl / 1e3, "reaccion_suelo_ELU_kN": Rz / 1e3,
                         "error_pct": abs(Napl - Rz) / Napl * 100 if Napl else 0.0}
    # asiento diferencial (ELS) entre pilares
    asientos = [p["asiento_mm"] for p in res["info"]["pilares"]]
    res["info"]["asiento_max_mm"] = max(asientos)
    res["info"]["asiento_min_mm"] = min(asientos)
    res["info"]["asiento_dif_mm"] = max(asientos) - min(asientos)
    return m, res


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ifc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-losa-cimentacion", "raft.ifc")
    proj = os.path.dirname(ifc)
    model = parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    _, res = solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    eq = res["equilibrio"]; inf = res["info"]
    pr = [p["p"] for p in res["losa"]["ELU"]["presion"]]
    q = res["losa"]["ELU"]["quads"]
    mmax = max(max(abs(qq["Mx"]), abs(qq["My"])) for qq in q)
    print("LOSA %dx%d m  canto=%.2f  %d pilares  ks=%.0f MN/m3" % (inf["BX"], inf["LY"], inf["espesor"], inf["n_pilares"], inf["ks"] / 1e6))
    print("  equilibrio ELU: aplicada=%.0f  reaccion suelo=%.0f kN  error=%.2f%%"
          % (eq["aplicada_ELU_kN"], eq["reaccion_suelo_ELU_kN"], eq["error_pct"]))
    print("  presion suelo ELU=[%.0f, %.0f] kPa (Rd=%.0f)" % (min(pr) / 1e3, max(pr) / 1e3, inf["Rd"] / 1e3))
    print("  M placa max=%.0f kN.m/m  asiento dif=%.2f mm" % (mmax / 1e3, inf["asiento_dif_mm"]))
