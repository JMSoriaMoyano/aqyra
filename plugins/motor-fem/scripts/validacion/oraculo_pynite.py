"""
Oraculo PyNite del *strangler* (FEM-0) -- SOLO DESARROLLO/TEST.

Construye modelos de prueba en PyNite (oraculo), los replica en el nucleo propio
con `mallador.desde_pynite` y contrasta desplazamientos, reacciones y esfuerzos.
PyNite vive en otro plugin (aislamiento de runtime); este contraste se ejecuta en
desarrollo con `PYTHONPATH=/tmp/pylibs`, NO en produccion del nucleo nuevo.

Si PyNite no esta disponible, `validar()` devuelve (None, {"skip":...}).
SI (N, m). Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
from __future__ import annotations
import os
import sys
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import mallador  # noqa: E402


def _cmp(m, mine, combo):
    maxd = maxr = maxf = 0.0
    for n in m.nodes:
        nd = m.nodes[n]
        dpy = np.array([nd.DX[combo], nd.DY[combo], nd.DZ[combo],
                        nd.RX[combo], nd.RY[combo], nd.RZ[combo]])
        maxd = max(maxd, float(np.max(np.abs(dpy - np.array(mine["combos"][combo]["desplazamientos"][n])))))
        if any([nd.support_DX, nd.support_DY, nd.support_DZ, nd.support_RX, nd.support_RY, nd.support_RZ]):
            rpy = np.array([nd.RxnFX[combo], nd.RxnFY[combo], nd.RxnFZ[combo],
                            nd.RxnMX[combo], nd.RxnMY[combo], nd.RxnMZ[combo]])
            maxr = max(maxr, float(np.max(np.abs(rpy - np.array(mine["combos"][combo]["reacciones"][n])))))
    for bid, mb in m.members.items():
        L = mb.L(); e = mine["combos"][combo]["esfuerzos_barra"][bid]
        for py, mi in [(mb.axial(0, combo), e["axial_i"]), (mb.axial(L, combo), e["axial_j"]),
                       (mb.shear("Fy", 0, combo), e["Vy_i"]), (mb.moment("Mz", L, combo), e["Mz_j"])]:
            maxf = max(maxf, abs(py - mi))
    for qid, q in m.quads.items():
        Mpy = q.moment(0, 0, True, combo).flatten()
        e = mine["combos"][combo]["esfuerzos_lamina"][qid]
        maxf = max(maxf, float(np.max(np.abs(Mpy - np.array([e["Mx"], e["My"], e["Mxy"]])))))
    return maxd, maxr, maxf


def oraculo_portico():
    from Pynite import FEModel3D
    E, G, nu = 210e9, 80.77e9, 0.3
    m = FEModel3D(); m.add_material("S", E, G, nu, 7850.0)
    m.add_section("s", 7.808e-3, 5.696e-5, 2.003e-5, 5.928e-7)
    m.add_node("N1", 0, 0, 0); m.add_node("N2", 0, 4, 0)
    m.add_node("N3", 6, 4, 0); m.add_node("N4", 6, 0, 0)
    m.add_member("C1", "N1", "N2", "S", "s"); m.add_member("B1", "N2", "N3", "S", "s")
    m.add_member("C2", "N3", "N4", "S", "s")
    m.def_support("N1", 1, 1, 1, 1, 0, 0); m.def_support("N4", 1, 1, 1, 1, 0, 0)
    for nm in m.nodes:
        nd = m.nodes[nm]
        m.def_support(nm, nd.support_DX, nd.support_DY, True, True, True, nd.support_RZ)
    m.add_member_dist_load("B1", "FY", -12000, -12000, case="G")
    m.add_load_combo("ELU", {"G": 1.35})
    m.analyze_linear(check_stability=False)
    M, combos = mallador.desde_pynite(m)
    mine = M.resolver(combos)
    d, r, f = _cmp(m, mine, "ELU")
    return {"portico_desplaz": (d, 0, d), "portico_reac": (r, 0, r), "portico_esf": (f, 0, f)}


def oraculo_placa(n=8):
    from Pynite import FEModel3D
    a, t, E, nu, q = 5.0, 0.2, 30e9, 0.3, 10e3
    m = FEModel3D(); m.add_material("C", E, E / (2 * (1 + nu)), nu, 2500.0)
    m.add_rectangle_mesh("S", a / n, a, a, t, "C", origin=(0, 0, 0), plane="XY")
    m.meshes["S"].generate()
    for nm in m.nodes:
        nd = m.nodes[nm]
        edge = abs(nd.X) < 1e-6 or abs(nd.X - a) < 1e-6 or abs(nd.Y) < 1e-6 or abs(nd.Y - a) < 1e-6
        m.def_support(nm, False, False, edge, False, False, True)
    for nm in m.nodes:
        nd = m.nodes[nm]
        if abs(nd.X) < 1e-6 and abs(nd.Y) < 1e-6:
            m.def_support(nm, True, True, True, False, False, True)
        if abs(nd.X - a) < 1e-6 and abs(nd.Y) < 1e-6:
            m.def_support(nm, False, True, True, False, False, True)
    for q_ in list(m.quads.keys()):
        m.add_quad_surface_pressure(q_, q, case="Q")
    m.add_load_combo("Q", {"Q": 1.0})
    m.analyze_linear(check_stability=False)
    M, combos = mallador.desde_pynite(m)
    mine = M.resolver(combos)
    d, r, f = _cmp(m, mine, "Q")
    return {"placa_desplaz": (d, 0, d), "placa_reac": (r, 0, r), "placa_Mplaca": (f, 0, f)}


def validar(tol_rel=1e-6):
    try:
        import Pynite  # noqa: F401
    except Exception as ex:
        return None, {"skip": "PyNite no disponible (%s)" % ex}
    checks = {}
    checks.update(oraculo_portico())
    checks.update(oraculo_placa())
    # tolerancias absolutas pequenas (EB-vs-EB y DKMQ-vs-DKMQ -> ~maquina)
    ok = all(v[0] < 1e-3 for v in checks.values())
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("=" * 64)
    print("ORACULO PyNite (strangler, FEM-0):", "OK" if ok else ("SKIP" if ok is None else "FALLO"))
    print("=" * 64)
    for k, (c, t, e) in checks.items() if "skip" not in checks else []:
        print("  %-22s max|dif|=%.3e" % (k, c))
    if "skip" in checks:
        print("  ", checks["skip"])
    sys.exit(0 if ok or ok is None else 1)
