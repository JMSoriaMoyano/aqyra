"""
ODT -- Obra de Drenaje Transversal (capacidad). Norma 5.2-IC. Plugin obras-lineales.
PT 6.1 (Ola 6). stdlib pura.

Comprueba la CAPACIDAD de una obra de drenaje transversal (tubo CIRCULAR o MARCO
rectangular) que cruza la plataforma, frente al CAUDAL de la cuenca vertiente
(hidrologia.py). Criterio SIMPLIFICADO de predimensionado por CONTROL DE ENTRADA /
CONTROL DE SALIDA (la capacidad gobernante es la MENOR de las dos):

  - CONTROL DE SALIDA (friccion en el conducto, lamina libre por Manning a un grado
    de llenado maximo recomendado, fill_max ~ 0.75):
        Q_out = (1/n) * A(fill) * R(fill)^(2/3) * J^(1/2)
  - CONTROL DE ENTRADA (la embocadura limita; orificio sumergido con carga a la
    entrada HW <= HW_max = HW_ratio * altura):
        Q_in = Cd * A_llena * sqrt(2*g*(HW - h_centroide))

Comprueba ademas la DIMENSION MINIMA (5.2-IC recomienda diametro/altura libre minimos
por conservacion/limpieza) y la VELOCIDAD (autolimpieza / no erosion). NO es un grafo
de red: capacidad LOCAL de UNA ODT con su cuenca. Las redes de colectores (Manning
sobre grafo) son del PT 6.2.

Devuelve un registro homogeneo CUMPLE/NO CUMPLE. Predimensionado; revisar y firmar por
tecnico competente (ICCP). NDP [confirmar AN].
"""
import math

G = 9.81

# --- Manning por material del conducto (s/m^(1/3)) -- NDP [confirmar AN].
N_MANNING_ODT = {
    "hormigon": 0.013,
    "hormigon_in_situ": 0.015,
    "chapa_ondulada": 0.024,
    "pvc": 0.010,
}
# --- Parametros de predimensionado por defecto -- NDP [confirmar AN].
FILL_MAX_DEF = 0.75       # grado de llenado maximo en control de salida (lamina libre)
HW_RATIO_DEF = 1.20       # carga a la entrada admisible HW/altura (control de entrada)
CD_DEF = 0.60             # coef. de descarga de la embocadura (orificio)
DIM_MIN_DEF_M = 1.80      # dimension libre minima de ODT bajo plataforma (m). [confirmar AN].
VEL_ODT_ADM = (0.5, 6.0)  # (autolimpieza, no erosion hormigon) m/s


def _n(odt):
    if odt.get("n_manning") is not None:
        return float(odt["n_manning"])
    return N_MANNING_ODT.get(odt.get("material", "hormigon"), 0.013)


def geom_circular(D, y):
    """Area mojada A, perimetro mojado P y ancho superficial T de un tubo circular de
    diametro D a un calado y (0<y<=D)."""
    D = float(D)
    y = min(max(float(y), 0.0), D)
    if y <= 0:
        return 0.0, 0.0, 0.0
    theta = 2.0 * math.acos(1.0 - 2.0 * y / D)   # angulo mojado (rad)
    A = (D ** 2 / 8.0) * (theta - math.sin(theta))
    P = D * theta / 2.0
    T = D * math.sin(theta / 2.0)
    return A, P, T


def geom_marco(B, H, y):
    """Area, perimetro y ancho de un marco rectangular B x H a un calado y (lamina
    libre, y<=H)."""
    B, H = float(B), float(H)
    y = min(max(float(y), 0.0), H)
    A = B * y
    P = B + 2.0 * y
    T = B
    return A, P, T


def _geom(odt, y):
    if odt.get("tipo") == "marco":
        return geom_marco(odt["B_m"], odt["H_m"], y)
    return geom_circular(odt["D_m"], y)


def _altura(odt):
    return float(odt["H_m"]) if odt.get("tipo") == "marco" else float(odt["D_m"])


def _dim_min(odt):
    """Dimension libre minima de la ODT (D o min(B,H))."""
    if odt.get("tipo") == "marco":
        return min(float(odt["B_m"]), float(odt["H_m"]))
    return float(odt["D_m"])


def _area_llena(odt):
    h = _altura(odt)
    A, _, _ = _geom(odt, h * 0.999999)
    return A


def capacidad_salida(odt, J, fill_max=FILL_MAX_DEF):
    """Capacidad por control de salida (Manning, lamina libre a grado de llenado
    fill_max). Devuelve (Q, A, R) en el calado de llenado maximo."""
    h = _altura(odt)
    y = fill_max * h
    A, P, _ = _geom(odt, y)
    if A <= 0 or P <= 0:
        return 0.0, 0.0, 0.0
    R = A / P
    n = _n(odt)
    Q = (1.0 / n) * A * R ** (2.0 / 3.0) * math.sqrt(max(float(J), 0.0))
    return Q, A, R


def capacidad_entrada(odt, hw_ratio=HW_RATIO_DEF, Cd=CD_DEF):
    """Capacidad por control de entrada (orificio sumergido con carga HW a la
    embocadura):  Q = Cd * A_llena * sqrt(2 g (HW - h_centroide))."""
    h = _altura(odt)
    A_full = _area_llena(odt)
    HW = hw_ratio * h
    h_cen = h / 2.0
    carga = max(HW - h_cen, 0.0)
    return float(Cd) * A_full * math.sqrt(2.0 * G * carga)


def calado_normal_circular(Q, D, n, J, fill_max=0.95, tol=1e-6):
    """Calado normal en tubo circular por biseccion (para la velocidad real)."""
    Q = float(Q)
    if Q <= 0:
        return 0.0
    def q(y):
        A, P, _ = geom_circular(D, y)
        if A <= 0 or P <= 0:
            return 0.0
        return (1.0 / n) * A * (A / P) ** (2.0 / 3.0) * math.sqrt(max(J, 0.0))
    y_max = fill_max * D
    if q(y_max) < Q:
        return None
    lo, hi = 0.0, y_max
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if q(mid) < Q:
            lo = mid
        else:
            hi = mid
        if hi - lo < tol:
            break
    return 0.5 * (lo + hi)


def _velocidad(odt, Q, J, fill_max):
    """Velocidad media en el conducto para Q (lamina libre)."""
    n = _n(odt)
    if odt.get("tipo") == "marco":
        B, H = float(odt["B_m"]), float(odt["H_m"])
        # calado normal rectangular por biseccion
        def q(y):
            A, P, _ = geom_marco(B, H, y)
            if A <= 0 or P <= 0:
                return 0.0
            return (1.0 / n) * A * (A / P) ** (2.0 / 3.0) * math.sqrt(max(J, 0.0))
        lo, hi, y = 0.0, fill_max * H, None
        if q(hi) >= Q:
            for _ in range(200):
                mid = 0.5 * (lo + hi)
                if q(mid) < Q:
                    lo = mid
                else:
                    hi = mid
            y = 0.5 * (lo + hi)
        if y is None:
            return None
        A, _, _ = geom_marco(B, H, y)
    else:
        y = calado_normal_circular(Q, float(odt["D_m"]), n, J, fill_max=fill_max)
        if y is None:
            return None
        A, _, _ = geom_circular(float(odt["D_m"]), y)
    return Q / A if A > 0 else None


def comprobar_odt(odt, Q_cuenca):
    """Comprueba una ODT frente al caudal de la cuenca vertiente Q_cuenca (m3/s).

    odt: {id, tipo(circular|marco), D_m | (B_m,H_m), pendiente_long(J), material|
          n_manning, fill_max, hw_ratio, Cd, dim_min_m, v_min, v_max}.
    Capacidad = min(control de entrada, control de salida). Devuelve registro
    CUMPLE/NO CUMPLE con capacidad, control gobernante, dimension y velocidad.
    """
    J = float(odt.get("pendiente_long", odt.get("J")))
    fill_max = float(odt.get("fill_max", FILL_MAX_DEF))
    hw_ratio = float(odt.get("hw_ratio", HW_RATIO_DEF))
    Cd = float(odt.get("Cd", CD_DEF))
    dim_min = float(odt.get("dim_min_m", DIM_MIN_DEF_M))
    v_min, v_max = (float(odt.get("v_min", VEL_ODT_ADM[0])),
                    float(odt.get("v_max", VEL_ODT_ADM[1])))

    Q_out, _, _ = capacidad_salida(odt, J, fill_max)
    Q_in = capacidad_entrada(odt, hw_ratio, Cd)
    if Q_out <= Q_in:
        cap, control = Q_out, "salida (friccion/Manning)"
    else:
        cap, control = Q_in, "entrada (embocadura/orificio)"

    errores, info = [], []

    # 1) capacidad
    ok_cap = Q_cuenca <= cap + 1e-9
    if ok_cap:
        info.append("Capacidad %.3f m3/s (control de %s) >= Q cuenca %.3f m3/s"
                    % (cap, control, Q_cuenca))
    else:
        errores.append("Capacidad %.3f m3/s (control de %s) < Q cuenca %.3f m3/s: "
                       "aumentar dimension/pendiente o duplicar la ODT."
                       % (cap, control, Q_cuenca))
    info.append("Control de salida %.3f m3/s vs control de entrada %.3f m3/s "
                "(gobierna el menor)." % (Q_out, Q_in))

    # 2) dimension minima (limpieza/conservacion)
    dim = _dim_min(odt)
    if dim + 1e-9 < dim_min:
        errores.append("Dimension libre %.2f m < minima %.2f m (limpieza/conservacion 5.2-IC)."
                       % (dim, dim_min))
    else:
        info.append("Dimension libre %.2f m >= minima %.2f m." % (dim, dim_min))

    # 3) velocidad
    v = _velocidad(odt, Q_cuenca, J, fill_max) if ok_cap else None
    if v is not None:
        if v + 1e-9 < v_min:
            errores.append("Velocidad %.2f m/s < minima de autolimpieza %.2f m/s." % (v, v_min))
        elif v > v_max + 1e-9:
            errores.append("Velocidad %.2f m/s > maxima %.2f m/s (erosion: cuenco "
                           "amortiguador/escollera a la salida)." % (v, v_max))
        else:
            info.append("Velocidad %.2f m/s en rango [%.2f, %.2f] m/s." % (v, v_min, v_max))

    veredicto = "CUMPLE" if not errores else "NO CUMPLE"
    seccion = ({"tipo": "marco", "B_m": float(odt["B_m"]), "H_m": float(odt["H_m"])}
               if odt.get("tipo") == "marco"
               else {"tipo": "circular", "D_m": float(odt["D_m"])})
    return {
        "id": odt.get("id", "ODT"),
        "seccion": seccion,
        "material": odt.get("material"),
        "n_manning": _n(odt),
        "pendiente_long_m_m": J,
        "Q_cuenca_m3_s": round(float(Q_cuenca), 4),
        "capacidad_m3_s": round(cap, 4),
        "control_gobernante": control,
        "capacidad_salida_m3_s": round(Q_out, 4),
        "capacidad_entrada_m3_s": round(Q_in, 4),
        "dimension_libre_m": dim,
        "dimension_min_m": dim_min,
        "velocidad_m_s": round(v, 3) if v is not None else None,
        "velocidad_adm_m_s": [v_min, v_max],
        "veredicto": veredicto,
        "errores": errores,
        "info": info,
        "norma": "5.2-IC",
    }


if __name__ == "__main__":
    import json
    o = {"id": "ODT-1", "tipo": "circular", "D_m": 1.80, "pendiente_long": 0.015,
         "material": "hormigon"}
    print(json.dumps(comprobar_odt(o, 1.2), indent=2, ensure_ascii=False))
