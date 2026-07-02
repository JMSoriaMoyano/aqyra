"""
Comprobacion EC2 de una LOSA POSTESADA (EN 1992-1-1/-2, AN Espana).

REUTILIZA (PYTHONPATH a motor-calculo/scripts/pretensado):
 - `balance_2d`              -> balance de cargas 2D, sigma_cp por direccion, V_p.
 - `verificacion_losa_postesada` -> `_fib`, `M_Rd_franja`, `As_pasiva_para`.

Metodo de BALANCE DE CARGAS (EC2 5.10): el postesado se trata como (a) carga
equivalente vertical (ya aplicada en el FEM) y (b) precompresion axil sigma_cp=P/t.
La tension por franja es  sigma = sigma_cp +/- M_net * c / I  (M_net = momento de
la carga NO equilibrada, sagging positivo tracciona el fondo), via `_fib`.

Comprobaciones por franja de VANO (por metro de ancho), sobre las envolventes de
esfuerzo de placa Mx del FEM (motor-fem, objetivo `esfuerzo_lamina`):
 - TENSIONES EN VACIO (transferencia): sigma_cp(P0) + M_net_transfer.
 - TENSIONES EN SERVICIO (ELS car): sigma_cp(Pinf) + M_net_serv.
 - DESCOMPRESION (ELS cuasiperm): traccion de fondo <= 0.
 - FLEXION ELU: M_Rd (bloque rectangular, Ap/m + pasiva) vs M_Ed externo factorizado.
 - PUNZONAMIENTO (EC2 6.4): SOLO con apoyos PUNTUALES (pilares); con estribos
   lineales -> N/A. Descuento del postesado via `balance_2d.Vp_perimetro_control`.

Perdidas del postesado: SIMPLIFICADAS por porcentaje (decision nº5, PT 7.1).
[confirmar AN]: limites de tension, fck(t), reparto biaxial, k1 de 6.4.4.
SI (N, m, Pa). Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import math
import balance_2d as b2d
import verificacion_losa_postesada as vlp


def _chk(nombre, valor, limite, modo="<="):
    if modo == "<=":
        ap = abs(valor) / abs(limite) if limite else 0.0
        ok = abs(valor) <= abs(limite) * (1 + 1e-6)
    else:
        ap = abs(limite) / abs(valor) if valor else 0.0
        ok = abs(valor) >= abs(limite) * (1 - 1e-6)
    return {"nombre": nombre, "valor": valor, "limite": limite, "aprov": ap, "cumple": bool(ok)}


def comprobar(tablero, postesado, esfuerzos, punz=None):
    """tablero: {'t','L','B','material'{fck,fctm?},'fck_transferencia'?}.
    postesado: {'P0_x_N_m','P0_y_N_m','a_x','a_y','Ap_x_m2_m','fpk','perdidas_pct',
                'd_p','d_s','As_pas_x_m2_m'}.
    esfuerzos (N*m/m, SAGGING POSITIVO tracciona el fondo):
        {'M_net_transfer','M_net_serv','M_net_cp','M_Ed_ELU','w_equilibrar_N_m2'}.
    punz (opc): {'pilar':(cx,cy),'V_Ed_N','d','posicion','rho_l'}."""
    t = tablero['t']; fck = tablero['material']['fck']
    fctm = tablero['material'].get('fctm', 0.30 * (fck / 1e6) ** (2 / 3) * 1e6)
    fck_t = tablero.get('fck_transferencia', 0.8 * fck)
    c = t / 2.0; I = t ** 3 / 12.0; fcd = fck / 1.5

    P0x = postesado['P0_x_N_m']; P0y = postesado.get('P0_y_N_m', 0.0)
    perd = postesado.get('perdidas_pct', 18.0) / 100.0
    Pinfx = P0x * (1 - perd); Pinfy = P0y * (1 - perd)
    a_x = postesado['a_x']; a_y = postesado.get('a_y', a_x)
    L = tablero['L']; B = tablero['B']
    w_eq = esfuerzos.get('w_equilibrar_N_m2', 0.0) or 1.0
    bal = b2d.balance_2d(Pinfx, Pinfy, L, B, a_x, a_y, w_eq, t)
    sigma_cp0 = -P0x / t; sigma_cp = -Pinfx / t

    checks = []
    # transferencia (P0 + g1, no equilibrado)
    s_sup0, s_inf0 = vlp._fib(sigma_cp0, esfuerzos['M_net_transfer'], c, I)
    checks.append(_chk("transfer_comp_inf", min(s_inf0, 0.0), -0.6 * fck_t))
    checks.append(_chk("transfer_tracc_sup", max(s_sup0, 0.0), fctm))
    # servicio ELS caracteristica (Pinf + perm + LM1)
    s_sup, s_inf = vlp._fib(sigma_cp, esfuerzos['M_net_serv'], c, I)
    checks.append(_chk("servicio_comp_sup", min(s_sup, 0.0), -0.6 * fck))
    checks.append(_chk("servicio_tracc_inf", max(s_inf, 0.0), fctm))
    # descompresion (cuasiperm)
    _, s_inf_cp = vlp._fib(sigma_cp, esfuerzos['M_net_cp'], c, I)
    checks.append(_chk("descompresion_inf_cp", max(s_inf_cp, 0.0), 0.0))
    # flexion ELU (Ap/m activa + pasiva)
    M_Ed = esfuerzos['M_Ed_ELU']
    fpd = postesado['fpk'] / 1.15; fyd = 500e6 / 1.15
    d_p = postesado.get('d_p', 0.9 * t); d_s = postesado.get('d_s', 0.9 * t)
    Ap_x = postesado['Ap_x_m2_m']; As_pas = postesado.get('As_pas_x_m2_m', 0.0)
    rd = vlp.M_Rd_franja(d_p, fpd, Ap_x, As_pas, d_s, fyd, fcd, t)
    M_Rd = rd["M_Rd_kNm_m"] * 1e3
    chk_flex = _chk("flexion_ELU_vano", M_Ed, M_Rd); checks.append(chk_flex)
    As_req = 0.0
    if not chk_flex["cumple"]:
        As_req, rd = vlp.As_pasiva_para(M_Ed, d_p, fpd, Ap_x, d_s, fyd, fcd, t, As_pas)
        M_Rd = rd["M_Rd_kNm_m"] * 1e3
        checks[-1] = _chk("flexion_ELU_vano", M_Ed, M_Rd)

    punz_res = None
    if punz:
        cx, cy = punz['pilar']; d = punz['d']; pos = punz.get('posicion', 'interior')
        vp = b2d.Vp_perimetro_control(bal['w_px_N_m2'], bal['w_py_N_m2'], (cx, cy, d), pos)
        V_Ed = punz['V_Ed_N'] - vp['V_p_N']
        u1 = 2 * (cx + cy) + 2 * math.pi * 2 * d
        v_Ed = V_Ed / (u1 * d)
        k = min(1 + (0.2 / d) ** 0.5, 2.0); rho_l = punz.get('rho_l', 0.005)
        v_min = 0.035 * k ** 1.5 * (fck / 1e6) ** 0.5 * 1e6
        sigma_cp_pun = min(abs(bal['sigma_cp_Pa']), 0.2 * fcd)
        v_Rdc = max(0.18 / 1.5 * k * (100 * rho_l * fck / 1e6) ** (1 / 3) * 1e6, v_min) + 0.10 * sigma_cp_pun
        checks.append(_chk("punzonamiento", v_Ed, v_Rdc))
        punz_res = {"V_Ed_neto_N": V_Ed, "V_p_N": vp["V_p_N"], "v_Ed_Pa": v_Ed, "v_Rdc_Pa": v_Rdc, "u1_m": u1}

    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    aprov_max = max(c["aprov"] for c in checks)
    return {"checks": checks, "veredicto": veredicto, "aprovechamiento_max": aprov_max,
            "M_Rd_Nm_m": M_Rd, "M_Ed_Nm_m": M_Ed, "As_pas_req_cm2_m": As_req * 1e4,
            "balance": bal, "punzonamiento": punz_res,
            "tensiones": {"transfer_sup_Pa": s_sup0, "transfer_inf_Pa": s_inf0,
                          "servicio_sup_Pa": s_sup, "servicio_inf_Pa": s_inf,
                          "descompresion_inf_cp_Pa": s_inf_cp}}
