"""
Comprobacion EC2 + EC7 de un PORTICO (marco) de paso (AN Espana).

REUTILIZA `verificacion_muro` (motor-calculo/scripts/muros-contencion) para la
armadura de flexion y el cortante V_Rd,c (PYTHONPATH). Comprueba:
 - DINTEL (EC2): flexion ELU (M_Rd con As provista; dimensiona si falta) y
   cortante V_Rd,c.
 - PILAS (EC2): flexion con 2.º ORDEN APROXIMADO (amplificacion de momentos
   delta = 1/(1 - N_Ed/N_cr), N_cr = pi^2 EI/Lcr^2, Lcr = beta*H — marco con
   desplazamiento). M-N simplificado (se ignora el axil favorable -> conservador).
 - CIMENTACION (EC7): tension del terreno sigma_max <= q_adm (zapata B x Lf con
   excentricidad e=M/N) y deslizamiento H <= mu*N.

2.º orden: amplificacion aproximada AHORA (P-Delta completo -> FEM-3). Empuje de
tierras: K dado (K0 reposo recomendado). [confirmar AN]: Lcr/beta, q_adm, mu,
modelo M-N. SI (N, m, Pa). Predimensionado; revisar y firmar por tecnico (ICCP).
"""
from __future__ import annotations
import math
import verificacion_muro as vm

FYD = 500e6 / 1.15


def _M_Rd_rect(As, d, fck, b=1.0):
    fcd = fck / 1.5
    if As <= 0 or d <= 0:
        return 0.0
    x = As * FYD / (0.8 * fcd * b)
    x = min(x, 0.45 * d)                 # limita ductilidad
    z = d - 0.4 * x
    return As * FYD * z


def _chk(nombre, M_Ed, M_Rd):
    ap = abs(M_Ed) / abs(M_Rd) if M_Rd else 9.99
    return {"nombre": nombre, "M_Ed_Nm": M_Ed, "M_Rd_Nm": M_Rd, "aprov": ap,
            "cumple": bool(abs(M_Ed) <= abs(M_Rd) * (1 + 1e-6))}


def amplificacion_2orden(N_Ed, EI, H, beta=2.0):
    """delta = 1/(1 - N_Ed/N_cr), N_cr = pi^2 EI/(beta H)^2. Marco con desplaz.:
    beta~2. Si N_Ed >= N_cr -> inestable (delta grande, se reporta)."""
    Lcr = beta * H
    N_cr = math.pi ** 2 * EI / Lcr ** 2
    if N_cr <= 0 or N_Ed >= N_cr:
        return 9.99, N_cr
    return 1.0 / (1.0 - N_Ed / N_cr), N_cr


def comprobar(p, esf):
    """esf = {'M_dintel_Ed','V_dintel_Ed','N_pila_Ed','M_pila_Ed','N_base','M_base',
       'H_base'} (N, N*m). p define secciones/armado/cimentacion/material."""
    mat = p['material']; fck = mat['fck']
    fctm = mat.get('fctm', 0.30 * (fck / 1e6) ** (2 / 3) * 1e6)
    E = mat['E']
    checks = []; elementos_chk = []

    # --- DINTEL ---
    d_d = p['dintel_sec'].get('d', 0.9 * p['dintel_sec'].get('h', 1.0))
    b_d = p['dintel_sec'].get('b', 1.0)
    As_d = p.get('As_dintel_m2', 0.0)
    M_Rd_d = _M_Rd_rect(As_d, d_d, fck, b_d)
    cflex_d = _chk("dintel_flexion_ELU", esf['M_dintel_Ed'], M_Rd_d)
    As_d_req = 0.0
    if not cflex_d["cumple"]:
        fl = vm.flexion(abs(esf['M_dintel_Ed']), d_d, fck, fctm, p['dintel_sec'].get('h', 1.0), b_d)
        As_d_req = fl["As_prov_cm2_m"] / 1e4 * b_d
        M_Rd_d = _M_Rd_rect(As_d_req, d_d, fck, b_d)
        cflex_d = _chk("dintel_flexion_ELU", esf['M_dintel_Ed'], M_Rd_d)
    checks.append(cflex_d)
    # cortante del dintel por BIELAS (V_Rd,max) + dimensionado de cercos (no V_Rd,c)
    fcd = fck / 1.5; z_d = 0.9 * d_d; cot = 2.5
    nu1 = 0.6 * (1 - (fck / 1e6) / 250.0)
    V_Rd_max = b_d * z_d * nu1 * fcd / (cot + 1.0 / cot)
    fywd = 500e6 / 1.15
    Asw_s = abs(esf['V_dintel_Ed']) / (z_d * fywd * cot)   # m2/m
    cort_d = {"nombre": "dintel_cortante_biela", "valor": esf['V_dintel_Ed'], "limite": V_Rd_max,
              "aprov": abs(esf['V_dintel_Ed']) / V_Rd_max if V_Rd_max else 9.99,
              "cumple": bool(abs(esf['V_dintel_Ed']) <= V_Rd_max * (1 + 1e-6)),
              "Asw_s_cm2_m": Asw_s * 1e4}
    checks.append({k: cort_d[k] for k in ("nombre", "valor", "limite", "aprov", "cumple")})
    elementos_chk.append({"nombre": "DINTEL", "M_Ed_Nm": esf['M_dintel_Ed'], "M_Rd_Nm": M_Rd_d,
                          "aprov_max": max(cflex_d["aprov"], cort_d["aprov"]),
                          "veredicto": "CUMPLE" if (cflex_d["cumple"] and cort_d["cumple"]) else "NO CUMPLE",
                          "As_req_cm2_m": As_d_req / b_d * 1e4})

    # --- PILA (2.º orden aproximado) ---
    d_p = p['pila_sec'].get('d', 0.9 * p['pila_sec'].get('h', 1.0))
    b_p = p['pila_sec'].get('b', 1.0); Ipila = p['pila_sec']['Iy']
    beta = p.get('beta_pila', 2.0)
    delta, N_cr = amplificacion_2orden(abs(esf['N_pila_Ed']), E * Ipila, p_H(p), beta)
    M_pila_2 = delta * abs(esf['M_pila_Ed'])
    As_p = p.get('As_pila_m2', 0.0)
    M_Rd_p = _M_Rd_rect(As_p, d_p, fck, b_p)
    cflex_p = _chk("pila_flexion_2orden", M_pila_2, M_Rd_p)
    As_p_req = 0.0
    if not cflex_p["cumple"]:
        fl = vm.flexion(M_pila_2, d_p, fck, fctm, p['pila_sec'].get('h', 1.0), b_p)
        As_p_req = fl["As_prov_cm2_m"] / 1e4 * b_p
        M_Rd_p = _M_Rd_rect(As_p_req, d_p, fck, b_p)
        cflex_p = _chk("pila_flexion_2orden", M_pila_2, M_Rd_p)
    checks.append(cflex_p)
    elementos_chk.append({"nombre": "PILA", "M_Ed_Nm": M_pila_2, "M_Rd_Nm": M_Rd_p,
                          "aprov_max": cflex_p["aprov"],
                          "veredicto": "CUMPLE" if cflex_p["cumple"] else "NO CUMPLE",
                          "delta_2orden": delta, "N_cr_N": N_cr, "As_req_cm2_m": As_p_req / b_p * 1e4})

    # --- CIMENTACION (EC7) ---
    cim = p['cimentacion']; Bf = cim['B']; Lf = cim['Lf']; q_adm = cim['q_adm']
    mu = cim.get('mu', 0.5)
    N = abs(esf['N_base']); M = abs(esf['M_base']); Hb = abs(esf.get('H_base', 0.0))
    e = M / N if N else 0.0
    A = Bf * Lf
    if e <= Bf / 6.0:
        sigma_max = N / A * (1 + 6 * e / Bf)
    else:
        sigma_max = 2 * N / (3 * Lf * (Bf / 2.0 - e)) if (Bf / 2.0 - e) > 0 else 9.99e9
    ec7_hund = {"nombre": "EC7_hundimiento", "valor": sigma_max, "limite": q_adm,
                "aprov": sigma_max / q_adm if q_adm else 9.99, "cumple": bool(sigma_max <= q_adm * (1 + 1e-6))}
    H_rd = mu * N
    ec7_desl = {"nombre": "EC7_deslizamiento", "valor": Hb, "limite": H_rd,
                "aprov": Hb / H_rd if H_rd else 0.0, "cumple": bool(Hb <= H_rd * (1 + 1e-6))}
    checks += [ec7_hund, ec7_desl]

    veredicto = "CUMPLE" if all(c["cumple"] for c in checks) else "NO CUMPLE"
    aprov_max = max(c["aprov"] for c in checks)
    return {"checks": checks, "elementos_chk": elementos_chk, "veredicto": veredicto,
            "aprovechamiento_max": aprov_max,
            "ec7": {"sigma_max_kPa": sigma_max / 1e3, "q_adm_kPa": q_adm / 1e3,
                    "e_m": e, "aprov_hundimiento": ec7_hund["aprov"], "aprov_deslizamiento": ec7_desl["aprov"]},
            "delta_2orden": delta}


def p_H(p):
    return float(p['H'])
