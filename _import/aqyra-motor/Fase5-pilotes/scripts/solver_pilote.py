"""
PILOTE (cimentacion profunda). Dos fisicas desacopladas (predimensionado):

 A) Capacidad AXIL geotecnica (EN 1997-1, EC7): resistencia por fuste + punta.
 B) Comportamiento LATERAL: pilote como VIGA SOBRE MUELLES horizontales
    (modulo de balasto horizontal), resuelto con el SOLVER DE BARRAS (PyNite).

SI (N, m, Pa).
"""
import sys
import json
import ifcopenshell
import math
from Pynite import FEModel3D
from combinaciones import build_combos

GAMMA_B = 1.10   # resistencia de punta (EC7, persistente) [confirmar AN/DA]
GAMMA_S = 1.10   # resistencia de fuste


def capacidad_axil(D, L, qs, qb):
    """Resistencia axil de calculo (compresion): Rc,d = Rs/gS + Rb/gB."""
    perimetro = math.pi * D
    Ab = math.pi * D ** 2 / 4
    Rs_k = perimetro * L * qs
    Rb_k = Ab * qb
    Rc_d = Rs_k / GAMMA_S + Rb_k / GAMMA_B
    return {"Rs_k_kN": Rs_k / 1e3, "Rb_k_kN": Rb_k / 1e3,
            "Rc_d_kN": Rc_d / 1e3, "perimetro_m": perimetro, "Ab_m2": Ab}


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        mats[mp.Material.Name] = {"E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fck": d.get("CompressiveStrength"), "fctm": d.get("TensileStrength")}
    pm = ifc.by_type("IfcStructuralCurveMember")[0]
    ps = {}
    for rel in getattr(pm, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
            pd = rel.RelatingPropertyDefinition
            ps[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                           if p.is_a("IfcPropertySingleValue") and p.NominalValue}
    g = ps["Pset_Estructurando_Pilote"]
    cargas = {}
    for n, p in ps.items():
        if n.startswith("Pset_Estructurando_Carga_Pilote"):
            cargas[p["Caso"]] = {"N": p.get("N_N", 0.0), "H": p.get("H_N", 0.0), "M": p.get("M_Nm", 0.0)}
    matn = None
    for rel in getattr(pm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matn = rel.RelatingMaterial.Name
    return {"materiales": mats, "pilote": {
        "D": g["Diametro"], "L": g["Longitud"], "material": matn or g.get("Material"),
        "kh": g["BalastoHorizontal_N_m3"], "qs": g["FusteUnit_Pa"], "qb": g["PuntaUnit_Pa"],
        "n_elem": int(g.get("NumElementos", 24)), "cabeza": g.get("Cabeza", "libre")}, "cargas": cargas}


def solve(model):
    p = model["pilote"]; mat = p["material"]; mp = model["materiales"][mat]
    D = p["D"]; L = p["L"]; kh = p["kh"]; n = p["n_elem"]
    A = math.pi * D ** 2 / 4
    I = math.pi * D ** 4 / 64
    J = 2 * I

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_section("PIL", A, I, I, J)
    dz = L / n
    for i in range(n + 1):
        m.add_node(f"N{i}", 0.0, 0.0, -i * dz)   # de la cabeza (z=0) a la punta (z=-L)
    for i in range(n):
        m.add_member(f"E{i}", f"N{i}", f"N{i+1}", mat, "PIL")
    # muelles laterales (X) por nodo: k = kh * D * trib ; coaccionar fuera de plano
    for i in range(n + 1):
        trib = dz if 0 < i < n else dz / 2
        m.def_support(f"N{i}", False, True, False, True, False, True)  # plano XZ (DY,RX,RZ fijos)
        m.def_support_spring(f"N{i}", "DX", kh * D * trib)
    # base: apoyo vertical (estabiliza el modelo lateral) ; punta tambien lateral por muelle
    m.def_support(f"N{n}", False, True, True, True, False, True)

    # combinaciones (cargas laterales H y momento M en cabeza)
    casos = sorted(model["cargas"].keys())
    for caso, c in model["cargas"].items():
        if c["H"]:
            m.add_node_load("N0", "FX", c["H"], case=caso)
        if c["M"]:
            m.add_node_load("N0", "MY", c["M"], case=caso)
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    res = {"combos_meta": meta, "info": {"D": D, "L": L, "material": mat, "kh": kh,
           "I_m4": I, "A_m2": A, "n_elem": n}, "pilote": {}}
    for combo in combos:
        pts = []
        for i in range(n):
            mb = m.members[f"E{i}"]
            zc = -(i + 0.5) * dz
            pts.append({"z": zc, "M": mb.moment("My", dz / 2, combo), "V": mb.shear("Fz", dz / 2, combo)})
        defl = [{"z": -i * dz, "dx": m.nodes[f"N{i}"].DX[combo]} for i in range(n + 1)]
        res["pilote"][combo] = {"esfuerzos": pts, "deformada": defl}
    # equilibrio lateral ELU
    H_ap = sum(c["H"] * combos["ELU"].get(caso, 0) for caso, c in model["cargas"].items())
    Rx = sum((-kh * D * (dz if 0 < i < n else dz / 2)) * m.nodes[f"N{i}"].DX["ELU"] for i in range(n + 1))
    res["equilibrio"] = {"H_aplicado_ELU_kN": H_ap / 1e3, "reaccion_muelles_ELU_kN": Rx / 1e3,
                         "error_pct": abs(H_ap + Rx) / abs(H_ap) * 100 if H_ap else 0.0}
    return m, res


if __name__ == "__main__":
    ifc = sys.argv[1] if len(sys.argv) > 1 else "proyecto-pilote/pilote.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "proyecto-pilote/resultados.json"
    model = parse(ifc)
    json.dump(model, open("proyecto-pilote/modelo_neutro.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    cap = capacidad_axil(model["pilote"]["D"], model["pilote"]["L"], model["pilote"]["qs"], model["pilote"]["qb"])
    _, res = solve(model)
    res["capacidad_axil"] = cap
    json.dump(res, open(out, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    e = res["pilote"]["ELU"]["esfuerzos"]
    Mmax = max(abs(pt["M"]) for pt in e)
    dxh = res["pilote"]["ELS_car"]["deformada"][0]["dx"] if "ELS_car" in res["pilote"] else res["pilote"]["ELU"]["deformada"][0]["dx"]
    print(f"PILOTE Ø{model['pilote']['D']} L={model['pilote']['L']} m")
    print(f"  EC7 axil Rc,d = {cap['Rc_d_kN']:.0f} kN (fuste {cap['Rs_k_kN']:.0f} + punta {cap['Rb_k_kN']:.0f}, char.)")
    print(f"  lateral: M_max = {Mmax/1e3:.1f} kN·m  flecha cabeza = {abs(dxh)*1e3:.1f} mm")
    print(f"  equilibrio lateral error = {res['equilibrio']['error_pct']:.2f}%")
