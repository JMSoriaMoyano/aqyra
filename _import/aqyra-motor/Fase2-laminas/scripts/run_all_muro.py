"""
Orquestador del MURO de carga.
  IFC -> solver lamina (plano vertical) -> verificacion EC2 muro -> mapas
Memoria: NODE_PATH=$(npm root -g) node generate_memoria_muro.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_muro
import verificacion_muro
import plots_muro


def run(proj="proyecto-muro", ifc=None):
    ifc = ifc or os.path.join(proj, "muro.ifc")
    print(f"[1/4] IFC: {ifc}")
    model = solver_muro.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Solver lamina (muro)...")
    _, res = solver_muro.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      equilibrio vert ELU error={res['equilibrio']['error_pct']:.2f}%")
    print("[3/4] Verificacion EC2 muro...")
    out = verificacion_muro.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    c = out["compresion"]
    print(f"      compresion N_Ed={c['N_Ed_kN_m']:.0f} kN/m lambda={c['lambda']:.0f} "
          f"aprov={c['u']*100:.0f}% -> {out['veredicto']}")
    print("[4/4] Mapas...")
    for f in plots_muro.generar(res, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_muro.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-muro"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
