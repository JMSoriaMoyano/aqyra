"""
Enrutado de la CIMENTACION de la pila (PT 7.3). Dado el tipo declarado en el caso
(zapata / pilotes / encepado) y las reacciones REALES de la base de la pila
(N, M, H de calculo), comprueba la cimentacion reutilizando el DIMENSIONADO ya
validado de `motor-calculo-estructural` (EC7/EC2).

Como `motor-calculo` ejecuta esos modulos con PyNite (no disponible en este runtime),
se reutilizan sus FORMULAS PURAS, copiadas byte-fiel y atribuidas (mismo patron que
la copia del solver Darcy en PT 6.3):
 - zapata:  Meyerhof B'=B-2e (EC7 hundimiento) + deslizamiento H<=mu*N  (cimentaciones)
 - pilotes: capacidad_axil Rc,d = Rs/gS + Rb/gB + reparto de grupo  (scripts/pilotes/solver_pilote.capacidad_axil)
 - encepado: biela-tirante cerrada (T=R/tan th, C=R/sin th) + nudos/biela  (scripts/bielas-tirantes/ec2_strut_tie)

SI (N, m, Pa). Predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import math

GAMMA_S_PIL = 1.30        # resistencia por fuste (EC7, AN-ES) [confirmar AN]
GAMMA_B_PIL = 1.50        # resistencia por punta [confirmar AN]


def _zapata(cim, N, M, H):
    """EC7 zapata: hundimiento Meyerhof (B'=B-2e) y deslizamiento. cim={B,Lf,q_adm,mu}."""
    B = cim["B"]; Lf = cim["Lf"]; q_adm = cim["q_adm"]; mu = cim.get("mu", 0.5)
    # peso propio de la zapata (estabiliza el deslizamiento y suma al hundimiento)
    canto = cim.get("canto", 0.0); rho = cim.get("rho", 2500.0)
    Wz = B * Lf * canto * rho * 9.81
    N_t = N + Wz
    e = M / N_t if N_t else 0.0
    if e <= B / 6.0:
        sigma_max = N_t / (B * Lf) * (1 + 6 * e / B)
    else:
        sigma_max = 2 * N_t / (3 * Lf * (B / 2.0 - e)) if (B / 2.0 - e) > 0 else 9.99e9
    H_rd = mu * N_t
    return {"tipo": "zapata", "B_m": B, "Lf_m": Lf, "e_m": e, "e_lim_m": B / 6.0,
            "sigma_max_kPa": sigma_max / 1e3, "q_adm_kPa": q_adm / 1e3,
            "aprov_hundimiento": sigma_max / q_adm if q_adm else 9.99,
            "ok_hundimiento": bool(sigma_max <= q_adm * (1 + 1e-6)),
            "H_d_kN": H / 1e3, "H_Rd_kN": H_rd / 1e3,
            "aprov_deslizamiento": H / H_rd if H_rd else 0.0,
            "ok_deslizamiento": bool(H <= H_rd * (1 + 1e-6)),
            "ok_despegue": bool(e <= B / 6.0)}


def _capacidad_axil(D, L, qs, qb):
    """Copia byte-fiel de solver_pilote.capacidad_axil (Rc,d = Rs/gS + Rb/gB)."""
    perimetro = math.pi * D; Ab = math.pi * D ** 2 / 4
    Rs_k = perimetro * L * qs; Rb_k = Ab * qb
    Rc_d = Rs_k / GAMMA_S_PIL + Rb_k / GAMMA_B_PIL
    return {"Rs_k_kN": Rs_k / 1e3, "Rb_k_kN": Rb_k / 1e3, "Rc_d_kN": Rc_d / 1e3}


def _pilotes(cim, N, M, H):
    """Grupo de pilotes: reparto axil N/n +/- M*x/sum(x^2); cada pilote <= Rc,d."""
    D = cim["D"]; L = cim["L"]; qs = cim["qs"]; qb = cim["qb"]
    n = cim["n"]; sep = cim.get("sep", 3 * D)
    cap = _capacidad_axil(D, L, qs, qb); Rc_d = cap["Rc_d_kN"] * 1e3
    # pilotes en una fila simetrica respecto al centro (predim)
    xs = [(i - (n - 1) / 2.0) * sep for i in range(n)]
    sum_x2 = sum(x * x for x in xs) or 1.0
    N_max = N / n + (M * (max(abs(x) for x in xs)) / sum_x2 if n > 1 else 0.0)
    N_min = N / n - (M * (max(abs(x) for x in xs)) / sum_x2 if n > 1 else 0.0)
    return {"tipo": "pilotes", "n": n, "D_m": D, "L_m": L, "Rc_d_kN": Rc_d / 1e3,
            "N_pilote_max_kN": N_max / 1e3, "N_pilote_min_kN": N_min / 1e3,
            "aprov": N_max / Rc_d if Rc_d else 9.99,
            "ok": bool(N_max <= Rc_d * (1 + 1e-6)),
            "traccion": bool(N_min < 0.0)}


def _encepado(cim, N, M, H, fck):
    """Encepado de 2 pilotes por biela-tirante CERRADA (copia de la forma cerrada de
    ec2_strut_tie.verificar_encepado, sin el cross-check PyNite). cim={a,h,b,c_col,
    d_pilote,cover,phi}."""
    a = cim["a"]; h = cim["h"]; b = cim["b"]; c_col = cim.get("c_col", 0.4)
    d_pilote = cim.get("d_pilote", 0.45); cover = cim.get("cover", 0.05); phi = cim.get("phi", 0.020)
    FYD = 500e6 / 1.15; GC = 1.5
    d = h - cover - phi; z = 0.9 * d
    R = N / 2.0
    th = math.atan(z / (a / 2.0))
    T = R / math.tan(th); C = R / math.sin(th)
    fcd = fck / GC; nu_p = 1 - fck / 1e6 / 250
    sRd_strut = 0.6 * nu_p * fcd; sRd_CCC = 1.0 * nu_p * fcd; sRd_CCT = 0.85 * nu_p * fcd
    As_req = T / FYD
    u = 2 * (cover + phi / 2)
    w_strut = d_pilote * math.sin(th) + u * math.cos(th)
    sigma_strut = C / (b * w_strut)
    sigma_CCC = N / (c_col * c_col)
    A_pile = math.pi * (d_pilote / 2) ** 2
    sigma_CCT = R / A_pile
    ok = (sigma_strut <= sRd_strut and sigma_CCC <= sRd_CCC and sigma_CCT <= sRd_CCT)
    aprov = max(sigma_strut / sRd_strut, sigma_CCC / sRd_CCC, sigma_CCT / sRd_CCT)
    return {"tipo": "encepado", "theta_deg": math.degrees(th),
            "T_tirante_kN": T / 1e3, "C_biela_kN": C / 1e3, "R_pilote_kN": R / 1e3,
            "As_tirante_cm2": As_req * 1e4,
            "biela": {"sigma_MPa": sigma_strut / 1e6, "sRd_MPa": sRd_strut / 1e6, "ok": bool(sigma_strut <= sRd_strut)},
            "nudo_CCC": {"sigma_MPa": sigma_CCC / 1e6, "sRd_MPa": sRd_CCC / 1e6, "ok": bool(sigma_CCC <= sRd_CCC)},
            "nudo_CCT": {"sigma_MPa": sigma_CCT / 1e6, "sRd_MPa": sRd_CCT / 1e6, "ok": bool(sigma_CCT <= sRd_CCT)},
            "aprov": aprov, "ok": bool(ok)}


def comprobar(cimentacion, N_base, M_base, H_base, fck=30e6):
    """Despacha por tipo. cimentacion={'tipo': 'zapata'|'pilotes'|'encepado', ...}.
    N_base, M_base, H_base de CALCULO (N, N*m, N). Devuelve dict con veredicto."""
    tipo = cimentacion.get("tipo", "zapata")
    N = abs(N_base); M = abs(M_base); H = abs(H_base)
    if tipo == "zapata":
        r = _zapata(cimentacion, N, M, H)
        r["ok"] = r["ok_hundimiento"] and r["ok_deslizamiento"] and r["ok_despegue"]
        r["aprov"] = max(r["aprov_hundimiento"], r["aprov_deslizamiento"])
    elif tipo == "pilotes":
        r = _pilotes(cimentacion, N, M, H)
    elif tipo == "encepado":
        r = _encepado(cimentacion, N, M, H, fck)
    else:
        raise ValueError("tipo de cimentacion no reconocido: %s" % tipo)
    r["veredicto"] = "CUMPLE" if r["ok"] else "NO CUMPLE"
    return r
