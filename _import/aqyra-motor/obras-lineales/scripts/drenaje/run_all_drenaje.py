"""
RUN_ALL DRENAJE -- 5.2-IC de extremo a extremo: hidrologia (caudales de calculo) ->
capacidad de cunetas (drenaje superficial) y ODT (drenaje transversal) -> verificacion
-> rellena el gancho `drenaje` del modelo neutro lineal. Plugin obras-lineales. PT 6.1.

Flujo:  modelo neutro lineal (de iso19650-openbim) + DATOS de drenaje (cuencas,
        cunetas, ODT)  ->  hidrologia.caudal_cuenca (racional 5.2-IC)  ->
        cuneta.comprobar_cuneta / odt.comprobar_odt  ->  verificacion  ->  salidas:
            modelo_neutro_lineal_drenaje.json  (modelo con el gancho `drenaje` relleno)
            resultados_drenaje.json            (caudales + comprobaciones + veredicto)

Los DATOS de drenaje se toman, por orden de prevalencia:
  1) fichero --datos datos_drenaje.json (inyeccion explicita del agente),
  2) modelo["datos_drenaje"] (Pset/GIS volcado al modelo neutro: el dato del proyecto
     PREVALECE sobre cualquier valor por defecto),
  3) si faltan -> error.

Estructura de datos_drenaje.json:
  {
    "cuencas": [ {"id","area_m2"|"area_km2","longitud_m"|"longitud_km","pendiente",
                  "pd_mm","i1_id","po_mm","tipo_elemento"} ],
    "cunetas": [ {"id","cuenca","tipo","b_m","z1","z2","profundidad_m",
                  "pendiente_long","revestimiento"|"n_manning","resguardo_m"} ],
    "odt":     [ {"id","cuenca","tipo","D_m"|("B_m","H_m"),"pendiente_long",
                  "material"|"n_manning"} ]
  }

Uso:  python3 run_all_drenaje.py modelo.json [outdir] --datos datos_drenaje.json
                                 [--tr-cuneta 25] [--tr-odt 100] [--tc-min H]
Predimensionado; revisar y firmar por tecnico competente (ICCP).
"""
import copy
import json
import os
import sys

import cuneta as CU
import hidrologia as H
import odt as OD
import verificacion_drenaje as V


def dimensionar(modelo, datos, tr_cuneta=None, tr_odt=None, tc_min_h=0.0,
                in_place=False):
    """Calcula caudales y comprobaciones y RELLENA el gancho `drenaje` del modelo.
    Devuelve (modelo_actualizado, resultado)."""
    m = modelo if in_place else copy.deepcopy(modelo)

    # 1) hidrologia: un caudal por cuenca (indexado por id)
    caudales, q_por_cuenca = [], {}
    for cu in datos.get("cuencas", []):
        tipo = cu.get("tipo_elemento", "plataforma")
        T = (tr_cuneta if (tr_cuneta is not None and tipo in ("plataforma", "cuneta"))
             else tr_odt if (tr_odt is not None and tipo.startswith("odt"))
             else cu.get("periodo_retorno"))
        q = H.caudal_cuenca(cu, periodo_retorno_anos=T, tipo_elemento=tipo,
                            tc_min_h=tc_min_h)
        caudales.append(q)
        q_por_cuenca[cu.get("id", "cuenca")] = q["caudal_m3_s"]

    # 2) cunetas (drenaje superficial)
    cunetas = []
    for c in datos.get("cunetas", []):
        Q = q_por_cuenca.get(c.get("cuenca"))
        if Q is None:
            raise ValueError("La cuneta %s referencia una cuenca inexistente: %s"
                             % (c.get("id"), c.get("cuenca")))
        cunetas.append(CU.comprobar_cuneta(c, Q))

    # 3) ODT (drenaje transversal)
    odts = []
    for o in datos.get("odt", []):
        Q = q_por_cuenca.get(o.get("cuenca"))
        if Q is None:
            raise ValueError("La ODT %s referencia una cuenca inexistente: %s"
                             % (o.get("id"), o.get("cuenca")))
        odts.append(OD.comprobar_odt(o, Q))

    # 4) rellena el gancho `drenaje` (clave NUEVA; no redefine las existentes, C1 §4bis)
    m["drenaje"] = {
        "norma": "5.2-IC",
        "metodo_hidrologico": "Racional modificado 5.2-IC (Temez)",
        "cuencas": caudales,
        "cunetas": cunetas,
        "odt": odts,
        "nota": "Predimensionado 5.2-IC (calculo local por elemento, sin grafo de red). "
                "Cuenca/lluvia del GIS/Pset si existen. NDP [confirmar AN].",
    }
    resultado = {"caudales": caudales, "cunetas": cunetas, "odt": odts}
    return m, resultado


def _parse(rest):
    opts = {"outdir": None, "datos": None, "tr_cuneta": None, "tr_odt": None,
            "tc_min": 0.0}
    i = 0
    while i < len(rest):
        a = rest[i]
        if a == "--datos": opts["datos"] = rest[i + 1]; i += 2
        elif a == "--tr-cuneta": opts["tr_cuneta"] = float(rest[i + 1]); i += 2
        elif a == "--tr-odt": opts["tr_odt"] = float(rest[i + 1]); i += 2
        elif a == "--tc-min": opts["tc_min"] = float(rest[i + 1]); i += 2
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

    if o["datos"]:
        with open(o["datos"], encoding="utf-8") as fh:
            datos = json.load(fh)
    else:
        datos = modelo.get("datos_drenaje")
    if not datos:
        print("ERROR: faltan datos de drenaje. Pasa --datos datos_drenaje.json o "
              "incluyelos en el modelo neutro (modelo['datos_drenaje']).")
        return 2

    modelo2, res = dimensionar(modelo, datos, tr_cuneta=o["tr_cuneta"],
                               tr_odt=o["tr_odt"], tc_min_h=o["tc_min"])
    ver = V.verificar(modelo2, res)
    res["verificacion"] = ver
    print(V.informe(modelo2, res, ver))

    if o["outdir"]:
        os.makedirs(o["outdir"], exist_ok=True)
        with open(os.path.join(o["outdir"], "modelo_neutro_lineal_drenaje.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(modelo2, fh, indent=2, ensure_ascii=False)
        with open(os.path.join(o["outdir"], "resultados_drenaje.json"), "w",
                  encoding="utf-8") as fh:
            json.dump(res, fh, indent=2, ensure_ascii=False)
        print("\nSalidas escritas en", o["outdir"])

    return 0 if ver["veredicto"] == "CUMPLE" else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
