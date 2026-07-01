"""
Micro-test de la RED MEP de ABASTECIMIENTO (PT 6.3, Ola 6). Genera el IFC de
prueba (deposito + anillo), lo parsea con el parser MEP y valida la red. Comprueba
que el parser reconoce el sistema WATERSUPPLY, el DEPOSITO como FUENTE (ancla de
presion por cota) y la malla, y que la validacion de red CUMPLE (continuidad desde
la fuente). Requiere ifcopenshell -> ejecutar con PYTHONPATH=/tmp/pylibs.

Uso:  PYTHONPATH=/tmp/pylibs python3 test_red_abastecimiento.py
"""
import os
import sys
import tempfile

_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.join(_HERE, "..", "nucleo"))
import generate_test_ifc_abastecimiento as gen
import ifc_to_model_mep as parser
import validacion_red as vr

_fallos = []


def check(cond, msg):
    print(("  OK  " if cond else " FAIL ") + msg)
    if not cond:
        _fallos.append(msg)


tmp = tempfile.mkdtemp()
ifc_path = os.path.join(tmp, "red_abast.ifc")
gen.main(ifc_path)
modelo = parser.parse(ifc_path)

print("== 1. parser: sistema y topologia ==")
check(str(modelo["sistema"]["tipo"]).upper() in
      ("WATERSUPPLY", "DOMESTICCOLDWATER", "POTABLEWATER"),
      "sistema de abastecimiento reconocido (%s)" % modelo["sistema"]["tipo"])
check(len(modelo["nodos"]) == 5 and len(modelo["tramos"]) == 5,
      "5 nodos y 5 tramos (anillo + aduccion)")

print("== 2. parser: DEPOSITO como fuente (ancla de presion por cota) ==")
fuentes = modelo["fuentes"]
check(len(fuentes) == 1, "1 fuente detectada")
check(fuentes[0]["tipo"] == "deposito", "la fuente es un DEPOSITO (IfcTank)")
check(fuentes[0].get("cota_lamina") == 130.0,
      "cota de lamina del deposito leida del Pset (130 m)")
check(len(modelo["vertidos"]) == 0, "abastecimiento: sin vertidos (ancla = fuente)")

print("== 3. parser: terminales (acometidas + hidrante) ==")
ids = sorted(t["id"] for t in modelo["terminales"])
check(ids == ["ACO-1", "ACO-2", "HIDRANTE-1"],
      "3 terminales: ACO-1, ACO-2, HIDRANTE-1")

print("== 4. validacion de red: conexa desde la fuente -> CUMPLE ==")
r = vr.validar(modelo)
check(r["veredicto"] == "CUMPLE", "red de abastecimiento anclada en la fuente -> CUMPLE")
check(r["resumen"]["cobertura_pct"] == 100.0, "cobertura 100 % desde la fuente")

print("== 5. topologia de MALLA (un lazo): m - n + 1 = 1 ==")
m_lazos = len(modelo["tramos"]) - len(modelo["nodos"]) + 1
check(m_lazos == 1, "la red tiene 1 lazo (anillo) para ejercitar Hardy-Cross")

print()
if _fallos:
    print("MICRO-TEST RED ABASTECIMIENTO: %d FALLO(S)" % len(_fallos))
    sys.exit(1)
print("MICRO-TEST RED ABASTECIMIENTO: TODO OK")
