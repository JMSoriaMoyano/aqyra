"""
Comprobacion EC2 de un tablero VIGA-CAJON postesado (EN 1992-1-1/-2, AN Espana).

Cajon idealizado por LAMINA PURA (motor-fem FEM-2). Metodo de BALANCE DE CARGAS
(EC2 5.10): el postesado = (a) carga equivalente w_p (ya en el FEM, caso P) +
(b) precompresion axil sigma_cp = -P/A (analitica). Las tensiones de fibra del
ala SE TOMAN DEL FEM (Nx de panel / t -> incluye SHEAR LAG nativamente):

   sigma_fibra = sigma_cp(P) + Nx_panel / t        (traccion positiva)

Comprobaciones (predimensionado), por FASE:
 - FASE CONSTRUCCION (en vacio, transferencia): P0 + peso propio g1.
     comp_inf <= 0.6 fck(t) ; tracc_sup <= fctm.
 - FASE SERVICIO (ELS caracteristica): Pinf + g1 + g2 + LM1 + diferidos (perdidas).
     comp_sup <= 0.6 fck ; tracc_inf <= fctm.
 - DESCOMPRESION (ELS cuasiperm): tracc_inf <= 0.
 - FLEXION ELU: M_Rd de la seccion cajon (bloque en losa superior) vs M_Ed.
 - CORTANTE+TORSION (EC2 6.3): alma con flujo de Bredt; interaccion
     V_Ed/V_Rd,max + T_Ed/T_Rd,max <= 1.
 - SHEAR LAG: ancho eficaz del ala desde la distribucion de Nx del FEM.

Diferidos (fluencia/retraccion/relajacion): SIMPLIFICADOS por % de perdidas
(decision PT 7.4). [confirmar AN]: limites de tension, fck(t), theta de bielas,
nu1, alpha_cw, ancho eficaz. SI (N, m, Pa). Predim.; revisar y firmar (ICCP).
"""
from __future__ import annotations
import math


def _chk(nombre, valor, limite, modo="<="):
    if modo == "<=":
        ap = abs(valor) / abs(limite) if limite else 0.0
        ok = abs(valor) <= abs(limite) * (1 + 1e-6)
    else:
        ap = abs(limite) / abs(valor) if valor else 0.0
        ok = abs(valor) >= abs(limite) * (1 - 1e-6)
    return {"nombre": nombre, "valor": valor, "limite": limite, "aprov": ap, "cumple": bool(ok)}


def comprobar(cajon, postesado, esfuerzos, props):
    """cajon: {'material'{fck,fctm?},'fck_transferencia'?,'bs','h','t_top','t_web'}.
    postesado: {'P0_N','perdidas_pct','e_p','Ap_m2','fpk','As_pas_m2'?,'d_p'?}.
    esfuerzos (del FEM/recuperacion, traccion positiva, Pa salvo M/V/T):
        {'sig_top_transfer','sig_bot_transfer',           # con sigma_fem(g1+P0wp)
         'sig_top_serv','sig_bot_serv','sig_bot_cp',        # con sigma_fem(serv)
         'M_Ed_ELU_Nm','V_Ed_N','T_Ed_Nm','Nx_ala_borde','Nx_ala_centro'}.
    props: salida de cajon._seccion_props (A, Iy, c_sup, c_inf, Am_bredt, J_bredt)."""
    fck = cajon['material']['fck']
    fctm = cajon['material'].get('fctm', 0.30 * (fck / 1e6) ** (2 / 3) * 1e6)
    fck_t = cajon.get('fck_transferencia', 0.8 * fck)
    fcd = fck / 1.5
    A = props['A']; I = props['Iy']; c_sup = props['c_sup']; c_inf = props['c_inf']
    P0 = postesado['P0_N']; perd = postesado.get('perdidas_pct', 18.0) / 100.0
    Pinf = P0 * (1 - perd)
    sig_cp0 = -P0 / A; sig_cp = -Pinf / A

    checks = []
    # --- FASE CONSTRUCCION (transferencia): sigma_cp(P0) + fem(g1 + P0 wp) ---
    s_sup0 = sig_cp0 + esfuerzos['sig_top_transfer']
    s_inf0 = sig_cp0 + esfuerzos['sig_bot_transfer']
    checks.append(_chk("constr_comp_inf", min(s_inf0, 0.0), -0.6 * fck_t))
    checks.append(_chk("constr_tracc_sup", max(s_sup0, 0.0), fctm))
    # --- FASE SERVICIO (ELS car): sigma_cp(Pinf) + fem(serv) ---
    s_sup = sig_cp + esfuerzos['sig_top_serv']
    s_inf = sig_cp + esfuerzos['sig_bot_serv']
    checks.append(_chk("servicio_comp_sup", min(s_sup, 0.0), -0.6 * fck))
    checks.append(_chk("servicio_tracc_inf", max(s_inf, 0.0), fctm))
    # --- DESCOMPRESION (cuasiperm) ---
    s_inf_cp = sig_cp + esfuerzos['sig_bot_cp']
    checks.append(_chk("descompresion_inf_cp", max(s_inf_cp, 0.0), 0.0))

    # --- FLEXION ELU: M_Rd de la seccion cajon ---
    fpd = postesado['fpk'] / 1.15; fyd = 500e6 / 1.15
    Ap = postesado['Ap_m2']; As = postesado.get('As_pas_m2', 0.0)
    h = cajon['h']; d_p = postesado.get('d_p', 0.5 * c_sup + c_inf + 0.9 * (h - c_sup - c_inf) if False else 0.9 * h)
    beff_top = cajon.get('beff_top', cajon['bs'])
    Fs = Ap * fpd + As * fyd
    x = Fs / (0.8 * fcd * beff_top)             # profundidad del bloque (en losa sup)
    z = d_p - 0.4 * x
    M_Rd = Fs * z
    M_Ed = esfuerzos['M_Ed_ELU_Nm']
    checks.append(_chk("flexion_ELU", M_Ed, M_Rd))

    # --- CORTANTE + TORSION (EC2 6.3), bielas a 45deg, dos almas ---
    V_Ed = esfuerzos.get('V_Ed_N', 0.0); T_Ed = esfuerzos.get('T_Ed_Nm', 0.0)
    tw = cajon['t_web']; lw = props['l_alma']; Am = props['Am_bredt']
    z_v = 0.9 * (h - cajon['t_top'] / 2 - cajon['t_bot'] / 2)
    nu1 = 0.6 * (1 - fck / 1e6 / 250.0); alpha_cw = 1.0
    # V_Rd,max (dos almas inclinadas, proyeccion vertical)
    bw_tot = 2 * tw * (z_v / lw if lw else 1.0) * lw / lw  # ~2*tw vertical efficiency
    V_Rdmax = alpha_cw * (2 * tw) * z_v * nu1 * fcd / 2.0     # cot+tan=2 a 45deg
    # T_Rd,max (Bredt): T_Rdmax = 2 nu1 alpha_cw fcd Ak tef sin cos = nu1 fcd Ak tef (45deg)
    tef = tw
    T_Rdmax = nu1 * alpha_cw * fcd * Am * tef
    inter = (abs(V_Ed) / V_Rdmax if V_Rdmax else 0.0) + (abs(T_Ed) / T_Rdmax if T_Rdmax else 0.0)
    checks.append(_chk("cortante_torsion_interaccion", inter, 1.0))
    # tension tangencial combinada en el alma (Bredt + cortante)
    tau_V = abs(V_Ed) / (2 * tw * z_v) if z_v else 0.0
    tau_T = abs(T_Ed) / (2 * Am * tef) if Am else 0.0
    tau_tot = tau_V + tau_T

    # --- SHEAR LAG: ancho eficaz desde Nx del ala (borde junto al alma vs centro) ---
    nb = esfuerzos.get('Nx_ala_borde'); ncn = esfuerzos.get('Nx_ala_centro')
    beff_frac = (ncn / nb) if (nb not in (None, 0)) else 1.0
    beff_frac = max(0.0, min(1.0, abs(beff_frac)))

    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    aprov_max = max(c["aprov"] for c in checks)
    return {"checks": checks, "veredicto": veredicto, "aprovechamiento_max": aprov_max,
            "M_Rd_Nm": M_Rd, "M_Ed_Nm": M_Ed, "x_bloque_m": x, "z_m": z,
            "V_Rdmax_N": V_Rdmax, "T_Rdmax_Nm": T_Rdmax, "interaccion_VT": inter,
            "tau_web_Pa": {"V": tau_V, "T": tau_T, "total": tau_tot},
            "shear_lag_beff_frac": beff_frac,
            "tensiones": {"constr_sup_Pa": s_sup0, "constr_inf_Pa": s_inf0,
                          "servicio_sup_Pa": s_sup, "servicio_inf_Pa": s_inf,
                          "descompresion_inf_cp_Pa": s_inf_cp,
                          "sigma_cp0_Pa": sig_cp0, "sigma_cp_Pa": sig_cp}}
