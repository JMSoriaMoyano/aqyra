"""
Parches ANALITICOS del arnes de validacion (FEM-0).

Contrasta el nucleo propio contra soluciones cerradas conocidas:
 - Viga biapoyada (Euler-Bernoulli): flecha 5wL^4/384EI y M = wL^2/8.
 - Voladizo con carga en punta: flecha PL^3/3EI y M_base = PL.
 - Barra a axil: alargamiento PL/EA.
 - Barra a torsion: giro TL/GJ.
 - Placa cuadrada simplemente apoyada (Timoshenko, nu=0.3): w=0.00406 q a^4/D,
   M = 0.0479 q a^2 (tolerancia de malla < 5%).

`validar()` devuelve (ok, checks) con (calculado, teorico, error_relativo).
SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from fem_core import ModeloFEM, ElementoBarra, ElementoLamina  # noqa: E402

E = 210e9; G = 80.77e9; NU = 0.3
A = 8.68e-3; IY = 5.7e-5; IZ = 2.0e-5; JT = 1.0e-6
MAT = {"E": E, "G": G, "nu": NU, "rho": 7850.0}
SEC = {"A": A, "Iy": IY, "Iz": IZ, "J": JT}


def _err(c, t):
    return abs(c - t) / abs(t) if t else abs(c)


def viga_biapoyada(L=6.0, w=-12000.0, ne=8):
    M = ModeloFEM()
    xs = [L * i / ne for i in range(ne + 1)]
    for i, x in enumerate(xs):
        M.add_nodo("n%d" % i, x, 0, 0)
    for i in range(ne):
        el = ElementoBarra("b%d" % i, "n%d" % i, "n%d" % (i + 1),
                           (xs[i], 0, 0), (xs[i + 1], 0, 0), MAT, SEC)
        el.cargas.append({"caso": "Q", "tipo": "global_uniforme", "qz": w})
        M.add_elemento(el)
    M.set_apoyo("n0", [1, 1, 1, 1, 0, 0]); M.set_apoyo("n%d" % ne, [0, 1, 1, 0, 0, 0])
    r = M.resolver()["combos"]["Q"]
    dz = r["desplazamientos"]["n%d" % (ne // 2)][2]
    dz_t = 5 * abs(w) * L ** 4 / (384 * E * IY) * (-1 if w < 0 else 1)
    # M en centro: My del extremo j del elemento izquierdo central
    My_c = r["esfuerzos_barra"]["b%d" % (ne // 2 - 1)]["My_j"]
    Mt = abs(w) * L ** 2 / 8
    return {"flecha_centro_m": (dz, dz_t, _err(dz, dz_t)),
            "M_centro_Nm": (abs(My_c), Mt, _err(abs(My_c), Mt)),
            "equilibrio_N": (r["equilibrio"]["norma_residuo_N"], 0.0, r["equilibrio"]["norma_residuo_N"])}


def voladizo(L=4.0, P=-20000.0, ne=6):
    M = ModeloFEM()
    xs = [L * i / ne for i in range(ne + 1)]
    for i, x in enumerate(xs):
        M.add_nodo("n%d" % i, x, 0, 0)
    for i in range(ne):
        M.add_elemento(ElementoBarra("b%d" % i, "n%d" % i, "n%d" % (i + 1),
                                     (xs[i], 0, 0), (xs[i + 1], 0, 0), MAT, SEC))
    M.set_apoyo("n0", [1, 1, 1, 1, 1, 1])
    M.add_carga_nodal("Q", "n%d" % ne, [0, 0, P, 0, 0, 0])
    r = M.resolver()["combos"]["Q"]
    dz = r["desplazamientos"]["n%d" % ne][2]
    dz_t = P * L ** 3 / (3 * E * IY)
    Mb = r["esfuerzos_barra"]["b0"]["My_i"]
    Mt = abs(P) * L
    return {"flecha_punta_m": (dz, dz_t, _err(dz, dz_t)),
            "M_base_Nm": (abs(Mb), Mt, _err(abs(Mb), Mt))}


def barra_axil(L=3.0, P=500000.0, ne=1):
    M = ModeloFEM()
    M.add_nodo("a", 0, 0, 0); M.add_nodo("b", L, 0, 0)
    M.add_elemento(ElementoBarra("b", "a", "b", (0, 0, 0), (L, 0, 0), MAT, SEC))
    M.set_apoyo("a", [1, 1, 1, 1, 1, 1])
    M.add_carga_nodal("N", "b", [P, 0, 0, 0, 0, 0])
    r = M.resolver()["combos"]["N"]
    u = r["desplazamientos"]["b"][0]
    u_t = P * L / (E * A)
    return {"alargamiento_m": (u, u_t, _err(u, u_t))}


def barra_torsion(L=3.0, T=10000.0):
    M = ModeloFEM()
    M.add_nodo("a", 0, 0, 0); M.add_nodo("b", L, 0, 0)
    M.add_elemento(ElementoBarra("b", "a", "b", (0, 0, 0), (L, 0, 0), MAT, SEC))
    M.set_apoyo("a", [1, 1, 1, 1, 1, 1])
    M.add_carga_nodal("T", "b", [0, 0, 0, T, 0, 0])
    r = M.resolver()["combos"]["T"]
    rx = r["desplazamientos"]["b"][3]
    rx_t = T * L / (G * JT)
    return {"giro_rad": (rx, rx_t, _err(rx, rx_t))}


def placa_timoshenko(a=5.0, t=0.20, Ec=30e9, nu=0.3, q=10e3, n=10):
    h = a / n
    M = ModeloFEM()
    def nm(i, j): return "n%d_%d" % (i, j)
    for i in range(n + 1):
        for j in range(n + 1):
            M.add_nodo(nm(i, j), i * h, j * h, 0.0)
    for i in range(n):
        for j in range(n):
            el = ElementoLamina("q%d_%d" % (i, j),
                                [nm(i, j), nm(i + 1, j), nm(i + 1, j + 1), nm(i, j + 1)],
                                [(i * h, j * h, 0), ((i + 1) * h, j * h, 0),
                                 ((i + 1) * h, (j + 1) * h, 0), (i * h, (j + 1) * h, 0)], t, Ec, nu)
            el.cargas.append({"caso": "Q", "p": q}); M.add_elemento(el)
    for i in range(n + 1):
        for j in range(n + 1):
            edge = i in (0, n) or j in (0, n)
            M.set_apoyo(nm(i, j), [0, 0, 1 if edge else 0, 0, 0, 1])
    M.set_apoyo(nm(0, 0), [1, 1, 1, 0, 0, 1]); M.set_apoyo(nm(n, 0), [0, 1, 1, 0, 0, 1])
    r = M.resolver({"Q": {"Q": 1.0}})["combos"]["Q"]
    w = max((d[2] for d in r["desplazamientos"].values()), key=abs)
    Mmax = max(max(abs(e["Mx"]), abs(e["My"])) for e in r["esfuerzos_lamina"].values())
    D = Ec * t ** 3 / (12 * (1 - nu ** 2))
    w_t = 0.00406 * q * a ** 4 / D; M_t = 0.0479 * q * a ** 2
    return {"flecha_centro_m": (abs(w), w_t, _err(abs(w), w_t)),
            "M_centro_Nm": (Mmax, M_t, _err(Mmax, M_t))}


def validar(tol_barra=1e-6, tol_placa=0.05):
    checks = {}
    checks.update({"viga_" + k: v for k, v in viga_biapoyada().items()})
    checks.update({"voladizo_" + k: v for k, v in voladizo().items()})
    checks.update({"axil_" + k: v for k, v in barra_axil().items()})
    checks.update({"torsion_" + k: v for k, v in barra_torsion().items()})
    checks.update({"placa_" + k: v for k, v in placa_timoshenko().items()})
    ok = True
    for k, (c, t, e) in checks.items():
        tol = tol_placa if k.startswith("placa") else tol_barra
        if k.endswith("equilibrio_N"):
            tol = 1e-3
        if e > tol:
            ok = False
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("=" * 64)
    print("PARCHES ANALITICOS (FEM-0):", "OK" if ok else "FALLO")
    print("=" * 64)
    for k, (c, t, e) in checks.items():
        print("  %-26s calc=%12.6g  teor=%12.6g  err=%.3e" % (k, c, t, e))
    sys.exit(0 if ok else 1)
