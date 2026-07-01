"""
MICRO-TEST del solver hidraulico de red (balance de caudales y presiones), analogo
al micro-test del nucleo y al cierre de equilibrio estructural. Sin libs externas.

  1. Tramo recto unico: contrasta la perdida Darcy-Weisbach del solver contra el
     calculo analitico cerrado (mismo f) -> error ~0.
  2. Red en arbol (1 fuente -> te -> 2 ramales): balance de caudales en la te = 0,
     reparto correcto, presion en terminales = fuente - perdidas.
  3. Friccion: laminar (Re<2000) f=64/Re; turbulento Swamee-Jain monotono.
Uso:  python3 test_solver_red.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solver_red as S

fallos = 0


def chk(cond, msg):
    global fallos
    print(("  ok  " if cond else "  XX  ") + msg)
    if not cond:
        fallos += 1


# --- 1) friccion ------------------------------------------------------------
chk(abs(S.factor_friccion(1000.0, 1e-3) - 64.0 / 1000.0) < 1e-12,
    "laminar f=64/Re")
f1 = S.factor_friccion(1e5, 1e-3)
f2 = S.factor_friccion(1e5, 5e-3)
chk(0.0 < f1 < 0.1 and f2 > f1, "turbulento Swamee-Jain crece con la rugosidad")

# --- 2) tramo recto unico: solver vs analitico ------------------------------
# fuente p=600 kPa -> 1 tramo DN100 L=10 m -> 1 terminal q=6.6 l/s, p_min=0
modelo1 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "FIREPROTECTION", "demanda": {"n_simultaneas": 1}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 10, "y": 0, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 100.0, "rugosidad": 0.045,
                      "longitud": 10.0}},
    "terminales": [{"id": "B1", "nodo": "N2",
                    "demanda": {"caudal_l_s": 6.6, "presion_din_min_kPa": 0.0}}],
    "fuentes": [{"id": "G", "nodo": "N1", "presion": 600.0}],
}
r1 = S.resolver(modelo1, k_acc=1.0)   # sin mayoracion para contrastar analitico
t1 = r1["tramos"]["T1"]
Q = 6.6 / 1000.0
D = 0.1
A = math.pi * D * D / 4.0
v = Q / A
Re = v * D / S.NU
f = S.factor_friccion(Re, (0.045 / 1000.0) / D)
hf = f * (10.0 / D) * v * v / (2.0 * S.G)
dp_an = S.RHO * S.G * hf / 1000.0
chk(abs(t1["dp_kPa"] - round(dp_an, 4)) < 1e-3, "tramo recto: dp solver == analitico")
chk(abs(t1["velocidad_m_s"] - round(v, 4)) < 1e-3, "tramo recto: velocidad correcta")
p_term = r1["terminales"][0]["presion_disponible_kPa"]
chk(abs(p_term - (600.0 - dp_an)) < 1e-3, "presion terminal = fuente - perdida")

# --- 3) red en arbol: balance de caudales en la te --------------------------
modelo2 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "FIREPROTECTION", "demanda": {"n_simultaneas": 2}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 10, "y": 0, "z": 0, "tipo": "union"},
              "N3": {"x": 10, "y": 5, "z": 0, "tipo": "terminal"},
              "N4": {"x": 10, "y": -5, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 100.0, "rugosidad": 0.045, "longitud": 10.0},
               "T2": {"ni": "N2", "nj": "N3", "dn": 65.0, "rugosidad": 0.045, "longitud": 5.0},
               "T3": {"ni": "N2", "nj": "N4", "dn": 65.0, "rugosidad": 0.045, "longitud": 5.0}},
    "terminales": [{"id": "B1", "nodo": "N3", "demanda": {"caudal_l_s": 3.3, "presion_din_min_kPa": 200.0}},
                   {"id": "B2", "nodo": "N4", "demanda": {"caudal_l_s": 3.3, "presion_din_min_kPa": 200.0}}],
    "fuentes": [{"id": "G", "nodo": "N1", "presion": 600.0}],
}
r2 = S.resolver(modelo2)
qT1 = r2["tramos"]["T1"]["caudal_l_s"]
qT2 = r2["tramos"]["T2"]["caudal_l_s"]
qT3 = r2["tramos"]["T3"]["caudal_l_s"]
chk(abs(qT1 - 6.6) < 1e-6, "T1 (cabecera) lleva 6.6 l/s (suma de ramales)")
chk(abs(qT2 - 3.3) < 1e-6 and abs(qT3 - 3.3) < 1e-6, "ramales 3.3 l/s cada uno")
chk(abs(qT1 - (qT2 + qT3)) < 1e-9, "BALANCE en la te: Q_T1 = Q_T2 + Q_T3 (residuo 0)")
chk(r2["veredicto"] == "CUMPLE", "red en arbol: veredicto CUMPLE")
chk(r2["topologia"]["n_lazos"] == 0, "red en arbol: 0 lazos (sin Hardy-Cross)")

# --- 4) MALLA de 1 lazo SIMETRICA: reparto analitico 50/50 (Hardy-Cross) -----
# fuente N1 -> dos caminos paralelos IDENTICOS N1-N2-N3 y N1-N4-N3 -> demanda en N3.
modelo3 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "FIREPROTECTION", "demanda": {"n_simultaneas": 1}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 10, "y": 5, "z": 0, "tipo": "union"},
              "N3": {"x": 20, "y": 0, "z": 0, "tipo": "terminal"},
              "N4": {"x": 10, "y": -5, "z": 0, "tipo": "union"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 80.0, "rugosidad": 0.045, "longitud": 11.18},
               "T2": {"ni": "N2", "nj": "N3", "dn": 80.0, "rugosidad": 0.045, "longitud": 11.18},
               "T3": {"ni": "N1", "nj": "N4", "dn": 80.0, "rugosidad": 0.045, "longitud": 11.18},
               "T4": {"ni": "N4", "nj": "N3", "dn": 80.0, "rugosidad": 0.045, "longitud": 11.18}},
    "terminales": [{"id": "R1", "nodo": "N3",
                    "demanda": {"caudal_l_s": 10.0, "presion_din_min_kPa": 100.0}}],
    "fuentes": [{"id": "G", "nodo": "N1", "presion": 600.0}],
}
r3 = S.resolver(modelo3, activos=["R1"])
chk(r3["topologia"]["n_lazos"] == 1, "malla 1 lazo detectada (m-n+c = 1)")
chk(abs(r3["tramos"]["T1"]["caudal_l_s"] - 5.0) < 1e-3
    and abs(r3["tramos"]["T3"]["caudal_l_s"] - 5.0) < 1e-3,
    "reparto SIMETRICO 50/50 por las dos ramas (5.0 l/s c/u)")
chk(abs(r3["hardy_cross"]["residuo_lazo_max_kPa"]) < 1e-3,
    "CIERRE de lazo (Sigma perdidas) ~ 0 [Hardy-Cross]")

# --- 5) MALLA de 2 lazos (rejilla 2x2): balance nodal + cierre por lazo ------
modelo4 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "FIREPROTECTION", "demanda": {"n_simultaneas": 2}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 10, "y": 0, "z": 0, "tipo": "union"},
              "N3": {"x": 20, "y": 0, "z": 0, "tipo": "union"},
              "N4": {"x": 20, "y": -10, "z": 0, "tipo": "terminal"},
              "N5": {"x": 10, "y": -10, "z": 0, "tipo": "union"},
              "N6": {"x": 0, "y": -10, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 100.0, "rugosidad": 0.045, "longitud": 10.0},
               "T2": {"ni": "N2", "nj": "N3", "dn": 80.0, "rugosidad": 0.045, "longitud": 10.0},
               "T3": {"ni": "N3", "nj": "N4", "dn": 65.0, "rugosidad": 0.045, "longitud": 10.0},
               "T4": {"ni": "N4", "nj": "N5", "dn": 65.0, "rugosidad": 0.045, "longitud": 10.0},
               "T5": {"ni": "N5", "nj": "N6", "dn": 80.0, "rugosidad": 0.045, "longitud": 10.0},
               "T6": {"ni": "N6", "nj": "N1", "dn": 100.0, "rugosidad": 0.045, "longitud": 10.0},
               "T7": {"ni": "N2", "nj": "N5", "dn": 65.0, "rugosidad": 0.045, "longitud": 10.0}},
    "terminales": [{"id": "RA", "nodo": "N4", "demanda": {"caudal_l_s": 6.0, "presion_din_min_kPa": 50.0}},
                   {"id": "RB", "nodo": "N6", "demanda": {"caudal_l_s": 6.0, "presion_din_min_kPa": 50.0}}],
    "fuentes": [{"id": "G", "nodo": "N1", "presion": 600.0}],
}
r4 = S.resolver(modelo4, activos=["RA", "RB"])
chk(r4["topologia"]["n_lazos"] == 2, "malla 2 lazos detectada (7-6+1 = 2)")
chk(all(abs(x) < 1e-3 for x in r4["hardy_cross"]["residuos_lazo_kPa"]),
    "ambos lazos cierran (Sigma perdidas ~ 0)")
# balance nodal estricto con caudal con signo
net = {nm: 0.0 for nm in r4["nodos"]}
for tid, to in r4["tramos"].items():
    qs = to["caudal_signed_l_s"]
    net[to["ni"]] -= qs
    net[to["nj"]] += qs
chk(abs(net["N2"]) < 1e-6 and abs(net["N3"]) < 1e-6 and abs(net["N5"]) < 1e-6,
    "BALANCE en nudos de union (N2,N3,N5) ~ 0 con caudal con signo")
chk(abs(net["N4"] - 6.0) < 1e-6 and abs(net["N6"] - 6.0) < 1e-6,
    "terminales N4,N6 reciben su demanda (6.0 l/s)")
chk(abs(net["N1"] + 12.0) < 1e-6, "fuente N1 inyecta el caudal total (12.0 l/s)")

print("\n%d fallo(s)." % fallos)
sys.exit(1 if fallos else 0)
