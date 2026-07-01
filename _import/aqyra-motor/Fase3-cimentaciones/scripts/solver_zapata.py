"""
Solver de ZAPATA AISLADA sobre lecho elastico (Winkler).
 - Placa (quad MITC4) en horizontal sobre muelles verticales (k = ks * area trib).
 - Carga del pilar (N + Mx) repartida en la HUELLA del pilar (evita concentracion).
 - Presion del terreno = ks * asiento ; esfuerzos de placa para flexion ; reaccion.
SI (N, m).
"""
import sys
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

    def psets(el):
        out = {}
        for rel in getattr(el, "IsDefinedBy", []) or []:
            if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
                pd = rel.RelatingPropertyDefinition
                out[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                                if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        return out

    fm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = psets(fm); g = ps["Pset_Estructurando_Zapata"]
    cargas = [{"caso": p["Caso"], "N": p["N_N"], "Mx": p.get("Mx_Nm", 0.0)}
              for n, p in ps.items() if n.startswith("Pset_Estructurando_Carga_Pilar")]
    matz = None
    for rel in getattr(fm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matz = rel.RelatingMaterial.Name
    return {"materiales": mats, "zapata": {
        "B": g["B"], "L": g["L"], "espesor": g["Espesor"], "malla": g["TamanoMalla"],
        "material": matz or g.get("Material"), "c_pilar": g["LadoPilar"], "ks": g["ModuloBalasto_N_m3"],
        "Rd": g["Rd_suelo_Pa"], "xp": g["xpilar"], "yp": g["ypilar"], "cargas": cargas}}


def solve(model):
    z = model["zapata"]; mat = z["material"]; mp = model["materiales"][mat]
    t = z["espesor"]; B = z["B"]; Lz = z["L"]; mesh = z["malla"]; ks = z["ks"]
    xp, yp, c = z["xp"], z["yp"], z["c_pilar"]

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_rectangle_mesh("Z", mesh, B, Lz, t, mat, origin=(0, 0, 0), plane="XY")
    m.meshes["Z"].generate()

    # area tributaria por nodo
    trib = defaultdict(float)
    for q in m.quads.values():
        P = [np.array([n.X, n.Y, n.Z]) for n in (q.i_node, q.j_node, q.m_node, q.n_node)]
        a = 0.5 * np.linalg.norm(np.cross(P[2] - P[0], P[3] - P[1]))
        for n in (q.i_node, q.j_node, q.m_node, q.n_node):
            trib[n.name] += a / 4
    # muelles Winkler (DZ) + drilling; estabilizacion en plano
    for nm, nd in m.nodes.items():
        m.def_support(nm, False, False, False, False, False, True)
        m.def_support_spring(nm, "DZ", ks * trib[nm])
    cen = min(m.nodes.values(), key=lambda n: (n.X - xp) ** 2 + (n.Y - yp) ** 2)
    m.def_support(cen.name, True, True, False, False, False, True)
    otro = max(m.nodes.values(), key=lambda n: (n.X - cen.X) ** 2 + (n.Y - cen.Y) ** 2)
    m.def_support(otro.name, False, True, False, False, False, True)

    # nodos de la huella del pilar
    patch = [nd for nd in m.nodes.values()
             if abs(nd.X - xp) <= c / 2 + 1e-9 and abs(nd.Y - yp) <= c / 2 + 1e-9]
    if not patch:
        patch = [cen]
    Iyy = sum((nd.Y - yp) ** 2 for nd in patch) or 1.0
    for cgar in z["cargas"]:
        N = cgar["N"]; Mx = cgar["Mx"]; case = cgar["caso"]
        for nd in patch:
            P = N / len(patch) + Mx * (nd.Y - yp) / Iyy
            m.add_node_load(nd.name, "FZ", P, case=case)

    casos = sorted({c["caso"] for c in z["cargas"]})
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    res = {"combos_meta": meta, "info": {"B": B, "L": Lz, "espesor": t, "material": mat,
           "c_pilar": c, "ks": ks, "Rd": z["Rd"], "xp": xp, "yp": yp,
           "area": B * Lz}, "zapata": {}}
    for combo in combos:
        quads = []
        for q in m.quads.values():
            M = q.moment(0, 0, True, combo)
            cx = (q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4
            cy = (q.i_node.Y + q.j_node.Y + q.m_node.Y + q.n_node.Y) / 4
            quads.append({"x": cx, "y": cy, "Mx": float(M[0, 0]), "My": float(M[1, 0])})
        # presion de terreno por nodo = -ks*dz (positiva en compresion)
        pres = [{"x": nd.X, "y": nd.Y, "p": -ks * nd.DZ[combo]} for nd in m.nodes.values()]
        res["zapata"][combo] = {"quads": quads, "presion": pres}

    # equilibrio (ELU): suma reacciones muelles = carga aplicada
    Rz = sum(m.nodes[nm].RxnFZ["ELU"] for nm in m.nodes) if False else None
    # reaccion = suma de presiones*trib
    Rz = sum((-ks * m.nodes[nm].DZ["ELU"]) * trib[nm] for nm in m.nodes)
    Napl = 0.0
    for cgar in z["cargas"]:
        Napl += abs(cgar["N"]) * combos["ELU"].get(cgar["caso"], 0)
    res["equilibrio"] = {"aplicada_ELU_kN": Napl / 1e3, "reaccion_suelo_ELU_kN": Rz / 1e3,
                         "error_pct": abs(Napl - Rz) / Napl * 100}
    return m, res


if __name__ == "__main__":
    ifc = sys.argv[1] if len(sys.argv) > 1 else "proyecto-zapata/zapata.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "proyecto-zapata/resultados.json"
    model = parse(ifc)
    json.dump(model, open("proyecto-zapata/modelo_neutro.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    _, res = solve(model)
    json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    eq = res["equilibrio"]
    pr = [p["p"] for p in res["zapata"]["ELU"]["presion"]]
    q = res["zapata"]["ELU"]["quads"]
    mmax = max(max(abs(qq["Mx"]), abs(qq["My"])) for qq in q)
    print(f"Zapata B={res['info']['B']} t={res['info']['espesor']}")
    print(f"  equilibrio ELU: aplicada={eq['aplicada_ELU_kN']:.0f} reaccion suelo={eq['reaccion_suelo_ELU_kN']:.0f} "
          f"error={eq['error_pct']:.2f}%")
    print(f"  presion suelo ELU rango=[{min(pr)/1e3:.1f}, {max(pr)/1e3:.1f}] kPa  (Rd={res['info']['Rd']/1e3:.0f} kPa)")
    print(f"  M placa max={mmax/1e3:.1f} kN·m/m")
