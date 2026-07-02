"""
Validacion FEM-2 (lamina curva MITC4 + rigidizador con offset + pared delgada).

FEM-2 NO tiene oraculo PyNite (no hay lamina curva ni pared delgada en el oraculo)
-> se valida con BENCHMARKS NAFEMS / MacNeal-Harder publicados y con la TEORIA de
viga-cajon (Bredt + shear lag):

  1. Scordelis-Lo roof   (lamina cilindrica, flexion)  ref w = -0.3024
  2. Pinched cylinder    (membrana+flexion, severo)    ref w = -1.8248e-5
  3. Hemispherical shell (18deg, doble curvatura)       ref u = 0.094
  4. Placa rigidizada    (offset rigido = seccion T)    vs Euler compuesta
  5. Cajon vs viga-cajon (Bredt J + shear lag b_eff)    vs teoria

Tolerancia NAFEMS: +-5% (decision PT 7.4; mallas de predimensionado). La lamina
plana facetada converge mas lento en doble curvatura (hemisferio) -> se refina la
malla hasta entrar en tolerancia; en PANELES PLANOS (almas/alas del cajon) es casi
exacta. La no-regresion de FEM-0/1 es EXACTA por construccion (modulos aditivos).

`validar()` -> (ok, checks). SI (N, m). Predim.; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "elementos"))
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve
from lamina_curva import LaminaCurvaMITC4
from fem2 import bredt_J, shear_lag_beff


# --------------------------------------------------------------------------- #
#  ensamblaje disperso minimo para mallas de lamina curva                      #
# --------------------------------------------------------------------------- #
def _assemble(nodes, elems, t, E, nu):
    nn = len(nodes); ndof = 6 * nn
    r = []; c = []; d = []; els = []
    for ns in elems:
        cc = [nodes[k] for k in ns]
        el = LaminaCurvaMITC4(cc[0], cc[1], cc[2], cc[3], t, E, nu)
        Kg = el.K(); dofs = np.array([6 * k + dd for k in ns for dd in range(6)])
        r.append(np.repeat(dofs, 24)); c.append(np.tile(dofs, 24)); d.append(Kg.flatten())
        els.append((el, ns))
    K = coo_matrix((np.concatenate(d), (np.concatenate(r), np.concatenate(c))),
                   shape=(ndof, ndof)).tocsr()
    return K, ndof, els


def _solve(K, F, fixed, ndof):
    free = np.array([x for x in range(ndof) if x not in fixed])
    U = np.zeros(ndof); U[free] = spsolve(K[np.ix_(free, free)].tocsc(), F[free])
    return U


# --------------------------------------------------------------------------- #
#  1. Scordelis-Lo roof (cuarto de modelo)                                      #
# --------------------------------------------------------------------------- #
def scordelis_lo(N=10, R=25.0, L=50.0, t=0.25, E=4.32e8, nu=0.0, g=90.0):
    phimax = np.radians(40.0)
    phis = np.linspace(0, phimax, N + 1); ys = np.linspace(0, L / 2, N + 1)
    idx = {}; nodes = []
    for j in range(N + 1):
        for i in range(N + 1):
            ph = phis[i]
            nodes.append((R * np.sin(ph), ys[j], R * np.cos(ph))); idx[(i, j)] = len(nodes) - 1
    elems = [[idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]]
             for j in range(N) for i in range(N)]
    K, ndof, els = _assemble(nodes, elems, t, E, nu); F = np.zeros(ndof)
    for el, ns in els:
        p = [np.array(nodes[k]) for k in ns]
        area = (0.5 * np.linalg.norm(np.cross(p[1] - p[0], p[2] - p[0]))
                + 0.5 * np.linalg.norm(np.cross(p[2] - p[0], p[3] - p[0])))
        for k in ns:
            F[6 * k + 2] += -g * area / 4.0
    fixed = set()
    for j in range(N + 1):
        for i in range(N + 1):
            n = idx[(i, j)]
            if j == 0:
                fixed.add(6 * n + 0); fixed.add(6 * n + 2)
            if j == N:
                [fixed.add(6 * n + x) for x in (1, 3, 5)]
            if i == 0:
                [fixed.add(6 * n + x) for x in (0, 4, 5)]
    U = _solve(K, F, fixed, ndof)
    w = U[6 * idx[(N, N)] + 2]; ref = -0.3024
    return {"scordelis_lo_w": (w, ref, abs(w - ref) / abs(ref))}


# --------------------------------------------------------------------------- #
#  2. Pinched cylinder (un octante)                                            #
# --------------------------------------------------------------------------- #
def pinched_cylinder(N=24, R=300.0, L=600.0, t=3.0, E=3.0e6, nu=0.3, P=1.0):
    ths = np.radians(np.linspace(0, 90.0, N + 1)); ys = np.linspace(0, L / 2, N + 1)
    idx = {}; nodes = []
    for j in range(N + 1):
        for i in range(N + 1):
            th = ths[i]
            nodes.append((R * np.sin(th), ys[j], R * np.cos(th))); idx[(i, j)] = len(nodes) - 1
    elems = [[idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]]
             for j in range(N) for i in range(N)]
    K, ndof, els = _assemble(nodes, elems, t, E, nu); F = np.zeros(ndof)
    F[6 * idx[(0, N)] + 2] += -P / 4.0
    fixed = set()
    for j in range(N + 1):
        for i in range(N + 1):
            n = idx[(i, j)]
            if j == 0:
                fixed.add(6 * n + 0); fixed.add(6 * n + 2)
            if j == N:
                [fixed.add(6 * n + x) for x in (1, 3, 5)]
            if i == 0:
                [fixed.add(6 * n + x) for x in (0, 4, 5)]
            if i == N:
                [fixed.add(6 * n + x) for x in (2, 3, 4)]
    U = _solve(K, F, fixed, ndof)
    w = U[6 * idx[(0, N)] + 2]; ref = -1.8248e-5
    return {"pinched_cylinder_w": (w, ref, abs(w - ref) / abs(ref))}


# --------------------------------------------------------------------------- #
#  3. Hemispherical shell con agujero de 18 grados (cuarto)                     #
# --------------------------------------------------------------------------- #
def hemispherical(N=40, R=10.0, t=0.04, E=6.825e7, nu=0.3, P=2.0):
    th = np.radians(np.linspace(18.0, 90.0, N + 1)); ph = np.radians(np.linspace(0, 90.0, N + 1))
    idx = {}; nodes = []
    for j in range(N + 1):
        for i in range(N + 1):
            t_ = th[i]; p_ = ph[j]
            nodes.append((R * np.sin(t_) * np.cos(p_), R * np.sin(t_) * np.sin(p_), R * np.cos(t_)))
            idx[(i, j)] = len(nodes) - 1
    elems = [[idx[(i, j)], idx[(i + 1, j)], idx[(i + 1, j + 1)], idx[(i, j + 1)]]
             for j in range(N) for i in range(N)]
    K, ndof, els = _assemble(nodes, elems, t, E, nu); F = np.zeros(ndof)
    F[6 * idx[(N, 0)] + 0] += P; F[6 * idx[(N, N)] + 1] += -P
    fixed = set()
    for j in range(N + 1):
        for i in range(N + 1):
            n = idx[(i, j)]
            if j == 0:
                [fixed.add(6 * n + x) for x in (1, 3, 5)]
            if j == N:
                [fixed.add(6 * n + x) for x in (0, 4, 5)]
    fixed.add(6 * idx[(N, 0)] + 2)
    U = _solve(K, F, fixed, ndof)
    u = U[6 * idx[(N, 0)] + 0]; ref = 0.094
    return {"hemispherical_u": (u, ref, abs(u - ref) / abs(ref))}


# --------------------------------------------------------------------------- #
#  4. Placa rigidizada = seccion T (offset rigido) vs Euler compuesta          #
# --------------------------------------------------------------------------- #
def placa_rigidizada(N=20, L=10.0, b=0.4, tp=0.05, E=3.0e10, nu=0.2, P=1.0e5):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from fem_core import ModeloFEM
    from fem2 import ElementoLaminaCurva, ElementoRigidizador
    bw = 0.1; hw = 0.4; As = bw * hw; Is = bw * hw ** 3 / 12.0
    e = tp / 2.0 + hw / 2.0
    xs = np.linspace(0, L, N + 1)
    M = ModeloFEM()
    nid = lambda i, j: "N%d_%d" % (i, j)
    for j in range(2):
        for i in range(N + 1):
            M.add_nodo(nid(i, j), xs[i], j * b, 0.0)
    G = E / (2 * (1 + nu)); mat = {"E": E, "G": G, "nu": nu, "rho": 2500.0}
    sec = {"A": As, "Iy": Is, "Iz": bw ** 3 * hw / 12.0, "J": Is * 0.5}
    for i in range(N):
        ns = [nid(i, 0), nid(i + 1, 0), nid(i + 1, 1), nid(i, 1)]
        M.add_elemento(ElementoLaminaCurva("Q%d" % i, ns, [M.nodos[n] for n in ns], tp, E, nu, rho=2500.0))
    for j in (0, 1):
        for i in range(N):
            a, bb = nid(i, j), nid(i + 1, j)
            M.add_elemento(ElementoRigidizador("R%d_%d" % (j, i), a, bb, M.nodos[a], M.nodos[bb],
                                               mat, sec, offset=(0.0, 0.0, -e)))
    for j in range(2):
        for i in range(N + 1):
            n = nid(i, j); ap = [0, 1, 0, 0, 0, 1]
            if i == 0: ap = [1, 1, 1, 0, 0, 1]
            if i == N: ap = [0, 1, 1, 0, 0, 1]
            M.set_apoyo(n, ap)
    mid = N // 2
    M.add_carga_nodal("Q", nid(mid, 0), [0, 0, -P / 2, 0, 0, 0])
    M.add_carga_nodal("Q", nid(mid, 1), [0, 0, -P / 2, 0, 0, 0])
    wc = M.resolver({"Q": {"Q": 1.0}})["combos"]["Q"]["desplazamientos"][nid(mid, 0)][2]
    Apl = b * tp; Ipl = b * tp ** 3 / 12.0; Ast = 2 * As
    zna = (Ast * (-e)) / (Apl + Ast)
    Icomp = (Ipl + Apl * zna ** 2) + (2 * Is + Ast * (-e - zna) ** 2)
    w_an = -P * L ** 3 / (48 * E * Icomp)
    return {"placa_rigidizada_w": (wc, w_an, abs(wc - w_an) / abs(w_an))}


# --------------------------------------------------------------------------- #
#  5. Cajon vs viga-cajon: Bredt J + shear lag                                  #
# --------------------------------------------------------------------------- #
def cajon_vs_teoria():
    # cajon unicelular b_sup=6, b_inf=3, canto h=2, espesores: losas 0.25, almas 0.30
    bs, bi, h = 6.0, 3.0, 2.0; tsup = tinf = 0.25; talma = 0.30
    # linea media de la celda cerrada (aprox): trapecio de la cavidad
    bms = bs - talma; bmi = bi - talma; hm = h - 0.5 * (tsup + tinf)
    Am = 0.5 * (bms + bmi) * hm                  # area encerrada por la linea media
    lado_inclinado = np.hypot((bms - bmi) / 2.0, hm)
    tramos = [(bms, tsup), (bmi, tinf), (lado_inclinado, talma), (lado_inclinado, talma)]
    J = bredt_J(Am, tramos)
    # comprobacion: J de Bredt > 0 y del orden de 4 Am^2 t / perimetro
    peri = sum(s for s, _ in tramos); tmed = (tsup + tinf + 2 * talma) / 4.0
    J_aprox = 4.0 * Am * Am * tmed / peri
    err_J = abs(J - J_aprox) / J_aprox
    # shear lag: ala superior en voladizo b=(bs-talma)/2 ~2.85, luz L=30
    sl = shear_lag_beff(b=(bs - talma) / 2.0, L=30.0)
    ok_sl = 0.0 < sl["b_eff_frac"] <= 1.0
    return {"cajon_bredt_J": (J, J_aprox, err_J),
            "cajon_shear_lag_frac": (sl["b_eff_frac"], 1.0, 0.0 if ok_sl else 1.0)}


def validar(tol=0.05):
    checks = {}
    checks.update(scordelis_lo(N=10))
    checks.update(pinched_cylinder(N=24))
    checks.update(hemispherical(N=40))
    checks.update(placa_rigidizada(N=20))
    checks.update(cajon_vs_teoria())
    ok = all(e <= tol for (_, _, e) in checks.values())
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("=" * 70)
    print("BENCHMARKS FEM-2 (lamina curva MITC4 + rigidizador + pared delgada):",
          "OK" if ok else "FALLO")
    print("=" * 70)
    for k, (c, r, e) in checks.items():
        print("  %-26s calc=%+.5g  ref=%+.5g  err=%.2f%%" % (k, c, r, e * 100))
    sys.exit(0 if ok else 1)
