"""
Solver FEM (PyNite) a partir del MODELO NEUTRO (JSON).

Convenciones (validadas empiricamente, ver verificacion.py):
 - Plano de la estructura: el modelo IFC esta en plano XZ (Y=0) con gravedad -Z.
   Se remapea a PyNite con  X_p=x,  Y_p=z (vertical),  Z_p=y.
 - Para que la flexion EN EL PLANO use la inercia MAYOR del perfil, se asigna a
   PyNite  Iz = Iy_seccion (mayor)  e  Iy = Iz_seccion (menor).
 - Esfuerzos en el plano:  axil = Fx (axial),  cortante = Fy,  flector = Mz.
 - Se coaccionan los GDL fuera del plano (Z_p, RX_p, RY_p) en todos los nodos
   para estabilizar el modelo plano dentro de un solver 3D.

Salida: dict de resultados por combinacion y por barra (envolventes y arrays
para diagramas), mas reacciones.
"""
import sys
import json
from Pynite import FEModel3D
from combinaciones import build_combos

NPTS = 21  # puntos por barra para diagramas


def _remap_support(apoyo):
    """IFC [DX,DY,DZ,RX,RY,RZ] -> PyNite [DX,DY,DZ,RX,RY,RZ] con Y<->Z intercambiados."""
    DX, DY, DZ, RX, RY, RZ = apoyo
    # X_p=x, Y_p=z, Z_p=y  => trans: DXp=DX, DYp=DZ, DZp=DY ; rot: RXp=RX, RYp=RZ, RZp=RY
    return dict(DX=DX, DY=DZ, DZ=DY, RX=RX, RY=RZ, RZ=RY)


def build_model(model):
    m = FEModel3D()

    # Materiales
    for name, mp in model["materiales"].items():
        m.add_material(name, mp["E"], mp["G"], mp["nu"], mp["rho"], fy=mp.get("fy"))

    # Secciones: Iz <- inercia mayor (Iy_seccion), Iy <- menor (Iz_seccion)
    for name, s in model["secciones"].items():
        m.add_section(name, s["A"], s["Iz"], s["Iy"], s["J"])  # (A, Iy_p=menor, Iz_p=mayor, J)

    # Nodos (remapeo de coords y apoyos) + estabilizacion fuera de plano
    for nid, n in model["nodos"].items():
        Xp, Yp, Zp = n["x"], n["z"], n["y"]
        m.add_node(nid, Xp, Yp, Zp)
        sup = _remap_support(n["apoyo"])
        # coaccionar fuera de plano (Z_p, RX_p, RY_p) en TODOS los nodos
        m.def_support(nid,
                      support_DX=sup["DX"], support_DY=sup["DY"], support_DZ=True,
                      support_RX=True, support_RY=True, support_RZ=sup["RZ"])

    # Barras
    for bid, b in model["barras"].items():
        m.add_member(bid, b["ni"], b["nj"], b["material"], b["seccion"])

    # Cargas distribuidas (qz global -Z  ->  FY global en PyNite, mismo signo)
    for c in model["cargas"]:
        m.add_member_dist_load(c["barra"], "FY", c["qz"], c["qz"], case=c["caso"])

    return m


def solve(model):
    m = build_model(model)
    casos = sorted({c["caso"] for c in model["cargas"]})
    combos, meta = build_combos(casos)
    for name, factors in combos.items():
        m.add_load_combo(name, factors)
    m.analyze_linear()

    results = {"combos_meta": meta, "barras": {}, "reacciones": {}, "longitudes": {}}

    # longitudes de barra
    for bid, b in model["barras"].items():
        ni, nj = model["nodos"][b["ni"]], model["nodos"][b["nj"]]
        Lx = nj["x"] - ni["x"]; Ly = nj["y"] - ni["y"]; Lz = nj["z"] - ni["z"]
        results["longitudes"][bid] = (Lx**2 + Ly**2 + Lz**2) ** 0.5

    for bid in model["barras"]:
        mb = m.members[bid]
        results["barras"][bid] = {}
        for combo in combos:
            N_i = -mb.axial(0.0, combo)  # signo estandar: compresion negativa
            N_j = -mb.axial(results["longitudes"][bid], combo)
            results["barras"][bid][combo] = {
                "N_max": (N_i if abs(N_i) >= abs(N_j) else N_j),
                "N_i": N_i, "N_j": N_j,
                "V_max": mb.max_shear("Fy", combo),
                "V_min": mb.min_shear("Fy", combo),
                "M_max": mb.max_moment("Mz", combo),
                "M_min": mb.min_moment("Mz", combo),
                "T_max": mb.max_torque(combo),
                "defl_min": mb.min_deflection("dy", combo),
                "defl_max": mb.max_deflection("dy", combo),
                # arrays para diagramas
                "x": list(mb.shear_array("Fy", NPTS, combo)[0]),
                "V": list(mb.shear_array("Fy", NPTS, combo)[1]),
                "M": list(mb.moment_array("Mz", NPTS, combo)[1]),
                "defl": list(mb.deflection_array("dy", NPTS, combo)[1]),
            }

    # reacciones en nodos con apoyo
    for nid, n in model["nodos"].items():
        if any(n["apoyo"]):
            nd = m.nodes[nid]
            results["reacciones"][nid] = {
                combo: {"RX": nd.RxnFX[combo], "RY": nd.RxnFY[combo],
                        "RZ": nd.RxnFZ[combo], "MZ": nd.RxnMZ[combo]}
                for combo in combos
            }

    return m, results


if __name__ == "__main__":
    in_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    with open(in_path, encoding="utf-8") as fh:
        model = json.load(fh)
    _, results = solve(model)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    print("Resultados escritos en:", out_path)
    # resumen ELU
    print("\n=== Envolvente ELU (1.35G+1.50Q) ===")
    for bid, r in results["barras"].items():
        e = r["ELU"]
        print(f" {bid}: N={max(abs(e['N_i']),abs(e['N_j']))/1e3:7.1f} kN  "
              f"V=[{e['V_min']/1e3:6.1f},{e['V_max']/1e3:6.1f}] kN  "
              f"M=[{e['M_min']/1e3:7.1f},{e['M_max']/1e3:7.1f}] kN·m")
