"""
Orquestador end-to-end del Caso 12 - Viga postesada isostatica (EC2 §5.10).

  IFC -> modelo neutro -> pretensado (cargas equivalentes + fuerza/excentricidad)
  -> perdidas instantaneas y diferidas -> momentos y combinaciones ->
  verificacion (tensiones transferencia/servicio, ELU fibras, fisuracion,
  cortante) -> JSON + diagramas.

Uso:
  python3 pretensado/run_all_pretensado.py <carpeta_proyecto> <ruta caso-12.ifc>

La memoria Word se genera aparte:
  python3 pretensado/generate_memoria_pretensado.py <carpeta_proyecto>
"""
import sys
import os
import json
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import solver_pretensado
import ec2_pretensado as ec2
import verificacion_pretensado as verif

try:
    import plots_pretensado
except Exception:
    plots_pretensado = None


def run(proj, ifc):
    print("[1/6] IFC -> modelo neutro:", ifc)
    model = solver_pretensado.parse(ifc)
    os.makedirs(proj, exist_ok=True)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w",
                          encoding="utf-8"), indent=2, ensure_ascii=False)

    s = model["seccion"]; mat = model["material"]; pr = model["pretensado"]
    c = model["cargas"]
    L = model["geometria"]["L_m"]
    A = s["A_m2"]; I = s["I_m4"]; c_sup = s["c_sup_m"]; c_inf = s["c_inf_m"]
    e = float(pr["e_centro_m"]); e_apoyo = float(pr["e_apoyo_m"])
    Ap = float(pr["Ap_mm2"]) * 1e-6
    fpk = float(pr["fpk_MPa"]) * 1e6
    Ep = float(pr["Ep_GPa"]) * 1e9
    Ecm = mat["E_Pa"]
    g0 = c["g0_N_m"]; g2 = c["g2_N_m"]; q = c["q_N_m"]; psi2 = c["psi2"]

    # ----- pretensado: fuerzas -----
    P0 = float(pr["P0_kN"]) * 1e3
    Pinf = float(pr["Pm_inf_kN"]) * 1e3
    sigma_p0 = P0 / Ap
    sigma_pinf = Pinf / Ap
    print("      P0=%.0f kN (sigma_p0=%.0f MPa=%.3f fpk)  Pm,inf=%.0f kN (sigma_pinf=%.0f MPa=%.3f fpk)" % (
        P0 / 1e3, sigma_p0 / 1e6, sigma_p0 / fpk, Pinf / 1e3, sigma_pinf / 1e6, sigma_pinf / fpk))

    # ----- perdidas instantaneas a lo largo del tendon (rozamiento) -----
    print("[2/6] Perdidas instantaneas (rozamiento + cuna + acortamiento)...")
    mu = float(pr["mu_rozamiento"]); k = float(pr["k_desviacion"])
    # tension de tesado en el gato (sigma_pmax ~ 0.80 fpk antes de perdidas inst.)
    sigma_pmax = 0.80 * fpk
    xs = [L * i / 20.0 for i in range(21)]
    perfil_roz = []
    for x in xs:
        # tesado por dos extremos -> tomar el extremo mas cercano
        xx = min(x, L - x)
        theta = ec2.angulo_acumulado(xx, L, e, e_apoyo)
        dloss, sig = ec2.perdida_rozamiento(sigma_pmax, xx, theta, mu, k)
        perfil_roz.append({"x_m": x, "sigma_MPa": sig / 1e6,
                           "perdida_MPa": dloss / 1e6})
    # penetracion de cuna
    slip = float(pr["penetracion_cuna_mm"]) * 1e-3
    pc = ec2.perdida_penetracion_cuna(sigma_pmax, slip, Ep, mu, k, L, e)
    dsig_anc, dsig_cuna_media, x_set = pc
    # acortamiento elastico (a partir de la compresion bajo P0+g0 en el tendon)
    M_g0 = ec2.momento_isostatico(g0, L)
    sig_c_tendon0 = (-P0 / A - (M_g0 - P0 * e) * (-e) / I)   # compresion a cota tendon
    dsig_ac = ec2.perdida_acortamiento_elastico(sig_c_tendon0, Ep, Ecm,
                                                int(pr["n_tendones"]))
    perd_inst = {
        "sigma_pmax_MPa": sigma_pmax / 1e6,
        "rozamiento_centro_MPa": next(p["perdida_MPa"] for p in perfil_roz
                                      if abs(p["x_m"] - L / 2.0) < 1e-6),
        "cuna_anclaje_MPa": dsig_anc / 1e6,
        "cuna_media_MPa": dsig_cuna_media / 1e6,
        "cuna_x_set_m": x_set,
        "acortamiento_elastico_MPa": dsig_ac / 1e6,
        "perfil_rozamiento": perfil_roz,
    }
    print("      rozamiento(centro)=%.0f MPa  cuna(media)=%.0f MPa (x_set=%.1f m)  acort.elast=%.0f MPa" % (
        perd_inst["rozamiento_centro_MPa"], dsig_cuna_media / 1e6, x_set, dsig_ac / 1e6))

    # ----- perdidas diferidas -----
    print("[3/6] Perdidas diferidas (retraccion + fluencia + relajacion)...")
    eps_cs = 30e-5            # retraccion total tipica C40/50 [confirmar AN]
    phi = 2.0                 # coef. de fluencia tipico (carga a edad temprana)
    rho1000 = float(pr["rho1000_pct"]) / 100.0
    clase = int(pr["relajacion_clase"])
    dsig_pr = ec2.relajacion(sigma_p0, fpk, rho1000 * 100.0, clase)
    zcp = e                   # distancia c.d.g.-tendon en centro de vano
    M_qp = ec2.momento_isostatico(g0 + g2 + psi2 * q, L)
    sig_c_qp = -Pinf / A - (M_qp - Pinf * e) * (-e) / I
    dsig_dif = ec2.perdidas_diferidas(eps_cs, Ep, dsig_pr, phi, sig_c_qp,
                                      Ecm, Ap, A, I, zcp)
    perd_dif = {
        "eps_cs": eps_cs, "phi_fluencia": phi,
        "relajacion_MPa": dsig_pr / 1e6,
        "diferida_total_MPa": dsig_dif / 1e6,
        "modelo": "EC2 ec. 5.46 (combinada) + relajacion ec. 3.29",
    }
    # comprobacion de consistencia: Pinf ~ P0 - dsig_dif*Ap
    Pinf_check = P0 - dsig_dif * Ap
    perd_dif["Pinf_recalculada_kN"] = Pinf_check / 1e3
    perd_dif["coherencia_pct"] = abs(Pinf_check - Pinf) / Pinf * 100.0
    print("      relajacion=%.0f MPa  diferida_total=%.0f MPa  Pinf_recalc=%.0f kN (coh. %.1f%%)" % (
        dsig_pr / 1e6, dsig_dif / 1e6, Pinf_check / 1e3, perd_dif["coherencia_pct"]))

    # ----- pretensado como cargas equivalentes (load balancing) -----
    print("[4/6] Cargas equivalentes (load balancing) vs fuerza+excentricidad...")
    ceq = ec2.cargas_equivalentes(Pinf, L, e, e_apoyo)
    w_p = ceq["w_p_N_m"]
    w_perm = g0 + g2
    residual = (w_perm - w_p)               # carga no equilibrada (N/m)
    residual_pct = abs(residual) / w_perm * 100.0
    P_balance_perm = ec2.P_balance(w_perm, L, e, e_apoyo)
    balance = {
        "w_p_kN_m": w_p / 1e3, "w_permanente_kN_m": w_perm / 1e3,
        "residual_kN_m": residual / 1e3, "residual_pct": residual_pct,
        "P_para_equilibrar_perm_kN": P_balance_perm / 1e3,
        "N_axil_kN": ceq["N_axil_N"] / 1e3,
    }
    print("      w_p=%.2f kN/m  w_perm=%.2f kN/m  residual=%.3f%%  P_balance=%.0f kN" % (
        w_p / 1e3, w_perm / 1e3, residual_pct, P_balance_perm / 1e3))

    # ----- momentos -----
    M_g0v = ec2.momento_isostatico(g0, L)
    M_g2v = ec2.momento_isostatico(g2, L)
    M_qv = ec2.momento_isostatico(q, L)
    comb = ec2.combinaciones_momentos(M_g0v / 1e3, M_g2v / 1e3, M_qv / 1e3, psi2)
    M_rara = comb["M_caracteristica_rara"] * 1e3
    M_qpv = comb["M_cuasipermanente"] * 1e3
    M_ELU = comb["M_ELU"] * 1e3
    V_ELU = (1.35 * (g0 + g2) + 1.5 * q) * L / 2.0
    print("      M_g0=%.0f M_perm=%.0f M_q=%.0f M_qp=%.0f M_rara=%.0f M_ELU=%.0f kN*m" % (
        comb["M_g0"], comb["M_perm"], comb["M_q"], comb["M_cuasipermanente"],
        comb["M_caracteristica_rara"], comb["M_ELU"]))

    # ----- validacion cruzada: cargas equivalentes vs fuerza+excentricidad -----
    # estado tensional bajo cuasipermanente por los DOS metodos en centro de vano:
    # (a) fuerza+excentricidad
    sa_sup, sa_inf = verif._fib_stresses(Pinf, e, M_qpv, A, I, c_sup, c_inf)
    # (b) cargas equivalentes: la carga neta es w_qp - w_p (flexion) + axil -Pinf/A
    w_qp = g0 + g2 + psi2 * q
    M_net = ec2.momento_isostatico(w_qp - w_p, L)   # momento de la carga no equilibrada
    sb_sup = -Pinf / A - M_net * c_sup / I
    sb_inf = -Pinf / A + M_net * c_inf / I
    cross = {
        "metodo_fuerza_excentricidad": {"sup_MPa": sa_sup / 1e6, "inf_MPa": sa_inf / 1e6},
        "metodo_cargas_equivalentes": {"sup_MPa": sb_sup / 1e6, "inf_MPa": sb_inf / 1e6},
        "dif_sup_MPa": abs(sa_sup - sb_sup) / 1e6,
        "dif_inf_MPa": abs(sa_inf - sb_inf) / 1e6,
        "coincide": bool(abs(sa_sup - sb_sup) < 1e3 and abs(sa_inf - sb_inf) < 1e3),
    }
    print("      cross-check (qp): F+e sup=%.2f inf=%.2f | w_eq sup=%.2f inf=%.2f -> %s" % (
        sa_sup / 1e6, sa_inf / 1e6, sb_sup / 1e6, sb_inf / 1e6,
        "COINCIDE" if cross["coincide"] else "DIFIERE"))

    # ----- verificacion -----
    print("[5/6] Verificacion (tensiones / ELU fibras / fisuracion / cortante)...")
    esf = {
        "P0_N": P0, "Pm_inf_N": Pinf,
        "M_g0_Nm": M_g0v, "M_cuasiperm_Nm": M_qpv, "M_rara_Nm": M_rara,
        "M_ELU_Nm": M_ELU, "V_ELU_N": V_ELU,
    }
    ver = verif.verificar(model, esf, As_pasiva_m2=0.0)
    ap = ver["aprovechamientos"]
    print("      transf u=%.2f | qp u=%.2f | rara_tracc u=%.2f | ELU u=%.2f -> %s" % (
        ap["compresion_transferencia"], ap["compresion_cuasiperm"],
        ap["traccion_rara_fctm"], ap["ELU_flexion"], ver["veredicto"]))

    crit = {
        "Pm_inf_kN": Pinf / 1e3, "Pm_inf_ok": abs(Pinf / 1e3 - 2125.0) < 50.0,
        "sigma_pinf_frac_fpk": sigma_pinf / fpk,
        "sigma_pinf_ok": abs(sigma_pinf / fpk - 0.59) < 0.02,
        "P0_kN": P0 / 1e3, "P0_ok": abs(P0 / 1e3 - 2535.0) < 60.0,
        "sigma_p0_frac_fpk": sigma_p0 / fpk,
        "perdidas_totales_pct": (sigma_pmax - sigma_pinf) / sigma_pmax * 100.0,
        "w_p_kN_m": w_p / 1e3, "residual_balance_pct": residual_pct,
        "residual_ok": residual_pct < 1.0,
        "M_ELU_kNm": M_ELU / 1e3, "M_ELU_ok": abs(M_ELU / 1e3 - 2334.0) < 50.0,
        "M_Rd_kNm": ver["ELU_flexion"]["M_Rd_kNm"],
        "ELU_ok": ver["ELU_flexion"]["ok"],
        "cross_check_coincide": cross["coincide"],
        "aprov_max": ver["aprov_max"], "aprov_ok": ver["aprov_max"] <= 1.0,
    }

    res = {
        "caso": "12-viga-postesada",
        "modelo_resumen": {
            "b_m": s["b_m"], "h_m": s["h_m"], "L_m": L,
            "A_m2": A, "I_m4": I, "W_sup_m3": s["W_sup_m3"], "W_inf_m3": s["W_inf_m3"],
            "material": mat["nombre"], "fck_MPa": mat["fck_Pa"] / 1e6,
            "fck_t_MPa": mat["fck_t_Pa"] / 1e6, "fctm_MPa": mat["fctm_Pa"] / 1e6,
            "g0_kN_m": g0 / 1e3, "g2_kN_m": g2 / 1e3, "q_kN_m": q / 1e3,
        },
        "pretensado": {
            "Ap_mm2": Ap * 1e6, "fpk_MPa": fpk / 1e6, "Ep_GPa": Ep / 1e9,
            "e_centro_m": e, "e_apoyo_m": e_apoyo, "trazado": pr["trazado"],
            "P0_kN": P0 / 1e3, "sigma_p0_MPa": sigma_p0 / 1e6,
            "sigma_p0_frac_fpk": sigma_p0 / fpk,
            "Pm_inf_kN": Pinf / 1e3, "sigma_pinf_MPa": sigma_pinf / 1e6,
            "sigma_pinf_frac_fpk": sigma_pinf / fpk,
        },
        "perdidas_instantaneas": perd_inst,
        "perdidas_diferidas": perd_dif,
        "load_balancing": balance,
        "momentos_kNm": comb,
        "esfuerzos_diseno": {
            "M_g0_kNm": M_g0v / 1e3, "M_cuasiperm_kNm": M_qpv / 1e3,
            "M_rara_kNm": M_rara / 1e3, "M_ELU_kNm": M_ELU / 1e3,
            "V_ELU_kN": V_ELU / 1e3,
        },
        "validacion_cruzada": cross,
        "verificacion": ver,
        "criterios_aceptacion": crit,
        "avisos": [
            "Resultado de PREDIMENSIONADO. Debe ser revisado y FIRMADO por "
            "tecnico competente.",
            "[confirmar AN] EC2 §5.10: coeficientes de rozamiento mu/k, "
            "penetracion de cuna, limites de tension del acero activo, "
            "retraccion y fluencia (Anejo Nacional Espana).",
            "Picos locales en apoyos tratados como envolvente; valor de diseno "
            "en seccion critica (centro de vano).",
        ],
    }
    json.dump(res, open(os.path.join(proj, "verificacion_pretensado.json"), "w",
                        encoding="utf-8"), indent=2, ensure_ascii=False)

    print("[6/6] Diagramas...")
    if plots_pretensado is not None:
        try:
            archivos = plots_pretensado.generar(model, res, proj)
            for a in archivos:
                print("      ", a)
        except Exception as ex:
            print("      AVISO: no se pudieron generar diagramas (%s)" % ex)
    print("OK. Memoria: python3 pretensado/generate_memoria_pretensado.py", proj)
    return res


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-viga-postesada"
    ifc = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "caso-12.ifc")
    run(proj, ifc)
