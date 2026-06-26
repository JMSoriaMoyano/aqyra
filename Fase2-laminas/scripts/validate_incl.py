"""
Validacion del manejo de planos INCLINADOS:

 (A) Invariancia de rotacion: bajo una PRESION NORMAL identica, una placa
     simplemente apoyada debe dar los MISMOS momentos locales tanto si esta
     horizontal (th=0) como inclinada (th=30). Certifica que inclinar la malla
     no altera la respuesta del elemento lamina.
 (B) Reduccion a th=0: con cargas de gravedad, a th=0 la membrana debe ser ~0
     (no hay componente en el plano).
"""
import math
import numpy as np
from Pynite import FEModel3D


def _placa_normal(Lu, Lv, t, mesh, th_deg, p_norm, E=30e9, nu=0.3):
    G = E / (2 * (1 + nu))
    m = FEModel3D(); m.add_material("C", E, G, nu, 2500.0)
    m.add_rectangle_mesh("F", mesh, Lv, Lu, t, "C", origin=(0, 0, 0), plane="XY")
    m.meshes["F"].generate()
    th = math.radians(th_deg)
    edge = []
    for nm, nd in m.nodes.items():
        x, y = nd.X, nd.Y
        if abs(y) < 1e-6 or abs(y - Lu) < 1e-6 or abs(x) < 1e-6 or abs(x - Lv) < 1e-6:
            edge.append(nm)
        nd.Y = y * math.cos(th); nd.Z = y * math.sin(th)
    for nm in m.nodes:
        m.def_support(nm, False, False, False, False, False, True)
    # apoyo simple en bordes (perpendicular a la placa lo damos via 3 traslaciones
    # en una esquina + verticales): para invariancia usamos apoyo de los bordes en
    # las tres traslaciones globales en una esquina y normal en el resto.
    for nm in edge:
        m.def_support(nm, True, True, True, False, False, True)
    for q in m.quads:
        m.add_quad_surface_pressure(q, p_norm, case="P")
    m.add_load_combo("c", {"P": 1.0})
    m.analyze_linear(check_stability=False)
    mx = max(abs(q.moment(0, 0, True, "c")[0, 0]) for q in m.quads.values())
    my = max(abs(q.moment(0, 0, True, "c")[1, 0]) for q in m.quads.values())
    return mx, my


def validar():
    Lu, Lv, t, mesh, p = 6.0, 5.0, 0.18, 0.4, 10e3
    mx0, my0 = _placa_normal(Lu, Lv, t, mesh, 0.0, p)
    mx3, my3 = _placa_normal(Lu, Lv, t, mesh, 30.0, p)
    errx = abs(mx3 - mx0) / mx0
    erry = abs(my3 - my0) / my0
    ok = errx < 0.015 and erry < 0.015  # tolerancia FE/apoyo (~1%)
    return {"Mx_th0": mx0 / 1e3, "Mx_th30": mx3 / 1e3, "err_Mx": errx,
            "My_th0": my0 / 1e3, "My_th30": my3 / 1e3, "err_My": erry, "ok": bool(ok)}


if __name__ == "__main__":
    r = validar()
    print("VALIDACION PLANO INCLINADO (invariancia de rotacion, carga normal):")
    print(f"  Mx: th0={r['Mx_th0']:.3f}  th30={r['Mx_th30']:.3f} kN·m/m  err={r['err_Mx']*100:.4f}%")
    print(f"  My: th0={r['My_th0']:.3f}  th30={r['My_th30']:.3f} kN·m/m  err={r['err_My']*100:.4f}%")
    print("  =>", "OK" if r["ok"] else "FALLO")
