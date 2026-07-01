#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""generar_galeria.py -> IFC con UNA instancia de cada subtipo concreto de IfcElement
(IFC4X3), cada una con geometría + atributos + Psets estándar + URI bsDD.
Distribuye los elementos en una rejilla agrupada por grupo (calle por grupo).
Uso: python3 generar_galeria.py galeria.ifc"""
import sys, math
import ifcopenshell
from ifcopenshell.api import run
import catalogo_ifc as C

def main():
    out = sys.argv[1] if len(sys.argv) > 1 else "galeria.ifc"
    m = ifcopenshell.file(schema=C.SCHEMA)
    project = run("root.create_entity", m, ifc_class="IfcProject", name="Galería IfcElement (IFC4X3)")
    run("unit.assign_unit", m, length={"is_metric": True, "raw": "METERS"})
    model_ctx = run("context.add_context", m, context_type="Model")
    body_ctx = run("context.add_context", m, context_type="Model", context_identifier="Body",
                   target_view="MODEL_VIEW", parent=model_ctx)
    site = run("root.create_entity", m, ifc_class="IfcSite", name="Emplazamiento")
    building = run("root.create_entity", m, ifc_class="IfcBuilding", name="Catálogo")
    run("aggregate.assign_object", m, relating_object=project, products=[site])
    run("aggregate.assign_object", m, relating_object=site, products=[building])
    storey = run("root.create_entity", m, ifc_class="IfcBuildingStorey", name="Planta Catálogo")
    storey.Elevation = 0.0
    run("aggregate.assign_object", m, relating_object=building, products=[storey])

    cat = C.construir_catalogo()
    # agrupar por grupo, una "calle" (fila) por grupo
    por_grupo = {}
    for clase, info in cat.items():
        por_grupo.setdefault(info["grupo"], []).append(clase)
    cache = {}
    SX, SY = 4.0, 6.0   # separación en X (entre elementos) y entre calles (Y)
    n_el = 0; n_props = 0; fallos = []
    for gi, grupo in enumerate(sorted(por_grupo)):
        clases = sorted(por_grupo[grupo])
        y = gi * SY
        for ci, clase in enumerate(clases):
            x = ci * SX
            try:
                el, np_ = C.crear_elemento(m, body_ctx, storey, clase, clase,
                                           origin=(x, y, 0.0), classif_cache=cache)
                n_el += 1; n_props += np_
            except Exception as e:
                fallos.append((clase, str(e)))
    m.write(out)
    print(f"OK  galería -> {out}  esquema={m.schema}")
    print(f"    elementos creados={n_el}  propiedades estándar={n_props}  fallos={len(fallos)}")
    if fallos:
        for c, e in fallos[:12]: print("    FALLO", c, e)

if __name__ == "__main__":
    main()
