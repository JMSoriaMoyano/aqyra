"""
Solver MIXTO barras + placa (PyNite) a partir del MODELO NEUTRO 3D.

Convenciones (validadas):
 - Ejes X,Y horizontales; Z vertical; gravedad -Z.
 - Barras: seccion con Iy = inercia MAYOR, Iz = menor. Flexion vertical de vigas
   -> momento My, cortante Fz. (ver tests de orientacion).
 - Losa: malla de quads MITC4 (certificada vs Timoshenko en plate_validation.py).
   Esfuerzos de placa por unidad de ancho: [Mx, My, Mxy].
 - La malla de la losa comparte nodos con las vigas perimetrales (apoyo de borde)
   y con las cabezas de pilar.

Salida: dict con esfuerzos de barras, esfuerzos/deformada de placa, reacciones,
y comprobacion de equilibrio vertical.
"""
import sys
import json
from Pynite import FEModel3D
from combinaciones import build_combos

G_ACC = 9.81


def _find_node(m, x, y, z, tol=1e-4):
    for name, nd in m.nodes.items():
        if abs(nd.X - x) < tol and abs(nd.Y - y) < tol and abs(nd.Z - z) < tol:
            return name
    return None


def build_model(model):
    m = FEModel3D()
    for name, mp in model["materiales"].items():
        m.add_material(name, mp["E"], mp["G"], mp["nu"], mp["rho"], fy=mp.get("fy"))
    for name, s in model["secciones"].items():
        m.add_section(name, s["A"], s["Iy"], s["Iz"], s["J"])  # Iy=mayor, Iz=menor

    # secciones/materiales por tipo
    sec_viga = next(b["seccion"] for b in model["barras"].values() if b["tipo"] == "viga")
    sec_pilar = next(b["seccion"] for b in model["barras"].values() if b["tipo"] == "pilar")
    mat_acero = next(b["material"] for b in model["barras"].values())

    surf = model["superficies"][0]
    mat_losa = surf["material"]
    t = surf["espesor"]
    mesh = surf["malla"]

    # esquinas de la losa (coordenadas de los nodos referenciados)
    cor = [model["nodos"][n] for n in surf["esquinas"]]
    xs = [c["x"] for c in cor]; ys = [c["y"] for c in cor]; zsl = cor[0]["z"]
    x0, y0 = min(xs), min(ys)
    W = max(xs) - x0; Hh = max(ys) - y0

    # --- malla de la losa ---
    m.add_rectangle_mesh("LOSA", mesh, W, Hh, t, mat_losa, origin=(x0, y0, zsl), plane="XY")
    m.meshes["LOSA"].generate()

    slab_nodes = [(name, nd) for name, nd in m.nodes.items() if abs(nd.Z - zsl) < 1e-4]

    def on(v, a):
        return abs(v - a) < 1e-4
    perim = [(name, nd) for name, nd in slab_nodes
             if on(nd.X, x0) or on(nd.X, x0 + W) or on(nd.Y, y0) or on(nd.Y, y0 + Hh)]

    # --- vigas perimetrales (segmentos entre nodos consecutivos de cada borde) ---
    edges = {
        "S": sorted([p for p in perim if on(p[1].Y, y0)], key=lambda p: p[1].X),
        "N": sorted([p for p in perim if on(p[1].Y, y0 + Hh)], key=lambda p: p[1].X),
        "W": sorted([p for p in perim if on(p[1].X, x0)], key=lambda p: p[1].Y),
        "E": sorted([p for p in perim if on(p[1].X, x0 + W)], key=lambda p: p[1].Y),
    }
    beam_members = []
    member_sec = {}
    for lab, nodes_e in edges.items():
        for i in range(len(nodes_e) - 1):
            mid = f"V_{lab}{i}"
            m.add_member(mid, nodes_e[i][0], nodes_e[i + 1][0], mat_acero, sec_viga)
            beam_members.append(mid); member_sec[mid] = sec_viga

    # --- pilares (de base z=0 a esquina superior de la malla) ---
    col_members = []
    base_support = []
    corners = [(x0, y0), (x0 + W, y0), (x0 + W, y0 + Hh), (x0, y0 + Hh)]
    for i, (cx, cy) in enumerate(corners, start=1):
        top = _find_node(m, cx, cy, zsl)
        base = f"BASE{i}"
        m.add_node(base, cx, cy, 0.0)
        m.def_support(base, True, True, True, True, True, True)
        m.add_member(f"C{i}", base, top, mat_acero, sec_pilar)
        col_members.append(f"C{i}"); member_sec[f"C{i}"] = sec_pilar
        base_support.append(base)

    # --- cargas ---
    rho_losa = model["materiales"][mat_losa]["rho"]
    peso_losa = rho_losa * G_ACC * t  # N/m2 (autopeso losa, caso G)
    for c in surf["cargas"]:
        for qel in m.quads:
            m.add_quad_surface_pressure(qel, c["qz"], case=c["caso"])
    for qel in m.quads:
        m.add_quad_surface_pressure(qel, -peso_losa, case="G")   # autopeso losa
    rho_acero = model["materiales"][mat_acero]["rho"]
    pp_barras = 0.0
    for mid, sname in member_sec.items():
        L_m = m.members[mid].L()
        w = model["secciones"][sname]["A"] * rho_acero * G_ACC   # N/m (peso propio)
        m.add_member_dist_load(mid, "FZ", -w, -w, case="G")
        pp_barras += w * L_m

    meta_info = {
        "area_losa": W * Hh, "espesor": t, "peso_losa_N_m2": peso_losa,
        "sec_viga": sec_viga, "sec_pilar": sec_pilar, "mat_losa": mat_losa,
        "vigas": beam_members, "pilares": col_members, "bases": base_support,
        "x0": x0, "y0": y0, "W": W, "H": Hh, "z": zsl, "pp_barras_N": pp_barras,
    }
    return m, meta_info, surf


def solve(model):
    m, info, surf = build_model(model)
    casos = sorted({c["caso"] for c in surf["cargas"]} | {"G"})
    combos, meta = build_combos(casos)
    for name, factors in combos.items():
        m.add_load_combo(name, factors)
    m.analyze_linear(check_stability=False)

    res = {"combos_meta": meta, "info": info, "barras": {}, "losa": {},
           "reacciones": {}, "equilibrio": {}}

    # --- barras ---
    all_bars = info["vigas"] + info["pilares"]
    for bid in all_bars:
        mb = m.members[bid]
        L = mb.L()
        res["barras"][bid] = {}
        for combo in combos:
            res["barras"][bid][combo] = {
                "N": -mb.axial(0.0, combo),  # compresion negativa
                "My_max": mb.max_moment("My", combo), "My_min": mb.min_moment("My", combo),
                "Mz_max": mb.max_moment("Mz", combo), "Mz_min": mb.min_moment("Mz", combo),
                "Vz_max": mb.max_shear("Fz", combo), "Vz_min": mb.min_shear("Fz", combo),
                "Vy_max": mb.max_shear("Fy", combo), "Vy_min": mb.min_shear("Fy", combo),
                "L": L,
            }

    # --- losa: esfuerzos por quad (centro) + deformada nodal ---
    for combo in combos:
        quads = []
        for qname, q in m.quads.items():
            M = q.moment(0, 0, True, combo)  # [Mx,My,Mxy] por unidad de ancho
            cx = (q.i_node.X + q.j_node.X + q.m_node.X + q.n_node.X) / 4
            cy = (q.i_node.Y + q.j_node.Y + q.m_node.Y + q.n_node.Y) / 4
            quads.append({"x": cx, "y": cy, "Mx": float(M[0, 0]),
                          "My": float(M[1, 0]), "Mxy": float(M[2, 0])})
        # deformada nodal de la losa
        zsl = info["z"]
        defl = []
        for name, nd in m.nodes.items():
            if abs(nd.Z - zsl) < 1e-4:
                defl.append({"x": nd.X, "y": nd.Y, "dz": nd.DZ[combo]})
        res["losa"][combo] = {"quads": quads, "deformada": defl}

    # --- reacciones y equilibrio ---
    for combo in combos:
        Rz = 0.0
        for base in info["bases"]:
            nd = m.nodes[base]
            Rz += nd.RxnFZ[combo]
        res["reacciones"][combo] = {"Rz_total_kN": Rz / 1e3}

    # equilibrio ELU: carga total aplicada vs reaccion
    area = info["area_losa"]
    qtot = 0.0
    fG = combos["ELU"].get("G", 0.0); fQ = combos["ELU"].get("Q", 0.0)
    for c in surf["cargas"]:
        fac = combos["ELU"].get(c["caso"], 0.0)
        qtot += abs(c["qz"]) * fac
    qtot += info["peso_losa_N_m2"] * fG  # autopeso losa
    carga_losa = qtot * area
    pp_barras_ELU = info["pp_barras_N"] * fG
    aplicada = carga_losa + pp_barras_ELU
    reaccion = res["reacciones"]["ELU"]["Rz_total_kN"] * 1e3
    res["equilibrio"] = {
        "carga_losa_ELU_kN": carga_losa / 1e3,
        "pp_barras_ELU_kN": pp_barras_ELU / 1e3,
        "aplicada_total_ELU_kN": aplicada / 1e3,
        "reaccion_ELU_kN": reaccion / 1e3,
        "error_pct": abs(aplicada - reaccion) / aplicada * 100,
    }
    return m, res


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    model = json.load(open(in_path, encoding="utf-8"))
    _, res = solve(model)
    json.dump(res, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Resultados 3D escritos en:", out_path)
    info = res["info"]
    print(f"  losa {info['W']}x{info['H']} m, t={info['espesor']} m, "
          f"autopeso={info['peso_losa_N_m2']/1e3:.2f} kN/m2")
    print(f"  vigas={len(info['vigas'])} segmentos, pilares={len(info['pilares'])}, "
          f"quads={len(res['losa']['ELU']['quads'])}")
    eq = res["equilibrio"]
    print(f"  EQUILIBRIO ELU: carga losa={eq['carga_losa_ELU_kN']:.1f} kN  "
          f"reaccion={eq['reaccion_ELU_kN']:.1f} kN")
    # envolvente momentos losa
    mx = max(abs(q["Mx"]) for q in res["losa"]["ELU"]["quads"])
    my = max(abs(q["My"]) for q in res["losa"]["ELU"]["quads"])
    print(f"  Losa ELU: |Mx|max={mx/1e3:.1f}  |My|max={my/1e3:.1f} kN·m/m")
