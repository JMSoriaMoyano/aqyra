"""
Micro-test de la RED MEP (PT 4.2, Ola 4, hueco H2). Autocontenido y SIN IFC:
valida la construccion del grafo por puertos (snap/troceo) con el nucleo y la
VALIDACION DE RED (continuidad / terminales / componentes huerfanas / unidades).
Exit != 0 si algo falla.

Uso:  python3 test_red_mep.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "nucleo"))
import grafo_red as gr
import validacion_red as vr

_fallos = []


def check(cond, msg):
    print(("  OK  " if cond else " FAIL ") + msg)
    if not cond:
        _fallos.append(msg)


print("== 1. construir_grafo: union por puertos coincidentes (te de 3 vias) ==")
# T1 acaba en (10,0,0); T2 y T3 arrancan en (10,0,0) -> los puertos coinciden y
# el nucleo los fusiona en un solo nudo de union (lo que hace el parser via puertos).
segs = [
    {"p0": [0, 0, 0],  "p1": [10, 0, 0], "payload": {"elemento": "T1"}},
    {"p0": [10, 0, 0], "p1": [10, 5, 0], "payload": {"elemento": "T2"}},
    {"p0": [10, 0, 0], "p1": [20, 0, 0], "payload": {"elemento": "T3"}},
]
g = gr.construir_grafo(segs, tol=0.001)
check(len(g["tramos"]) == 3, "3 tramos (T1, T2, T3)")
check(len(g["nodos"]) == 4, "4 nodos: fuente, te compartido, 2 extremos")
# el nudo de la te es compartido por los 3 tramos
from collections import Counter
inc = Counter()
for t in g["tramos"].values():
    inc[t["ni"]] += 1
    inc[t["nj"]] += 1
check(max(inc.values()) == 3, "el nudo de la te concurre en 3 tramos")

print("== 2. construir_grafo: troceo T/X por extremo de ramal sobre pasante ==")
# un montante cuyo extremo cae en el INTERIOR del pasante -> trocea el pasante
segs2 = [
    {"p0": [0, 0, 0], "p1": [10, 0, 0], "payload": {"elemento": "pasante"}},
    {"p0": [5, 0, 0], "p1": [5, 4, 0], "payload": {"elemento": "ramal"}},
]
g2 = gr.construir_grafo(segs2, tol=0.01)
check(len(g2["tramos"]) == 3, "pasante troceado en 2 + ramal = 3 tramos")
check(len(g2["metricas"]["cruces_troceados"]) == 1, "1 cruce troceado registrado")

print("== 3. validacion de red: red conexa desde fuente -> CUMPLE ==")
modelo_ok = {
    "unidades": {"longitud": "m", "caudal": "l/s", "presion": "kPa"},
    "sistema": {"tipo": "FIRESUPPRESSION"},
    "nodos": {"N1": {"x": 0, "y": 0, "z": 0, "tipo": "fuente"},
              "N2": {"x": 10, "y": 0, "z": 0, "tipo": "union"},
              "N3": {"x": 10, "y": 5, "z": 0, "tipo": "terminal"},
              "N4": {"x": 20, "y": 0, "z": 0, "tipo": "terminal"}},
    "tramos": {"T1": {"ni": "N1", "nj": "N2"},
               "T2": {"ni": "N2", "nj": "N3"},
               "T3": {"ni": "N2", "nj": "N4"}},
    "terminales": [{"id": "BIE-1", "nodo": "N3"}, {"id": "BIE-2", "nodo": "N4"}],
    "fuentes": [{"id": "grupo", "nodo": "N1"}],
}
r = vr.validar(modelo_ok)
check(r["veredicto"] == "CUMPLE", "red conexa con fuente y terminales -> CUMPLE")
check(r["resumen"]["cobertura_pct"] == 100.0, "cobertura 100 % desde la fuente")

print("== 4. validacion: componente huerfana (sin fuente) -> NO CUMPLE ==")
modelo_huerfano = {k: (dict(v) if isinstance(v, dict) else list(v))
                   for k, v in modelo_ok.items()}
modelo_huerfano["nodos"] = dict(modelo_ok["nodos"])
modelo_huerfano["nodos"]["N5"] = {"x": 50, "y": 0, "z": 0, "tipo": "union"}
modelo_huerfano["nodos"]["N6"] = {"x": 55, "y": 0, "z": 0, "tipo": "terminal"}
modelo_huerfano["tramos"] = dict(modelo_ok["tramos"])
modelo_huerfano["tramos"]["T9"] = {"ni": "N5", "nj": "N6"}   # subgrafo suelto
r2 = vr.validar(modelo_huerfano)
check(r2["veredicto"] == "NO CUMPLE", "subgrafo sin ancla -> NO CUMPLE")
check(r2["resumen"]["huerfanas_tramos"] == 1, "detecta 1 tramo huerfano (T9)")

print("== 5. validacion: terminal desconectado -> NO CUMPLE ==")
modelo_term = {k: v for k, v in modelo_ok.items()}
modelo_term["nodos"] = dict(modelo_ok["nodos"])
modelo_term["nodos"]["N7"] = {"x": 99, "y": 0, "z": 0, "tipo": "terminal"}
modelo_term["terminales"] = list(modelo_ok["terminales"]) + [{"id": "BIE-X", "nodo": "N7"}]
r3 = vr.validar(modelo_term)
check(r3["veredicto"] == "NO CUMPLE", "terminal en nodo no alcanzable -> NO CUMPLE")

print("== 6. validacion: unidades no SI -> NO CUMPLE ==")
modelo_u = {k: v for k, v in modelo_ok.items()}
modelo_u["unidades"] = {"longitud": "mm"}
r4 = vr.validar(modelo_u)
check(r4["veredicto"] == "NO CUMPLE", "unidad de longitud != m -> NO CUMPLE")

print("== 7. validacion saneamiento: ancla en el VERTIDO (sin fuente) -> CUMPLE ==")
modelo_sane = {
    "unidades": {"longitud": "m", "caudal": "l/s", "presion": "kPa"},
    "sistema": {"tipo": "SEWAGE"},
    "nodos": {"P1": {"x": 0, "y": 0, "z": 100.5, "tipo": "terminal", "cota_solera": 100.5},
              "P3": {"x": 50, "y": 0, "z": 100.0, "tipo": "union", "cota_solera": 100.0},
              "V":  {"x": 100, "y": 0, "z": 99.5, "tipo": "vertido", "cota_solera": 99.5}},
    "tramos": {"T1": {"ni": "P1", "nj": "P3"}, "T3": {"ni": "P3", "nj": "V"}},
    "terminales": [{"id": "ACO-1", "nodo": "P1"}],
    "fuentes": [],
    "vertidos": [{"id": "VERTIDO", "nodo": "V", "tipo": "vertido"}],
}
r5 = vr.validar(modelo_sane)
check(r5["veredicto"] == "CUMPLE", "red de saneamiento anclada en el vertido -> CUMPLE")
check(r5["resumen"]["cobertura_pct"] == 100.0, "cobertura 100 % desde el vertido")

print("== 8. validacion saneamiento: sin fuente NI vertido -> NO CUMPLE ==")
modelo_sin_ancla = {k: (dict(v) if isinstance(v, dict) else list(v))
                    for k, v in modelo_sane.items()}
modelo_sin_ancla["nodos"] = {nm: dict(n) for nm, n in modelo_sane["nodos"].items()}
modelo_sin_ancla["nodos"]["V"]["tipo"] = "union"
modelo_sin_ancla["vertidos"] = []
r6 = vr.validar(modelo_sin_ancla)
check(r6["veredicto"] == "NO CUMPLE", "red sin fuente ni vertido -> NO CUMPLE")

print()
if _fallos:
    print("MICRO-TEST RED MEP: %d FALLO(S)" % len(_fallos))
    sys.exit(1)
print("MICRO-TEST RED MEP: TODO OK")
