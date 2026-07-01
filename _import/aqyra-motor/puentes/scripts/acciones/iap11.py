"""
Acciones IAP-11 (puentes de carretera) -- modulo de la disciplina `puentes`
(slot C4-puentes). El nucleo `motor-fem` NO conoce esta normativa: aqui se
traducen las acciones a CASOS DE CARGA del modelo C5 y al TREN del barrido movil.

Implementado para vigas pretensadas: permanentes (g1+g2), LM1 (tandem+UDL por
carril), termica (uniforme+gradiente), viento (basico) y combinaciones de puente.
Valores IAP-11/EN 1991-2 (AN Espana). alpha_Q=alpha_q=1.0 [confirmar AN].
SI (N, m). Predimensionado/asistencia; revisar y firmar por tecnico competente.
"""
from __future__ import annotations
G_ACC = 9.81
Q_IK = {1: 300e3, 2: 200e3, 3: 100e3}      # carga de EJE del tandem por carril (N)
Q_K = {1: 9.0e3, 2: 2.5e3, 3: 2.5e3}       # sobrecarga uniforme por carril (N/m2)
Q_K_REST = 2.5e3
ALPHA_Q = 1.0; ALPHA_Q_Q = 1.0
ANCHO_CARRIL = 3.0


def permanentes(tablero, model, meta, g2_N_m2=None):
    mat = model["materiales"]["HORM"]; A = model["secciones"]["VIGA"]["A"]
    n = meta["n_vigas"]; sep = meta["sep"]
    g1_N_m = mat["rho"] * G_ACC * A
    ancho_total = (n - 1) * sep + tablero.get("voladizo", sep)
    g2 = g2_N_m2 if g2_N_m2 is not None else tablero.get("g2_N_m2", 0.0)
    g2_N_m = g2 * ancho_total / n
    for bid, b in model["barras"].items():
        if b.get("tipo") == "viga":
            model["cargas"].append({"caso": "G", "barra": bid, "direccion": "GZ", "qz": -(g1_N_m + g2_N_m)})
    return {"g1_N_m_viga": g1_N_m, "g2_N_m_viga": g2_N_m, "ancho_total_m": ancho_total}


def lm1(tablero, model, meta):
    n = meta["n_vigas"]; ne = meta["ne"]; centro = meta["centro"]
    ancho_total = (n - 1) * meta["sep"] + tablero.get("voladizo", meta["sep"])
    n_carriles = min(3, max(1, int(ancho_total // ANCHO_CARRIL)))
    orden = sorted(range(n), key=lambda g: abs(g - centro))
    lineas = []
    for k in range(1, n_carriles + 1):
        g = orden[k - 1] if (k - 1) < n else orden[-1]
        Qe = ALPHA_Q * Q_IK.get(k, 100e3)
        udl = ALPHA_Q_Q * Q_K.get(k, Q_K_REST) * ANCHO_CARRIL
        lineas.append({"id": "carril%d" % k, "viga": g, "camino": list(meta["girders"][g]),
                       "tren": {"axles": [{"P": Qe, "offset": 0.0}, {"P": Qe, "offset": 1.2}], "udl": udl}})
    objetivos = []
    for g in range(n):
        mid = ne // 2
        objetivos.append({"id": "M_centro_v%d" % g, "tipo": "esfuerzo_barra",
                          "elem": "G_%d_%d" % (g, mid - 1), "comp": "My_j"})
        objetivos.append({"id": "V_apoyo_v%d" % g, "tipo": "esfuerzo_barra",
                          "elem": "G_%d_0" % g, "comp": "Vz_i"})
        objetivos.append({"id": "R_apoyo_v%d" % g, "tipo": "reaccion",
                          "nodo": meta["girders"][g][0], "comp": 2})
    cm = {"posiciones": tablero.get("posiciones", 41), "objetivos": objetivos, "lineas": lineas}
    model["cargas_moviles"] = cm
    return cm


def termica(tablero, model, meta, dT_unif=None, dT_grad=None):
    alpha = tablero.get("alpha_termico", 1.0e-5)
    dTu = dT_unif if dT_unif is not None else tablero.get("dT_uniforme", 15.0)
    dTg = dT_grad if dT_grad is not None else tablero.get("dT_gradiente", 10.0)
    h = tablero["viga_sec"].get("h", 1.0)
    for bid, b in model["barras"].items():
        if b.get("tipo") == "viga":
            model["cargas"].append({"caso": "T", "barra": bid, "tipo": "termica_axil", "alpha": alpha, "dT": dTu})
            model["cargas"].append({"caso": "T", "barra": bid, "tipo": "termica_gradiente", "alpha": alpha, "dT": dTg, "h": h})
    return {"dT_uniforme": dTu, "dT_gradiente": dTg, "alpha": alpha}


def viento(tablero, model, meta, q_viento_N_m=None):
    qv = q_viento_N_m if q_viento_N_m is not None else tablero.get("q_viento_N_m", 0.0)
    if qv:
        for bid, b in model["barras"].items():
            if b.get("tipo") == "viga":
                model["cargas"].append({"caso": "V", "barra": bid, "direccion": "GY", "qz": qv})
    return {"q_viento_N_m": qv}


def combinaciones(psi0_Q=0.4, psi1_Q=0.4, psi2_Q=0.2, psi0_T=0.6, psi0_V=0.6):
    return {
        "ELU": {"G": 1.35, "P": 1.0, "M": 1.35, "T": 1.5 * psi0_T, "V": 1.5 * psi0_V},
        "ELU_G": {"G": 1.35, "P": 1.0},
        "ELS_car": {"G": 1.0, "P": 1.0, "M": 1.0, "T": psi0_T, "V": psi0_V},
        "ELS_fre": {"G": 1.0, "P": 1.0, "M": psi1_Q},
        "ELS_cp": {"G": 1.0, "P": 1.0, "M": psi2_Q},
    }


# --------------------------------------------------------------------------- #
#  IAP-11 sobre LOSA (lamina DKMQ) -- PT 7.2 (losa postesada)                  #
# --------------------------------------------------------------------------- #
def permanentes_losa(tablero, M, meta, caso_g1="G1", caso_g2="G2"):
    """Peso propio g1 (rho*g*t) y carga muerta g2 (pavimento, N/m2) como PRESION
    sobre las laminas (p<0 = hacia abajo). Casos separados (g1 para transferencia).
    Devuelve {g1_N_m2,g2_N_m2,w_equilibrar_N_m2}."""
    rho = tablero['material'].get('rho', 2500.0); t = meta['t']
    g1 = rho * G_ACC * t
    g2 = tablero.get('g2_N_m2', 0.0)
    for el in M.elementos:
        if getattr(el, "eid", "").startswith("Q_"):
            el.cargas.append({"caso": caso_g1, "p": -g1})
            if g2:
                el.cargas.append({"caso": caso_g2, "p": -g2})
    return {"g1_N_m2": g1, "g2_N_m2": g2, "w_equilibrar_N_m2": g1 + g2}


def postesado_losa(tablero, M, meta, postesado, caso="P"):
    """Carga equivalente del postesado biaxial como PRESION hacia ARRIBA (p>0)
    sobre las laminas: w_p = w_px + w_py (balance de cargas, P_inf). sigma_cp se
    trata aparte (analitico) en la comprobacion EC2. Devuelve {w_p,w_px,w_py}."""
    import balance_2d as b2d
    perd = postesado.get('perdidas_pct', 18.0) / 100.0
    Pinfx = postesado['P0_x_N_m'] * (1 - perd); Pinfy = postesado.get('P0_y_N_m', 0.0) * (1 - perd)
    w_px = b2d.w_balance_direccion(Pinfx, meta['L'], postesado['a_x'])
    w_py = b2d.w_balance_direccion(Pinfy, meta['B'], postesado.get('a_y', postesado['a_x']))
    w_p = w_px + w_py
    for el in M.elementos:
        if getattr(el, "eid", "").startswith("Q_"):
            el.cargas.append({"caso": caso, "p": +w_p})
    return {"w_p_N_m2": w_p, "w_px_N_m2": w_px, "w_py_N_m2": w_py,
            "Pinfx_N_m": Pinfx, "Pinfy_N_m": Pinfy}


WHEEL_SEP = 2.0   # separacion transversal de ruedas del tandem LM1 (m)


def _fila_mas_cercana(meta, y):
    ys = meta["ys"]; return min(range(len(ys)), key=lambda j: abs(ys[j] - y))


def lm1_losa(tablero, meta, caminos):
    """Tren LM1 por carril sobre la losa + objetivos `esfuerzo_lamina` (Mx, momento
    de VANO) en la franja central. Cada carril se modela con DOS lineas de rueda
    (tandem = 2 ruedas/eje separadas WHEEL_SEP), cada una con MEDIA carga de eje y
    MEDIA sobrecarga -> evita la concentracion artificial de una linea-cuchillo y
    es fiel al LM1. Devuelve cm para fem1.movil."""
    grid = meta["nid_grid"]; ys = meta["ys"]; B = meta["B"]; nx = meta["nx"]
    objetivos = []
    for eid in meta["franja_centro"]:
        objetivos.append({"id": "Mx_%s" % eid, "tipo": "esfuerzo_lamina", "elem": eid, "comp": "Mx"})
    lineas = []
    for k, cam in enumerate(caminos, start=1):
        Qe = ALPHA_Q * Q_IK.get(k, 100e3)
        udl = ALPHA_Q_Q * Q_K.get(k, Q_K_REST) * ANCHO_CARRIL
        yc = ys[cam["jrow"]]
        for lado, dy in (("L", -WHEEL_SEP / 2.0), ("R", +WHEEL_SEP / 2.0)):
            yw = min(max(yc + dy, 0.0), B)
            jrow = _fila_mas_cercana(meta, yw)
            lineas.append({"id": "%s_%s" % (cam["id"], lado),
                           "camino": [grid[jrow][i] for i in range(nx + 1)],
                           "tren": {"axles": [{"P": Qe / 2.0, "offset": 0.0},
                                              {"P": Qe / 2.0, "offset": 1.2}], "udl": udl / 2.0}})
    return {"posiciones": tablero.get("posiciones", nx + 1), "objetivos": objetivos, "lineas": lineas}


# --------------------------------------------------------------------------- #
#  IAP-11 + empuje de tierras sobre PORTICO (barras) -- PT 7.2                 #
# --------------------------------------------------------------------------- #
def permanentes_portico(p, model, meta, caso="G"):
    """Peso propio del dintel (rho*g*A) + carga muerta g2 (N/m) como GZ sobre las
    barras del dintel."""
    mat = model["materiales"]["HORM"]; A = model["secciones"]["DINTEL"]["A"]
    g1 = mat["rho"] * G_ACC * A
    g2 = p.get("g2_N_m", 0.0)
    for bid in meta["dintel_barras"]:
        model["cargas"].append({"caso": caso, "barra": bid, "direccion": "GZ", "qz": -(g1 + g2)})
    return {"g1_N_m": g1, "g2_N_m": g2}


def lm1_portico(p, model, meta):
    """Tren LM1 (1 carril dominante, tandem+UDL) sobre el camino del dintel +
    objetivos de envolvente: My en centro de dintel y My en base de pilas."""
    ne = meta["ne"]
    Qe = ALPHA_Q * Q_IK[1]; udl = ALPHA_Q_Q * Q_K[1] * ANCHO_CARRIL
    n_carriles = p.get("n_carriles", 1)
    if n_carriles >= 2:
        udl += ALPHA_Q_Q * Q_K[2] * ANCHO_CARRIL
        Qe += ALPHA_Q * Q_IK[2]
    lineas = [{"id": "calzada", "camino": list(meta["camino_dintel"]),
               "tren": {"axles": [{"P": Qe, "offset": 0.0}, {"P": Qe, "offset": 1.2}], "udl": udl}}]
    mid = ne // 2
    objetivos = [{"id": "M_dintel", "tipo": "esfuerzo_barra", "elem": "DIN_%d" % (mid), "comp": "My_i"},
                 {"id": "M_pilaL_base", "tipo": "esfuerzo_barra", "elem": meta["pilaL_barras"][0], "comp": "My_i"},
                 {"id": "M_pilaR_base", "tipo": "esfuerzo_barra", "elem": meta["pilaR_barras"][0], "comp": "My_i"}]
    cm = {"posiciones": p.get("posiciones", ne + 1), "objetivos": objetivos, "lineas": lineas}
    model["cargas_moviles"] = cm
    return cm


def empuje_tierras(p, model, meta, caso="E"):
    """Empuje de tierras horizontal TRIANGULAR sobre ambas pilas (marco enterrado),
    aplicado por SEGMENTO como carga uniforme global GX (presion media x ancho).
    K se pasa ya calculado (K0 reposo o Ka activo). Pilas empujadas hacia el vano:
    izquierda +X, derecha -X. Devuelve {K,gamma,resultante_kN_pila}."""
    emp = p["empuje"]; K = emp["K"]; gamma = emp["gamma"]; b = emp.get("b", 1.0)
    H = meta["H"]; npil = meta["np"]
    res = 0.0
    for lado, barras_lado, signo in (("L", meta["pilaL_barras"], +1.0),
                                     ("R", meta["pilaR_barras"], -1.0)):
        for k, bid in enumerate(barras_lado):
            z_mid = H * (k + 0.5) / npil
            depth = H - z_mid                       # profundidad desde superficie (cota H)
            pres = K * gamma * depth                # N/m2
            q = signo * pres * b                    # N/m (linea sobre la pila)
            model["cargas"].append({"caso": caso, "barra": bid, "direccion": "GX", "qz": q})
            res += abs(pres * b) * (H / npil)
    return {"K": K, "gamma": gamma, "b": b, "resultante_N_pila": res / 2.0}


# --------------------------------------------------------------------------- #
#  IAP-11 sobre CELOSIA (barras articuladas) -- PT 7.2                         #
# --------------------------------------------------------------------------- #
def permanentes_celosia(c, M, meta, caso="G"):
    """Carga permanente del tablero (g, N/m, incluye peso propio de la celosia de
    forma simplificada) como cargas NODALES en los nudos del cordon inferior
    (p por nudo interior, p/2 en extremos). Hacia -Z."""
    g = c.get("g_N_m", 0.0); p = meta["p"]; bot = meta["bot"]; n = meta["n"]
    for i, nd in enumerate(bot):
        trib = p if 0 < i < n else p / 2.0
        M.add_carga_nodal(caso, nd, [0.0, 0.0, -g * trib, 0.0, 0.0, 0.0])
    return {"g_N_m": g}


def lm1_celosia(c, meta):
    """Tren LM1 (1-2 carriles) sobre el camino del cordon inferior + objetivos de
    envolvente del AXIL (N_i) de cordones y diagonales. Devuelve cm para fem1.movil."""
    Qe = ALPHA_Q * Q_IK[1]; udl = ALPHA_Q_Q * Q_K[1] * ANCHO_CARRIL
    if c.get("n_carriles", 1) >= 2:
        Qe += ALPHA_Q * Q_IK[2]; udl += ALPHA_Q_Q * Q_K[2] * ANCHO_CARRIL
    lineas = [{"id": "calzada", "camino": list(meta["camino_inferior"]),
               "tren": {"axles": [{"P": Qe, "offset": 0.0}, {"P": Qe, "offset": 1.2}], "udl": udl}}]
    objetivos = []
    for bid in meta["cordon_inf"] + meta["cordon_sup"] + meta["diagonales"] + meta["montantes"]:
        objetivos.append({"id": "N_%s" % bid, "tipo": "esfuerzo_barra", "elem": bid, "comp": "N_i"})
    return {"posiciones": c.get("posiciones", meta["n"] * 2 + 1), "objetivos": objetivos, "lineas": lineas}


# --------------------------------------------------------------------------- #
#  IAP-11 sobre SUBESTRUCTURA (pila + aparato de apoyo) -- PT 7.3              #
# --------------------------------------------------------------------------- #
#  Convencion de casos: G=permanente, M=trafico LM1 (vertical), F=frenado/arranque
#  (horizontal), V=viento (horizontal), T=termica (horizontal). gamma_Q=1.35 para
#  el grupo de trafico de carretera (IAP-11). El aparato de apoyo transmite las
#  reacciones del tablero a la cabeza de la pila como cargas NODALES.

def cargas_cabeza_pila(reac, M, meta, e_long=0.0, e_trans=0.0):
    """Aplica las reacciones del tablero (dict estandar de aparatos_apoyo) como
    cargas NODALES en la cabeza de la pila. reac tiene N_G_N, N_LM1_N, H_frenado_N,
    H_viento_N, H_termica_N, M_G_Nm, M_LM1_Nm. e_long: excentricidad longitudinal
    del apoyo (m) -> momento adicional My por el axil. Devuelve resumen."""
    head = meta["head_node"]
    NG = reac.get("N_G_N", 0.0); NM = reac.get("N_LM1_N", 0.0)
    # vertical (hacia -Z) + momento por excentricidad del axil (My = N*e_long)
    M.add_carga_nodal("G", head, [0.0, 0.0, -NG, 0.0, NG * e_long, 0.0])
    M.add_carga_nodal("M", head, [0.0, 0.0, -NM, 0.0, NM * e_long, 0.0])
    # horizontales en cabeza (direccion X = longitudinal del puente)
    if reac.get("H_frenado_N", 0.0):
        M.add_carga_nodal("F", head, [reac["H_frenado_N"], 0.0, 0.0, 0.0, 0.0, 0.0])
    if reac.get("H_viento_N", 0.0):
        M.add_carga_nodal("V", head, [reac["H_viento_N"], 0.0, 0.0, 0.0, 0.0, 0.0])
    if reac.get("H_termica_N", 0.0):
        M.add_carga_nodal("T", head, [reac["H_termica_N"], 0.0, 0.0, 0.0, 0.0, 0.0])
    if reac.get("M_G_Nm", 0.0):
        M.add_carga_nodal("G", head, [0.0, 0.0, 0.0, 0.0, reac["M_G_Nm"], 0.0])
    if reac.get("M_LM1_Nm", 0.0):
        M.add_carga_nodal("M", head, [0.0, 0.0, 0.0, 0.0, reac["M_LM1_Nm"], 0.0])
    return {"head": head, "N_G_N": NG, "N_LM1_N": NM,
            "H_frenado_N": reac.get("H_frenado_N", 0.0),
            "H_viento_N": reac.get("H_viento_N", 0.0),
            "H_termica_N": reac.get("H_termica_N", 0.0), "e_long_m": e_long}


def peso_propio_pila(p, M, meta, caso="G"):
    """Peso propio del fuste como carga global GZ sobre las barras de la pila."""
    rho = p["material"].get("rho", 2500.0); A = p["pila_sec"]["A"]
    g = rho * G_ACC * A
    for el in M.elementos:
        if getattr(el, "eid", "").startswith("PIL_"):
            el.cargas.append({"caso": caso, "tipo": "global_uniforme", "qz": -g})
    return {"g_pp_N_m": g}


def viento_pila(p, M, meta, q_viento_N_m=None, caso="V"):
    """Viento transversal sobre el fuste de la pila como carga global GX (N/m)."""
    qv = q_viento_N_m if q_viento_N_m is not None else p.get("q_viento_pila_N_m", 0.0)
    if qv:
        for el in M.elementos:
            if getattr(el, "eid", "").startswith("PIL_"):
                el.cargas.append({"caso": caso, "tipo": "global_uniforme", "qx": qv})
    return {"q_viento_pila_N_m": qv}


def combinaciones_pila(psi0_V=0.6, psi0_T=0.6):
    """Combinaciones ELU/ELS de puente para la pila (IAP-11). Grupo de trafico
    (M+F) con gamma_Q=1.35; viento/termica concomitantes con psi0. [confirmar AN]."""
    return {
        "ELU": {"G": 1.35, "M": 1.35, "F": 1.35, "V": 1.5 * psi0_V, "T": 1.5 * psi0_T},
        "ELU_G": {"G": 1.35},
        "ELS_car": {"G": 1.0, "M": 1.0, "F": 1.0, "V": psi0_V, "T": psi0_T},
    }
