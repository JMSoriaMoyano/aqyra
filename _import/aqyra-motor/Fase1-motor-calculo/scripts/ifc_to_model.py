"""
Parser IFC (dominio de analisis estructural) -> MODELO NEUTRO (JSON).

Lee IfcStructuralPointConnection (nodos + apoyos), IfcStructuralCurveMember
(barras + seccion + material) e IfcStructuralLinearAction (cargas), apoyandose
en los Psets propios 'Pset_Estructurando_*' para una relectura robusta.

Salida: un dict serializable a JSON con la estructura:
{
  "unidades": {...},
  "materiales": { "S275JR": {E,G,nu,rho,fy} },
  "secciones":  { "IPE 330": {A,Iy,Iz,J,Wply,Wely,h} },
  "nodos":      { "N1": {x,y,z, apoyo:[DX,DY,DZ,RX,RY,RZ]} },
  "barras":     { "B1": {ni,nj, seccion, material, tipo} },
  "cargas":     [ {caso, barra, direccion, qz} ],
}
Uso:  python3 ifc_to_model.py <archivo.ifc> <salida.json>
"""
import sys
import json
import ifcopenshell


def _psets(element):
    """Devuelve {pset_name: {prop: value}} de un elemento via IfcRelDefinesByProperties."""
    out = {}
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet"):
                props = {}
                for p in pdef.HasProperties:
                    if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                        props[p.Name] = p.NominalValue.wrappedValue
                out[pdef.Name] = props
    return out


def _material_props(ifc):
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        m = mp.Material
        d = {}
        for p in mp.Properties:
            if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                d[p.Name] = p.NominalValue.wrappedValue
        mats[m.Name] = {
            "E": d.get("YoungModulus"),
            "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"),
            "rho": d.get("MassDensity"),
            "fy": d.get("YieldStress"),
        }
    return mats


def _node_coords(conn):
    """Extrae (x,y,z) del IfcVertexPoint del IfcStructuralPointConnection."""
    rep = conn.Representation
    for r in rep.Representations:
        for item in r.Items:
            if item.is_a("IfcVertexPoint"):
                c = item.VertexGeometry.Coordinates
                return [float(c[0]), float(c[1]), float(c[2])]
    return None


def _support(conn):
    bc = conn.AppliedCondition
    if bc is None or not bc.is_a("IfcBoundaryNodeCondition"):
        return [False] * 6
    def val(attr):
        a = getattr(bc, attr, None)
        if a is None:
            return False
        # IfcBoolean True => coaccion rigida
        try:
            return bool(a.wrappedValue)
        except AttributeError:
            return bool(a)
    return [val("TranslationalStiffnessX"), val("TranslationalStiffnessY"),
            val("TranslationalStiffnessZ"), val("RotationalStiffnessX"),
            val("RotationalStiffnessY"), val("RotationalStiffnessZ")]


def _member_material(mb):
    for rel in getattr(mb, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            m = rel.RelatingMaterial
            if m.is_a("IfcMaterial"):
                return m.Name
    return None


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    model = {
        "unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
        "materiales": _material_props(ifc),
        "secciones": {},
        "nodos": {},
        "barras": {},
        "cargas": [],
    }

    # Nodos: mapa de VertexPoint -> nombre de nodo (para resolver topologia de barras)
    vertex_to_node = {}
    for conn in ifc.by_type("IfcStructuralPointConnection"):
        name = conn.Name
        model["nodos"][name] = {
            "x": None, "y": None, "z": None, "apoyo": _support(conn),
        }
        coords = _node_coords(conn)
        if coords:
            model["nodos"][name]["x"], model["nodos"][name]["y"], model["nodos"][name]["z"] = coords
        for r in conn.Representation.Representations:
            for item in r.Items:
                if item.is_a("IfcVertexPoint"):
                    vertex_to_node[item.id()] = name

    # Barras
    for mb in ifc.by_type("IfcStructuralCurveMember"):
        ps = _psets(mb)
        analisis = ps.get("Pset_Estructurando_Analisis", {})
        sec_name = analisis.get("Seccion")
        ni = analisis.get("NodoInicial")
        nj = analisis.get("NodoFinal")
        # respaldo: resolver nodos por topologia del IfcEdge
        if (ni is None or nj is None) and mb.Representation:
            for r in mb.Representation.Representations:
                for item in r.Items:
                    if item.is_a("IfcEdge"):
                        ni = ni or vertex_to_node.get(item.EdgeStart.id())
                        nj = nj or vertex_to_node.get(item.EdgeEnd.id())
        model["barras"][mb.Name] = {
            "ni": ni, "nj": nj, "seccion": sec_name,
            "material": _member_material(mb), "tipo": analisis.get("Tipo"),
        }
        if sec_name and sec_name not in model["secciones"]:
            model["secciones"][sec_name] = {
                k: analisis.get(k) for k in
                ("A", "Iy", "Iz", "J", "Wply", "Wely", "h", "Avz", "clase")
            }

    # Cargas
    for act in ifc.by_type("IfcStructuralLinearAction"):
        ps = _psets(act)
        carga = ps.get("Pset_Estructurando_Carga", {})
        if carga:
            model["cargas"].append({
                "caso": carga.get("Caso"),
                "barra": carga.get("Barra"),
                "direccion": carga.get("Direccion", "GZ"),
                "qz": carga.get("qz_N_m"),
            })

    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/portico_demo.ifc"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/modelo_neutro.json"
    model = parse(ifc_path)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2, ensure_ascii=False)
    print("Modelo neutro escrito en:", out_path)
    print(json.dumps(model, indent=2, ensure_ascii=False))
