"""
Solver de ELEMENTO PLANO INCLINADO (cubierta / forjado inclinado) de hormigon.

Estrategia:
 1) se malla el faldon en el plano XY (ancho Lv en X, longitud Lu en Y),
 2) se INCLINA girando los nodos un angulo th alrededor del eje X:
        (x, y, 0) -> (x, y*cos th, y*sin th)
 3) las cargas de GRAVEDAD se aplican como cargas nodales verticales (global -Z),
    repartiendo q*area_real entre los 4 nodos de cada quad (valido en cualquier
    inclinacion, a diferencia de la presion normal),
 4) apoyos: 4 bordes simplemente apoyados (borde inferior tambien coarta el
    deslizamiento en el plano horizontal).

Esfuerzos de placa locales [Mx,My,Mxy] y de membrana [nx,ny,nxy]; flecha normal
al faldon. SI (N, m).
"""
import sys
import json
import math
import numpy as np
import ifcopenshell
from Pynite import FEModel3D
from combinaciones import build_combos

G_ACC = 9.81


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        mats[mp.Material.Name] = {"E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fck": d.get("CompressiveStrength"), "fctm": d.get("TensileStrength")}

    def psets(el):
        out = {}
        for rel in getattr(el, "IsDefinedBy", []) or []:
            if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                pd = rel.RelatingPropertyDefinition
                out[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                                if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        return out

    sm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = psets(sm)
    g = ps["Pset_Estructurando_Superficie_Inclinada"]
    cargas = [{"caso": p["Caso"], "qz": p["qz_N_m2"]} for n, p in ps.items()
              if n.startswith("Pset_Estructurando_Carga_Vertical")]
    mat_losa = None
    for rel in getattr(sm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat_losa = rel.RelatingMaterial.Name
    return {"materiales": mats, "superficie": {
        "Lu": g["Lu"], "Lv": g["Lv"], "espesor": g["Espesor"], "malla": g["TamanoMalla"],
        "angulo": g["AnguloGrados"], "material": mat_losa or g.get("Material"), "cargas": cargas}}


def _quad_area(q):
    P = [np.array([n.X, n.Y, n.Z]) for n in (q.i_node, q.j_node, q.m_node, q.n_node)]
    return 0.5 * np.linalg.norm(np.cross(P[2] - P[0], P[3] - P[1]))


def solve(model, angulo=None):
    s = model["superficie"]
    mat = s["material"]; mp = model["materiales"][mat]
    t = s["espesor"]; mesh = s["malla"]; Lu = s["Lu"]; Lv = s["Lv"]
    th = math.radians(s["angulo"] if angulo is None else angulo)

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_rectangle_mesh("F", mesh, Lv, Lu, t, mat, origin=(0, 0, 0), plane="XY")
    m.meshes["F"].generate()

    # clasificar bordes con coords locales (pre-inclinacion) y luego inclinar
    eps = 1e-6
    edge = {"inf": [], "sup": [], "lat": []}
    for nm, nd in m.nodes.items():
        x, y = nd.X, nd.Y
        if abs(y) < eps:
            edge["inf"].append(nm)
        elif abs(y - Lu) < eps:
            edge["sup"].append(nm)
        elif abs(x) < eps or abs(x - Lv) < eps:
            edge["lat"].append(nm)
        # inclinar: girar alrededor del eje X
        nd.Y = y * math.cos(th)
        nd.Z = y * math.sin(th)

    # apoyos: borde inferior (alero) empotrado a deslizamiento (pin DX,DY,DZ);
    # resto de bordes apoyo vertical (DZ). Drilling RZ en todos los nodos.
    for nm in m.nodes:
        m.def_support(nm, False, False, False, False, False, True)
    for nm in edge["inf"]:
        m.def_support(nm, True, True, True, False, False, True)
    for nm in edge["sup"] + edge["lat"]:
        m.def_support(nm, False, False, True, False, False, True)

    # cargas de gravedad (verticales) repartidas a nodos
    peso = mp["rho"] * G_ACC * t
    q_caso = {"G": peso}
    for c in s["cargas"]:
        q_caso[c["caso"]] = q_caso.get(c["caso"], 0.0) + abs(c["qz"])
    nodal = {caso: {} for caso in q_caso}
    for q in m.quads.values():
        a = _quad_area(q)
        for caso, qv in q_caso.items():
            for nd in (q.i_node, q.j_node, q.m_node, q.n_node):
                nodal[caso][nd.name] = nodal[caso].get(nd.name, 0.0) + qv * a / 4.0
    for caso, dd in nodal.items():
        for nm, P in dd.items():
            m.add_node_load(nm, "FZ", -P, case=caso)

    casos = sorted(q_caso.keys())
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    # normal al faldon (tras girar (0,0,1) un angulo th alrededor de X)
    normal = np.array([0.0, -math.sin(th), math.cos(th)])
    res = {"combos_meta": meta, "info": {"Lu": Lu, "Lv": Lv, "espesor": t,
           "angulo": s["angulo"] if angulo is None else angulo,
           "peso_losa_N_m2": peso, "material": mat, "area_real": Lu * Lv}, "losa": {}}
    for combo in combos:
        quads = []
        for q in m.quads.values():
            M = q.moment(0, 0, True, combo); N = q.membrane(0, 0, True, combo)
            P = [(q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4,
                 (q.i_node.Y + q.j_node.Y + q.m_node.Y + q.n_node.Y) / 4]
            quads.append({"x": P[0], "y": P[1], "Mx": float(M[0, 0]), "My": float(M[1, 0]),
                          "Mxy": float(M[2, 0]), "nx": float(N[0, 0]), "ny": float(N[1, 0])})
        # flecha normal al faldon
        dn = []
        for nd in m.nodes.values():
            u = np.array([nd.DX[combo], nd.DY[combo], nd.DZ[combo]])
            dn.append({"x": nd.X, "y": nd.Y, "dn": float(np.dot(u, normal)), "dz": nd.DZ[combo]})
        res["losa"][combo] = {"quads": quads, "deformada": dn}

    # equilibrio vertical
    area = Lu * Lv
    qELU = sum((q_caso[c] if c == "G" else 0) for c in [])  # placeholder
    qELU = peso * combos["ELU"].get("G", 0)
    for c in s["cargas"]:
        qELU += abs(c["qz"]) * combos["ELU"].get(c["caso"], 0)
    Rz = sum(nd.RxnFZ["ELU"] for nd in m.nodes.values()
             if nd.name in (edge["inf"] + edge["sup"] + edge["lat"]))
    res["equilibrio"] = {"aplicada_ELU_kN": qELU * area / 1e3, "reaccion_ELU_kN": Rz / 1e3,
                         "error_pct": abs(qELU * area - Rz) / (qELU * area) * 100}
    return m, res


if __name__ == "__main__":
    ifc = sys.argv[1] if len(sys.argv) > 1 else "proyecto-cubierta/cubierta.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "proyecto-cubierta/resultados.json"
    model = parse(ifc)
    json.dump(model, open("proyecto-cubierta/modelo_neutro.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    _, res = solve(model)
    json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    eq = res["equilibrio"]
    print(f"Cubierta angulo={res['info']['angulo']} deg")
    print(f"  equilibrio ELU: aplicada={eq['aplicada_ELU_kN']:.1f} reaccion={eq['reaccion_ELU_kN']:.1f} "
          f"error={eq['error_pct']:.2f}%")
    qd = res["losa"]["ELU"]["quads"]
    mxs = max(abs(q["Mx"]) for q in qd); mys = max(abs(q["My"]) for q in qd)
    nmax = max(abs(q["ny"]) for q in qd)
    dn = max(abs(p["dn"]) for p in res["losa"]["ELS_car"]["deformada"])
    print(f"  |Mx|max={mxs/1e3:.1f} |My|max={mys/1e3:.1f} kN·m/m  |n|max={nmax/1e3:.1f} kN/m  "
          f"flecha normal={dn*1e3:.2f} mm")
