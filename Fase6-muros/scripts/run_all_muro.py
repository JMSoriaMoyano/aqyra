"""
Orquestador del MURO DE CONTENCION en mensula.
  IFC -> empujes + estabilidad EC7 + esfuerzos (solver barras) -> verificacion -> diagramas
Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_muro.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_muro
import verificacion_muro
import plots_muro


def run(proj=None, ifc=None):
    proj = proj or os.path.join(HERE, "..", "proyecto-muro-mensula")
    ifc = ifc or os.path.join(proj, "muro.ifc")
    print("[1/4] IFC:", ifc)
    model = solver_muro.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[2/4] Empujes + estabilidad EC7 + esfuerzos del alzado (solver de barras)...")
    res = solver_muro.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("[3/4] Verificacion EC7 (vuelco/deslizamiento/hundimiento) + EC2 (alzado/puntera/talon)...")
    out = verificacion_muro.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      vuelco u=%.2f  desliz u=%.2f  hund u=%.2f  -> %s"
          % (out["vuelco"]["u"], out["deslizamiento"]["u"], out["hundimiento"]["u"], out["veredicto"]))
    print("      validacion empuje: error %.2f %%" % out["validacion"]["error_pct"])
    print("[4/4] Diagramas...")
    for f in plots_muro.generar(model, res, out, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_muro.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else None
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
