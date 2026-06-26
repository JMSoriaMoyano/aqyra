"""
Biblioteca del NUCLEO DE PANTALLAS ACOPLADAS (caso 15, PT 1.5). Extiende la
pantalla aislada (ec8.py / stick 1 GdL) al NUCLEO con diafragma rigido y 3 GdL
por planta (ux, uy, theta).

  - Cada pantalla = voladizo (flexion Euler-Bernoulli + cortante Timoshenko):
    reutiliza ec8.stick_lateral_stiffness en SU direccion.
  - Los machones de alma ACOPLADOS por dinteles se condensan en UN elemento Y
    con la rigidez del par acoplado (plano-portico 2D con brazos rigidos +
    flexibilidad de cortante del dintel) -> el acoplamiento ENTRA en la rigidez
    global (no son voladizos independientes).
  - Ensamblaje a 3 GdL/planta (diafragma rigido) -> CR, CM, e0; modal; reparto
    de cortante DIRECTO + TORSION natural (CR!=CM) + TORSION ACCIDENTAL
    +-0.05*L (EC8 §4.3.2); derivas en el borde mas flexible.

Unidades SI internas (N, m, kg). NDP [confirmar AN].
"""
import math
import numpy as np
import ec8

G = 9.81


def _e(resiste):
    return (1.0, 0.0) if resiste.upper() == "X" else (0.0, 1.0)


def _lever(xc, yc, resiste, CMx, CMy):
    ex, ey = _e(resiste)
    return -(yc - CMy) * ex + (xc - CMx) * ey


# ---------------------------------------------------------------------------
# Plano-portico 2D (Y-Z) de la pareja de machones acoplados por dinteles
# ---------------------------------------------------------------------------
def _frame2d_kl(L, EA, EI):
    return np.array([
        [EA / L, 0, 0, -EA / L, 0, 0],
        [0, 12 * EI / L ** 3, 6 * EI / L ** 2, 0, -12 * EI / L ** 3, 6 * EI / L ** 2],
        [0, 6 * EI / L ** 2, 4 * EI / L, 0, -6 * EI / L ** 2, 2 * EI / L],
        [-EA / L, 0, 0, EA / L, 0, 0],
        [0, -12 * EI / L ** 3, -6 * EI / L ** 2, 0, 12 * EI / L ** 3, -6 * EI / L ** 2],
        [0, 6 * EI / L ** 2, 2 * EI / L, 0, -6 * EI / L ** 2, 4 * EI / L]])


def _frame2d_T(Yi, Zi, Yj, Zj):
    L = math.hypot(Yj - Yi, Zj - Zi)
    c = (Yj - Yi) / L; s = (Zj - Zi) / L
    R = np.array([[c, s, 0], [-s, c, 0], [0, 0, 1.0]])
    T = np.zeros((6, 6)); T[:3, :3] = R; T[3:, 3:] = R
    return T, L


def _build_coupled_frame(piers, dintel, z_full, E, Gsh):
    """Construye el portico 2D (Y-Z) del par de machones + dinteles con brazos
    rigidos y dintel de cortante. Devuelve (K, coords, members, nid, n)."""
    p1, p2 = piers
    yc1, yc2 = sorted([p1["yc_m"], p2["yc_m"]])
    a = p1["Lw_m"] / 2.0
    yf1 = yc1 + a; yf2 = yc2 - a
    n = len(z_full) - 1; zs = z_full
    EA_w = E * p1["A_m2"]; EI_w = E * p1["I_m4"]
    b = dintel["b_m"]; h = dintel["h_m"]; ln = dintel["ln_m"]
    Ib = b * h ** 3 / 12.0; Avb = 5.0 / 6.0 * b * h
    Ib_eff = Ib / (1.0 + 12.0 * E * Ib / (Gsh * Avb * ln ** 2))
    EI_b = E * Ib_eff; EA_b = E * (b * h); RIG = 1e14
    nodes = {}; idx = [0]
    def nid(tag):
        if tag not in nodes:
            nodes[tag] = idx[0]; idx[0] += 1
        return nodes[tag]
    coords = {}
    for j in range(n + 1):
        coords[nid("c1_%d" % j)] = (yc1, zs[j]); coords[nid("c2_%d" % j)] = (yc2, zs[j])
    for j in range(1, n + 1):
        coords[nid("f1_%d" % j)] = (yf1, zs[j]); coords[nid("f2_%d" % j)] = (yf2, zs[j])
    nn = idx[0]; ndof = 3 * nn
    K = np.zeros((ndof, ndof)); members = []
    def add(ni, nj, EA, EI):
        Yi, Zi = coords[ni]; Yj, Zj = coords[nj]
        T, L = _frame2d_T(Yi, Zi, Yj, Zj); kl = _frame2d_kl(L, EA, EI)
        kg = T.T.dot(kl).dot(T)
        d = [3 * ni, 3 * ni + 1, 3 * ni + 2, 3 * nj, 3 * nj + 1, 3 * nj + 2]
        for x in range(6):
            for y in range(6):
                K[d[x], d[y]] += kg[x, y]
        members.append((ni, nj, kl, T, d, "wall" if EA == EA_w else ("dintel" if EA == EA_b else "rig")))
    for j in range(1, n + 1):
        add(nid("c1_%d" % (j - 1)), nid("c1_%d" % j), EA_w, EI_w)
        add(nid("c2_%d" % (j - 1)), nid("c2_%d" % j), EA_w, EI_w)
        add(nid("c1_%d" % j), nid("f1_%d" % j), RIG, RIG)
        add(nid("f2_%d" % j), nid("c2_%d" % j), RIG, RIG)
        add(nid("f1_%d" % j), nid("f2_%d" % j), EA_b, EI_b)
    meta = {"yc1": yc1, "yc2": yc2, "ell_m": abs(yc2 - yc1), "yf1": yf1, "yf2": yf2,
            "Ib_m4": Ib, "Ib_eff_m4": Ib_eff, "ln_m": ln, "h_m": h, "b_m": b}
    return K, coords, members, nodes, n, meta


def coupled_K(piers, dintel, z_full, E, Gsh):
    """Rigidez condensada (n x n) del par acoplado a las traslaciones Y de planta
    (diafragma rigido: c1_j.Y = c2_j.Y = U_y[j])."""
    K, coords, members, nodes, n, meta = _build_coupled_frame(piers, dintel, z_full, E, Gsh)
    ndof = K.shape[0]
    # dofs prescritos: c1_j.Y y c2_j.Y (j=1..n) ; base c1_0,c2_0 fija
    base = []
    for tag in ("c1_0", "c2_0"):
        b0 = 3 * nodes[tag]; base += [b0, b0 + 1, b0 + 2]
    pres = {}
    for j in range(1, n + 1):
        pres[3 * nodes["c1_%d" % j]] = j - 1
        pres[3 * nodes["c2_%d" % j]] = j - 1
    P = list(pres.keys())
    Fr = [i for i in range(ndof) if i not in P and i not in base]
    Kc = np.zeros((n, n))
    KFrFr = K[np.ix_(Fr, Fr)]
    KFrP = K[np.ix_(Fr, P)]
    for j in range(n):
        uP = np.array([1.0 if pres[p] == j else 0.0 for p in P])
        uFr = np.linalg.solve(KFrFr, -KFrP.dot(uP))
        # reaccion en P
        RP = K[np.ix_(P, P)].dot(uP) + K[np.ix_(P, Fr)].dot(uFr)
        for ip, p in enumerate(P):
            Kc[pres[p], j] += RP[ip]
    Kc = 0.5 * (Kc + Kc.T)
    return Kc, meta


def acoplados(piers, dintel, z_full, F_storey_Y, E, Gsh):
    """Resuelve el portico del par bajo las fuerzas de planta Y -> cortante del
    dintel por planta, axil de acoplamiento, DoC y momentos de base."""
    K, coords, members, nodes, n, meta = _build_coupled_frame(piers, dintel, z_full, E, Gsh)
    ndof = K.shape[0]
    base = []
    for tag in ("c1_0", "c2_0"):
        b0 = 3 * nodes[tag]; base += [b0, b0 + 1, b0 + 2]
    free = [i for i in range(ndof) if i not in base]
    Fg = np.zeros(ndof)
    for j in range(1, n + 1):
        Fg[3 * nodes["c1_%d" % j]] += F_storey_Y[j - 1] / 2.0
        Fg[3 * nodes["c2_%d" % j]] += F_storey_Y[j - 1] / 2.0
    U = np.zeros(ndof)
    U[free] = np.linalg.solve(K[np.ix_(free, free)], Fg[free])
    V_lintel = []
    for j in range(1, n + 1):
        ni = nodes["f1_%d" % j]; nj = nodes["f2_%d" % j]
        for (mi, mj, kl, T, d, kind) in members:
            if mi == ni and mj == nj and kind == "dintel":
                fl = kl.dot(T.dot(U[d])); V_lintel.append(abs(fl[1])); break
    V_lintel = np.array(V_lintel)
    N_base = float(np.sum(V_lintel))
    ell = meta["ell_m"]
    M_ot = float(np.sum(np.asarray(F_storey_Y) * np.asarray(z_full[1:])))
    DoC = N_base * ell / M_ot if M_ot > 0 else 0.0
    out = dict(meta)
    out.update({"V_lintel_kN": [v / 1e3 for v in V_lintel],
                "V_lintel_max_kN": float(np.max(V_lintel) / 1e3) if len(V_lintel) else 0.0,
                "N_acopl_base_kN": N_base / 1e3, "M_overturning_kNm": M_ot / 1e3,
                "M_walls_flexion_kNm": (M_ot - N_base * ell) / 1e3, "DoC": DoC, "n_plantas": n})
    return out


# ---------------------------------------------------------------------------
# Elementos del nucleo (pantallas sueltas + par acoplado condensado)
# ---------------------------------------------------------------------------
def build_elements(pantallas, dinteles, z_full, E, Gsh):
    """Lista de elementos {nombre,resiste,xc,yc,Kw}. Los machones acoplados se
    funden en UN elemento Y con la rigidez condensada del par."""
    elems = []; coupling = None
    piers = [p for p in pantallas if p.get("par_acoplado")]
    sueltas = [p for p in pantallas if not p.get("par_acoplado")]
    for p in sueltas:
        Kw = ec8.stick_lateral_stiffness(z_full, E, p["I_m4"], p["A_v_m2"], Gsh, base_fixed=True)
        elems.append({"nombre": p["nombre"], "resiste": p["resiste"],
                      "xc": p["xc_m"], "yc": p["yc_m"], "Kw": Kw, "piers": None})
    if len(piers) >= 2:
        Kc, meta = coupled_K(piers[:2], dinteles, z_full, E, Gsh)
        xc = piers[0]["xc_m"]; yc = 0.5 * (piers[0]["yc_m"] + piers[1]["yc_m"])
        elems.append({"nombre": "NUCLEO_ALMA_acoplada", "resiste": piers[0]["resiste"],
                      "xc": xc, "yc": yc, "Kw": Kc, "piers": [p["nombre"] for p in piers[:2]]})
        coupling = {"meta": meta, "piers": piers[:2]}
    elif len(piers) == 1:
        p = piers[0]
        Kw = ec8.stick_lateral_stiffness(z_full, E, p["I_m4"], p["A_v_m2"], Gsh, base_fixed=True)
        elems.append({"nombre": p["nombre"], "resiste": p["resiste"], "xc": p["xc_m"],
                      "yc": p["yc_m"], "Kw": Kw, "piers": None})
    return elems, coupling


def assemble(elems, z_full, masses, CMx, CMy, Lx, Ly):
    n = len(masses); ndof = 3 * n
    K = np.zeros((ndof, ndof))
    for el in elems:
        ex, ey = _e(el["resiste"]); r = _lever(el["xc"], el["yc"], el["resiste"], CMx, CMy)
        T = np.zeros((n, ndof))
        for j in range(n):
            T[j, j] = ex; T[j, n + j] = ey; T[j, 2 * n + j] = r
        K += T.T.dot(el["Kw"]).dot(T)
    m = np.asarray(masses, float)
    rad2 = (Lx ** 2 + Ly ** 2) / 12.0
    M = np.diag(np.concatenate([m, m, m * rad2]))
    # CR por rigidez escalar de cada elemento (suma de su Kw -> proxy de rigidez)
    kx_sum = ky_sum = crx_num = cry_num = 0.0
    for el in elems:
        ki = float(np.sum(np.abs(el["Kw"])))
        if el["resiste"].upper() == "Y":
            ky_sum += ki; crx_num += ki * el["xc"]
        else:
            kx_sum += ki; cry_num += ki * el["yc"]
    CRx = crx_num / ky_sum if ky_sum else CMx
    CRy = cry_num / kx_sum if kx_sum else CMy
    info = {"CRx": CRx, "CRy": CRy, "CMx": CMx, "CMy": CMy,
            "e0x_m": CMx - CRx, "e0y_m": CMy - CRy, "Lx_m": Lx, "Ly_m": Ly}
    return K, M, info


def modal(K, M, n):
    try:
        from scipy.linalg import eigh
        w2, phi = eigh(K, M)
    except Exception:
        Minv_sqrt = np.diag(1.0 / np.sqrt(np.diag(M)))
        A = Minv_sqrt.dot(K).dot(Minv_sqrt)
        w2, y = np.linalg.eigh(A); phi = Minv_sqrt.dot(y)
    w2 = np.clip(w2, 0.0, None); omega = np.sqrt(w2)
    T = np.where(omega > 0, 2.0 * math.pi / np.where(omega > 0, omega, 1.0), 0.0)
    ndof = 3 * n
    for i in range(ndof):
        mi = phi[:, i].dot(M).dot(phi[:, i])
        if mi > 0:
            phi[:, i] /= math.sqrt(mi)
    rX = np.concatenate([np.ones(n), np.zeros(n), np.zeros(n)])
    rY = np.concatenate([np.zeros(n), np.ones(n), np.zeros(n)])
    rT = np.concatenate([np.zeros(n), np.zeros(n), np.ones(n)])
    MX = float(np.sum(np.diag(M)[:n]))
    order = np.argsort(T)[::-1]
    modes = []
    for k, idx in enumerate(order):
        ph = phi[:, idx]
        gX = ph.dot(M).dot(rX); gY = ph.dot(M).dot(rY); gT = ph.dot(M).dot(rT)
        modes.append({"modo": k + 1, "T_s": float(T[idx]),
            "MeffX_frac": float(gX ** 2 / MX) if MX else 0.0,
            "MeffY_frac": float(gY ** 2 / MX) if MX else 0.0,
            "tipo": ("X" if gX ** 2 >= max(gY ** 2, gT ** 2)
                     else ("Y" if gY ** 2 >= gT ** 2 else "torsion"))})
    return {"modos": modes, "sumMeffX": sum(m["MeffX_frac"] for m in modes),
            "sumMeffY": sum(m["MeffY_frac"] for m in modes), "T1": modes[0]["T_s"]}


def T1_dir(modal_res, direccion):
    cand = [mm["T_s"] for mm in modal_res["modos"] if mm["tipo"] == direccion]
    return max(cand) if cand else modal_res["T1"]


def _solve(elems, K, n, CMx, CMy, F):
    U = np.linalg.solve(K, F)
    ux = U[:n]; uy = U[n:2 * n]; th = U[2 * n:]
    res = []
    for el in elems:
        ex, ey = _e(el["resiste"]); r = _lever(el["xc"], el["yc"], el["resiste"], CMx, CMy)
        d = ex * ux + ey * uy + r * th
        f = el["Kw"].dot(d)
        res.append({"f": f, "V": float(np.sum(f))})
    return res, (ux, uy, th)


def distribuir(elems, K, n, info, F_storey, direccion, e_acc):
    CMx, CMy = info["CMx"], info["CMy"]
    F = np.zeros(3 * n); off = 0 if direccion.upper() == "X" else n
    F[off:off + n] = np.asarray(F_storey, float)
    nat, U = _solve(elems, K, n, CMx, CMy, F)
    Fa = np.zeros(3 * n); Fa[2 * n:] = np.asarray(F_storey, float) * e_acc
    accp, _ = _solve(elems, K, n, CMx, CMy, F + Fa)
    accm, _ = _solve(elems, K, n, CMx, CMy, F - Fa)
    out = []
    for i, el in enumerate(elems):
        Vnat = nat[i]["V"]
        Venv = max(abs(accp[i]["V"]), abs(accm[i]["V"]), abs(Vnat))
        f_env = accp[i]["f"] if abs(accp[i]["V"]) >= abs(accm[i]["V"]) else accm[i]["f"]
        out.append({"nombre": el["nombre"], "resiste": el["resiste"], "piers": el["piers"],
            "V_directo_torsion_kN": Vnat / 1e3, "V_envolvente_kN": Venv / 1e3,
            "f_planta_kN": [x / 1e3 for x in f_env]})
    return {"direccion": direccion, "V_basal_kN": sum(F_storey) / 1e3, "e_acc_m": e_acc,
            "por_pantalla": out, "U": U}


def derivas_globales(U, z_plant, q, half_dim, direccion):
    ux, uy, th = U; n = len(z_plant)
    d_tras = ux if direccion.upper() == "X" else uy
    d_edge = np.abs(d_tras) + np.abs(th) * half_dim
    d_d = q * d_edge
    h = np.diff(np.concatenate(([0.0], z_plant)))
    dr = np.zeros(n); prev = 0.0
    for i in range(n):
        dr[i] = d_d[i] - prev; prev = d_d[i]
    return {"d_elastico_centro_mm": [float(abs(d_tras[i]) * 1e3) for i in range(n)],
            "d_elastico_borde_mm": [float(d_edge[i] * 1e3) for i in range(n)],
            "d_diseno_borde_mm": [float(d_d[i] * 1e3) for i in range(n)],
            "dr_entreplanta_mm": [float(dr[i] * 1e3) for i in range(n)],
            "h_planta_m": [float(x) for x in h],
            "deriva_rel": [float(dr[i] / h[i]) for i in range(n)]}
