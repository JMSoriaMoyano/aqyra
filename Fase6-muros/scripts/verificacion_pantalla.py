"""
Verificacion de la PANTALLA ANCLADA.

  - EMPOTRAMIENTO (EC7): FoS del empuje pasivo por el metodo de apoyo libre
    (free-earth support): M_pasivo / M_activo respecto al ancla. Tambien la
    utilizacion del pasivo movilizado (modelo de muelles) vs el disponible.
  - ANCLA: fuerza de calculo por fila y separacion; longitud de bulbo a partir del
    rozamiento lechada-terreno y longitud libre minima (mas alla de la cuna activa).
  - FUSTE (EC2): flexion + cortante del momento maximo del fuste.

Enfoque DA-2* (NDP [confirmar AN Espana]).
SI (N, m, Pa).
"""
import sys
import os
import json
import math
from solver_pantalla import _coef, _sigv
from verificacion_muro import flexion, cortante, GR_E

# Coeficientes [confirmar AN]
G_SUP, Q_SUP = 1.35, 1.50
FS_PASIVO_OBJ = 1.5     # FoS objetivo del empotramiento (apoyo libre) [criterio/AN]
C_NOM = 0.060           # recubrimiento de pantalla en contacto con terreno (m)
PHI_BARRA = 0.025


def _activo_integral(t, model, has_w, zw, gw, z_ref):
    """Empuje activo y su momento respecto a z_ref (caracteristico), separando
    G (suelo+agua) y Q (sobrecarga). Devuelve E, M, E_G, M_G, E_Q, M_Q."""
    Ka, _ = _coef(t); L = model["pantalla"]["L"]; q = model["sobrecarga"]
    n = 400; dz = L / n
    E_G = M_G = E_Q = M_Q = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        pG = Ka * _sigv(t, z, has_w, zw, gw) + (gw * max(z - zw, 0) if has_w else 0)
        pQ = Ka * q
        arm = z - z_ref
        E_G += pG * dz; M_G += pG * dz * arm
        E_Q += pQ * dz; M_Q += pQ * dz * arm
    return E_G + E_Q, M_G + M_Q, E_G, M_G, E_Q, M_Q


def verificar(model, results):
    info = results["info"]
    p = model["pantalla"]; t = model["terreno"]; anc = model["ancla"]
    mp = model["materiales"][p["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]
    L = p["L"]; h = p["h"]; d = p["d"]; tp = p["t"]
    Ka, Kp = _coef(t)
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    z_a = info["z_ancla"]

    out = {"info": info, "equilibrio": results["equilibrio"]}

    # --- EMPOTRAMIENTO: apoyo libre (free-earth) respecto al ancla ---
    Ea, Ma, E_G, M_G, E_Q, M_Q = _activo_integral(t, model, has_w, zw, gw, z_a)  # activo (driving)
    Pp = 0.5 * Kp * t["gamma_pas"] * d ** 2                            # pasivo disponible (caract.)
    z_p = h + 2 * d / 3                                                # punto de aplicacion del pasivo
    Mp = Pp * (z_p - z_a)
    FoS = Mp / Ma if Ma > 0 else 9.99
    # pasivo movilizado por el modelo de muelles (ELU) vs disponible de calculo
    Pp_mob_elu = results["ELU"]["Pp_mov_kN"] * 1e3
    Pp_d = Pp / GR_E
    out["empotramiento"] = {
        "Ea_caract_kN": Ea / 1e3, "Pp_disp_caract_kN": Pp / 1e3, "Pp_disp_calc_kN": Pp_d / 1e3,
        "FoS_pasivo": FoS, "FoS_objetivo": FS_PASIVO_OBJ,
        "Pp_movilizado_ELU_kN": Pp_mob_elu / 1e3,
        "u_pasivo_informativo": Pp_mob_elu / Pp_d if Pp_d else 9.99,
        "ok": bool(FoS >= FS_PASIVO_OBJ)}

    # --- ANCLA ---
    # (a) reaccion del modelo FE (viga sobre muelles), ELU
    T_h_fe = results["ELU"]["T_h_kN"] * 1e3
    # (b) metodo de apoyo libre (free-earth) de calculo: acciones mayoradas,
    #     pasivo movilizado por equilibrio de momentos respecto al ancla
    Ma_d = G_SUP * M_G + Q_SUP * M_Q
    Ea_d = G_SUP * E_G + Q_SUP * E_Q
    Pp_mob_req_d = Ma_d / (z_p - z_a)               # pasivo necesario (de calculo)
    T_h_fe_libre = Ea_d - Pp_mob_req_d              # reaccion horizontal del ancla (free-earth)
    # diseno del ancla con la ENVOLVENTE (conservador)
    T_h = max(T_h_fe, T_h_fe_libre)
    metodo_dim = "free-earth" if T_h_fe_libre >= T_h_fe else "muelles (FE)"
    incl = math.radians(anc["incl"])
    T_anchor_m = T_h / math.cos(incl)               # fuerza a lo largo del ancla, por metro
    F_anchor = T_anchor_m * anc["sep"]              # por ancla (segun separacion)
    # longitud de bulbo: F_anchor * FS / (pi * D * tau)
    L_bulbo = F_anchor * anc["fs_bulbo"] / (math.pi * anc["D_bulbo"] * anc["tau"])
    # longitud libre minima: superar la cuna activa (plano a 45+phi/2 desde el pie)
    ang = math.radians(45 + t["phi"] / 2)
    x_libre = (L - z_a) / math.tan(ang)             # dist. horizontal a la cuna en el nivel del ancla
    L_libre = x_libre / math.cos(incl) + 0.5        # + holgura [criterio]
    out["ancla"] = {
        "T_h_kN_m": T_h / 1e3, "T_h_FE_kN_m": T_h_fe / 1e3, "T_h_freeearth_kN_m": T_h_fe_libre / 1e3,
        "metodo_dimensionante": metodo_dim,
        "T_ancla_kN_m": T_anchor_m / 1e3, "F_ancla_kN": F_anchor / 1e3,
        "separacion_m": anc["sep"], "inclinacion_grados": anc["incl"],
        "L_bulbo_m": L_bulbo, "L_libre_min_m": L_libre, "L_total_min_m": L_bulbo + L_libre,
        "D_bulbo_m": anc["D_bulbo"], "tau_kPa": anc["tau"] / 1e3, "fs_bulbo": anc["fs_bulbo"],
        "ok": True}

    # --- FUSTE (EC2) ---
    M_Ed = abs(results["ELU"]["M_max_kNm"]) * 1e3
    V_Ed = max(abs(pt["V"]) for pt in results["ELU"]["esfuerzos"])
    d_fuste = tp - C_NOM - PHI_BARRA / 2
    fl = flexion(M_Ed, d_fuste, fck, fctm, tp)
    cv = cortante(V_Ed, d_fuste, fck, fl["As_prov_cm2_m"] / 1e4)
    out["fuste"] = {"d_mm": d_fuste * 1e3, "flexion": fl, "cortante": cv}

    geo_ok = out["empotramiento"]["ok"]
    est_ok = out["fuste"]["flexion"]["ok"] and out["fuste"]["cortante"]["ok"]
    out["veredicto"] = "CUMPLE" if (geo_ok and est_ok) else "REVISAR"
    return out


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-pantalla-anclada")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    out = verificar(model, results)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    em = out["empotramiento"]; an = out["ancla"]; fu = out["fuste"]
    ff = fu["flexion"]; fc = fu["cortante"]
    print("PANTALLA anclada -> %s" % out["veredicto"])
    print("  EMPOTRAMIENTO: FoS_pasivo=%.2f (obj %.2f)  pasivo mov(ELU)=%.0f / disp(d)=%.0f kN  %s" % (
        em["FoS_pasivo"], em["FoS_objetivo"], em["Pp_movilizado_ELU_kN"],
        em["Pp_disp_calc_kN"], "OK" if em["ok"] else "NO"))
    print("  ANCLA: T_h=%.0f kN/m [FE=%.0f, free-earth=%.0f -> dim. %s]  F_ancla=%.0f kN" % (
        an["T_h_kN_m"], an["T_h_FE_kN_m"], an["T_h_freeearth_kN_m"],
        an["metodo_dimensionante"], an["F_ancla_kN"]))
    print("         sep=%.1f m incl=%.0f  L_bulbo=%.1f m  L_libre>=%.1f m  L_tot>=%.1f m" % (
        an["separacion_m"], an["inclinacion_grados"], an["L_bulbo_m"],
        an["L_libre_min_m"], an["L_total_min_m"]))
    print("  FUSTE: M_Ed=%.0f kNm/m As=%.1f cm2/m  V_Ed=%.0f kN/m u_V=%.2f  d=%.0f mm" % (
        ff["M_Ed_kNm_m"], ff["As_prov_cm2_m"], fc["V_Ed_kN_m"], fc["u"], fu["d_mm"]))
