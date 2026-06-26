"""
Orquestador del PILOTE.
  IFC -> EC7 axil + solver lateral (viga sobre muelles) -> verificacion -> diagramas
Memoria: NODE_PATH=$(npm root -g) node generate_memoria_pilote.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_pilote
import verificacion_pilote
import plots_pilote


def run(proj="proyecto-pilote", ifc=None):
    ifc = ifc or os.path.join(proj, "pilote.ifc")
    print(f"[1/4] IFC: {ifc}")
    model = solver_pilote.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] EC7 axil + solver lateral (viga sobre muelles)...")
    cap = solver_pilote.capacidad_axil(model["pilote"]["D"], model["pilote"]["L"],
                                       model["pilote"]["qs"], model["pilote"]["qb"])
    _, res = solver_pilote.solve(model)
    res["capacidad_axil"] = cap
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      Rc,d={cap['Rc_d_kN']:.0f} kN  equilibrio lateral err={res['equilibrio']['error_pct']:.2f}%")
    print("[3/4] Verificacion EC7 + lateral + EC2...")
    out = verificacion_pilote.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      axil {out['axil_ec7']['u']*100:.0f}%  flecha {out['lateral']['u']*100:.0f}%  -> {out['veredicto']}")
    print("[4/4] Diagramas...")
    for f in plots_pilote.generar(res, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_pilote.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-pilote"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
