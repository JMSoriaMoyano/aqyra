"""
Aparatos de apoyo de puente (slot C4-puentes, PT 7.3) -- traducen las REACCIONES
del tablero a la subestructura como RESORTES de 6 GdL del nucleo C5 y REPARTEN la
reaccion horizontal del tablero entre las pilas/estribos por rigidez efectiva.

Tipos:
 - ELASTOMERICO (zunchado): rigidez horizontal Kh = G*A/Te (cortante del elastomero),
   vertical Kv = Ec*A/Te (Ec = modulo de compresion efectivo, depende del factor de
   forma S), giro Kr = Ec*I/Te. G ~ 0.9 MPa (dureza 60 IRHD) [confirmar AN].
 - POT / ESFERICO: vertical RIGIDO; horizontal coaccionado o liberado segun tipo
   (fijo / guiado unidireccional / libre multidireccional); GIROS LIBERADOS.

El vector resorte sigue la convencion del nucleo C5: [kx,ky,kz,krx,kry,krz]
(0 = liberado; valor grande = RIGIDO ~ coaccion). SI (N, m). Predim. (ICCP).
"""
from __future__ import annotations
import math

K_RIGIDO = 1.0e12          # rigidez "infinita" ~ coaccion (N/m o N*m/rad)


def elastomerico(a, b, Te, t_capa=None, n_capas=None, G=0.9e6, Ec=None):
    """Apoyo elastomerico rectangular a x b (m), espesor TOTAL de elastomero Te (m).
    Kh = G*A/Te ; Kv = Ec*A/Te ; Kr = Ec*I/Te (I del area del apoyo).
    Ec: si no se da, se estima Ec = 6*G*S^2 con S = a*b/(2*(a+b)*t_capa) (factor de
    forma de una capa). Devuelve {vector,[kx,ky,kz,krx,kry,krz], Kh, Kv, S, Ec}."""
    A = a * b
    if Ec is None:
        if t_capa and n_capas:
            S = A / (2.0 * (a + b) * t_capa)            # factor de forma de una capa
        else:
            S = 10.0                                      # valor tipico [confirmar AN]
        Ec = 6.0 * G * S ** 2
    else:
        S = None
    Kh = G * A / Te
    Kv = Ec * A / Te
    Ix = a * b ** 3 / 12.0                                 # giro alrededor de X (eje long. b)
    Iy = b * a ** 3 / 12.0                                 # giro alrededor de Y (eje long. a)
    Krx = Ec * Ix / Te
    Kry = Ec * Iy / Te
    Krz = G * (Ix + Iy) / Te                               # torsion (rotacion eje vertical)
    vec = [Kh, Kh, Kv, Krx, Kry, Krz]
    return {"tipo": "elastomerico", "vector": vec, "Kh_N_m": Kh, "Kv_N_m": Kv,
            "Ec_Pa": Ec, "S": S, "a": a, "b": b, "Te": Te}


def pot(tipo="fijo"):
    """Apoyo POT/esferico. tipo in {fijo, guiado_x, guiado_y, libre}. Vertical
    RIGIDO; giros LIBERADOS (0). Devuelve {vector, tipo}."""
    R = K_RIGIDO
    if tipo == "fijo":
        vec = [R, R, R, 0.0, 0.0, 0.0]                     # ambos horizontales coaccionados
    elif tipo == "guiado_x":
        vec = [0.0, R, R, 0.0, 0.0, 0.0]                   # desliza en X, fijo en Y
    elif tipo == "guiado_y":
        vec = [R, 0.0, R, 0.0, 0.0, 0.0]                   # desliza en Y, fijo en X
    elif tipo == "libre":
        vec = [0.0, 0.0, R, 0.0, 0.0, 0.0]                 # multidireccional: solo vertical
    else:
        raise ValueError("tipo POT no reconocido: %s" % tipo)
    return {"tipo": "pot_%s" % tipo, "vector": vec}


def k_pila_horizontal(E, I, H, condicion="mensula"):
    """Rigidez horizontal en cabeza de una pila (N/m). mensula (empotrada-libre):
    k = 3EI/H^3. Para el reparto en serie con el apoyo."""
    if condicion == "mensula":
        return 3.0 * E * I / H ** 3
    if condicion == "biempotrada":
        return 12.0 * E * I / H ** 3
    return 3.0 * E * I / H ** 3


def reparto_horizontal(H_total, soportes):
    """Reparte la reaccion horizontal del tablero H_total entre soportes por su
    rigidez EFECTIVA (serie apoyo + pila). soportes = [{'id','k_apoyo','k_pila'}].
    k_eff = 1/(1/k_apoyo + 1/k_pila) (resortes en serie). Devuelve
    {id: {'k_eff','H'}}. Apoyos libres (k_apoyo=0) no toman horizontal."""
    keffs = {}
    for s in soportes:
        ka = s.get("k_apoyo", 0.0); kp = s.get("k_pila", K_RIGIDO)
        if ka <= 0:
            keff = 0.0
        elif kp <= 0:
            keff = 0.0
        else:
            keff = 1.0 / (1.0 / ka + 1.0 / kp)
        keffs[s["id"]] = keff
    tot = sum(keffs.values())
    out = {}
    for s in soportes:
        keff = keffs[s["id"]]
        out[s["id"]] = {"k_eff_N_m": keff, "H_N": (H_total * keff / tot) if tot else 0.0}
    return out


def reacciones_desde_caso(r):
    """Modo 'dato del caso': normaliza las reacciones del tablero que aporta el caso.
    r = {'N_G_N','N_LM1_N','H_frenado_N'(opc),'H_viento_N'(opc),'H_termica_N'(opc),
         'M_G_Nm'(opc),'M_LM1_Nm'(opc)}. Devuelve dict estandar."""
    return {
        "modo": "caso",
        "N_G_N": float(r.get("N_G_N", 0.0)),
        "N_LM1_N": float(r.get("N_LM1_N", 0.0)),
        "H_frenado_N": float(r.get("H_frenado_N", 0.0)),
        "H_viento_N": float(r.get("H_viento_N", 0.0)),
        "H_termica_N": float(r.get("H_termica_N", 0.0)),
        "M_G_Nm": float(r.get("M_G_Nm", 0.0)),
        "M_LM1_Nm": float(r.get("M_LM1_Nm", 0.0)),
    }


def reacciones_desde_tablero(resultado_tablero, apoyo_id):
    """Modo 'acoplado': extrae las reacciones de un resultado de tablero (PT 7.1/7.2)
    para el apoyo `apoyo_id`. Lee la reaccion vertical permanente y la envolvente
    LM1 (objetivos R_apoyo_v* del barrido movil). Devuelve dict estandar.

    Soporta el resultado de vigas pretensadas (claves 'reacciones_perm' y
    'envolventes' con 'R_apoyo_v%d') o un dict generico {'N_G_N','N_LM1_N',...}."""
    if all(k in resultado_tablero for k in ("N_G_N", "N_LM1_N")):
        d = reacciones_desde_caso(resultado_tablero); d["modo"] = "acoplado(dict)"; return d
    N_G = 0.0; N_LM1 = 0.0
    reac = resultado_tablero.get("reacciones_perm") or resultado_tablero.get("reacciones") or {}
    if apoyo_id in reac:
        v = reac[apoyo_id]
        N_G = abs(v[2] if isinstance(v, (list, tuple)) else v)
    env = (resultado_tablero.get("envolventes") or {})
    key = "R_apoyo_%s" % apoyo_id
    if key in env:
        e = env[key]; N_LM1 = max(abs(e.get("max", 0.0)), abs(e.get("min", 0.0)))
    return {"modo": "acoplado", "N_G_N": N_G, "N_LM1_N": N_LM1,
            "H_frenado_N": float(resultado_tablero.get("H_frenado_N", 0.0)),
            "H_viento_N": 0.0, "H_termica_N": 0.0, "M_G_Nm": 0.0, "M_LM1_Nm": 0.0}
