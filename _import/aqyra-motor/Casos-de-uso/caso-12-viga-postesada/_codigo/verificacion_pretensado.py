"""
Verificacion de VIGA POSTESADA isostatica (EN 1992-1-1 §5.10/§7, AN Espana).

  - TENSIONES EN TRANSFERENCIA (P0 + g0) por fibras: compresion <= 0.6*fck(t)
    (§5.10.2.2); traccion <= fctm(t).
  - TENSIONES EN SERVICIO por fibras:
      * cuasipermanente (Pm,inf + M_qp): compresion <= 0.45*fck (linealidad de
        fluencia, §7.2(3)); control de descompresion del fondo.
      * caracteristica rara (Pm,inf + M_rara): traccion <= fctm (control de
        fisuracion, clase de exposicion); compresion <= 0.6*fck (§7.2(2)).
  - ELU DE FLEXION por FIBRAS con armadura ACTIVA + PASIVA: bloque de compresion
    del hormigon (parabola-rectangulo simplificado a bloque eta*fcd, lambda*x) +
    traccion del acero activo (fpd) y pasivo (fyd). M_Rd >= M_Ed.
  - FISURACION §7.3 (ancho de fisura estimado / criterio de descompresion).
  - CORTANTE con pretensado: V_Rd,c con sigma_cp (§6.2.2 ec. 6.2a/6.4).

Sigmas: compresion NEGATIVA, traccion POSITIVA. SI (N, m, Pa).
gamma_c=1.5, gamma_s=1.15. [confirmar AN].
"""
import math

GC = 1.50
GS = 1.15
GP_ELU = 1.0     # pretensado en ELU (P como accion, valor medio; gamma_P~1.0)


def _fib_stresses(P, e, M_ext, A, I, c_sup, c_inf):
    """Tension fibra sup/inf (Pa, compresion negativa). M_p = -P*e (hogging)."""
    M = M_ext - P * e
    s_sup = -P / A - M * c_sup / I
    s_inf = -P / A + M * c_inf / I
    return s_sup, s_inf


def tensiones(model, esf):
    s = model["seccion"]; mat = model["material"]; pr = model["pretensado"]
    A = s["A_m2"]; I = s["I_m4"]; c_sup = s["c_sup_m"]; c_inf = s["c_inf_m"]
    e = float(pr["e_centro_m"])
    fck = mat["fck_Pa"]; fck_t = mat["fck_t_Pa"]; fctm = mat["fctm_Pa"]
    P0 = esf["P0_N"]; Pinf = esf["Pm_inf_N"]
    M_g0 = esf["M_g0_Nm"]; M_qp = esf["M_cuasiperm_Nm"]; M_rara = esf["M_rara_Nm"]

    # transferencia (P0 + g0)
    t_sup, t_inf = _fib_stresses(P0, e, M_g0, A, I, c_sup, c_inf)
    lim_c_t = 0.6 * fck_t
    # servicio cuasipermanente (Pinf + M_qp)
    qp_sup, qp_inf = _fib_stresses(Pinf, e, M_qp, A, I, c_sup, c_inf)
    lim_c_qp = 0.45 * fck
    # servicio rara (Pinf + M_rara)
    r_sup, r_inf = _fib_stresses(Pinf, e, M_rara, A, I, c_sup, c_inf)
    lim_c_r = 0.6 * fck

    def comp(sig, lim):
        # aprovechamiento de compresion (sig negativo); lim positivo (magnitud)
        return abs(min(sig, 0.0)) / lim

    out = {
        "transferencia": {
            "sigma_sup_MPa": t_sup / 1e6, "sigma_inf_MPa": t_inf / 1e6,
            "lim_compresion_MPa": -lim_c_t / 1e6,
            "lim_traccion_MPa": fctm / 1e6,
            "u_compresion": max(comp(t_sup, lim_c_t), comp(t_inf, lim_c_t)),
            "traccion_max_MPa": max(0.0, t_sup, t_inf) / 1e6,
            "todo_comprimido": bool(t_sup <= 0 and t_inf <= 0),
            "ok": bool(min(t_sup, t_inf) >= -lim_c_t and max(t_sup, t_inf) <= fctm),
        },
        "servicio_cuasiperm": {
            "sigma_sup_MPa": qp_sup / 1e6, "sigma_inf_MPa": qp_inf / 1e6,
            "lim_compresion_MPa": -lim_c_qp / 1e6,
            "u_compresion": max(comp(qp_sup, lim_c_qp), comp(qp_inf, lim_c_qp)),
            "descompresion_fondo": bool(qp_inf > 0.0),
            "ok": bool(min(qp_sup, qp_inf) >= -lim_c_qp and qp_inf <= 0.0),
            "nota": "sin descompresion del fondo (qp_inf<=0) -> seccion siempre comprimida en cuasipermanente",
        },
        "servicio_rara": {
            "sigma_sup_MPa": r_sup / 1e6, "sigma_inf_MPa": r_inf / 1e6,
            "lim_compresion_MPa": -lim_c_r / 1e6,
            "lim_traccion_fctm_MPa": fctm / 1e6,
            "u_compresion": max(comp(r_sup, lim_c_r), comp(r_inf, lim_c_r)),
            "traccion_inf_MPa": max(0.0, r_inf) / 1e6,
            "u_traccion_fctm": max(0.0, r_inf) / fctm,
            "ok": bool(min(r_sup, r_inf) >= -lim_c_r and max(r_sup, r_inf) <= fctm),
        },
    }
    return out


def M_Rd_fibras(model, esf, As_pasiva_m2=0.0, d_pasiva_m=None):
    """Momento ultimo resistente por FIBRAS (bloque rectangular eta*fcd, lambda*x).
    Acero activo a la profundidad del tendon (d_p), tension fpd; acero pasivo
    opcional a d_pasiva, tension fyd. Equilibrio de axil -> profundidad x.
    Para C40/50 (<=50 MPa): eta=1.0, lambda=0.8."""
    s = model["seccion"]; mat = model["material"]; pr = model["pretensado"]
    b = s["b_m"]; h = s["h_m"]
    fck = mat["fck_Pa"]
    fcd = fck / GC
    eta = 1.0
    lam = 0.8

    Ap = float(pr["Ap_mm2"]) * 1e-6
    fpk = float(pr["fpk_MPa"]) * 1e6
    fp01k = float(pr["fp01k_MPa"]) * 1e6
    Ep = float(pr["Ep_GPa"]) * 1e9
    fpd = fp01k / GS                  # limite de calculo del acero activo
    e = float(pr["e_centro_m"])
    d_p = s["cdg_m"] + e             # canto util del tendon (desde fibra superior)

    fyd = 500e6 / GS                 # B500S por defecto
    d_s = d_pasiva_m if d_pasiva_m is not None else (h - 0.05)

    # predeformacion del acero activo (incremento desde sigma_pm_inf hasta fpd)
    # se adopta el modelo simplificado: el acero activo alcanza fpd en rotura.
    Fp = Ap * fpd
    Fs = As_pasiva_m2 * fyd
    T = Fp + Fs                        # traccion total

    # equilibrio: C = eta*fcd*b*(lam*x) = T  -> x
    x = T / (eta * fcd * b * lam)
    z_block = lam * x / 2.0            # cdg del bloque desde fibra superior
    # brazo de cada traccion al cdg del bloque
    M = Fp * (d_p - z_block) + Fs * (d_s - z_block)
    return {
        "fcd_MPa": fcd / 1e6, "fpd_MPa": fpd / 1e6, "fyd_MPa": fyd / 1e6,
        "Ap_mm2": Ap * 1e6, "As_pasiva_cm2": As_pasiva_m2 * 1e4,
        "d_p_m": d_p, "d_s_m": d_s,
        "Fp_kN": Fp / 1e3, "Fs_kN": Fs / 1e3, "T_total_kN": T / 1e3,
        "x_m": x, "x_d_ratio": x / d_p,
        "M_Rd_kNm": M / 1e3,
        "modelo": "bloque rectangular eta=1.0 lambda=0.8 (C40/50<=50MPa)",
    }


def cortante_pretensado(model, esf, V_Ed_N, As_long_m2=0.0):
    """V_Rd,c de elemento sin armadura de cortante con pretensado (§6.2.2 ec.6.2a):
       V_Rd,c = [C_Rd,c*k*(100*rho_l*fck)^(1/3) + k1*sigma_cp]*bw*d
       con minimo (6.2b) v_min = 0.035*k^1.5*fck^0.5."""
    s = model["seccion"]; mat = model["material"]; pr = model["pretensado"]
    b = s["b_m"]; h = s["h_m"]
    fck_MPa = mat["fck_Pa"] / 1e6
    e = float(pr["e_centro_m"])
    d = s["cdg_m"] + e
    A = s["A_m2"]
    Pinf = esf["Pm_inf_N"]
    sigma_cp = min(Pinf / A, 0.2 * mat["fck_Pa"] / GC)   # limitado a 0.2 fcd
    CRdc = 0.18 / GC
    k = min(1.0 + math.sqrt(0.2 / d), 2.0)
    rho_l = min(As_long_m2 / (b * d), 0.02) if As_long_m2 > 0 else 0.0
    # incluir el acero activo como longitudinal a efectos de rho_l
    Ap = float(pr["Ap_mm2"]) * 1e-6
    rho_l = min((As_long_m2 + Ap) / (b * d), 0.02)
    vRdc = (CRdc * k * (100.0 * rho_l * fck_MPa) ** (1.0 / 3.0) * 1e6
            + 0.15 * sigma_cp) * b * d
    vmin = (0.035 * k ** 1.5 * fck_MPa ** 0.5 * 1e6 + 0.15 * sigma_cp) * b * d
    V_Rdc = max(vRdc, vmin)
    return {
        "V_Ed_kN": V_Ed_N / 1e3, "V_Rd_c_kN": V_Rdc / 1e3,
        "sigma_cp_MPa": sigma_cp / 1e6, "k": k, "rho_l": rho_l,
        "u": V_Ed_N / V_Rdc if V_Rdc > 0 else 0.0,
        "ok": bool(V_Ed_N <= V_Rdc),
        "nota": "si V_Ed>V_Rd,c disponer armadura de cortante (celosia §6.2.3)",
    }


def fisuracion(model, ten):
    """Control de fisuracion §7.3 simplificado por el estado tensional rara:
    si la traccion en el fondo bajo combinacion rara es < fctm, no se forma
    fisura significativa (clase de exposicion XC). Si descomprime, estimar w_k."""
    fctm = model["material"]["fctm_Pa"] / 1e6
    sig_inf = ten["servicio_rara"]["sigma_inf_MPa"]
    fisura = sig_inf > fctm
    return {
        "sigma_inf_rara_MPa": sig_inf, "fctm_MPa": fctm,
        "supera_fctm": bool(fisura),
        "u": max(0.0, sig_inf) / fctm,
        "ok": bool(not fisura),
        "nota": "traccion de fondo en rara < fctm -> sin fisuracion significativa "
                "(clase XC). [confirmar AN] limite de descompresion segun exposicion.",
    }


def verificar(model, esf, As_pasiva_m2=0.0):
    ten = tensiones(model, esf)
    elu = M_Rd_fibras(model, esf, As_pasiva_m2=As_pasiva_m2)
    M_Ed = esf["M_ELU_Nm"]
    elu["M_Ed_kNm"] = M_Ed / 1e3
    elu["u"] = M_Ed / (elu["M_Rd_kNm"] * 1e3)
    elu["ok"] = bool(M_Ed <= elu["M_Rd_kNm"] * 1e3)
    fis = fisuracion(model, ten)
    cor = cortante_pretensado(model, esf, esf.get("V_ELU_N", 0.0),
                              As_long_m2=As_pasiva_m2)

    aprov = {
        "compresion_transferencia": ten["transferencia"]["u_compresion"],
        "compresion_cuasiperm": ten["servicio_cuasiperm"]["u_compresion"],
        "compresion_rara": ten["servicio_rara"]["u_compresion"],
        "traccion_rara_fctm": ten["servicio_rara"]["u_traccion_fctm"],
        "ELU_flexion": elu["u"],
        "fisuracion": fis["u"],
        "cortante": cor["u"],
    }
    oks = [ten["transferencia"]["ok"], ten["servicio_cuasiperm"]["ok"],
           ten["servicio_rara"]["ok"], elu["ok"], fis["ok"], cor["ok"]]
    aprov_max = max(aprov.values())
    out = {
        "tensiones": ten,
        "ELU_flexion": elu,
        "fisuracion": fis,
        "cortante": cor,
        "aprovechamientos": aprov,
        "aprov_max": aprov_max,
        "veredicto": "CUMPLE" if all(oks) else "REVISAR",
    }
    return out
