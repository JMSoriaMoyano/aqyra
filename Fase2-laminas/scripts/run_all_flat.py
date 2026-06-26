"""
Orquestador de la LOSA PLANA sobre pilares (punzonamiento real + dimensionamiento).

  IFC losa plana -> solver placa (apoyos puntuales) -> verificacion EC2
      (flexion, flecha, punzonamiento+dimensionamiento, fisuracion) -> mapas

Uso: python3 run_all_flat.py [carpeta] [archivo.ifc]
Memoria: NODE_PATH=$(npm root -g) node generate_memoria_flat.js <carpeta>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import solver_flat
import verificacion_flat
import plots_flat


def run(proj="proyecto-losa-plana", ifc=None):
    ifc = ifc or os.path.join(proj, "losa_plana.ifc")
    print(f"[1/4] IFC: {ifc}")
    model = solver_flat.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      pilares={len(model['pilares'])}")

    print("[2/4] Solver placa (apoyos puntuales)...")
    _, res = solver_flat.solve(model)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      equilibrio ELU error={res['equilibrio']['error_pct']:.2f}%")

    print("[3/4] Verificacion EC2 (flexion/flecha/punzonamiento/fisuracion)...")
    out = verificacion_flat.verificar(model, res)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    for pos, e in out["punzonamiento"].items():
        c = e["check"]
        extra = ""
        if "dimensionado" in e:
            extra = f" -> canto≥{e['dimensionado']['canto_minimo']['h_min_mm']}mm"
        print(f"      punz {pos}: {c['u_vRdc']*100:.0f}% {'OK' if c['ok'] else 'NO'}{extra}")

    print("[4/4] Mapas y plano de pilares...")
    for f in plots_flat.generar(res, out, proj):
        print("      ", f)
    print("Memoria: NODE_PATH=$(npm root -g) node scripts/generate_memoria_flat.js", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-losa-plana"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    run(proj, ifc)
