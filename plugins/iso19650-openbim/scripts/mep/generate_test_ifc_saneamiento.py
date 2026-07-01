"""
GENERADOR de IFC MEP de SANEAMIENTO de prueba (banco de pruebas del parser/validacion
de red en lamina libre). PT 6.2 (Ola 6). Analogo a generate_test_ifc_mep.py (PCI),
adaptado al dominio de SANEAMIENTO (colectores por gravedad).

Construye una red de colectores residuales en ARBOL que converge a un VERTIDO:

   ACO-1 (P1) --T1(DN315)--\\
                            P3 (pozo) --T3(DN400)--\\
   ACO-2 (P2) --T2(DN315)--/                        V (VERTIDO/outfall)
   ACO-3 (P4) ------------------T4(DN315)----------/

  - IfcDistributionSystem  PredefinedType=SEWAGE
  - IfcFlowTerminal        acometidas de sector (con Pset_Estructurando_Red:
                           CotaSolera, HabitantesEq) -> aporte residual (EN 752)
  - IfcDistributionChamberElement  pozo de registro P3 (con CotaSolera)
  - IfcFlowTerminal        VERTIDO (PredefinedType=OUTLET) -> ancla del arbol
  - IfcFlowSegment x4      colectores (Pset_PipeSegmentTypeCommon: NominalDiameter)
                           con material (-> n de Manning) y CotaSolera por nudo
  - IfcDistributionPort + IfcRelConnectsPorts : conectividad puerto a puerto

Las cotas de solera (invert) gobiernan el flujo por gravedad: pendientes ~1.0-1.2 %.

Uso:  python3 generate_test_ifc_saneamiento.py salida.ifc
Predimensionado/asistencia; a revisar y firmar por tecnico competente (ICCP).
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
    run("root.create_entity", model, ifc_class="IfcProject", name="Red saneamiento prueba")
    _u = run("unit.add_si_unit", model, unit_type="LENGTHUNIT")   # metro (sin prefijo)
    run("unit.assign_unit", model, units=[_u])
    run("context.add_context", model, context_type="Model")
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Urbanizacion")
    storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Rasante")
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

    # cotas de solera (invert) por nudo -- gobiernan el flujo por gravedad
    SOL = {"P1": 100.50, "P2": 100.50, "P3": 100.00, "P4": 100.20, "V": 99.50}
    XY = {"P1": (0, 0), "P2": (0, 100), "P3": (50, 50), "P4": (120, 0), "V": (100, 50)}

    def xyz(nm):
        return [float(XY[nm][0]), float(XY[nm][1]), SOL[nm]]

    # --- acometidas de sector (aporte residual) ----------------------------
    def acometida(nombre, nm, habeq):
        t = crear("IfcFlowTerminal", nombre, xyz(nm), "USERDEFINED")
        p = _puerto(model, nombre + "-out", xyz(nm), "SOURCE")
        _nest(model, t, [p])
        ps = run("pset.add_pset", model, product=t, name="Pset_Estructurando_Red")
        run("pset.edit_pset", model, pset=ps,
            properties={"CotaSolera": SOL[nm], "HabitantesEq": float(habeq)})
        return t, p

    a1, a1p = acometida("ACO-1", "P1", 2600)   # ~12.0 l/s punta
    a2, a2p = acometida("ACO-2", "P2", 2600)   # ~12.0 l/s punta
    a3, a3p = acometida("ACO-3", "P4", 1700)   # ~7.9 l/s punta

    # --- pozo de registro P3 (nudo de union) -------------------------------
    pozo = crear("IfcDistributionChamberElement", "POZO-P3", xyz("P3"))
    pz_a = _puerto(model, "P3-a", xyz("P3"), "SINK")
    pz_b = _puerto(model, "P3-b", xyz("P3"), "SINK")
    pz_c = _puerto(model, "P3-c", xyz("P3"), "SOURCE")
    _nest(model, pozo, [pz_a, pz_b, pz_c])
    ps = run("pset.add_pset", model, product=pozo, name="Pset_Estructurando_Red")
    run("pset.edit_pset", model, pset=ps, properties={"CotaSolera": SOL["P3"]})

    # --- vertido / outfall (ancla del arbol) -------------------------------
    vert = crear("IfcFlowTerminal", "VERTIDO", xyz("V"), "OUTLET")
    v_a = _puerto(model, "V-a", xyz("V"), "SINK")
    v_b = _puerto(model, "V-b", xyz("V"), "SINK")
    _nest(model, vert, [v_a, v_b])
    psv = run("pset.add_pset", model, product=vert, name="Pset_Estructurando_Red")
    run("pset.edit_pset", model, pset=psv, properties={"CotaSolera": SOL["V"]})

    # --- colectores (IfcFlowSegment) ---------------------------------------
    def colector(nombre, a, b, dn, material="hormigon"):
        s = crear("IfcFlowSegment", nombre, xyz(a), "PIPESEGMENT")
        pa = _puerto(model, nombre + "-0", xyz(a), "SINK")
        pb = _puerto(model, nombre + "-1", xyz(b), "SOURCE")
        _nest(model, s, [pa, pb])
        ps = run("pset.add_pset", model, product=s, name="Pset_PipeSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps, properties={"NominalDiameter": float(dn)})
        mat = run("material.add_material", model, name=material)
        run("material.assign_material", model, products=[s], material=mat)
        return s, pa, pb

    t1, t1a, t1b = colector("COL-1", "P1", "P3", 315)
    t2, t2a, t2b = colector("COL-2", "P2", "P3", 315)
    t3, t3a, t3b = colector("COL-3", "P3", "V", 400)
    t4, t4a, t4b = colector("COL-4", "P4", "V", 315)

    # --- conectividad puerto a puerto --------------------------------------
    _connect(model, a1p, t1a)      # ACO-1 -> COL-1
    _connect(model, t1b, pz_a)     # COL-1 -> pozo
    _connect(model, a2p, t2a)      # ACO-2 -> COL-2
    _connect(model, t2b, pz_b)     # COL-2 -> pozo
    _connect(model, pz_c, t3a)     # pozo  -> COL-3
    _connect(model, t3b, v_a)      # COL-3 -> VERTIDO
    _connect(model, a3p, t4a)      # ACO-3 -> COL-4
    _connect(model, t4b, v_b)      # COL-4 -> VERTIDO

    # --- sistema SEWAGE ----------------------------------------------------
    sistema = run("root.create_entity", model, ifc_class="IfcDistributionSystem",
                  name="Red de saneamiento residual")
    try:
        sistema.PredefinedType = "SEWAGE"
    except Exception:
        pass
    model.create_entity("IfcRelAssignsToGroup", GlobalId=ifcopenshell.guid.new(),
                        RelatedObjects=elementos, RelatingGroup=sistema)

    model.write(out)
    print("IFC MEP de saneamiento escrito en %s (esquema %s, %d elementos)"
          % (out, model.schema, len(elementos)))


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "red_saneamiento_prueba.ifc")
