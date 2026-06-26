"""
Comprobaciones EC2 adicionales de la losa:
  - PUNZONAMIENTO (EN 1992-1-1 §6.4)
  - FISURACION    (EN 1992-1-1 §7.3, calculo directo de wk)

Unidades de entrada en SI (N, m, Pa). Las formulas que requieren MPa/mm se
convierten internamente.
"""
import math

GC = 1.50
ES = 200e9  # modulo del acero


# ---------------------------------------------------------------------------
# PUNZONAMIENTO  (EC2 6.4)
# ---------------------------------------------------------------------------
def punzonamiento(V_Ed, c1, c2, d, fck, rho_l, posicion="corner", beta=None):
    """
    V_Ed : fuerza de punzonamiento (N)  -- reaccion del pilar
    c1,c2: dimensiones del pilar (m)
    d    : canto util medio de la losa (m)
    fck  : resistencia del hormigon (Pa)
    rho_l: cuantia geometrica media de traccion (-)
    posicion: 'interior' | 'edge' | 'corner'
    """
    d_mm = d * 1e3
    fck_MPa = fck / 1e6
    rho_l = min(rho_l, 0.02)

    # factor de posicion (EC2 6.4.3, valores recomendados)
    beta_def = {"interior": 1.15, "edge": 1.40, "corner": 1.50}
    if beta is None:
        beta = beta_def[posicion]

    # perimetros de control (m): basico u1 (a 2d) y del pilar u0
    if posicion == "interior":
        u1 = 2 * (c1 + c2) + 4 * math.pi * d
        u0 = 2 * (c1 + c2)
    elif posicion == "edge":
        u1 = 2 * c1 + c2 + 2 * math.pi * d
        u0 = 2 * c1 + c2
    else:  # corner
        u1 = c1 + c2 + math.pi * d
        u0 = c1 + c2

    # resistencia sin armadura de punzonamiento (MPa)
    k = min(1 + math.sqrt(200 / d_mm), 2.0)
    C_Rd_c = 0.18 / GC
    v_Rd_c_MPa = max(C_Rd_c * k * (100 * rho_l * fck_MPa) ** (1 / 3),
                     0.035 * k ** 1.5 * fck_MPa ** 0.5)
    v_Rd_c = v_Rd_c_MPa * 1e6  # Pa

    # tension de calculo en el perimetro de control u1
    v_Ed = beta * V_Ed / (u1 * d)            # Pa
    # compresion maxima en el perimetro del pilar u0
    nu = 0.6 * (1 - fck_MPa / 250)
    v_Rd_max = 0.5 * nu * (fck / GC)         # Pa
    v_Ed_0 = beta * V_Ed / (u0 * d)

    ok_c = v_Ed <= v_Rd_c
    ok_max = v_Ed_0 <= v_Rd_max
    return {
        "V_Ed_kN": V_Ed / 1e3, "posicion": posicion, "beta": beta,
        "u0_m": u0, "u1_m": u1, "d_mm": d_mm, "k": k, "rho_l": rho_l,
        "vEd_u1_MPa": v_Ed / 1e6, "vRdc_MPa": v_Rd_c_MPa, "u_vRdc": v_Ed / v_Rd_c,
        "vEd_u0_MPa": v_Ed_0 / 1e6, "vRdmax_MPa": v_Rd_max / 1e6, "u_vRdmax": v_Ed_0 / v_Rd_max,
        "ok_vRdc": bool(ok_c), "ok_vRdmax": bool(ok_max),
        "requiere_armadura": bool(not ok_c),
        "ok": bool(ok_c and ok_max),
    }


# ---------------------------------------------------------------------------
# FISURACION  (EC2 7.3.4, calculo directo de wk)
# ---------------------------------------------------------------------------
def fisuracion(M_qp, As, d, h, c, phi, fctm, Ecm, b=1.0,
               wmax=0.3e-3, kt=0.4, k1=0.8, k2=0.5):
    """
    M_qp : momento cuasipermanente (N·m/m)
    As   : armadura dispuesta (m2/m)
    d,h  : canto util y total (m) ; c: recubrimiento (m) ; phi: diametro (m)
    """
    alpha_e = ES / Ecm
    z = 0.9 * d
    sigma_s = M_qp / (As * z)                      # Pa

    # area eficaz a traccion (EC2 7.3.2)
    hc_ef = min(2.5 * (h - d), h / 2)
    rho_p_eff = As / (b * hc_ef)

    # deformacion media (EC2 7.9)
    term = (sigma_s - kt * (fctm / rho_p_eff) * (1 + alpha_e * rho_p_eff)) / ES
    eps = max(term, 0.6 * sigma_s / ES)

    # separacion maxima de fisuras (EC2 7.11)
    k3, k4 = 3.4, 0.425
    sr_max = k3 * c + k1 * k2 * k4 * phi / rho_p_eff   # m
    wk = sr_max * eps                                   # m
    return {
        "M_qp_kNm_m": M_qp / 1e3, "sigma_s_MPa": sigma_s / 1e6,
        "rho_p_eff": rho_p_eff, "hc_ef_mm": hc_ef * 1e3,
        "eps_sm_cm": eps, "sr_max_mm": sr_max * 1e3,
        "wk_mm": wk * 1e3, "wmax_mm": wmax * 1e3,
        "u": wk / wmax, "ok": bool(wk <= wmax),
    }


def _perimetros(posicion, c1, c2, d):
    if posicion == "interior":
        return 2 * (c1 + c2) + 4 * math.pi * d, 2 * (c1 + c2)
    if posicion == "edge":
        return 2 * c1 + c2 + 2 * math.pi * d, 2 * c1 + c2
    return c1 + c2 + math.pi * d, c1 + c2  # corner


def _vRdc(d, fck, rho_l):
    d_mm = d * 1e3; fck_MPa = fck / 1e6; rho_l = min(rho_l, 0.02)
    k = min(1 + math.sqrt(200 / d_mm), 2.0)
    v = max((0.18 / GC) * k * (100 * rho_l * fck_MPa) ** (1 / 3),
            0.035 * k ** 1.5 * fck_MPa ** 0.5)
    return v * 1e6, k


def dimensionar_punzonamiento(V_Ed, c1, c2, h, cover, phi, fck, As_l,
                              posicion="interior", fywk=500e6, beta=None):
    """
    Dimensiona TRES soluciones cuando el punzonamiento no cumple:
      1) canto minimo de losa (sin armadura),
      2) armadura de punzonamiento (EC2 6.4.5) manteniendo el canto,
      3) abaco/capitel (ampliacion del soporte).
    As_l: armadura de flexion media dispuesta (m2/m), para la cuantia rho_l.
    """
    beta_def = {"interior": 1.15, "edge": 1.40, "corner": 1.50}
    if beta is None:
        beta = beta_def[posicion]

    def d_de(h_):
        return h_ - cover - phi  # canto util medio (dos capas)

    d0 = d_de(h)
    rho0 = min(As_l / d0, 0.02)
    vRdc0, _ = _vRdc(d0, fck, rho0)
    u1_0, u0_0 = _perimetros(posicion, c1, c2, d0)
    vEd0 = beta * V_Ed / (u1_0 * d0)

    # --- 1) canto minimo ---
    h_min = h
    for _ in range(200):
        d = d_de(h_min)
        rho = min(As_l / d, 0.02)
        vRdc, _ = _vRdc(d, fck, rho)
        u1, _ = _perimetros(posicion, c1, c2, d)
        if beta * V_Ed / (u1 * d) <= vRdc:
            break
        h_min += 0.01
    canto_min = {"h_min_mm": round(h_min * 1e3), "incremento_mm": round((h_min - h) * 1e3)}

    # --- 2) armadura de punzonamiento (EC2 6.4.5) ---
    fywd = fywk / 1.15
    d_mm = d0 * 1e3
    fywd_ef = min(250e6 + 0.25e6 * d_mm, fywd)   # Pa
    # Asw/sr por anillo (m2/m) a partir de vEd = 0.75 vRdc + 1.5 (Asw/sr) fywd_ef /u1
    asw_sr = max((vEd0 - 0.75 * vRdc0) * u1_0 / (1.5 * fywd_ef), 0.0)  # m2/m
    # perimetro exterior donde ya no se necesita armadura
    u_out = beta * V_Ed / (vRdc0 * d0)
    # compresion en biela (limite superior)
    nu = 0.6 * (1 - fck / 1e6 / 250)
    vRdmax = 0.5 * nu * (fck / GC)
    vEd_u0 = beta * V_Ed / (u0_0 * d0)
    armadura = {
        "asw_sr_mm2_m": asw_sr * 1e6 / 1e3,   # mm2 por mm radial -> mm2/m
        "asw_sr_cm2_m": asw_sr * 1e4,
        "u_out_m": u_out, "fywd_ef_MPa": fywd_ef / 1e6,
        "viable": bool(vEd_u0 <= vRdmax),
        "nota": "armadura viable solo si vEd(u0) <= vRd,max",
    }

    # --- 3) abaco/capitel (ampliacion del soporte cuadrado c') ---
    u1_req = beta * V_Ed / (vRdc0 * d0)
    if posicion == "interior":
        c_cap = (u1_req - 4 * math.pi * d0) / 4
    elif posicion == "edge":
        c_cap = (u1_req - 2 * math.pi * d0 - c2) / 2
    else:
        c_cap = (u1_req - math.pi * d0) / 2
    capitel = {"lado_capitel_mm": round(max(c_cap, c1) * 1e3),
               "ampliacion_mm": round(max(c_cap - c1, 0) * 1e3)}

    return {
        "V_Ed_kN": V_Ed / 1e3, "posicion": posicion, "beta": beta,
        "h_actual_mm": round(h * 1e3), "d_actual_mm": round(d0 * 1e3),
        "u_actual_vRdc": vEd0 / vRdc0,
        "canto_minimo": canto_min,
        "armadura": armadura,
        "capitel": capitel,
    }


if __name__ == "__main__":
    # prueba con valores del demo (losa C30/37, pilar HEB200, esquina)
    fck = 30e6; fctm = 2.9e6; Ecm = 32.84e9
    d = (0.169 + 0.157) / 2
    # cuantia con As ~ 5.24 cm2/m (y) y 3.93 (x)
    rho = math.sqrt((3.93e-4 / 0.169) * (5.24e-4 / 0.157))
    p = punzonamiento(93e3, 0.20, 0.20, d, fck, rho, "corner")
    print("PUNZONAMIENTO:", {k: (round(v, 3) if isinstance(v, float) else v) for k, v in p.items()})
    fi = fisuracion(18e3, 5.24e-4, 0.157, 0.20, 0.025, 0.012, fctm, Ecm)
    print("FISURACION:", {k: (round(v, 4) if isinstance(v, float) else v) for k, v in fi.items()})
