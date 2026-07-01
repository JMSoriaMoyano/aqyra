"""
Orquestador Fase 1: ejecuta toda la cadena de calculo de extremo a extremo.

  IFC -> modelo neutro -> solver FEM -> validacion cruzada -> verificacion EC3
      -> diagramas -> (memoria Word: ver paso node aparte)

Uso:
  python3 run_all.py [carpeta_proyecto] [archivo.ifc]
Por defecto: carpeta 'proyecto-demo' y su 'portico_demo.ifc'.

La memoria Word se genera despues con:
  NODE_PATH=$(npm root -g) node generate_memoria.js <carpeta_proyecto>
"""
import sys
import os
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import ifc_to_model
import solver as solver_mod
import cross_validate as cv_mod
import verificacion as ver_mod
import plots as plots_mod


def run(proj="proyecto-demo", ifc=None):
    ifc = ifc or os.path.join(proj, "portico_demo.ifc")
    print(f"[1/6] Leyendo IFC: {ifc}")
    model = ifc_to_model.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      nodos={len(model['nodos'])}  barras={len(model['barras'])}  "
          f"cargas={len(model['cargas'])}")

    print("[2/6] Resolviendo (PyNite)...")
    _, results = solver_mod.solve(model)
    json.dump(results, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    print("[3/6] Validacion cruzada (anaStruct)...")
    rep = cv_mod.cross_validate(model, results)
    json.dump(rep, open(os.path.join(proj, "cross_validation.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print(f"      {'OK' if rep['ok'] else 'DISCREPANCIA'}")

    print("[4/6] Verificacion EC3...")
    out = ver_mod.verificar(model, results)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    ad = out["autodiagnostico"]
    print(f"      autodiagnostico={'OK' if ad['valido'] else 'FALLO'}")
    for bid, b in out["barras"].items():
        print(f"      {bid}: {b['veredicto']} (aprov {b['aprovechamiento_max']*100:.1f}%)")

    print("[5/6] Diagramas...")
    for f in plots_mod.generar(model, results, proj):
        print("      ", f)

    print("[6/6] Cadena completa OK. Genera la memoria con:")
    print("       NODE_PATH=$(npm root -g) node scripts/generate_memoria.js", proj)
    return rep["ok"] and ad["valido"] and all(
        b["veredicto"] == "CUMPLE" for b in out["barras"].values())


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo"
    ifc = sys.argv[2] if len(sys.argv) > 2 else None
    ok = run(proj, ifc)
    print("\nRESULTADO GLOBAL:", "TODO CORRECTO" if ok else "REVISAR")
