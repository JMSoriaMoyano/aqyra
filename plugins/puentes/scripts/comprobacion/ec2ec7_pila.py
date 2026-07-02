"""
Comprobacion EC2 (fuste) + EC7 (cimentacion, via router) de una PILA de puente.

 - FUSTE (EC2 flexo-compresion): M-N de seccion rectangular con armadura SIMETRICA
   (As/2 por cara). Momento amplificado por 2.o ORDEN APROXIMADO
   delta = 1/(1 - N_Ed/N_cr), N_cr = pi^2 EI/Lcr^2, Lcr = beta*H (mensula beta~2).
   Cortante por BIELAS (V_Rd,max) + dimensionado de cercos.
 - CIMENTACION (EC7): se delega en `cimentacion_router` (zapata/pilotes/encepado)
   con la reaccion REAL de base de calculo (N, M amplificado, H).

2.o orden: amplificacion aproximada AHORA (P-Delta riguroso/pandeo -> FEM-3,
decision abierta nº3). [confirmar AN]: Lcr/beta, armadura, modelo M-N.
SI (N, m, Pa). Predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import math
import cimentacion_router as cr

FYD = 500e6 / 1.15
GC = 1.5


def amplificacion_2orden(N_Ed, EI, H, beta=2.0):
    """delta = 1/(1 - N_Ed/N_cr), N_cr = pi^2 EI/(beta H)^2. Mensula beta~2."""
    Lcr = beta * H
    N_cr = math.pi ** 2 * EI / Lcr ** 2
    if N_cr <= 0 or N_Ed >= N_cr:
        return 9.99, N_cr
    return 1.0 / (1.0 - N_Ed / N_cr), N_cr


def M_Rd_rect_simetrico(N_Ed, As_total, b, h, d, fck):
    """M_Rd de seccion rectangular b x h con armadura simetrica (As_total/2 por cara,
    a d y h-d), al nivel de axil N_Ed (compresion +). Bloque rectangular 0.8x; se
    asume plastificacion de ambas capas (predim, conservador). Devuelve M_Rd (N*m)."""
    fcd = fck / GC
    # equilibrio axil: N_Ed = 0.8*x*b*fcd  (las dos capas simetricas se cancelan)
    x = N_Ed / (0.8 * b * fcd) if (b * fcd) else 0.0
    x = max(min(x, h), 1e-6)
    Fc = 0.8 * x * b * fcd
    # momento respecto al centro de la seccion
    M_c = Fc * (h / 2.0 - 0.4 * x)
    M_s = As_total * FYD * (d - h / 2.0)        # contribucion de la armadura simetrica
    return max(M_c + M_s, 0.0)


def comprobar(p, esf):
    """esf = {'N_base','M_base','V_base'} de CALCULO (N, N*m, N) en la base del fuste.
    p define pila_sec{b,h,d,Iy}, material{E,fck}, As_pila_m2, beta_pila, cimentacion."""
    mat = p["material"]; fck = mat["fck"]; E = mat["E"]
    sec = p["pila_sec"]; b = sec.get("b", 1.0); h = sec.get("h", 1.0)
    d = sec.get("d", 0.9 * h); Ipila = sec["Iy"]
    beta = p.get("beta_pila", 2.0); H = float(p["H"])
    N_Ed = abs(esf["N_base"]); M_Ed = abs(esf["M_base"]); V_Ed = abs(esf["V_base"])

    # --- 2.o orden ---
    delta, N_cr = amplificacion_2orden(N_Ed, E * Ipila, H, beta)
    M_2 = delta * M_Ed

    # --- FUSTE flexo-compresion (M-N) ---
    As = p.get("As_pila_m2", 0.0)
    M_Rd = M_Rd_rect_simetrico(N_Ed, As, b, h, d, fck)
    aprov_flex = M_2 / M_Rd if M_Rd else 9.99
    # capacidad a compresion pura (squash) como cota
    fcd = fck / GC
    N_Rd_max = 0.85 * fcd * b * h + As * FYD
    aprov_N = N_Ed / N_Rd_max if N_Rd_max else 9.99
    cflex = {"nombre": "fuste_flexocompresion", "N_Ed_kN": N_Ed / 1e3, "M_Ed_kNm": M_2 / 1e3,
             "M_Rd_kNm": M_Rd / 1e3, "N_Rd_max_kN": N_Rd_max / 1e3,
             "aprov": max(aprov_flex, aprov_N), "delta_2orden": delta, "N_cr_kN": N_cr / 1e3,
             "cumple": bool(M_2 <= M_Rd * (1 + 1e-6) and N_Ed <= N_Rd_max * (1 + 1e-6))}

    # --- cortante del fuste por BIELAS (V_Rd,max) + cercos ---
    z = 0.9 * d; cot = 2.5
    nu1 = 0.6 * (1 - (fck / 1e6) / 250.0)
    V_Rd_max = b * z * nu1 * fcd / (cot + 1.0 / cot)
    Asw_s = V_Ed / (z * FYD * cot)
    ccort = {"nombre": "fuste_cortante_biela", "V_Ed_kN": V_Ed / 1e3, "V_Rd_max_kN": V_Rd_max / 1e3,
             "aprov": V_Ed / V_Rd_max if V_Rd_max else 9.99, "Asw_s_cm2_m": Asw_s * 1e4,
             "cumple": bool(V_Ed <= V_Rd_max * (1 + 1e-6))}

    # --- CIMENTACION (EC7) via router con la reaccion real amplificada ---
    cim = cr.comprobar(p["cimentacion"], N_Ed, M_2, V_Ed, fck=fck)

    checks = [cflex, ccort]
    geo_ok = cim["ok"]
    est_ok = all(c["cumple"] for c in checks)
    aprov_max = max([c["aprov"] for c in checks] + [cim.get("aprov", 0.0)])
    veredicto = "CUMPLE" if (geo_ok and est_ok) else "NO CUMPLE"
    return {"checks": checks, "cimentacion": cim, "delta_2orden": delta,
            "aprovechamiento_max": aprov_max, "veredicto": veredicto,
            "elementos_chk": [
                {"nombre": "PILA_fuste", "N_Ed_kN": N_Ed / 1e3, "M_Ed_kNm": M_2 / 1e3,
                 "M_Rd_kNm": M_Rd / 1e3, "aprov_max": max(cflex["aprov"], ccort["aprov"]),
                 "veredicto": "CUMPLE" if est_ok else "NO CUMPLE", "delta_2orden": delta},
                {"nombre": "CIMENTACION_%s" % cim["tipo"], "aprov_max": cim.get("aprov", 0.0),
                 "veredicto": cim["veredicto"]}]}
