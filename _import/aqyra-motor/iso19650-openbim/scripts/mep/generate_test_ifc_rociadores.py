"""
GENERADOR de IFC MEP de prueba -- RED MALLADA DE ROCIADORES (UNE-EN 12845).
PT 4.4 (Ola 4). Analogo a generate_test_ifc_mep.py (BIE, en arbol) pero con una
red en MALLA (con bucles) para ejercitar el solver de mallas (Hardy-Cross).

Topologia: malla principal en ESCALERA (ladder) de 8 nudos + 6 rociadores colgando
por ramales (drops). La escalera tiene 3 lazos independientes (10 tramos - 8 nudos
+ 1 = 3); los 6 ramales son hojas (no anaden lazos).

    n1--n2--n3--n4      (colector superior, DN100)        ROC-1..3 cuelgan de n2..n4
    |   |   |   |       (montantes/rungs, DN80)
    n5--n6--n7--n8      (colector inferior, DN100)        ROC-4..6 cuelgan de n6..n8
    ^ grupo de presion (fuente) en n1

  - IfcDistributionSystem  PredefinedType=FIREPROTECTION (IFC4)
  - IfcFlowMovingDevice    grupo de presion (fuente / ancla)
  - IfcFlowSegment x16     tuberia (Pset_PipeSegmentTypeCommon: NominalDiameter, Roughness)
  - IfcFlowTerminal x6     rociadores "ROC-n" (el solver les aplica demanda UNE-EN 12845)
  - IfcDistributionPort + IfcRelConnectsPorts : conectividad (estrella por nudo)

La topologia del grafo la fija el SNAP de extremos de segmento (nucleo); los puertos
dan coordenadas y los rociadores/fuente se asocian a su nudo por cercania.

Uso:  python3 generate_test_ifc_rociadores.py salida.ifc
Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
import sys

import ifcopenshell
from ifcopenshell.api import run


def _placement(model, xyz):
    pt = model.create_entity("IfcCartesianPoint", Coordinates=[float(xyz[0]),
                             float(xyz[1]), float(xyz[2])])
    a2p = model.create_entity("IfcAxis2Placement3D", Location=pt)
    return model.create_entity("IfcLocalPlacement", RelativePlacement=a2p)


def _puerto(model, nombre, xyz, flujo):
    po = run("root.create_entity", model, ifc_class="IfcDistributionPort", name=nombre)
    po.ObjectPlacement = _placement(model, xyz)
    try:
        po.FlowDirection = flujo
    except Exception:
        pass
    return po


def _nest(model, elemento, puertos):
    model.create_entity("IfcRelNests", GlobalId=ifcopenshell.guid.new(),
                        RelatingObject=elemento, RelatedObjects=puertos)


def _connect(model, pa, pb):
    model.create_entity("IfcRelConnectsPorts", GlobalId=ifcopenshell.guid.new(),
                        RelatingPort=pa, RelatedPort=pb)


def main(out):
    model = ifcopenshell.file(schema="IFC4")
    run("root.create_entity", model, ifc_class="IfcProject", name="Red rociadores prueba")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")     # metro (sin prefijo)
    run("unit.assign_unit", model, units=[_u])
    run("context.add_context", model, context_type="Model")
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Edificio")
    storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Planta 00")
    prj = model.by_type("IfcProject")[0]
    run("aggregate.assign_object", model, relating_object=prj, products=[site])
    run("aggregate.assign_object", model, relating_object=site, products=[building])
    run("aggregate.assign_object", model, relating_object=building, products=[storey])

    elementos = []
    puertos_por_nudo = {}   # coord redondeada -> [puertos] (para conectividad)

    def reg_puerto(po, xyz):
        k = (round(xyz[0], 3), round(xyz[1], 3), round(xyz[2], 3))
        puertos_por_nudo.setdefault(k, []).append(po)

    def crear(cls, nombre, origen, pred=None):
        el = run("root.create_entity", model, ifc_class=cls, name=nombre)
        el.ObjectPlacement = _placement(model, origen)
        if pred is not None:
            try:
                el.PredefinedType = pred
            except Exception:
                pass
        run("spatial.assign_container", model, relating_structure=storey, products=[el])
        elementos.append(el)
        return el

    # --- nudos de la malla principal (escalera) ----------------------------
    N = {
        "n1": [0, 0, 0],   "n2": [8, 0, 0],   "n3": [16, 0, 0],  "n4": [24, 0, 0],
        "n5": [0, -8, 0],  "n6": [8, -8, 0],  "n7": [16, -8, 0], "n8": [24, -8, 0],
    }
    # rociadores (drops): nudo de cuelgue -> coord del rociador
    ROC = {
        "ROC-1": ("n2", [8, 3, 0]),   "ROC-2": ("n3", [16, 3, 0]),  "ROC-3": ("n4", [24, 3, 0]),
        "ROC-4": ("n6", [8, -11, 0]), "ROC-5": ("n7", [16, -11, 0]), "ROC-6": ("n8", [24, -11, 0]),
    }

    def tubo(nombre, a, b, dn):
        p0, p1 = N[a], N[b]
        s = crear("IfcFlowSegment", nombre, p0, "PIPESEGMENT")
        pa = _puerto(model, nombre + "-0", p0, "SINK")
        pb = _puerto(model, nombre + "-1", p1, "SOURCE")
        _nest(model, s, [pa, pb])
        reg_puerto(pa, p0); reg_puerto(pb, p1)
        ps = run("pset.add_pset", model, product=s, name="Pset_PipeSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps,
            properties={"NominalDiameter": float(dn), "Roughness": 0.045})   # mm
        mat = run("material.add_material", model, name="Acero galvanizado")
        run("material.assign_material", model, products=[s], material=mat)
        return s

    def tubo_drop(nombre, a, xyz, dn):
        p0, p1 = N[a], xyz
        s = crear("IfcFlowSegment", nombre, p0, "PIPESEGMENT")
        pa = _puerto(model, nombre + "-0", p0, "SINK")
        pb = _puerto(model, nombre + "-1", p1, "SOURCE")
        _nest(model, s, [pa, pb])
        reg_puerto(pa, p0); reg_puerto(pb, p1)
        ps = run("pset.add_pset", model, product=s, name="Pset_PipeSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps,
            properties={"NominalDiameter": float(dn), "Roughness": 0.045})
        mat = run("material.add_material", model, name="Acero galvanizado")
        run("material.assign_material", model, products=[s], material=mat)
        return s

    # colectores (DN100), montantes (DN80)
    tubo("M-T1", "n1", "n2", 100); tubo("M-T2", "n2", "n3", 100); tubo("M-T3", "n3", "n4", 100)
    tubo("M-B1", "n5", "n6", 100); tubo("M-B2", "n6", "n7", 100); tubo("M-B3", "n7", "n8", 100)
    tubo("R-1", "n1", "n5", 80); tubo("R-2", "n2", "n6", 80)
    tubo("R-3", "n3", "n7", 80); tubo("R-4", "n4", "n8", 80)

    # --- grupo de presion (fuente) en n1 -----------------------------------
    grupo = crear("IfcFlowMovingDevice", "Grupo de presion PCI", N["n1"], "PUMP")
    g_out = _puerto(model, "Grupo-out", N["n1"], "SOURCE")
    _nest(model, grupo, [g_out]); reg_puerto(g_out, N["n1"])
    psg = run("pset.add_pset", model, product=grupo, name="Pset_Estructurando_Red")
    run("pset.edit_pset", model, pset=psg,
        properties={"Pressure": 300.0, "FlowRate": 12.0})   # kPa, l/s [confirmar AN]

    # --- rociadores (drops + terminal) -------------------------------------
    for nombre, (nudo, xyz) in ROC.items():
        tubo_drop("D-" + nombre, nudo, xyz, 32)              # ramal DN32
        t = crear("IfcFlowTerminal", nombre, xyz, "USERDEFINED")
        p = _puerto(model, nombre + "-in", xyz, "SINK")
        _nest(model, t, [p]); reg_puerto(p, xyz)
        # sin Pset de caudal/presion: el solver aplica la demanda UNE-EN 12845 (OH1)

    # --- conectividad: estrella de puertos coincidentes por nudo -----------
    for k, plist in puertos_por_nudo.items():
        base = plist[0]
        for po in plist[1:]:
            _connect(model, base, po)

    # --- sistema FIREPROTECTION --------------------------------------------
    sistema = run("root.create_entity", model, ifc_class="IfcDistributionSystem",
                  name="Red rociadores PCI")
    try:
        sistema.PredefinedType = "FIREPROTECTION"
    except Exception:
        pass
    # INC-12: la clase de riesgo (UNE-EN 12845) como DATO DE PROYECTO en el IFC,
    # para que el parser la lea y el caso sea reproducible sin inyeccion del agente.
    psis = run("pset.add_pset", model, product=sistema, name="Pset_Estructurando_SistemaPCI")
    run("pset.edit_pset", model, pset=psis, properties={"ClaseRiesgo": "OH1"})
    model.create_entity("IfcRelAssignsToGroup", GlobalId=ifcopenshell.guid.new(),
                        RelatedObjects=elementos, RelatingGroup=sistema)

    model.write(out)
    print("IFC MEP rociadores (malla) escrito en %s (esquema %s, %d elementos)"
          % (out, model.schema, len(elementos)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "red_rociadores_prueba.ifc")
