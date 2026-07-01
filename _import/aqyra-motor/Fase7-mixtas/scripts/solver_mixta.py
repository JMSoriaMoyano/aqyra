"""
Solver de VIGA MIXTA biapoyada (reutiliza el solver de barras, PyNite).

La viga es estaticamente determinada: M(x) y V(x) no dependen de la seccion, asi que
se resuelven dos FASES de carga sobre la misma viga:
  - CONSTRUCCION (sin apear): acero solo bajo hormigon fresco + sobrecarga de ejecucion.
  - MIXTA (servicio): cargas permanentes totales + sobrecarga de uso.

La flecha se evalua en verificacion_mixta con la rigidez de cada fase (acero / mixta
con coeficiente de equivalencia). Aqui se entregan esfuerzos y diagramas.
Convencion: viga segun X; carga gravitatoria -Y; flexion fuerte = Mz, cortante = Fy.
SI (N, m).
"""
import sys
import os
import json
from Pynite import FEModel3D
from combinaciones import build_combos

G_ACC = 9.81
NPTS = 17


def parse(ifc_path):
    import ifcopenshell
    ifc = ifcopenshell.open(ifc_path)
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        mats[mp.Material.Name] = {"E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fck": d.get("CompressiveStrength"), "fctm": d.get("TensileStrength"),
            "fy": d.get("YieldStress")}
    sm = ifc.by_type("IfcStructuralCurveMember")[0]
    ps = {}
    for rel in getattr(sm, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
            pd = rel.RelatingPropertyDefinition
            ps[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                           if p.is_a("IfcPropertySingleValue") and p.NominalValue}
    v = ps["Pset_Estructurando_VigaMixta"]; lo = ps["Pset_Estructurando_Losa"]
    co = ps["Pset_Estructurando_Conectores"]; cg = ps["Pset_Estructurando_Cargas_Mixta"]
    return {"materiales": mats,
            "viga": {"L": v["Luz_m"], "sep": v["Separacion_m"], "n_elem": int(v.get("NumElementos", 16)),
                     "perfil": v["Perfil"], "acero": v["MaterialAcero"], "hormigon": v["MaterialHormigon"],
                     "apeado": int(v.get("Apeado", 0)),
                     "A": v["A_m2"], "h": v["h_m"], "b": v["b_m"], "tw": v["tw_m"], "tf": v["tf_m"],
                     "Iy": v["Iy_m4"], "Wply": v["Wply_m3"], "Avz": v["Avz_m2"]},
            "losa": {"ht": lo["ht_m"], "hp": lo["hp_m"], "hc": lo["hc_m"], "b0": lo["b0_m"],
                     "nervios": lo.get("nervios", "perpendicular"), "nr": int(lo.get("nr", 1))},
            "conectores": {"d": co["d_m"], "hsc": co["hsc_m"], "fu": co["fu_Pa"], "sep_long": co["sep_long_m"]},
            "cargas": {"G_losa": cg["G_losa_Pa"], "G2": cg["G2_perm_Pa"], "Q": cg["Q_uso_Pa"],
                       "Qc": cg["Qc_ejec_Pa"]}}


def _solve_fase(model, w_G, w_Q):
    """Resuelve la viga biapoyada con cargas lineales (N/m) por caso G y Q."""
    v = model["viga"]; mat = v["acero"]; mp = model["materiales"][mat]
    L = v["L"]; n = v["n_elem"]
    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    # seccion: flexion fuerte en el plano XY -> Iz = Iy_fuerte
    m.add_section("S", v["A"], v["Iy"] / 2, v["Iy"], v["Iy"])  # Iy_p(menor) irrelevante; Iz_p=Iy fuerte
    dx = L / n
    for i in range(n + 1):
        m.add_node(f"N{i}", i * dx, 0.0, 0.0)
    for i in range(n + 1):
        m.def_support(f"N{i}", False, False, True, True, True, False)  # fuera de plano fijo
    m.def_support("N0", True, True, True, True, True, False)
    m.def_support(f"N{n}", False, True, True, True, True, False)
    for i in range(n):
        m.add_member(f"E{i}", f"N{i}", f"N{i+1}", mat, "S")
        m.add_member_dist_load(f"E{i}", "FY", -w_G, -w_G, 0.0, dx, case="G")
        m.add_member_dist_load(f"E{i}", "FY", -w_Q, -w_Q, 0.0, dx, case="Q")
    combos, meta = build_combos(["G", "Q"])
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)
    out = {"combos_meta": meta}
    for combo in combos:
        Ms, Vs, xs = [], [], []
        for i in range(n):
            mb = m.members[f"E{i}"]
            xx, MM = mb.moment_array("Mz", 3, combo)
            _, VV = mb.shear_array("Fy", 3, combo)
            for k in range(3):
                xs.append(i * dx + xx[k]); Ms.append(float(MM[k])); Vs.append(float(VV[k]))
        out[combo] = {"M_max": max(abs(mm) for mm in Ms), "V_max": max(abs(vv) for vv in Vs),
                      "x": xs, "M": Ms, "V": Vs}
    return out


def solve(model):
    v = model["viga"]; c = model["cargas"]; sep = v["sep"]
    mp = model["materiales"][v["acero"]]
    w_steel = v["A"] * mp["rho"] * G_ACC
    w_losa = c["G_losa"] * sep
    w_g2 = c["G2"] * sep
    w_q = c["Q"] * sep
    w_qc = c["Qc"] * sep
    # fase mixta: G = acero + losa + cargas muertas; Q = uso
    mixta = _solve_fase(model, w_steel + w_losa + w_g2, w_q)
    # fase construccion: G = acero + hormigon fresco; Q = ejecucion
    constr = _solve_fase(model, w_steel + w_losa, w_qc)
    res = {"info": {"L": v["L"], "sep": sep, "perfil": v["perfil"], "apeado": v["apeado"],
                    "acero": v["acero"], "hormigon": v["hormigon"]},
           "cargas_kN_m": {"w_steel": w_steel / 1e3, "w_losa": w_losa / 1e3, "w_g2": w_g2 / 1e3,
                           "w_q": w_q / 1e3, "w_qc": w_qc / 1e3},
           "mixta": mixta, "construccion": constr}
    return res


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ifc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-viga-mixta", "viga_mixta.ifc")
    proj = os.path.dirname(ifc)
    model = parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    res = solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    wm = res["mixta"]["ELU"]; wc = res["construccion"]["ELU"]
    print("VIGA MIXTA %s L=%.1f m  sep=%.1f m" % (res["info"]["perfil"], res["info"]["L"], res["info"]["sep"]))
    print("  fase MIXTA   ELU: M_Ed=%.0f kN.m  V_Ed=%.0f kN" % (wm["M_max"] / 1e3, wm["V_max"] / 1e3))
    print("  fase CONSTR. ELU: M_Ed=%.0f kN.m  V_Ed=%.0f kN" % (wc["M_max"] / 1e3, wc["V_max"] / 1e3))
