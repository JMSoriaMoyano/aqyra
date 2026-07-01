"""Comprobaciones de validacion IFC para el dominio de OBRA LINEAL (alineacion).
PT 5.1 (Ola 5). Complementa checks-ifc.py con reglas de ALINEACION georreferenciada
(IFC 4.3 / IFC4X3). Uso: python checks-lineal.py modelo.ifc

Valida esquema, inventario de entidades de alineacion, presencia de GEORREFERENCIA y
CONTINUIDAD/TANGENCIA de la alineacion reutilizando el parser y la validacion de
scripts/lineal (que a su vez reutilizan el nucleo). NO calcula trazado (3.1-IC) ni
firmes (6.1-IC): eso es de la disciplina obras-lineales.
"""
import os
import sys

import ifcopenshell

# scripts/lineal del plugin (parser + validacion de alineacion, sobre el nucleo)
_HERE = os.path.dirname(os.path.abspath(__file__))
_LINEAL = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "scripts", "lineal"))
sys.path.insert(0, _LINEAL)

CLASES_ALINEACION = ("IfcAlignment", "IfcAlignmentHorizontal", "IfcAlignmentVertical",
                     "IfcAlignmentCant", "IfcAlignmentSegment")


def main(path):
    m = ifcopenshell.open(path)
    print("Esquema IFC:", m.schema)
    issues = []

    if m.schema not in ("IFC4X3", "IFC4X3_ADD2", "IFC4X3_ADD1", "IFC4X3_TC1"):
        issues.append(("AVISO", "ESQUEMA", "-",
                       "La alineacion (IfcAlignment) es propia de IFC 4.3; esquema=%s" % m.schema))

    # 1) inventario de entidades de alineacion
    counts = {c: len(m.by_type(c)) for c in CLASES_ALINEACION if m.by_type(c)}
    print("Entidades de alineacion:", counts or "(ninguna)")
    if not m.by_type("IfcAlignment"):
        issues.append(("BLOQUEANTE", "IfcAlignment", "-", "El modelo no declara ningun IfcAlignment"))

    # 2) infraestructura (informativo)
    for c in ("IfcRoad", "IfcRailway", "IfcFacility"):
        if m.by_type(c):
            print("Infraestructura:", c, getattr(m.by_type(c)[0], "Name", "?"))
            break

    # 3) georreferencia: IfcMapConversion + IfcProjectedCRS
    mc = m.by_type("IfcMapConversion")
    crs = m.by_type("IfcProjectedCRS")
    if not mc or not crs:
        issues.append(("BLOQUEANTE", "GEORREF", "-",
                       "Falta georreferencia (IfcMapConversion + IfcProjectedCRS)"))
    else:
        print("Georref:", crs[0].Name, "| origen E=%s N=%s" % (mc[0].Eastings, mc[0].Northings))

    # 4) nomenclatura del eje
    for al in m.by_type("IfcAlignment"):
        if not getattr(al, "Name", None):
            issues.append(("AVISO", "IfcAlignment", getattr(al, "GlobalId", "?"),
                           "IfcAlignment sin Nombre"))

    # 5) CONTINUIDAD / TANGENCIA: parsear -> validar (reutiliza nucleo + scripts/lineal)
    try:
        import ifc_to_model_lineal as parser
        import validacion_alineacion as val
        modelo = parser.parse(path)
        res = val.validar(modelo)
        print("\nValidacion de ALINEACION:", res["veredicto"], "| resumen:", res["resumen"])
        for e in res["errores"]:
            issues.append(("BLOQUEANTE", "ALINEACION", "-", e))
        for w in res["avisos"]:
            issues.append(("AVISO", "ALINEACION", "-", w))
    except Exception as e:
        issues.append(("AVISO", "ALINEACION", "-", "No se pudo validar la alineacion: %s" % e))

    print("\nIncidencias: %d" % len(issues))
    for sev, cls, gid, desc in issues[:200]:
        print("[%s] %s %s: %s" % (sev, cls, gid, desc))
    bloqueantes = [i for i in issues if i[0] == "BLOQUEANTE"]
    print("\nVEREDICTO LINEAL:", "APTO" if not bloqueantes else "NO APTO",
          "(%d bloqueantes)" % len(bloqueantes))
    return 0 if not bloqueantes else 1


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
