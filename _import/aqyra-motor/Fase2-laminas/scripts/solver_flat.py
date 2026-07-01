"""
Solver de LOSA PLANA sobre pilares (apoyos puntuales). Lee el IFC, malla la losa
con elementos placa (quad MITC4) y aplica apoyos verticales en los pilares.
Extrae: reacciones de pilar (carga de punzonamiento), esfuerzos de placa y flecha.

Convencion: X,Y horizontales, Z vertical, gravedad -Z. SI (N, m).
"""
import sys
import json
import ifcopenshell
from Pynite import FEModel3D
from combinaciones import build_combos

G_ACC = 9.81


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    # materiales
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

    # pilares
    pilares = []
    for c in ifc.by_type("IfcStructuralPointConnection"):
        pp = psets(c).get("Pset_Estructurando_Pilar")
        if pp:
            pilares.append({"nombre": c.Name, "x": pp["x"], "y": pp["y"],
                            "lado": pp["Lado"], "posicion": pp["Posicion"]})
    # superficie
    sm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = psets(sm)
    geo = ps.get("Pset_Estructurando_Superficie", {})
    cargas = [{"caso": p["Caso"], "qz": p["qz_N_m2"]} for n, p in ps.items()
              if n.startswith("Pset_Estructurando_Carga_Superficie")]
    mat_losa = None
    for rel in getattr(sm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            mat_losa = rel.RelatingMaterial.Name
    surf = {"espesor": geo.get("Espesor", sm.Thickness), "malla": geo.get("TamanoMalla", 0.5),
            "material": mat_losa or geo.get("Material"), "cargas": cargas}
    return {"materiales": mats, "pilares": pilares, "superficie": surf}


def solve(model):
    surf = model["superficie"]
    mat = surf["material"]; mp = model["materiales"][mat]
    t = surf["espesor"]; mesh = surf["malla"]
    xs = [p["x"] for p in model["pilares"]]; ys = [p["y"] for p in model["pilares"]]
    x0, y0 = min(xs), min(ys); W = max(xs) - x0; H = max(ys) - y0

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_rectangle_mesh("LOSA", mesh, W, H, t, mat, origin=(x0, y0, 0.0), plane="XY")
    m.meshes["LOSA"].generate()

    def node_at(x, y):
        for nm, nd in m.nodes.items():
            if abs(nd.X - x) < 1e-4 and abs(nd.Y - y) < 1e-4:
                return nm
        return None

    # apoyos verticales en pilares + drilling (RZ) en todos los nodos
    for nm, nd in m.nodes.items():
        m.def_support(nm, False, False, False, False, False, True)
    col_node = {}
    for p in model["pilares"]:
        nm = node_at(p["x"], p["y"])
        col_node[p["nombre"]] = nm
        m.def_support(nm, False, False, True, False, False, True)
    # eliminar movimiento de solido rigido en plano
    cen = min(model["pilares"], key=lambda p: (p["x"] - (x0 + W / 2))**2 + (p["y"] - (y0 + H / 2))**2)
    ncen = col_node[cen["nombre"]]
    m.def_support(ncen, True, True, True, False, False, True)
    # otro pilar para impedir giro en planta
    otro = max(model["pilares"], key=lambda p: (p["x"] - cen["x"])**2 + (p["y"] - cen["y"])**2)
    m.def_support(col_node[otro["nombre"]], True, False, True, False, False, True)

    # cargas
    peso = mp["rho"] * G_ACC * t
    for c in surf["cargas"]:
        for q in m.quads:
            m.add_quad_surface_pressure(q, c["qz"], case=c["caso"])
    for q in m.quads:
        m.add_quad_surface_pressure(q, -peso, case="G")

    casos = sorted({c["caso"] for c in surf["cargas"]} | {"G"})
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    res = {"combos_meta": meta, "pilares": {}, "losa": {},
           "info": {"x0": x0, "y0": y0, "W": W, "H": H, "espesor": t,
                    "peso_losa_N_m2": peso, "material": mat, "mesh": mesh}}

    # reacciones de pilar
    for p in model["pilares"]:
        nd = m.nodes[col_node[p["nombre"]]]
        res["pilares"][p["nombre"]] = {
            "x": p["x"], "y": p["y"], "lado": p["lado"], "posicion": p["posicion"],
            "Rz": {combo: nd.RxnFZ[combo] for combo in combos},
        }

    # esfuerzos de placa + deformada
    for combo in combos:
        quads = []
        for q in m.quads.values():
            M = q.moment(0, 0, True, combo)
            cx = (q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4
            cy = (q.i_node.Y + q.j_node.Y + q.m_node.Y + q.n_node.Y) / 4
            quads.append({"x": cx, "y": cy, "Mx": float(M[0, 0]), "My": float(M[1, 0]), "Mxy": float(M[2, 0])})
        defl = [{"x": nd.X, "y": nd.Y, "dz": nd.DZ[combo]} for nd in m.nodes.values()]
        res["losa"][combo] = {"quads": quads, "deformada": defl}

    # equilibrio
    area = W * H
    qELU = 0.0
    for c in surf["cargas"]:
        qELU += abs(c["qz"]) * combos["ELU"].get(c["caso"], 0.0)
    qELU += peso * combos["ELU"].get("G", 0.0)
    Rz = sum(res["pilares"][p["nombre"]]["Rz"]["ELU"] for p in model["pilares"])
    res["equilibrio"] = {"aplicada_ELU_kN": qELU * area / 1e3, "reaccion_ELU_kN": Rz / 1e3,
                         "error_pct": abs(qELU * area - Rz) / (qELU * area) * 100}
    return m, res


if __name__ == "__main__":
    ifc = sys.argv[1] if len(sys.argv) > 1 else "proyecto-losa-plana/losa_plana.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "proyecto-losa-plana/resultados.json"
    model = parse(ifc)
    json.dump(model, open("proyecto-losa-plana/modelo_neutro.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    _, res = solve(model)
    json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Resultados losa plana:", out)
    eq = res["equilibrio"]
    print(f"  equilibrio ELU: aplicada={eq['aplicada_ELU_kN']:.1f} reaccion={eq['reaccion_ELU_kN']:.1f} "
          f"error={eq['error_pct']:.2f}%")
    for nm, p in res["pilares"].items():
        print(f"  {nm} ({p['posicion']:8s}) Rz_ELU={p['Rz']['ELU']/1e3:7.1f} kN")
