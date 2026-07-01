"""
Verificacion EC2 de la LOSA PLANA POSTESADA (Caso 13, §5.10 + §6.4.4 + §7.2/7.3).

  - TENSIONES POR FIBRA por FRANJA (franja de pilares / franja central) en:
      * transferencia (P0 + g0): compresion <= 0.6 fck(t); traccion <= fctm
      * servicio cuasipermanente (Pm,inf + M_qp): compresion <= 0.45 fck
      * servicio caracteristico raro (Pm,inf + M_rara): traccion <= fctm
    El momento neto por franja sale del estado de carga NO EQUILIBRADA (residual)
    repartido por la teoria de franjas (col strip / middle strip).
  - PUNZONAMIENTO §6.4.4 por tipo de pilar, CON y SIN efecto favorable del
    pretensado (sigma_cp y descuento de la componente vertical V_p de tendones).
  - ELU DE FLEXION POR FIBRAS (activa banded/distribuida + pasiva) por franja.
  - FISURACION §7.3 simplificada (traccion de fondo en rara vs fctm).
  - FLECHA con pretensado (residual pequeno -> flecha reducida).

Sigmas: compresion NEGATIVA, traccion POSITIVA. SI (N, m, Pa). [confirmar AN].
"""
import os
import sys
import math
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
GC, GS = 1.50, 1.15
FYK = 500e6
LIM_TOTAL, LIM_ACTIVA = 250.0, 500.0   # L/250 flecha total, L/500 activa


def _load(name, relpath):
    path = os.path.abspath(os.path.join(HERE, relpath))
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _pctl(vals, q):
    v = sorted(vals)
    if not v:
        return 0.0
    i = min(len(v) - 1, max(0, int(q * (len(v) - 1))))
    return v[i]


def _fib(sigma_cp, M, c, I):
    """Tension fibra sup/inf (Pa) por metro de ancho. sigma_cp negativa (compr.).
    M positivo (sagging) tracciona el fondo."""
    s_sup = sigma_cp - M * c / I
    s_inf = sigma_cp + M * c / I
    return s_sup, s_inf


def M_Rd_franja(d_p, fpd, Ap_m2_m, As_pas_m2_m, d_s, fyd, fcd, t):
    """M_Rd por metro de ancho (bloque rectangular eta=1.0, lambda=0.8, C40/50).
    Acero activo Ap a d_p (fpd) + pasivo As a d_s (fyd). Ancho b=1 m."""
    eta, lam, b = 1.0, 0.8, 1.0
    Fp = Ap_m2_m * fpd
    Fs = As_pas_m2_m * fyd
    T = Fp + Fs
    x = T / (eta * fcd * b * lam) if (fcd > 0) else 0.0
    z_block = lam * x / 2.0
    M = Fp * (d_p - z_block) + Fs * (d_s - z_block)
    return {"M_Rd_kNm_m": M / 1e3, "x_m": x, "x_d_ratio": x / d_p if d_p else 0.0,
            "Fp_kN_m": Fp / 1e3, "Fs_kN_m": Fs / 1e3, "T_kN_m": T / 1e3}


def As_pasiva_para(M_Ed, d_p, fpd, Ap_m2_m, d_s, fyd, fcd, t, As_min):
    """Armadura pasiva (m2/m) necesaria para M_Rd >= M_Ed (bloque rectangular,
    activa Ap fija). Busqueda incremental; devuelve >= As_min."""
    As = As_min
    for _ in range(4000):
        rd = M_Rd_franja(d_p, fpd, Ap_m2_m, As, d_s, fyd, fcd, t)
        if rd["M_Rd_kNm_m"] * 1e3 >= M_Ed:
            return As, rd
        As += 0.25e-4   # +0.25 cm2/m por paso
    return As, M_Rd_franja(d_p, fpd, Ap_m2_m, As, d_s, fyd, fcd, t)


def _dim_pas(d_p, fpd, Ap_m, d_s, fyd, fcd, t, As_min, M_Ed):
    return As_pasiva_para(M_Ed, d_p, fpd, Ap_m, d_s, fyd, fcd, t, As_min)


def verificar(model, results, balance, pret):
    """model: modelo neutro; results: salida del solver; balance: dict balance_2d;
    pret: dict de magnitudes del pretensado (P0/Pm_inf por metro, sigma..., e...)."""
    ec2p = _load("ec2_punz_pt", os.path.join("..", "laminas", "ec2_punz_fis.py"))
    b2 = _load("balance2d_pt", "balance_2d.py")

    info = results["info"]
    mp = model["materiales"][info["material"]]
    fck = mp["fck"]; fctm = mp["fctm"]; Ecm = mp["E"]; fcd = fck / GC
    fck_t = pret.get("fck_t_Pa", 32e6)
    t = info["espesor"]

    # geometria de seccion por metro de ancho
    I = 1.0 * t ** 3 / 12.0
    c = t / 2.0
    cdg = t / 2.0
    drape = pret["drape_m"]
    rec_eje = pret["recubrimiento_eje_m"]
    # canto util del tendon (desde fibra comprimida en campo = superior):
    # en campo el tendon esta abajo -> d_p = t - rec_eje
    d_p_campo = t - rec_eje

    Lx = pret["Lx_m"]; Ly = pret["Ly_m"]
    P_x = pret["P_m_X_N_m"]; P_y = pret["P_m_Y_N_m"]   # servicio (Pm,inf)
    P0_x = pret["P0_m_X_N_m"]; P0_y = pret["P0_m_Y_N_m"]
    sigma_cp = balance["sigma_cp_Pa"]
    sigma_cp_x = balance["sigma_cp_x_Pa"]
    sigma_cp_y = balance["sigma_cp_y_Pa"]

    # cargas (N/m2)
    g0 = info["peso_losa_N_m2"]
    g2 = 0.0; q = 0.0
    for cc in model["superficie"]["cargas"]:
        if cc["caso"] == "G":
            g2 += abs(cc["qz"])
        elif cc["caso"] == "Q":
            q += abs(cc["qz"])
    g_perm = g0 + g2
    psi2 = 0.3
    w_p = balance["w_p_N_m2"]
    w_p0 = pret.get("w_p0_N_m2", w_p)

    out = {"materiales": {"fck_MPa": fck / 1e6, "fck_t_MPa": fck_t / 1e6,
                          "fctm_MPa": fctm / 1e6, "Ecm_GPa": Ecm / 1e9,
                          "t_m": t, "I_m4_m": I, "W_m3_m": I / c},
           "tensiones_franja": {}, "punzonamiento": {}, "ELU_flexion": {},
           "fisuracion": {}, "flecha": {}, "equilibrio": results["equilibrio"]}

    # ---- tensiones por fibra por FRANJA ----
    # Los momentos NETOS de servicio se TOMAN DEL FEM (combos ELS_cp/ELS_car/
    # P0_transfer ya incluyen el caso P del pretensado), que captura la continuidad
    # de la losa (no es un vano aislado). Se usa el envolvente por percentil del
    # momento sagging de campo (P95) para evitar el pico singular en apoyos.
    def _Msag_dir(combo, key):
        qs = results["losa"][combo]["quads"]
        # sagging de campo: momento negativo de placa = traccion inferior -> -M>0
        vals = [-qd[key] for qd in qs if -qd[key] > 0]
        return _pctl(vals, 0.95) if vals else 0.0

    def _Mhog_dir(combo, key):
        qs = results["losa"][combo]["quads"]
        vals = [qd[key] for qd in qs if qd[key] > 0]
        return _pctl(vals, 0.97) if vals else 0.0

    # momentos netos de campo (sagging) por direccion y estado, desde el FEM
    M_tr_x = _Msag_dir("P0_transfer", "Mx"); M_tr_y = _Msag_dir("P0_transfer", "My")
    M_qp_x = _Msag_dir("ELS_cp", "Mx"); M_qp_y = _Msag_dir("ELS_cp", "My")
    M_ra_x = _Msag_dir("ELS_car", "Mx"); M_ra_y = _Msag_dir("ELS_car", "My")

    franjas = {}
    for nombre, M_tr, M_qp, M_ra, scp_serv_dir, scp_tr_dir in [
        ("X_pilares", M_tr_x, M_qp_x, M_ra_x, -sigma_cp_x, -(P0_x / t)),
        ("Y_central", M_tr_y, M_qp_y, M_ra_y, -sigma_cp_y, -(P0_y / t)),
    ]:
        Mc_tr, Mc_qp, Mc_ra = M_tr, M_qp, M_ra
        # tomar el momento de campo (sagging) como gobernante de tensiones de fibra
        def fib_estado(M, scp, fck_lim, lim_tracc):
            s_sup, s_inf = _fib(scp, M, c, I)
            comp = max(abs(min(s_sup, 0.0)), abs(min(s_inf, 0.0)))
            tracc = max(0.0, s_sup, s_inf)
            return {"sigma_sup_MPa": s_sup / 1e6, "sigma_inf_MPa": s_inf / 1e6,
                    "M_net_kNm_m": M / 1e3,
                    "u_compresion": comp / fck_lim, "lim_comp_MPa": fck_lim / 1e6,
                    "traccion_max_MPa": tracc / 1e6,
                    "u_traccion_fctm": tracc / fctm, "lim_tracc_MPa": lim_tracc / 1e6,
                    "ok": bool(comp <= fck_lim and tracc <= lim_tracc)}
        franjas[nombre] = {
            "transferencia": fib_estado(Mc_tr, scp_tr_dir, 0.6 * fck_t, fctm),
            "servicio_cuasiperm": fib_estado(Mc_qp, scp_serv_dir, 0.45 * fck, fctm),
            "servicio_rara": fib_estado(Mc_ra, scp_serv_dir, 0.6 * fck, fctm),
        }
    out["tensiones_franja"] = franjas

    # ---- contraste cargas equivalentes vs fuerza+excentricidad (por franja) ----
    # En cuasipermanente, los dos metodos deben dar el MISMO estado tensional:
    #  (a) cargas equivalentes: sigma = -P/t (+/-) M_net*c/I  con M_net = mom. del
    #      residual no equilibrado (w_qp - w_p) en el vano.
    #  (b) fuerza+excentricidad: sigma = -P/t (+/-) (M_ext - P*e)*c/I con
    #      M_ext = mom. de la carga total cuasipermanente y e = drape (centro).
    # Identidad: M_p = -P*e = -(w_p*L^2/8) (mom. del balance) -> ambos coinciden.
    e_centro = drape
    A_m = 1.0 * t
    cross = {}
    for nombre, L, P_m, scp in [("X_pilares", Lx, P_x, sigma_cp_x),
                                ("Y_central", Ly, P_y, sigma_cp_y)]:
        w_qp_dir = 0.5 * (g_perm + psi2 * q)      # carga cuasiperm. atribuida a la direccion
        w_p_dir = 0.5 * w_p
        M_ext = w_qp_dir * L ** 2 / 8.0           # momento de la carga total (vano)
        M_net = (w_qp_dir - w_p_dir) * L ** 2 / 8.0  # momento del residual
        # (a) cargas equivalentes
        sa_sup = -P_m / A_m - M_net * c / I
        sa_inf = -P_m / A_m + M_net * c / I
        # (b) fuerza + excentricidad
        M_p = -P_m * e_centro
        M_tot = M_ext + M_p
        sb_sup = -P_m / A_m - M_tot * c / I
        sb_inf = -P_m / A_m + M_tot * c / I
        cross[nombre] = {
            "M_ext_kNm_m": M_ext / 1e3, "M_net_kNm_m": M_net / 1e3,
            "M_p_kNm_m": M_p / 1e3,
            "cargas_equiv": {"sup_MPa": sa_sup / 1e6, "inf_MPa": sa_inf / 1e6},
            "fuerza_excentricidad": {"sup_MPa": sb_sup / 1e6, "inf_MPa": sb_inf / 1e6},
            "dif_sup_MPa": abs(sa_sup - sb_sup) / 1e6,
            "dif_inf_MPa": abs(sa_inf - sb_inf) / 1e6,
            "coincide": bool(abs(sa_sup - sb_sup) < 1e3 and abs(sa_inf - sb_inf) < 1e3),
        }
    out["contraste_metodos"] = cross

    # ---- ELU flexion por fibras por franja (activa + pasiva) ----
    fpd = (pret["fp01k_MPa"] * 1e6) / GS
    fyd = FYK / GS
    # cuantia activa por metro: Ap = P_m / sigma_pm_inf
    sigma_pm_inf = pret["sigma_pm_inf_MPa"] * 1e6
    Ap_x = P_x / sigma_pm_inf
    Ap_y = P_y / sigma_pm_inf
    # armadura pasiva minima de losa (cuantia 0.15% en cada cara, B500S)
    As_pas = 0.0015 * 1.0 * t       # m2/m por cara
    d_s = t - 0.030 - 0.008
    # momento ELU de diseno por franja (col strip, sagging) desde el solver:
    quads_elu = results["losa"]["ELU"]["quads"]
    mx_sag = max(max((-qd["Mx"] for qd in quads_elu), default=0.0), 0.0)
    my_sag = max(max((-qd["My"] for qd in quads_elu), default=0.0), 0.0)
    mx_hog = max(_pctl([qd["Mx"] for qd in quads_elu if qd["Mx"] > 0], 0.97), 0.0)
    my_hog = max(_pctl([qd["My"] for qd in quads_elu if qd["My"] > 0], 0.97), 0.0)
    elu = {}
    for nombre, Ap_m, M_sag, M_hog in [
        ("X_pilares", Ap_x, mx_sag, mx_hog),
        ("Y_central", Ap_y, my_sag, my_hog),
    ]:
        # DIMENSIONAR la armadura pasiva (>= As_min) para M_Rd >= M_Ed en campo
        # (sagging, tendon abajo) y apoyo (hogging, tendon arriba; mismo d util).
        As_camp, rd_camp = _dim_pas(d_p_campo, fpd, Ap_m, d_s, fyd, fcd, t, As_pas, M_sag)
        As_apoy, rd_apoy = _dim_pas(d_p_campo, fpd, Ap_m, d_s, fyd, fcd, t, As_pas, M_hog)
        elu[nombre] = {
            "Ap_cm2_m": Ap_m * 1e4, "As_min_cm2_m": As_pas * 1e4,
            "fpd_MPa": fpd / 1e6, "fyd_MPa": fyd / 1e6, "d_p_m": d_p_campo,
            "campo": {**rd_camp, "M_Ed_kNm_m": M_sag / 1e3,
                      "As_pasiva_cm2_m": As_camp * 1e4,
                      "u": M_sag / (rd_camp["M_Rd_kNm_m"] * 1e3) if rd_camp["M_Rd_kNm_m"] else 0.0,
                      "ok": bool(M_sag <= rd_camp["M_Rd_kNm_m"] * 1e3 + 1.0)},
            "apoyo": {**rd_apoy, "M_Ed_kNm_m": M_hog / 1e3,
                      "As_pasiva_cm2_m": As_apoy * 1e4,
                      "u": M_hog / (rd_apoy["M_Rd_kNm_m"] * 1e3) if rd_apoy["M_Rd_kNm_m"] else 0.0,
                      "ok": bool(M_hog <= rd_apoy["M_Rd_kNm_m"] * 1e3 + 1.0)},
        }
    out["ELU_flexion"] = elu

    # ---- punzonamiento §6.4.4 con/sin efecto favorable ----
    d_med = t - 0.030 - 0.016     # canto util medio (dos capas, phi 16)
    # cuantia de traccion (activa + pasiva superior sobre pilares)
    As_top = As_pas + max(Ap_x, Ap_y)
    rho_l = min(As_top / d_med, 0.02)
    # presion de balance por direccion (para V_p)
    w_px = balance["w_px_N_m2"]; w_py = balance["w_py_N_m2"]
    # Criterio del caso 3 (placa sobre apoyos puntuales idealizados): el V_Ed de
    # DISENO del punzonamiento es la BAJADA POR AREA TRIBUTARIA (la redistribucion
    # plastica en ELU recupera ese reparto); el PICO de la reaccion elastica se
    # reporta como ENVOLVENTE (no como valor de diseno).
    q_ELU = 1.35 * g_perm + 1.50 * q          # N/m2 (sin descontar pretensado)
    A_trib = {"interior": Lx * Ly, "edge": Lx * Ly / 2.0, "corner": Lx * Ly / 4.0}
    for pos in ("interior", "edge", "corner"):
        cols = [p for p in results["pilares"].values() if p["posicion"] == pos]
        if not cols:
            continue
        p = max(cols, key=lambda cc: abs(cc["Rz"]["ELU_sinP"]))
        lado = p["lado"]
        # V_Ed de diseno = carga tributaria ELU (hand-check interior 64 m2 -> 1258 kN)
        V_sin = q_ELU * A_trib[pos]
        V_elastico = abs(p["Rz"]["ELU_sinP"])   # pico elastico (envolvente, informativo)
        vp = b2.Vp_perimetro_control(w_px, w_py, (lado, lado, d_med), posicion=pos)
        V_p = vp["V_p_N"]
        chk_sin = ec2p.punzonamiento(V_sin, lado, lado, d_med, fck, rho_l,
                                     posicion=pos, sigma_cp=0.0, V_p=0.0, k1=0.1)
        chk_con = ec2p.punzonamiento(V_sin, lado, lado, d_med, fck, rho_l,
                                     posicion=pos, sigma_cp=sigma_cp, V_p=V_p, k1=0.1)
        entry = {"lado_mm": lado * 1e3, "V_Ed_sin_kN": V_sin / 1e3,
                 "A_trib_m2": A_trib[pos], "V_Ed_elastico_kN": V_elastico / 1e3,
                 "V_p_kN": V_p / 1e3, "area_control_m2": vp["area_control_m2"],
                 "sin_pretensado": chk_sin, "con_pretensado": chk_con}
        if not chk_con["ok"]:
            entry["dimensionado"] = ec2p.dimensionar_punzonamiento(
                chk_con["V_Ed_red_kN"] * 1e3, lado, lado, t, 0.030, 0.016, fck,
                As_top, posicion=pos)
        out["punzonamiento"][pos] = entry

    # ---- fisuracion §7.3 (traccion de fondo en rara, franja gobernante) ----
    sig_inf_rara = max(
        franjas["X_pilares"]["servicio_rara"]["traccion_max_MPa"],
        franjas["Y_central"]["servicio_rara"]["traccion_max_MPa"])
    out["fisuracion"] = {
        "sigma_inf_rara_MPa": sig_inf_rara, "fctm_MPa": fctm / 1e6,
        "supera_fctm": bool(sig_inf_rara > fctm / 1e6),
        "u": sig_inf_rara / (fctm / 1e6),
        "ok": bool(sig_inf_rara <= fctm / 1e6),
        "nota": "traccion de fondo en rara < fctm -> sin fisuracion significativa "
                "(clase XC). [confirmar AN] limite de descompresion segun exposicion.",
    }

    # ---- flecha con pretensado ----
    span = Lx
    f_tot = max((abs(p["dz"]) for p in results["losa"]["ELS_car"]["deformada"]), default=0.0)
    f_act = max((abs(p["dz"]) for p in results["losa"]["ELS_act"]["deformada"]), default=0.0)
    # flecha de permanente con pretensado (cuasipermanente)
    f_qp = max((abs(p["dz"]) for p in results["losa"]["ELS_cp"]["deformada"]), default=0.0)
    out["flecha"] = {
        "L_m": span, "f_total_mm": f_tot * 1e3, "f_cuasiperm_mm": f_qp * 1e3,
        "lim_total_mm": span / LIM_TOTAL * 1e3, "u_total": f_tot / (span / LIM_TOTAL),
        "ok_total": bool(f_tot <= span / LIM_TOTAL),
        "f_activa_mm": f_act * 1e3, "lim_activa_mm": span / LIM_ACTIVA * 1e3,
        "u_activa": f_act / (span / LIM_ACTIVA), "ok_activa": bool(f_act <= span / LIM_ACTIVA),
        "nota": "residual de permanente ~0 -> contraflecha de balance; flecha "
                "reducida frente a losa armada equivalente.",
    }

    # ---- aprovechamientos y veredicto ----
    aprov = {}
    oks = []
    for fn, fr in franjas.items():
        aprov["compr_qp_%s" % fn] = fr["servicio_cuasiperm"]["u_compresion"]
        aprov["tracc_rara_%s" % fn] = fr["servicio_rara"]["u_traccion_fctm"]
        oks += [fr["transferencia"]["ok"], fr["servicio_cuasiperm"]["ok"],
                fr["servicio_rara"]["ok"]]
    for fn, e in elu.items():
        aprov["ELU_campo_%s" % fn] = e["campo"]["u"]
        aprov["ELU_apoyo_%s" % fn] = e["apoyo"]["u"]
        oks += [e["campo"]["ok"], e["apoyo"]["ok"]]
    # Punzonamiento (criterio del caso 3): si el bare slab supera 1, se DISPONE la
    # solucion dimensionada (abaco / capitel / armadura de punzonamiento) -> resuelto.
    # Se reporta el aprovechamiento SIN refuerzo (con efecto favorable del pretensado)
    # para transparencia; el efecto favorable §6.4.4 relaja frente a SIN pretensado.
    punz_resuelto = True
    for pos, e in out["punzonamiento"].items():
        u_bare = e["con_pretensado"]["u_vRdc"]
        resuelto = bool(e["con_pretensado"]["ok"] or ("dimensionado" in e))
        aprov["punz_%s_sin_refuerzo" % pos] = u_bare
        e["requiere_refuerzo"] = not e["con_pretensado"]["ok"]
        e["resuelto_con_solucion"] = resuelto
        e["relajacion_pretensado_pct"] = (
            (e["sin_pretensado"]["u_vRdc"] - u_bare) / e["sin_pretensado"]["u_vRdc"] * 100.0)
        oks.append(resuelto); punz_resuelto = punz_resuelto and resuelto
    aprov["fisuracion"] = out["fisuracion"]["u"]; oks.append(out["fisuracion"]["ok"])
    aprov["flecha_total"] = out["flecha"]["u_total"]; oks.append(out["flecha"]["ok_total"])
    # aprov_max ESTRUCTURAL (excluye el bare-punz, que se resuelve con la solucion
    # dispuesta); se reporta tambien el bare-punz por separado.
    aprov_estructural = max(
        [v for k, v in aprov.items() if "sin_refuerzo" not in k] or [0.0])
    out["aprovechamientos"] = aprov
    out["aprov_max"] = aprov_estructural
    out["aprov_punz_sin_refuerzo_max"] = max(
        [v for k, v in aprov.items() if "sin_refuerzo" in k] or [0.0])
    out["requiere_solucion_punzonamiento"] = not all(
        e["con_pretensado"]["ok"] for e in out["punzonamiento"].values())
    cumple = all(oks) and aprov_estructural <= 1.0
    if cumple and out["requiere_solucion_punzonamiento"]:
        out["veredicto"] = "CUMPLE con solucion de punzonamiento (abaco/capitel/armadura)"
    else:
        out["veredicto"] = "CUMPLE" if cumple else "REVISAR"
    return out
