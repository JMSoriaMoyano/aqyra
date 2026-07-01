"""Plantilla de creacion de un IFC minimo valido con IfcOpenShell.
Uso: python crear-ifc.py salida.ifc"""
import sys
import ifcopenshell
from ifcopenshell.api import run

def main(out):
    model = ifcopenshell.file(schema="IFC4")
    project = run("root.create_entity", model, ifc_class="IfcProject", name="Proyecto")
    run("unit.assign_unit", model)  # unidades SI por defecto
    ctx = run("context.add_context", model, context_type="Model")
    site = run("root.create_entity", model, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", model, ifc_class="IfcBuilding", name="Edificio")
    storey = run("root.create_entity", model, ifc_class="IfcBuildingStorey", name="Planta 00")
    run("aggregate.assign_object", model, relating_object=project, products=[site])
    run("aggregate.assign_object", model, relating_object=site, products=[building])
    run("aggregate.assign_object", model, relating_object=building, products=[storey])
    # Ejemplo de elemento + Pset
    wall = run("root.create_entity", model, ifc_class="IfcWall", name="Muro-001")
    run("spatial.assign_container", model, relating_structure=storey, products=[wall])
    pset = run("pset.add_pset", model, product=wall, name="Pset_WallCommon")
    run("pset.edit_pset", model, pset=pset, properties={"IsExternal": True, "LoadBearing": False})
    model.write(out)
    print(f"IFC escrito en {out} (esquema {model.schema})")

if __name__ == "__main__":
    main(sys.argv[1])
