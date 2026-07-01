"""
GENERADOR de IFC MEP de prueba -- INSTALACION ELECTRICA TERCIARIA/INDUSTRIAL
(REBT, caso REBT-02). Fixture del caso (no se empaqueta): lo lee el parser MEP de
iso19650-openbim SIN modificarlo. Red radial con linea general (trifasica) a un
subcuadro y derivaciones a luminarias (mono), una toma (mono) y un motor (tri):

    CUADRO (fuente) --LGA--> SUBCUADRO --L1--> LUM-1
                                       --L2--> LUM-2
                                       --L3--> TOMA-1
                                       --L4--> MOTOR-1 (trifasico)

  - IfcDistributionSystem  PredefinedType=ELECTRICAL
  - IfcFlowController       cuadro general (fuente / ancla)
  - IfcFlowFitting         subcuadro (nudo de union; no crea tramo)
  - IfcFlowSegment x5      conductores
  - IfcFlowTerminal x4     LUM-1, LUM-2, TOMA-1, MOTOR-1 (Name clasifica el receptor)

Uso:  PYTHONPATH=/tmp/pylibs python3 generate_test_ifc_terciario.py salida.ifc
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
    run("root.create_entity", model, ifc_class="IfcProject", name="Terciario REBT prueba")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")
    run("unit.assign_unit", model, units=[_u])
    run("context.add_context", model, context_type="Model")
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Edificio")
    storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Local")
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

    mat = run("material.add_material", model, name="Cobre")

    # --- cuadro general (fuente) y subcuadro (union) -------------------------
    P_CUADRO = [0, 0, 0]
    P_SUB = [20, 0, 0]
    cuadro = crear("IfcFlowController", "Cuadro general", P_CUADRO, "USERDEFINED")
    c_out = _puerto(model, "Cuadro-out", P_CUADRO, "SOURCE")
    _nest(model, cuadro, [c_out])

    sub = crear("IfcFlowFitting", "Subcuadro", P_SUB, "USERDEFINED")
    s_in = _puerto(model, "Sub-in", P_SUB, "SINK")
    s_o1 = _puerto(model, "Sub-o1", P_SUB, "SOURCE")
    s_o2 = _puerto(model, "Sub-o2", P_SUB, "SOURCE")
    s_o3 = _puerto(model, "Sub-o3", P_SUB, "SOURCE")
    s_o4 = _puerto(model, "Sub-o4", P_SUB, "SOURCE")
    _nest(model, sub, [s_in, s_o1, s_o2, s_o3, s_o4])

    def conductor(nombre, p0, p1):
        s = crear("IfcFlowSegment", nombre, p0, "USERDEFINED")
        pa = _puerto(model, nombre + "-0", p0, "SINK")
        pb = _puerto(model, nombre + "-1", p1, "SOURCE")
        _nest(model, s, [pa, pb])
        ps = run("pset.add_pset", model, product=s, name="Pset_CableSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps, properties={"Material": "Cu"})
        run("material.assign_material", model, products=[s], material=mat)
        return s, pa, pb

    def terminal(nombre, xyz):
        t = crear("IfcFlowTerminal", nombre, xyz, "USERDEFINED")
        tp = _puerto(model, nombre + "-in", xyz, "SINK")
        _nest(model, t, [tp])
        return t, tp

    # --- linea general (cuadro -> subcuadro) --------------------------------
    lga, lga_a, lga_b = conductor("LGA", P_CUADRO, P_SUB)
    _connect(model, c_out, lga_a)
    _connect(model, lga_b, s_in)

    # --- derivaciones --------------------------------------------------------
    # derivaciones en direcciones distintas (evitar tramos colineales solapados,
    # que el grafo del nucleo trocearia por interseccion T/X creando lazos espurios).
    derivs = [
        ("LUM-1",   [32, 10, 0], s_o1),
        ("LUM-2",   [32, -10, 0], s_o2),
        ("TOMA-1",  [30, 20, 0], s_o3),
        ("MOTOR-1", [35, -18, 0], s_o4),
    ]
    for nombre, xyz, puerto_sub in derivs:
        nseg = "L-" + nombre
        seg, pa, pb = conductor(nseg, P_SUB, xyz)
        term, tp = terminal(nombre, xyz)
        _connect(model, puerto_sub, pa)
        _connect(model, pb, tp)

    sistema = run("root.create_entity", model, ifc_class="IfcDistributionSystem",
                  name="Instalacion electrica terciaria")
    try:
        sistema.PredefinedType = "ELECTRICAL"
    except Exception:
        pass
    model.create_entity("IfcRelAssignsToGroup", GlobalId=ifcopenshell.guid.new(),
                        RelatedObjects=elementos, RelatingGroup=sistema)

    model.write(out)
    print("IFC terciario REBT escrito en %s (esquema %s, %d elementos)"
          % (out, model.schema, len(elementos)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "terciario_rebt.ifc")
