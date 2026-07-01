"""
Parser IFC (dominio de analisis estructural) -> MODELO NEUTRO (JSON).

Soporta DOS dialectos de IFC, dando PRIORIDAD a las entidades estandar
(IFC ortodoxo) y cayendo a los Psets propios 'Pset_Estructurando_*' como
respaldo (compatibilidad con los IFC de prueba del catalogo):

  - Nodos + apoyos: IfcStructuralPointConnection + IfcBoundaryNodeCondition.
  - Barras + topologia: IfcStructuralCurveMember + IfcEdge.
  - Seccion: IfcRelAssociatesMaterial -> IfcMaterialProfileSet ->
             IfcMaterialProfile -> IfcIShapeProfileDef  (con DB de perfiles).
             Respaldo: Pset_Estructurando_Analisis.Seccion.
  - Material: IfcMaterialProfileSet.<profile>.Material  o  IfcMaterial directo.
  - Cargas: IfcStructuralCurveAction + IfcStructuralLoadLinearForce, con el caso
            (G/Q) tomado del IfcStructuralLoadGroup (IfcRelAssignsToGroup) y la
            barra de IfcRelConnectsStructuralActivity.
            Respaldo: IfcStructuralLinearAction + Pset_Estructurando_Carga.

Salida: dict serializable a JSON. Uso:
  python3 ifc_to_model.py <archivo.ifc> <salida.json>
"""
import sys
import os
import json
import ifcopenshell

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import perfiles_db

# nucleo transversal (PT 4.1, Ola 4): _psets centralizado (antes duplicado)
sys.path.insert(0, os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "nucleo"))
import ifc_utils


# --- Psets propios (respaldo) -> nucleo (ifc_utils.psets); adaptador fino ----
_psets = ifc_utils.psets


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
        try:
            return bool(a.wrappedValue)
        except AttributeError:
            return bool(a)
    return [val("TranslationalStiffnessX"), val("TranslationalStiffnessY"),
            val("TranslationalStiffnessZ"), val("RotationalStiffnessX"),
            val("RotationalStiffnessY"), val("RotationalStiffnessZ")]


# --- Material y seccion de un miembro --------------------------------------
def _associated_material(mb):
    """Devuelve el RelatingMaterial de la IfcRelAssociatesMaterial del miembro."""
    for rel in getattr(mb, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            return rel.RelatingMaterial
    return None


def _resolve_material_name(relmat):
    """Nombre del material desde IfcMaterial, IfcMaterialProfileSet o
    IfcMaterialProfile."""
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
    """(nombre_seccion, props) desde un IfcMaterialProfileSet/Profile. None si
    no hay perfil asociado."""
    if relmat is None:
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


# --- Cargas ortodoxas ------------------------------------------------------
def _action_bar_map(ifc):
    """IfcStructuralCurveAction -> nombre de barra (IfcStructuralCurveMember),
    via IfcRelConnectsStructuralActivity."""
    out = {}
    for rel in ifc.by_type("IfcRelConnectsStructuralActivity"):
        act = rel.RelatedStructuralActivity
        el = rel.RelatingElement
        if act is not None and el is not None:
            out[act.id()] = el.Name
    return out


def _action_case_map(ifc):
    """IfcStructuralCurveAction -> nombre de caso (IfcStructuralLoadGroup),
    via IfcRelAssignsToGroup."""
    out = {}
    for rel in ifc.by_type("IfcRelAssignsToGroup"):
        grp = rel.RelatingGroup
        if grp is None or not grp.is_a("IfcStructuralLoadGroup"):
            continue
        for obj in rel.RelatedObjects or []:
            out[obj.id()] = grp.Name
    return out


def _linear_force_qz(load):
    """Componente vertical (Z global) de un IfcStructuralLoadLinearForce [N/m]."""
    if load is None:
        return None
    if load.is_a("IfcStructuralLoadLinearForce"):
        fz = getattr(load, "LinearForceZ", None)
        return float(fz) if fz is not None else None
    return None


def _parse_loads_orthodox(ifc):
    bar_of = _action_bar_map(ifc)
    case_of = _action_case_map(ifc)
    cargas = []
    for act in ifc.by_type("IfcStructuralCurveAction"):
        qz = _linear_force_qz(act.AppliedLoad)
        if qz is None:
            continue
        cargas.append({
            "caso": case_of.get(act.id()),
            "barra": bar_of.get(act.id()),
            "direccion": "GZ",
            "qz": qz,
        })
    return cargas


def _parse_loads_pset(ifc):
    cargas = []
    for act in ifc.by_type("IfcStructuralLinearAction"):
        carga = _psets(act).get("Pset_Estructurando_Carga", {})
        if carga:
            cargas.append({
                "caso": carga.get("Caso"),
                "barra": carga.get("Barra"),
                "direccion": carga.get("Direccion", "GZ"),
                "qz": carga.get("qz_N_m"),
            })
    return cargas


# --- Parser principal ------------------------------------------------------
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

    # Nodos
    vertex_to_node = {}
    for conn in ifc.by_type("IfcStructuralPointConnection"):
        name = conn.Name
        model["nodos"][name] = {"x": None, "y": None, "z": None,
                                "apoyo": _support(conn)}
        coords = _node_coords(conn)
        if coords:
            (model["nodos"][name]["x"], model["nodos"][name]["y"],
             model["nodos"][name]["z"]) = coords
        for r in conn.Representation.Representations:
            for item in r.Items:
                if item.is_a("IfcVertexPoint"):
                    vertex_to_node[item.id()] = name

    # Barras
    for mb in ifc.by_type("IfcStructuralCurveMember"):
        ps = _psets(mb)
        analisis = ps.get("Pset_Estructurando_Analisis", {})

        # nodos: primero Pset, respaldo topologia IfcEdge
        ni = analisis.get("NodoInicial")
        nj = analisis.get("NodoFinal")
        if (ni is None or nj is None) and mb.Representation:
            for r in mb.Representation.Representations:
                for item in r.Items:
                    if item.is_a("IfcEdge"):
                        ni = ni or vertex_to_node.get(item.EdgeStart.id())
                        nj = nj or vertex_to_node.get(item.EdgeEnd.id())
                        # respaldo por COORDENADAS: si el IFC usa vertices
                        # distintos para la arista y para el punto de conexion
                        # (caso 10) el id no casa; se resuelve por posicion.
                        if ni is None or nj is None:
                            def _match(vp):
                                try:
                                    c = vp.VertexGeometry.Coordinates
                                except Exception:
                                    return None
                                for nm, nd in model["nodos"].items():
                                    if (nd["x"] is not None and
                                            abs(nd["x"] - float(c[0])) < 1e-4 and
                                            abs(nd["y"] - float(c[1])) < 1e-4 and
                                            abs(nd["z"] - float(c[2])) < 1e-4):
                                        return nm
                                return None
                            ni = ni or _match(item.EdgeStart)
                            nj = nj or _match(item.EdgeEnd)

        # material + seccion: PRIORIDAD entidades estandar
        relmat = _associated_material(mb)
        mat_name = _resolve_material_name(relmat)
        sec_name, sec_props = _resolve_section(relmat)

        # respaldo Pset para seccion
        if sec_name is None:
            sec_name = analisis.get("Seccion")
            if sec_name and sec_name not in model["secciones"]:
                model["secciones"][sec_name] = {
                    k: analisis.get(k) for k in
                    ("A", "Iy", "Iz", "J", "Wply", "Wely", "h", "Avz", "clase")
                }
        elif sec_name not in model["secciones"]:
            model["secciones"][sec_name] = sec_props

        model["barras"][mb.Name] = {
            "ni": ni, "nj": nj, "seccion": sec_name,
            "material": mat_name, "tipo": analisis.get("Tipo") or
            (mb.PredefinedType if getattr(mb, "PredefinedType", None) else None),
        }

    # Cargas: ortodoxas y, si no hay, respaldo Pset
    cargas = _parse_loads_orthodox(ifc)
    if not cargas:
        cargas = _parse_loads_pset(ifc)
    model["cargas"] = cargas

    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/portico_demo.ifc"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/modelo_neutro.json"
    model = parse(ifc_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2, ensure_ascii=False)
    print("Modelo neutro escrito en:", out_path)
    print(json.dumps(model, indent=2, ensure_ascii=False))
