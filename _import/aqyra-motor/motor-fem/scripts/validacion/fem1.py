"""
Arnes de validacion FEM-1: MODAL + LINEAS DE INFLUENCIA, contra solucion cerrada.

 - Modal viga biapoyada vs f_n = (n^2*pi/(2L^2))*sqrt(E*Iy/(rho*A))  (tol 5%, lumped).
 - Modal voladizo vs f_n = (beta_n/L)^2*sqrt(E*Iy/(rho*A))/(2pi), beta=1.875,4.694,7.855.
 - Linea de influencia de la reaccion de viga isostatica vs (1 - x/L)  (tol 1e-3).
 - Linea de influencia del momento en centro de vano: pico = a*b/L  (tol 1e-2).
 - Viga continua de 2 vanos: equilibrio exacto de las lineas de influencia de
   las reacciones, SUM(IL) = -1 por carga unidad (+Z)  (tol 1e-9).

`validar()` -> (ok, checks) con (calculado, teorico, error). El estatico FEM-0
NO se toca (no-regresion garantizada por construccion: fem1 es aditivo).
SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "elementos"))
from fem_core import ModeloFEM, ElementoBarra  # noqa: E402
import fem1                                     # noqa: E402

E = 210e9; G = 80.77e9; NU = 0.3; RHO = 7850.0
A = 8.68e-3; IY = 5.7e-5; IZ = 2.0e-5; JT = 1.0e-6
MAT = {"E": E, "G": G, "nu": NU, "rho": RHO}
SEC = {"A": A, "Iy": IY, "Iz": IZ, "J": JT}


def _err(c, t):
    return abs(c - t) / abs(t) if t else abs(c)


def _viga(L, ne):
    M = ModeloFEM(); xs = [L * i / ne for i in range(ne + 1)]
    for i, x in enumerate(xs):
        M.add_nodo("n%d" % i, x, 0, 0)
    for i in range(ne):
        M.add_elemento(ElementoBarra("b%d" % i, "n%d" % i, "n%d" % (i + 1),
                                     (xs[i], 0, 0), (xs[i + 1], 0, 0), MAT, SEC))
    for i in range(ne + 1):
        M.set_apoyo("n%d" % i, [0, 1, 0, 1, 0, 1])   # plano xz
    return M, xs


def modal_biapoyada(L=10.0, ne=20):
    M, _ = _viga(L, ne)
    M.set_apoyo("n0", [1, 1, 1, 1, 0, 1]); M.set_apoyo("n%d" % ne, [0, 1, 1, 1, 0, 1])
    r = fem1.modal(M, nmodos=4); m = RHO * A
    out = {}
    for k in (1, 2, 3):
        ft = (k * k * np.pi / (2 * L * L)) * np.sqrt(E * IY / m)
        fc = r["frecuencias_Hz"][k - 1]
        out["modal_ss_f%d_Hz" % k] = (fc, ft, _err(fc, ft))
    return out


def modal_voladizo(L=10.0, ne=20):
    M, _ = _viga(L, ne)
    M.set_apoyo("n0", [1, 1, 1, 1, 1, 1])
    r = fem1.modal(M, nmodos=4); m = RHO * A
    beta = [1.875104, 4.694091, 7.854757]; out = {}
    for k in (1, 2, 3):
        ft = (beta[k - 1] / L) ** 2 * np.sqrt(E * IY / m) / (2 * np.pi)
        fc = r["frecuencias_Hz"][k - 1]
        out["modal_vol_f%d_Hz" % k] = (fc, ft, _err(fc, ft))
    return out


def il_isostatica(L=12.0, ne=24):
    M, _ = _viga(L, ne)
    M.set_apoyo("n0", [1, 1, 1, 1, 0, 1]); M.set_apoyo("n%d" % ne, [0, 1, 1, 1, 0, 1])
    mid = ne // 2
    cfg = {"posiciones": 49,
           "objetivos": [{"id": "RA", "tipo": "reaccion", "nodo": "n0", "comp": 2},
                         {"id": "Mc", "tipo": "esfuerzo_barra", "elem": "b%d" % (mid - 1), "comp": "My_j"}],
           "lineas": [{"id": "v", "camino": ["n%d" % i for i in range(ne + 1)],
                       "tren": {"axles": [{"P": 150e3, "offset": 0.0}, {"P": 150e3, "offset": 1.2}], "udl": 9e3}}]}
    out = fem1.movil(M, cfg)
    d = out["lineas_influencia"]["RA"]["v"]; s = np.array(d["s"]); eta_g = -np.array(d["eta"])
    err_RA = float(np.max(np.abs(np.abs(eta_g) - (1 - s / L))))
    dM = out["lineas_influencia"]["Mc"]["v"]; pico = float(np.max(np.abs(np.array(dM["eta"]))))
    return {"il_reaccion_err": (err_RA, 0.0, err_RA),
            "il_M_centro_pico": (pico, L / 4, _err(pico, L / 4))}


def il_continua(L=10.0, ne=20):
    M, _ = _viga(2 * L, 2 * ne); nN = 2 * ne
    M.set_apoyo("n0", [1, 1, 1, 1, 0, 1]); M.set_apoyo("n%d" % ne, [0, 1, 1, 1, 0, 1])
    M.set_apoyo("n%d" % nN, [0, 1, 1, 1, 0, 1])
    cfg = {"posiciones": 41,
           "objetivos": [{"id": "R0", "tipo": "reaccion", "nodo": "n0", "comp": 2},
                         {"id": "R1", "tipo": "reaccion", "nodo": "n%d" % ne, "comp": 2},
                         {"id": "R2", "tipo": "reaccion", "nodo": "n%d" % nN, "comp": 2}],
           "lineas": [{"id": "v", "camino": ["n%d" % i for i in range(nN + 1)],
                       "tren": {"axles": [{"P": 1.0, "offset": 0}], "udl": 0}}]}
    o = fem1.movil(M, cfg)
    suma = (np.array(o["lineas_influencia"]["R0"]["v"]["eta"])
            + np.array(o["lineas_influencia"]["R1"]["v"]["eta"])
            + np.array(o["lineas_influencia"]["R2"]["v"]["eta"]))
    err = float(np.max(np.abs(suma - (-1.0))))
    return {"il_continua_equilibrio": (err, 0.0, err)}


def il_lamina(L=12.0, B=4.0, nx=12, ny=4):
    """IL de un esfuerzo de PLACA (My) en una losa DKMQ de una direccion (SS).
    Cross-check: el valor de la IL del barrido movil (objetivo esfuerzo_lamina,
    PT 7.2) debe coincidir con el esfuerzo de placa de un solve estatico directo
    con la misma carga nodal unidad (consistencia a precision de maquina)."""
    from fem_core import ElementoLamina
    Em = 35e9; num = 0.2; t = 0.30
    M = ModeloFEM()
    xs = [L * i / nx for i in range(nx + 1)]; ys = [B * j / ny for j in range(ny + 1)]
    nid = lambda i, j: "n_%d_%d" % (i, j)
    for j in range(ny + 1):
        for i in range(nx + 1):
            M.add_nodo(nid(i, j), xs[i], ys[j], 0.0)
    for j in range(ny):
        for i in range(nx):
            el = ElementoLamina("q_%d_%d" % (i, j),
                                [nid(i, j), nid(i + 1, j), nid(i + 1, j + 1), nid(i, j + 1)],
                                [(xs[i], ys[j], 0), (xs[i + 1], ys[j], 0),
                                 (xs[i + 1], ys[j + 1], 0), (xs[i], ys[j + 1], 0)], t, Em, num)
            el.rho = 2500.0; M.add_elemento(el)
    for j in range(ny + 1):
        for i in range(nx + 1):
            ap = [1, 1, 0, 0, 0, 1]
            if i == 0 or i == nx:
                ap[2] = 1
            M.set_apoyo(nid(i, j), ap)
    target = "q_%d_%d" % (nx // 2 - 1, ny // 2)
    camino = [nid(i, ny // 2) for i in range(nx + 1)]
    cfg = {"posiciones": nx + 1,
           "objetivos": [{"id": "My", "tipo": "esfuerzo_lamina", "elem": target, "comp": "My"}],
           "lineas": [{"id": "c", "camino": camino,
                       "tren": {"axles": [{"P": 1.0, "offset": 0.0}], "udl": 0.0}}]}
    out = fem1.movil(M, cfg)
    d = out["lineas_influencia"]["My"]["c"]; s = np.array(d["s"]); eta = np.array(d["eta"])
    errs = []
    for k in range(len(s)):
        M.cargas_nodales = []
        M.add_carga_nodal("U", camino[k], [0, 0, 1.0, 0, 0, 0])
        r = M.resolver({"U": {"U": 1.0}})
        errs.append(abs(r["combos"]["U"]["esfuerzos_lamina"][target]["My"] - eta[k]))
    M.cargas_nodales = []
    max_err = float(max(errs)); il_sup = float(abs(eta[0]) + abs(eta[-1]))
    return {"il_lamina_consistencia": (max_err, 0.0, max_err),
            "il_lamina_apoyos": (il_sup, 0.0, il_sup)}


def validar():
    checks = {}
    checks.update(modal_biapoyada())
    checks.update(modal_voladizo())
    checks.update(il_isostatica())
    checks.update(il_continua())
    checks.update(il_lamina())
    ok = True
    for k, (c, t, e) in checks.items():
        if k.startswith("modal"):
            tol = 0.05
        elif k == "il_M_centro_pico":
            tol = 1e-2
        elif k == "il_continua_equilibrio":
            tol = 1e-9
        elif k.startswith("il_lamina"):
            tol = 1e-9
        else:
            tol = 1e-3
        if e > tol:
            ok = False
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("=" * 64)
    print("VALIDACION FEM-1 (modal + lineas de influencia):", "OK" if ok else "FALLO")
    print("=" * 64)
    for k, (c, t, e) in checks.items():
        print("  %-26s calc=%12.6g  teor=%12.6g  err=%.3e" % (k, c, t, e))
    sys.exit(0 if ok else 1)
