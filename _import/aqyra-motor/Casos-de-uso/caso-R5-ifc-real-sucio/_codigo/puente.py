"""
PUENTE FISICO -> ANALITICO  (Direccion 2, modulo puente_analitico).

Convierte un IFC FISICO (entregable BIM real: IfcColumn/IfcBeam/IfcMember con
GEOMETRIA Body de barrido, IfcMaterialProfileSetUsage y estructura espacial, y
-desde R2- IfcSlab con IfcMaterialLayerSet, SIN entidades de analisis ni cargas)
en el MISMO modelo neutro estandar que ya consume el motor, para reutilizar el
clasificador/enrutador y los solvers sin cambios.

Que hace el puente:
  ELEMENTOS LINEALES (caso R1, IfcColumn/IfcBeam/IfcMember):
    1. eje = directriz del barrido: origen = traslacion del ObjectPlacement
       compuesto (ifcopenshell.util.placement.get_local_placement), direccion =
       eje local Z del placement, longitud = Depth del IfcExtrudedAreaSolid.
    2. perfil = IfcMaterialProfileSetUsage -> IfcMaterialProfileSet ->
       IfcMaterialProfile -> IfcIShapeProfileDef (reutiliza perfiles_db, con
       prioridad a catalogo; geometria del SweptArea como respaldo).
    3. material = IfcMaterial del profile set; props de IfcMaterialProperties.

  SUPERFICIES FISICAS (caso R2, IfcSlab; en R3 IfcWall/IfcFooting):
    4. SUPERFICIE MEDIA = footprint del IfcExtrudedAreaSolid (esquinas del
       SweptArea -IfcRectangleProfileDef/IfcArbitraryClosedProfileDef-) llevado a
       coordenadas de MUNDO con el placement compuesto (get_local_placement) y la
       Position del solido (get_axis2placement); la cota = z medio del barrido
       (base + ExtrudedDirection*Depth/2).
    5. ESPESOR = Sigma LayerThickness de IfcMaterialLayerSetUsage ->
       IfcMaterialLayerSet -> IfcMaterialLayer (geometria -Depth- como respaldo);
       MATERIAL = IfcRelAssociatesMaterial -> IfcMaterial (props de hormigon:
       fck de CompressiveStrength, fctm de TensileStrength o derivado EC2).
    6. CONECTIVIDAD superficie<->barras: la losa se asocia a las VIGAS que la
       soportan (eje de viga dentro/bajo el contorno en planta, por proximidad,
       como el clasificador del caso 10) -> 'vigas_asociadas'.

  CONDICIONES (no estan en el IFC fisico, son HIPOTESIS del calculista):
    APOYOS de Pset_Estructurando_ApoyoBase (cota base, biarticulado).
    CARGAS de Pset_Estructurando_CargaHipotesis: de SUPERFICIE (G/Q kN/m2) si
    esta en la losa; de LINEA (G/Q kN/m) si esta en una barra (R1).

  SALIDA: modelo neutro estandar (mismas claves que laminas/ifc_to_model_3d.py:
  nodos, barras, secciones, superficies[], materiales, cargas, hipotesis).

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

# CardinalPoint (IfcMaterialProfileSetUsage): posicion del eje de referencia SOBRE
# la seccion, en fracciones de (ancho b, canto h) relativas al centroide. 5=centroide.
CP_FRAC = {1: (-0.5, -0.5), 2: (0.0, -0.5), 3: (0.5, -0.5),
           4: (-0.5, 0.0), 5: (0.0, 0.0), 6: (0.5, 0.0),
           7: (-0.5, 0.5), 8: (0.0, 0.5), 9: (0.5, 0.5)}

_PREFIJO_SI = {None: 1.0, "EXA": 1e18, "PETA": 1e15, "TERA": 1e12, "GIGA": 1e9,
               "MEGA": 1e6, "KILO": 1e3, "HECTO": 1e2, "DECA": 1e1, "DECI": 1e-1,
               "CENTI": 1e-2, "MILLI": 1e-3, "MICRO": 1e-6, "NANO": 1e-9}


def _length_scale(ifc):
    """Factor para pasar la unidad de longitud del IFC a METROS (respeta el
    IfcUnitAssignment del exportador). METRE->1.0; MILLIMETRE->1e-3; unidades de
    conversion (pulgada, pie) -> su factor. Por defecto 1.0 (modelos R1-R4 en m)."""
    try:
        for ua in ifc.by_type("IfcUnitAssignment"):
            for u in ua.Units:
                if u.is_a("IfcSIUnit") and u.UnitType == "LENGTHUNIT":
                    return _PREFIJO_SI.get(getattr(u, "Prefix", None), 1.0)
                if u.is_a("IfcConversionBasedUnit") and u.UnitType == "LENGTHUNIT":
                    return float(u.ConversionFactor.ValueComponent.wrappedValue)
    except Exception:
        pass
    return 1.0


def _snap_tol_from_ifc(ifc, defecto=TOL):
    """Tolerancia de snap (m) del Pset_Estructurando_Puente (proyecto o elemento);
    si no existe, la trivial de R1-R4 (TOL=1 mm) -> comportamiento identico."""
    try:
        for pset in ifc.by_type("IfcPropertySet"):
            if pset.Name == "Pset_Estructurando_Puente":
                for p in pset.HasProperties:
                    if p.is_a("IfcPropertySingleValue") and p.Name == "Snap_tol_m" \
                            and p.NominalValue is not None:
                        return float(p.NominalValue.wrappedValue)
    except Exception:
        pass
    return defecto


def _profile_bh(element, scale=1.0):
    """(b, h) en METROS del perfil del profile set (escalados). (None,None) si no."""
    for rel in getattr(element, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            rm = rel.RelatingMaterial
            mps = None
            if rm.is_a("IfcMaterialProfileSetUsage"):
                mps = rm.ForProfileSet
            elif rm.is_a("IfcMaterialProfileSet"):
                mps = rm
            if mps is not None and mps.MaterialProfiles:
                prof = mps.MaterialProfiles[0].Profile
                if prof.is_a("IfcIShapeProfileDef"):
                    return float(prof.OverallWidth) * scale, float(prof.OverallDepth) * scale
                if prof.is_a("IfcRectangleProfileDef"):
                    return float(prof.XDim) * scale, float(prof.YDim) * scale
                if prof.is_a("IfcCircleProfileDef"):
                    d = 2.0 * float(prof.Radius) * scale
                    return d, d
            break
    return None, None


def _cardinal_point(element):
    for rel in getattr(element, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            rm = rel.RelatingMaterial
            if rm.is_a("IfcMaterialProfileSetUsage"):
                return getattr(rm, "CardinalPoint", None)
            break
    return None


def _axis_recovery(element, p0, p1, scale=1.0):
    """Recupera el eje ANALITICO (baricentrico) a partir del eje FISICO (p0,p1)
    aplicando el offset del CardinalPoint del IfcMaterialProfileSetUsage sobre los
    ejes locales del placement. Devuelve (p0c, p1c, ecc, cp). cp=5/None -> sin
    offset (identidad) -> R1-R4 (cardinal 5) quedan EXACTAMENTE igual."""
    cp = _cardinal_point(element)
    if cp is None or int(cp) == 5:
        return p0, p1, 0.0, (int(cp) if cp is not None else 5)
    fr = CP_FRAC.get(int(cp))
    if fr is None:
        return p0, p1, 0.0, int(cp)
    b, h = _profile_bh(element, scale)
    if b is None:
        return p0, p1, 0.0, int(cp)
    M = _to_list4(_place.get_local_placement(element.ObjectPlacement))
    xax = [M[i][0] for i in range(3)]
    yax = [M[i][1] for i in range(3)]
    nx = math.sqrt(sum(c * c for c in xax)) or 1.0
    ny = math.sqrt(sum(c * c for c in yax)) or 1.0
    xax = [c / nx for c in xax]
    yax = [c / ny for c in yax]
    cpx = fr[0] * b
    cpy = fr[1] * h
    off = [cpx * xax[i] + cpy * yax[i] for i in range(3)]
    p0c = [p0[i] - off[i] for i in range(3)]
    p1c = [p1[i] - off[i] for i in range(3)]
    ecc = math.sqrt(cpx * cpx + cpy * cpy)
    return p0c, p1c, ecc, int(cp)


# --- algebra de matrices 4x4 (sin numpy obligatorio) ------------------------
def _matmul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(4)) for j in range(4)]
            for i in range(4)]


def _apply(M, p):
    """Transforma el punto p=[x,y,z] por la matriz homogenea 4x4 M."""
    x = M[0][0] * p[0] + M[0][1] * p[1] + M[0][2] * p[2] + M[0][3]
    y = M[1][0] * p[0] + M[1][1] * p[1] + M[1][2] * p[2] + M[1][3]
    z = M[2][0] * p[0] + M[2][1] * p[1] + M[2][2] * p[2] + M[2][3]
    return [float(x), float(y), float(z)]


def _to_list4(M):
    """Convierte una matriz (numpy o lista) a lista 4x4 de floats."""
    return [[float(M[i][j]) for j in range(4)] for i in range(4)]


def _ident4():
    return [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]


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


def _fctm_from_fck(fck_pa):
    """EC2 Tabla 3.1: fctm = 0.30 fck^(2/3) (fck<=50 MPa), en Pa."""
    if not fck_pa:
        return None
    fck_mpa = fck_pa / 1e6
    if fck_mpa <= 50.0:
        fctm_mpa = 0.30 * fck_mpa ** (2.0 / 3.0)
    else:
        fctm_mpa = 2.12 * math.log(1.0 + (fck_mpa + 8.0) / 10.0)
    return fctm_mpa * 1e6


def _material_props(ifc):
    """Propiedades mecanicas por material desde IfcMaterialProperties.
    Incluye fck (CompressiveStrength) y fctm (TensileStrength o derivado EC2)
    para hormigon, ademas de E/G/nu/rho/fy."""
    mats = {}
    for mp in ifc.by_type("IfcMaterialProperties"):
        m = mp.Material
        d = {}
        for p in mp.Properties:
            if p.is_a("IfcPropertySingleValue") and p.NominalValue is not None:
                d[p.Name] = p.NominalValue.wrappedValue
        fck = d.get("CompressiveStrength")
        fctm = d.get("TensileStrength")
        if fck is not None and fctm is None:
            fctm = _fctm_from_fck(float(fck))
        entry = {
            "E": d.get("YoungModulus"), "G": d.get("ShearModulus"),
            "nu": d.get("PoissonRatio"), "rho": d.get("MassDensity"),
            "fy": d.get("YieldStress"),
        }
        if fck is not None:
            entry["fck"] = float(fck)
        if fctm is not None:
            entry["fctm"] = float(fctm)
        mats[m.Name] = entry
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


def _eje(element, scale=1.0):
    """Devuelve (p0, p1) en coordenadas de MUNDO del eje del elemento lineal."""
    M = _place.get_local_placement(element.ObjectPlacement)
    p0 = [float(M[i][3]) * scale for i in range(3)]
    zax = [float(M[i][2]) for i in range(3)]   # eje local Z = directriz del barrido
    solid = _swept_solid(element)
    if solid is None:
        return None
    depth = float(solid.Depth) * scale
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


# --- Geometria de la SUPERFICIE (losa/muro/zapata fisicos) -----------------
def _profile_corners_2d(prof):
    """Esquinas (lista de [x,y]) del perfil del SweptArea, en su plano local,
    aplicando su Position 2D si la tiene."""
    pts = []
    if prof.is_a("IfcRectangleProfileDef"):
        xd = float(prof.XDim); yd = float(prof.YDim)
        pts = [[-xd / 2.0, -yd / 2.0], [xd / 2.0, -yd / 2.0],
               [xd / 2.0, yd / 2.0], [-xd / 2.0, yd / 2.0]]
    elif prof.is_a("IfcArbitraryClosedProfileDef"):
        curve = prof.OuterCurve
        if curve.is_a("IfcPolyline"):
            raw = [[float(p.Coordinates[0]), float(p.Coordinates[1])]
                   for p in curve.Points]
            # quitar el punto de cierre repetido si existe
            if len(raw) >= 2 and abs(raw[0][0] - raw[-1][0]) < 1e-9 \
                    and abs(raw[0][1] - raw[-1][1]) < 1e-9:
                raw = raw[:-1]
            pts = raw
    if not pts:
        return []
    # aplicar Position 2D del perfil (IfcAxis2Placement2D)
    pos = getattr(prof, "Position", None)
    if pos is not None and pos.Location is not None:
        ox = float(pos.Location.Coordinates[0]); oy = float(pos.Location.Coordinates[1])
        rd = getattr(pos, "RefDirection", None)
        if rd is not None:
            cx, cy = float(rd.DirectionRatios[0]), float(rd.DirectionRatios[1])
        else:
            cx, cy = 1.0, 0.0
        out = []
        for x, y in pts:
            wx = ox + cx * x - cy * y
            wy = oy + cy * x + cx * y
            out.append([wx, wy])
        pts = out
    return pts


def _superficie(element, clase=None, espesor_layer=None):
    """Devuelve dict de superficie en MUNDO clasificada por ORIENTACION o None.

    Distingue dos familias de superficie barrida (extrusion VERTICAL +Z):
      - HORIZONTAL (IfcSlab/IfcFooting): el plano medio es el FOOTPRINT en planta a
        la cota media del barrido; el ESPESOR/canto = profundidad de extrusion.
      - VERTICAL (IfcWall extruido en +Z): la huella es un rectangulo "alargado y
        fino" (un lado ~ espesor); el plano medio es VERTICAL (longitud L_w del
        muro x altura H = profundidad de extrusion), centrado en el lado fino.

    La orientacion se decide por la NORMAL del plano medio:
      - extrusion casi vertical (|edw_z|~1) + footprint fino (IfcWall, un lado <=
        2.5x espesor, o el menor lado << el mayor) -> VERTICAL (normal horizontal).
      - resto -> HORIZONTAL (normal vertical).

    Devuelve:
      {esquinas_coords:[[x,y,z]x4], z_med, espesor_geom, orientacion, normal,
       espesor_lado, largo}.
    """
    M = _to_list4(_place.get_local_placement(element.ObjectPlacement))
    solid = _swept_solid(element)
    if solid is None:
        return None
    depth = float(solid.Depth)
    prof = solid.SweptArea
    corners2d = _profile_corners_2d(prof)
    if not corners2d:
        return None
    # Position del solido (IfcAxis2Placement3D) -> matriz local del barrido
    Msolid = _ident4()
    if getattr(solid, "Position", None) is not None:
        Msolid = _to_list4(_place.get_axis2placement(solid.Position))
    Mtot = _matmul(M, Msolid)
    # direccion de extrusion en MUNDO (vector normalizado) -> orientacion del barrido
    ed = solid.ExtrudedDirection.DirectionRatios
    edw = [Mtot[i][0] * ed[0] + Mtot[i][1] * ed[1] + Mtot[i][2] * ed[2] for i in range(3)]
    nrm = math.sqrt(sum(c * c for c in edw)) or 1.0
    edw = [c / nrm for c in edw]
    edw_z = edw[2]
    # base del footprint en MUNDO (plano del SweptArea, z local = 0)
    base = [_apply(Mtot, [cx, cy, 0.0]) for cx, cy in corners2d]
    z_base = sum(c[2] for c in base) / len(base)

    # lados del footprint en planta (bbox) -> aspecto fino / alargado
    xs = [c[0] for c in base]; ys = [c[1] for c in base]
    sx = max(xs) - min(xs); sy = max(ys) - min(ys)
    lado_menor = min(sx, sy); lado_mayor = max(sx, sy)
    extrusion_vertical = abs(abs(edw_z) - 1.0) < 1e-3

    # criterio de muro VERTICAL: IfcWall + extrusion vertical + footprint fino
    esp_ref = espesor_layer if espesor_layer else lado_menor
    es_fino = (lado_menor <= 2.5 * esp_ref + 1e-9) and (lado_mayor > 1.5 * lado_menor)
    es_muro = (clase == "IfcWall") and extrusion_vertical and es_fino

    if es_muro:
        # PLANO MEDIO VERTICAL: rectangulo (longitud L_w del muro x altura H=depth).
        # Colapsar la direccion FINA del footprint a su linea central; subir de la
        # base del barrido (z_base) a la cabeza (z_base + edw_z*depth).
        z_top = z_base + edw_z * depth
        z_lo, z_hi = min(z_base, z_top), max(z_base, z_top)
        if sx >= sy:
            # muro largo en X, fino en Y -> centro en y
            yc = (min(ys) + max(ys)) / 2.0
            x_lo, x_hi = min(xs), max(xs)
            esquinas = [[x_lo, yc, z_lo], [x_hi, yc, z_lo],
                        [x_hi, yc, z_hi], [x_lo, yc, z_hi]]
            largo = sx; normal = [0.0, 1.0, 0.0]
        else:
            # muro largo en Y, fino en X -> centro en x
            xc = (min(xs) + max(xs)) / 2.0
            y_lo, y_hi = min(ys), max(ys)
            esquinas = [[xc, y_lo, z_lo], [xc, y_hi, z_lo],
                        [xc, y_hi, z_hi], [xc, y_lo, z_hi]]
            largo = sy; normal = [1.0, 0.0, 0.0]
        z_med = (z_lo + z_hi) / 2.0
        return {"esquinas_coords": esquinas, "z_med": z_med, "espesor_geom": lado_menor,
                "orientacion": "vertical", "normal": normal,
                "espesor_lado": lado_menor, "largo": largo, "altura": z_hi - z_lo}

    # HORIZONTAL: footprint a la cota media del barrido; espesor = profundidad
    z_med = z_base + edw_z * depth / 2.0
    esquinas_med = [[c[0], c[1], z_med] for c in base]
    return {"esquinas_coords": esquinas_med, "z_med": z_med, "espesor_geom": depth,
            "orientacion": "horizontal", "normal": [0.0, 0.0, 1.0],
            "espesor_lado": depth, "largo": lado_mayor, "altura": 0.0}


def _layerset_thickness_material(element):
    """(espesor=Sigma LayerThickness, nombre_material) de
    IfcMaterialLayerSetUsage -> IfcMaterialLayerSet. (None,None) si no hay."""
    lset = None
    mat = None
    for rel in getattr(element, "HasAssociations", []) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            rm = rel.RelatingMaterial
            if rm.is_a("IfcMaterialLayerSetUsage"):
                lset = rm.ForLayerSet
            elif rm.is_a("IfcMaterialLayerSet"):
                lset = rm
            elif rm.is_a("IfcMaterial"):
                mat = rm.Name
            break
    if lset is not None and lset.MaterialLayers:
        tot = sum(float(l.LayerThickness) for l in lset.MaterialLayers)
        for l in lset.MaterialLayers:
            if l.Material is not None:
                mat = l.Material.Name
                break
        return tot, mat
    return None, mat


# --- Grafo de nudos ---------------------------------------------------------
class _Nodos:
    """Registro de nudos con fusion por tolerancia."""
    def __init__(self, tol=TOL):
        self.tol = tol
        self.coords = []   # lista de [x,y,z]
        self.names = []    # nombre asignado
        self.fused = []    # (nombre_nodo, distancia) por cada fusion de extremos

    def add(self, c):
        for i, q in enumerate(self.coords):
            if (abs(q[0] - c[0]) <= self.tol and abs(q[1] - c[1]) <= self.tol
                    and abs(q[2] - c[2]) <= self.tol):
                d = math.sqrt(sum((q[k] - c[k]) ** 2 for k in range(3)))
                self.fused.append((self.names[i], d))
                return i
        self.coords.append([float(c[0]), float(c[1]), float(c[2])])
        self.names.append("N%d" % len(self.coords))
        return len(self.coords) - 1


def _proyeccion(p, a, b):
    """Proyeccion ortogonal de p sobre la recta a-b (para trocear con offset:
    el punto de corte se lleva a la directriz del pasante, que queda recto)."""
    ab = [b[i] - a[i] for i in range(3)]
    L2 = sum(c * c for c in ab) or 1.0
    t = sum((p[i] - a[i]) * ab[i] for i in range(3)) / L2
    return [a[i] + t * ab[i] for i in range(3)]


def _punto_en_segmento(p, a, b, tol):
    """True si p cae en el INTERIOR del segmento a-b (para troceo en cruces)."""
    ab = [b[i] - a[i] for i in range(3)]
    ap = [p[i] - a[i] for i in range(3)]
    L2 = sum(c * c for c in ab)
    if L2 < tol * tol:
        return False
    t = sum(ap[i] * ab[i] for i in range(3)) / L2
    marg = tol / math.sqrt(L2)
    if t <= marg or t >= 1.0 - marg:
        return False  # coincide con un extremo, no es interior
    proj = [a[i] + t * ab[i] for i in range(3)]
    d = math.sqrt(sum((p[i] - proj[i]) ** 2 for i in range(3)))
    return d <= tol


# --- Construccion del modelo neutro ----------------------------------------
def _es_vertical(p0, p1):
    dx = p1[0] - p0[0]; dy = p1[1] - p0[1]; dz = p1[2] - p0[2]
    horiz = math.sqrt(dx * dx + dy * dy)
    return abs(dz) > 1e-6 and horiz < 1e-6


def _bbox_xy(esquinas):
    xs = [c[0] for c in esquinas]; ys = [c[1] for c in esquinas]
    return min(xs), max(xs), min(ys), max(ys)


def _filtrar_desconectadas(model):
    """Elimina las barras de componentes NO CONECTADAS al subgrafo apoyado
    (elementos sueltos/sin apoyo tipicos de un export real). Conserva los
    subgrafos con >=1 nudo apoyado; documenta lo descartado en limpieza."""
    barras = model["barras"]
    nodos = model["nodos"]
    if not barras:
        return
    # union-find sobre nudos via barras
    padre = {nm: nm for nm in nodos}
    def find(a):
        while padre[a] != a:
            padre[a] = padre[padre[a]]; a = padre[a]
        return a
    def union(a, b):
        padre[find(a)] = find(b)
    for b in barras.values():
        if b["ni"] in padre and b["nj"] in padre:
            union(b["ni"], b["nj"])
    apoyados = set(find(nm) for nm, n in nodos.items() if any(n.get("apoyo", [])))
    bar_drop = [bid for bid, b in barras.items()
                if find(b["ni"]) not in apoyados]
    if not bar_drop:
        return
    nodos_usados = set()
    for bid, b in barras.items():
        if bid not in bar_drop:
            nodos_usados.add(b["ni"]); nodos_usados.add(b["nj"])
    for bid in bar_drop:
        b = barras.pop(bid)
        model["limpieza"]["elementos_filtrados"].append({
            "barra": bid, "elemento": b.get("elemento_fisico"),
            "clase_ifc": b.get("clase_ifc"),
            "motivo": "componente no conectada (sin apoyo) -> descartada"})
    for nm in [n for n in nodos if n not in nodos_usados]:
        nodos.pop(nm, None)
    model["cargas"] = [c for c in model["cargas"]
                       if c.get("barra") in barras or c.get("barra") is None]


def parse(ifc_path, snap_tol=None):
    ifc = ifcopenshell.open(ifc_path)
    scale = _length_scale(ifc)                       # unidad del IFC -> metros
    tol = snap_tol if snap_tol is not None else _snap_tol_from_ifc(ifc)
    model = {
        "unidades": {"longitud": "m", "fuerza": "N", "momento": "N*m",
                     "factor_escala_ifc": scale, "snap_tol_m": tol},
        "origen": "puente_fisico_analitico",
        "materiales": _material_props(ifc),
        "secciones": {},
        "nodos": {},
        "barras": {},
        "superficies": [],
        "cargas": [],
        "hipotesis": {"apoyos": [], "cargas": []},
        "limpieza": {"snap_tol_m": tol, "factor_escala_ifc": scale,
                     "excentricidades": [], "nudos_fusionados": 0,
                     "huecos_puenteados": [], "cruces_troceados": [],
                     "elementos_filtrados": []},
    }

    # 1) extraer elementos lineales fisicos
    elementos = []
    for cls in ("IfcColumn", "IfcBeam", "IfcMember"):
        for el in ifc.by_type(cls):
            ejes = _eje(el, scale)
            if ejes is None:
                continue
            p0, p1 = ejes
            # recuperar el eje ANALITICO (baricentrico) del eje FISICO por el
            # CardinalPoint del usage (ejes no centrados de exportadores reales)
            p0, p1, ecc, cp = _axis_recovery(el, p0, p1, scale)
            sec_name, sec_props, mat = _profile_and_material(el)
            elementos.append({
                "ifc": el, "clase": cls, "nombre": el.Name or ("E%d" % el.id()),
                "p0": p0, "p1": p1, "seccion": sec_name, "props": sec_props,
                "material": mat, "ecc": ecc, "cardinal": cp,
            })

    # registrar las clases NO estructurales presentes (se filtran por clase).
    # Solo se documenta en IFC "real-sucio" (no altera el modelo en R1-R4 limpios).
    _ESTRUCT = ("IfcColumn", "IfcBeam", "IfcMember", "IfcSlab", "IfcWall", "IfcFooting")
    try:
      if tol > TOL:
        for el in ifc.by_type("IfcElement"):
            if not el.is_a("IfcElement"):
                continue
            if any(el.is_a(c) for c in _ESTRUCT):
                continue
            model["limpieza"]["elementos_filtrados"].append({
                "nombre": el.Name or ("E%d" % el.id()), "clase_ifc": el.is_a(),
                "motivo": "clase no estructural (descartada)"})
    except Exception:
        pass

    # 2) nudos por fusion de extremos (+ troceo en cruces interiores con tolerancia)
    nod = _Nodos(tol)
    extremos = []
    for e in elementos:
        extremos.append(e["p0"]); extremos.append(e["p1"])
    puntos_corte = {id(e): [] for e in elementos}
    for e in elementos:
        for pe in extremos:
            if _punto_en_segmento(pe, e["p0"], e["p1"], tol):
                proj = _proyeccion(pe, e["p0"], e["p1"])
                puntos_corte[id(e)].append(proj)
                model["limpieza"]["cruces_troceados"].append({
                    "elemento": e["nombre"],
                    "punto": [round(c, 4) for c in proj],
                    "offset_m": round(math.sqrt(sum((pe[i]-proj[i])**2
                                       for i in range(3))), 4)})
    bar_counter = {"pilar": 0, "viga": 0}
    for e in elementos:
        tipo = "pilar" if _es_vertical(e["p0"], e["p1"]) else "viga"
        ab = [e["p1"][i] - e["p0"][i] for i in range(3)]
        L2 = sum(c * c for c in ab) or 1.0
        pts = [e["p0"], e["p1"]] + puntos_corte[id(e)]
        uniq = []
        for p in pts:
            t = sum((p[i] - e["p0"][i]) * ab[i] for i in range(3)) / L2
            if not any(abs(t - tt) < 1e-6 for tt, _ in uniq):
                uniq.append((t, p))
        uniq.sort(key=lambda x: x[0])
        if e["seccion"] and e["seccion"] not in model["secciones"] and e["props"]:
            model["secciones"][e["seccion"]] = e["props"]
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
        e["centro"] = [(e["p0"][i] + e["p1"][i]) / 2.0 for i in range(3)]
        for bn in seg_names:
            model["limpieza"]["excentricidades"].append({
                "barra": bn, "elemento": e["nombre"],
                "cardinal": e.get("cardinal"),
                "ecc_eje_fisico_analitico_m": round(e.get("ecc", 0.0), 4)})

    # 2b) SUPERFICIES fisicas (IfcSlab; en R3 IfcWall/IfcFooting).
    #     Se extrae primero el espesor del IfcMaterialLayerSet (sirve de pista para
    #     clasificar el muro fino) y despues la geometria del plano medio, que se
    #     clasifica por ORIENTACION (vertical = IfcWall extruido en +Z fino;
    #     horizontal = IfcSlab/IfcFooting).
    superficies = []
    for cls in ("IfcSlab", "IfcWall", "IfcFooting"):
        for el in ifc.by_type(cls):
            esp_layer, mat_layer = _layerset_thickness_material(el)
            geo = _superficie(el, clase=cls, espesor_layer=esp_layer)
            if geo is None:
                continue
            # para el muro vertical el espesor es el LADO FINO de la huella
            # (= Sigma LayerThickness si esta); para losa/zapata es el canto.
            if geo["orientacion"] == "vertical":
                espesor = esp_layer if esp_layer is not None else geo["espesor_lado"]
            else:
                espesor = esp_layer if esp_layer is not None else geo["espesor_geom"]
            nombre = el.Name or ("S%d" % el.id())
            superficies.append({
                "ifc": el, "clase": cls, "nombre": nombre, "geo": geo,
                "espesor": espesor, "espesor_origen":
                    ("IfcMaterialLayerSet" if esp_layer is not None else "geometria"),
                "material": mat_layer,
            })

    # 2c) CONECTIVIDAD superficie<->barras: vigas cuyo eje cae dentro/bajo el
    #     contorno en planta de la losa (proximidad en planta, como el caso 10)
    for s in superficies:
        xmin, xmax, ymin, ymax = _bbox_xy(s["geo"]["esquinas_coords"])
        margen = TOL
        vigas_asoc = []
        for e in elementos:
            if _es_vertical(e["p0"], e["p1"]):
                continue
            cx, cy = e["centro"][0], e["centro"][1]
            if (xmin - margen <= cx <= xmax + margen
                    and ymin - margen <= cy <= ymax + margen):
                vigas_asoc.extend(e.get("barras_analiticas") or [])
        s["vigas_asociadas"] = vigas_asoc

    # 3) escribir nudos con coordenadas (apoyo se rellena luego)
    for i, c in enumerate(nod.coords):
        model["nodos"][nod.names[i]] = {
            "x": c[0], "y": c[1], "z": c[2], "apoyo": [False] * 6,
        }
    # metricas del grafo: fusiones de extremos y huecos/solapes puenteados (> TOL)
    model["limpieza"]["nudos_fusionados"] = len(nod.fused)
    model["limpieza"]["huecos_puenteados"] = [
        {"nodo": nm, "salto_m": round(d, 4)} for nm, d in nod.fused if d > TOL]

    # 2d) CADENA muro<->cimiento (R3): asociar cada muro VERTICAL a la zapata
    #     HORIZONTAL que lo soporta (pie del muro sobre la huella, por proximidad
    #     en planta; analogo a pilar<->zapata por pie comun del caso 10).
    muros = [s for s in superficies if s["geo"]["orientacion"] == "vertical"]
    cimientos = [s for s in superficies
                 if s["geo"]["orientacion"] == "horizontal"
                 and s["clase"] in ("IfcFooting", "IfcSlab")]
    for mw in muros:
        xs = [c[0] for c in mw["geo"]["esquinas_coords"]]
        ys = [c[1] for c in mw["geo"]["esquinas_coords"]]
        cxw = sum(xs) / len(xs); cyw = sum(ys) / len(ys)
        z_pie = min(c[2] for c in mw["geo"]["esquinas_coords"])
        mejor = None; mejor_d = None
        for fo in cimientos:
            fx = [c[0] for c in fo["geo"]["esquinas_coords"]]
            fy = [c[1] for c in fo["geo"]["esquinas_coords"]]
            xmin, xmax = min(fx), max(fx); ymin, ymax = min(fy), max(fy)
            dentro = (xmin - TOL <= cxw <= xmax + TOL and ymin - TOL <= cyw <= ymax + TOL)
            # cota: pie del muro ~ cara superior de la zapata (z_med + canto/2)
            z_top_fo = fo["geo"]["z_med"] + fo["espesor"] / 2.0
            dz = abs(z_pie - z_top_fo)
            if dentro and (mejor is None or dz < mejor_d):
                mejor, mejor_d = fo, dz
        mw["zapata_asociada"] = mejor["nombre"] if mejor is not None else None
        if mejor is not None:
            mejor.setdefault("muros_asociados", []).append(mw["nombre"])
    for fo in cimientos:
        fo.setdefault("muros_asociados", [])

    # 2e) CARGA DE CABEZA del muro (Pset_Estructurando_CargaHipotesis: N_G/N_Q + e).
    #     El IFC fisico no trae acciones -> hipotesis del calculista. N en kN/m de
    #     faja, M = N*e por cara (M_Nm_m). Igual idea que el pilar del caso 5/7.
    for mw in muros:
        ps = _psets(mw["ifc"])
        ch = ps.get("Pset_Estructurando_CargaHipotesis", {})
        e_cab = float(ch.get("Excentricidad_cabeza_m", 0.0) or 0.0)
        arr_raw = str(ch.get("Arriostrado", "si")).strip().lower()
        arr = arr_raw in ("si", "s", "1", "true", "yes", "y")
        cabeza = []
        for caso, key in (("G", "N_G_kN_m"), ("Q", "N_Q_kN_m")):
            if ch.get(key) is not None:
                n_n_m = float(ch[key]) * 1000.0          # kN/m -> N/m
                cabeza.append({"caso": caso, "N_N_m": n_n_m, "M_Nm_m": n_n_m * e_cab})
        mw["cabeza"] = cabeza
        mw["e_cabeza_m"] = e_cab
        mw["arriostrado"] = arr

    # 3b) volcar superficies al modelo neutro (esquema estandar de laminas +
    #     campos de R3: orientacion, normal, largo, cadena muro<->cimiento, cabeza)
    for s in superficies:
        sd = {
            "nombre": s["nombre"], "clase_ifc": s["clase"],
            "esquinas_coords": s["geo"]["esquinas_coords"],
            "z_medio": s["geo"]["z_med"],
            "orientacion": s["geo"]["orientacion"],
            "normal": s["geo"]["normal"],
            "largo": s["geo"].get("largo"),
            "altura": s["geo"].get("altura"),
            "espesor": s["espesor"], "espesor_origen": s["espesor_origen"],
            "material": s["material"], "malla": 0.5,
            "apoyo": "", "cargas": [],
            "vigas_asociadas": s.get("vigas_asociadas", []),
            "muros_asociados": s.get("muros_asociados", []),
            "zapata_asociada": s.get("zapata_asociada"),
        }
        if s["geo"]["orientacion"] == "vertical":
            sd["cabeza"] = s.get("cabeza", [])
            sd["e_cabeza_m"] = s.get("e_cabeza_m", 0.0)
            sd["arriostrado"] = s.get("arriostrado", True)
        model["superficies"].append(sd)

    # 4) apoyos: Pset_Estructurando_ApoyoBase de los elementos (muro/zapata) ->
    #    cota base; nodos de barra (R1) reciben el apoyo biarticulado. En R3 (sin
    #    barras) el apoyo/lecho se documenta como hipotesis y lo aplica el solver.
    cotas_apoyo = []
    tipo_apoyo = "biarticulado"
    for s in superficies:
        ps = _psets(s["ifc"])
        ab = ps.get("Pset_Estructurando_ApoyoBase")
        if ab:
            cotas_apoyo.append(float(ab.get("Cota_z_m", 0.0)))
            tipo_apoyo = ab.get("Tipo", tipo_apoyo)
            model["hipotesis"]["apoyos"].append({
                "elemento": s["nombre"], "clase_ifc": s["clase"],
                "cota_z": float(ab.get("Cota_z_m", 0.0)),
                "tipo": ab.get("Tipo", tipo_apoyo),
                "ubicacion": ab.get("Ubicacion")})
    for e in elementos:
        ps = _psets(e["ifc"])
        ab = ps.get("Pset_Estructurando_ApoyoBase")
        if ab:
            cotas_apoyo.append(float(ab.get("Cota_z_m", 0.0)))
            tipo_apoyo = ab.get("Tipo", tipo_apoyo)
    if cotas_apoyo and model["nodos"]:
        cota_base = min(cotas_apoyo)
        if tipo_apoyo.lower().startswith("biarticul") or tipo_apoyo.lower() == "articulado":
            apoyo_base = [True, True, True, False, False, True]
        else:
            apoyo_base = [True, True, True, True, True, True]
        for nm, n in model["nodos"].items():
            if abs(n["z"] - cota_base) <= tol:
                n["apoyo"] = list(apoyo_base)

    # 4b) filtrar componentes NO CONECTADAS sin apoyo (elementos sueltos del
    #     export real). Solo en IFC "real-sucio" (snap_tol > TOL declarada): un IFC
    #     LIMPIO (R1-R4, tol=TOL) NO se filtra -> comportamiento identico.
    if tol > TOL:
        _filtrar_desconectadas(model)

    # 5) cargas de hipotesis: Pset_Estructurando_CargaHipotesis
    #    - SUPERFICIE losa: G/Q kN/m2 -> surf['cargas'] (R2).
    #    - MURO vertical: carga de cabeza N+e -> documentada en hipotesis (cabeza).
    #    - BARRA (R1): carga de linea G/Q kN/m -> model['cargas'].
    surf_by_name = {sm["nombre"]: sm for sm in model["superficies"]}
    for s in superficies:
        ps = _psets(s["ifc"])
        ch = ps.get("Pset_Estructurando_CargaHipotesis")
        if not ch:
            continue
        direccion = ch.get("Direccion", "-Z")
        signo = -1.0 if str(direccion).strip().upper().startswith("-Z") else 1.0
        sm = surf_by_name.get(s["nombre"])
        for caso, key in (("G", "G_kN_m2"), ("Q", "Q_kN_m2")):
            if ch.get(key) is not None:
                qz = signo * float(ch[key]) * 1000.0
                sm["cargas"].append({"caso": caso, "qz": qz})
                model["hipotesis"]["cargas"].append({
                    "superficie": s["nombre"], "caso": caso,
                    "q_kN_m2": float(ch[key]), "direccion": direccion,
                    "tipo": "superficie", "descripcion": ch.get("Descripcion")})
        for caso, key in (("G", "N_G_kN_m"), ("Q", "N_Q_kN_m")):
            if ch.get(key) is not None:
                model["hipotesis"]["cargas"].append({
                    "muro": s["nombre"], "caso": caso, "N_kN_m": float(ch[key]),
                    "excentricidad_m": float(ch.get("Excentricidad_cabeza_m", 0.0) or 0.0),
                    "M_kNm_m": float(ch[key]) * float(ch.get("Excentricidad_cabeza_m", 0.0) or 0.0),
                    "direccion": direccion, "tipo": "cabeza_muro",
                    "descripcion": ch.get("Descripcion")})
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
                qz = signo * float(ch[key]) * 1000.0
                model["cargas"].append({
                    "caso": caso, "barra": barra, "direccion": "GZ", "qz": qz})
                model["hipotesis"]["cargas"].append({
                    "barra": barra, "elemento_fisico": e["nombre"], "caso": caso,
                    "q_kN_m": float(ch[key]), "direccion": direccion,
                    "tipo": "linea", "descripcion": ch.get("Descripcion")})

    # 6) respaldo de propiedades de material por defecto (acero) si falta E
    for mname, mp in list(model["materiales"].items()):
        if mp.get("E") is None and mname in _MAT_DEFECTO:
            model["materiales"][mname] = dict(_MAT_DEFECTO[mname])
    for b in model["barras"].values():
        mn = b["material"]
        if mn and mn not in model["materiales"]:
            model["materiales"][mn] = dict(_MAT_DEFECTO.get(mn, _MAT_DEFECTO["S275"]))

    return model


if __name__ == "__main__":
    ifc_path = sys.argv[1] if len(sys.argv) > 1 else "caso-R3.ifc"
    out_path = sys.argv[2] if len(sys.argv) > 2 else "modelo_neutro.json"
    model = parse(ifc_path)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as fh:
        json.dump(model, fh, indent=2, ensure_ascii=False)
    print("Puente fisico->analitico:", out_path)
    print("  nodos=%d  barras=%d  superficies=%d  cargas=%d" % (
        len(model["nodos"]), len(model["barras"]),
        len(model["superficies"]), len(model["cargas"])))
    lp = model.get("limpieza", {})
    print("  [limpieza] escala_ifc=%s  snap_tol=%.3f m  nudos_fusionados=%d" % (
        lp.get("factor_escala_ifc"), lp.get("snap_tol_m", 0.0),
        lp.get("nudos_fusionados", 0)))
    print("  [limpieza] huecos_puenteados=%d  cruces_troceados=%d  filtrados=%d" % (
        len(lp.get("huecos_puenteados", [])), len(lp.get("cruces_troceados", [])),
        len(lp.get("elementos_filtrados", []))))
    for ex in lp.get("excentricidades", []):
        if ex.get("ecc_eje_fisico_analitico_m", 0.0) > 0:
            print("    ecc %s (CP=%s): %.4f m" % (
                ex["barra"], ex.get("cardinal"), ex["ecc_eje_fisico_analitico_m"]))
    for s in model["superficies"]:
        zs = [c[2] for c in s["esquinas_coords"]]
        print("  '%s' [%s] %s t=%.3f m (%s) mat=%s Z[%.2f,%.2f] largo=%s zap=%s muros=%s" % (
            s["nombre"], s["clase_ifc"], s.get("orientacion"), s["espesor"],
            s["espesor_origen"], s["material"], min(zs), max(zs),
            s.get("largo"), s.get("zapata_asociada"), s.get("muros_asociados")))
