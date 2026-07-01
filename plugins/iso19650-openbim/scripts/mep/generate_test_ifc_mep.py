"""
GENERADOR de IFC MEP de prueba (banco de pruebas del parser/validacion de red).
PT 4.2 (Ola 4, hueco H2). Analogo a los generate_test_ifc* estructurales.

Construye una red PCI (proteccion contra incendios) sencilla pero COMPLETA para
validar el parser y la validacion de red de extremo a extremo:

    GRUPO (fuente)  --T1-->  TE  --T2-->  BIE-1
                                \\-T3-->  BIE-2
                       TE       --T4-->  BIE-3   (tres terminales)

  - IfcDistributionSystem  PredefinedType=FIREPROTECTION (IFC4; en IFC4X3: FIRESUPPRESSION)
  - IfcFlowMovingDevice    grupo de presion (fuente / ancla de la red)
  - IfcFlowSegment x4      tuberia (con Pset_PipeSegmentTypeCommon: NominalDiameter)
  - IfcFlowFitting         te (nudo de union; no crea tramo)
  - IfcFlowTerminal x3     BIE-25 (con caudal/presion minimos)
  - IfcDistributionPort + IfcRelConnectsPorts : conectividad puerto a puerto

Uso:  python3 generate_test_ifc_mep.py salida.ifc

Predimensionado/asistencia; a revisar y firmar por tecnico competente.
"""
import sys

import ifcopenshell
from ifcopenshell.api import run


def _placement(model, ctx_origin, xyz):
    """IfcLocalPlacement ABSOLUTO en xyz (PlacementRelTo=None)."""
    pt = model.create_entity("IfcCartesianPoint", Coordinates=[float(xyz[0]),
                             float(xyz[1]), float(xyz[2])])
    a2p = model.create_entity("IfcAxis2Placement3D", Location=pt)
    return model.create_entity("IfcLocalPlacement", RelativePlacement=a2p)


def _puerto(model, nombre, xyz, flujo):
    """IfcDistributionPort con placement absoluto y direccion de flujo."""
    po = run("root.create_entity", model, ifc_class="IfcDistributionPort",
             name=nombre)
    po.ObjectPlacement = _placement(model, None, xyz)
    try:
        po.FlowDirection = flujo  # SOURCE / SINK / SOURCEANDSINK
    except Exception:
        pass
    return po


def _nest(model, elemento, puertos):
    """IfcRelNests: anida los puertos en el elemento (patron IFC4)."""
    model.create_entity("IfcRelNests",
                        GlobalId=ifcopenshell.guid.new(),
                        RelatingObject=elemento, RelatedObjects=puertos)


def _connect(model, pa, pb):
    """IfcRelConnectsPorts: une dos puertos."""
    model.create_entity("IfcRelConnectsPorts",
                        GlobalId=ifcopenshell.guid.new(),
                        RelatingPort=pa, RelatedPort=pb)


def main(out):
    model = ifcopenshell.file(schema="IFC4")
    run("root.create_entity", model, ifc_class="IfcProject", name="Red PCI prueba")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")  # metro (sin prefijo)
    run("unit.assign_unit", model, units=[_u])  # unidades SI: longitud en METROS
    run("context.add_context", model, context_type="Model")
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Edificio")
    storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Planta 00")
    prj = model.by_type("IfcProject")[0]
    run("aggregate.assign_object", model, relating_object=prj, products=[site])
    run("aggregate.assign_object", model, relating_object=site, products=[building])
    run("aggregate.assign_object", model, relating_object=building, products=[storey])

    elementos = []

    def crear(cls, nombre, origen, pred=None):
        el = run("root.create_entity", model, ifc_class=cls, name=nombre)
        el.ObjectPlacement = _placement(model, None, origen)
        if pred is not None:
            try:
                el.PredefinedType = pred
            except Exception:
                pass
        run("spatial.assign_container", model, relating_structure=storey,
            products=[el])
        elementos.append(el)
        return el

    # --- fuente: grupo de presion ------------------------------------------
    grupo = crear("IfcFlowMovingDevice", "Grupo de presion PCI", [0, 0, 0], "PUMP")
    g_out = _puerto(model, "Grupo-out", [0, 0, 0], "SOURCE")
    _nest(model, grupo, [g_out])
    pset_g = run("pset.add_pset", model, product=grupo, name="Pset_Estructurando_Red")
    run("pset.edit_pset", model, pset=pset_g,
        properties={"Pressure": 600.0, "FlowRate": 25.0})  # kPa, l/s [confirmar AN]

    # --- te (nudo de union) en (10,0,0) ------------------------------------
    te = crear("IfcFlowFitting", "Te-01", [10, 0, 0], "TEE")
    te_a = _puerto(model, "Te-a", [10, 0, 0], "SINK")
    te_b = _puerto(model, "Te-b", [10, 0, 0], "SOURCE")
    te_c = _puerto(model, "Te-c", [10, 0, 0], "SOURCE")
    _nest(model, te, [te_a, te_b, te_c])

    # --- terminales BIE -----------------------------------------------------
    def bie(nombre, xyz):
        t = crear("IfcFlowTerminal", nombre, xyz, "USERDEFINED")
        p = _puerto(model, nombre + "-in", xyz, "SINK")
        _nest(model, t, [p])
        ps = run("pset.add_pset", model, product=t,
                 name="Pset_FireSuppressionTerminalTypeCommon")
        run("pset.edit_pset", model, pset=ps,
            properties={"FlowRate": 3.3, "PressureDrop": 350.0})  # l/s, kPa BIE-25 [confirmar AN]
        return t, p

    bie1, b1_in = bie("BIE-1", [10, 5, 0])
    bie2, b2_in = bie("BIE-2", [20, 0, 0])
    bie3, b3_in = bie("BIE-3", [10, -5, 0])

    # --- tuberias (IfcFlowSegment) -----------------------------------------
    def tubo(nombre, p0, p1, dn):
        s = crear("IfcFlowSegment", nombre, p0, "PIPESEGMENT")
        pa = _puerto(model, nombre + "-0", p0, "SINK")
        pb = _puerto(model, nombre + "-1", p1, "SOURCE")
        _nest(model, s, [pa, pb])
        ps = run("pset.add_pset", model, product=s,
                 name="Pset_PipeSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps,
            properties={"NominalDiameter": float(dn), "Roughness": 0.045})  # mm
        mat = run("material.add_material", model, name="Acero galvanizado")
        run("material.assign_material", model, products=[s], material=mat)
        return s, pa, pb

    t1, t1a, t1b = tubo("T1", [0, 0, 0], [10, 0, 0], 100)
    t2, t2a, t2b = tubo("T2", [10, 0, 0], [10, 5, 0], 65)
    t3, t3a, t3b = tubo("T3", [10, 0, 0], [20, 0, 0], 65)
    t4, t4a, t4b = tubo("T4", [10, 0, 0], [10, -5, 0], 65)

    # --- conectividad puerto a puerto (IfcRelConnectsPorts) -----------------
    _connect(model, g_out, t1a)          # grupo -> T1
    _connect(model, t1b, te_a)           # T1 -> te
    _connect(model, te_b, t2a)           # te -> T2 ; te -> T3 ; te -> T4
    _connect(model, te_c, t3a)
    _connect(model, te_c, t4a)           # nota: 3a salida del mismo nudo te
    _connect(model, t2b, b1_in)          # T2 -> BIE-1
    _connect(model, t3b, b2_in)          # T3 -> BIE-2
    _connect(model, t4b, b3_in)          # T4 -> BIE-3

    # --- sistema FIRESUPPRESSION (agrupa todos los elementos) ---------------
    sistema = run("root.create_entity", model, ifc_class="IfcDistributionSystem",
                  name="Red BIE PCI")
    # IFC4: FIREPROTECTION (en IFC4X3 el termino es FIRESUPPRESSION). El parser
    # es agnostico al esquema: emite el string tal cual venga del modelo.
    try:
        sistema.PredefinedType = "FIREPROTECTION"
    except Exception:
        pass
    model.create_entity("IfcRelAssignsToGroup",
                        GlobalId=ifcopenshell.guid.new(),
                        RelatedObjects=elementos, RelatingGroup=sistema)

    model.write(out)
    print("IFC MEP de prueba escrito en %s (esquema %s, %d elementos)"
          % (out, model.schema, len(elementos)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "red_pci_prueba.ifc")
