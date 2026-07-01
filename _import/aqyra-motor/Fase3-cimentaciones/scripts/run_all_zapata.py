"""
Orquestador de la ZAPATA aislada sobre lecho elastico.
  IFC -> solver placa+muelles -> verificacion EC7+EC2 -> mapas
Memoria: NODE_PATH=$(npm root -g) node generate_memoria_zapata.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_zapata
import verificacion_zapata
import plots_zapata


def run(proj="proyecto-zapata", ifc=None):
    ifc = ifc or os.path.join(proj, "zapata.ifc")
    print(f"[1/4] IFC: {ifc}")
    model = solver_zapata.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Solver placa sobre muelles Winkler...")
    _, res = solver_zapata.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      equilibrio ELU error={res['equilibrio']['error_pct']:.2f}%")
    print("[3/4] Verificacion EC7 + EC2...")
    out = verificacion_zapata.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    g = out["geotecnia"]
    print(f"      terreno {g['p_max_kPa']:.0f}/{g['Rd_kPa']:.0f} kPa ({g['u_Rd']*100:.0f}%)  "
          f"punz {out['punzonamiento']['u_vRdc']*100:.0f}%  -> {out['veredicto']}")
    print("[4/4] Mapas...")
    for f in plots_zapata.generar(res, out, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_zapata.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-zapata"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
