"""
Idealizacion por LAMINA (placa DKMQ) de una LOSA POSTESADA de tablero.

Construye DIRECTAMENTE un `ModeloFEM` del nucleo `motor-fem` (C5): malla
estructurada nx x ny de laminas DKMQ (con su `rho` para el modal) sobre el plano
del tablero, apoyada de forma SIMPLE en los dos bordes transversales (estribos).
Opcionalmente, vigas de borde como barras longitudinales.

Frontera (C5/C1): NO calcula la mecanica; entrega el `ModeloFEM` para resolver
con `motor-fem`. La PRECOMPRESION del postesado se trata como (a) carga
equivalente vertical hacia arriba `w_p` (balance de cargas 2D) y (b) tension
axil `sigma_cp` ANALITICA en la comprobacion EC2 -> la membrana de la placa se
BLOQUEA (DX,DY,RZ) y la placa trabaja a FLEXION pura (reparto + envolventes LM1).

Convencion: X = vano longitudinal, Y = ancho; Z vertical, gravedad -Z. El momento
de VANO (longitudinal) es `Mx`; el TRANSVERSAL es `My` (esfuerzos de placa por
unidad de ancho). Carga de gravedad como presion p<0 (hacia abajo); postesado
p>0 (hacia arriba). SI (N, m). Predimensionado/asistencia; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
sys.path.insert(0, os.environ.get("MOTOR_FEM_SCRIPTS", ""))
from fem_core import ModeloFEM, ElementoLamina, ElementoBarra  # motor-fem (C5)


def construir_losa(tablero):
    """tablero = {'L','B','t','nx','ny','material'{E,nu,rho,fck,...},
       'viga_borde'(opc){A,Iy,Iz,J}}. Devuelve (M:ModeloFEM, meta)."""
    L = float(tablero['L']); B = float(tablero['B']); t = float(tablero['t'])
    nx = int(tablero['nx']); ny = int(tablero['ny'])
    mat = tablero['material']; E = mat['E']; nu = mat['nu']; rho = mat.get('rho', 2500.0)

    M = ModeloFEM()
    xs = [L * i / nx for i in range(nx + 1)]
    ys = [B * j / ny for j in range(ny + 1)]
    nid = lambda i, j: "N_%d_%d" % (i, j)
    for j in range(ny + 1):
        for i in range(nx + 1):
            M.add_nodo(nid(i, j), xs[i], ys[j], 0.0)
    laminas = {}
    for j in range(ny):
        for i in range(nx):
            eid = "Q_%d_%d" % (i, j)
            el = ElementoLamina(eid, [nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)],
                                [(xs[i], ys[j], 0), (xs[i + 1], ys[j], 0),
                                 (xs[i + 1], ys[j + 1], 0), (xs[i], ys[j + 1], 0)], t, E, nu)
            el.rho = rho
            M.add_elemento(el)
            laminas[eid] = (i, j)

    # apoyos: SS en los dos bordes transversales (x=0, x=L); membrana+drilling
    # bloqueados en toda la malla (la precompresion se trata analiticamente).
    nodos_apoyo = []
    for j in range(ny + 1):
        for i in range(nx + 1):
            ap = [1, 1, 0, 0, 0, 1]            # DX,DY,RZ bloqueados
            if i == 0 or i == nx:
                ap[2] = 1                       # DZ en estribos
                nodos_apoyo.append(nid(i, j))
            M.set_apoyo(nid(i, j), ap)

    # vigas de borde (opcional) como barras longitudinales en y=0 y y=B
    vigas_borde = []
    vb = tablero.get('viga_borde')
    if vb:
        sec = {"A": vb["A"], "Iy": vb["Iy"], "Iz": vb["Iz"], "J": vb["J"],
               "Avy": vb.get("Avy"), "Avz": vb.get("Avz")}
        matd = {"E": E, "G": mat.get("G", E / (2 * (1 + nu))), "nu": nu, "rho": rho}
        for jb in (0, ny):
            for i in range(nx):
                bid = "VB_%d_%d" % (jb, i)
                a, b = nid(i, jb), nid(i + 1, jb)
                el = ElementoBarra(bid, a, b, M.nodos[a], M.nodos[b], matd, sec)
                M.add_elemento(el); vigas_borde.append(bid)

    mid_i = nx // 2
    # franja longitudinal central (elementos del centro de vano, todas las bandas y)
    franja_centro = ["Q_%d_%d" % (mid_i - 1, j) for j in range(ny)]
    meta = {"L": L, "B": B, "t": t, "nx": nx, "ny": ny, "xs": xs, "ys": ys,
            "nid_grid": [[nid(i, j) for i in range(nx + 1)] for j in range(ny + 1)],
            "laminas": laminas, "nodos_apoyo": nodos_apoyo, "mid_i": mid_i,
            "franja_centro": franja_centro, "vigas_borde": vigas_borde}
    return M, meta


def caminos_carriles(meta, n_carriles=None):
    """Lineas longitudinales de nodos (un camino por carril LM1), centradas en Y."""
    ny = meta["ny"]; B = meta["B"]; ys = meta["ys"]; grid = meta["nid_grid"]
    if n_carriles is None:
        n_carriles = min(3, max(1, int(B // 3.0)))
    # calzada de n*3 m CENTRADA en el ancho (deja arcenes/bordillos en los
    # bordes -> las ruedas no caen en el borde libre, donde irian vigas de borde)
    ANCHO = 3.0
    start = (B - n_carriles * ANCHO) / 2.0
    centros = [start + ANCHO * (k + 0.5) for k in range(n_carriles)]
    caminos = []
    for k, yc in enumerate(centros):
        jrow = min(range(ny + 1), key=lambda j: abs(ys[j] - yc))
        caminos.append({"id": "carril%d" % (k + 1), "jrow": jrow,
                        "camino": [grid[jrow][i] for i in range(meta["nx"] + 1)]})
    return caminos
