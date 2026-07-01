"""
Orquestador de la CUBIERTA / forjado inclinado.
  IFC -> solver lamina inclinada -> validacion + verificacion EC2 -> mapas
Memoria: NODE_PATH=$(npm root -g) node generate_memoria_incl.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_incl
import verificacion_incl
import plots_incl


def run(proj="proyecto-cubierta", ifc=None):
    ifc = ifc or os.path.join(proj, "cubierta.ifc")
    print(f"[1/4] IFC: {ifc}")
    model = solver_incl.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Solver lamina inclinada...")
    _, res = solver_incl.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      equilibrio ELU error={res['equilibrio']['error_pct']:.2f}%")
    print("[3/4] Validacion + verificacion EC2...")
    out = verificacion_incl.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    v = out["validacion"]
    print(f"      invariancia {'OK' if v['invariancia_rotacion']['ok'] else 'NO'}  "
          f"flecha {out['losa']['flecha']['u_total']*100:.0f}%  "
          f"membrana uRd {out['membrana']['u_comp']*100:.1f}%  "
          f"fisuracion {'OK' if out['fisuracion']['ok'] else 'NO'}")
    print("[4/4] Mapas y vista 3D...")
    for f in plots_incl.generar(res, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_incl.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-cubierta"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
