"""
Idealizacion por BARRAS + RESORTES (suelo Winkler) de un PORTICO (marco) de paso.

Construye el modelo neutro C5 (barras) de un portico cerrado en el plano XZ: un
DINTEL horizontal (tablero) de luz L a la cota H, sobre dos PILAS (hastiales)
verticales empotradas en el dintel, con la base sobre RESORTES (cimentacion/suelo
Winkler: kx horizontal, kz vertical, kry de giro). Discretiza dintel (ne) y pilas
(np) para aplicar cargas y recuperar esfuerzos.

Frontera (C5/C1): NO calcula la mecanica; entrega el modelo + meta. La mecanica la
resuelve `motor-fem` (estabilizar_plano=True: marco plano XZ; los resortes de base
dan la estabilidad en el plano). El empuje de tierras y el 2.º orden los aplican
las acciones/comprobacion (no el nucleo). SI (N, m). Predimensionado (ICCP).
"""
from __future__ import annotations


def construir_portico(p):
    """p = {'L','H','ne','np','material'{E,G,nu,rho,fck},'dintel_sec','pila_sec',
       'suelo'{kx,kz,kry}}. Devuelve (model_C5, meta)."""
    L = float(p['L']); H = float(p['H']); ne = int(p['ne']); npil = int(p['np'])
    materiales = {'HORM': dict(p['material'])}
    secciones = {'DINTEL': {k: p['dintel_sec'][k] for k in ('A', 'Iy', 'Iz', 'J')},
                 'PILA': {k: p['pila_sec'][k] for k in ('A', 'Iy', 'Iz', 'J')}}
    for s in secciones.values():
        s.setdefault('Avy', None); s.setdefault('Avz', None)

    nodos = {}; barras = {}

    def add_n(nid, x, y, z):
        nodos[nid] = {"x": float(x), "y": float(y), "z": float(z), "apoyo": [0, 0, 0, 0, 0, 0]}

    # dintel: D0..Dne en z=H
    dintel_nodes = []
    for i in range(ne + 1):
        nid = "D_%d" % i; add_n(nid, L * i / ne, 0.0, H); dintel_nodes.append(nid)
    for i in range(ne):
        barras["DIN_%d" % i] = {"ni": dintel_nodes[i], "nj": dintel_nodes[i + 1],
                                "seccion": "DINTEL", "material": "HORM", "tipo": "dintel"}
    # pila izquierda: base PL_0 (z=0) .. tope = D_0
    pilaL = []; pilaR = []
    base_L = "PL_0"; add_n(base_L, 0.0, 0.0, 0.0); pilaL.append(base_L)
    for k in range(1, npil):
        nid = "PL_%d" % k; add_n(nid, 0.0, 0.0, H * k / npil); pilaL.append(nid)
    pilaL.append(dintel_nodes[0])
    base_R = "PR_0"; add_n(base_R, L, 0.0, 0.0); pilaR.append(base_R)
    for k in range(1, npil):
        nid = "PR_%d" % k; add_n(nid, L, 0.0, H * k / npil); pilaR.append(nid)
    pilaR.append(dintel_nodes[ne])
    pilaL_b = []; pilaR_b = []
    for k in range(npil):
        bid = "PIL_L_%d" % k; barras[bid] = {"ni": pilaL[k], "nj": pilaL[k + 1],
                                             "seccion": "PILA", "material": "HORM", "tipo": "pila"}
        pilaL_b.append(bid)
        bid = "PIL_R_%d" % k; barras[bid] = {"ni": pilaR[k], "nj": pilaR[k + 1],
                                             "seccion": "PILA", "material": "HORM", "tipo": "pila"}
        pilaR_b.append(bid)

    model = {"unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
             "materiales": materiales, "secciones": secciones,
             "nodos": nodos, "barras": barras, "cargas": []}
    meta = {"L": L, "H": H, "ne": ne, "np": npil, "dintel_nodes": dintel_nodes,
            "dintel_barras": ["DIN_%d" % i for i in range(ne)],
            "pilaL_barras": pilaL_b, "pilaR_barras": pilaR_b,
            "pilaL_nodes": pilaL, "pilaR_nodes": pilaR,
            "base_nodes": [base_L, base_R], "camino_dintel": list(dintel_nodes),
            "suelo": p["suelo"]}
    return model, meta
