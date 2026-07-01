"""
Orquestador Fase 2: cadena completa del modelo mixto barras + losa.

  IFC 3D -> modelo neutro -> solver mixto -> verificacion EC2/EC3 -> mapas

Uso: python3 run_all.py [carpeta] [archivo.ifc]
Memoria Word: NODE_PATH=$(npm root -g) node generate_memoria_fase2.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import ifc_to_model_3d
import solver_3d
import verificacion_ec2
import plots_3d


def run(proj="proyecto-demo", ifc=None):
    ifc = ifc or os.path.join(proj, "modulo_demo.ifc")
    print(f"[1/5] IFC: {ifc}")
    model = ifc_to_model_3d.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      nodos={len(model['nodos'])} barras={len(model['barras'])} "
          f"superficies={len(model['superficies'])}")

    print("[2/5] Solver mixto barras+placa...")
    _, res = solver_3d.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    eq = res["equilibrio"]
    print(f"      equilibrio ELU error={eq['error_pct']:.2f}%")

    print("[3/5] Verificacion EC2 (losa) + EC3 (barras)...")
    out = verificacion_ec2.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      placa={'OK' if out['autodiagnostico_placa']['valido'] else 'FALLO'}  "
          f"losa={out['losa']['veredicto']}")

    print("[4/5] Mapas de color y vista 3D...")
    for f in plots_3d.generar(model, res, proj):
        print("      ", f)

    print("[5/5] Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_fase2.py", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    out = run(proj, ifc)
    print("\nRESULTADO:", "LOSA " + out["losa"]["veredicto"])
