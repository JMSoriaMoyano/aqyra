"""
MICRO-TEST del vertical de ABASTECIMIENTO a presion (EN 805). Disciplina
`obras-lineales`, PT 6.3 (Ola 6). STDLIB pura (no abre IFC). Gemelo a presion del
`test_obras_hidraulicas.py` (saneamiento, lamina libre).

Cubre:
  1. DEPOSITO POR COTA: la carga estatica nace de rho*g*dz (presion fuente = 0);
     la presion disponible aguas abajo = ganancia por cota - perdidas Darcy.
  2. Reparto en ARBOL: balance de caudales en la te (continuidad).
  3. MALLA simetrica (Hardy-Cross): reparto 50/50 y cierre de lazo ~ 0.
  4. NEGATIVO presion insuficiente: deposito demasiado bajo -> NO CUMPLE.
  5. NEGATIVO velocidad excesiva: DN pequeno y caudal alto -> v > v_max.
  6. NEGATIVO DN insuficiente: run_all con DN < DN_min -> NO CUMPLE.
  7. BASES de demanda: acometida (dotacion*hab*punta), hidrante (caudal de
     incendio sin consumo domestico) y fuente deposito (presion 0 inyectada).
Uso:  python3 test_abastecimiento.py
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import solver_presion as S
import bases_abastecimiento as B
import run_all_abastecimiento as R

fallos = 0


def chk(cond, msg):
    global fallos
    print(("  ok  " if cond else "  XX  ") + msg)
    if not cond:
        fallos += 1


# --- 1) DEPOSITO POR COTA: carga estatica = rho*g*dz ------------------------
# deposito (lamina) en N1 a z=30, presion 0; terminal N2 a z=0 -> p ~ +293.7 kPa.
modelo_dep = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": {}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 30.0, "tipo": "fuente"},
              "N2": {"x": 100, "y": 0, "z": 0.0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 150.0, "rugosidad": 0.1,
                      "longitud": 100.0}},
    "terminales": [{"id": "A1", "nodo": "N2",
                    "demanda": {"caudal_l_s": 5.0, "presion_din_min_kPa": 250.0}}],
    "fuentes": [{"id": "DEP", "nodo": "N1", "presion": 0.0}],
}
r1 = S.resolver(modelo_dep, k_acc=1.0)
dp_z = S.RHO * S.G * (0.0 - 30.0) / 1000.0          # kPa (negativo: ganancia)
dp_t = r1["tramos"]["T1"]["dp_kPa"]
p_n2 = r1["nodos"]["N2"]["presion_kPa"]
chk(abs(p_n2 - (0.0 - dp_t - dp_z)) < 1e-2,
    "deposito por cota: presion N2 = carga estatica (rho*g*dz) - perdidas")
chk(p_n2 > 250.0 and r1["veredicto"] == "CUMPLE",
    "deposito alto (30 m): presion disponible >= 250 kPa -> CUMPLE")

# --- 2) ARBOL: balance de caudales en la te ---------------------------------
modelo_arbol = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": {}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 40.0, "tipo": "fuente"},
              "N2": {"x": 50, "y": 0, "z": 0.0, "tipo": "union"},
              "N3": {"x": 50, "y": 30, "z": 0.0, "tipo": "terminal"},
              "N4": {"x": 50, "y": -30, "z": 0.0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 150.0, "rugosidad": 0.1, "longitud": 50.0},
               "T2": {"ni": "N2", "nj": "N3", "dn": 100.0, "rugosidad": 0.1, "longitud": 30.0},
               "T3": {"ni": "N2", "nj": "N4", "dn": 100.0, "rugosidad": 0.1, "longitud": 30.0}},
    "terminales": [{"id": "A1", "nodo": "N3", "demanda": {"caudal_l_s": 4.0, "presion_din_min_kPa": 250.0}},
                   {"id": "A2", "nodo": "N4", "demanda": {"caudal_l_s": 3.0, "presion_din_min_kPa": 250.0}}],
    "fuentes": [{"id": "DEP", "nodo": "N1", "presion": 0.0}],
}
r2 = S.resolver(modelo_arbol)
chk(abs(r2["tramos"]["T1"]["caudal_l_s"] - 7.0) < 1e-6, "T1 cabecera = 7.0 l/s (4+3)")
chk(abs(r2["tramos"]["T1"]["caudal_l_s"]
        - (r2["tramos"]["T2"]["caudal_l_s"] + r2["tramos"]["T3"]["caudal_l_s"])) < 1e-9,
    "BALANCE en la te: Q_T1 = Q_T2 + Q_T3")
chk(r2["topologia"]["n_lazos"] == 0 and r2["veredicto"] == "CUMPLE",
    "red en arbol (0 lazos): CUMPLE")

# --- 3) MALLA simetrica: Hardy-Cross 50/50 ----------------------------------
modelo_malla = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": {"n_simultaneas": 1}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 10, "y": 5, "z": 0, "tipo": "union"},
              "N3": {"x": 20, "y": 0, "z": 0, "tipo": "terminal"},
              "N4": {"x": 10, "y": -5, "z": 0, "tipo": "union"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 100.0, "rugosidad": 0.1, "longitud": 11.18},
               "T2": {"ni": "N2", "nj": "N3", "dn": 100.0, "rugosidad": 0.1, "longitud": 11.18},
               "T3": {"ni": "N1", "nj": "N4", "dn": 100.0, "rugosidad": 0.1, "longitud": 11.18},
               "T4": {"ni": "N4", "nj": "N3", "dn": 100.0, "rugosidad": 0.1, "longitud": 11.18}},
    "terminales": [{"id": "A1", "nodo": "N3",
                    "demanda": {"caudal_l_s": 10.0, "presion_din_min_kPa": 100.0}}],
    "fuentes": [{"id": "BOMBEO", "nodo": "N1", "presion": 600.0}],
}
r3 = S.resolver(modelo_malla, activos=["A1"])
chk(r3["topologia"]["n_lazos"] == 1, "malla 1 lazo detectada")
chk(abs(r3["tramos"]["T1"]["caudal_l_s"] - 5.0) < 1e-3
    and abs(r3["tramos"]["T3"]["caudal_l_s"] - 5.0) < 1e-3,
    "reparto SIMETRICO 50/50 por las dos ramas (5.0 l/s c/u)")
chk(abs(r3["hardy_cross"]["residuo_lazo_max_kPa"]) < 1e-3,
    "CIERRE de lazo ~ 0 (Hardy-Cross)")

# --- 4) NEGATIVO: presion insuficiente (deposito demasiado bajo) ------------
modelo_bajo = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": {}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 5.0, "tipo": "fuente"},
              "N2": {"x": 100, "y": 0, "z": 0.0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 150.0, "rugosidad": 0.1, "longitud": 100.0}},
    "terminales": [{"id": "A1", "nodo": "N2",
                    "demanda": {"caudal_l_s": 5.0, "presion_din_min_kPa": 250.0}}],
    "fuentes": [{"id": "DEP", "nodo": "N1", "presion": 0.0}],
}
r4 = S.resolver(modelo_bajo, k_acc=1.0)
chk(r4["veredicto"] == "NO CUMPLE", "deposito bajo (5 m): NO CUMPLE")
chk(r4["terminales"][0]["cumple"] is False, "terminal A1 no alcanza 250 kPa")

# --- 5) NEGATIVO: velocidad excesiva (DN pequeno, caudal alto) --------------
modelo_vel = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": {}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 80.0, "tipo": "fuente"},
              "N2": {"x": 50, "y": 0, "z": 0.0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 50.0, "rugosidad": 0.1, "longitud": 50.0}},
    "terminales": [{"id": "A1", "nodo": "N2",
                    "demanda": {"caudal_l_s": 10.0, "presion_din_min_kPa": 100.0}}],
    "fuentes": [{"id": "DEP", "nodo": "N1", "presion": 0.0}],
}
r5 = S.resolver(modelo_vel, v_max=R.V_MAX_DEF)   # v_max = 2.0 m/s
v_pico = r5["velocidad_pico_m_s"]
chk(v_pico > 2.0 and r5["veredicto"] == "NO CUMPLE",
    "DN50 con 10 l/s: v %.2f m/s > 2.0 -> NO CUMPLE" % v_pico)

# --- 6) NEGATIVO: DN insuficiente (run_all, _comprob_extra) -----------------
modelo_dn = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": {}},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 60.0, "tipo": "fuente"},
              "N2": {"x": 50, "y": 0, "z": 0.0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 50.0, "rugosidad": 0.1,
                      "longitud": 50.0, "elemento": "COND-1"}},
    "terminales": [{"id": "A1", "nodo": "N2", "caudal_min": 2.0,
                    "demanda": None}],
    "fuentes": [{"id": "DEP", "nodo": "N1", "presion": None}],
}
m6, res6, ver6, map6 = R.run(modelo_dn, dn_min=80.0, incendio=False)
chk(ver6["veredicto"] == "NO CUMPLE", "DN50 < DN_min 80 -> NO CUMPLE (run_all)")
chk(any("DN" in e for e in ver6["errores"]), "el error reporta el DN insuficiente")
chk(m6["red"]["norma"] == "EN 805", "gancho `red` con norma EN 805 relleno")

# --- 7) BASES de demanda: acometida, hidrante y fuente deposito -------------
modelo_bases = {
    "unidades": {"longitud": "m"},
    "sistema": {"tipo": "WATERSUPPLY", "demanda": None},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 25.0, "tipo": "fuente"},
              "N2": {"x": 50, "y": 0, "z": 0.0, "tipo": "terminal"},
              "N3": {"x": 80, "y": 0, "z": 0.0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2", "dn": 150.0, "longitud": 50.0},
               "T2": {"ni": "N2", "nj": "N3", "dn": 100.0, "longitud": 30.0}},
    "terminales": [{"id": "ACO-1", "nodo": "N2", "habitantes_eq": 100, "demanda": None},
                   {"id": "HIDRANTE-1", "nodo": "N3", "demanda": None}],
    "fuentes": [{"id": "DEP", "nodo": "N1", "presion": None}],
}
mb = B.aplicar_demanda(modelo_bases)   # deposito + incendio por defecto
d_aco = next(t["demanda"] for t in mb["terminales"] if t["id"] == "ACO-1")
d_hid = next(t["demanda"] for t in mb["terminales"] if t["id"] == "HIDRANTE-1")
q_med_esp = 200.0 * 100 / 86400.0
chk(abs(d_aco["caudal_l_s"] - q_med_esp * 2.5) < 1e-3,
    "acometida: Q = dotacion*hab*punta (%.3f l/s)" % (q_med_esp * 2.5))
chk(abs(d_hid["caudal_consumo_l_s"]) < 1e-9 and abs(d_hid["caudal_incendio_l_s"] - 16.7) < 1e-6,
    "hidrante: sin consumo domestico, solo caudal de incendio 16.7 l/s")
chk(mb["fuentes"][0]["presion"] == 0.0 and mb["fuentes"][0]["modelo_fuente"] == "deposito",
    "fuente deposito: presion 0 inyectada (carga por cota)")

print("\n%d fallo(s)." % fallos)
sys.exit(1 if fallos else 0)
