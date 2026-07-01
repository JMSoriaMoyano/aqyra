"""
Verificacion de VIGA POSTESADA CONTINUA (hiperestatica) - EN 1992-1-1 §5.10/§5.5/§7.

  - TENSIONES POR FIBRA con el MOMENTO SECUNDARIO incluido:
        M = M_ext - P*e + M_sec   ->  sigma = -P/A -+ M*c/I
    en TRANSFERENCIA (P0, M_sec escalado a P0), SERVICIO cuasipermanente y rara,
    en las secciones criticas (apoyo central / centro de vano).
  - ELU DE FLEXION por FIBRAS con el SECUNDARIO como ACCION (gamma_P=1.0, §5.10.8):
        M_Ed = gamma_G*M_g + gamma_Q*M_q + 1.0*M_sec
    y M_Rd por fibras con el acero ACTIVO a f_pd (+ pasivo), evitando doble computo
    del primario. Centro de vano (sagging) y apoyo central (hogging).
  - REDISTRIBUCION §5.5: coeficiente delta admisible a partir de x_u/d.
  - FISURACION §7.3 (traccion de fondo/cabeza en rara < fctm).

Sigmas: compresion NEGATIVA, traccion POSITIVA. Sagging (+) = traccion abajo.
SI (N, m, Pa). gamma_c=1.5, gamma_s=1.15. [confirmar AN].
"""
GC = 1.50
GS = 1.15


def tension_fibra(P, e, M_ext, M_sec, A, I, c_sup, c_inf):
    """Tension fibra sup/inf (Pa, compresion negativa) con secundario.
    M = M_ext - P*e + M_sec ; sigma_sup = -P/A - M*c_sup/I ; sigma_inf = -P/A + M*c_inf/I."""
    M = M_ext - P * e + M_sec
    s_sup = -P / A - M * c_sup / I
    s_inf = -P / A + M * c_inf / I
    return s_sup, s_inf, M


def tensiones_seccion(model, sec):
    """sec: dict con e (m), M_ext por combinacion (Nm) y M_sec a Pinf (Nm).
    Escala M_sec a P0 en transferencia (proporcional a P)."""
    s = model["seccion"]; mat = model["material"]; esf = model["esfuerzos"]
    A = s["A_m2"]; I = s["I_m4"]; csup = s["c_sup_m"]; cinf = s["c_inf_m"]
    fck = mat["fck_Pa"]; fck_t = mat["fck_t_Pa"]; fctm = mat["fctm_Pa"]
    P0 = esf["P0_N"]; Pinf = esf["Pm_inf_N"]
    e = sec["e_m"]; Msec = sec["M_sec_Nm"]
    Msec0 = Msec * (P0 / Pinf)

    t_sup, t_inf, _ = tension_fibra(P0, e, sec["M_g0_Nm"], Msec0, A, I, csup, cinf)
    qp_sup, qp_inf, _ = tension_fibra(Pinf, e, sec["M_qp_Nm"], Msec, A, I, csup, cinf)
    r_sup, r_inf, _ = tension_fibra(Pinf, e, sec["M_rara_Nm"], Msec, A, I, csup, cinf)
    lim_t = 0.6 * fck_t; lim_qp = 0.45 * fck; lim_r = 0.6 * fck

    def comp(sig, lim):
        return abs(min(sig, 0.0)) / lim

    return {
        "transferencia": {
            "sigma_sup_MPa": t_sup / 1e6, "sigma_inf_MPa": t_inf / 1e6,
            "lim_compresion_MPa": -lim_t / 1e6, "lim_traccion_MPa": fctm / 1e6,
            "u_compresion": max(comp(t_sup, lim_t), comp(t_inf, lim_t)),
            "traccion_max_MPa": max(0.0, t_sup, t_inf) / 1e6,
            "ok": bool(min(t_sup, t_inf) >= -lim_t and max(t_sup, t_inf) <= fctm),
        },
        "servicio_cuasiperm": {
            "sigma_sup_MPa": qp_sup / 1e6, "sigma_inf_MPa": qp_inf / 1e6,
            "lim_compresion_MPa": -lim_qp / 1e6,
            "u_compresion": max(comp(qp_sup, lim_qp), comp(qp_inf, lim_qp)),
            "traccion_max_MPa": max(0.0, qp_sup, qp_inf) / 1e6,
            "ok": bool(min(qp_sup, qp_inf) >= -lim_qp and max(qp_sup, qp_inf) <= fctm),
        },
        "servicio_rara": {
            "sigma_sup_MPa": r_sup / 1e6, "sigma_inf_MPa": r_inf / 1e6,
            "lim_compresion_MPa": -lim_r / 1e6, "lim_traccion_fctm_MPa": fctm / 1e6,
            "u_compresion": max(comp(r_sup, lim_r), comp(r_inf, lim_r)),
            "traccion_max_MPa": max(0.0, r_sup, r_inf) / 1e6,
            "u_traccion_fctm": max(0.0, r_sup, r_inf) / fctm,
            "ok": bool(min(r_sup, r_inf) >= -lim_r and max(r_sup, r_inf) <= fctm),
        },
    }


def M_Rd_fibras(model, sec, sense, As_pasiva_m2=0.0):
    """M_Rd por fibras (bloque eta*fcd, lambda*x). sense in {'sagging','hogging'}.
    Acero activo a f_pd a su canto util d_p segun el sentido; pasivo opcional."""
    s = model["seccion"]; mat = model["material"]; pr = model["pretensado"]
    b = s["b_m"]; h = s["h_m"]; cdg = s["cdg_m"]
    fck = mat["fck_Pa"]; fcd = fck / GC
    eta = 1.0; lam = 0.8
    Ap = float(pr["Ap_mm2"]) * 1e-6
    fp01k = float(pr["fp01k_MPa"]) * 1e6
    fpd = fp01k / GS
    e = sec["e_m"]                       # excentricidad del tendon (m, +abajo)
    dist_top = cdg + e                   # distancia tendon desde fibra superior
    cover = 0.05
    if sense == "sagging":
        d_p = dist_top                   # compresion arriba
        d_s = h - cover
    else:                                 # hogging: compresion abajo
        d_p = h - dist_top
        d_s = h - cover
    fyd = 500e6 / GS
    Fp = Ap * fpd
    Fs = As_pasiva_m2 * fyd
    T = Fp + Fs
    x = T / (eta * fcd * b * lam)
    zc = lam * x / 2.0
    M = Fp * (d_p - zc) + Fs * (d_s - zc)
    return {"sense": sense, "fcd_MPa": fcd / 1e6, "fpd_MPa": fpd / 1e6,
            "Ap_mm2": Ap * 1e6, "As_pasiva_cm2": As_pasiva_m2 * 1e4,
            "d_p_m": d_p, "x_m": x, "x_d_ratio": x / d_p,
            "Fp_kN": Fp / 1e3, "Fs_kN": Fs / 1e3,
            "M_Rd_kNm": M / 1e3}


def redistribucion_delta(x_d, fck_MPa):
    """delta minimo admisible (§5.5(4)): fck<=50 -> delta>=0.44+1.25*(xu/d).
    Devuelve delta_min y la reduccion maxima de momento permitida (1-delta)."""
    if fck_MPa <= 50:
        d_min = 0.44 + 1.25 * x_d
    else:
        d_min = 0.54 + 1.25 * (0.6 + 0.0014 / 0.0035) * x_d
    d_min = max(min(d_min, 1.0), 0.7)
    return {"delta_min": d_min, "reduccion_max_pct": 100.0 * (1.0 - d_min),
            "x_d": x_d, "nota": "redistribucion admisible si la capacidad de "
            "rotacion (x/d) lo permite (§5.5)."}
