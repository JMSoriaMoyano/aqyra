"""
Solver de MURO DE CARGA (elemento plano vertical, plano XZ).
 - Malla de lamina en el plano XZ (X largo, Z altura, normal global Y).
 - Cargas: autopeso (vertical), carga vertical en cabeza (linea), viento (presion normal).
 - Apoyos: base empotrada a traslacion; cabeza arriostrada fuera de plano.
Extrae membrana vertical (compresion), flexion fuera de plano y flecha normal.
SI (N, m).
"""
import sys
import json
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

    wm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = psets(wm); g = ps["Pset_Estructurando_Muro"]
    cargas = []
    for n, p in ps.items():
        if n.startswith("Pset_Estructurando_Carga_Muro"):
            cargas.append({"tipo": p["Tipo"], "caso": p["Caso"],
                           "valor": p.get("valor_N_m", p.get("valor_N_m2"))})
    matw = None
    for rel in getattr(wm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matw = rel.RelatingMaterial.Name
    return {"materiales": mats, "muro": {"H": g["H"], "L": g["L"], "espesor": g["Espesor"],
            "malla": g["TamanoMalla"], "beta": g["Beta"], "material": matw or g.get("Material"),
            "cargas": cargas}}


def solve(model):
    w = model["muro"]; mat = w["material"]; mp = model["materiales"][mat]
    t = w["espesor"]; H = w["H"]; L = w["L"]; mesh = w["malla"]

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_rectangle_mesh("W", mesh, L, H, t, mat, origin=(0, 0, 0), plane="XZ")
    m.meshes["W"].generate()

    base, top = [], []
    for nm, nd in m.nodes.items():
        if abs(nd.Z) < 1e-6:
            base.append(nm)
        elif abs(nd.Z - H) < 1e-6:
            top.append(nm)
    # apoyos: drilling (RY, normal al muro) en todos; base empotrada a traslacion;
    # cabeza arriostrada fuera de plano (DY)
    for nm in m.nodes:
        m.def_support(nm, False, False, False, False, True, False)
    for nm in base:
        m.def_support(nm, True, True, True, False, True, False)
    for nm in top:
        m.def_support(nm, False, True, False, False, True, False)

    # cargas
    peso = mp["rho"] * G_ACC * t
    # autopeso (vertical, caso G) repartido por area
    for q in m.quads.values():
        P = [np.array([n.X, n.Y, n.Z]) for n in (q.i_node, q.j_node, q.m_node, q.n_node)]
        a = 0.5 * np.linalg.norm(np.cross(P[2] - P[0], P[3] - P[1]))
        for nd in (q.i_node, q.j_node, q.m_node, q.n_node):
            m.add_node_load(nd.name, "FZ", -peso * a / 4.0, case="G")
    # carga vertical en cabeza (linea -> nodal por tributario en X)
    top_sorted = sorted(top, key=lambda nm: m.nodes[nm].X)
    xs = [m.nodes[nm].X for nm in top_sorted]
    trib = []
    for i, x in enumerate(xs):
        lo = (x - xs[i - 1]) / 2 if i > 0 else 0
        hi = (xs[i + 1] - x) / 2 if i < len(xs) - 1 else 0
        trib.append(lo + hi)
    for c in w["cargas"]:
        if c["tipo"] == "top_vertical":
            for nm, tr in zip(top_sorted, trib):
                m.add_node_load(nm, "FZ", c["valor"] * tr, case=c["caso"])
        elif c["tipo"] == "viento_normal":
            for q in m.quads:
                m.add_quad_surface_pressure(q, c["valor"], case=c["caso"])

    casos = sorted({c["caso"] for c in w["cargas"]} | {"G"})
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    res = {"combos_meta": meta, "info": {"H": H, "L": L, "espesor": t, "beta": w["beta"],
           "material": mat, "peso_N_m2": peso}, "muro": {}}
    for combo in combos:
        quads = []
        for q in m.quads.values():
            M = q.moment(0, 0, True, combo); N = q.membrane(0, 0, True, combo)
            cx = (q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4
            cz = (q.i_node.Z + q.j_node.Z + q.m_node.Z + q.n_node.Z) / 4
            quads.append({"x": cx, "z": cz, "Mx": float(M[0, 0]), "My": float(M[1, 0]),
                          "nx": float(N[0, 0]), "ny": float(N[1, 0])})
        defl = [{"x": nd.X, "z": nd.Z, "dy": nd.DY[combo]} for nd in m.nodes.values()]
        res["muro"][combo] = {"quads": quads, "deformada": defl}

    # equilibrio vertical (ELU)
    Rz = sum(m.nodes[nm].RxnFZ["ELU"] for nm in base)
    # carga vertical total ELU
    fG = combos["ELU"].get("G", 0); fQ = combos["ELU"].get("Q", 0)
    Wv = peso * (H * L) * fG
    for c in w["cargas"]:
        if c["tipo"] == "top_vertical":
            Wv += abs(c["valor"]) * L * combos["ELU"].get(c["caso"], 0)
    res["equilibrio"] = {"aplicada_vert_ELU_kN": Wv / 1e3, "reaccion_vert_ELU_kN": Rz / 1e3,
                         "error_pct": abs(Wv - Rz) / Wv * 100}
    return m, res


if __name__ == "__main__":
    ifc = sys.argv[1] if len(sys.argv) > 1 else "proyecto-muro/muro.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "proyecto-muro/resultados.json"
    model = parse(ifc)
    json.dump(model, open("proyecto-muro/modelo_neutro.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    _, res = solve(model)
    json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    eq = res["equilibrio"]
    q = res["muro"]["ELU"]["quads"]
    ncomp = min(qq["ny"] for qq in q)         # vertical (Z), compresion negativa
    mmax = max(max(abs(qq["Mx"]), abs(qq["My"])) for qq in q)
    dy = max(abs(p["dy"]) for p in res["muro"]["ELS_car"]["deformada"])
    print(f"Muro H={res['info']['H']} L={res['info']['L']} t={res['info']['espesor']}")
    print(f"  equilibrio vert ELU: aplicada={eq['aplicada_vert_ELU_kN']:.0f} reaccion={eq['reaccion_vert_ELU_kN']:.0f} "
          f"error={eq['error_pct']:.2f}%")
    print(f"  membrana vertical compresion max={ncomp/1e3:.0f} kN/m  M fuera plano max={mmax/1e3:.1f} kN·m/m  "
          f"flecha normal={dy*1e3:.2f} mm")
