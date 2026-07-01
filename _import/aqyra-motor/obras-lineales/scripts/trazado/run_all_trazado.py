"""
RUN_ALL TRAZADO -- orquesta la comprobacion de trazado 3.1-IC de extremo a extremo.
Plugin obras-lineales. PT 5.2 (Ola 5).

Flujo:  modelo neutro lineal (de iso19650-openbim) + Vp  ->  comprobacion 3.1-IC
        (planta/alzado/visibilidad/coordinacion)  ->  verificacion (veredicto)
        ->  resultados_trazado.json

La Vp se toma, por orden de prevalencia:
  1) argumento de linea de comandos (--vp),
  2) Pset del IFC ya volcado al modelo neutro: alineacion.parametros_proyecto.vp_kmh
     o eje.vp_kmh  (el dato del proyecto/IFC PREVALECE),
  3) por defecto, None -> error (debe inyectarla el agente).

Uso:  python3 run_all_trazado.py modelo_neutro_lineal.json [outdir] [--vp 60]
Predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
import json
import os
import sys

import comprobacion_trazado as C
import verificacion_trazado as V


def _vp_del_modelo(modelo):
    """Vp del dato de proyecto (IFC) si esta en el modelo neutro."""
    for ruta in (("alineacion", "parametros_proyecto", "vp_kmh"),
                 ("parametros_proyecto", "vp_kmh"),
                 ("eje", "vp_kmh")):
        d = modelo
        ok = True
        for k in ruta:
            if isinstance(d, dict) and k in d:
                d = d[k]
            else:
                ok = False
                break
        if ok and d:
            return float(d)
    return None


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    path = argv[0]
    outdir = None
    vp_cli = None
    rest = argv[1:]
    i = 0
    while i < len(rest):
        if rest[i] == "--vp" and i + 1 < len(rest):
            vp_cli = float(rest[i + 1])
            i += 2
        else:
            outdir = rest[i]
            i += 1

    with open(path, encoding="utf-8") as fh:
        modelo = json.load(fh)

    vp = vp_cli if vp_cli is not None else _vp_del_modelo(modelo)
    if vp is None:
        print("ERROR: falta la velocidad de proyecto Vp. Pasa --vp <km/h> o inclu"
              "yela en el modelo neutro (Pset del IFC). El dato del IFC prevalece.")
        return 2
    origen = "CLI" if vp_cli is not None else "IFC/modelo neutro"
    print("Velocidad de proyecto Vp = %.0f km/h (origen: %s)" % (vp, origen))

    res = C.comprobar(modelo, vp)
    res["vp_origen"] = origen
    print(V.informe(res))

    if outdir:
        os.makedirs(outdir, exist_ok=True)
        out = os.path.join(outdir, "resultados_trazado.json")
        with open(out, "w", encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("\nResultados escritos en", out)

    return 0 if res["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
