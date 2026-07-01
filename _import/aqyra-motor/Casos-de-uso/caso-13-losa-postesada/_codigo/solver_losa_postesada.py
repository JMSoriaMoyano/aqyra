"""
Solver de LOSA PLANA POSTESADA sobre pilares (Caso 13, EC2 §5.10 + §6.4.4).

Reutiliza el parser ortodoxo de laminas/solver_flat (pilares + superficie) y la
malla MITC4 sobre apoyos puntuales, pero ANADE:
  - el caso de carga del PRETENSADO P como presion equivalente hacia ARRIBA
    (balance de cargas 2D: w_p = w_px + w_py), de modo que la flecha de
    permanente queda compensada (contraflecha de balance);
  - combinaciones de servicio/ELU que incluyen P (favorable, gamma_P~1.0);
  - el peso propio g0 (NO viene del IFC: G del IFC = g2 unicamente).

Convencion validada: X,Y horizontales, Z vertical, gravedad -Z; presion hacia
abajo qz<0; el pretensado w_p se aplica como presion qz>0 (hacia arriba).
SI (N, m). [confirmar AN].
"""
import os
import sys
import json
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
G_ACC = 9.81
GAMMA_C = 25000.0   # peso especifico del hormigon armado (N/m3) - practica ES


def _load(name, relpath):
    """Carga un modulo por ruta explicita (salvaguarda de modulos homonimos)."""
    path = os.path.abspath(os.path.join(HERE, relpath))
    sys.path.insert(0, os.path.dirname(path))
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def build_combos_pt(psi2=0.3, psi1=0.5):
    """Combinaciones con G (g2), G0 (peso propio), Q y P (pretensado favorable).
    El pretensado se trata como accion con coeficiente 1.0 (valor medio P_m,inf en
    servicio / ELU). G0 y G son ambas permanentes (gamma=1.35 en ELU)."""
    combos = {
        "ELU":     {"G0": 1.35, "G": 1.35, "Q": 1.50, "P": 1.0},
        "ELU_sinP": {"G0": 1.35, "G": 1.35, "Q": 1.50},
        "ELS_car": {"G0": 1.0, "G": 1.0, "Q": 1.0, "P": 1.0},
        "ELS_fre": {"G0": 1.0, "G": 1.0, "Q": psi1, "P": 1.0},
        "ELS_cp":  {"G0": 1.0, "G": 1.0, "Q": psi2, "P": 1.0},
        "ELS_act": {"Q": 1.0},   # flecha activa (proxy variable)
        "P0_transfer": {"G0": 1.0, "P0": 1.0},  # transferencia (P0 + g0)
    }
    meta = {
        "ELU": "1.35(G0+G) + 1.50 Q + P",
        "ELU_sinP": "1.35(G0+G) + 1.50 Q (sin pretensado, referencia)",
        "ELS_car": "G0+G+Q+P", "ELS_fre": "G0+G+%.1f Q+P" % psi1,
        "ELS_cp": "G0+G+%.1f Q+P" % psi2, "ELS_act": "Q",
        "P0_transfer": "g0 + P0 (transferencia)",
    }
    return combos, meta


def solve(model, w_p_N_m2, w_p0_N_m2=None):
    """Resuelve la placa MITC4 con apoyos puntuales y el caso P del pretensado.
    w_p_N_m2 : presion equivalente del pretensado en servicio (P_m,inf), hacia
               arriba (se aplica como qz=+w_p).
    w_p0_N_m2: presion equivalente en transferencia (P0); si None usa w_p.
    """
    from Pynite import FEModel3D
    if w_p0_N_m2 is None:
        w_p0_N_m2 = w_p_N_m2

    surf = model["superficie"]
    mat = surf["material"]; mp = model["materiales"][mat]
    t = surf["espesor"]; mesh = surf["malla"]
    xs = [p["x"] for p in model["pilares"]]; ys = [p["y"] for p in model["pilares"]]
    x0, y0 = min(xs), min(ys); W = max(xs) - x0; H = max(ys) - y0

    m = FEModel3D()
    m.add_material(mat, mp["E"], mp["G"], mp["nu"], mp["rho"])
    m.add_rectangle_mesh("LOSA", mesh, W, H, t, mat, origin=(x0, y0, 0.0), plane="XY")
    m.meshes["LOSA"].generate()

    def node_at(x, y):
        for nm, nd in m.nodes.items():
            if abs(nd.X - x) < 1e-4 and abs(nd.Y - y) < 1e-4:
                return nm
        return None

    for nm in m.nodes:
        m.def_support(nm, False, False, False, False, False, True)
    col_node = {}
    for p in model["pilares"]:
        nm = node_at(p["x"], p["y"])
        col_node[p["nombre"]] = nm
        m.def_support(nm, False, False, True, False, False, True)
    cen = min(model["pilares"], key=lambda p: (p["x"] - (x0 + W / 2)) ** 2 + (p["y"] - (y0 + H / 2)) ** 2)
    m.def_support(col_node[cen["nombre"]], True, True, True, False, False, True)
    otro = max(model["pilares"], key=lambda p: (p["x"] - cen["x"]) ** 2 + (p["y"] - cen["y"]) ** 2)
    m.def_support(col_node[otro["nombre"]], True, False, True, False, False, True)

    # cargas externas: G (g2 del IFC), Q (del IFC) -- qz negativo (hacia abajo)
    for c in surf["cargas"]:
        for q in m.quads:
            m.add_quad_surface_pressure(q, c["qz"], case=c["caso"])
    # peso propio g0 (NO viene del IFC) en caso G0
    g0 = t * GAMMA_C  # gamma_c=25 kN/m3 (EC2/EHE), = t*25 -> 6.25 kN/m2 (caso 12)
    for q in m.quads:
        m.add_quad_surface_pressure(q, -g0, case="G0")
    # pretensado: presion hacia ARRIBA (qz>0) en caso P (servicio) y P0 (transfer.)
    for q in m.quads:
        m.add_quad_surface_pressure(q, +w_p_N_m2, case="P")
        m.add_quad_surface_pressure(q, +w_p0_N_m2, case="P0")

    combos, meta = build_combos_pt(psi2=0.3, psi1=0.5)
    for nm, fac in combos.items():
        m.add_load_combo(nm, fac)
    m.analyze_linear(check_stability=False)

    res = {"combos_meta": meta, "pilares": {}, "losa": {},
           "info": {"x0": x0, "y0": y0, "W": W, "H": H, "espesor": t,
                    "peso_losa_N_m2": g0, "material": mat, "mesh": mesh,
                    "w_p_N_m2": w_p_N_m2, "w_p0_N_m2": w_p0_N_m2}}

    for p in model["pilares"]:
        nd = m.nodes[col_node[p["nombre"]]]
        res["pilares"][p["nombre"]] = {
            "x": p["x"], "y": p["y"], "lado": p["lado"], "posicion": p["posicion"],
            "Rz": {c: nd.RxnFZ[c] for c in combos},
        }

    for combo in combos:
        quads = []
        for q in m.quads.values():
            M = q.moment(0, 0, True, combo)
            cx = (q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4
            cy = (q.i_node.Y + q.j_node.Y + q.m_node.Y + q.n_node.Y) / 4
            quads.append({"x": cx, "y": cy, "Mx": float(M[0, 0]),
                          "My": float(M[1, 0]), "Mxy": float(M[2, 0])})
        defl = [{"x": nd.X, "y": nd.Y, "dz": nd.DZ[combo]} for nd in m.nodes.values()]
        res["losa"][combo] = {"quads": quads, "deformada": defl}

    # equilibrio ELU (aplicada neta = 1.35(g0+g2)+1.5q - 1.0*w_p)
    area = W * H
    qELU = 1.35 * g0
    for c in surf["cargas"]:
        qELU += abs(c["qz"]) * combos["ELU"].get(c["caso"], 0.0)
    qELU_neta = qELU - 1.0 * w_p_N_m2
    Rz = sum(res["pilares"][p["nombre"]]["Rz"]["ELU"] for p in model["pilares"])
    res["equilibrio"] = {
        "aplicada_neta_ELU_kN": qELU_neta * area / 1e3,
        "reaccion_ELU_kN": Rz / 1e3,
        "error_pct": abs(qELU_neta * area - Rz) / abs(qELU_neta * area) * 100.0,
    }
    return m, res


def parse(ifc_path):
    """Parser ortodoxo (pilares+superficie) reutilizando laminas/solver_flat, con
    incluye_pp=False (g0 lo anade el solver) y lectura del Pset de pretensado."""
    import ifcopenshell
    sf = _load("solver_flat_pt", os.path.join("..", "laminas", "solver_flat.py"))
    model = sf.parse_ortodoxo(ifc_path)
    model["superficie"]["incluye_pp"] = False   # G del IFC = g2; g0 lo anade el solver
    # malla 1,0 m: hace coincidir nodos con las 9 cabezas en {0,8,16} y entra en
    # el presupuesto de calculo del sandbox (0,5 m queda como refinamiento).
    model["superficie"]["malla"] = 1.0

    # leer Pset de pretensado de la superficie
    ifc = ifcopenshell.open(ifc_path)
    sm = ifc.by_type("IfcStructuralSurfaceMember")[0]
    pr = {}
    for rel in getattr(sm, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pd = rel.RelatingPropertyDefinition
            if pd.is_a("IfcPropertySet") and pd.Name == "Pset_Estructurando_Pretensado":
                for p in pd.HasProperties:
                    if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                        pr[p.Name] = p.NominalValue.wrappedValue
    model["pretensado"] = pr
    return model
