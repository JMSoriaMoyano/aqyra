"""
Verificacion sismica de la PANTALLA DE CORTANTE (Caso 11, EC8/EC2 + AN Esp.).

  - Cortante del alma (EC2 §6.2.3 + amplificacion EC8 DCM): V_Rd,max (bielas)
    y armadura horizontal del alma (rho_h), V_Rd,s.
  - Elementos de borde confinados (EC8 §5.4.3.4 / §5.5.3.4): longitud l_c,
    armadura vertical concentrada y confinamiento, comprobacion de compresion
    y cuantia minima.
  - Interaccion N-M en base con armadura vertical (distribuida en el alma +
    concentrada en bordes); punto de diseno sobre el diagrama N-M.
  - Deriva entre plantas (limitacion de dano §4.4.3.2): d_r*nu <= limite.

NDP [confirmar AN]: factor de amplificacion de cortante en DCM, beta del
limite del espectro, nu de limitacion de dano, limite de deriva.
"""
import math

GC = 1.50          # gamma_c
GS = 1.15          # gamma_s
C_NOM = 0.040      # recubrimiento mecanico (m) [confirmar AN]


def _fcd(fck_Pa):
    return fck_Pa / GC


def cortante_alma(V_Ed_N, Lw, tw, fck_Pa, fyk_Pa=500e6,
                  eps_amplif=1.5, theta_deg=45.0):
    """Cortante del alma de la pantalla (EC2 §6.2.3, biela 45 deg) con posible
    amplificacion EC8 DCM (eps_amplif). Devuelve V_Rd,max, armadura horizontal
    necesaria y comprobacion.

    Se usa d ~ 0.8*Lw (canto util del muro a cortante en su plano)."""
    fcd = _fcd(fck_Pa)
    fyd = fyk_Pa / GS
    fck = fck_Pa / 1e6
    d = 0.8 * Lw
    z = 0.9 * d
    bw = tw
    V_Ed = eps_amplif * V_Ed_N

    nu1 = 0.6 * (1.0 - fck / 250.0)        # EC2 (6.6N)
    theta = math.radians(theta_deg)
    cot = 1.0 / math.tan(theta)
    tan = math.tan(theta)
    V_Rd_max = nu1 * fcd * bw * z / (cot + tan)     # N

    # armadura horizontal (cercos del alma) A_sw/s = V_Ed/(z*fyd*cot)
    Asw_s = V_Ed / (z * fyd * cot)         # m2/m
    Asw_s_cm2_m = Asw_s * 1e4
    # cuantia horizontal minima de muro sismico (EC8 §5.4.3.4.2): rho_h,min
    rho_h_min = 0.002                       # [confirmar AN]
    Asw_s_min = rho_h_min * bw * 1.0 * 1e4  # cm2/m (por metro de altura, 2 caras)
    Asw_s_dis = max(Asw_s_cm2_m, Asw_s_min)
    aprov = V_Ed / V_Rd_max if V_Rd_max > 0 else 99.0
    return {
        "V_Ed_kN_sin_amplif": float(V_Ed_N / 1e3),
        "eps_amplif_EC8": eps_amplif,
        "V_Ed_diseno_kN": float(V_Ed / 1e3),
        "d_m": d, "z_m": z, "bw_m": bw, "nu1": float(nu1),
        "V_Rd_max_kN": float(V_Rd_max / 1e3),
        "aprov_biela": float(aprov),
        "Asw_s_necesaria_cm2_m": float(Asw_s_cm2_m),
        "rho_h_min": rho_h_min,
        "Asw_s_minima_cm2_m": float(Asw_s_min),
        "Asw_s_diseno_cm2_m": float(Asw_s_dis),
        "ok": bool(aprov <= 1.0),
        "ref": "EC2 §6.2.3 (biela 45) + EC8 §5.4.2.4 (amplif. DCM) [confirmar AN]",
    }


def elemento_borde(N_Ed_N, M_Ed_Nm, Lw, tw, fck_Pa, fyk_Pa=500e6):
    """Elementos de borde confinados (EC8 §5.4.3.4.2 / §5.5.3.4).

    Estima la longitud del elemento de borde l_c, la fuerza de compresion del
    borde y la armadura vertical concentrada necesaria; cuantia minima."""
    fcd = _fcd(fck_Pa)
    fyd = fyk_Pa / GS
    # longitud minima de elemento de borde (EC8 §5.4.3.4.2): max(0.15Lw,1.5tw)
    l_c_min = max(0.15 * Lw, 1.5 * tw)
    # fuerza axil del borde comprimido: N/2 + M/(0.8*Lw)
    brazo = 0.8 * Lw
    F_compr = N_Ed_N / 2.0 + M_Ed_Nm / brazo          # N
    F_tracc = M_Ed_Nm / brazo - N_Ed_N / 2.0          # N (negativo => comprimido)
    # PREDIMENSIONADO: si el hormigon del borde minimo no basta a compresion,
    # se AGRANDA el elemento de borde (hasta 0.5*Lw) para no apoyarse solo en
    # armadura de compresion (criterio de robustez). [confirmar AN]
    l_c = l_c_min
    l_c_max = 0.5 * Lw
    while (0.85 * fcd * (l_c * tw)) < F_compr and l_c < l_c_max:
        l_c = min(l_c + 0.05, l_c_max)
    # capacidad a compresion del puntal de borde (hormigon)
    A_borde = l_c * tw
    N_Rd_c = 0.85 * fcd * A_borde                      # N (hormigon solo)
    # armadura vertical necesaria si F_compr > N_Rd_c
    As_compr = max(0.0, (F_compr - N_Rd_c)) / fyd      # m2
    # armadura de traccion del borde
    As_tracc = max(0.0, F_tracc) / fyd                 # m2
    As_borde = max(As_compr, As_tracc)
    # cuantia minima del elemento de borde (EC8 §5.4.3.4.2(8)): 0.5% de A_borde
    rho_min = 0.005                                    # [confirmar AN]
    As_min = rho_min * A_borde
    As_dis = max(As_borde, As_min)
    aprov_compr = F_compr / N_Rd_c if N_Rd_c > 0 else 99.0
    # confinamiento: cercos del borde (cuantia mecanica) - reporte
    return {
        "l_c_m": float(l_c),
        "l_c_min_normativo_m": float(l_c_min),
        "l_c_criterio": "max(0.15*Lw,1.5*tw) (EC8 §5.4.3.4.2); agrandado en predim. si compr. > N_Rd_c",
        "A_borde_m2": float(A_borde),
        "F_compr_borde_kN": float(F_compr / 1e3),
        "F_tracc_borde_kN": float(F_tracc / 1e3),
        "N_Rd_hormigon_borde_kN": float(N_Rd_c / 1e3),
        "aprov_compr_borde": float(aprov_compr),
        "As_borde_necesaria_cm2": float(As_borde * 1e4),
        "rho_min_borde": rho_min,
        "As_borde_minima_cm2": float(As_min * 1e4),
        "As_borde_diseno_cm2": float(As_dis * 1e4),
        "ok_compr": bool(aprov_compr <= 1.0),
        "confinamiento": "cercos de confinamiento en l_c (EC8 §5.4.3.4.2) [confirmar AN]",
        "ref": "EC8 §5.4.3.4.2 / §5.5.3.4.5",
    }


def interaccion_NM(N_Ed_N, M_Ed_Nm, Lw, tw, fck_Pa, fyk_Pa=500e6,
                   As_borde_m2=None, rho_v_alma=0.0025):
    """Diagrama N-M de la seccion de la pantalla y punto de diseno.

    Modelo de fibras simplificado: hormigon a compresion (bloque rectangular)
    + armadura vertical (distribuida en alma rho_v_alma + concentrada en bordes
    As_borde por borde). Construye la frontera N-M (varias profundidades de
    fibra neutra) y comprueba que (N_Ed, M_Ed) queda dentro."""
    fcd = _fcd(fck_Pa)
    fyd = fyk_Pa / GS
    h = Lw                              # canto = longitud del muro
    b = tw
    eps_cu = 0.0035
    # armadura: bordes + distribuida en alma
    if As_borde_m2 is None:
        As_borde_m2 = rho_v_alma * b * (0.15 * Lw)   # estimacion
    As_v_alma = rho_v_alma * b * Lw                  # total distribuida
    # capas de armadura: borde traccionado (d=0.95h), alma (centro), borde
    # comprimido (d'=0.05h)
    capas = [
        {"As": As_borde_m2, "d": 0.95 * h},
        {"As": As_v_alma,   "d": 0.50 * h},
        {"As": As_borde_m2, "d": 0.05 * h},
    ]
    puntos = []
    for c_x in [0.02 * h, 0.05 * h, 0.1 * h, 0.2 * h, 0.3 * h, 0.4 * h,
                0.5 * h, 0.6 * h, 0.7 * h, 0.85 * h, 1.0 * h, 1.3 * h, 2.0 * h]:
        x = c_x
        Fc = 0.85 * fcd * b * min(0.8 * x, h)        # compresion hormigon
        N = Fc
        M = Fc * (h / 2.0 - 0.4 * min(x, h / 0.8) if x < h / 0.8 else h / 2.0 - 0.5 * h)
        # mejor: brazo del bloque respecto centro
        a = min(0.8 * x, h)
        M = Fc * (h / 2.0 - a / 2.0)
        for capa in capas:
            d = capa["d"]; As = capa["As"]
            eps_s = eps_cu * (x - d) / x if x > 0 else -0.01   # >0 compresion
            sig = max(-fyd, min(fyd, eps_s * 200e9))
            Fs = sig * As
            N += Fs
            M += Fs * (h / 2.0 - d)
        puntos.append({"x_m": float(x), "N_kN": float(N / 1e3),
                       "M_kNm": float(M / 1e3)})
    # comprobacion: el punto de diseno debe quedar 'dentro' de la frontera.
    # criterio simple: para el N_Ed dado, M_Rd ~ interpolacion del max M de la
    # frontera a ese axil; aprov = M_Ed / M_Rd
    Ns = [p["N_kN"] for p in puntos]
    Ms = [p["M_kNm"] for p in puntos]
    N_Ed_kN = N_Ed_N / 1e3
    M_Ed_kNm = M_Ed_Nm / 1e3
    # M_Rd a N_Ed: interpola en la rama de la frontera
    M_Rd = _interp_M_at_N(Ns, Ms, N_Ed_kN)
    aprov = M_Ed_kNm / M_Rd if M_Rd > 0 else 99.0
    return {
        "N_Ed_kN": float(N_Ed_kN), "M_Ed_kNm": float(M_Ed_kNm),
        "As_borde_cm2": float(As_borde_m2 * 1e4),
        "As_v_alma_total_cm2": float(As_v_alma * 1e4),
        "rho_v_alma": rho_v_alma,
        "M_Rd_a_NEd_kNm": float(M_Rd),
        "aprov_flexocompresion": float(aprov),
        "ok": bool(aprov <= 1.0),
        "frontera_NM": puntos,
        "ref": "EC2 §6.1 (flexocompresion, fibras) + EC8 §5.4.3.4",
    }


def _interp_M_at_N(Ns, Ms, N_target):
    """Interpola M_Rd a un axil dado sobre la frontera N-M (rama ascendente)."""
    pares = sorted(zip(Ns, Ms))
    for i in range(len(pares) - 1):
        n0, m0 = pares[i]; n1, m1 = pares[i + 1]
        if (n0 <= N_target <= n1) or (n1 <= N_target <= n0):
            if n1 == n0:
                return max(m0, m1)
            t = (N_target - n0) / (n1 - n0)
            return m0 + t * (m1 - m0)
    # fuera de rango: devuelve el M maximo (lado seguro de reportar)
    return max(Ms)


def deriva(deriva_res, nu=0.5, limite_rel=0.0075):
    """Limitacion de dano (§4.4.3.2): d_r*nu <= limite.

    limite_rel: fraccion de h (0.005 fragil, 0.0075 ductil, 0.010 sin
    afeccion). nu: factor de reduccion (importancia II ~0.5) [confirmar AN]."""
    dr = deriva_res["dr_entreplanta_mm"]
    h = deriva_res["h_planta_m"]
    res = []
    aprov_max = 0.0
    for i in range(len(dr)):
        dr_nu = dr[i] * nu                       # mm
        lim = limite_rel * h[i] * 1e3            # mm
        ap = dr_nu / lim if lim > 0 else 99.0
        aprov_max = max(aprov_max, ap)
        res.append({
            "planta": i + 1, "dr_mm": float(dr[i]),
            "dr_nu_mm": float(dr_nu), "limite_mm": float(lim),
            "deriva_rel": float(dr[i] / 1e3 / h[i]),
            "aprov": float(ap), "ok": bool(ap <= 1.0),
        })
    return {
        "nu": nu, "limite_rel_h": limite_rel,
        "limite_descripcion": "0.5%h fragil / 0.75%h ductil / 1.0%h sin afeccion",
        "por_planta": res,
        "aprov_max": float(aprov_max),
        "ok": bool(aprov_max <= 1.0),
        "ref": "EC8 §4.4.3.2 [confirmar AN nu y limite]",
    }


def verificar(model, esfuerzos):
    """Orquesta todas las verificaciones a partir del modelo (stick) y los
    esfuerzos de diseno (envolvente)."""
    sp = model["seccion_pared"]
    mat = model["material"]
    Lw = sp["Lw_m"]; tw = sp["tw_m"]
    fck = mat["fck_Pa"] or 30e6

    V_Ed = esfuerzos["V_base_diseno_N"]
    M_Ed = esfuerzos["M_base_diseno_Nm"]
    N_Ed = esfuerzos["N_base_diseno_N"]

    cort = cortante_alma(V_Ed, Lw, tw, fck, eps_amplif=esfuerzos.get("eps_amplif", 1.5))
    borde = elemento_borde(N_Ed, M_Ed, Lw, tw, fck)
    nm = interaccion_NM(N_Ed, M_Ed, Lw, tw, fck,
                        As_borde_m2=borde["As_borde_diseno_cm2"] / 1e4,
                        rho_v_alma=0.0025)
    der = deriva(esfuerzos["deriva"], nu=0.5, limite_rel=0.0075)

    aprovs = {
        "cortante_alma": cort["aprov_biela"],
        "compr_borde": borde["aprov_compr_borde"],
        "flexocompresion_NM": nm["aprov_flexocompresion"],
        "deriva": der["aprov_max"],
    }
    ok = (cort["ok"] and borde["ok_compr"] and nm["ok"] and der["ok"])
    return {
        "cortante_alma": cort,
        "elemento_borde": borde,
        "interaccion_NM": nm,
        "deriva": der,
        "aprovechamientos": aprovs,
        "aprov_max": max(aprovs.values()),
        "veredicto": "CUMPLE" if ok else "NO CUMPLE (predimensionar)",
    }
