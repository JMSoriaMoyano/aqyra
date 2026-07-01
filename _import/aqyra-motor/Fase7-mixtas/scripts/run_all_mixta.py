"""
Orquestador de la VIGA MIXTA (EC4).
  IFC -> esfuerzos viga biapoyada (2 fases) -> verificacion EC4 -> diagramas
Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_mixta.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_mixta
import verificacion_mixta
import plots_mixta


def run(proj=None, ifc=None):
    proj = proj or os.path.join(HERE, "..", "proyecto-viga-mixta")
    ifc = ifc or os.path.join(proj, "viga_mixta.ifc")
    print("[1/4] IFC:", ifc)
    model = solver_mixta.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Esfuerzos viga biapoyada (fase construccion + fase mixta)...")
    res = solver_mixta.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[3/4] Verificacion EC4 (b_eff, M_pl/M_Rd, conexion, cortante, construccion, flecha)...")
    out = verificacion_mixta.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    fm = out["flexion_mixta"]; cx = out["conexion"]
    print("      M_Ed=%.0f/M_Rd=%.0f kNm (%s, grado %.2f)  flecha %.0f%%  -> %s"
          % (fm["M_Ed_kNm"], fm["M_Rd_kNm"], fm["tipo_conexion"], cx["grado_eta"],
             out["flecha"]["u_total"] * 100, out["veredicto"]))
    print("[4/4] Diagramas...")
    for f in plots_mixta.generar(model, res, out, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_mixta.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else None
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
