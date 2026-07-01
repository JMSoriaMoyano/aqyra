"""
MICRO-TEST del soporte lineal (PT 5.1, Ola 5). Solo stdlib + ifcopenshell.
Ejecuta extremo a extremo: genera IFC 4.3 -> parsea -> valida (POSITIVO), y
ademas comprueba que la validacion DETECTA fallos (NEGATIVO): salto en planta,
PK no contiguo y ausencia de georreferencia.

Uso:  PYTHONPATH=/tmp/pylibs python3 test_lineal.py
"""
import copy
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

import generate_test_ifc_lineal as gen
import ifc_to_model_lineal as parser
import validacion_alineacion as val

_fallos = []


def _ok(cond, msg):
    print(("  OK  " if cond else "  XX  ") + msg)
    if not cond:
        _fallos.append(msg)


def main():
    tmp = tempfile.mkdtemp(prefix="lin_")
    ifc = os.path.join(tmp, "eje.ifc")
    gen.main(ifc)
    modelo = parser.parse(ifc)

    print("\n[1] PARSER")
    planta = modelo["alineacion"]["planta"]
    _ok(len(planta) == 5, "planta con 5 segmentos (%d)" % len(planta))
    _ok(abs(modelo["longitud_total"] - 400.0) < 1e-6,
        "longitud total 400 m (%.3f)" % modelo["longitud_total"])
    _ok(modelo["pk_inicio"] == 0.0 and abs(modelo["pk_fin"] - 400.0) < 1e-6,
        "PK 0 -> 400")
    tipos = [s["tipo"] for s in planta]
    _ok(tipos == ["LINE", "CLOTHOID", "CIRCULARARC", "CLOTHOID", "LINE"],
        "secuencia de planta correcta (%s)" % tipos)
    clot = planta[1]
    _ok(clot["A_clotoide"] and abs(clot["A_clotoide"] - (300 * 60) ** 0.5) < 0.1,
        "A de clotoide = sqrt(R*L) = 134.16 (%.2f)" % (clot["A_clotoide"] or 0))
    _ok((modelo["georref"] or {}).get("epsg") == "EPSG:25830",
        "georref EPSG:25830 leida")
    alz = modelo["alineacion"]["alzado"]
    _ok(len(alz) == 3 and abs(alz[0]["cota_ini"] - 100.0) < 1e-6,
        "alzado 3 segmentos, cota inicial 100 m")
    _ok(len(modelo["alineacion"]["peralte"]) == 5, "peralte 5 segmentos")
    _ok(modelo["secciones_tipo"] is None and modelo["firme"] is None
        and modelo["terreno"] is None,
        "ganchos de disciplina (secciones_tipo/firme/terreno) previstos = None")

    print("\n[2] VALIDACION POSITIVA")
    res = val.validar(modelo)
    _ok(res["veredicto"] == "CUMPLE", "veredicto CUMPLE")
    _ok(res["resumen"]["continuidad_max_m"] < val.TOL_XY, "continuidad bajo tolerancia")
    _ok(res["resumen"]["tangencia_max_rad"] < val.TOL_AZ, "tangencia bajo tolerancia")

    print("\n[3] VALIDACION NEGATIVA (debe detectar fallos)")
    # 3a) salto en planta: desplazo el inicio de un segmento
    m1 = copy.deepcopy(modelo)
    m1["alineacion"]["planta"][2]["x_ini"] += 5.0
    r1 = val.validar(m1)
    _ok(r1["veredicto"] == "NO CUMPLE"
        and any("SALTO" in e for e in r1["errores"]),
        "detecta SALTO de continuidad en planta")
    # 3b) PK no contiguo
    m2 = copy.deepcopy(modelo)
    m2["alineacion"]["planta"][3]["pk_ini"] += 10.0
    r2 = val.validar(m2)
    _ok(r2["veredicto"] == "NO CUMPLE"
        and any("PK no contiguo" in e for e in r2["errores"]),
        "detecta PK no contiguo")
    # 3c) sin georreferencia
    m3 = copy.deepcopy(modelo)
    m3["georref"] = None
    r3 = val.validar(m3)
    _ok(r3["veredicto"] == "NO CUMPLE"
        and any("GEORREFERENCIA" in e for e in r3["errores"]),
        "detecta ausencia de georreferencia")

    print("\n" + "=" * 50)
    if _fallos:
        print("FALLOS: %d" % len(_fallos))
        for f in _fallos:
            print("  X", f)
        return 1
    print("TODOS LOS TESTS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
