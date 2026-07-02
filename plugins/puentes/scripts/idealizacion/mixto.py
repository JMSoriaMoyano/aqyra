"""
Idealizacion por LAMINA RIGIDIZADA de un tablero MIXTO acero-hormigon (o cajon
metalico). PT 7.5 (Ola 7).

La LOSA de hormigon se malla con laminas curvas MITC4 (motor-fem, FEM-2) en su
plano medio (z=0). Cada VIGA de acero (bijacena/multijacena) se modela como un
ElementoRigidizador (barra excentrica) corriendo en longitudinal BAJO la losa,
acoplado por OFFSET RIGIDO -> INTERACCION COMPLETA (la accion compuesta validada
en `placa_rigidizada`, 1,3% vs Euler compuesta, criterios PT 7.4). El cajon
metalico es el mismo patron: chapas = laminas, rigidizadores long./transv. =
ElementoRigidizador. NO se anaden nudos: el rigid link u=u_nudo+theta x r lleva la
viga de acero al plano de la losa.

Eje X = longitudinal; Y = transversal; Z vertical (gravedad -Z). Nudos fundidos
por coordenada redondeada. Devuelve (M:ModeloFEM, meta) con paneles de losa,
lineas de viga (rigidizadores), propiedades de acero/losa, secciones criticas y
caminos de carril.

Frontera (C5): el motor-fem NO se toca (lamina curva + rigidizador ya bastan). La
comprobacion EC3/EC4 (clase de seccion, abolladura EN 1993-1-5, conexion, fatiga)
va en `comprobacion/ec3ec4_mixto.py`. SI (N, m). Predimensionado/asistencia;
revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.environ.get("MOTOR_FEM_SCRIPTS", ""))
from fem_core import ModeloFEM           # motor-fem (C5)
from fem2 import ElementoLaminaCurva, ElementoRigidizador
# reuso por formula (puro, sin PyNite) de las propiedades de perfil de acero
sys.path.insert(0, os.environ.get("MOTOR_CALCULO_BARRAS", ""))
try:
    import perfiles_db as _pdb
except Exception:
    _pdb = None

G_ACC = 9.81


def _ishape_props(b, h, tw, tf, r=0.0):
    """Propiedades de un perfil en I bisimetrico desde su geometria (placas).
    Espejo de perfiles_db.from_ishape_geometry (reuso por formula). Metros."""
    if _pdb is not None and hasattr(_pdb, "from_ishape_geometry"):
        return _pdb.from_ishape_geometry(b, h, tw, tf, r)
    hw = h - 2.0 * tf
    A = 2.0 * b * tf + hw * tw
    Iy = (b * h ** 3) / 12.0 - ((b - tw) * hw ** 3) / 12.0
    Iz = (2.0 * tf * b ** 3) / 12.0 + (hw * tw ** 3) / 12.0
    Wply = b * tf * (h - tf) + tw * hw ** 2 / 4.0
    J = (2.0 * b * tf ** 3 + (h - tf) * tw ** 3) / 3.0
    Avz = A - 2.0 * b * tf + (tw + 2.0 * r) * tf
    return {"A": A, "Iy": Iy, "Iz": Iz, "Wely": Iy / (h / 2.0), "Wply": Wply,
            "J": J, "Avz": Avz}


def _seccion_mixta_props(steel, t_losa, b_eff, mat_h, mat_s):
    """Inercia y centroide de la seccion mixta homogeneizada (corto plazo, n0).
    Referencia z desde el plano medio de la losa (z=0, +hacia abajo)."""
    h_s = steel["h"]
    A_s = steel["A"]; I_s = steel["Iy"]
    n0 = mat_s["E"] / mat_h["E"]
    A_c = b_eff * t_losa / n0
    z_c = 0.0                                   # losa centrada en z=0
    z_s = t_losa / 2.0 + h_s / 2.0              # centroide del acero (bajo la losa)
    z_na = (A_c * z_c + A_s * z_s) / (A_c + A_s)
    I_comp = (b_eff * t_losa ** 3 / 12.0) / n0 + A_c * (z_c - z_na) ** 2 \
        + I_s + A_s * (z_s - z_na) ** 2
    return {"n0": n0, "A_c_hom": A_c, "z_na_desde_losa": z_na, "z_s": z_s,
            "I_comp_m4": I_comp, "c_acero_inf": (z_s + h_s / 2.0) - z_na,
            "c_losa_sup": z_na - (z_c - t_losa / 2.0)}


def construir_mixto(mixto):
    """mixto = {'L','n_vanos','B'(ancho tablero),'n_vigas','perfil'{h,b,tw,tf,r?}
       (o 'perfil_nombre'),'t_losa','nx','ny'(divis. transv. losa),
       'material_h'{E,nu,rho,fck,fctm?},'material_s'{E,nu,rho,fy,fu}}.
    Devuelve (M, meta)."""
    L = float(mixto["L"]); nv = int(mixto.get("n_vanos", 1)); Ltot = L * nv
    B = float(mixto["B"]); ng = int(mixto.get("n_vigas", 2))
    t_losa = float(mixto["t_losa"])
    nx = int(mixto.get("nx", 12)); ny = int(mixto.get("ny", 8))
    mh = mixto["material_h"]; ms = mixto["material_s"]
    Eh = mh["E"]; nuh = mh["nu"]; rho_h = mh.get("rho", 2500.0)
    rho_s = ms.get("rho", 7850.0)

    perf = mixto.get("perfil")
    if perf is None and _pdb is not None and mixto.get("perfil_nombre"):
        perf = _pdb.from_db(mixto["perfil_nombre"]); steel = dict(perf)
        steel.setdefault("h", perf.get("h"))
    if perf is not None and "A" in perf and "Iy" in perf:
        steel = dict(perf)
    else:
        steel = _ishape_props(perf["b"], perf["h"], perf["tw"], perf["tf"], perf.get("r", 0.0))
        steel.update({k: perf[k] for k in ("b", "h", "tw", "tf") if k in perf})
        steel["r"] = perf.get("r", 0.0)
    h_s = float(steel["h"])
    lever = t_losa / 2.0 + h_s / 2.0            # offset losa(mid) -> centroide acero

    # posiciones de las vigas (simetricas en B)
    ys_g = list(np.linspace(-B / 2 + B / (2 * ng), B / 2 - B / (2 * ng), ng))
    sep_vigas = (ys_g[1] - ys_g[0]) if ng > 1 else B
    # nudos transversales de la losa: union linspace + posiciones de viga
    ys_base = list(np.linspace(-B / 2, B / 2, ny + 1))
    ys = sorted(set([round(y, 4) for y in (ys_base + ys_g)]))
    xs = np.linspace(0.0, Ltot, nx * nv + 1)

    M = ModeloFEM(); reg = {}
    def node(x, y, z):
        key = (round(x, 4), round(y, 4), round(z, 4))
        if key not in reg:
            nm = "N%d" % len(reg); reg[key] = nm; M.add_nodo(nm, x, y, z)
        return reg[key]

    # --- losa: paneles de lamina curva en z=0 --------------------------------
    panels_top = []
    for ix in range(len(xs) - 1):
        x0, x1 = xs[ix], xs[ix + 1]
        for k in range(len(ys) - 1):
            y0, y1 = ys[k], ys[k + 1]
            ns = [node(x0, y0, 0.0), node(x1, y0, 0.0), node(x1, y1, 0.0), node(x0, y1, 0.0)]
            eid = "LOSA_%d_%d" % (ix, k)
            el = ElementoLaminaCurva(eid, ns, [M.nodos[q] for q in ns], t_losa, Eh, nuh, rho=rho_h)
            M.add_elemento(el); panels_top.append((eid, ix, k))

    # --- vigas de acero: rigidizadores con offset rigido bajo la losa --------
    Gs = ms["E"] / (2 * (1 + ms["nu"]))
    sec_s = {"A": steel["A"], "Iy": steel["Iy"], "Iz": steel.get("Iz", steel["Iy"] / 10.0),
             "J": steel.get("J", steel["Iy"] / 50.0)}
    mat_s = {"E": ms["E"], "G": Gs, "nu": ms["nu"], "rho": rho_s}
    vigas = {}                                  # id_viga -> [eids]
    for g, yg in enumerate(ys_g):
        yg_r = round(yg, 4)
        eids = []
        for ix in range(len(xs) - 1):
            ni = reg[(round(xs[ix], 4), yg_r, 0.0)]
            nj = reg[(round(xs[ix + 1], 4), yg_r, 0.0)]
            eid = "VIGA%d_%d" % (g, ix)
            el = ElementoRigidizador(eid, ni, nj, M.nodos[ni], M.nodos[nj], mat_s, sec_s,
                                     offset=(0.0, 0.0, -lever))
            M.add_elemento(el); eids.append((eid, ix))
        vigas["VIGA%d" % g] = {"y": yg, "eids": eids}

    # --- apoyos simples en x=k*L sobre las lineas de viga --------------------
    for k in range(nv + 1):
        xk = round(k * L, 4)
        for yg in ys_g:
            n = reg.get((xk, round(yg, 4), 0.0))
            if n:
                vec = list(M.apoyos.get(n, [0] * 6)); vec[2] = 1  # uz
                M.set_apoyo(n, vec)
        nc = reg.get((xk, round(ys_g[len(ys_g) // 2], 4), 0.0))
        if nc:
            vec = list(M.apoyos.get(nc, [0] * 6)); vec[1] = 1     # uy
            if k == 0:
                vec[0] = 1                                        # ux (un punto)
            M.set_apoyo(nc, vec)

    # --- secciones criticas: centro de vano + viga mas cargada (central) -----
    sec_crit = []
    for v in range(nv):
        xc = (v + 0.5) * L
        ixc = int(np.argmin([abs(x - xc) for x in xs[:-1]]))
        sec_crit.append({"vano": v, "x": float(xs[ixc]), "ix": ixc})

    # --- caminos de carril sobre la losa -------------------------------------
    n_carriles = int(mixto.get("n_carriles", min(3, max(1, int(B // 3.0)))))
    ANCHO = 3.0; start = -n_carriles * ANCHO / 2.0
    centros = [start + ANCHO * (kk + 0.5) for kk in range(n_carriles)]
    caminos = []
    for kk, yc in enumerate(centros):
        jrow = int(np.argmin([abs(y - yc) for y in ys]))
        camino = [reg[(round(x, 4), round(ys[jrow], 4), 0.0)] for x in xs]
        caminos.append({"id": "carril%d" % (kk + 1), "jrow": jrow, "yc": yc, "camino": camino})

    meta = {"L": L, "n_vanos": nv, "Ltot": Ltot, "B": B, "n_vigas": ng,
            "t_losa": t_losa, "nx": nx, "ny": ny, "xs": xs.tolist(), "ys": ys,
            "ys_g": ys_g, "sep_vigas": sep_vigas, "lever": lever,
            "steel": steel, "panels_top": panels_top, "vigas": vigas,
            "sec_crit": sec_crit, "caminos": caminos, "reg": reg,
            "material_h": mh, "material_s": ms}
    return M, meta


# --------------------------------------------------------------------------- #
#  Cargas (IAP-11) sobre el modelo mixto                                       #
# --------------------------------------------------------------------------- #
def aplicar_peso_propio(M, meta, caso="G1"):
    """Peso propio: losa (laminas, area*t*rho_h*g/4 por nudo) + vigas de acero
    (A_s*rho_s*g por unidad de longitud, repartido a los nudos de la viga)."""
    rho_h = meta["material_h"].get("rho", 2500.0)
    for el in M.elementos:
        q = getattr(el, "quad", None)
        if q is None:
            continue
        p = [q.Xi, q.Xj, q.Xm, q.Xn]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        wq = rho_h * G_ACC * q.t * area / 4.0
        for nm in el.nodos:
            M.add_carga_nodal(caso, nm, [0, 0, -wq, 0, 0, 0])
    # peso del acero
    rho_s = meta["material_s"].get("rho", 7850.0); A_s = meta["steel"]["A"]
    xs = meta["xs"]; reg = meta["reg"]
    for vg in meta["vigas"].values():
        yg = round(vg["y"], 4)
        for i, x in enumerate(xs):
            n = reg.get((round(x, 4), yg, 0.0))
            if not n:
                continue
            dx = (xs[min(i + 1, len(xs) - 1)] - xs[max(i - 1, 0)]) / 2.0
            w = A_s * rho_s * G_ACC * dx
            M.add_carga_nodal(caso, n, [0, 0, -w, 0, 0, 0])


def aplicar_carga_muerta(M, meta, g2_N_m2, caso="G2"):
    """Pavimento (g2, N/m2) sobre la losa superior, nodal -Z por area tributaria."""
    for (eid, ix, k) in meta["panels_top"]:
        el = next(e for e in M.elementos if getattr(e, "eid", None) == eid)
        q = el.quad; p = [q.Xi, q.Xj, q.Xm, q.Xn]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        wq = g2_N_m2 * area / 4.0
        for nm in el.nodos:
            M.add_carga_nodal(caso, nm, [0, 0, -wq, 0, 0, 0])


# constantes LM1 (IAP-11 / EN 1991-2)
Q_IK = {1: 300e3, 2: 200e3, 3: 100e3}            # carga total del tandem por carril (N)
Q_K = {1: 9.0e3, 2: 2.5e3, 3: 2.5e3}             # UDL por carril (N/m2)
ANCHO_CARRIL = 3.0


def aplicar_lm1_estatico(M, meta, caso="Q", vano=0):
    """LM1 ESTATICO desfavorable (predim): tandem de cada carril centrado en el
    vano + UDL del carril. Carga nodal -Z. Por carril k: tandem total Q_IK[k]
    (2 ejes), UDL Q_K[k]*3 m repartida en el camino. Devuelve resumen."""
    xs = meta["xs"]; reg = meta["reg"]; L = meta["L"]
    xc = (vano + 0.5) * L
    ixc = int(np.argmin([abs(x - xc) for x in xs]))
    resumen = []
    for k, cam in enumerate(meta["caminos"], start=1):
        Q = Q_IK.get(k, 100e3); udl = Q_K.get(k, 2.5e3) * ANCHO_CARRIL
        # tandem: dos ejes a +-0.6 m del centro, mitad de carga cada uno
        for di in (-1, 0):
            ix = min(max(ixc + di, 0), len(xs) - 1)
            n = cam["camino"][ix]
            M.add_carga_nodal(caso, n, [0, 0, -Q / 2.0, 0, 0, 0])
        # UDL a lo largo del camino del carril
        cam_nodos = cam["camino"]
        for i, n in enumerate(cam_nodos):
            dx = (xs[min(i + 1, len(xs) - 1)] - xs[max(i - 1, 0)]) / 2.0
            M.add_carga_nodal(caso, n, [0, 0, -udl * dx, 0, 0, 0])
        resumen.append({"carril": k, "Q_tandem_N": Q, "udl_N_m": udl})
    return {"vano": vano, "ix_centro": ixc, "carriles": resumen}


def esfuerzos_viga_central(est_combo, meta, vano=0):
    """Recupera, para la viga central en el centro del vano, el axil y el momento
    fuerte del acero (esfuerzos_barra), y compone el MOMENTO MIXTO de la seccion:
    M = |N_acero|*lever + |M_acero_fuerte|, sumado a todas las vigas.
    Devuelve dict {M_Ed_Nm, V_Ed_N, N_acero_N, M_acero_Nm, por_viga[]}."""
    esf_b = est_combo["esfuerzos_barra"]
    lever = meta["lever"]; ixc = meta["sec_crit"][vano]["ix"]
    M_tot = 0.0; V_tot = 0.0; por_viga = []
    for vid, vg in meta["vigas"].items():
        eid = None
        for (e, ix) in vg["eids"]:
            if ix == ixc:
                eid = e; break
        if eid is None or eid not in esf_b:
            continue
        e = esf_b[eid]
        N = e["axial_i"]
        Mfuerte = max(abs(e["My_i"]), abs(e["Mz_i"]))
        Vfuerte = max(abs(e["Vz_i"]), abs(e["Vy_i"]))
        M_viga = abs(N) * lever + Mfuerte
        M_tot += M_viga; V_tot += Vfuerte
        por_viga.append({"viga": vid, "N_acero_N": N, "M_acero_Nm": Mfuerte,
                         "V_N": Vfuerte, "M_mixto_Nm": M_viga})
    return {"M_Ed_Nm": M_tot, "V_Ed_N": V_tot, "por_viga": por_viga,
            "n_vigas": len(por_viga)}
