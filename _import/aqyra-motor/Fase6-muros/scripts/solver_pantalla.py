"""
PANTALLA DE CONTENCION ANCLADA. Predimensionado EC7 + EC2.

La pantalla se idealiza como VIGA VERTICAL (reutiliza el solver de barras / el modelo
de "viga sobre muelles" del pilote):
  - empuje ACTIVO del trasdos (Rankine/Coulomb + sobrecarga + agua) como carga,
  - el terreno DELANTE del empotramiento como MUELLES horizontales (balasto kh) que
    movilizan el empuje PASIVO,
  - el ANCLA como APOYO horizontal en su nivel -> su reaccion es la fuerza del ancla.

Salidas: fuerza de ancla, ley de momentos M(z) y cortantes del fuste, deformada, y
reaccion del terreno (pasivo movilizado). La longitud de bulbo/libre y la flexion EC2
se calculan en verificacion_pantalla.

Convencion: z hacia abajo desde la coronacion; +X = sentido del empuje activo.
SI (N, m, Pa).
"""
import sys
import os
import json
import math
import ifcopenshell
from Pynite import FEModel3D
from combinaciones import build_combos
from solver_muro import ka_rankine, ka_coulomb, kp_rankine


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
    g = ps["Pset_Estructurando_Pantalla"]
    a = ps["Pset_Estructurando_Ancla"]
    t = ps["Pset_Estructurando_Terreno"]
    q = ps.get("Pset_Estructurando_Carga_q", {}).get("Sobrecarga_Pa", 0.0)
    matn = None
    for rel in getattr(pm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matn = rel.RelatingMaterial.Name
    return {"materiales": mats,
            "pantalla": {"tipo": g.get("Tipo", "anclada"), "t": g["Espesor_m"], "h": g["ExcavacionH_m"],
                         "d": g["Empotramiento_m"], "L": g["Long_m"], "kh": g["BalastoHorizontal_N_m3"],
                         "n_elem": int(g.get("NumElementos", 40)), "material": matn or g.get("Material")},
            "ancla": {"z": a["Profundidad_m"], "incl": a["Inclinacion_grados"], "sep": a["Separacion_m"],
                      "D_bulbo": a["DiamBulbo_m"], "tau": a["RozamientoBulbo_Pa"],
                      "fs_bulbo": a["FS_Bulbo"], "n_filas": int(a.get("NumFilas", 1))},
            "terreno": {"metodo": t.get("Metodo", "rankine"), "gamma": t["Gamma_N_m3"], "phi": t["Phi_grados"],
                        "c": t["Cohesion_Pa"], "beta": t["Beta_grados"], "delta": t["DeltaMuro_grados"],
                        "phi_pas": t["PhiPasivo_grados"], "gamma_pas": t["GammaPasivo_N_m3"],
                        "Rd": t["Rd_Pa"], "nf": t["NivelFreatico_m"], "gamma_w": t["GammaAgua_N_m3"]},
            "sobrecarga": q}


def _coef(t):
    delta = t["delta"] if t["metodo"] == "coulomb" else 0.0
    Ka = ka_coulomb(t["phi"], delta, t["beta"]) if t["metodo"] == "coulomb" else ka_rankine(t["phi"], t["beta"])
    Kp = kp_rankine(t["phi_pas"])
    return Ka, Kp


def solve(model):
    p = model["pantalla"]; t = model["terreno"]; mat = p["material"]; mp = model["materiales"][mat]
    L = p["L"]; h = p["h"]; n = p["n_elem"]; kh = p["kh"]; tp = p["t"]
    Ka, Kp = _coef(t)
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    q = model["sobrecarga"]

    # seccion rectangular por metro (ancho 1 m, canto = espesor pantalla)
    A = 1.0 * tp; I = 1.0 * tp ** 3 / 12; J = tp ** 3 / 3
    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_section("PANT", A, I, I, J)
    dz = L / n
    for i in range(n + 1):
        m.add_node(f"N{i}", 0.0, 0.0, -i * dz)
    for i in range(n):
        m.add_member(f"E{i}", f"N{i}", f"N{i+1}", mat, "PANT")
    # restricciones fuera de plano + vertical en el pie
    for i in range(n + 1):
        m.def_support(f"N{i}", False, True, False, True, False, True)
    m.def_support("N0", False, True, False, True, False, True)
    m.def_support(f"N{n}", False, True, True, True, False, True)  # apoyo vertical en el pie
    # muelles del terreno delante (solo en el empotramiento: profundidad > h)
    spring_nodes = []
    for i in range(n + 1):
        depth = i * dz
        if depth > h + 1e-9:
            trib = dz if 0 < i < n else dz / 2
            k = kh * 1.0 * trib
            m.def_support_spring(f"N{i}", "DX", k)
            spring_nodes.append((i, k))
    # ancla: apoyo horizontal en el nodo mas proximo a z_a
    a_idx = max(1, min(n - 1, round(model["ancla"]["z"] / dz)))
    m.def_support(f"N{a_idx}", True, True, False, True, False, True)  # DX fijo = ancla

    # cargas (empuje activo en el trasdos), por caso; x1,x2 LOCALES (0..dz)
    for i in range(n):
        d0 = i * dz; d1 = (i + 1) * dz
        # suelo activo (G): tension efectiva
        s0 = Ka * _sigv(t, d0, has_w, zw, gw)
        s1 = Ka * _sigv(t, d1, has_w, zw, gw)
        m.add_member_dist_load(f"E{i}", "FX", s0, s1, 0.0, dz, case="G")
        # sobrecarga (Q): constante
        m.add_member_dist_load(f"E{i}", "FX", Ka * q, Ka * q, 0.0, dz, case="Q")
        # agua (G): hidrostatica en el trasdos
        if has_w:
            w0 = gw * max(d0 - zw, 0.0); w1 = gw * max(d1 - zw, 0.0)
            if w0 or w1:
                m.add_member_dist_load(f"E{i}", "FX", w0, w1, 0.0, dz, case="G")

    casos = ["G", "Q"]
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    out = {"combos_meta": meta, "info": {"L": L, "h": h, "d": p["d"], "t": tp, "n": n,
            "kh": kh, "Ka": Ka, "Kp": Kp, "metodo": t["metodo"], "material": mat,
            "z_ancla": a_idx * dz, "dz": dz}}
    for combo in combos:
        pts = []
        for i in range(n):
            mb = m.members[f"E{i}"]
            zc = (i + 0.5) * dz
            pts.append({"z": zc, "M": mb.moment("My", dz / 2, combo), "V": mb.shear("Fz", dz / 2, combo)})
        defl = [{"z": i * dz, "dx": m.nodes[f"N{i}"].DX[combo]} for i in range(n + 1)]
        T_h = -m.nodes[f"N{a_idx}"].RxnFX[combo]   # reaccion del ancla (horizontal)
        # pasivo movilizado = suma de las fuerzas resistentes de los muelles (k*DX)
        Pp_mob = sum(k * m.nodes[f"N{i}"].DX[combo] for i, k in spring_nodes)
        M_max = max(pts, key=lambda r: abs(r["M"]))
        out[combo] = {"esfuerzos": pts, "deformada": defl, "T_h_kN": T_h / 1e3,
                      "Pp_mov_kN": Pp_mob / 1e3, "M_max_kNm": M_max["M"] / 1e3, "z_Mmax": M_max["z"]}
    # equilibrio horizontal ELU
    Ea = _empuje_activo_total(t, model, has_w, zw, gw) / 1e3
    bal = out["ELU"]
    H_elu = _empuje_activo_ELU(t, model, has_w, zw, gw) / 1e3
    err = abs((bal["T_h_kN"] + bal["Pp_mov_kN"]) - H_elu)
    out["equilibrio"] = {"Ea_caract_kN": Ea, "T_h_ELU_kN": bal["T_h_kN"], "Pp_mov_ELU_kN": bal["Pp_mov_kN"],
                         "H_aplicado_ELU_kN": H_elu, "error_pct": err / max(abs(H_elu), 1e-9) * 100}
    return out


def _sigv(t, z, has_w, zw, gw):
    if not has_w or z <= zw:
        return t["gamma"] * z
    return t["gamma"] * zw + (t["gamma"] - gw) * (z - zw)


def _empuje_activo_total(t, model, has_w, zw, gw):
    Ka, _ = _coef(t); L = model["pantalla"]["L"]; q = model["sobrecarga"]
    # integral del empuje activo caracteristico (suelo + sobrecarga + agua)
    n = 400; dz = L / n; E = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        E += (Ka * _sigv(t, z, has_w, zw, gw) + Ka * q + (gw * max(z - zw, 0) if has_w else 0)) * dz
    return E


def _empuje_activo_ELU(t, model, has_w, zw, gw):
    Ka, _ = _coef(t); L = model["pantalla"]["L"]; q = model["sobrecarga"]
    n = 400; dz = L / n; Eg = 0.0; Eq = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        Eg += (Ka * _sigv(t, z, has_w, zw, gw) + (gw * max(z - zw, 0) if has_w else 0)) * dz
        Eq += (Ka * q) * dz
    return 1.35 * Eg + 1.5 * Eq


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ifc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-pantalla-anclada", "pantalla.ifc")
    proj = os.path.dirname(ifc)
    model = parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    res = solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    e = res["ELU"]; eq = res["equilibrio"]
    print("PANTALLA anclada L=%.1f m  H_exc=%.1f  empot=%.1f  Ka=%.3f Kp=%.2f"
          % (res["info"]["L"], res["info"]["h"], res["info"]["d"], res["info"]["Ka"], res["info"]["Kp"]))
    print("  ELU: fuerza ancla (horiz) T_h=%.0f kN/m  M_max=%.0f kN.m/m (z=%.2f m)  pasivo mov.=%.0f kN/m"
          % (e["T_h_kN"], abs(e["M_max_kNm"]), e["z_Mmax"], e["Pp_mov_kN"]))
    print("  equilibrio horizontal ELU: error=%.2f %%" % eq["error_pct"])
