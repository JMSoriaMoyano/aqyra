"""
Idealizacion de una PILA de puente como COLUMNA (barra 3D) con APARATO DE APOYO en
cabeza y CIMENTACION (resorte Winkler) en base, para el motor-fem (C5).

Columna vertical en el plano XZ (x=0, y=0, z de 0 a H): base P_0 (z=0) sobre
resorte de suelo [kx,kz,kry]; cabeza P_np (z=H) donde el aparato de apoyo (resorte
opcional) recibe las reacciones del tablero como cargas NODALES. Discretiza la pila
(np segmentos) para aplicar viento y recuperar esfuerzos.

Frontera (C5/C1): NO calcula la mecanica; entrega el modelo neutro + meta. La
mecanica la resuelve `motor-fem` (estabilizar_plano=True: pila plana XZ; los
resortes dan la estabilidad). El 2.o orden lo aplica la comprobacion (amplificacion
aproximada). SI (N, m). Predimensionado (ICCP).
"""
from __future__ import annotations


def construir_pila(p):
    """p = {'H','np','material'{E,G,nu,rho,fck},'pila_sec'{A,Iy,Iz,J,...},
       'suelo'{kx,kz,kry}}. Devuelve (model_C5, meta)."""
    H = float(p['H']); npil = int(p.get('np', 6))
    materiales = {'HORM': dict(p['material'])}
    secciones = {'PILA': {k: p['pila_sec'][k] for k in ('A', 'Iy', 'Iz', 'J')}}
    for s in secciones.values():
        s.setdefault('Avy', None); s.setdefault('Avz', None)

    nodos = {}; barras = {}

    def add_n(nid, z):
        nodos[nid] = {"x": 0.0, "y": 0.0, "z": float(z), "apoyo": [0, 0, 0, 0, 0, 0]}

    pila_nodes = []
    for k in range(npil + 1):
        nid = "P_%d" % k; add_n(nid, H * k / npil); pila_nodes.append(nid)
    pila_barras = []
    for k in range(npil):
        bid = "PIL_%d" % k
        barras[bid] = {"ni": pila_nodes[k], "nj": pila_nodes[k + 1],
                       "seccion": "PILA", "material": "HORM", "tipo": "pila"}
        pila_barras.append(bid)

    model = {"unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
             "materiales": materiales, "secciones": secciones,
             "nodos": nodos, "barras": barras, "cargas": []}
    meta = {"H": H, "np": npil, "pila_nodes": pila_nodes, "pila_barras": pila_barras,
            "base_node": pila_nodes[0], "head_node": pila_nodes[-1],
            "suelo": p["suelo"]}
    return model, meta
