"""Comprobaciones de validacion IFC para el dominio MEP (instalaciones).
PT 4.2 (Ola 4, hueco H2). Complementa checks-ifc.py con reglas de RED.
Uso: python checks-mep.py modelo.ifc

Valida nomenclatura, Psets estandar y CONTINUIDAD de la red reutilizando el parser
y la validacion de red de scripts/mep (que a su vez reutilizan el nucleo). NO calcula
hidraulica. Adaptar REQUIRED_PSETS_MEP al EIR/LOIN del proyecto.
"""
import os
import sys

import ifcopenshell
import ifcopenshell.util.element as ue

# scripts/mep del plugin (parser + validacion de red, sobre el nucleo)
_HERE = os.path.dirname(os.path.abspath(__file__))
_MEP = os.path.normpath(os.path.join(_HERE, "..", "..", "..", "scripts", "mep"))
sys.path.insert(0, _MEP)

# Psets estandar esperados por clase MEP (ajustar al EIR/LOIN del proyecto). El
# Pset requerido del SEGMENTO depende del TIPO DE SISTEMA (PT 4.5): una red
# ELECTRICAL usa Pset_CableSegmentTypeCommon, una de aire Pset_DuctSegmentTypeCommon
# y una hidraulica (PCI/fontaneria) Pset_PipeSegmentTypeCommon.
_PSET_SEGMENTO_POR_SISTEMA = {
    "ELECTRICAL": "Pset_CableSegmentTypeCommon",
    "POWER": "Pset_CableSegmentTypeCommon",
    "LIGHTING": "Pset_CableSegmentTypeCommon",
    "AIRCONDITIONING": "Pset_DuctSegmentTypeCommon",
    "VENTILATION": "Pset_DuctSegmentTypeCommon",
    "AIRHANDLING": "Pset_DuctSegmentTypeCommon",
    "EXHAUST": "Pset_DuctSegmentTypeCommon",
}
_PSET_SEGMENTO_DEF = "Pset_PipeSegmentTypeCommon"   # hidraulico (PCI/fontaneria) por defecto


def _pset_segmento(tipo_sistema):
    """Pset estandar requerido del IfcFlowSegment segun el tipo de sistema."""
    return _PSET_SEGMENTO_POR_SISTEMA.get(str(tipo_sistema or "").upper(),
                                          _PSET_SEGMENTO_DEF)


REQUIRED_PSETS_MEP = {
    "IfcFlowSegment": [_PSET_SEGMENTO_DEF],   # se sustituye en main() por el del sistema
    "IfcFlowTerminal": [],   # p. ej. Pset_FireSuppressionTerminalTypeCommon (BIE)
}
# Clases del dominio MEP que deben ir agrupadas en un IfcSystem.
CLASES_MEP = ("IfcFlowSegment", "IfcFlowFitting", "IfcFlowTerminal",
              "IfcFlowController", "IfcFlowMovingDevice", "IfcEnergyConversionDevice")

# Pset de RESULTADO de red escrito por la disciplina (write-back, PT 4.4). El
# validador lo RECONOCE (informativo) para confirmar el ciclo IFC->calculo->IFC.
PSET_RESULTADO_RED = "Pset_Estructurando_ResultadoRed"


def main(path):
    m = ifcopenshell.open(path)
    print("Esquema IFC:", m.schema)
    issues = []

    # 1) inventario MEP + sistema
    counts = {}
    for el in m.by_type("IfcDistributionElement"):
        counts[el.is_a()] = counts.get(el.is_a(), 0) + 1
    print("Elementos MEP por clase:", counts)
    sistemas = m.by_type("IfcSystem")  # incluye IfcDistributionSystem (subtipo)
    tipo_sistema = None
    if not sistemas:
        issues.append(("AVISO", "IfcSystem", "-", "El modelo no declara IfcSystem/IfcDistributionSystem"))
    else:
        for s in sistemas:
            pt = getattr(s, "PredefinedType", None)
            if tipo_sistema is None and pt:
                tipo_sistema = pt
            print("Sistema:", s.is_a(), getattr(s, "Name", "?"), "PredefinedType=", pt)
    # Pset de segmento requerido segun el tipo de sistema (PT 4.5): Cable/Duct/Pipe.
    req_seg = _pset_segmento(tipo_sistema)
    required = dict(REQUIRED_PSETS_MEP)
    required["IfcFlowSegment"] = [req_seg]
    print("Pset de segmento requerido (sistema %s): %s" % (tipo_sistema or "?", req_seg))

    # 1bis) Psets de RESULTADO de red (write-back disciplina, PT 4.4): informativo
    con_resultado = [el for el in m.by_type("IfcDistributionElement")
                     if PSET_RESULTADO_RED in ue.get_psets(el)]
    if con_resultado:
        print("Psets de resultado de red (%s): %d elemento(s) enriquecidos "
              "(write-back IFC->calculo->IFC)" % (PSET_RESULTADO_RED, len(con_resultado)))

    # 2) nomenclatura + Psets + puertos por elemento
    for el in m.by_type("IfcDistributionElement"):
        cls, gid = el.is_a(), getattr(el, "GlobalId", "?")
        if not getattr(el, "Name", None):
            issues.append(("AVISO", cls, gid, "Elemento MEP sin Nombre"))
        psets = ue.get_psets(el)
        for req in required.get(cls, []):
            if req not in psets:
                issues.append(("BLOQUEANTE", cls, gid, "Falta Pset requerido: %s" % req))
        # los segmentos deben tener >= 2 puertos para definir un tramo
        if cls == "IfcFlowSegment":
            n_ports = _num_puertos(el)
            if n_ports < 2:
                issues.append(("BLOQUEANTE", cls, gid,
                               "IfcFlowSegment con %d puerto(s) (se requieren 2)" % n_ports))

    # 3) CONTINUIDAD de la red: parsear -> validar (reutiliza nucleo + scripts/mep)
    veredicto = None
    try:
        import ifc_to_model_mep as parser
        import validacion_red as vr
        modelo = parser.parse(path)
        res = vr.validar(modelo)
        veredicto = res["veredicto"]
        print("\nValidacion de RED:", veredicto, "| resumen:", res["resumen"])
        for e in res["errores"]:
            issues.append(("BLOQUEANTE", "RED", "-", e))
        for w in res["avisos"]:
            issues.append(("AVISO", "RED", "-", w))
    except Exception as e:
        issues.append(("AVISO", "RED", "-", "No se pudo validar la red: %s" % e))

    print("\nIncidencias: %d" % len(issues))
    for sev, cls, gid, desc in issues[:200]:
        print("[%s] %s %s: %s" % (sev, cls, gid, desc))
    bloqueantes = [i for i in issues if i[0] == "BLOQUEANTE"]
    print("\nVEREDICTO MEP:", "APTO" if not bloqueantes else "NO APTO",
          "(%d bloqueantes)" % len(bloqueantes))
    return 0 if not bloqueantes else 1


def _num_puertos(el):
    n = 0
    for rel in getattr(el, "IsNestedBy", []) or []:
        for o in getattr(rel, "RelatedObjects", []) or []:
            if o.is_a("IfcDistributionPort"):
                n += 1
    for rel in getattr(el, "HasPorts", []) or []:
        if getattr(rel, "RelatingPort", None) is not None:
            n += 1
    return n


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(sys.argv[1]))
