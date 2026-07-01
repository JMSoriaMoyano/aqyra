"""
Autodiagnostico de los elementos PLACA (quad MITC4 de PyNite) frente a la
solucion analitica de Timoshenko de una losa cuadrada simplemente apoyada con
carga uniforme (coeficientes para nu = 0.3):

    w_max = 0.00406 * q * a^4 / D       D = E t^3 / (12 (1 - nu^2))
    M_max = 0.0479  * q * a^2           (por unidad de ancho, en el centro)

Devuelve OK si los errores son aceptables para una malla fina (< 5 %).
"""
from Pynite import FEModel3D


def validar(a=5.0, t=0.20, E=30e9, nu=0.3, q=10e3, mesh=0.25):
    D = E * t**3 / (12 * (1 - nu**2))
    G = E / (2 * (1 + nu))
    m = FEModel3D()
    m.add_material("C", E, G, nu, 2500.0)
    m.add_rectangle_mesh("S", mesh, a, a, t, "C", origin=(0, 0, 0), plane="XY")
    m.meshes["S"].generate()

    # Bordes simplemente apoyados (DZ=0); membrana/drilling coaccionados
    for name, nd in m.nodes.items():
        x, y = nd.X, nd.Y
        edge = abs(x) < 1e-6 or abs(x - a) < 1e-6 or abs(y) < 1e-6 or abs(y - a) < 1e-6
        m.def_support(name, False, False, edge, False, False, True)
    # eliminar solido rigido en plano
    for name, nd in m.nodes.items():
        if abs(nd.X) < 1e-6 and abs(nd.Y) < 1e-6:
            m.def_support(name, True, True, True, False, False, True)
        if abs(nd.X - a) < 1e-6 and abs(nd.Y) < 1e-6:
            m.def_support(name, False, True, True, False, False, True)

    for q_el in list(m.quads.keys()):
        m.add_quad_surface_pressure(q_el, q, case="Q")
    m.add_load_combo("c", {"Q": 1.0})
    m.analyze_linear(check_stability=False)

    wc = max((nd.DZ["c"] for nd in m.nodes.values()), key=abs)
    Mmax = 0.0
    for qel in m.quads.values():
        M = qel.moment(0, 0, True, "c")
        Mmax = max(Mmax, abs(M[0, 0]), abs(M[1, 0]))

    w_t = 0.00406 * q * a**4 / D
    M_t = 0.0479 * q * a**2
    checks = {
        "flecha (mm)": (abs(wc) * 1e3, w_t * 1e3, abs(abs(wc) - w_t) / w_t),
        "M_max (kN·m/m)": (Mmax / 1e3, M_t / 1e3, abs(Mmax - M_t) / M_t),
    }
    ok = all(err < 0.05 for _, _, err in checks.values())
    return ok, checks


if __name__ == "__main__":
    ok, checks = validar()
    print("AUTODIAGNOSTICO PLACA (Timoshenko):", "OK" if ok else "FALLO")
    for k, (c, teo, err) in checks.items():
        print(f"   {k}: calc={c:.3f}  teor={teo:.3f}  err={err*100:.2f}%")
