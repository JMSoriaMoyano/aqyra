"""
Idealizacion por LAMINA de un tablero CURVO en planta (viga-cajon unicelular sobre
eje curvo). PT 7.5 (Ola 7).

El tablero se malla SIGUIENDO la DIRECTRIZ CURVA del eje (un IfcAlignment de la
Ola 5, o un arco de radio R constante para predim). En cada estacion de arco s se
levanta la seccion cajon (losa sup, losa inf, dos almas) en la terna local
{tangente t, normal radial n, vertical z}, con laminas curvas MITC4 que representan
la curvatura de forma nativa. La curvatura ACOPLA la TORSION a la flexion: bajo
carga vertical aparece un par torsor (dT/ds = M/R) que se concentra en los apoyos
(esquema de viga curva). Bredt da J de la celda cerrada.

Eje global X-Y = planta; Z vertical (gravedad -Z). Centro de curvatura en (0,R):
   P(s) = (R*sin(s/R), R - R*cos(s/R)) ; tangente t(s); normal n(s) (radial).
Nudos fundidos por coordenada. Devuelve (M:ModeloFEM, meta). El motor-fem NO se
toca. SI (N, m). Predimensionado/asistencia; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.environ.get("MOTOR_FEM_SCRIPTS", ""))
from fem_core import ModeloFEM
from fem2 import ElementoLaminaCurva, ElementoRigidizador, bredt_J
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from cajon import _seccion_props

G_ACC = 9.81


def _frame(s, R):
    """Punto y terna {t,n} de la directriz circular en la estacion de arco s."""
    a = s / R
    P = np.array([R * np.sin(a), R - R * np.cos(a), 0.0])
    t = np.array([np.cos(a), np.sin(a), 0.0])          # tangente
    n = np.array([-np.sin(a), np.cos(a), 0.0])         # normal radial (hacia el centro +)
    return P, t, n


def construir_curvo(curvo):
    """curvo = {'R'(radio),'L'(long. desarrollada=arco),'bs','bi','h','t_top',
       't_bot','t_web','nx','nyt','nyb','nz','material'{E,nu,rho,fck,...},
       'diafragmas'?, 'alineacion'?(opc: lista de (s,x,y) de iso19650)}.
    Devuelve (M, meta)."""
    R = float(curvo["R"]); S = float(curvo["L"])
    bs = float(curvo["bs"]); bi = float(curvo["bi"]); h = float(curvo["h"])
    tt = float(curvo["t_top"]); tb = float(curvo["t_bot"]); tw = float(curvo["t_web"])
    nx = int(curvo.get("nx", 16)); nyt = int(curvo.get("nyt", 6))
    nyb = int(curvo.get("nyb", 3)); nz = int(curvo.get("nz", 3))
    mat = curvo["material"]; E = mat["E"]; nu = mat["nu"]; rho = mat.get("rho", 2500.0)
    props = _seccion_props(bs, bi, h, tt, tb, tw)

    M = ModeloFEM(); reg = {}
    def node(x, y, z):
        key = (round(x, 4), round(y, 4), round(z, 4))
        if key not in reg:
            nm = "N%d" % len(reg); reg[key] = nm; M.add_nodo(nm, x, y, z)
        return reg[key]

    ss = np.linspace(0.0, S, nx + 1)
    # secciones transversales parametricas (y_local transversal, z vertical)
    ytop = np.linspace(-bs / 2, bs / 2, nyt + 1)
    ybot = np.linspace(-bi / 2, bi / 2, nyb + 1)
    tw_par = np.linspace(0.0, 1.0, nz + 1)
    def webL(p): return (-bs / 2 + p * (-bi / 2 + bs / 2), -h * p)
    def webR(p): return (bs / 2 + p * (bi / 2 - bs / 2), -h * p)
    top_line = [(y, 0.0) for y in ytop]
    bot_line = [(y, -h) for y in ybot]
    webL_line = [webL(p) for p in tw_par]
    webR_line = [webR(p) for p in tw_par]

    frames = [_frame(s, R) for s in ss]

    def gpt(i, y_local, z_local):
        P, t, n = frames[i]
        g = P + y_local * n + np.array([0.0, 0.0, z_local])
        return node(g[0], g[1], g[2])

    panels = {"top": [], "bot": [], "web_l": [], "web_r": []}
    def strip(part, line_pts, thick):
        for i in range(len(ss) - 1):
            for k in range(len(line_pts) - 1):
                (y0, z0), (y1, z1) = line_pts[k], line_pts[k + 1]
                ns = [gpt(i, y0, z0), gpt(i + 1, y0, z0), gpt(i + 1, y1, z1), gpt(i, y1, z1)]
                eid = "%s_%d_%d" % (part.upper(), i, k)
                el = ElementoLaminaCurva(eid, ns, [M.nodos[q] for q in ns], thick, E, nu, rho=rho)
                M.add_elemento(el); panels[part].append((eid, i, k))
    strip("top", top_line, tt); strip("bot", bot_line, tb)
    strip("web_l", webL_line, tw); strip("web_r", webR_line, tw)

    # apoyos en s=0 y s=S: losa inferior uz, agrupados por ALMA (interior/exterior)
    # para recuperar el par torsor de apoyo. uy/ux para estabilidad.
    apoyos = {"inicio": {"ext": [], "int": [], "all": []}, "fin": {"ext": [], "int": [], "all": []}}
    for lab, i in (("inicio", 0), ("fin", len(ss) - 1)):
        for yb in ybot:
            n = gpt(i, yb, -h)
            vec = list(M.apoyos.get(n, [0] * 6)); vec[2] = 1; M.set_apoyo(n, vec)
            apoyos[lab]["all"].append((n, yb))
            (apoyos[lab]["ext"] if yb < 0 else apoyos[lab]["int"]).append(n)
        ycen = min(ybot, key=abs)            # nudo inferior mas proximo al eje
        nc = gpt(i, ycen, -h)
        vec = list(M.apoyos.get(nc, [0] * 6)); vec[1] = 1
        if lab == "inicio":
            vec[0] = 1
        M.set_apoyo(nc, vec)

    # diafragmas de apoyo (rigidizadores transversales entre almas)
    diaf = []
    if curvo.get("diafragmas", True):
        Gd = E / (2 * (1 + nu))
        sec_d = {"A": tw * h, "Iy": tw * h ** 3 / 12, "Iz": h * tw ** 3 / 12, "J": tw ** 3 * h / 3}
        matd = {"E": E, "G": Gd, "nu": nu, "rho": rho}
        # conectar el diafragma a una DIVISION EXISTENTE del alma (la mas proxima a
        # media altura); si no existe el nudo, se omite (evita nudos colgantes).
        p_mid = min(tw_par, key=lambda p: abs(p - 0.5))
        for lab, i in (("inicio", 0), ("fin", len(ss) - 1)):
            P, t, n = frames[i]
            def _key(yl, zl):
                g = P + yl * n + np.array([0.0, 0.0, zl])
                return (round(g[0], 4), round(g[1], 4), round(g[2], 4))
            nl = reg.get(_key(*webL(p_mid))); nr = reg.get(_key(*webR(p_mid)))
            if nl and nr:
                el = ElementoRigidizador("DIAF_%s" % lab, nl, nr, M.nodos[nl], M.nodos[nr],
                                         matd, sec_d, offset=(0.0, 0.0, 0.0))
                M.add_elemento(el); diaf.append(el.eid)

    # seccion critica = centro del arco
    ixc = nx // 2
    sec_crit = [{"vano": 0, "s": float(ss[ixc]), "ix": ixc,
                 "panel_top": "TOP_%d_%d" % (ixc, nyt // 2),
                 "panel_bot": "BOT_%d_%d" % (ixc, nyb // 2)}]

    # camino de carril sobre la losa superior (linea central)
    jrow = nyt // 2
    camino = [gpt(i, ytop[jrow], 0.0) for i in range(len(ss))]
    caminos = [{"id": "carril1", "jrow": jrow, "camino": camino}]

    meta = {"R": R, "L": S, "Ltot": S, "h": h, "bs": bs, "bi": bi,
            "t_top": tt, "t_bot": tb, "t_web": tw, "nx": nx, "ss": ss.tolist(),
            "panels": panels, "props": props, "apoyos": apoyos, "diafragmas": diaf,
            "sec_crit": sec_crit, "caminos": caminos, "reg": reg,
            "ytop": ytop.tolist(), "ybot": ybot.tolist(), "material": mat,
            "frames": [(P.tolist(), t.tolist(), n.tolist()) for (P, t, n) in frames]}
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
    for (eid, i, k) in meta["panels"]["top"]:
        el = next(e for e in M.elementos if getattr(e, "eid", None) == eid)
        q = el.quad; p = [q.Xi, q.Xj, q.Xm, q.Xn]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        wq = g2_N_m2 * area / 4.0
        for nm in el.nodos:
            M.add_carga_nodal(caso, nm, [0, 0, -wq, 0, 0, 0])


def aplicar_lm1_estatico(M, meta, caso="Q"):
    """LM1 estatico: tandem de 600 kN en el centro del arco + UDL 9 kN/m2 *3m."""
    ss = meta["ss"]; ixc = meta["nx"] // 2
    cam = meta["caminos"][0]
    for di in (-1, 0):
        ix = min(max(ixc + di, 0), len(cam["camino"]) - 1)
        M.add_carga_nodal(caso, cam["camino"][ix], [0, 0, -300e3, 0, 0, 0])
    udl = 9.0e3 * 3.0
    for i, n in enumerate(cam["camino"]):
        ds = (ss[min(i + 1, len(ss) - 1)] - ss[max(i - 1, 0)]) / 2.0
        M.add_carga_nodal(caso, n, [0, 0, -udl * ds, 0, 0, 0])
    return {"Q_tandem_N": 600e3, "udl_N_m": udl}


def torsion_apoyo(est_combo, meta):
    """Par torsor en el apoyo de inicio recuperado del COUPLE de reacciones entre
    almas exterior/interior: T = (R_ext - R_int)/2 * d_almas (esquema viga curva)."""
    reac = est_combo["reacciones"]
    d_almas = 0.5 * (meta["bs"] + meta["bi"]) - meta["t_web"]    # separacion media de almas
    out = {}
    for lab in ("inicio", "fin"):
        Rext = sum(abs(reac.get(n, [0, 0, 0])[2]) for n in meta["apoyos"][lab]["ext"])
        Rint = sum(abs(reac.get(n, [0, 0, 0])[2]) for n in meta["apoyos"][lab]["int"])
        T = (Rext - Rint) / 2.0 * d_almas
        out[lab] = {"R_ext_N": Rext, "R_int_N": Rint, "T_Nm": T}
    return {"por_apoyo": out, "T_apoyo_Nm": abs(out["inicio"]["T_Nm"]),
            "d_almas_m": d_almas}


def momento_seccion(M, est_combo, meta, ix):
    """Momento flector de la seccion en la estacion ix (integra Nx de paneles)."""
    zbar = meta["props"]["zbar_desde_top"]; esf = est_combo["esfuerzos_lamina"]
    Mtot = 0.0
    for part in ("top", "bot", "web_l", "web_r"):
        for (eid, pix, k) in meta["panels"][part]:
            if pix != ix or eid not in esf:
                continue
            e = esf[eid]; z = e.get("z", 0.0)
            if part == "top":
                yt = meta["ytop"]; anc = abs(yt[k + 1] - yt[k])
            elif part == "bot":
                yb = meta["ybot"]; anc = abs(yb[k + 1] - yb[k])
            else:
                anc = meta["props"]["l_alma"] / float(meta.get("nx", 1) and meta["t_web"] and 3)
                anc = meta["props"]["l_alma"] / 3.0
            Mtot += e.get("Nx", 0.0) * anc * (z - zbar)
    return Mtot
