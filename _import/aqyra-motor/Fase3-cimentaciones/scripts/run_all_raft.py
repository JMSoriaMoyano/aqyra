"""
Orquestador de la LOSA DE CIMENTACION (raft).
  IFC -> placa sobre muelles (multi-pilar) -> verificacion EC7+EC2 -> mapas
Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_raft.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_raft
import verificacion_raft
import plots_raft


def run(proj=None, ifc=None):
    proj = proj or os.path.join(HERE, "..", "proyecto-losa-cimentacion")
    ifc = ifc or os.path.join(proj, "raft.ifc")
    print("[1/4] IFC:", ifc)
    model = solver_raft.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Placa sobre muelles Winkler (multi-pilar)...")
    _, res = solver_raft.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      equilibrio ELU error %.2f %%  asiento dif %.2f mm"
          % (res["equilibrio"]["error_pct"], res["info"]["asiento_dif_mm"]))
    print("[3/4] Verificacion EC7 (presion/asientos) + EC2 (flexion 2D + punzonamiento)...")
    out = verificacion_raft.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    pc = out["punz_critico"]
    print("      p_max %.0f/%.0f kPa  punz critico %s %.0f%%  -> %s"
          % (out["geotecnia"]["p_max_kPa"], out["geotecnia"]["Rd_kPa"],
             pc["pilar"]["pos"], pc["u_vRdc"] * 100, out["veredicto"]))
    print("[4/4] Mapas...")
    for f in plots_raft.generar(res, out, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_raft.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else None
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
