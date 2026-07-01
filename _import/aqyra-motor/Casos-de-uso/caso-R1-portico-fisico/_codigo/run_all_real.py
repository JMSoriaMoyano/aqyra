"""
Orquestador DIRECCION 2: IFC FISICO (BIM real) -> calculo de extremo a extremo.

  IFC fisico --[puente_analitico]--> modelo neutro --[clasificar/enrutar]-->
      modulo del motor (R1: barras/EC3) --> solver FEM --> validacion cruzada -->
      verificacion EC --> diagramas --> (memoria Word aparte)

A diferencia de run_all.py (que parte de un IFC ortodoxo del dominio de analisis),
aqui el primer paso es el PUENTE: deriva el modelo analitico (ejes, nudos, apoyos)
desde la GEOMETRIA fisica y aplica las hipotesis de carga/apoyo (Pset). El resto de
la cadena es el motor existente SIN CAMBIOS.

Uso:
  python3 puente_analitico/run_all_real.py [carpeta_proyecto] [archivo_fisico.ifc]
La memoria Word se genera despues con:
  NODE_PATH=$(npm root -g) node puente_analitico/generate_memoria_real.js <carpeta>
"""
import sys
import os
import json

_HERE = os.path.dirname(os.path.abspath(__file__))
_BARRAS = os.path.join(os.path.dirname(_HERE), "barras")
sys.path.insert(0, _HERE)
sys.path.insert(0, _BARRAS)

import puente  # noqa: E402
import solver as solver_mod  # noqa: E402  (barras/solver.py)
import cross_validate as cv_mod  # noqa: E402
import verificacion as ver_mod  # noqa: E402
import plots as plots_mod  # noqa: E402


# --- clasificacion sobre el modelo neutro derivado (mismos criterios que
#     scripts/clasificador.py: material S* + seccion en I + orientacion) ------
def _es_acero(mat):
    return bool(mat) and str(mat).strip().upper().startswith("S")


def _es_I(secname):
    s = str(secname or "").upper()
    return any(t in s for t in ("IPE", "HEB", "HEA", "HEM", "IPN"))


def _orient(model, b):
    ni = model["nodos"][b["ni"]]; nj = model["nodos"][b["nj"]]
    dz = abs(nj["z"] - ni["z"])
    dxy = ((nj["x"] - ni["x"]) ** 2 + (nj["y"] - ni["y"]) ** 2) ** 0.5
    return "vertical" if (dz > 1e-6 and dxy < 1e-6) else "horizontal"


def clasificar_neutro(model):
    """Devuelve (modulo, resumen). R1: portico plano de barras de acero -> barras."""
    barras = model["barras"]
    detalle = []
    todas_acero_I = True
    for bid, b in barras.items():
        ac = _es_acero(b.get("material"))
        es_i = _es_I(b.get("seccion"))
        orient = _orient(model, b)
        rol = ("pilar" if orient == "vertical" else "viga/dintel")
        detalle.append({"barra": bid, "material": b.get("material"),
                        "seccion": b.get("seccion"), "orientacion": orient,
                        "rol": rol, "acero_I": bool(ac and es_i)})
        todas_acero_I = todas_acero_I and ac and es_i
    modulo = "barras" if todas_acero_I else "mixto/revisar"
    return modulo, {"sistema": "portico_plano_acero" if todas_acero_I else "heterogeneo",
                    "modulo": modulo, "run_all": "barras/run_all.py",
                    "barras": detalle}


def run(proj, ifc):
    os.makedirs(proj, exist_ok=True)
    print("[1/6] PUENTE fisico->analitico:", ifc)
    model = puente.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      nodos=%d  barras=%d  cargas=%d  (derivados de la geometria)" % (
        len(model["nodos"]), len(model["barras"]), len(model["cargas"])))
    print("      apoyos (hipotesis):", [a["nodo"] + ":" + a["tipo"]
                                        for a in model["hipotesis"]["apoyos"]])

    print("[2/6] Clasificar / enrutar (sobre el modelo neutro derivado)...")
    modulo, rut = clasificar_neutro(model)
    json.dump(rut, open(os.path.join(proj, "clasificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      sistema=%s -> modulo '%s'" % (rut["sistema"], modulo))
    if modulo != "barras":
        print("      [aviso] el sistema no es un portico de acero homogeneo; revisar.")

    print("[3/6] Resolviendo (PyNite, modulo barras)...")
    _, results = solver_mod.solve(model)
    json.dump(results, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)

    print("[4/6] Validacion cruzada (anaStruct)...")
    rep = cv_mod.cross_validate(model, results)
    json.dump(rep, open(os.path.join(proj, "cross_validation.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      %s" % ("OK" if rep["ok"] else "DISCREPANCIA"))

    print("[5/6] Verificacion EC3...")
    out = ver_mod.verificar(model, results)
    json.dump(out, open(os.path.join(proj, "verificacion.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    ad = out["autodiagnostico"]
    print("      autodiagnostico=%s" % ("OK" if ad["valido"] else "FALLO"))
    for bid, b in out["barras"].items():
        print("      %s: %s (aprov %.1f%%)" % (
            bid, b["veredicto"], b["aprovechamiento_max"] * 100))

    print("[6/6] Diagramas...")
    for fpath in plots_mod.generar(model, results, proj):
        print("      ", fpath)

    ok = rep["ok"] and ad["valido"] and all(
        b["veredicto"] == "CUMPLE" for b in out["barras"].values())
    print("\nRESULTADO GLOBAL:", "TODO CORRECTO" if ok else "REVISAR")
    return ok


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-R1"
    ifc = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "caso-R1.ifc")
    run(proj, ifc)
