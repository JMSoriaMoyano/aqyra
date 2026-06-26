"""
MICRO-TEST del solver de red electrica (REBT), analogo al micro-test del solver
hidraulico. Sin libs externas. Contrasta la caida de tension del solver contra el
calculo analitico cerrado, el balance de potencias y el redimensionado por ΔU.

  1. Tramo recto mono: I = P/(U*cosphi) y dU = 2*L*I*cosphi/(gamma*S) analiticos.
  2. Tramo recto tri:  I = P/(sqrt3*U*cosphi) y dU = sqrt3*L*I*cosphi/(gamma*S).
  3. Arbol (cuadro -> 2 circuitos): balance de potencias en la cabecera = 0.
  4. Seccion propuesta respeta la intensidad admisible (ITC-BT-19).
  5. Redimensionado por caida de tension: un circuito largo de alumbrado (limite
     3 %) sube de seccion hasta cumplir.
Uso:  python3 test_solver_electrico.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solver_electrico as E

fallos = 0


def chk(cond, msg):
    global fallos
    print(("  ok  " if cond else "  XX  ") + msg)
    if not cond:
        fallos += 1


# --- 1) tramo recto mono: solver vs analitico -------------------------------
# cuadro (230 V) -> T1 L=20 m -> 1 terminal P=4600 W mono cosphi=1.0
modelo1 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "ELECTRICAL", "demanda": {"tension_V": 230.0}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 20, "y": 0, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "longitud": 20.0, "material": "Cu"}},
    "terminales": [{"id": "R1", "nodo": "N2", "demanda": {
        "potencia_W": 4600.0, "cosphi": 1.0, "fases": "mono", "uso": "fuerza",
        "tension_V": 230.0, "du_max_pct": 5.0, "seccion_min_mm2": 1.5}}],
    "fuentes": [{"id": "CGP", "nodo": "N1", "tipo": "equipo"}],
}
r1 = E.resolver(modelo1, aislamiento="PVC", material="Cu")
t1 = r1["tramos"]["T1"]
I_an = 4600.0 / (230.0 * 1.0)
chk(abs(t1["intensidad_A"] - round(I_an, 3)) < 1e-2, "mono: I = P/(U*cosphi) = 20 A")
S1 = t1["seccion_mm2"]
gamma = E.GAMMA["CU"]
du_an = 2.0 * 20.0 * I_an * 1.0 / (gamma * S1)
chk(abs(t1["caida_tension_V"] - round(du_an, 4)) < 1e-2,
    "mono: dU tramo = 2*L*I*cosphi/(gamma*S) analitico (S=%s mm2)" % S1)
chk(t1["I_admisible_A"] >= t1["intensidad_A"], "mono: seccion respeta I admisible")

# --- 2) tramo recto tri: solver vs analitico --------------------------------
modelo2 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "ELECTRICAL", "demanda": {"tension_V": 400.0}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 30, "y": 0, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "longitud": 30.0, "material": "Cu"}},
    "terminales": [{"id": "M1", "nodo": "N2", "demanda": {
        "potencia_W": 30000.0, "cosphi": 0.85, "fases": "tri", "uso": "fuerza",
        "tension_V": 400.0, "du_max_pct": 5.0, "seccion_min_mm2": 2.5}}],
    "fuentes": [{"id": "CGP", "nodo": "N1", "tipo": "equipo"}],
}
r2 = E.resolver(modelo2, aislamiento="PVC", material="Cu")
t2 = r2["tramos"]["T1"]
I_an2 = 30000.0 / (math.sqrt(3.0) * 400.0 * 0.85)
chk(abs(t2["intensidad_A"] - round(I_an2, 3)) < 1e-1, "tri: I = P/(sqrt3*U*cosphi)")
S2 = t2["seccion_mm2"]
du_an2 = math.sqrt(3.0) * 30.0 * I_an2 * 0.85 / (gamma * S2)
chk(abs(t2["caida_tension_V"] - round(du_an2, 4)) < 1e-1,
    "tri: dU tramo = sqrt3*L*I*cosphi/(gamma*S) analitico (S=%s mm2)" % S2)
chk(t2["fases"] == "tri", "tri: el tramo se resuelve como trifasico")

# --- 3) arbol: balance de potencias en la cabecera --------------------------
modelo3 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "ELECTRICAL", "demanda": {"tension_V": 230.0}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 5, "y": 0, "z": 0, "tipo": "union"},
              "N3": {"x": 5, "y": 5, "z": 0, "tipo": "terminal"},
              "N4": {"x": 5, "y": -5, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "longitud": 5.0, "material": "Cu"},
               "T2": {"ni": "N2", "nj": "N3", "longitud": 5.0, "material": "Cu"},
               "T3": {"ni": "N2", "nj": "N4", "longitud": 5.0, "material": "Cu"}},
    "terminales": [{"id": "A1", "nodo": "N3", "demanda": {
                        "potencia_W": 1500.0, "cosphi": 0.9, "fases": "mono",
                        "uso": "alumbrado", "tension_V": 230.0, "du_max_pct": 3.0,
                        "seccion_min_mm2": 1.5}},
                   {"id": "A2", "nodo": "N4", "demanda": {
                        "potencia_W": 2500.0, "cosphi": 0.95, "fases": "mono",
                        "uso": "fuerza", "tension_V": 230.0, "du_max_pct": 5.0,
                        "seccion_min_mm2": 2.5}}],
    "fuentes": [{"id": "CGP", "nodo": "N1", "tipo": "equipo"}],
}
r3 = E.resolver(modelo3)
pT1 = r3["tramos"]["T1"]["potencia_W"]
pT2 = r3["tramos"]["T2"]["potencia_W"]
pT3 = r3["tramos"]["T3"]["potencia_W"]
chk(abs(pT1 - (pT2 + pT3)) < 1e-6, "BALANCE de potencias en la cabecera: P_T1 = P_T2 + P_T3")
chk(abs(pT1 - 4000.0) < 1e-6, "cabecera lleva 1500+2500 = 4000 W")
chk(r3["topologia"]["n_lazos"] == 0, "red radial: 0 lazos (sin malla)")
chk(r3["veredicto"] == "CUMPLE", "arbol corto: veredicto CUMPLE")

# --- 4) seccion respeta la intensidad admisible -----------------------------
chk(all((to["I_admisible_A"] or 0) >= (to["intensidad_A"] or 0)
        for to in r3["tramos"].values() if to.get("intensidad_A") is not None),
    "todas las secciones respetan I admisible")

# --- 5) redimensionado por caida de tension (circuito largo de alumbrado) ----
# T1 L=100 m, P=2300 W alumbrado cosphi 0.9, limite 3 %. La 1.5 mm2 da ~10 % ->
# el solver debe subir seccion hasta cumplir el 3 %.
modelo5 = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "ELECTRICAL", "demanda": {"tension_V": 230.0}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 100, "y": 0, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "longitud": 100.0, "material": "Cu"}},
    "terminales": [{"id": "AL", "nodo": "N2", "demanda": {
        "potencia_W": 2300.0, "cosphi": 0.9, "fases": "mono", "uso": "alumbrado",
        "tension_V": 230.0, "du_max_pct": 3.0, "seccion_min_mm2": 1.5}}],
    "fuentes": [{"id": "CGP", "nodo": "N1", "tipo": "equipo"}],
}
r5 = E.resolver(modelo5)
t5 = r5["tramos"]["T1"]
caida5 = r5["terminales"][0]["caida_acum_pct"]
chk(caida5 <= 3.0 + 1e-6, "redimensionado: caida acumulada %.2f%% <= 3%% (alumbrado)" % caida5)
chk(t5["seccion_mm2"] > 1.5, "redimensionado: seccion subida por encima de 1.5 mm2 (S=%s)" % t5["seccion_mm2"])
chk(r5["veredicto"] == "CUMPLE", "redimensionado: veredicto CUMPLE")

print("\n%d fallo(s)." % fallos)
sys.exit(1 if fallos else 0)
