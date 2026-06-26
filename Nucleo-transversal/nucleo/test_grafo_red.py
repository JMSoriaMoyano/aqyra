"""
Micro-test del nucleo transversal (PT 4.1, Ola 4): grafo de red e ifc_utils.
Autocontenido y sin dependencias de IFC: valida interseccion / snap / troceo T/X /
union-find y la API de alto nivel construir_grafo. Exit != 0 si algo falla.

Uso:  python3 test_grafo_red.py
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import grafo_red as gr
import ifc_utils as iu

_fallos = []


def check(cond, msg):
    print(("  OK  " if cond else " FAIL ") + msg)
    if not cond:
        _fallos.append(msg)


print("== 1. RegistroNodos: fusion por tolerancia (snap) ==")
nod = gr.RegistroNodos(tol=0.06)
i0 = nod.add([0.0, 0.0, 0.0])
i1 = nod.add([6.0, 0.0, 0.0])
i2 = nod.add([6.02, 0.0, 0.0])          # a 20 mm < 60 mm -> fusiona con i1
check(i2 == i1, "extremo a 20 mm fusiona con el nudo previo (representante primero anadido)")
check(len(nod.coords) == 2, "solo 2 nudos tras la fusion")
check(abs(nod.coords[i1][0] - 6.0) < 1e-12, "conserva la coord del PRIMER punto (6.0, no 6.02)")
check(len(nod.fused) == 1 and nod.fused[0][1] > 0, "registra la fusion con su salto")

print("== 2. punto_en_segmento / proyeccion (troceo T/X con offset) ==")
a, b = [0.0, 0.0, 0.0], [6.0, 0.0, 0.0]
check(gr.punto_en_segmento([3.0, 0.05, 0.0], a, b, 0.06), "punto interior con offset 50 mm < tol 60 mm: SI")
check(not gr.punto_en_segmento([3.0, 0.05, 0.0], a, b, 0.001), "mismo punto con tol 1 mm: NO (gated por tolerancia)")
check(not gr.punto_en_segmento([0.0, 0.0, 0.0], a, b, 0.06), "extremo no es interior")
proj = gr.proyeccion([3.0, 0.05, 0.0], a, b)
check(abs(proj[0] - 3.0) < 1e-9 and abs(proj[1]) < 1e-9, "proyeccion cae en la directriz (3,0,0)")

print("== 3. construir_grafo: pasante + montante con offset (T/X) ==")
segs = [
    {"p0": [0, 0, 0], "p1": [6, 0, 0], "payload": {"n": "pasante"}},
    {"p0": [3.0, 0.05, 0], "p1": [3.0, 0.05, 3.0], "payload": {"n": "montante"}},
]
g = gr.construir_grafo(segs, tol=0.06)
check(len(g["tramos"]) == 3, "pasante troceado en 2 + montante = 3 tramos")
check(len(g["nodos"]) == 4, "4 nudos (extremos + nudo de corte compartido)")
check(len(g["metricas"]["cruces_troceados"]) == 1, "1 cruce troceado registrado")
# el montante engancha en el MISMO nudo en que se troceo el pasante
n_pas = set()
for t in g["tramos"].values():
    if t["payload"]["n"] == "pasante":
        n_pas.add(t["ni"]); n_pas.add(t["nj"])
mont = [t for t in g["tramos"].values() if t["payload"]["n"] == "montante"][0]
check(mont["ni"] in n_pas or mont["nj"] in n_pas, "el montante comparte el nudo proyectado del pasante")

print("== 4. construir_grafo: tolerancia trivial NO trocea (no-regresion) ==")
g2 = gr.construir_grafo(segs, tol=0.001)
check(len(g2["tramos"]) == 2 and len(g2["metricas"]["cruces_troceados"]) == 0,
      "con tol 1 mm no hay troceo: 2 tramos, 0 cruces")

print("== 5. filtrar_componentes_desconectadas (union-find generico) ==")
nodos = {"N1": {"apoyo": True}, "N2": {}, "N3": {}, "N4": {}}   # N3-N4 sueltos
tramos = {"T1": {"ni": "N1", "nj": "N2"}, "T2": {"ni": "N3", "nj": "N4"}}
drop_t, drop_n = gr.filtrar_componentes_desconectadas(
    nodos, tramos, lambda nm, nd: bool(nd.get("apoyo")))
check(drop_t == ["T2"], "descarta el tramo de la componente sin ancla (T2)")
check(set(drop_n) == {"N3", "N4"}, "marca huerfanos N3, N4")
# con ancla en ambas componentes no se descarta nada
nodos2 = {"N1": {"apoyo": True}, "N2": {}, "N3": {"apoyo": True}, "N4": {}}
dt2, _ = gr.filtrar_componentes_desconectadas(nodos2, tramos, lambda nm, nd: bool(nd.get("apoyo")))
check(dt2 == [], "si cada componente tiene ancla, no descarta nada")

print("== 6. ifc_utils: algebra 4x4 ==")
I = iu.ident4()
check(iu.apply(I, [1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0], "identidad no mueve el punto")
T = iu.ident4(); T[0][3] = 10.0
check(iu.apply(T, [1.0, 2.0, 3.0]) == [11.0, 2.0, 3.0], "traslacion +10 en X")
check(iu.matmul(I, T) == T, "I * T = T")
check(gr.bbox_xy([[0, 0], [6, 0], [6, 4], [0, 4]]) == (0, 6, 0, 4), "bbox_xy correcto")

print()
if _fallos:
    print("MICRO-TEST: %d FALLO(S)" % len(_fallos))
    sys.exit(1)
print("MICRO-TEST: TODO OK")
