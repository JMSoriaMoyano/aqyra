"""
Parser IFC 3D -> MODELO NEUTRO (JSON) con BARRAS y SUPERFICIES (losas/muros).

Lee:
  - IfcStructuralPointConnection -> nodos (coords + apoyos)
  - IfcStructuralCurveMember     -> barras (seccion, material, nodos)
  - IfcStructuralSurfaceMember   -> superficies (esquinas, espesor, malla, material, cargas)
  - IfcMaterialProperties        -> materiales (E,G,nu,rho,fy,fck,fctm)

Uso: python3 ifc_to_model_3d.py <archivo.ifc> <salida.json>
"""
import sys
import json
import ifcopenshell


def _psets(element):
    out = {}
    for rel in getattr(element, "IsDefinedBy", []) or []:
        if rel.is_a("IfcRelDefinesByProperties"):
            pdef = rel.RelatingPropertyDefinition
            if pdef.is_a("IfcPropertySet"):
                props = {p.Name: p.NominalValue.wrappedValue
                         for p in pdef.HasProperties
                         if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None}
                out[pdef.Name] = props
    return out


def _materials(ifc):
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        d = {p.Name: p.NominalValue.wrappedValue for p in mp.Properties
             if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None}
        mats[mp.Material.Name] = {
            "E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fy": d.get("YieldStress"), "fck": d.get("CompressiveStrength"),
            "fctm": d.get("TensileStrength"),
        }
    return mats


def _member_material(mb):
    for rel in getattr(mb, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial") and rel.RelatingMaterial.is_a("IfcMaterial"):
            return rel.RelatingMaterial.Name
    return None


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    model = {"unidades": {"longitud": "m", "fuerza": "N"},
             "materiales": _materials(ifc), "secciones": {},
             "nodos": {}, "barras": {}, "superficies": []}

    for conn in ifc.by_type("IfcStructuralPointConnection"):
        coords = None
        for r in conn.Representation.Representations:
            for item in r.Items:
                if item.is_a("IfcVertexPoint"):
                    c = item.VertexGeometry.Coordinates
                    coords = [float(c[0]), float(c[1]), float(c[2])]
        sup = [False] * 6
        bc = conn.AppliedCondition
        if bc and bc.is_a("IfcBoundaryNodeCondition"):
            def val(a):
                x = getattr(bc, a, None)
                if x is None:
                    return False
                return bool(getattr(x, "wrappedValue", x))
            sup = [val("TranslationalStiffnessX"), val("TranslationalStiffnessY"),
                   val("TranslationalStiffnessZ"), val("RotationalStiffnessX"),
                   val("RotationalStiffnessY"), val("RotationalStiffnessZ")]
        model["nodos"][conn.Name] = {"x": coords[0], "y": coords[1], "z": coords[2],
                                     "apoyo": sup}

    for mb in ifc.by_type("IfcStructuralCurveMember"):
        ps = _psets(mb).get("Pset_Estructurando_Analisis", {})
        sec_name = ps.get("Seccion")
        model["barras"][mb.Name] = {
            "ni": ps.get("NodoInicial"), "nj": ps.get("NodoFinal"),
            "seccion": sec_name, "material": _member_material(mb), "tipo": ps.get("Tipo")}
        if sec_name and sec_name not in model["secciones"]:
            model["secciones"][sec_name] = {k: ps.get(k) for k in
                ("A", "Iy", "Iz", "J", "Wply", "Wely", "h", "Avz", "clase")}

    for sm in ifc.by_type("IfcStructuralSurfaceMember"):
        ps = _psets(sm)
        geo = ps.get("Pset_Estructurando_Superficie", {})
        cargas = []
        for name, p in ps.items():
            if name.startswith("Pset_Estructurando_Carga_Superficie"):
                cargas.append({"caso": p.get("Caso"), "qz": p.get("qz_N_m2")})
        model["superficies"].append({
            "nombre": sm.Name,
            "esquinas": [s.strip() for s in geo.get("Esquinas", "").split(",") if s.strip()],
            "espesor": geo.get("Espesor", sm.Thickness),
            "malla": geo.get("TamanoMalla", 0.5),
            "material": _member_material(sm) or geo.get("Material"),
            "apoyo": geo.get("Apoyo", ""),
            "cargas": cargas,
        })

    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modulo_demo.ifc"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/modelo_neutro.json"
    model = parse(ifc_path)
    json.dump(model, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Modelo neutro 3D escrito en:", out_path)
    print(f"  nodos={len(model['nodos'])} barras={len(model['barras'])} "
          f"superficies={len(model['superficies'])}")
    for s in model["superficies"]:
        print(f"  losa '{s['nombre']}': esquinas={s['esquinas']} t={s['espesor']} "
              f"malla={s['malla']} mat={s['material']} cargas={[c['caso'] for c in s['cargas']]}")
