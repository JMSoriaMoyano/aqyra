"""
PUENTE FISICO -> ANALITICO  (Direccion 2, modulo puente_analitico).

Convierte un IFC FISICO (entregable BIM real: IfcColumn/IfcBeam/IfcMember con
GEOMETRIA Body de barrido, IfcMaterialProfileSetUsage y estructura espacial, SIN
entidades de analisis ni cargas) en el MISMO modelo neutro estandar que ya consume
el motor, para reutilizar el clasificador/enrutador y los solvers sin cambios.

Que hace el puente (caso R1, elementos lineales):
  1. EXTRACCION GEOMETRICA por elemento (IfcColumn/IfcBeam/IfcMember):
       - eje  = directriz del barrido: origen = traslacion del ObjectPlacement
         compuesto (ifcopenshell.util.placement.get_local_placement), direccion =
         eje local Z del placement, longitud = Depth del IfcExtrudedAreaSolid
         (respaldo: ExtrudedDirection*Depth si la directriz no es +Z local).
       - perfil = IfcMaterialProfileSetUsage -> IfcMaterialProfileSet ->
         IfcMaterialProfile -> IfcIShapeProfileDef  (reutiliza perfiles_db, con
         prioridad a catalogo; geometria del SweptArea como respaldo).
       - material = IfcMaterial del profile set; propiedades mecanicas de
         IfcMaterialProperties.
  2. CONECTIVIDAD / NUDOS: grafo de uniones por interseccion de ejes con
     TOLERANCIA -> fusion de extremos coincidentes y troceo de barras cuando el
     extremo de una cae en el interior de otra (R1: ejes limpios que se cortan en
     los extremos -> 4 nudos; los offsets/excentricidades fisico<->analitico se
     endurecen en R5).
  3. APOYOS: inferidos de Pset_Estructurando_ApoyoBase (cota base, biarticulado)
     o, en su defecto, de la cota minima.  CARGAS: el IFC fisico no las trae ->
     hipotesis de proyecto en Pset_Estructurando_CargaHipotesis (G/Q, direccion).
  4. SALIDA: modelo neutro estandar (mismas claves que barras/ifc_to_model.py).

Uso:
  python3 puente.py <archivo_fisico.ifc> <salida.json>
"""
import sys
import os
import json
import math

import ifcopenshell
import ifcopenshell.util.placement as _place

# perfiles_db vive en scripts/barras: ruta explicita (no contaminar sys.path global)
_HERE = os.path.dirname(os.path.abspath(__file__))
_BARRAS = os.path.join(os.path.dirname(_HERE), "barras")
if _BARRAS not in sys.path:
    sys.path.insert(0, _BARRAS)
import perfiles_db  # noqa: E402

TOL = 1e-3  # tolerancia de fusion de nudos (m)

# Material por defecto (respaldo si el IFC no trae propiedades mecanicas)
_MAT_DEFECTO = {
    "S275": {"E": 210e9, "G": 80.77e9, "nu": 0.3, "rho": 7850.0, "fy": 275e6},
    "S235": {"E": 210e9, "G": 80.77e9, "nu": 0.3, "rho": 7850.0, "fy": 235e6},
    "S355": {"E": 210e9, "G": 80.77e9, "nu": 0.3, "rho": 7850.0, "fy": 355e6},
}


# --- Psets ------------------------------------------------------------------
def _psets(element):
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
    """Propiedades mecanicas por material desde IfcMaterialProperties."""
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        m = mp.Material
        d = {}
        for p in mp.Properties:
            if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                d[p.Name] = p.NominalValue.wrappedValue
        mats[m.Name] = {
            "E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fy": d.get("YieldStress"),
        }
    return mats


# --- Geometria del elemento -------------------------------------------------
def _swept_solid(element):
    rep = getattr(element, "Representation", None)
    if rep is None:
        return None
    for r in rep.Representations:
        for item in r.Items:
            if item.is_a("IfcExtrudedAreaSolid"):
                return item
            if item.is_a("IfcMappedItem"):
                src = item.MappingSource.MappedRepresentation
                for it2 in src.Items:
                    if it2.is_a("IfcExtrudedAreaSolid"):
                        return it2
    return None


def _eje(element):
    """Devuelve (p0, p1) en coordenadas de MUNDO del eje del elemento lineal."""
    M = _place.get_local_placement(element.ObjectPlacement)
    p0 = [float(M[i][3]) for i in range(3)]
    zax = [float(M[i][2]) for i in range(3)]   # eje local Z = directriz del barrido
    solid = _swept_solid(element)
    if solid is None:
        return None
    depth = float(solid.Depth)
    # direccion de extrusion (normalmente +Z local); si no, proyectar al mundo
    ed = solid.ExtrudedDirection.DirectionRatios
    if abs(ed[0]) < 1e-9 and abs(ed[1]) < 1e-9 and abs(ed[2] - 1.0) < 1e-9:
        d = zax
    else:
        # combinar ejes locales del placement con la direccion de extrusion local
        xax = [float(M[i][0]) for i in range(3)]
        yax = [float(M[i][1]) for i in range(3)]
        d = [xax[i] * ed[0] + yax[i] * ed[1] + zax[i] * ed[2] for i in range(3)]
        nrm = math.sqrt(sum(c * c for c in d)) or 1.0
        d = [c / nrm for c in d]
    p1 = [p0[i] + d[i] * depth for i in range(3)]
    return p0, p1


def _profile_and_material(element):
    """(nombre_seccion, props, nombre_material) desde IfcMaterialProfileSetUsage."""
    relmat = None
    for rel in getattr(element, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            relmat = rel.RelatingMaterial
            break
    if relmat is None:
        return None, None, None
    mps = None
    if relmat.is_a("IfcMaterialProfileSetUsage"):
        mps = relmat.ForProfileSet
    elif relmat.is_a("IfcMaterialProfileSet"):
        mps = relmat
    elif relmat.is_a("IfcMaterialProfile"):
        prof = relmat.Profile
        mat = relmat.Material.Name if relmat.Material else None
        nm, props = perfiles_db.props_from_profile_def(prof)
        return nm, props, mat
    if mps is None or not mps.MaterialProfiles:
        return None, None, None
    mprof = mps.MaterialProfiles[0]
    prof = mprof.Profile
    mat = mprof.Material.Name if mprof.Material else None
    nm, props = perfiles_db.props_from_profile_def(prof)
    return nm, props, mat


# --- Grafo de nudos ---------------------------------------------------------
class _Nodos:
    """Registro de nudos con fusion por tolerancia."""
    def __init__(self, tol=TOL):
        self.tol = tol
        self.coords = []   # lista de [x,y,z]
        self.names = []    # nombre asignado

    def add(self, c):
        for i, q in enumerate(self.coords):
            if (abs(q[0] - c[0]) <= self.tol and abs(q[1] - c[1]) <= self.tol
                    and abs(q[2] - c[2]) <= self.tol):
                return i
        self.coords.append([float(c[0]), float(c[1]), float(c[2])])
        self.names.append("N%d" % len(self.coords))
        return i if False else len(self.coords) - 1


def _punto_en_segmento(p, a, b, tol):
    """True si p cae en el INTERIOR del segmento a-b (para troceo en cruces)."""
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    L2 = sum(c * c for c in ab)
    if L2 < tol * tol:
        return False
    t = sum(ap[i] * ab[i] for i in range(3)) / L2
    if t <= tol or t >= 1.0 - tol:
        return False  # coincide con un extremo, no es interior
    proj = [a[i] + t * ab[i] for i in range(3)]
    d = math.sqrt(sum((p[i] - proj[i]) ** 2 for i in range(3)))
    return d <= tol


# --- Construccion del modelo neutro ----------------------------------------
def _es_vertical(p0, p1):
    dx = p1[0] - p0[0]; dy = p1[1] - p0[1]; dz = p1[2] - p0[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    return abs(dz) > 1e-6 and horiz < 1e-6


def parse(ifc_path):
    ifc = ifcopenshell.open(ifc_path)
    model = {
        "unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m"},
        "origen": "puente_fisico_analitico",
        "materiales": _material_props(ifc),
        "secciones": {},
        "nodos": {},
        "barras": {},
        "cargas": [],
        "hipotesis": {"apoyos": [], "cargas": []},
    }

    # 1) extraer elementos lineales fisicos
    elementos = []
    for cls in ("IfcColumn", "IfcBeam", "IfcMember"):
        for el in ifc.by_type(cls):
            ejes = _eje(el)
            if ejes is None:
                continue
            p0, p1 = ejes
            sec_name, sec_props, mat = _profile_and_material(el)
            elementos.append({
                "ifc": el, "clase": cls, "nombre": el.Name or ("E%d" % el.id()),
                "p0": p0, "p1": p1, "seccion": sec_name, "props": sec_props,
                "material": mat,
            })

    # 2) nudos por fusion de extremos (+ troceo en cruces interiores con tolerancia)
    nod = _Nodos(TOL)
    # primero registrar todos los extremos
    extremos = []
    for e in elementos:
        extremos.append(e["p0"]); extremos.append(e["p1"])
    # troceo: si un extremo cae en el interior de un eje, ese eje se parte ahi
    puntos_corte = {id(e): [] for e in elementos}
    for e in elementos:
        for pe in extremos:
            if _punto_en_segmento(pe, e["p0"], e["p1"], TOL):
                puntos_corte[id(e)].append(pe)
    # construir sub-barras por elemento (troceadas en sus puntos de corte ordenados)
    bar_counter = {"pilar": 0, "viga": 0}
    for e in elementos:
        tipo = "pilar" if _es_vertical(e["p0"], e["p1"]) else "viga"
        # ordenar puntos del eje (extremos + cortes) por parametro t
        ab = [e["p1"][i] - e["p0"][i] for i in range(3)]
        L2 = sum(c * c for c in ab) or 1.0
        pts = [e["p0"], e["p1"]] + puntos_corte[id(e)]
        uniq = []
        for p in pts:
            t = sum((p[i] - e["p0"][i]) * ab[i] for i in range(3)) / L2
            if not any(abs(t - tt) < 1e-6 for tt, _ in uniq):
                uniq.append((t, p))
        uniq.sort(key=lambda x: x[0])
        # seccion
        if e["seccion"] and e["seccion"] not in model["secciones"] and e["props"]:
            model["secciones"][e["seccion"]] = e["props"]
        # crear cada tramo
        seg_names = []
        for k in range(len(uniq) - 1):
            a = uniq[k][1]; b = uniq[k + 1][1]
            ia = nod.add(a); ib = nod.add(b)
            bar_counter[tipo] += 1
            bname = ("C%d" if tipo == "pilar" else "B%d") % bar_counter[tipo]
            model["barras"][bname] = {
                "ni": nod.names[ia], "nj": nod.names[ib],
                "seccion": e["seccion"], "material": e["material"], "tipo": tipo,
                "elemento_fisico": e["nombre"], "clase_ifc": e["clase"],
            }
            seg_names.append(bname)
        e["barras_analiticas"] = seg_names

    # 3) escribir nudos con coordenadas (apoyo se rellena luego)
    for i, c in enumerate(nod.coords):
        model["nodos"][nod.names[i]] = {
            "x": c[0], "y": c[1], "z": c[2], "apoyo": [False] * 6,
        }

    # 4) apoyos: Pset_Estructurando_ApoyoBase -> cota base biarticulada
    cotas_apoyo = []
    tipo_apoyo = "biarticulado"
    for e in elementos:
        ps = _psets(e["ifc"])
        ab = ps.get("Pset_Estructurando_ApoyoBase")
        if ab:
            cotas_apoyo.append(float(ab.get("Cota_z_m", 0.0)))
            tipo_apoyo = ab.get("Tipo", tipo_apoyo)
    if not cotas_apoyo:
        # respaldo: cota minima de los nudos
        cotas_apoyo = [min(n["z"] for n in model["nodos"].values())]
    cota_base = min(cotas_apoyo)
    # biarticulado en el plano XZ: traslaciones coaccionadas, giro en plano libre
    # (= [DX,DY,DZ,RX,RY,RZ] = [T,T,T,F,F,T], igual que el caso 1)
    if tipo_apoyo.lower().startswith("biarticul") or tipo_apoyo.lower() == "articulado":
        apoyo_base = [True, True, True, False, False, True]
    else:  # empotrado
        apoyo_base = [True, True, True, True, True, True]
    for nm, n in model["nodos"].items():
        if abs(n["z"] - cota_base) <= TOL:
            n["apoyo"] = list(apoyo_base)
            model["hipotesis"]["apoyos"].append(
                {"nodo": nm, "cota_z": n["z"], "tipo": tipo_apoyo})

    # 5) cargas: Pset_Estructurando_CargaHipotesis -> G/Q sobre la barra del elemento
    for e in elementos:
        ps = _psets(e["ifc"])
        ch = ps.get("Pset_Estructurando_CargaHipotesis")
        if not ch:
            continue
        direccion = ch.get("Direccion", "-Z")
        signo = -1.0 if str(direccion).strip().upper().startswith("-Z") else 1.0
        barra = (e.get("barras_analiticas") or [None])[0]
        for caso, key in (("G", "G_kN_m"), ("Q", "Q_kN_m")):
            if ch.get(key) is not None:
                qz = signo * float(ch[key]) * 1000.0  # kN/m -> N/m
                model["cargas"].append({
                    "caso": caso, "barra": barra, "direccion": "GZ", "qz": qz})
                model["hipotesis"]["cargas"].append({
                    "barra": barra, "elemento_fisico": e["nombre"], "caso": caso,
                    "q_kN_m": float(ch[key]), "direccion": direccion,
                    "descripcion": ch.get("Descripcion")})

    # 6) respaldo de propiedades de material por defecto si el IFC no las trae
    for mname, mp in list(model["materiales"].items()):
        if mp.get("E") is None and mname in _MAT_DEFECTO:
            model["materiales"][mname] = dict(_MAT_DEFECTO[mname])
    # materiales referidos por barras pero sin entrada
    for b in model["barras"].values():
        mn = b["material"]
        if mn and mn not in model["materiales"]:
            model["materiales"][mn] = dict(_MAT_DEFECTO.get(mn, _MAT_DEFECTO["S275"]))

    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "caso-R1.ifc"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "modelo_neutro.json"
    model = parse(ifc_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2, ensure_ascii=False)
    print("Puente fisico->analitico:", out_path)
    print("  nodos=%d  barras=%d  cargas=%d" % (
        len(model["nodos"]), len(model["barras"]), len(model["cargas"])))
