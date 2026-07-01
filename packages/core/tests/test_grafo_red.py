"""Micro-test del núcleo transversal — grafo de red e ifc_utils (portado a pytest).

No-regresión de comportamiento: valida intersección / snap / troceo T/X / union-find y la
API de alto nivel `construir_grafo`. Autocontenido, sin dependencias de IFC. Es el mismo
conjunto de comprobaciones del canónico (`Nucleo-transversal/nucleo/test_grafo_red.py`),
adaptado a aserciones de pytest e importando desde el paquete `aqyra_core`.
"""
from aqyra_core import grafo_red as gr
from aqyra_core import ifc_utils as iu


def test_registro_nodos_fusion_por_tolerancia():
    nod = gr.RegistroNodos(tol=0.06)
    nod.add([0.0, 0.0, 0.0])
    i1 = nod.add([6.0, 0.0, 0.0])
    i2 = nod.add([6.02, 0.0, 0.0])  # a 20 mm < 60 mm -> fusiona con i1
    assert i2 == i1, "extremo a 20 mm fusiona con el nudo previo (representante primero añadido)"
    assert len(nod.coords) == 2, "solo 2 nudos tras la fusión"
    assert abs(nod.coords[i1][0] - 6.0) < 1e-12, "conserva la coord del PRIMER punto (6.0)"
    assert len(nod.fused) == 1 and nod.fused[0][1] > 0, "registra la fusión con su salto"


def test_punto_en_segmento_y_proyeccion():
    a, b = [0.0, 0.0, 0.0], [6.0, 0.0, 0.0]
    assert gr.punto_en_segmento([3.0, 0.05, 0.0], a, b, 0.06), "interior con offset 50 mm < tol 60 mm"
    assert not gr.punto_en_segmento([3.0, 0.05, 0.0], a, b, 0.001), "mismo punto, tol 1 mm: gated"
    assert not gr.punto_en_segmento([0.0, 0.0, 0.0], a, b, 0.06), "extremo no es interior"
    proj = gr.proyeccion([3.0, 0.05, 0.0], a, b)
    assert abs(proj[0] - 3.0) < 1e-9 and abs(proj[1]) < 1e-9, "proyección cae en la directriz"


def test_construir_grafo_troceo_tx():
    segs = [
        {"p0": [0, 0, 0], "p1": [6, 0, 0], "payload": {"n": "pasante"}},
        {"p0": [3.0, 0.05, 0], "p1": [3.0, 0.05, 3.0], "payload": {"n": "montante"}},
    ]
    g = gr.construir_grafo(segs, tol=0.06)
    assert len(g["tramos"]) == 3, "pasante troceado en 2 + montante = 3 tramos"
    assert len(g["nodos"]) == 4, "4 nudos (extremos + nudo de corte compartido)"
    assert len(g["metricas"]["cruces_troceados"]) == 1, "1 cruce troceado registrado"
    n_pas = set()
    for t in g["tramos"].values():
        if t["payload"]["n"] == "pasante":
            n_pas.add(t["ni"]); n_pas.add(t["nj"])
    mont = [t for t in g["tramos"].values() if t["payload"]["n"] == "montante"][0]
    assert mont["ni"] in n_pas or mont["nj"] in n_pas, "el montante comparte el nudo proyectado"


def test_construir_grafo_tolerancia_trivial_no_trocea():
    segs = [
        {"p0": [0, 0, 0], "p1": [6, 0, 0], "payload": {"n": "pasante"}},
        {"p0": [3.0, 0.05, 0], "p1": [3.0, 0.05, 3.0], "payload": {"n": "montante"}},
    ]
    g2 = gr.construir_grafo(segs, tol=0.001)
    assert len(g2["tramos"]) == 2 and len(g2["metricas"]["cruces_troceados"]) == 0, \
        "con tol 1 mm no hay troceo: 2 tramos, 0 cruces"


def test_filtrar_componentes_desconectadas():
    nodos = {"N1": {"apoyo": True}, "N2": {}, "N3": {}, "N4": {}}  # N3-N4 sueltos
    tramos = {"T1": {"ni": "N1", "nj": "N2"}, "T2": {"ni": "N3", "nj": "N4"}}
    drop_t, drop_n = gr.filtrar_componentes_desconectadas(
        nodos, tramos, lambda nm, nd: bool(nd.get("apoyo")))
    assert drop_t == ["T2"], "descarta el tramo de la componente sin ancla (T2)"
    assert set(drop_n) == {"N3", "N4"}, "marca huérfanos N3, N4"
    nodos2 = {"N1": {"apoyo": True}, "N2": {}, "N3": {"apoyo": True}, "N4": {}}
    dt2, _ = gr.filtrar_componentes_desconectadas(nodos2, tramos, lambda nm, nd: bool(nd.get("apoyo")))
    assert dt2 == [], "si cada componente tiene ancla, no descarta nada"


def test_ifc_utils_algebra_4x4():
    I = iu.ident4()
    assert iu.apply(I, [1.0, 2.0, 3.0]) == [1.0, 2.0, 3.0], "identidad no mueve el punto"
    T = iu.ident4(); T[0][3] = 10.0
    assert iu.apply(T, [1.0, 2.0, 3.0]) == [11.0, 2.0, 3.0], "traslación +10 en X"
    assert iu.matmul(I, T) == T, "I * T = T"
    assert gr.bbox_xy([[0, 0], [6, 0], [6, 4], [0, 4]]) == (0, 6, 0, 4), "bbox_xy correcto"
