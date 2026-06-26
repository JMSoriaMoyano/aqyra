"""
Parser IFC 3D -> MODELO NEUTRO (JSON) con BARRAS y SUPERFICIES (losas/muros).

Soporta DOS dialectos de IFC, dando PRIORIDAD a las entidades estandar
(IFC ortodoxo del dominio de analisis estructural) y cayendo a los Psets
propios 'Pset_Estructurando_*' como respaldo. Ampliado en v0.4.0 (caso 2), de
forma analoga a 'barras' v0.3.1.

  - IfcStructuralPointConnection -> nodos (coords + apoyos)
  - IfcStructuralCurveMember     -> barras (seccion/material ORTODOXO desde
        IfcMaterialProfileSet -> IfcIShapeProfileDef con DB de perfiles;
        respaldo Pset_Estructurando_Analisis)
  - IfcStructuralSurfaceMember   -> superficies (esquinas desde IfcFaceSurface/
        IfcPolyLoop; espesor de .Thickness; material de IfcRelAssociatesMaterial;
        cargas de IfcStructuralSurfaceAction + IfcStructuralLoadPlanarForce con
        caso desde IfcStructuralLoadGroup; respaldo Psets)
  - IfcMaterialProperties        -> materiales (E,G,nu,rho,fy,fck,fctm)

Uso: python3 ifc_to_model_3d.py <archivo.ifc> <salida.json>
"""
import sys
import os
import json
import ifcopenshell

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "barras"))
sys.path.insert(0, os.path.join(HERE, "..", "nucleo"))
sys.path.insert(0, HERE)
try:
    import perfiles_db
except Exception:
    perfiles_db = None
import ifc_utils  # nucleo transversal (PT 4.1): _psets centralizado


# _psets -> nucleo (ifc_utils.psets); adaptador fino
_psets = ifc_utils.psets


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


def _associated_material(mb):
    for rel in getattr(mb, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            return rel.RelatingMaterial
    return None


def _resolve_material_name(relmat):
    if relmat is None:
        return None
    if relmat.is_a("IfcMaterial"):
        return relmat.Name
    if relmat.is_a("IfcMaterialProfileSet"):
        for prof in relmat.MaterialProfiles or []:
            if prof.Material is not None:
                return prof.Material.Name
    if relmat.is_a("IfcMaterialProfile"):
        return relmat.Material.Name if relmat.Material else None
    return None


def _resolve_section(relmat):
    if relmat is None or perfiles_db is None:
        return None, None
    profile = None
    if relmat.is_a("IfcMaterialProfileSet"):
        profs = relmat.MaterialProfiles or []
        if profs:
            profile = profs[0].Profile
    elif relmat.is_a("IfcMaterialProfile"):
        profile = relmat.Profile
    if profile is None:
        return None, None
    return perfiles_db.props_from_profile_def(profile)


def _surface_corners(sm):
    rep = getattr(sm, "Representation", None)
    if rep is None:
        return []
    for r in rep.Representations:
        for item in r.Items:
            bounds = getattr(item, "Bounds", None)
            if bounds:
                for bound in bounds:
                    loop = bound.Bound
                    if loop.is_a("IfcPolyLoop"):
                        return [[float(p.Coordinates[0]), float(p.Coordinates[1]),
                                 float(p.Coordinates[2])] for p in loop.Polygon]
    return []


def _action_surface_map(ifc):
    out = {}
    for rel in ifc.by_type("IfcRelConnectsStructuralActivity"):
        act = rel.RelatedStructuralActivity
        el = rel.RelatingElement
        if act is not None and el is not None:
            out[act.id()] = el.Name
    return out


def _action_case_map(ifc):
    out = {}
    for rel in ifc.by_type("IfcRelAssignsToGroup"):
        grp = rel.RelatingGroup
        if grp is None or not grp.is_a("IfcStructuralLoadGroup"):
            continue
        for obj in rel.RelatedObjects or []:
            out[obj.id()] = grp.Name
    return out


def _planar_force_qz(load):
    if load is not None and load.is_a("IfcStructuralLoadPlanarForce"):
        fz = getattr(load, "PlanarForceZ", None)
        return float(fz) if fz is not None else None
    return None


def _parse_surface_loads_orthodox(ifc):
    surf_of = _action_surface_map(ifc)
    case_of = _action_case_map(ifc)
    out = {}
    for act in ifc.by_type("IfcStructuralSurfaceAction"):
        qz = _planar_force_qz(act.AppliedLoad)
        if qz is None:
            continue
        sname = surf_of.get(act.id())
        out.setdefault(sname, []).append({"caso": case_of.get(act.id()), "qz": qz})
    return out


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
                return bool(getattr(x, "wrappedValue", x)) if x is not None else False
            sup = [val("TranslationalStiffnessX"), val("TranslationalStiffnessY"),
                   val("TranslationalStiffnessZ"), val("RotationalStiffnessX"),
                   val("RotationalStiffnessY"), val("RotationalStiffnessZ")]
        model["nodos"][conn.Name] = {"x": coords[0], "y": coords[1], "z": coords[2],
                                     "apoyo": sup}

    def _node_at(x, y, z, tol=1e-4):
        for nm, nd in model["nodos"].items():
            if abs(nd["x"] - x) < tol and abs(nd["y"] - y) < tol and abs(nd["z"] - z) < tol:
                return nm
        return None

    for mb in ifc.by_type("IfcStructuralCurveMember"):
        ps = _psets(mb).get("Pset_Estructurando_Analisis", {})
        ni, nj = ps.get("NodoInicial"), ps.get("NodoFinal")
        if (ni is None or nj is None) and getattr(mb, "Representation", None):
            for r in mb.Representation.Representations:
                for item in r.Items:
                    if item.is_a("IfcEdge"):
                        cs = item.EdgeStart.VertexGeometry.Coordinates
                        ce = item.EdgeEnd.VertexGeometry.Coordinates
                        ni = ni or _node_at(float(cs[0]), float(cs[1]), float(cs[2]))
                        nj = nj or _node_at(float(ce[0]), float(ce[1]), float(ce[2]))
        relmat = _associated_material(mb)
        mat_name = _resolve_material_name(relmat)
        sec_name, sec_props = _resolve_section(relmat)
        if sec_name is None:
            sec_name = ps.get("Seccion")
            if sec_name and sec_name not in model["secciones"]:
                model["secciones"][sec_name] = {k: ps.get(k) for k in
                    ("A", "Iy", "Iz", "J", "Wply", "Wely", "h", "Avz", "clase")}
        elif sec_name not in model["secciones"]:
            model["secciones"][sec_name] = sec_props
        # tipo: del Pset si existe; si no, inferir por geometria (vertical -> pilar)
        tipo = ps.get("Tipo")
        if tipo is None:
            tipo = "viga"
            ndi, ndj = model["nodos"].get(ni), model["nodos"].get(nj)
            if ndi and ndj:
                dz = abs(ndi["z"] - ndj["z"])
                dxy = abs(ndi["x"] - ndj["x"]) + abs(ndi["y"] - ndj["y"])
                if dz > 1e-6 and dxy < 1e-6:
                    tipo = "pilar"
        model["barras"][mb.Name] = {
            "ni": ni, "nj": nj, "seccion": sec_name,
            "material": mat_name, "tipo": tipo}

    loads_ortho = _parse_surface_loads_orthodox(ifc)
    for sm in ifc.by_type("IfcStructuralSurfaceMember"):
        ps = _psets(sm)
        geo = ps.get("Pset_Estructurando_Superficie", {})
        coords = _surface_corners(sm)
        esquinas_nombres = []
        if coords:
            esquinas_nombres = [_node_at(x, y, z) for (x, y, z) in coords]
            if any(n is None for n in esquinas_nombres):
                esquinas_nombres = []
        else:
            esquinas_nombres = [s.strip() for s in geo.get("Esquinas", "").split(",") if s.strip()]
            for nm in esquinas_nombres:
                nd = model["nodos"].get(nm)
                if nd:
                    coords.append([nd["x"], nd["y"], nd["z"]])
        espesor = sm.Thickness if getattr(sm, "Thickness", None) is not None else geo.get("Espesor")
        cargas = loads_ortho.get(sm.Name)
        if not cargas:
            cargas = []
            for name, p in ps.items():
                if name.startswith("Pset_Estructurando_Carga_Superficie"):
                    cargas.append({"caso": p.get("Caso"), "qz": p.get("qz_N_m2")})
        model["superficies"].append({
            "nombre": sm.Name, "esquinas": esquinas_nombres, "esquinas_coords": coords,
            "espesor": espesor, "malla": geo.get("TamanoMalla", 0.5),
            "material": _resolve_material_name(_associated_material(sm)) or geo.get("Material"),
            "apoyo": geo.get("Apoyo", ""), "cargas": cargas})
    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modulo_demo.ifc"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/modelo_neutro.json"
    model = parse(ifc_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    json.dump(model, open(out_path, "w", encoding="utf-8"), indent=2, ensure_ascii=False)
    print("Modelo neutro 3D escrito en:", out_path)
    print("  nodos=%d barras=%d superficies=%d" % (
        len(model["nodos"]), len(model["barras"]), len(model["superficies"])))
    for bid, b in model["barras"].items():
        print("  barra '%s': %s->%s sec=%s mat=%s" % (bid, b["ni"], b["nj"], b["seccion"], b["material"]))
    for s in model["superficies"]:
        print("  losa '%s': esquinas=%s t=%s mat=%s cargas=%s" % (
            s["nombre"], s["esquinas_coords"], s["espesor"], s["material"],
            [(c["caso"], c["qz"]) for c in s["cargas"]]))
