"""
FEM-1: analisis MODAL + CARGAS MOVILES / LINEAS DE INFLUENCIA (motor-fem).

Capa ADITIVA sobre el nucleo FEM-0: NO modifica `fem_core.py` ni la libreria de
elementos (`barra.py`/`lamina.py`), de modo que el estatico lineal y la
no-regresion del *strangler* quedan intactos por construccion. Opera sobre un
`ModeloFEM` ya construido (mismos atributos: nodos, elementos, apoyos, resortes,
cargas).

 - MODAL: matriz de masas CONCENTRADA (lumped) -> problema generalizado
   K phi = w^2 M phi resuelto con `scipy.sparse.linalg.eigsh` en modo
   shift-invert (sigma=0). Devuelve frecuencias, periodos, modos y MASA
   PARTICIPANTE por direccion. Fuentes de masa: peso propio (rho*volumen),
   casos gravitatorios (|Fz|/g) y masas nodales.
 - MOVIL: LINEAS DE INFLUENCIA por barrido de carga unidad sobre un camino
   (reutilizando la factorizacion estatica `splu(Kff)` -> N solves baratos) y
   ENVOLVENTES de esfuerzos/reacciones por un TREN de cargas (tandem + UDL),
   con posiciones pesimas. El nucleo es AGNOSTICO a la normativa: el tren llega
   ya en magnitudes (IAP-11 lo arma la disciplina `puentes`). Los objetivos del
   barrido pueden ser de BARRA, de REACCION, de DESPLAZAMIENTO y -- desde
   v0.2.1 (PT 7.2, aditivo) -- de LAMINA (`esfuerzo_lamina`: Mx/My/Mxy... de una
   placa DKMQ), para envolventes LM1 de losas postesadas.

Convencion de ejes GLOBALES: X,Y horizontales, Z vertical, gravedad -Z. SI.
Predimensionado/asistencia; a revisar y firmar por tecnico competente (ICCP).
"""
from __future__ import annotations
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve, splu, eigsh

import sys, os
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "elementos"))
from fem_core import ModeloFEM, ElementoBarra, ElementoLamina  # noqa: E402

GDL = 6
G_ACC = 9.81   # m/s2 (conversion peso->masa) [confirmar AN]


# --------------------------------------------------------------------------- #
#  Matrices de masa CONCENTRADA (lumped) por elemento                          #
# --------------------------------------------------------------------------- #
def m_barra_lumped(el):
    """Masa concentrada 12x12 (global) de una barra: rho*A*L/2 por nudo en las
    3 traslaciones; inercia polar rho*Ip*L/2 en la rotacion axil; rotaciones de
    flexion sin masa (lumped clasico)."""
    rho = float(el.mat.get("rho", 0.0) or 0.0)
    A = float(el.sec.get("A", 0.0) or 0.0); L = el.L
    Ip = float(el.sec.get("Iy", 0.0) or 0.0) + float(el.sec.get("Iz", 0.0) or 0.0)
    if Ip == 0.0:
        Ip = float(el.sec.get("J", 0.0) or 0.0)
    mt = rho * A * L / 2.0; jt = rho * Ip * L / 2.0
    m = np.zeros((12, 12))
    for nb in (0, 6):
        m[nb, nb] = mt; m[nb + 1, nb + 1] = mt; m[nb + 2, nb + 2] = mt
        m[nb + 3, nb + 3] = jt
    return el.T.T @ m @ el.T


def m_lamina_lumped(el):
    """Masa concentrada 24x24 (global) de una lamina: rho*area*t/4 por nudo en
    las 3 traslaciones (requiere `el.rho`; 0 si no se asigno)."""
    rho = float(getattr(el, "rho", 0.0) or 0.0)
    q = el.quad
    p = [q.Xi, q.Xj, q.Xm, q.Xn]
    area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
            + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
    mn = rho * area * q.t / 4.0
    m = np.zeros((24, 24))
    for k in range(4):
        b = k * 6
        m[b, b] = mn; m[b + 1, b + 1] = mn; m[b + 2, b + 2] = mn
    return m


def _m_elemento(el):
    if isinstance(el, ElementoBarra):
        return m_barra_lumped(el)
    return m_lamina_lumped(el)


# --------------------------------------------------------------------------- #
#  Ensamblaje comun (K, particion libre/fijo, vector de carga por caso)        #
# --------------------------------------------------------------------------- #
def _ensamblar(M):
    nindex = M._nindex(); ndof = len(M.norden) * GDL; casos = M._casos()
    rows = []; cols = []; data = []
    for el in M.elementos:
        dofs = np.asarray(el.dofs(nindex)); Kg = np.asarray(el.Kglobal); n = len(dofs)
        rows.append(np.repeat(dofs, n)); cols.append(np.tile(dofs, n)); data.append(Kg.flatten())
    for name, kv in M.resortes.items():
        base = nindex[name] * GDL
        for i in range(6):
            if kv[i]:
                rows.append(np.array([base + i])); cols.append(np.array([base + i]))
                data.append(np.array([float(kv[i])]))
    K = coo_matrix((np.concatenate(data), (np.concatenate(rows), np.concatenate(cols))),
                   shape=(ndof, ndof)).tocsr()
    fixed = []
    for name, vec in M.apoyos.items():
        base = nindex[name] * GDL
        for i in range(6):
            if vec[i]:
                fixed.append(base + i)
    fixed = set(sorted(set(fixed)))
    free = np.array([d for d in range(ndof) if d not in fixed])
    Fc = {c: np.zeros(ndof) for c in casos}
    for el in M.elementos:
        dofs = el.dofs(nindex)
        for c in casos:
            fg = el.fer_global(c).flatten()
            for a, ia in enumerate(dofs):
                Fc[c][ia] -= fg[a]
    for cn in M.cargas_nodales:
        base = nindex[cn["nodo"]] * GDL
        for i in range(6):
            Fc[cn["caso"]][base + i] += cn["F"][i]
    return {"K": K, "nindex": nindex, "ndof": ndof, "free": free, "fixed": fixed,
            "casos": casos, "Fc": Fc}


# --------------------------------------------------------------------------- #
#  ANALISIS MODAL                                                              #
# --------------------------------------------------------------------------- #
def modal(M, nmodos=6, peso_propio=True, masas_casos=None, masas_nodales=None):
    """Frecuencias propias, modos y masa participante (masa concentrada).

    masas_casos: {caso: factor} -> aporta masa |Fz|/g de ese caso gravitatorio.
    masas_nodales: {nodo: [mx,my,mz,...]} masas concentradas adicionales.
    """
    asm = _ensamblar(M)
    K = asm["K"]; nindex = asm["nindex"]; ndof = asm["ndof"]; free = asm["free"]; Fc = asm["Fc"]
    mrows = []; mcols = []; mdata = []
    if peso_propio:
        for el in M.elementos:
            dofs = np.asarray(el.dofs(nindex)); Me = _m_elemento(el); n = len(dofs)
            mrows.append(np.repeat(dofs, n)); mcols.append(np.tile(dofs, n)); mdata.append(Me.flatten())
    masas_casos = masas_casos or {}
    for caso, fac in masas_casos.items():
        if caso in Fc:
            Fv = Fc[caso]
            for nm in M.norden:
                b = nindex[nm] * GDL
                w = abs(Fv[b + 2])
                if w:
                    mm = fac * w / G_ACC
                    mrows.append(np.array([b, b + 1, b + 2]))
                    mcols.append(np.array([b, b + 1, b + 2]))
                    mdata.append(np.array([mm, mm, mm]))
    masas_nodales = masas_nodales or {}
    for nm, mv in masas_nodales.items():
        b = nindex[nm] * GDL
        for i in range(6):
            if mv[i]:
                mrows.append(np.array([b + i])); mcols.append(np.array([b + i]))
                mdata.append(np.array([float(mv[i])]))
    if not mdata:
        raise ValueError("modal: el modelo no tiene masa (define rho, masas_casos o masas_nodales)")
    Mg = coo_matrix((np.concatenate(mdata), (np.concatenate(mrows), np.concatenate(mcols))),
                    shape=(ndof, ndof)).tocsr()
    Kff = K[np.ix_(free, free)].tocsc(); Mff = Mg[np.ix_(free, free)].tocsc()
    nm_eff = int(min(nmodos, len(free) - 1))
    vals, vecs = eigsh(Kff, k=nm_eff, M=Mff, sigma=0.0, which="LM")
    order = np.argsort(vals); vals = vals[order]; vecs = vecs[:, order]
    vals = np.clip(vals, 0.0, None)
    omega = np.sqrt(vals); freqs = omega / (2 * np.pi)
    periodos = [float(2 * np.pi / o) if o > 1e-9 else None for o in omega]
    # masa participante por direccion (x,y,z)
    masa_total = {}
    part = {"x": [], "y": [], "z": []}
    dir_idx = {"x": 0, "y": 1, "z": 2}
    Mff_arr = Mff
    diagM = np.asarray(Mg.diagonal())
    for d, di in dir_idx.items():
        sel = [free[j] for j in range(len(free)) if free[j] % GDL == di]
        masa_total[d] = float(sum(diagM[s] for s in sel))
    for i in range(nm_eff):
        phi = vecs[:, i]
        gen = float(phi @ (Mff_arr @ phi))
        for d, di in dir_idx.items():
            r = np.array([1.0 if free[j] % GDL == di else 0.0 for j in range(len(free))])
            L = float(phi @ (Mff_arr @ r))
            meff = (L * L / gen) if gen > 1e-30 else 0.0
            part[d].append(meff)
    res = {"n_modos": nm_eff,
           "frecuencias_Hz": [float(f) for f in freqs],
           "periodos_s": periodos,
           "omega_rad_s": [float(o) for o in omega],
           "masa_total_kg": masa_total,
           "masa_participante_kg": part,
           "masa_participante_frac": {d: [(part[d][i] / masa_total[d]) if masa_total[d] else 0.0
                                          for i in range(nm_eff)] for d in dir_idx},
           "modos": vecs.tolist(), "free": free.tolist()}
    return res


# --------------------------------------------------------------------------- #
#  CARGAS MOVILES / LINEAS DE INFLUENCIA                                        #
# --------------------------------------------------------------------------- #
def _esf_barra_nodal(el, U, nindex):
    """Esfuerzos de extremo de una barra con desplazamientos nodales (sin carga
    de barra: la carga movil se aplica como fuerzas NODALES)."""
    d = U[el.dofs(nindex)].reshape(12, 1)
    f = (el.k_cond @ (el.T @ d)).flatten()
    return {"axial_i": f[0], "Vy_i": f[1], "Vz_i": f[2], "T_i": f[3], "My_i": f[4], "Mz_i": f[5],
            "axial_j": -f[6], "Vy_j": -f[7], "Vz_j": -f[8], "T_j": -f[9], "My_j": -f[10], "Mz_j": -f[11],
            "N_i": -f[0], "N_j": f[6]}


def _camino_param(M, camino):
    """Devuelve (coords[Nx3], s_acumulado[N], total)."""
    pts = np.array([M.nodos[n] for n in camino], float)
    seg = np.linalg.norm(np.diff(pts, axis=0), axis=1)
    s = np.concatenate([[0.0], np.cumsum(seg)])
    return pts, s, float(s[-1])


def _carga_unidad_en_s(M, camino, s_acum, s_pos, nindex, ndof, P=1.0, dir_dof=2):
    """Vector de fuerza global de una carga puntual P en la posicion s_pos del
    camino (reparto lineal a los dos nudos del segmento)."""
    F = np.zeros(ndof)
    total = s_acum[-1]
    s_pos = min(max(s_pos, 0.0), total)
    k = int(np.searchsorted(s_acum, s_pos, side="right") - 1)
    k = min(max(k, 0), len(camino) - 2)
    seglen = s_acum[k + 1] - s_acum[k]
    xi = (s_pos - s_acum[k]) / seglen if seglen > 0 else 0.0
    na, nb = camino[k], camino[k + 1]
    F[nindex[na] * GDL + dir_dof] += P * (1 - xi)
    F[nindex[nb] * GDL + dir_dof] += P * xi
    return F


def _eval_objetivo(obj, U, K, F, M, nindex):
    if obj["tipo"] == "reaccion":
        b = nindex[obj["nodo"]] * GDL + int(obj["comp"])
        return float(K.dot(U)[b] - F[b])
    elif obj["tipo"] == "esfuerzo_barra":
        el = next(e for e in M.elementos if isinstance(e, ElementoBarra) and e.eid == obj["elem"])
        return float(_esf_barra_nodal(el, U, nindex)[obj["comp"]])
    elif obj["tipo"] == "desplazamiento":
        b = nindex[obj["nodo"]] * GDL + int(obj["comp"])
        return float(U[b])
    elif obj["tipo"] == "esfuerzo_lamina":
        # PT 7.2 (aditivo, motor v0.2.1): linea de influencia de un esfuerzo de
        # PLACA (Mx/My/Mxy/Qx/Qy/Nx/Ny/Nxy por unidad de ancho) en una lamina
        # objetivo, para envolventes LM1 de losas (postesadas) DKMQ. La carga
        # unidad ya viene aplicada como fuerza nodal -Z (dir_dof=2) sobre el
        # camino; aqui solo se recupera el esfuerzo de la lamina del U resultante.
        el = next(e for e in M.elementos
                  if isinstance(e, ElementoLamina) and e.eid == obj["elem"])
        return float(el.esfuerzos(U, nindex)[obj["comp"]])
    raise ValueError("objetivo desconocido: %s" % obj.get("tipo"))


def movil(M, cfg):
    """Lineas de influencia + envolventes por tren de cargas.

    cfg = {
      "posiciones": 41,
      "objetivos": [ {"id","tipo":"esfuerzo_barra|esfuerzo_lamina|reaccion|
                      desplazamiento", "elem","comp"} | {"nodo","comp"} ],
      "lineas":   [ {"id","camino":[nodos...],
                     "tren": {"axles":[{"P","offset"}...], "udl": w_N_m}} ]
    }
    Devuelve lineas_influencia (por objetivo y linea, carga unidad -Z) y
    envolventes (max/min por objetivo con posicion pesima).
    """
    asm = _ensamblar(M)
    K = asm["K"]; nindex = asm["nindex"]; ndof = asm["ndof"]; free = asm["free"]
    Kff = K[np.ix_(free, free)].tocsc(); lu = splu(Kff)
    npos = int(cfg.get("posiciones", 41))
    objetivos = cfg["objetivos"]; lineas = cfg["lineas"]

    def solve(F):
        U = np.zeros(ndof); U[free] = lu.solve(F[free]); return U

    li = {}            # obj_id -> linea_id -> {"s":[], "eta":[]}
    for ln in lineas:
        pts, s_acum, total = _camino_param(M, ln["camino"])
        s_list = np.linspace(0.0, total, npos)
        for obj in objetivos:
            li.setdefault(obj["id"], {})[ln["id"]] = {"s": s_list.tolist(), "eta": []}
        for s_pos in s_list:
            F = _carga_unidad_en_s(M, ln["camino"], s_acum, s_pos, nindex, ndof, P=1.0, dir_dof=2)
            U = solve(F)
            for obj in objetivos:
                li[obj["id"]][ln["id"]]["eta"].append(_eval_objetivo(obj, U, K, F, M, nindex))

    # --- envolventes por tren (combinacion de lineas de influencia) ---------- #
    env = {}
    for obj in objetivos:
        max_v = 0.0; min_v = 0.0; pos_max = None; pos_min = None
        # contribucion combinada de todas las lineas; el tandem se posiciona
        # barriendo su origen; la UDL integra la parte adversa de la IL.
        for ln in lineas:
            tren = ln.get("tren", {})
            axles = tren.get("axles", []); udl = float(tren.get("udl", 0.0))
            d = li[obj["id"]][ln["id"]]
            s_arr = np.array(d["s"]); eta = np.array(d["eta"])
            if len(s_arr) < 2:
                continue
            # eta es por carga unidad +Z; el trafico actua hacia -Z, asi que el
            # efecto por carga gravitatoria unidad es eta_g = -eta.
            eta_g = -eta
            # tandem: barrer origen s0 y sumar P_i*eta_g(s0+offset_i)
            tand_vals = np.zeros_like(s_arr)
            for j, s0 in enumerate(s_arr):
                v = 0.0
                for ax in axles:
                    sp = s0 + float(ax.get("offset", 0.0))
                    v += float(ax["P"]) * np.interp(sp, s_arr, eta_g, left=0.0, right=0.0)
                tand_vals[j] = v
            # UDL: parte positiva (para max) / negativa (para min)
            pos_area = np.trapezoid(np.clip(eta_g, 0, None), s_arr) * udl
            neg_area = np.trapezoid(np.clip(eta_g, None, 0), s_arr) * udl
            jmax = int(np.argmax(tand_vals)); jmin = int(np.argmin(tand_vals))
            max_v += tand_vals[jmax] + pos_area
            min_v += tand_vals[jmin] + neg_area
            if pos_max is None:
                pos_max = float(s_arr[jmax]); pos_min = float(s_arr[jmin])
        env[obj["id"]] = {"max": float(max_v), "min": float(min_v),
                          "pos_max_m": pos_max, "pos_min_m": pos_min}
    return {"lineas_influencia": li, "envolventes": env, "posiciones": npos}
