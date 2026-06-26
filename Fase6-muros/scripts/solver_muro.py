"""
MURO DE CONTENCION EN MENSULA (T-invertida). Predimensionado EC7 + EC2.

Tres bloques (desacoplados, practica estandar de predimensionado):
  A) EMPUJES del terreno: activo Rankine/Coulomb + sobrecarga + agua (freatico),
     y pasivo movilizable en la puntera.
  B) ESTABILIDAD geotecnica (la calcula verificacion_muro): vuelco (EQU),
     deslizamiento (GEO) y hundimiento (GEO, B' de Meyerhof).
  C) ESFUERZOS estructurales: el ALZADO como mensula vertical (viga sobre
     empotramiento), resuelto con el SOLVER DE BARRAS (PyNite) -> M(z), V(z).
     La puntera y el talon se calculan analiticamente en verificacion_muro.

Convencion: X horizontal (desde puntera x=0 hacia el trasdos), Z vertical hacia
arriba. z medido hacia abajo desde la coronacion del relleno para los empujes.
SI (N, m, Pa).
"""
import sys
import os
import json
import math
import ifcopenshell
from Pynite import FEModel3D
from combinaciones import build_combos

G_ACC = 9.81


# ---------------- COEFICIENTES DE EMPUJE ----------------
def ka_rankine(phi, beta=0.0):
    phir, br = math.radians(phi), math.radians(beta)
    if abs(beta) < 1e-9:
        return math.tan(math.radians(45 - phi / 2)) ** 2
    cb, cp = math.cos(br), math.cos(phir)
    r = math.sqrt(max(cb ** 2 - cp ** 2, 0.0))
    return cb * (cb - r) / (cb + r)


def ka_coulomb(phi, delta, beta=0.0, theta=0.0):
    phir, dr, br, tr = map(math.radians, (phi, delta, beta, theta))
    num = math.cos(phir - tr) ** 2
    raiz = math.sqrt(math.sin(phir + dr) * math.sin(phir - br) /
                     (math.cos(dr + tr) * math.cos(tr - br)))
    den = math.cos(tr) ** 2 * math.cos(dr + tr) * (1 + raiz) ** 2
    return num / den


def kp_rankine(phi):
    return math.tan(math.radians(45 + phi / 2)) ** 2


# ---------------- PARSER IFC ----------------
def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue}
        mats[mp.Material.Name] = {"E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fck": d.get("CompressiveStrength"), "fctm": d.get("TensileStrength")}
    sm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    ps = {}
    for rel in getattr(sm, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties") and rel.RelatingPropertyDefinition.is_a("IfcPropertySet"):
            pd = rel.RelatingPropertyDefinition
            ps[pd.Name] = {p.Name: p.NominalValue.wrappedValue for p in pd.HasProperties
                           if p.is_a("IfcPropertySingleValue") and p.NominalValue}
    g = ps["Pset_Estructurando_Muro"]
    t = ps["Pset_Estructurando_Terreno"]
    q = ps.get("Pset_Estructurando_Carga_Muro_q", {}).get("Sobrecarga_Pa", 0.0)
    cor = ps.get("Pset_Estructurando_Carga_Muro_coronacion", {})
    matn = None
    for rel in getattr(sm, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            matn = rel.RelatingMaterial.Name
    return {"materiales": mats,
            "muro": {"tipo": g.get("Tipo", "mensula"), "Hm": g["AlturaAlzado_m"],
                     "t_alz": g["EspesorAlzado_m"], "e_z": g["CantoZapata_m"],
                     "puntera": g["Puntera_m"], "talon": g["Talon_m"], "B": g["AnchoZapata_m"],
                     "Df": g["ProfTierrasDelante_m"], "material": matn or g.get("Material")},
            "terreno": {"metodo": t.get("Metodo", "rankine"), "gamma": t["Gamma_N_m3"],
                        "phi": t["Phi_grados"], "c": t["Cohesion_Pa"], "beta": t["Beta_grados"],
                        "delta": t["DeltaMuro_grados"], "phi_pas": t["PhiPasivo_grados"],
                        "gamma_pas": t["GammaPasivo_N_m3"], "f_pas": t["FraccionPasivo"],
                        "phi_base": t["PhiBase_grados"], "adh_base": t["AdherenciaBase_Pa"],
                        "Rd": t["Rd_Pa"], "nf": t["NivelFreatico_m"], "gamma_w": t["GammaAgua_N_m3"]},
            "sobrecarga": q, "coronacion": cor}


# ---------------- EMPUJES (caracteristicos) ----------------
def empujes(model, n=400):
    """Integra las presiones sobre el plano virtual del trasdos (altura total H,
    desde la coronacion del relleno hasta la base de la zapata). Devuelve
    componentes caracteristicas con fuerza H, V y brazo z sobre la base."""
    m = model["muro"]; t = model["terreno"]
    H = m["Hm"] + m["e_z"]                 # altura total resistida (Rankine: plano vertical en el talon)
    gamma, phi, c, beta = t["gamma"], t["phi"], t["c"], t["beta"]
    delta = t["delta"] if t["metodo"] == "coulomb" else 0.0
    Ka = ka_coulomb(phi, delta, beta) if t["metodo"] == "coulomb" else ka_rankine(phi, beta)
    q = model["sobrecarga"]
    gw = t["gamma_w"]
    zw = t["nf"]                            # profundidad del NF desde coronacion (<0 = sin agua)
    has_w = zw is not None and zw >= 0.0

    dz = H / n
    E_soil = M_soil = 0.0      # empuje activo del suelo (G) y su momento sobre la base
    E_water = M_water = 0.0    # empuje hidrostatico (G)
    sigv_eff = q               # tension vertical efectiva en coronacion (sobrecarga aparte)
    # se integra el suelo con su peso; la sobrecarga se trata como componente aparte (Q)
    sigv_soil = 0.0
    for i in range(n):
        z = (i + 0.5) * dz                 # profundidad media de la franja
        # peso efectivo del suelo segun NF
        g_eff = gamma - gw if (has_w and z > zw) else gamma
        sigv_soil += g_eff * dz
        sh_soil = max(Ka * sigv_soil - 2 * c * math.sqrt(Ka), 0.0)
        za = H - z                         # brazo sobre la base
        E_soil += sh_soil * dz
        M_soil += sh_soil * dz * za
        if has_w and z > zw:
            u = gw * (z - zw)
            E_water += u * dz
            M_water += u * dz * za
    # sobrecarga: presion horizontal constante Ka*q sobre toda la altura (Q)
    E_q = Ka * q * H
    M_q = E_q * (H / 2)

    def comp(name, Eh_total, M, caso):
        za = M / Eh_total if Eh_total else 0.0
        # Coulomb: el empuje del suelo y de la sobrecarga se inclina delta
        if name in ("empuje_suelo", "empuje_sobrecarga") and delta:
            Eh = Eh_total * math.cos(math.radians(delta))
            Ev = Eh_total * math.sin(math.radians(delta))
        else:
            Eh, Ev = Eh_total, 0.0
        return {"nombre": name, "caso": caso, "Eh_kN": Eh / 1e3, "Ev_kN": Ev / 1e3,
                "z_kN_m": za, "x_Ev_m": m["B"]}

    comps = [comp("empuje_suelo", E_soil, M_soil, "G"),
             comp("empuje_sobrecarga", E_q, M_q, "Q")]
    if E_water:
        comps.append(comp("empuje_agua", E_water, M_water, "G"))

    # pasivo movilizable en la puntera (caracteristico, ya reducido por f_pas)
    Kp = kp_rankine(t["phi_pas"])
    Pp = 0.5 * Kp * t["gamma_pas"] * m["Df"] ** 2
    Pp_mov = t["f_pas"] * Pp
    return {"H": H, "Ka": Ka, "Kp": Kp, "metodo": t["metodo"], "delta": delta,
            "componentes": comps, "pasivo_kN": Pp_mov / 1e3, "z_pasivo_m": m["Df"] / 3}


# ---------------- PESOS ESTABILIZADORES (caracteristicos) ----------------
def pesos(model):
    m = model["muro"]; t = model["terreno"]
    rho = model["materiales"][m["material"]]["rho"]
    gc = rho * G_ACC                         # peso especifico del hormigon (N/m3)
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    Hm, t_alz, e_z = m["Hm"], m["t_alz"], m["e_z"]
    pun, tal, B, Df = m["puntera"], m["talon"], m["B"], m["Df"]
    x_alz = pun + t_alz / 2
    # peso del suelo sobre el talon (altura Hm); efectivo si sumergido
    h_w_heel = (Hm - zw) if (has_w and zw < Hm) else 0.0
    g_soil_dry = t["gamma"]
    W_soil_heel = tal * ((Hm - max(h_w_heel, 0)) * g_soil_dry + max(h_w_heel, 0) * (t["gamma"] - gw))
    items = [
        {"nombre": "peso_alzado", "W_kN": (t_alz * Hm * gc) / 1e3, "x_m": x_alz, "caso": "G"},
        {"nombre": "peso_zapata", "W_kN": (B * e_z * gc) / 1e3, "x_m": B / 2, "caso": "G"},
        {"nombre": "suelo_talon", "W_kN": W_soil_heel / 1e3, "x_m": pun + t_alz + tal / 2, "caso": "G"},
        {"nombre": "suelo_puntera", "W_kN": (pun * Df * t["gamma_pas"]) / 1e3, "x_m": pun / 2, "caso": "G"},
        {"nombre": "sobrecarga_talon", "W_kN": (model["sobrecarga"] * tal) / 1e3,
         "x_m": pun + t_alz + tal / 2, "caso": "Q"},
    ]
    cor = model.get("coronacion", {})
    if cor.get("N_G_N"):
        items.append({"nombre": "coron_G", "W_kN": cor["N_G_N"] / 1e3, "x_m": x_alz, "caso": "G"})
    if cor.get("N_Q_N"):
        items.append({"nombre": "coron_Q", "W_kN": cor["N_Q_N"] / 1e3, "x_m": x_alz, "caso": "Q"})
    return items, gc


# ---------------- ESFUERZOS DEL ALZADO (solver de barras) ----------------
def solve_alzado(model):
    """El alzado como mensula vertical empotrada en la zapata; presiones del
    trasdos como cargas distribuidas por caso (G suelo+agua, Q sobrecarga)."""
    m = model["muro"]; t = model["terreno"]
    mat = m["material"]; mp = model["materiales"][mat]
    Hm, t_alz = m["Hm"], m["t_alz"]
    # seccion rectangular por metro de muro (ancho 1 m, canto t_alz)
    A = 1.0 * t_alz
    I = 1.0 * t_alz ** 3 / 12
    J = t_alz ** 3 * 1.0 / 3  # aprox (no relevante: sin torsion)

    gamma, phi, beta = t["gamma"], t["phi"], t["beta"]
    delta = t["delta"] if t["metodo"] == "coulomb" else 0.0
    Ka = ka_coulomb(phi, delta, beta) if t["metodo"] == "coulomb" else ka_rankine(phi, beta)
    q = model["sobrecarga"]; gw = t["gamma_w"]; zw = t["nf"]
    has_w = zw is not None and zw >= 0.0
    # presiones del suelo sobre el alzado: la coronacion del relleno coincide con la
    # coronacion del alzado -> profundidad 0 arriba, Hm en la base del alzado
    # arriba (z'=0): sh_soil = 0 ; base (z'=Hm): sh_soil = Ka*gamma*Hm (sin agua)
    p_soil_top = 0.0
    g_eff_base = gamma  # si NF dentro del alzado, el tramo inferior usa g'; aprox lineal por simplicidad
    p_soil_base = Ka * gamma * Hm
    p_q = Ka * q  # constante
    # agua sobre el alzado (si NF dentro del alzado): triangular desde NF
    p_w_base = gw * (Hm - zw) if (has_w and zw < Hm) else 0.0
    p_w_top = 0.0

    n = 22
    M = FEModel3D()
    M.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    M.add_section("ALZ", A, I, I, J)
    dz = Hm / n
    for i in range(n + 1):
        M.add_node(f"N{i}", 0.0, 0.0, i * dz)
    M.def_support("N0", True, True, True, True, True, True)  # empotrado en la base
    # estabilizar fuera de plano
    for i in range(1, n + 1):
        M.def_support(f"N{i}", False, True, False, True, False, True)
    for i in range(n):
        M.add_member(f"E{i}", f"N{i}", f"N{i+1}", mat, "ALZ")
    # cargas distribuidas lineales (FX) por caso; w(z) en N/m (ancho 1 m)
    for i in range(n):
        z0 = i * dz; z1 = (i + 1) * dz       # altura desde la base
        d0 = Hm - z0; d1 = Hm - z1            # profundidad desde coronacion
        # NOTA: x1,x2 de add_member_dist_load son LOCALES al elemento (0..dz)
        # suelo (G): lineal con la profundidad
        w0 = p_soil_base * (d0 / Hm)
        w1 = p_soil_base * (d1 / Hm)
        M.add_member_dist_load(f"E{i}", "FX", w0, w1, 0.0, dz, case="G")
        # sobrecarga (Q): constante
        M.add_member_dist_load(f"E{i}", "FX", p_q, p_q, 0.0, dz, case="Q")
        # agua (G): triangular desde el NF
        if p_w_base:
            hw = Hm - zw
            ww0 = p_w_base * (max(d0 - zw, 0) / hw) if hw > 0 else 0.0
            ww1 = p_w_base * (max(d1 - zw, 0) / hw) if hw > 0 else 0.0
            M.add_member_dist_load(f"E{i}", "FX", ww0, ww1, 0.0, dz, case="G")
    # carga horizontal en coronacion (Q)
    if model.get("coronacion", {}).get("H_Q_N"):
        M.add_node_load(f"N{n}", "FX", model["coronacion"]["H_Q_N"], case="Q")

    casos = ["G", "Q"]
    combos, meta = build_combos(casos)
    for nm, fac in combos.items():
        M.add_load_combo(nm, fac)
    M.analyze_linear(check_stability=False)

    out = {"combos_meta": meta, "info": {"Hm": Hm, "t_alz": t_alz, "n": n}}
    for combo in combos:
        pts = []
        for i in range(n):
            mb = M.members[f"E{i}"]
            zc = (i + 0.5) * dz
            pts.append({"z": zc, "M": mb.moment("My", dz / 2, combo), "V": mb.shear("Fz", dz / 2, combo)})
        # seccion critica = base del alzado (arranque sobre la zapata), x=0 de E0
        M_base = M.members["E0"].moment("My", 0.0, combo)
        V_base = M.members["E0"].shear("Fz", 0.0, combo)
        out[combo] = {"esfuerzos": pts, "M_base": M_base, "V_base": V_base}
    return out


def solve(model):
    emp = empujes(model)
    pes, gc = pesos(model)
    alz = solve_alzado(model)
    # equilibrio de comprobacion: la distribucion lineal de presiones bajo la zapata
    # debe equilibrar SUM(V) y SUM(M) -> se valida en verificacion (B' Meyerhof).
    res = {"info": {**alz["info"], "B": model["muro"]["B"], "e_z": model["muro"]["e_z"],
                    "puntera": model["muro"]["puntera"], "talon": model["muro"]["talon"],
                    "material": model["muro"]["material"], "gamma_hormigon_kN_m3": gc / 1e3,
                    "H": emp["H"], "Ka": emp["Ka"], "Kp": emp["Kp"], "metodo": emp["metodo"]},
           "empujes": emp, "pesos": pes, "alzado": alz}
    return res


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    ifc = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-muro-mensula", "muro.ifc")
    proj = os.path.dirname(ifc)
    model = parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    res = solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    emp = res["empujes"]
    Eh = sum(c["Eh_kN"] for c in emp["componentes"])
    Mmax = abs(res["alzado"]["ELU"]["M_base"])
    H_ = emp["H"]; met = emp["metodo"]; Ka_ = emp["Ka"]; Kp_ = emp["Kp"]; pas = emp["pasivo_kN"]
    print("MURO mensula H=%.2f m  metodo=%s  Ka=%.3f Kp=%.2f" % (H_, met, Ka_, Kp_))
    print("  empuje horizontal total (caract.) = %.1f kN/m  | pasivo movil. = %.1f kN/m" % (Eh, pas))
    print("  alzado: M_Ed(base) = %.1f kN.m/m  (ELU)" % (Mmax / 1e3))
