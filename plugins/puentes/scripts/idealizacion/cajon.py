"""
Idealizacion por LAMINA PURA de un tablero de VIGA-CAJON (cajon unicelular).

Malla 3D de laminas curvas MITC4 (motor-fem, FEM-2) de las cuatro paredes del
cajon -- losa SUPERIOR, losa INFERIOR y dos ALMAS (inclinadas) -- a lo largo del
eje, con N vanos y apoyos simples en estribos/pilas sobre la losa inferior, y
DIAFRAGMAS de apoyo como RIGIDIZADORES transversales (controlan la distorsion).
Decision PT 7.4: lamina pura (capta torsion, distorsion y shear lag por geometria;
reutilizable por las cubiertas laminares de la Ola 3).

Eje X = longitudinal; Y = transversal; Z vertical (gravedad -Z). Los nudos se
FUNDEN por coordenada redondeada (las aristas losa-alma se comparten). Devuelve
(M:ModeloFEM, meta) con grupos de panel (top/bot/web_l/web_r), propiedades de
seccion (A, Iy, c_sup, c_inf, Am de Bredt), secciones criticas y caminos de carril.

Frontera (C5): NO calcula la mecanica; entrega el ModeloFEM para `motor-fem`. La
precompresion del postesado se inyecta como carga equivalente (balance) + axil
analitico en EC2. SI (N, m). Predimensionado/asistencia; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.environ.get("MOTOR_FEM_SCRIPTS", ""))
from fem_core import ModeloFEM           # motor-fem (C5)
from fem2 import ElementoLaminaCurva, ElementoRigidizador, bredt_J


def _seccion_props(bs, bi, h, tt, tb, tw):
    """Propiedades de la seccion cajon (pared delgada) referidas a la fibra
    superior z=0 (positivo hacia abajo -z). Devuelve A, Iy(fuerte), c_sup, c_inf,
    Am (area de la celda media para Bredt) y los tramos (s,t) de la celda."""
    lw = np.hypot((bs - bi) / 2.0, h)          # longitud del alma inclinada
    A = bs * tt + bi * tb + 2 * lw * tw
    # centroides de cada pared (z hacia abajo, top en 0)
    parts = [(bs * tt, 0.0), (bi * tb, -h), (lw * tw, -h / 2.0), (lw * tw, -h / 2.0)]
    zbar = sum(a * z for a, z in parts) / A
    Iy = (bs * tt ** 3 / 12 + bs * tt * (0 - zbar) ** 2
          + bi * tb ** 3 / 12 + bi * tb * (-h - zbar) ** 2
          + 2 * (tw * lw ** 3 / 12 * (h / lw) ** 2 + lw * tw * (-h / 2 - zbar) ** 2))
    c_sup = abs(0 - zbar); c_inf = abs(-h - zbar)
    # celda media (Bredt)
    bms = bs - tw; bmi = bi - tw; hm = h - 0.5 * (tt + tb)
    lwm = np.hypot((bms - bmi) / 2.0, hm)
    Am = 0.5 * (bms + bmi) * hm
    tramos = [(bms, tt), (bmi, tb), (lwm, tw), (lwm, tw)]
    J = bredt_J(Am, tramos)
    return {"A": A, "Iy": Iy, "c_sup": c_sup, "c_inf": c_inf, "zbar_desde_top": zbar,
            "Am_bredt": Am, "J_bredt": J, "l_alma": lw, "tramos_celda": tramos}


def construir_cajon(cajon):
    """cajon = {'L'(luz de vano),'n_vanos','bs','bi','h','t_top','t_bot','t_web',
       'nx'(divis. long/vano),'nyt','nyb','nz','material'{E,nu,rho,fck,...},
       'diafragmas'(opc bool, en apoyos)}. Devuelve (M, meta)."""
    L = float(cajon['L']); nv = int(cajon.get('n_vanos', 1)); Ltot = L * nv
    bs = float(cajon['bs']); bi = float(cajon['bi']); h = float(cajon['h'])
    tt = float(cajon['t_top']); tb = float(cajon['t_bot']); tw = float(cajon['t_web'])
    nx = int(cajon.get('nx', 8)); nyt = int(cajon.get('nyt', 4))
    nyb = int(cajon.get('nyb', 2)); nz = int(cajon.get('nz', 2))
    mat = cajon['material']; E = mat['E']; nu = mat['nu']; rho = mat.get('rho', 2500.0)
    props = _seccion_props(bs, bi, h, tt, tb, tw)

    M = ModeloFEM(); reg = {}
    def node(x, y, z):
        key = (round(x, 4), round(y, 4), round(z, 4))
        if key not in reg:
            nm = "N%d" % len(reg); reg[key] = nm; M.add_nodo(nm, x, y, z)
        return reg[key]

    xs = np.linspace(0.0, Ltot, nx * nv + 1)
    panels = {"top": [], "bot": [], "web_l": [], "web_r": []}
    # lineas transversales parametricas
    ytop = np.linspace(-bs / 2, bs / 2, nyt + 1)
    ybot = np.linspace(-bi / 2, bi / 2, nyb + 1)
    tw_par = np.linspace(0.0, 1.0, nz + 1)
    # alma izquierda: de (-bs/2,0) a (-bi/2,-h) ; derecha: (bs/2,0)->(bi/2,-h)
    def webL(s): return (-bs / 2 + s * (-bi / 2 + bs / 2), -h * s)
    def webR(s): return (bs / 2 + s * (bi / 2 - bs / 2), -h * s)

    def strip(part, line_pts, thick, ix):
        x0, x1 = xs[ix], xs[ix + 1]
        for k in range(len(line_pts) - 1):
            (y0, z0), (y1, z1) = line_pts[k], line_pts[k + 1]
            ns = [node(x0, y0, z0), node(x1, y0, z0), node(x1, y1, z1), node(x0, y1, z1)]
            eid = "%s_%d_%d" % (part.upper(), ix, k)
            el = ElementoLaminaCurva(eid, ns, [M.nodos[q] for q in ns], thick, E, nu, rho=rho)
            M.add_elemento(el); panels[part].append((eid, ix, k))

    top_line = [(y, 0.0) for y in ytop]
    bot_line = [(y, -h) for y in ybot]
    webL_line = [webL(s) for s in tw_par]
    webR_line = [webR(s) for s in tw_par]
    for ix in range(len(xs) - 1):
        strip("top", top_line, tt, ix)
        strip("bot", bot_line, tb, ix)
        strip("web_l", webL_line, tw, ix)
        strip("web_r", webR_line, tw, ix)

    # apoyos: en cada seccion de apoyo (x = k*L) coaccionar uz en los nudos de la
    # losa inferior; uy en un alma; ux en un punto -> viga continua isostatica/hiperest.
    nodos_apoyo = []
    for k in range(nv + 1):
        xk = round(k * L, 4)
        for yb in ybot:
            n = reg.get((xk, round(yb, 4), round(-h, 4)))
            if n:
                vec = list(M.apoyos.get(n, [0] * 6)); vec[2] = 1   # uz
                M.set_apoyo(n, vec); nodos_apoyo.append(n)
        # uy en el nudo central inferior; ux solo en el primer apoyo
        nc = reg.get((xk, 0.0, round(-h, 4)))
        if nc:
            vec = list(M.apoyos.get(nc, [0] * 6)); vec[1] = 1
            if k == 0:
                vec[0] = 1
            M.set_apoyo(nc, vec)

    # diafragmas de apoyo: rigidizadores transversales (top<->bot) en cada apoyo
    diaf = []
    if cajon.get('diafragmas', True):
        Gd = E / (2 * (1 + nu)); rho_d = rho
        sec_d = {"A": tw * h, "Iy": tw * h ** 3 / 12, "Iz": h * tw ** 3 / 12, "J": tw ** 3 * h / 3}
        matd = {"E": E, "G": Gd, "nu": nu, "rho": rho_d}
        for k in range(nv + 1):
            xk = round(k * L, 4)
            # barra transversal a media altura uniendo las dos almas
            nl = reg.get((xk, round(webL(0.5)[0], 4), round(webL(0.5)[1], 4)))
            nr = reg.get((xk, round(webR(0.5)[0], 4), round(webR(0.5)[1], 4)))
            if nl and nr:
                el = ElementoRigidizador("DIAF_%d" % k, nl, nr, M.nodos[nl], M.nodos[nr],
                                         matd, sec_d, offset=(0.0, 0.0, 0.0))
                M.add_elemento(el); diaf.append(el.eid)

    # secciones criticas (centro de vano de cada vano) y paneles de fibra
    sec_crit = []
    for v in range(nv):
        xc = (v + 0.5) * L
        ixc = int(np.argmin([abs(x - xc) for x in xs[:-1]]))
        # panel central de top y bot en esa estacion
        topc = "TOP_%d_%d" % (ixc, nyt // 2)
        botc = "BOT_%d_%d" % (ixc, nyb // 2)
        sec_crit.append({"vano": v, "x": float(xs[ixc]), "ix": ixc,
                         "panel_top": topc, "panel_bot": botc})

    # caminos de carril sobre la losa superior (lineas longitudinales de nudos)
    n_carriles = int(cajon.get('n_carriles', min(3, max(1, int((bs) // 3.0)))))
    ANCHO = 3.0; start = (bs - n_carriles * ANCHO) / 2.0
    centros = [start + ANCHO * (kk + 0.5) for kk in range(n_carriles)]
    caminos = []
    for kk, yc in enumerate(centros):
        jrow = int(np.argmin([abs(y - yc) for y in ytop]))
        camino = []
        for x in xs:
            n = reg.get((round(x, 4), round(ytop[jrow], 4), 0.0))
            if n:
                camino.append(n)
        caminos.append({"id": "carril%d" % (kk + 1), "camino": camino})

    meta = {"L": L, "n_vanos": nv, "nz": nz, "Ltot": Ltot, "bs": bs, "bi": bi, "h": h,
            "t_top": tt, "t_bot": tb, "t_web": tw, "nx": nx, "xs": xs.tolist(),
            "panels": panels, "props": props, "nodos_apoyo": nodos_apoyo,
            "diafragmas": diaf, "sec_crit": sec_crit, "caminos": caminos,
            "reg": reg, "ytop": ytop.tolist(), "ybot": ybot.tolist()}
    return M, meta


def momento_seccion(M, res_combo, meta, ix):
    """Integra el momento flector de la seccion en la estacion ix a partir de las
    fuerzas de membrana longitudinales Nx de los paneles (recuperacion FEM del
    esfuerzo de seccion). M_y = sum(Nx_panel * ancho * (z_panel - z_NA))."""
    xs = meta["xs"]; h = meta["h"]; zbar = meta["props"]["zbar_desde_top"]
    esf = res_combo["esfuerzos_lamina"]
    Mtot = 0.0
    for part in ("top", "bot", "web_l", "web_r"):
        for (eid, pix, k) in meta["panels"][part]:
            if pix != ix or eid not in esf:
                continue
            e = esf[eid]
            z = e["z"]                      # cota del centro del panel
            ancho = _panel_ancho(meta, part, k)
            Mtot += e["Nx"] * ancho * (z - zbar)
    return Mtot


def _panel_ancho(meta, part, k):
    if part == "top":
        yt = meta["ytop"]; return abs(yt[k + 1] - yt[k])
    if part == "bot":
        yb = meta["ybot"]; return abs(yb[k + 1] - yb[k])
    return meta["props"]["l_alma"] / float(meta.get("nz", 2))


# --------------------------------------------------------------------------- #
#  Aplicacion de cargas (IAP-11) sobre el modelo de lamina pura               #
# --------------------------------------------------------------------------- #
G_ACC = 9.81


def aplicar_peso_propio(M, meta, rho, caso="G1"):
    """Peso propio de las laminas como carga nodal -Z (area*t*rho*g/4 por nudo)."""
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
    """Carga muerta superpuesta (pavimento, etc.) sobre la losa superior, como
    carga nodal -Z repartida por area tributaria de los paneles top."""
    for (eid, ix, k) in meta["panels"]["top"]:
        el = next(e for e in M.elementos if getattr(e, "eid", None) == eid)
        q = el.quad; p = [q.Xi, q.Xj, q.Xm, q.Xn]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        wq = g2_N_m2 * area / 4.0
        for nm in el.nodos:
            M.add_carga_nodal(caso, nm, [0, 0, -wq, 0, 0, 0])


def inyectar_postesado(M, meta, postesado, caso="P"):
    """Carga equivalente del postesado (balance): w_p = 8*Pinf*f/L^2 hacia ARRIBA,
    aplicada como carga nodal +Z sobre la linea inferior central (eje del tendon).
    Usa Pinf (con perdidas %); la fase de transferencia escala por P0/Pinf en EC2.
    Devuelve dict de balance (w_p, Pinf, ...)."""
    L = meta["L"]; nv = meta["n_vanos"]; reg = meta["reg"]; h = meta["h"]
    P0 = postesado["P0_N"]; perd = postesado.get("perdidas_pct", 18.0) / 100.0
    Pinf = P0 * (1 - perd)
    f = postesado.get("f_sag", 0.5 * (h - 0.3))     # flecha del trazado parabolico
    w_p = 8.0 * Pinf * f / L ** 2                    # N/m por vano
    # nudos de la linea inferior mas proxima al centro (el tendon va por la celda)
    ybot = meta["ybot"]; ycent = min(ybot, key=lambda y: abs(y))
    nodos_linea = []
    for x in meta["xs"]:
        n = reg.get((round(x, 4), round(ycent, 4), round(-h, 4)))
        if n:
            nodos_linea.append((x, n))
    # reparto: por longitud tributaria; signo +Z (hacia arriba) en vano,
    # invertido cerca de apoyos (parabola por vano) -> simplificado: +Z uniforme
    # por vano (predimensionado de balance, como en la losa).
    dx = L / max(1, (len(nodos_linea) - 1) // max(1, nv))
    for i, (x, n) in enumerate(nodos_linea):
        trib = dx if 0 < i < len(nodos_linea) - 1 else dx / 2.0
        M.add_carga_nodal(caso, n, [0, 0, +w_p * trib, 0, 0, 0])
    return {"P0_N": P0, "Pinf_N": Pinf, "perdidas_pct": perd * 100.0,
            "f_sag_m": f, "w_p_N_m": w_p}


def lm1_cargas_moviles(meta, postesado=None):
    """Config de cargas moviles LM1 (motor-fem `movil`): caminos sobre la losa
    superior + objetivos `esfuerzo_lamina` (Nx) en los paneles de fibra top/bot
    de cada seccion critica. Tandem como dos lineas de rueda; UDL por carril."""
    objetivos = []
    for sc in meta["sec_crit"]:
        objetivos.append({"id": "Nx_bot_%d" % sc["vano"], "tipo": "esfuerzo_lamina",
                          "elem": sc["panel_bot"], "comp": "Nx"})
        objetivos.append({"id": "Nx_top_%d" % sc["vano"], "tipo": "esfuerzo_lamina",
                          "elem": sc["panel_top"], "comp": "Nx"})
    lineas = []
    for cam in meta["caminos"]:
        lineas.append({"id": cam["id"], "camino": cam["camino"],
                       "tren": {"axles": [{"P": 300e3, "offset": 0.0},
                                          {"P": 300e3, "offset": 1.2}], "udl": 9e3}})
    return {"posiciones": int(meta.get("posiciones", 21)), "objetivos": objetivos, "lineas": lineas}
