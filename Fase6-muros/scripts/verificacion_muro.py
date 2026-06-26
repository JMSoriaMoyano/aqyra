"""
Verificacion del MURO DE CONTENCION en mensula.

ESTABILIDAD geotecnica (EC7, EN 1997-1):
  - VUELCO (EQU): M_estab,d >= M_vuelco,d      (gamma EQU)
  - DESLIZAMIENTO (GEO, DA-2*): H_d <= R_d = (N_fav*tan(phi_b)+a*B)/gR_h + Pp_mov/gR_e
  - HUNDIMIENTO (GEO, DA-2*): q_Ed = N_d/B' <= R_d ; B' = B - 2e (Meyerhof)
    + comprobacion de despegue (e <= B/6)

ESTRUCTURA (EC2, EN 1992-1-1) por metro de muro:
  - ALZADO: flexion + cortante en el arranque (M_base, V_base del solver de barras)
  - PUNTERA: mensula bajo la presion del terreno (hacia arriba)
  - TALON: mensula bajo el peso de tierras+sobrecarga (hacia abajo) menos la reaccion

Enfoque DA-2*: coeficientes parciales sobre EFECTOS de las acciones y sobre las
RESISTENCIAS. Todos los NDP marcados [confirmar AN Espana].
SI (N, m, Pa).
"""
import sys
import os
import json
import math

# ---- Coeficientes parciales [confirmar AN Espana] ----
# EQU (vuelco)
G_DST_EQU = 1.10   # permanente desestabilizadora
G_STB_EQU = 0.90   # permanente estabilizadora
Q_DST_EQU = 1.50   # variable desestabilizadora
# STR/GEO (DA-2*): acciones
G_SUP = 1.35       # permanente desfavorable
G_INF = 1.00       # permanente favorable
Q_SUP = 1.50       # variable desfavorable
# Resistencias (DA-2*)
GR_H = 1.10        # deslizamiento
GR_V = 1.40        # hundimiento (resistencia del terreno)
GR_E = 1.40        # empuje pasivo

# Hormigon / acero
GC, GS = 1.50, 1.15
FYK = 500e6
FYD = FYK / GS
C_NOM = 0.050      # recubrimiento en contacto con el terreno (m)
PHI_BARRA = 0.020  # diametro estimado (m) para el canto util


def _sum(items, casos, key="W_kN", arm=None):
    s = 0.0
    for it in items:
        if it["caso"] in casos:
            s += it[key] * (it[arm] if arm else 1.0)
    return s


def flexion(M_Ed, d, fck, fctm, h, b=1.0):
    """Armadura de flexion (N.m por b=1 m) -> As (cm2/m) y cuantia minima EC2 9.2.1."""
    fcd = fck / GC
    if M_Ed <= 0 or d <= 0:
        As = 0.0
    else:
        # mu y brazo (rectangular)
        mu = M_Ed / (b * d ** 2 * fcd)
        mu = min(mu, 0.32)
        z = d * (0.5 + math.sqrt(max(0.25 - mu / 2, 0.0)))
        As = M_Ed / (z * FYD)
    As_min = max(0.26 * (fctm / FYK) * b * d, 0.0013 * b * d)
    As_prov = max(As, As_min)
    return {"M_Ed_kNm_m": M_Ed / 1e3, "As_cm2_m": As * 1e4,
            "As_min_cm2_m": As_min * 1e4, "As_prov_cm2_m": As_prov * 1e4,
            "rho": As_prov / (b * d), "ok": True}


def cortante(V_Ed, d, fck, As_prov, b=1.0):
    """V_Rd,c segun EC2 6.2.2 (sin armadura de cortante)."""
    k = min(1 + math.sqrt(0.2 / d), 2.0)
    rho_l = min(As_prov / (b * d), 0.02)
    fck_MPa = fck / 1e6
    vmin = 0.035 * k ** 1.5 * math.sqrt(fck_MPa)  # MPa
    vRdc = max(0.18 / GC * k * (100 * rho_l * fck_MPa) ** (1 / 3), vmin) * 1e6  # Pa
    VRdc = vRdc * b * d
    return {"V_Ed_kN_m": V_Ed / 1e3, "VRdc_kN_m": VRdc / 1e3,
            "u": V_Ed / VRdc if VRdc else 9.99, "ok": bool(V_Ed <= VRdc)}


def verificar(model, results):
    m = model["muro"]; t = model["terreno"]
    mp = model["materiales"][m["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]
    B = m["B"]; e_z = m["e_z"]; pun = m["puntera"]; tal = m["talon"]; t_alz = m["t_alz"]
    gc = results["info"]["gamma_hormigon_kN_m3"] * 1e3
    emp = results["empujes"]; comps = emp["componentes"]; pes = results["pesos"]

    # --- Resultantes caracteristicas ---
    Eh_G = sum(c["Eh_kN"] for c in comps if c["caso"] == "G")
    Eh_Q = sum(c["Eh_kN"] for c in comps if c["caso"] == "Q")
    Ev_G = sum(c["Ev_kN"] for c in comps if c["caso"] == "G")
    Ev_Q = sum(c["Ev_kN"] for c in comps if c["caso"] == "Q")
    Mh_G = sum(c["Eh_kN"] * c["z_kN_m"] for c in comps if c["caso"] == "G")  # momento vuelco (sobre base)
    Mh_Q = sum(c["Eh_kN"] * c["z_kN_m"] for c in comps if c["caso"] == "Q")
    W_G = _sum(pes, ("G",))
    W_Q = _sum(pes, ("Q",))
    Mw_G = _sum(pes, ("G",), arm="x_m")    # momento estabilizador sobre la puntera (x=0)
    Mw_Q = _sum(pes, ("Q",), arm="x_m")
    xEv = comps[0]["x_Ev_m"] if comps else B
    Pp = emp["pasivo_kN"]; zPp = emp["z_pasivo_m"]

    out = {"info": results["info"], "factores": {
        "EQU": {"G_dst": G_DST_EQU, "G_stb": G_STB_EQU, "Q_dst": Q_DST_EQU},
        "GEO_DA2*": {"G_sup": G_SUP, "Q_sup": Q_SUP, "gR_h": GR_H, "gR_v": GR_V, "gR_e": GR_E},
        "nota": "NDP [confirmar AN Espana]"}}

    # --- VUELCO (EQU) sobre la puntera (x=0) ---
    M_stb_d = G_STB_EQU * (Mw_G + Ev_G * xEv)            # variable favorable -> no se cuenta
    M_dst_d = G_DST_EQU * Mh_G + Q_DST_EQU * Mh_Q
    FS_vuelco_car = (Mw_G + Ev_G * xEv) / (Mh_G + Mh_Q) if (Mh_G + Mh_Q) else 9.99
    out["vuelco"] = {"M_estab_d_kNm": M_stb_d, "M_vuelco_d_kNm": M_dst_d,
                     "u": M_dst_d / M_stb_d if M_stb_d else 9.99,
                     "FS_caracteristico": FS_vuelco_car, "ok": bool(M_dst_d <= M_stb_d)}

    # --- DESLIZAMIENTO (GEO DA-2*) ---
    H_d = G_SUP * Eh_G + Q_SUP * Eh_Q
    N_fav = G_INF * W_G + G_INF * Ev_G                    # favorable (permanente); variable fav -> 0
    R_fric = (N_fav * math.tan(math.radians(t["phi_base"])) + t["adh_base"] / 1e3 * B) / GR_H
    R_pas = Pp / GR_E
    R_d = R_fric + R_pas
    N_k = W_G + W_Q + Ev_G + Ev_Q
    FS_desl_car = (N_k * math.tan(math.radians(t["phi_base"])) + t["adh_base"] / 1e3 * B + Pp) / (Eh_G + Eh_Q)
    out["deslizamiento"] = {"H_d_kN": H_d, "R_d_kN": R_d, "R_friccion_kN": R_fric,
                            "R_pasivo_kN": R_pas, "N_favorable_kN": N_fav,
                            "u": H_d / R_d if R_d else 9.99,
                            "FS_caracteristico": FS_desl_car, "ok": bool(H_d <= R_d)}

    # --- HUNDIMIENTO (GEO DA-2*) ---
    # acciones de calculo (permanente y variable desfavorables)
    N_d = G_SUP * (W_G + Ev_G) + Q_SUP * (W_Q + Ev_Q)
    M_estab_d = G_SUP * (Mw_G + Ev_G * xEv) + Q_SUP * (Mw_Q + Ev_Q * xEv)
    M_vuelco_d = G_SUP * Mh_G + Q_SUP * Mh_Q
    x_R = (M_estab_d - M_vuelco_d) / N_d if N_d else B / 2   # posicion de la resultante desde la puntera
    e = B / 2 - x_R
    Bp = B - 2 * abs(e)
    q_Ed = (N_d / Bp) if Bp > 0 else 9.99e3                 # kPa (N_d en kN/m, Bp en m)
    Rd = t["Rd"] / 1e3                                       # kPa (resistencia de calculo)
    out["hundimiento"] = {"N_d_kN": N_d, "e_m": e, "e_lim_B6_m": B / 6, "Bp_m": Bp,
                          "q_Ed_kPa": q_Ed, "Rd_kPa": Rd, "u": q_Ed / Rd if Rd else 9.99,
                          "ok_despegue": bool(abs(e) <= B / 6), "ok": bool(q_Ed <= Rd)}

    # --- EC2: presion bajo la zapata (de calculo, para puntera y talon) ---
    # distribucion lineal con N_d y e (kN/m, kPa)
    p_med = N_d / B
    p_toe = p_med * (1 + 6 * e / B)     # en x=0 (puntera)
    p_heel = p_med * (1 - 6 * e / B)    # en x=B (talon)

    # --- ALZADO (arranque) ---
    M_alz = abs(results["alzado"]["ELU"]["M_base"])
    V_alz = abs(results["alzado"]["ELU"]["V_base"])
    d_alz = t_alz - C_NOM - PHI_BARRA / 2
    fa = flexion(M_alz, d_alz, fck, fctm, t_alz)
    va = cortante(V_alz, d_alz, fck, fa["As_prov_cm2_m"] / 1e4)
    out["alzado"] = {"d_mm": d_alz * 1e3, "flexion": fa, "cortante": va}

    # --- PUNTERA: mensula bajo presion del terreno (arriba) - peso propio losa ---
    d_z = e_z - C_NOM - PHI_BARRA / 2
    # presion del terreno en la puntera (lineal de p_toe a p en la cara del alzado)
    x_face_toe = pun
    p_at_face = p_med * (1 + 6 * e * (B / 2 - x_face_toe) / B ** 2)
    w_self = G_SUP * e_z * gc / 1e3                  # peso propio losa (kN/m2) factorizado
    # momento en la cara del alzado (voladizo de longitud pun)
    # presion neta hacia arriba (trapecio p_toe..p_at_face) menos peso propio
    p1 = p_toe - w_self; p2 = p_at_face - w_self
    M_toe = (p1 * pun ** 2 / 2 + (p2 - p1) * pun ** 2 / 3) * 1e3  # N.m/m (x desde cara)
    # cortante a un canto d de la cara
    xd = max(pun - d_z, 0.0)
    p_d = p_med * (1 + 6 * e * (B / 2 - xd) / B ** 2) - w_self
    V_toe = ((p1 + p_d) / 2 * (pun - xd) + 0) * 1e3 if pun > d_z else (p1 + p2) / 2 * pun * 1e3
    ft = flexion(abs(M_toe), d_z, fck, fctm, e_z)
    vt = cortante(abs(V_toe), d_z, fck, ft["As_prov_cm2_m"] / 1e4)
    out["puntera"] = {"d_mm": d_z * 1e3, "p_borde_kPa": p_toe, "p_cara_kPa": p_at_face,
                      "flexion": ft, "cortante": vt}

    # --- TALON: mensula bajo peso de tierras + sobrecarga (abajo) - reaccion (arriba) ---
    x_face_heel = pun + t_alz
    p_at_face_h = p_med * (1 + 6 * e * (B / 2 - x_face_heel) / B ** 2)
    Hm = m["Hm"]
    w_soil = G_SUP * Hm * t["gamma"] / 1e3          # peso de tierras (kN/m2) factorizado
    w_surch = Q_SUP * model["sobrecarga"] / 1e3     # sobrecarga (kN/m2) factorizada
    w_self_h = G_SUP * e_z * gc / 1e3
    w_down = w_soil + w_surch + w_self_h
    # presion neta hacia abajo = w_down - reaccion (trapecio p_at_face_h .. p_heel)
    pn1 = w_down - p_at_face_h; pn2 = w_down - p_heel
    M_heel = (pn1 * tal ** 2 / 2 + (pn2 - pn1) * tal ** 2 / 3) * 1e3   # N.m/m (x desde cara hacia el talon)
    xd_h = max(tal - d_z, 0.0)
    p_dh = p_med * (1 + 6 * e * (B / 2 - (x_face_heel + xd_h)) / B ** 2)
    pn_d = w_down - p_dh
    V_heel = (pn1 + pn_d) / 2 * (tal - xd_h) * 1e3 if tal > d_z else (pn1 + pn2) / 2 * tal * 1e3
    fh = flexion(abs(M_heel), d_z, fck, fctm, e_z)
    vh = cortante(abs(V_heel), d_z, fck, fh["As_prov_cm2_m"] / 1e4)
    out["talon"] = {"d_mm": d_z * 1e3, "p_cara_kPa": p_at_face_h, "p_borde_kPa": p_heel,
                    "flexion": fh, "cortante": vh}

    # --- VALIDACION (cruzada): empuje integrado vs forma cerrada ---
    Ka = emp["Ka"]; H = emp["H"]
    Ea_cf = (0.5 * Ka * t["gamma"] * H ** 2 + Ka * model["sobrecarga"] * H) / 1e3  # sin agua
    Eh_tot = Eh_G + Eh_Q - (sum(c["Eh_kN"] for c in comps if c["nombre"] == "empuje_agua"))
    out["validacion"] = {"Ea_forma_cerrada_kN": Ea_cf, "Eh_integrado_kN": Eh_tot,
                         "error_pct": abs(Eh_tot - Ea_cf) / Ea_cf * 100 if Ea_cf else 0.0}

    geo_ok = (out["vuelco"]["ok"] and out["deslizamiento"]["ok"]
              and out["hundimiento"]["ok"] and out["hundimiento"]["ok_despegue"])
    est_ok = all([out["alzado"]["flexion"]["ok"], out["alzado"]["cortante"]["ok"],
                  out["puntera"]["cortante"]["ok"], out["talon"]["cortante"]["ok"]])
    out["veredicto"] = "CUMPLE" if (geo_ok and est_ok) else "REVISAR"
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-muro-mensula")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    v = out["vuelco"]; d = out["deslizamiento"]; h = out["hundimiento"]
    print("MURO mensula -> %s" % out["veredicto"])
    print("  VUELCO (EQU): u=%.2f  FS_car=%.2f  %s" % (v["u"], v["FS_caracteristico"], "OK" if v["ok"] else "NO"))
    print("  DESLIZAMIENTO (GEO): H_d=%.0f / R_d=%.0f kN  u=%.2f  FS_car=%.2f  %s"
          % (d["H_d_kN"], d["R_d_kN"], d["u"], d["FS_caracteristico"], "OK" if d["ok"] else "NO"))
    print("  HUNDIMIENTO (GEO): q_Ed=%.0f / Rd=%.0f kPa  e=%.3f (lim %.3f) B'=%.2f  u=%.2f  %s"
          % (h["q_Ed_kPa"], h["Rd_kPa"], h["e_m"], h["e_lim_B6_m"], h["Bp_m"], h["u"], "OK" if h["ok"] else "NO"))
    a = out["alzado"]["flexion"]; av = out["alzado"]["cortante"]
    print("  ALZADO: M=%.0f kNm/m As=%.1f cm2/m  V=%.0f kN/m u_V=%.2f"
          % (a["M_Ed_kNm_m"], a["As_prov_cm2_m"], av["V_Ed_kN_m"], av["u"]))
    pt = out["puntera"]["flexion"]; th = out["talon"]["flexion"]
    print("  PUNTERA: M=%.0f kNm/m As=%.1f cm2/m | TALON: M=%.0f kNm/m As=%.1f cm2/m"
          % (pt["M_Ed_kNm_m"], pt["As_prov_cm2_m"], th["M_Ed_kNm_m"], th["As_prov_cm2_m"]))
    val = out["validacion"]
    print("  VALIDACION empuje: integrado=%.1f vs forma cerrada=%.1f kN  error=%.2f%%"
          % (val["Eh_integrado_kN"], val["Ea_forma_cerrada_kN"], val["error_pct"]))
