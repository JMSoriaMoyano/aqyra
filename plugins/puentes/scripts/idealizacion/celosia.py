"""
Idealizacion por BARRAS ARTICULADAS de una CELOSIA (Pratt) de tablero.

Construye el modelo neutro C5 (barras articuladas) de una celosia plana XZ: cordon
INFERIOR (tablero, z=0) y cordon SUPERIOR (z=h), montantes y diagonales (Pratt),
en `n` paneles de luz L. Las barras son `tipo:"articulado"` (el mallador les libera
la flexion -> solo axil/torsion). Apoyos isostaticos en los extremos del cordon
inferior. El trafico circula por el cordon inferior (camino del barrido movil).

Frontera (C5/C1): NO calcula la mecanica; entrega el modelo + meta. La mecanica la
resuelve `motor-fem` con la malla bloqueada a 2D (DX,DZ libres; rotaciones y fuera
de plano coaccionadas en run_all -> celosia pura). SI (N, m). Predimensionado (ICCP).
"""
from __future__ import annotations


def construir_celosia(c):
    """c = {'L','h','n','material'{E,G,nu,rho,fy},'cordon_sec','diagonal_sec',
       'montante_sec'}. Devuelve (model_C5, meta)."""
    L = float(c['L']); h = float(c['h']); n = int(c['n'])
    materiales = {'ACERO': dict(c['material'])}
    secciones = {}
    for key, sk in (('CORDON', 'cordon_sec'), ('DIAG', 'diagonal_sec'), ('MONT', 'montante_sec')):
        secciones[key] = {k: c[sk][k] for k in ('A', 'Iy', 'Iz', 'J')}
        secciones[key].setdefault('Avy', None); secciones[key].setdefault('Avz', None)

    nodos = {}; barras = {}
    p = L / n

    def add_n(nid, x, z):
        nodos[nid] = {"x": float(x), "y": 0.0, "z": float(z), "apoyo": [0, 0, 0, 0, 0, 0]}
    bot = []; top = []
    for i in range(n + 1):
        b = "B_%d" % i; t = "T_%d" % i
        add_n(b, p * i, 0.0); add_n(t, p * i, h); bot.append(b); top.append(t)
    # cordones
    for i in range(n):
        barras["CI_%d" % i] = {"ni": bot[i], "nj": bot[i + 1], "seccion": "CORDON", "material": "ACERO", "tipo": "articulado"}
        barras["CS_%d" % i] = {"ni": top[i], "nj": top[i + 1], "seccion": "CORDON", "material": "ACERO", "tipo": "articulado"}
    # montantes
    for i in range(n + 1):
        barras["M_%d" % i] = {"ni": bot[i], "nj": top[i], "seccion": "MONT", "material": "ACERO", "tipo": "articulado"}
    # diagonales Pratt (descendentes hacia el centro): mitad izq T_i-B_{i+1}, der B_i-T_{i+1}
    mid = n // 2
    for i in range(n):
        if i < mid:
            ni, nj = top[i], bot[i + 1]
        else:
            ni, nj = bot[i], top[i + 1]
        barras["D_%d" % i] = {"ni": ni, "nj": nj, "seccion": "DIAG", "material": "ACERO", "tipo": "articulado"}

    # apoyos isostaticos en extremos inferiores (DX en B_0; DZ en ambos)
    nodos[bot[0]]["apoyo"] = [1, 1, 1, 0, 0, 0]
    nodos[bot[n]]["apoyo"] = [0, 1, 1, 0, 0, 0]

    model = {"unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
             "materiales": materiales, "secciones": secciones,
             "nodos": nodos, "barras": barras, "cargas": []}
    meta = {"L": L, "h": h, "n": n, "p": p, "bot": bot, "top": top,
            "cordon_inf": ["CI_%d" % i for i in range(n)],
            "cordon_sup": ["CS_%d" % i for i in range(n)],
            "diagonales": ["D_%d" % i for i in range(n)],
            "montantes": ["M_%d" % i for i in range(n + 1)],
            "camino_inferior": list(bot), "apoyos": [bot[0], bot[n]]}
    return model, meta
