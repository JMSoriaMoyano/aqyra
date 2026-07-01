"""
Comprobacion EC2 de MUROS de hormigon (elemento plano vertical):
  - Compresion con efectos de esbeltez (metodo simplificado de muros
    EN 1992-1-1 §12.6.5.2, factor Phi; clasificacion de esbeltez §5.8.3.1)
  - Armadura minima de muro (§9.6): vertical y horizontal

Trabaja por metro de ancho de muro. Unidades SI (N, m, Pa).
Nota: el metodo §12.6.5.2 es del lado de la seguridad para muros de hormigon;
para muros muy armados, §5.8 (curvatura nominal) permitiria mayor capacidad.
"""
import math

GC, GS = 1.50, 1.15


def comprobar_compresion(N_Ed, M_Ed, t, H, fck, beta=1.0):
    """
    N_Ed : axil de compresion por metro (N/m, valor absoluto)
    M_Ed : momento fuera de plano por metro (N·m/m)
    t    : espesor del muro (m) ; H: altura libre (m) ; beta: factor de pandeo (lo=beta*H)
    """
    b = 1.0
    Ac = b * t
    fcd = fck / GC
    lo = beta * H
    i = t / math.sqrt(12)
    lam = lo / i

    # clasificacion de esbeltez (§5.8.3.1)
    n = N_Ed / (Ac * fcd)
    A, B, C = 0.7, 1.1, 0.7
    lam_lim = 20 * A * B * C / math.sqrt(n) if n > 0 else 1e9
    esbelto = lam > lam_lim

    # excentricidades
    e0 = M_Ed / N_Ed if N_Ed > 0 else 0.0
    ei = lo / 400.0                    # imperfeccion
    etot = e0 + ei

    # factor de capacidad Phi (§12.6.5.2)
    phi = min(1.14 * (1 - 2 * etot / t) - 0.02 * lo / t, 1 - 2 * etot / t)
    phi = max(phi, 0.0)
    N_Rd = b * t * fcd * phi          # N/m (capacidad de la seccion de hormigon)

    return {
        "N_Ed_kN_m": N_Ed / 1e3, "M_Ed_kNm_m": M_Ed / 1e3,
        "lo_m": lo, "lambda": lam, "lambda_lim": lam_lim, "esbelto": bool(esbelto),
        "e0_mm": e0 * 1e3, "ei_mm": ei * 1e3, "etot_mm": etot * 1e3,
        "Phi": phi, "N_Rd_kN_m": N_Rd / 1e3, "u": N_Ed / N_Rd if N_Rd > 0 else 9.99,
        "ok": bool(N_Rd > 0 and N_Ed <= N_Rd),
    }


def armadura_minima(t, fck=None):
    """Armadura minima de muro (§9.6), por metro. Devuelve cm2/m totales."""
    Ac = 1.0 * t
    As_v = 0.002 * Ac                 # vertical, total (repartir en dos caras)
    As_v = min(As_v, 0.04 * Ac)
    As_h = max(0.25 * As_v, 0.001 * Ac)
    return {"As_v_min_cm2_m": As_v * 1e4, "As_h_min_cm2_m": As_h * 1e4}


def dimensionar(N_Ed, M_Ed, t, H, fck, beta=1.0, t_step=0.05, t_max=0.60):
    """Si la compresion no cumple, busca el espesor minimo que cumple."""
    tt = t
    while tt <= t_max:
        if comprobar_compresion(N_Ed, M_Ed, tt, H, fck, beta)["ok"]:
            return {"t_min_mm": round(tt * 1e3), "incremento_mm": round((tt - t) * 1e3)}
        tt += t_step
    return {"t_min_mm": None, "incremento_mm": None, "nota": "no cumple hasta t_max"}


if __name__ == "__main__":
    r = comprobar_compresion(N_Ed=220e3, M_Ed=25e3, t=0.25, H=3.5, fck=30e6)
    import json
    print(json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in r.items()},
                     indent=1, ensure_ascii=False))
    print("Armadura minima:", armadura_minima(0.25))
