"""
Idealizacion de un ESTRIBO de puente como MURO con CARGAS DE TABLERO en cabeza
(PT 7.3). El estribo se trata como un muro mensula (alzado + zapata puntera/talon)
con empuje de tierras + sobrecarga de trafico tras el trasdos + las reacciones del
tablero (vertical permanente + LM1; horizontal de frenado) aplicadas en la
CORONACION.

Reutiliza el dimensionado de `muros-contencion` (motor-calculo): la verificacion
EC7 (vuelco/deslizamiento/hundimiento) y EC2 (alzado/puntera/talon) se delegan en
`verificacion_muro.verificar` (puro, sin PyNite). Como `solver_muro` arrastra PyNite
(no disponible), sus FORMULAS PURAS (ka_rankine/ka_coulomb/kp_rankine/empujes/pesos)
se copian byte-fiel y se atribuyen; y el FUSTE (alzado) se resuelve con `motor-fem`
(C5) en vez de PyNite (mensula vertical bajo empuje + cargas de cabeza).

Empuje ACTIVO Ka por defecto (estribo abierto/con junta, con movilidad) o REPOSO K0
(estribo cerrado/integral) segun `terreno.metodo_empuje`. SI (N, m, Pa). Predim (ICCP).
"""
from __future__ import annotations
import math
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "comun"))


# --- COPIA BYTE-FIEL de solver_muro (motor-calculo v0.23.0): coeficientes de empuje ---
def ka_rankine(phi, beta=0.0):
    phir, br = math.radians(phi), math.radians(beta)
    if abs(beta) < 1e-9:
        return math.tan(math.radians(45 - phi / 2)) ** 2
    cb, cp = math.cos(br), math.cos(phir)
    r = math.sqrt(max(cb ** 2 - cp ** 2, 0.0))
    return cb * (cb - r) / (cb + r)


def ka_coulomb(phi, delta, beta=0.0, theta=0.0):
    phir, dr, br, tr = map(math.radians, (phi, delta, beta, theta))
    num = math.cos(phir - tr) ** 2
    raiz = math.sqrt(math.sin(phir + dr) * math.sin(phir - br) /
                     (math.cos(dr + tr) * math.cos(tr - br)))
    den = math.cos(tr) ** 2 * math.cos(dr + tr) * (1 + raiz) ** 2
    return num / den


def kp_rankine(phi):
    return math.tan(math.radians(45 + phi / 2)) ** 2


def k0_reposo(phi):
    return 1.0 - math.sin(math.radians(phi))


G_ACC = 9.81


# --- COPIA BYTE-FIEL de solver_muro.empujes (integra presiones del trasdos) ---
def empujes(model, n=400):
    m = model["muro"]; t = model["terreno"]
    H = m["Hm"] + m["e_z"]
    gamma, phi, c, beta = t["gamma"], t["phi"], t["c"], t["beta"]
    delta = t["delta"] if t["metodo"] == "coulomb" else 0.0
    Ka = ka_coulomb(phi, delta, beta) if t["metodo"] == "coulomb" else ka_rankine(phi, beta)
    if t.get("metodo_empuje", "activo") == "reposo":
        Ka = k0_reposo(phi); delta = 0.0
    q = model["sobrecarga"]
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    dz = H / n
    E_soil = M_soil = 0.0; E_water = M_water = 0.0; sigv_soil = 0.0
    for i in range(n):
        z = (i + 0.5) * dz
        g_eff = gamma - gw if (has_w and z > zw) else gamma
        sigv_soil += g_eff * dz
        sh_soil = max(Ka * sigv_soil - 2 * c * math.sqrt(Ka), 0.0)
        za = H - z
        E_soil += sh_soil * dz; M_soil += sh_soil * dz * za
        if has_w and z > zw:
            u = gw * (z - zw); E_water += u * dz; M_water += u * dz * za
    E_q = Ka * q * H; M_q = E_q * (H / 2)

    def comp(name, Eh_total, M, caso):
        za = M / Eh_total if Eh_total else 0.0
        if name in ("empuje_suelo", "empuje_sobrecarga") and delta:
            Eh = Eh_total * math.cos(math.radians(delta)); Ev = Eh_total * math.sin(math.radians(delta))
        else:
            Eh, Ev = Eh_total, 0.0
        return {"nombre": name, "caso": caso, "Eh_kN": Eh / 1e3, "Ev_kN": Ev / 1e3,
                "z_kN_m": za, "x_Ev_m": m["B"]}
    comps = [comp("empuje_suelo", E_soil, M_soil, "G"), comp("empuje_sobrecarga", E_q, M_q, "Q")]
    if E_water:
        comps.append(comp("empuje_agua", E_water, M_water, "G"))
    Kp = kp_rankine(t["phi_pas"]); Pp = 0.5 * Kp * t["gamma_pas"] * m["Df"] ** 2; Pp_mov = t["f_pas"] * Pp
    return {"H": H, "Ka": Ka, "Kp": Kp, "metodo": t["metodo"], "delta": delta,
            "componentes": comps, "pasivo_kN": Pp_mov / 1e3, "z_pasivo_m": m["Df"] / 3}


# --- COPIA BYTE-FIEL de solver_muro.pesos (pesos estabilizadores) ---
def pesos(model):
    m = model["muro"]; t = model["terreno"]
    rho = model["materiales"][m["material"]]["rho"]
    gc = rho * G_ACC
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    Hm, t_alz, e_z = m["Hm"], m["t_alz"], m["e_z"]
    pun, tal, B, Df = m["puntera"], m["talon"], m["B"], m["Df"]
    x_alz = pun + t_alz / 2
    h_w_heel = (Hm - zw) if (has_w and zw < Hm) else 0.0
    g_soil_dry = t["gamma"]
    W_soil_heel = tal * ((Hm - max(h_w_heel, 0)) * g_soil_dry + max(h_w_heel, 0) * (t["gamma"] - gw))
    items = [
        {"nombre": "peso_alzado", "W_kN": (t_alz * Hm * gc) / 1e3, "x_m": x_alz, "caso": "G"},
        {"nombre": "peso_zapata", "W_kN": (B * e_z * gc) / 1e3, "x_m": B / 2, "caso": "G"},
        {"nombre": "suelo_talon", "W_kN": W_soil_heel / 1e3, "x_m": pun + t_alz + tal / 2, "caso": "G"},
        {"nombre": "suelo_puntera", "W_kN": (pun * Df * t["gamma_pas"]) / 1e3, "x_m": pun / 2, "caso": "G"},
        {"nombre": "sobrecarga_talon", "W_kN": (model["sobrecarga"] * tal) / 1e3,
         "x_m": pun + t_alz + tal / 2, "caso": "Q"},
    ]
    cor = model.get("coronacion", {})
    if cor.get("N_G_N"):
        items.append({"nombre": "coron_G", "W_kN": cor["N_G_N"] / 1e3, "x_m": x_alz, "caso": "G"})
    if cor.get("N_Q_N"):
        items.append({"nombre": "coron_Q", "W_kN": cor["N_Q_N"] / 1e3, "x_m": x_alz, "caso": "Q"})
    return items, gc


def construir_modelo_muro(p):
    """Construye el modelo neutro del muro/estribo a partir de los parametros del
    estribo (geometria, terreno, material) y las reacciones del tablero en cabeza.
    p['reacciones'] = {N_G_N, N_LM1_N, H_frenado_N}. Devuelve el dict 'model'."""
    g = p["geom"]; t = dict(p["terreno"]); mat = p["material"]
    reac = p.get("reacciones", {})
    Hm = g["Hm"]; e_z = g["e_z"]; t_alz = g["t_alz"]
    pun = g["puntera"]; tal = g["talon"]; B = pun + t_alz + tal; Df = g.get("Df", e_z)
    model = {
        "muro": {"Hm": Hm, "e_z": e_z, "t_alz": t_alz, "puntera": pun, "talon": tal,
                 "B": B, "Df": Df, "material": "HORM"},
        "terreno": {"gamma": t.get("gamma", 19000.0), "phi": t.get("phi", 30.0),
                    "c": t.get("c", 0.0), "beta": t.get("beta", 0.0),
                    "delta": t.get("delta", 0.0), "metodo": t.get("metodo", "rankine"),
                    "metodo_empuje": t.get("metodo_empuje", "activo"),
                    "gamma_w": t.get("gamma_w", 9810.0), "nf": t.get("nf", -1.0),
                    "phi_pas": t.get("phi_pas", t.get("phi", 30.0)),
                    "gamma_pas": t.get("gamma_pas", t.get("gamma", 19000.0)),
                    "f_pas": t.get("f_pas", 0.5), "phi_base": t.get("phi_base", 30.0),
                    "adh_base": t.get("adh_base", 0.0), "Rd": t.get("Rd", 500000.0)},
        "materiales": {"HORM": {"E": mat.get("E", 33e9), "G": mat.get("G", 13.75e9),
                                "nu": mat.get("nu", 0.2), "rho": mat.get("rho", 2500.0),
                                "fck": mat["fck"],
                                "fctm": mat.get("fctm", 0.30 * (mat["fck"] / 1e6) ** (2 / 3) * 1e6)}},
        "sobrecarga": p.get("sobrecarga", 10000.0),
        "coronacion": {"N_G_N": reac.get("N_G_N", 0.0), "N_Q_N": reac.get("N_LM1_N", 0.0),
                       "H_Q_N": reac.get("H_frenado_N", 0.0)},
    }
    return model


def solve_fuste_fem(model, n=12):
    """Resuelve el ALZADO (fuste) del estribo como MENSULA vertical con motor-fem
    (C5): empuje del suelo (G, triangular), sobrecarga (Q, constante), agua (G) y la
    horizontal de frenado del tablero (Q) en coronacion. Devuelve esfuerzos por combo
    {ELU,ELS_car,ELS_cp:{M_base,V_base}} (N*m, N) por metro de muro (b=1 m)."""
    import mallador
    m = model["muro"]; t = model["terreno"]; mp = model["materiales"]["HORM"]
    Hm = m["Hm"]; t_alz = m["t_alz"]
    A = 1.0 * t_alz; I = 1.0 * t_alz ** 3 / 12.0; J = t_alz ** 3 / 3.0
    Ka = (ka_coulomb(t["phi"], t["delta"], t["beta"]) if t["metodo"] == "coulomb"
          else ka_rankine(t["phi"], t["beta"]))
    if t.get("metodo_empuje", "activo") == "reposo":
        Ka = k0_reposo(t["phi"])
    gamma = t["gamma"]; q = model["sobrecarga"]
    p_soil_base = Ka * gamma * Hm        # presion del suelo en la base del alzado (N/m2)
    p_q = Ka * q                          # presion de sobrecarga (constante)
    H_head = model["coronacion"].get("H_Q_N", 0.0)

    nb = max(n, 6)
    nodos = {}; barras = {}
    dz = Hm / nb
    for i in range(nb + 1):
        nodos["N%d" % i] = {"x": 0.0, "y": 0.0, "z": i * dz, "apoyo": [0, 0, 0, 0, 0, 0]}
    nodos["N0"]["apoyo"] = [1, 1, 1, 1, 1, 1]            # empotrado en la base
    for i in range(nb):
        barras["E%d" % i] = {"ni": "N%d" % i, "nj": "N%d" % (i + 1),
                             "seccion": "ALZ", "material": "HORM", "tipo": "alzado"}
    model_alz = {"unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
                 "materiales": {"HORM": mp},
                 "secciones": {"ALZ": {"A": A, "Iy": I, "Iz": I, "J": J}},
                 "nodos": nodos, "barras": barras, "cargas": []}
    M = mallador.desde_modelo_neutro(model_alz, estabilizar_plano=True)
    # presiones del trasdos como cargas globales GX por segmento (presion media)
    for i in range(nb):
        z0 = i * dz; z1 = (i + 1) * dz; zmid = (z0 + z1) / 2.0
        d_mid = Hm - zmid                                # profundidad desde coronacion
        w_soil = p_soil_base * (d_mid / Hm)              # G
        for el in M.elementos:
            if el.eid == "E%d" % i:
                el.cargas.append({"caso": "G", "tipo": "global_uniforme", "qx": w_soil})
                el.cargas.append({"caso": "Q", "tipo": "global_uniforme", "qx": p_q})
    if H_head:
        M.add_carga_nodal("Q", "N%d" % nb, [H_head, 0.0, 0.0, 0.0, 0.0, 0.0])
    combos = {"ELU": {"G": 1.35, "Q": 1.50}, "ELS_car": {"G": 1.0, "Q": 1.0},
              "ELS_cp": {"G": 1.0, "Q": 0.0}}
    sol = M.resolver(combos)["combos"]
    out = {}
    for cb in combos:
        ef = sol[cb]["esfuerzos_barra"]["E0"]
        out[cb] = {"M_base": ef["My_i"], "V_base": ef["Vz_i"]}
    return out
