"""
RUN_ALL FIRME -- selecciona la seccion de firme 6.1-IC de extremo a extremo y
rellena los ganchos del modelo neutro lineal. Plugin obras-lineales. PT 5.2.

Flujo:  modelo neutro lineal (de iso19650-openbim) + datos de trafico/explanada
        ->  bases (categoria de trafico + explanada)  ->  catalogo 6.1-IC (seccion)
        ->  relleno de ganchos firme/secciones_tipo  ->  verificacion  ->  salidas:
            modelo_neutro_lineal_firme.json (modelo con los ganchos rellenos)
            resultados_firme.json (bases + seccion + veredicto)

Los datos de trafico/explanada se toman, por orden de prevalencia:
  1) argumentos de linea de comandos,
  2) Pset del IFC volcado al modelo neutro: modelo["datos_firme"] (IFC PREVALECE),
  3) por defecto: error (debe inyectarlos el agente).

Uso:
  python3 run_all_firme.py modelo.json [outdir] [--imdp N | --imd N --pct P]
                            [--ev2 MPa | --cbr C] [--calzada-unica]
Predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
import json
import os
import sys

import seleccion_firme as S
import verificacion_firme as V


def _parse(rest):
    opts = {"outdir": None, "imdp": None, "imd": None, "pct": None,
            "ev2": None, "cbr": None, "calzada_unica": False}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--imdp": opts["imdp"] = float(rest[i + 1]); i += 2
        elif a == "--imd": opts["imd"] = float(rest[i + 1]); i += 2
        elif a == "--pct": opts["pct"] = float(rest[i + 1]); i += 2
        elif a == "--ev2": opts["ev2"] = float(rest[i + 1]); i += 2
        elif a == "--cbr": opts["cbr"] = float(rest[i + 1]); i += 2
        elif a == "--calzada-unica": opts["calzada_unica"] = True; i += 1
        else: opts["outdir"] = a; i += 1
    return opts


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    o = _parse(argv[1:])
    with open(path, encoding="utf-8") as fh:
        modelo = json.load(fh)

    # respaldo: datos del IFC volcados al modelo neutro (prevalecen si no hay CLI)
    d = modelo.get("datos_firme", {}) or {}
    imdp = o["imdp"] if o["imdp"] is not None else d.get("imdp")
    imd = o["imd"] if o["imd"] is not None else d.get("imd_total")
    pct = o["pct"] if o["pct"] is not None else d.get("pct_pesados")
    ev2 = o["ev2"] if o["ev2"] is not None else d.get("ev2_mpa")
    cbr = o["cbr"] if o["cbr"] is not None else d.get("cbr")
    calz = o["calzada_unica"] or bool(d.get("calzada_unica"))

    if imdp is None and (imd is None or pct is None):
        print("ERROR: faltan datos de trafico (--imdp o --imd y --pct).")
        return 2
    if ev2 is None and cbr is None:
        print("ERROR: faltan datos de explanada (--ev2 o --cbr).")
        return 2

    modelo2, res = S.seleccionar(modelo, imdp=imdp, imd_total=imd, pct_pesados=pct,
                                 ev2_mpa=ev2, cbr=cbr, calzada_unica=calz)
    ver = V.verificar(modelo2, res)
    res["verificacion"] = ver
    print(V.informe(modelo2, res, ver))

    if o["outdir"]:
        os.makedirs(o["outdir"], exist_ok=True)
        with open(os.path.join(o["outdir"], "modelo_neutro_lineal_firme.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(modelo2, fh, indent=2, ensure_ascii=False)
        with open(os.path.join(o["outdir"], "resultados_firme.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("\nSalidas escritas en", o["outdir"])

    return 0 if ver["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
