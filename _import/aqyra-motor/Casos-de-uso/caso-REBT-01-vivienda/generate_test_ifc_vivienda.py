"""
GENERADOR de IFC MEP de prueba -- INSTALACION ELECTRICA DE VIVIENDA (REBT, caso
REBT-01). Banco de pruebas del vertical electrico (PT 4.5, Ola 4). Es un FIXTURE
del caso (no se empaqueta en ningun plugin): construye un IFC y luego lo lee el
parser MEP de iso19650-openbim SIN modificarlo.

Red radial de un cuadro de vivienda (electrificacion elevada, ITC-BT-25):

    CUADRO (fuente)  --C1-->  Iluminacion
                     --C2-->  Tomas uso general
                     --C3-->  Cocina/horno
                     --C4-->  Lavadora/lavavajillas/termo
                     --C5-->  Tomas banos y cocina
                     --C8-->  Calefaccion
                     --C9-->  Aire acondicionado
                     --C12--> Circuito adicional

  - IfcDistributionSystem  PredefinedType=ELECTRICAL
  - IfcFlowController       cuadro general (fuente / ancla; el parser lo trata como fuente)
  - IfcFlowSegment x8       conductores (IfcFlowSegment para que el parser intacto los lea)
  - IfcFlowTerminal x8      un terminal por circuito (Name "C1..C12-..." para clasificar)
  - IfcDistributionPort + IfcRelConnectsPorts : conectividad puerto a puerto

Uso:  PYTHONPATH=/tmp/pylibs python3 generate_test_ifc_vivienda.py salida.ifc
Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
import math
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


# circuitos: (id, coordenada del terminal)  -- la longitud es la distancia al cuadro
_CIRCUITOS = [
    ("C1-Iluminacion",        (15.0, 0.0, 0.0)),
    ("C2-Tomas-generales",    (0.0, 15.0, 0.0)),
    ("C3-Cocina-horno",       (-15.0, 0.0, 0.0)),
    ("C4-Lavadora-termo",     (0.0, -15.0, 0.0)),
    ("C5-Tomas-bano-cocina",  (12.0, 12.0, 0.0)),
    ("C8-Calefaccion",        (-12.0, 12.0, 0.0)),
    ("C9-Aire-acondicionado", (-12.0, -12.0, 0.0)),
    ("C12-Adicional",         (12.0, -12.0, 0.0)),
]


def main(out):
    model = ifcopenshell.file(schema="IFC4")
    run("root.create_entity", model, ifc_class="IfcProject", name="Vivienda REBT prueba")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")  # metro (sin prefijo)
    run("unit.assign_unit", model, units=[_u])
    run("context.add_context", model, context_type="Model")
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Edificio")
    storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Vivienda")
    prj = model.by_type("IfcProject")[0]
    run("aggregate.assign_object", model, relating_object=prj, products=[site])
    run("aggregate.assign_object", model, relating_object=site, products=[building])
    run("aggregate.assign_object", model, relating_object=building, products=[storey])

    elementos = []

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

    # --- cuadro general (fuente) en el origen --------------------------------
    cuadro = crear("IfcFlowController", "Cuadro general vivienda", [0, 0, 0], "USERDEFINED")
    c_out = _puerto(model, "Cuadro-out", [0, 0, 0], "SOURCE")
    _nest(model, cuadro, [c_out])

    mat = run("material.add_material", model, name="Cobre")

    def circuito(nombre, xyz):
        # conductor (IfcFlowSegment)
        s = crear("IfcFlowSegment", nombre, [0, 0, 0], "USERDEFINED")
        pa = _puerto(model, nombre + "-0", [0, 0, 0], "SINK")
        pb = _puerto(model, nombre + "-1", xyz, "SOURCE")
        _nest(model, s, [pa, pb])
        ps = run("pset.add_pset", model, product=s, name="Pset_CableSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps, properties={"Material": "Cu"})
        run("material.assign_material", model, products=[s], material=mat)
        # terminal (IfcFlowTerminal) en el extremo
        t = crear("IfcFlowTerminal", nombre, xyz, "USERDEFINED")
        tp = _puerto(model, nombre + "-in", xyz, "SINK")
        _nest(model, t, [tp])
        _connect(model, c_out, pa)
        _connect(model, pb, tp)

    for nombre, xyz in _CIRCUITOS:
        circuito(nombre, xyz)

    sistema = run("root.create_entity", model, ifc_class="IfcDistributionSystem",
                  name="Instalacion electrica vivienda")
    try:
        sistema.PredefinedType = "ELECTRICAL"
    except Exception:
        pass
    model.create_entity("IfcRelAssignsToGroup", GlobalId=ifcopenshell.guid.new(),
                        RelatedObjects=elementos, RelatingGroup=sistema)

    model.write(out)
    print("IFC vivienda REBT escrito en %s (esquema %s, %d elementos, %d circuitos)"
          % (out, model.schema, len(elementos), len(_CIRCUITOS)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "vivienda_rebt.ifc")
