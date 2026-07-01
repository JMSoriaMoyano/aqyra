"""
GENERADOR de IFC MEP de ABASTECIMIENTO de prueba (banco de pruebas del parser/
validacion de red a presion). PT 6.3 (Ola 6). Analogo a generate_test_ifc_mep.py
(PCI) y generate_test_ifc_saneamiento.py, adaptado al dominio de ABASTECIMIENTO
(red de distribucion a presion).

Construye una red de distribucion con DEPOSITO (fuente por cota) y una MALLA (anillo)
para ejercitar el Hardy-Cross:

   DEP (deposito, lamina z=130) --T0(DN200)--> N0 (cabecera)
                         N0 --T1(DN150)--> N1 (ACO-1) --T2(DN150)--> N2 (HIDRANTE-1)
                         N0 --T4(DN150)--> N3 (ACO-2) --T3(DN150)--> N2
   (anillo N0-N1-N2-N3-N0 = 1 lazo)

  - IfcDistributionSystem  PredefinedType=WATERSUPPLY (o DOMESTICCOLDWATER en IFC4)
  - IfcTank                DEPOSITO -> fuente = ancla de presion por cota
                           (Pset_Estructurando_Red: WaterLevel)
  - IfcFlowTerminal        acometidas (Pset_Estructurando_Red: HabitantesEq) e
                           HIDRANTE (PredefinedType marcado; caudal de incendio)
  - IfcFlowSegment x5      tuberias (Pset_PipeSegmentTypeCommon: NominalDiameter,
                           Roughness) con material
  - IfcDistributionPort + IfcRelConnectsPorts : conectividad puerto a puerto

Las cotas (z) gobiernan la carga estatica: el deposito (lamina alta) genera la
presion aguas abajo por rho*g*dz (la fuente declara presion 0).

Uso:  python3 generate_test_ifc_abastecimiento.py salida.ifc
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


# coordenadas (x, y, z) -- la z gobierna la carga estatica del deposito
XYZ = {
    "DEP": (0.0, 0.0, 130.0),    # lamina de agua del deposito (fuente)
    "N0": (0.0, 0.0, 100.0),     # cabecera
    "N1": (120.0, 0.0, 98.0),    # ACO-1
    "N2": (120.0, 120.0, 96.0),  # HIDRANTE-1 (nudo mas desfavorable)
    "N3": (0.0, 120.0, 99.0),    # ACO-2
}


def main(out):
    model = ifcopenshell.file(schema="IFC4")
    run("root.create_entity", model, ifc_class="IfcProject", name="Red abastecimiento prueba")
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

    def crear(cls, nombre, nm, pred=None):
        el = run("root.create_entity", model, ifc_class=cls, name=nombre)
        el.ObjectPlacement = _placement(model, XYZ[nm])
        if pred is not None:
            try:
                el.PredefinedType = pred
            except Exception:
                pass
        run("spatial.assign_container", model, relating_structure=storey, products=[el])
        elementos.append(el)
        return el

    # --- deposito (fuente = ancla de presion por cota) ---------------------
    dep = crear("IfcTank", "DEPOSITO", "DEP")
    dep_p = _puerto(model, "DEP-out", XYZ["DEP"], "SOURCE")
    _nest(model, dep, [dep_p])
    psd = run("pset.add_pset", model, product=dep, name="Pset_Estructurando_Red")
    run("pset.edit_pset", model, pset=psd, properties={"WaterLevel": XYZ["DEP"][2]})

    # --- acometidas e hidrante (consumo / incendio) ------------------------
    def terminal(nombre, nm, pred="USERDEFINED", habeq=None):
        t = crear("IfcFlowTerminal", nombre, nm, pred)
        p = _puerto(model, nombre + "-in", XYZ[nm], "SINK")
        _nest(model, t, [p])
        if habeq is not None:
            ps = run("pset.add_pset", model, product=t, name="Pset_Estructurando_Red")
            run("pset.edit_pset", model, pset=ps, properties={"HabitantesEq": float(habeq)})
        return t, p

    a1, a1p = terminal("ACO-1", "N1", habeq=800)
    a2, a2p = terminal("ACO-2", "N3", habeq=600)
    hid, hidp = terminal("HIDRANTE-1", "N2", pred="FIREHYDRANT")

    # --- nudo de cabecera N0 (union) ---------------------------------------
    n0 = crear("IfcFlowFitting", "NUDO-N0", "N0")
    n0_a = _puerto(model, "N0-a", XYZ["N0"], "SINK")
    n0_b = _puerto(model, "N0-b", XYZ["N0"], "SOURCE")
    n0_c = _puerto(model, "N0-c", XYZ["N0"], "SOURCE")
    _nest(model, n0, [n0_a, n0_b, n0_c])

    # --- tuberias (IfcFlowSegment) -----------------------------------------
    def tuberia(nombre, a, b, dn, rug=0.1, material="fundicion ductil"):
        s = crear("IfcFlowSegment", nombre, a, "PIPESEGMENT")
        # placement en el extremo a; puertos en a y b
        pa = _puerto(model, nombre + "-0", XYZ[a], "SINK")
        pb = _puerto(model, nombre + "-1", XYZ[b], "SOURCE")
        _nest(model, s, [pa, pb])
        ps = run("pset.add_pset", model, product=s, name="Pset_PipeSegmentTypeCommon")
        run("pset.edit_pset", model, pset=ps,
            properties={"NominalDiameter": float(dn), "Roughness": float(rug)})
        mat = run("material.add_material", model, name=material)
        run("material.assign_material", model, products=[s], material=mat)
        return s, pa, pb

    t0, t0a, t0b = tuberia("COND-0", "DEP", "N0", 200)   # aduccion (deposito->cabecera)
    t1, t1a, t1b = tuberia("COND-1", "N0", "N1", 125)
    t2, t2a, t2b = tuberia("COND-2", "N1", "N2", 125)
    t3, t3a, t3b = tuberia("COND-3", "N2", "N3", 125)
    t4, t4a, t4b = tuberia("COND-4", "N3", "N0", 125)    # cierra el anillo (1 lazo)

    # --- conectividad puerto a puerto --------------------------------------
    _connect(model, dep_p, t0a)    # DEP -> COND-0
    _connect(model, t0b, n0_a)     # COND-0 -> N0
    _connect(model, n0_b, t1a)     # N0 -> COND-1
    _connect(model, t1b, a1p)      # COND-1 -> ACO-1 (N1)
    _connect(model, t1b, t2a)      # COND-1 -> COND-2 (N1)
    _connect(model, t2b, hidp)     # COND-2 -> HIDRANTE (N2)
    _connect(model, t2b, t3a)      # COND-2 -> COND-3 (N2)
    _connect(model, t3b, a2p)      # COND-3 -> ACO-2 (N3)
    _connect(model, t3b, t4a)      # COND-3 -> COND-4 (N3)
    _connect(model, t4b, n0_c)     # COND-4 -> N0 (cierra el anillo)

    # --- sistema WATERSUPPLY -----------------------------------------------
    sistema = run("root.create_entity", model, ifc_class="IfcDistributionSystem",
                  name="Red de abastecimiento")
    if not _set_pred(sistema, "WATERSUPPLY"):
        _set_pred(sistema, "DOMESTICCOLDWATER")   # respaldo valido en IFC4
    model.create_entity("IfcRelAssignsToGroup", GlobalId=ifcopenshell.guid.new(),
                        RelatedObjects=elementos, RelatingGroup=sistema)

    model.write(out)
    print("IFC MEP de abastecimiento escrito en %s (esquema %s, %d elementos, sistema %s)"
          % (out, model.schema, len(elementos),
             getattr(sistema, "PredefinedType", None)))


def _set_pred(el, pred):
    try:
        el.PredefinedType = pred
        return getattr(el, "PredefinedType", None) == pred
    except Exception:
        return False


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "red_abastecimiento_prueba.ifc")
