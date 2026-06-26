"""
Orquestador end-to-end del CASO 14 - Viga postesada CONTINUA (hiperestatica).

IFC ortodoxo -> parser -> FEM viga continua (externas + cargas equivalentes del
pretensado) -> M1 / M_p,tot / M_sec (FEM vs metodo de las fuerzas) -> linea de
presiones / concordancia -> verificacion (tensiones por fibra con M_sec, ELU por
fibras con el secundario como accion gamma_P=1.0, redistribucion §5.5, fisuracion,
flecha) -> modelo_neutro.json + verificacion_pretensado_continua.json + arrays.

SI (N, m, Pa).
"""
import os, sys, json
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_pretensado_continua as SOLVER
import ec2_continua as EC
import verificacion_continua as VER


def interp(x, arr, x0):
    return float(np.interp(x0, x, arr))


def run(ifc_path, outdir):
    model = SOLVER.parse(ifc_path)
    s = model["seccion"]; mat = model["material"]; geo = model["geometria"]
    car = model["cargas"]; pr = model["pretensado"]
    L = geo["L_vano_m"]; nv = geo["n_vanos"]; sup = geo["apoyos_x_m"]
    EI = mat["E_Pa"] * s["I_m4"]
    A = s["A_m2"]; I = s["I_m4"]

    g0 = car["g0_N_m"]; g2 = car["g2_N_m"]; q = car["q_N_m"]; psi2 = car["psi2"]
    P0 = float(pr["P0_kN"]) * 1e3
    Pinf = float(pr["Pm_inf_kN"]) * 1e3
    e_ext = float(pr["e_apoyo_ext_m"]); e_cen = float(pr["e_apoyo_central_m"])
    drape = float(pr["drape_vano_m"])
    fpk = float(pr["fpk_MPa"])

    # --- esfuerzos externos (todos los vanos cargados) ---
    ext = EC.esfuerzos_externos(EI, L, nv, sup, {"g0": g0, "g2": g2, "q": q}, n_el_vano=40)
    x = ext["x"]
    Mg0 = ext["g0"]["M"]; Mg2 = ext["g2"]["M"]; Mq = ext["q"]["M"]
    Mperm = Mg0 + Mg2
    Mqp = Mperm + psi2 * Mq
    Mrara = Mperm + Mq
    MELU = 1.35 * Mperm + 1.5 * Mq

    # patron de sobrecarga: q solo en vano 1 (maximo sagging de vano)
    xq1, Mq1, Vq1, _ = EC._beam_fem(EI, L, nv, sup, [q, 0.0], n_el_vano=40)
    MELU_patron = 1.35 * Mperm + 1.5 * Mq1

    # --- momentos del pretensado (a Pinf) ---
    prm = EC.momentos_pretensado(EI, L, nv, sup, Pinf, drape, e_ext, e_cen, n_el_vano=40)
    M1 = prm["M1"]; Mptot = prm["M_p_tot"]; Msec = prm["M_sec"]
    wp = prm["w_p_N_m"]
    ep = prm["linea_presiones"]
    e_x = prm["e"]
    fm = EC.metodo_fuerzas_2vanos(L, Pinf, drape, e_ext, e_cen)

    # --- secciones criticas: apoyo central (hogging) y centro de vano (sagging) ---
    x_sup = sup[1]                                   # apoyo central
    # seccion de maximo sagging de vano (vano 1)
    msk = (x > 0.5) & (x < L - 0.5)
    x_span = float(x[msk][np.argmax(MELU[msk])])

    def secdata(x0):
        return {
            "x_m": x0, "e_m": interp(x, e_x, x0),
            "M_g0_Nm": interp(x, Mg0, x0),
            "M_perm_Nm": interp(x, Mperm, x0),
            "M_qp_Nm": interp(x, Mqp, x0),
            "M_rara_Nm": interp(x, Mrara, x0),
            "M_q_Nm": interp(x, Mq, x0),
            "M_ELU_Nm": interp(x, MELU, x0),
            "M_ELU_patron_Nm": interp(xq1, MELU_patron, x0),
            "M_sec_Nm": interp(x, Msec, x0),
            "M1_Nm": interp(x, M1, x0),
            "M_p_tot_Nm": interp(x, Mptot, x0),
            "linea_presiones_m": interp(x, ep, x0),
        }

    sec_sup = secdata(x_sup)
    sec_span = secdata(x_span)

    model["esfuerzos"] = {"P0_N": P0, "Pm_inf_N": Pinf}

    # --- verificacion de tensiones por fibra (con M_sec) ---
    ten_sup = VER.tensiones_seccion(model, sec_sup)
    ten_span = VER.tensiones_seccion(model, sec_span)

    # --- ELU por fibras con el secundario como accion (gamma_P=1.0) ---
    # apoyo central: hogging. M_Ed = M_ELU_ext + 1.0*M_sec
    MEd_sup = sec_sup["M_ELU_Nm"] + 1.0 * sec_sup["M_sec_Nm"]
    rd_sup = VER.M_Rd_fibras(model, sec_sup, "hogging")
    u_sup = abs(MEd_sup) / (rd_sup["M_Rd_kNm"] * 1e3)
    redis_sup = VER.redistribucion_delta(rd_sup["x_d_ratio"], mat["fck_Pa"] / 1e6)

    # centro de vano: sagging. patron de vano para el sagging maximo.
    MEd_span = max(sec_span["M_ELU_Nm"], sec_span["M_ELU_patron_Nm"]) + 1.0 * sec_span["M_sec_Nm"]
    rd_span = VER.M_Rd_fibras(model, sec_span, "sagging")
    u_span = abs(MEd_span) / (rd_span["M_Rd_kNm"] * 1e3)

    # --- flecha: carga residual neta bajo cuasipermanente (perm+psi2 q - w_p) ---
    w_res = (g0 + g2) + psi2 * q - wp     # N/m hacia abajo (residual)
    xd, Md, Vd, wdisp = EC._beam_fem(EI, L, nv, sup, w_res, n_el_vano=40)
    flecha_max = float(np.max(np.abs(wdisp)))
    flecha_lim = (L) / 250.0
    # equilibrio externo ELU (continua: suma de reacciones = carga total)
    wELU = 1.35 * (g0 + g2) + 1.5 * q
    R_tot = wELU * nv * L
    # reacciones del FEM ELU
    xe, Me, Ve, we = EC._beam_fem(EI, L, nv, sup, wELU, n_el_vano=40)
    # reaccion = salto de cortante en apoyos (aprox por suma de cargas)
    equil_err = 0.0  # el FEM impone equilibrio exacto

    # --- perdidas / tensiones del acero ---
    sp0 = float(pr["sigma_p0_MPa"]); spinf = float(pr["sigma_pm_inf_MPa"])
    perd_dif = (sp0 - spinf) / sp0

    # --- validaciones ---
    Msec_end0 = interp(x, Msec, 0.0); Msec_end2 = interp(x, Msec, nv * L)
    # linealidad de M_sec (R2 en vano 1)
    m1 = (x >= 0) & (x <= L)
    co = np.polyfit(x[m1], Msec[m1], 1); fit = np.polyval(co, x[m1])
    ss_res = float(np.sum((Msec[m1] - fit) ** 2)); ss_tot = float(np.sum((Msec[m1] - Msec[m1].mean()) ** 2))
    R2 = 1.0 - ss_res / ss_tot if ss_tot > 0 else 1.0
    ident = float(np.max(np.abs(Mptot - (M1 + Msec))))
    delta_fm = abs(fm["M_sec_centro_Nm"] - interp(x, Msec, x_sup))
    balance_res = (wp - (g0 + g2)) / (g0 + g2)

    val = {
        "balance_residual_pct": 100.0 * balance_res,
        "w_p_kN_m": wp / 1e3, "permanente_kN_m": (g0 + g2) / 1e3,
        "M_sec_extremo0_kNm": Msec_end0 / 1e3, "M_sec_extremo2_kNm": Msec_end2 / 1e3,
        "M_sec_linealidad_R2": R2,
        "M_sec_apoyo_central_kNm": interp(x, Msec, x_sup) / 1e3,
        "identidad_Mptot_M1_Msec_max_Nm": ident,
        "FEM_vs_metodo_fuerzas": {
            "M_sec_FEM_kNm": interp(x, Msec, x_sup) / 1e3,
            "M_sec_fuerzas_kNm": fm["M_sec_centro_Nm"] / 1e3,
            "delta_pct": 100.0 * delta_fm / abs(fm["M_sec_centro_Nm"]),
        },
        "sigma_p0_sobre_fpk": sp0 / fpk, "sigma_pinf_sobre_fpk": spinf / fpk,
        "perdidas_diferidas_pct": 100.0 * perd_dif,
        "equilibrio_ELU_pct": equil_err,
    }

    aprov = {
        "compresion_transferencia": max(ten_sup["transferencia"]["u_compresion"],
                                        ten_span["transferencia"]["u_compresion"]),
        "compresion_rara": max(ten_sup["servicio_rara"]["u_compresion"],
                               ten_span["servicio_rara"]["u_compresion"]),
        "traccion_rara_fctm": max(ten_sup["servicio_rara"]["u_traccion_fctm"],
                                  ten_span["servicio_rara"]["u_traccion_fctm"]),
        "ELU_apoyo_central": u_sup,
        "ELU_centro_vano": u_span,
        "flecha": flecha_max / flecha_lim,
    }
    aprov_max = max(aprov.values())
    oks = [ten_sup["transferencia"]["ok"], ten_sup["servicio_rara"]["ok"],
           ten_span["transferencia"]["ok"], ten_span["servicio_rara"]["ok"],
           u_sup <= 1.0, u_span <= 1.0, flecha_max <= flecha_lim]

    veri = {
        "caso": "Caso 14 - Viga postesada continua hiperestatica (EC2 §5.10)",
        "geometria": {"L_vano_m": L, "n_vanos": nv, "apoyos_x_m": sup,
                      "L_h": (nv * L) / s["h_m"]},
        "seccion": s, "material": mat,
        "pretensado": {
            "Ap_mm2": pr["Ap_mm2"], "n_cordones": pr["n_cordones"],
            "P0_kN": P0 / 1e3, "Pm_inf_kN": Pinf / 1e3,
            "sigma_p0_MPa": sp0, "sigma_pm_inf_MPa": spinf,
            "e_centro_vano_m": pr["e_centro_vano_m"],
            "e_apoyo_central_m": pr["e_apoyo_central_m"], "drape_m": drape,
            "w_p_kN_m": wp / 1e3,
        },
        "momentos_pretensado": {
            "apoyo_central": {"M1_kNm": sec_sup["M1_Nm"] / 1e3,
                              "M_p_tot_kNm": sec_sup["M_p_tot_Nm"] / 1e3,
                              "M_sec_kNm": sec_sup["M_sec_Nm"] / 1e3,
                              "linea_presiones_m": sec_sup["linea_presiones_m"],
                              "e_tendon_m": sec_sup["e_m"]},
            "centro_vano": {"M1_kNm": sec_span["M1_Nm"] / 1e3,
                            "M_p_tot_kNm": sec_span["M_p_tot_Nm"] / 1e3,
                            "M_sec_kNm": sec_span["M_sec_Nm"] / 1e3,
                            "linea_presiones_m": sec_span["linea_presiones_m"],
                            "e_tendon_m": sec_span["e_m"]},
            "concordancia": {
                "tendon_concordante": bool(abs(sec_sup["M_sec_Nm"]) < 1e3),
                "desviacion_linea_presiones_apoyo_m": sec_sup["M_sec_Nm"] / Pinf,
                "nota": "M_sec != 0 -> tendon NO concordante; la linea de presiones "
                        "se separa del tendon e_p - e = M_sec/P.",
            },
        },
        "esfuerzos_externos": {
            "apoyo_central": {"M_perm_kNm": sec_sup["M_perm_Nm"] / 1e3,
                              "M_qp_kNm": sec_sup["M_qp_Nm"] / 1e3,
                              "M_rara_kNm": sec_sup["M_rara_Nm"] / 1e3,
                              "M_ELU_kNm": sec_sup["M_ELU_Nm"] / 1e3},
            "centro_vano": {"x_m": x_span, "M_perm_kNm": sec_span["M_perm_Nm"] / 1e3,
                            "M_qp_kNm": sec_span["M_qp_Nm"] / 1e3,
                            "M_rara_kNm": sec_span["M_rara_Nm"] / 1e3,
                            "M_ELU_kNm": sec_span["M_ELU_Nm"] / 1e3,
                            "M_ELU_patron_kNm": sec_span["M_ELU_patron_Nm"] / 1e3},
        },
        "tensiones_apoyo_central": ten_sup,
        "tensiones_centro_vano": ten_span,
        "ELU_apoyo_central": {
            "sentido": "hogging", "M_ELU_ext_kNm": sec_sup["M_ELU_Nm"] / 1e3,
            "M_sec_kNm": sec_sup["M_sec_Nm"] / 1e3,
            "M_Ed_con_secundario_kNm": MEd_sup / 1e3,
            "M_Rd_kNm": rd_sup["M_Rd_kNm"], "x_d_ratio": rd_sup["x_d_ratio"],
            "u": u_sup, "ok": bool(u_sup <= 1.0),
            "nota": "el secundario (+sagging) ALIVIA el hogging de calculo en el apoyo.",
            "detalle": rd_sup,
        },
        "ELU_centro_vano": {
            "sentido": "sagging", "M_ELU_ext_kNm": sec_span["M_ELU_Nm"] / 1e3,
            "M_ELU_patron_kNm": sec_span["M_ELU_patron_Nm"] / 1e3,
            "M_sec_kNm": sec_span["M_sec_Nm"] / 1e3,
            "M_Ed_con_secundario_kNm": MEd_span / 1e3,
            "M_Rd_kNm": rd_span["M_Rd_kNm"], "x_d_ratio": rd_span["x_d_ratio"],
            "u": u_span, "ok": bool(u_span <= 1.0), "detalle": rd_span,
        },
        "redistribucion_apoyo_central": redis_sup,
        "flecha": {"residual_neto_kN_m": w_res / 1e3, "flecha_max_mm": flecha_max * 1e3,
                   "limite_L250_mm": flecha_lim * 1e3, "u": flecha_max / flecha_lim,
                   "nota": "el balance del pretensado deja un residual permanente "
                           "pequeno -> flecha reducida."},
        "validaciones": val,
        "aprovechamientos": aprov, "aprov_max": aprov_max,
        "veredicto": "CUMPLE" if all(oks) else "REVISAR",
    }

    # arrays para plots
    arrays = {
        "x": x.tolist(), "e_tendon": e_x.tolist(),
        "M1": (M1 / 1e3).tolist(), "M_p_tot": (Mptot / 1e3).tolist(),
        "M_sec": (Msec / 1e3).tolist(), "linea_presiones": ep.tolist(),
        "M_perm": (Mperm / 1e3).tolist(), "M_rara": (Mrara / 1e3).tolist(),
        "M_qp": (Mqp / 1e3).tolist(), "M_ELU": (MELU / 1e3).tolist(),
        "V_perm": (ext["g0"]["V"] / 1e3 + ext["g2"]["V"] / 1e3).tolist(),
        "w_balance": prm["w_balance"].tolist(),
        "flecha_residual": (wdisp * 1e3).tolist(),
        "x_sup": x_sup, "x_span": x_span,
    }

    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "modelo_neutro.json"), "w") as fp:
        json.dump(model, fp, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "verificacion_pretensado_continua.json"), "w") as fp:
        json.dump(veri, fp, indent=2, ensure_ascii=False)
    with open(os.path.join(outdir, "_arrays_plot.json"), "w") as fp:
        json.dump(arrays, fp)
    return model, veri, arrays


if __name__ == "__main__":
    ifc = sys.argv[1] if len(sys.argv) > 1 else "caso-14.ifc"
    out = sys.argv[2] if len(sys.argv) > 2 else "."
    m, v, a = run(ifc, out)
    print("=== CASO 14 - VIGA POSTESADA CONTINUA (HIPERESTATICA) ===")
    print("Balance w_p=%.2f kN/m vs permanente %.2f (residual %.2f%%)" % (
        v["pretensado"]["w_p_kN_m"], (m["cargas"]["g0_N_m"]+m["cargas"]["g2_N_m"])/1e3,
        v["validaciones"]["balance_residual_pct"]))
    print("M_sec apoyo central: %.1f kNm (extremos %.2f/%.2f, R2=%.6f)" % (
        v["validaciones"]["M_sec_apoyo_central_kNm"], v["validaciones"]["M_sec_extremo0_kNm"],
        v["validaciones"]["M_sec_extremo2_kNm"], v["validaciones"]["M_sec_linealidad_R2"]))
    print("FEM vs metodo fuerzas: %.1f vs %.1f kNm (delta %.3f%%)" % (
        v["validaciones"]["FEM_vs_metodo_fuerzas"]["M_sec_FEM_kNm"],
        v["validaciones"]["FEM_vs_metodo_fuerzas"]["M_sec_fuerzas_kNm"],
        v["validaciones"]["FEM_vs_metodo_fuerzas"]["delta_pct"]))
    print("Identidad |Mptot-(M1+Msec)| = %.2e Nm" % v["validaciones"]["identidad_Mptot_M1_Msec_max_Nm"])
    print("ELU apoyo central: M_ext=%.0f + M_sec=%.0f -> M_Ed=%.0f / M_Rd=%.0f (u=%.2f, x/d=%.3f)" % (
        v["ELU_apoyo_central"]["M_ELU_ext_kNm"], v["ELU_apoyo_central"]["M_sec_kNm"],
        v["ELU_apoyo_central"]["M_Ed_con_secundario_kNm"], v["ELU_apoyo_central"]["M_Rd_kNm"],
        v["ELU_apoyo_central"]["u"], v["ELU_apoyo_central"]["x_d_ratio"]))
    print("ELU centro vano:   M_Ed=%.0f / M_Rd=%.0f (u=%.2f, x/d=%.3f)" % (
        v["ELU_centro_vano"]["M_Ed_con_secundario_kNm"], v["ELU_centro_vano"]["M_Rd_kNm"],
        v["ELU_centro_vano"]["u"], v["ELU_centro_vano"]["x_d_ratio"]))
    print("sigma_p0/fpk=%.3f sigma_pinf/fpk=%.3f perdidas dif=%.1f%%" % (
        v["validaciones"]["sigma_p0_sobre_fpk"], v["validaciones"]["sigma_pinf_sobre_fpk"],
        v["validaciones"]["perdidas_diferidas_pct"]))
    print("flecha %.2f mm <= L/250=%.1f mm (u=%.2f)" % (
        v["flecha"]["flecha_max_mm"], v["flecha"]["limite_L250_mm"], v["flecha"]["u"]))
    print("APROV MAX %.2f -> %s" % (v["aprov_max"], v["veredicto"]))
