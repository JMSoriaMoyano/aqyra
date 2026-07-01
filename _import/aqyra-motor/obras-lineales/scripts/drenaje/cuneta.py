"""
CUNETA -- drenaje superficial por MANNING (seccion simple). Norma 5.2-IC.
Plugin obras-lineales. PT 6.1 (Ola 6). stdlib pura.

Comprueba la CAPACIDAD de una cuneta (triangular o trapezoidal) en lamina libre por
la formula de Manning-Strickler y la contrasta con el CAUDAL DE CALCULO (hidrologia.py):

    Q = (1/n) * A * R^(2/3) * J^(1/2)      [m3/s]

  - n : coeficiente de Manning del revestimiento (tierra/hormigon...).
  - A : area mojada; R = A/P (radio hidraulico); J : pendiente LONGITUDINAL (m/m).
  - Seccion TRIANGULAR (b=0) o TRAPEZOIDAL, taludes 1V:zH (z = H/V) a cada lado.

Calcula el CALADO NORMAL para el caudal de calculo (biseccion), comprueba:
  1) CAPACIDAD con RESGUARDO: calado_normal + resguardo <= profundidad de la cuneta.
  2) VELOCIDAD en rango [v_min autolimpieza, v_max no erosion del revestimiento].
NO hay grafo de red: es calculo LOCAL por elemento (seccion simple). El motor de red
(Manning sobre grafo) es del PT 6.2 (colectores en lamina libre).

Devuelve un registro homogeneo CUMPLE/NO CUMPLE por cuneta. Predimensionado; revisar
y firmar por tecnico competente (ICCP). NDP [confirmar AN].
"""
import math

# --- Coeficiente de Manning por revestimiento (s/m^(1/3)) -- NDP [confirmar AN].
N_MANNING = {
    "tierra": 0.025,
    "tierra_con_vegetacion": 0.035,
    "hormigon": 0.015,
    "revestida": 0.016,
    "escollera": 0.030,
}
# --- Velocidades admisibles (m/s) por revestimiento -- NDP [confirmar AN].
#     v_min: autolimpieza (evita sedimentacion); v_max: no erosion del revestimiento.
VELOCIDAD_ADM = {
    "tierra": (0.25, 1.5),
    "tierra_con_vegetacion": (0.25, 1.8),
    "hormigon": (0.5, 6.0),
    "revestida": (0.5, 5.0),
    "escollera": (0.5, 4.0),
}
RESGUARDO_DEF_M = 0.05   # resguardo minimo por defecto (m). NDP [confirmar AN].


def _n(cuneta):
    if cuneta.get("n_manning") is not None:
        return float(cuneta["n_manning"])
    return N_MANNING.get(cuneta.get("revestimiento", "tierra"), 0.025)


def _vel_adm(cuneta):
    if cuneta.get("v_min") is not None and cuneta.get("v_max") is not None:
        return float(cuneta["v_min"]), float(cuneta["v_max"])
    return VELOCIDAD_ADM.get(cuneta.get("revestimiento", "tierra"), (0.25, 1.5))


def area_perimetro(y, b=0.0, z1=1.0, z2=1.0):
    """Area mojada A, perimetro mojado P y ancho superficial T de una seccion
    trapezoidal/triangular para un calado y. Taludes 1V:z1H y 1V:z2H."""
    y = max(float(y), 0.0)
    b = float(b)
    A = (b + 0.5 * (z1 + z2) * y) * y
    P = b + y * (math.sqrt(1.0 + z1 ** 2) + math.sqrt(1.0 + z2 ** 2))
    T = b + (z1 + z2) * y
    return A, P, T


def caudal_manning(y, n, J, b=0.0, z1=1.0, z2=1.0):
    """Caudal por Manning para un calado y (m3/s)."""
    A, P, _ = area_perimetro(y, b, z1, z2)
    if A <= 0 or P <= 0:
        return 0.0
    R = A / P
    return (1.0 / float(n)) * A * R ** (2.0 / 3.0) * math.sqrt(max(float(J), 0.0))


def calado_normal(Q, n, J, b=0.0, z1=1.0, z2=1.0, y_max=10.0, tol=1e-6):
    """Calado normal (m) para un caudal Q por biseccion. Devuelve None si Q supera
    la capacidad a y_max (no converge en el rango fisico de la cuneta)."""
    Q = float(Q)
    if Q <= 0:
        return 0.0
    if caudal_manning(y_max, n, J, b, z1, z2) < Q:
        return None  # caudal mayor que la capacidad a calado maximo
    lo, hi = 0.0, y_max
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if caudal_manning(mid, n, J, b, z1, z2) < Q:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def comprobar_cuneta(cuneta, Q_calc):
    """Comprueba una cuneta frente al caudal de calculo Q_calc (m3/s).

    cuneta: {id, tipo, b_m, z1, z2, profundidad_m, pendiente_long (J), revestimiento|
             n_manning, resguardo_m, v_min, v_max}.
    Devuelve un registro CUMPLE/NO CUMPLE con calado, capacidad, velocidad y resguardo.
    """
    b = float(cuneta.get("b_m", 0.0))
    z1 = float(cuneta.get("z1", cuneta.get("talud", 1.0)))
    z2 = float(cuneta.get("z2", cuneta.get("talud", 1.0)))
    h = float(cuneta.get("profundidad_m"))
    J = float(cuneta.get("pendiente_long", cuneta.get("J")))
    n = _n(cuneta)
    resg = float(cuneta.get("resguardo_m", RESGUARDO_DEF_M))
    v_min, v_max = _vel_adm(cuneta)

    cap_total = caudal_manning(h, n, J, b, z1, z2)            # capacidad a seccion llena
    h_util = max(h - resg, 0.0)
    cap_util = caudal_manning(h_util, n, J, b, z1, z2)        # capacidad con resguardo
    y_n = calado_normal(Q_calc, n, J, b, z1, z2, y_max=max(h * 2.0, 1.0))

    errores, info = [], []

    # 1) capacidad con resguardo
    ok_cap = Q_calc <= cap_util + 1e-9
    if ok_cap:
        info.append("Capacidad util (con resguardo %.2f m) %.3f m3/s >= Q %.3f m3/s"
                    % (resg, cap_util, Q_calc))
    else:
        errores.append("Capacidad util %.3f m3/s < Q %.3f m3/s: aumentar seccion/"
                       "pendiente o revestir (n menor)." % (cap_util, Q_calc))

    # 2) calado normal y resguardo real
    if y_n is None:
        errores.append("El caudal supera la capacidad a calado maximo (%.3f m3/s): "
                       "la cuneta desborda." % cap_total)
        resg_real = 0.0
        v = None
    else:
        resg_real = h - y_n
        info.append("Calado normal %.3f m (profundidad %.2f m, resguardo real %.3f m)"
                    % (y_n, h, resg_real))
        if resg_real + 1e-9 < resg:
            errores.append("Resguardo real %.3f m < minimo %.2f m." % (resg_real, resg))
        A, _, _ = area_perimetro(y_n, b, z1, z2)
        v = Q_calc / A if A > 0 else 0.0

    # 3) velocidad en rango
    if v is not None:
        if v + 1e-9 < v_min:
            errores.append("Velocidad %.2f m/s < minima de autolimpieza %.2f m/s "
                           "(riesgo de sedimentacion)." % (v, v_min))
        elif v > v_max + 1e-9:
            errores.append("Velocidad %.2f m/s > maxima %.2f m/s del revestimiento "
                           "(riesgo de erosion: revestir o reducir pendiente)." % (v, v_max))
        else:
            info.append("Velocidad %.2f m/s en rango [%.2f, %.2f] m/s." % (v, v_min, v_max))

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    return {
        "id": cuneta.get("id", "cuneta"),
        "tipo": cuneta.get("tipo", "triangular" if b == 0 else "trapezoidal"),
        "seccion": {"b_m": b, "z1": z1, "z2": z2, "profundidad_m": h},
        "n_manning": n,
        "pendiente_long_m_m": J,
        "revestimiento": cuneta.get("revestimiento"),
        "Q_calculo_m3_s": round(float(Q_calc), 4),
        "capacidad_total_m3_s": round(cap_total, 4),
        "capacidad_util_m3_s": round(cap_util, 4),
        "calado_normal_m": round(y_n, 4) if y_n is not None else None,
        "resguardo_min_m": resg,
        "resguardo_real_m": round(resg_real, 4) if y_n is not None else None,
        "velocidad_m_s": round(v, 3) if v is not None else None,
        "velocidad_adm_m_s": [v_min, v_max],
        "veredicto": veredicto,
        "errores": errores,
        "info": info,
        "norma": "5.2-IC",
    }


if __name__ == "__main__":
    import json
    c = {"id": "CUN-D", "tipo": "triangular", "b_m": 0.0, "z1": 3.0, "z2": 3.0,
         "profundidad_m": 0.30, "pendiente_long": 0.02, "revestimiento": "hormigon"}
    print(json.dumps(comprobar_cuneta(c, 0.1524), indent=2, ensure_ascii=False))
