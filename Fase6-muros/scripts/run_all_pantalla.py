"""
Orquestador de la PANTALLA ANCLADA.
  IFC -> empujes + viga-muelles con ancla -> verificacion (empotramiento/ancla/fuste) -> diagramas
Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_pantalla.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_pantalla
import verificacion_pantalla
import plots_pantalla


def run(proj=None, ifc=None):
    proj = proj or os.path.join(HERE, "..", "proyecto-pantalla-anclada")
    ifc = ifc or os.path.join(proj, "pantalla.ifc")
    print("[1/4] IFC:", ifc)
    model = solver_pantalla.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Empujes + pantalla como viga sobre muelles con ancla (solver de barras)...")
    res = solver_pantalla.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      equilibrio horizontal ELU: error %.2f %%" % res["equilibrio"]["error_pct"])
    print("[3/4] Verificacion empotramiento (free-earth) + ancla/bulbo + fuste EC2...")
    out = verificacion_pantalla.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      FoS_pasivo=%.2f  F_ancla=%.0f kN  M_fuste=%.0f kNm/m  -> %s"
          % (out["empotramiento"]["FoS_pasivo"], out["ancla"]["F_ancla_kN"],
             out["fuste"]["flexion"]["M_Ed_kNm_m"], out["veredicto"]))
    print("[4/4] Diagramas...")
    for f in plots_pantalla.generar(model, res, out, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_pantalla.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else None
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
