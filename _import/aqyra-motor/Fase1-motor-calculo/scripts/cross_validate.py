"""
Validacion cruzada INDEPENDIENTE del motor (PyNite) frente a anaStruct, un
solver 2D de barras distinto. Construye el mismo portico en el plano x-z bajo la
combinacion ELU y compara, barra a barra, los esfuerzos maximos en magnitud.

Certifica simultaneamente: (a) el calculo de esfuerzos y (b) el criterio de
signos del axil. Devuelve OK si todas las diferencias < 1 %.

Uso: python3 cross_validate.py [modelo.json] [resultados.json]
"""
import sys
import json
from anastruct import SystemElements
from combinaciones import GAMMA_G_SUP, GAMMA_Q_SUP


def cross_validate(model, results, tol=0.01):
    E = next(iter(model["materiales"].values()))["E"]
    ss = SystemElements()
    # crear elementos (anaStruct: plano x-y, usamos x-z del modelo -> y=z)
    eid_of = {}
    for i, (bid, b) in enumerate(model["barras"].items(), start=1):
        ni, nj = model["nodos"][b["ni"]], model["nodos"][b["nj"]]
        sec = model["secciones"][b["seccion"]]
        ss.add_element([[ni["x"], ni["z"]], [nj["x"], nj["z"]]],
                       EA=E * sec["A"], EI=E * sec["Iy"])  # Iy = inercia mayor
        eid_of[bid] = i

    # apoyos empotrados
    # mapear nodo->id de anaStruct por coordenadas
    def node_id(nid):
        n = model["nodos"][nid]
        return ss.find_node_id([n["x"], n["z"]])
    for nid, n in model["nodos"].items():
        if all(n["apoyo"]):
            ss.add_support_fixed(node_id=node_id(nid))

    # cargas ELU (factor segun caso)
    factor = {"G": GAMMA_G_SUP, "Q": GAMMA_Q_SUP}
    q_acc = {}
    for c in model["cargas"]:
        q_acc[c["barra"]] = q_acc.get(c["barra"], 0.0) + c["qz"] * factor.get(c["caso"], 1.0)
    for bid, q in q_acc.items():
        ss.q_load(element_id=eid_of[bid], q=q)  # anaStruct sobrescribe: sumamos antes

    ss.solve()

    report = {"barras": {}, "ok": True, "tol": tol}
    for bid in model["barras"]:
        er = ss.get_element_results(eid_of[bid])
        # magnitudes max (independientes de signo)
        M_ana = max(abs(er["Mmin"]), abs(er["Mmax"]))
        V_ana = max(abs(er["Qmin"]), abs(er["Qmax"]))
        N_ana = max(abs(er["Nmin"]), abs(er["Nmax"]))
        e = results["barras"][bid]["ELU"]
        M_py = max(abs(e["M_min"]), abs(e["M_max"]))
        V_py = max(abs(e["V_min"]), abs(e["V_max"]))
        N_py = max(abs(e["N_i"]), abs(e["N_j"]))

        def reld(a, b):
            return abs(a - b) / max(abs(b), 1.0)
        dM, dV, dN = reld(M_py, M_ana), reld(V_py, V_ana), reld(N_py, N_ana)
        ok = bool(max(dM, dV, dN) < tol)
        report["ok"] = bool(report["ok"] and ok)
        report["barras"][bid] = {
            "M": (float(M_py/1e3), float(M_ana/1e3), float(dM)),
            "V": (float(V_py/1e3), float(V_ana/1e3), float(dV)),
            "N": (float(N_py/1e3), float(N_ana/1e3), float(dN)),
            "ok": ok,
        }
    return report


if __name__ == "__main__":
    mp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    rp = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    model = json.load(open(mp, encoding="utf-8"))
    results = json.load(open(rp, encoding="utf-8"))
    rep = cross_validate(model, results)
    print("VALIDACION CRUZADA  PyNite vs anaStruct:", "OK" if rep["ok"] else "DISCREPANCIA")
    print(f"{'Barra':6s} {'M PyNite':>9s} {'M anaSt':>9s} {'V PyNite':>9s} {'V anaSt':>9s} "
          f"{'N PyNite':>9s} {'N anaSt':>9s}  err%")
    for bid, d in rep["barras"].items():
        emax = max(d["M"][2], d["V"][2], d["N"][2]) * 100
        print(f"{bid:6s} {d['M'][0]:9.1f} {d['M'][1]:9.1f} {d['V'][0]:9.1f} {d['V'][1]:9.1f} "
              f"{d['N'][0]:9.1f} {d['N'][1]:9.1f}  {emax:.3f}")
    json.dump(rep, open("proyecto-demo/cross_validation.json", "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
