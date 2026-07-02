"""
Idealizacion por LAMINA de un tablero OBLICUO (esviado). PT 7.5 (Ola 7).

Tablero de losa (o lamina metalica) cuyos apoyos NO son perpendiculares al eje:
la linea de apoyo forma un angulo de esviaje phi con la normal al eje. Se malla
con una malla ROMBOIDAL que SIGUE la linea de apoyo oblicua (cuadrilateros
distorsionados que la lamina curva MITC4 admite de forma nativa). Decision PT 7.5:
malla romboidal (mejor captura del flujo hacia la esquina OBTUSA) frente a malla
ortogonal con borde recortado.

Parametrizacion del paralelogramo: nudo (i,j) en
   x_ij = y_j*tan(phi) + i*L/nx ,  y_j = -B/2 + j*B/ny ,  z = 0
de modo que las lineas i=0 e i=nx son las dos LINEAS DE APOYO esviadas. Eje X
longitudinal, Y transversal, Z vertical (gravedad -Z). Nudos fundidos por coord.

Devuelve (M:ModeloFEM, meta) con paneles, nudos de apoyo por linea, esquinas,
secciones criticas y caminos de carril. El motor-fem NO se toca. SI (N, m).
Predimensionado/asistencia; revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import os, sys, math
import numpy as np
sys.path.insert(0, os.environ.get("MOTOR_FEM_SCRIPTS", ""))
from fem_core import ModeloFEM
from fem2 import ElementoLaminaCurva

G_ACC = 9.81


def construir_oblicuo(obl):
    """obl = {'L'(luz recta),'B'(ancho),'esviaje_deg'(phi),'t'(espesor losa),
       'nx','ny','material'{E,nu,rho,fck?,fyk?},'n_carriles'?}. Devuelve (M, meta)."""
    L = float(obl["L"]); B = float(obl["B"]); phi = math.radians(float(obl.get("esviaje_deg", 0.0)))
    t = float(obl["t"]); nx = int(obl.get("nx", 14)); ny = int(obl.get("ny", 10))
    mat = obl["material"]; E = mat["E"]; nu = mat["nu"]; rho = mat.get("rho", 2500.0)
    tan = math.tan(phi)

    xs = np.linspace(0.0, L, nx + 1)
    ys = np.linspace(-B / 2, B / 2, ny + 1)

    M = ModeloFEM(); reg = {}; grid = {}
    def node(x, y):
        key = (round(x, 4), round(y, 4), 0.0)
        if key not in reg:
            nm = "N%d" % len(reg); reg[key] = nm; M.add_nodo(nm, x, y, 0.0)
        return reg[key]
    for i, xc in enumerate(xs):
        for j, y in enumerate(ys):
            grid[(i, j)] = node(xc + y * tan, y)

    panels = []
    for i in range(nx):
        for j in range(ny):
            ns = [grid[(i, j)], grid[(i + 1, j)], grid[(i + 1, j + 1)], grid[(i, j + 1)]]
            eid = "LOSA_%d_%d" % (i, j)
            el = ElementoLaminaCurva(eid, ns, [M.nodos[q] for q in ns], t, E, nu, rho=rho)
            M.add_elemento(el); panels.append((eid, i, j))

    # apoyos en las dos lineas esviadas i=0 e i=nx (uz); uy en un nudo central de
    # cada linea; ux en el centro de la linea de inicio.
    apoyos = {"inicio": [], "fin": []}
    for j in range(ny + 1):
        n0 = grid[(0, j)]; nL = grid[(nx, j)]
        v0 = list(M.apoyos.get(n0, [0] * 6)); v0[2] = 1; M.set_apoyo(n0, v0); apoyos["inicio"].append(n0)
        vL = list(M.apoyos.get(nL, [0] * 6)); vL[2] = 1; M.set_apoyo(nL, vL); apoyos["fin"].append(nL)
    nc0 = grid[(0, ny // 2)]; v = list(M.apoyos[nc0]); v[1] = 1; v[0] = 1; M.set_apoyo(nc0, v)
    ncL = grid[(nx, ny // 2)]; v = list(M.apoyos[ncL]); v[1] = 1; M.set_apoyo(ncL, v)

    # esquinas (para la reaccion en la esquina obtusa): obtusas = (inicio, y=-B/2)
    # y (fin, y=+B/2) cuando phi>0; agudas las otras dos.
    # con x = y*tan(phi): la esquina (inicio, y=+B/2) y (fin, y=-B/2) son OBTUSAS
    # (angulo 90+phi); las otras dos, AGUDAS (90-phi). La reaccion se concentra en
    # las obtusas (efecto de esviaje).
    esquinas = {"obtusa_1": grid[(0, ny)], "obtusa_2": grid[(nx, 0)],
                "aguda_1": grid[(0, 0)], "aguda_2": grid[(nx, ny)]}

    # seccion critica: franja central i=nx/2
    ixc = nx // 2
    franja_centro = [eid for (eid, i, j) in panels if i == ixc]

    # caminos de carril (lineas longitudinales sobre la malla romboidal)
    n_carriles = int(obl.get("n_carriles", min(3, max(1, int(B // 3.0)))))
    ANCHO = 3.0; start = -n_carriles * ANCHO / 2.0
    centros = [start + ANCHO * (kk + 0.5) for kk in range(n_carriles)]
    caminos = []
    for kk, yc in enumerate(centros):
        jrow = int(np.argmin([abs(y - yc) for y in ys]))
        camino = [grid[(i, jrow)] for i in range(nx + 1)]
        caminos.append({"id": "carril%d" % (kk + 1), "jrow": jrow, "camino": camino})

    meta = {"L": L, "B": B, "esviaje_deg": float(obl.get("esviaje_deg", 0.0)), "t": t,
            "nx": nx, "ny": ny, "xs": xs.tolist(), "ys": ys.tolist(), "tan_phi": tan,
            "panels": panels, "apoyos": apoyos, "esquinas": esquinas,
            "franja_centro": franja_centro, "ixc": ixc, "caminos": caminos,
            "grid": {repr(k): v for k, v in grid.items()}, "reg": reg, "material": mat}
    return M, meta


def aplicar_peso_propio(M, meta, caso="G1"):
    rho = meta["material"].get("rho", 2500.0)
    for el in M.elementos:
        q = getattr(el, "quad", None)
        if q is None:
            continue
        p = [q.Xi, q.Xj, q.Xm, q.Xn]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        wq = rho * G_ACC * q.t * area / 4.0
        for nm in el.nodos:
            M.add_carga_nodal(caso, nm, [0, 0, -wq, 0, 0, 0])


def aplicar_carga_muerta(M, meta, g2_N_m2, caso="G2"):
    for (eid, i, j) in meta["panels"]:
        el = next(e for e in M.elementos if getattr(e, "eid", None) == eid)
        q = el.quad; p = [q.Xi, q.Xj, q.Xm, q.Xn]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        wq = g2_N_m2 * area / 4.0
        for nm in el.nodos:
            M.add_carga_nodal(caso, nm, [0, 0, -wq, 0, 0, 0])


Q_IK = {1: 300e3, 2: 200e3, 3: 100e3}
Q_K = {1: 9.0e3, 2: 2.5e3, 3: 2.5e3}
ANCHO_CARRIL = 3.0


def aplicar_lm1_estatico(M, meta, caso="Q"):
    """LM1 estatico desfavorable: tandem de cada carril en el centro + UDL."""
    xs = meta["xs"]; ixc = meta["nx"] // 2; resumen = []
    for k, cam in enumerate(meta["caminos"], start=1):
        Q = Q_IK.get(k, 100e3); udl = Q_K.get(k, 2.5e3) * ANCHO_CARRIL
        for di in (-1, 0):
            ix = min(max(ixc + di, 0), len(cam["camino"]) - 1)
            M.add_carga_nodal(caso, cam["camino"][ix], [0, 0, -Q / 2.0, 0, 0, 0])
        cam_nodos = cam["camino"]
        for i, n in enumerate(cam_nodos):
            dx = (xs[min(i + 1, len(xs) - 1)] - xs[max(i - 1, 0)]) / 2.0
            M.add_carga_nodal(caso, n, [0, 0, -udl * dx, 0, 0, 0])
        resumen.append({"carril": k, "Q_tandem_N": Q, "udl_N_m": udl})
    return resumen


def reacciones_esquinas(est_combo, meta):
    """Reaccion vertical en cada esquina y factor de concentracion obtuso =
    R_obtusa_max / R_media_apoyo."""
    reac = est_combo["reacciones"]
    Rz = {k: abs(reac.get(n, [0, 0, 0])[2]) for k, n in meta["esquinas"].items()}
    # reaccion media por nudo de apoyo
    todos = meta["apoyos"]["inicio"] + meta["apoyos"]["fin"]
    Rtot = sum(abs(reac.get(n, [0, 0, 0])[2]) for n in todos)
    Rmedia = Rtot / max(1, len(todos))
    R_obt = max(Rz["obtusa_1"], Rz["obtusa_2"])
    R_agu = max(Rz["aguda_1"], Rz["aguda_2"])
    return {"R_esquinas_N": Rz, "R_media_apoyo_N": Rmedia,
            "concentracion_obtusa": (R_obt / Rmedia if Rmedia else 0.0),
            "R_obtusa_N": R_obt, "R_aguda_N": R_agu,
            "ratio_obtusa_aguda": (R_obt / R_agu if R_agu else 0.0)}


def momentos_franja(est_combo, meta, comp="Mx"):
    """Maximo |M| (por unidad de ancho) en la franja central y reparto transversal
    (lista de |Mx| por panel de la franja)."""
    esf = est_combo["esfuerzos_lamina"]; vals = []
    for eid in meta["franja_centro"]:
        e = esf.get(eid)
        if e and comp in e:
            vals.append(abs(e[comp]))
    if not vals:
        return {"M_max_Nm_m": 0.0, "reparto": []}
    return {"M_max_Nm_m": max(vals), "M_medio_Nm_m": float(np.mean(vals)),
            "reparto": vals, "factor_reparto": max(vals) / float(np.mean(vals))}
