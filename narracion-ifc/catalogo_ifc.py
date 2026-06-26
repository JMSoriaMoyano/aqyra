#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
catalogo_ifc.py  --  Catálogo data-driven de elementos IFC (Ruta 1, v0.4)

Deriva del ESQUEMA IFC4X3 el repertorio completo de subtipos concretos de
IfcElement y, por clase: grupo, bsdd_uri, predefined_types, psets_estandar,
arquetipo. Crea instancias enriquecidas (geometría + atributos + Psets + URI).

v0.4: GEOMETRÍA REALISTA para familias estructurales y de cierre
  - IfcBeam / IfcMember : perfil en I (doble T), tabla IPE/HEB, tumbado por su eje
  - IfcColumn          : rectangular o circular (param forma/d/seccion)
  - IfcFooting         : zapata (zapata pad + pedestal)
  - IfcDoor            : marco (jambas + dintel) + hoja
  - IfcWindow          : marco perimetral + vidrio
Las demás clases mantienen su arquetipo (losa/viga/cilindro/caja).
"""
import ifcopenshell
from ifcopenshell.api import run
import ifcopenshell.util.pset as _up
from functools import lru_cache

SCHEMA = "IFC4X3"
BSDD_BASE = "https://identifier.buildingsmart.org/uri/buildingsmart/ifc/4.3/class/"
GRUPOS = ["IfcBuiltElement", "IfcDistributionElement", "IfcElementAssembly",
          "IfcElementComponent", "IfcFeatureElement", "IfcFurnishingElement",
          "IfcGeographicElement", "IfcGeotechnicalElement", "IfcTransportElement",
          "IfcVirtualElement", "IfcCivilElement", "IfcVehicle"]

_sch = ifcopenshell.ifcopenshell_wrapper.schema_by_name(SCHEMA)
_pq = _up.PsetQto(SCHEMA)

# ---- arquetipos geométricos (para las clases SIN builder realista) ----------
_LOSA = {"IfcSlab","IfcPlate","IfcCovering","IfcRoof","IfcPavement","IfcCourse",
         "IfcShadingDevice","IfcCurtainWall","IfcReinforcingMesh","IfcEarthworksFill",
         "IfcReinforcedSoil","IfcWall","IfcWallStandardCase","IfcRailing","IfcGeoslice"}
_VIGA = {"IfcKerb","IfcRail","IfcTrackElement","IfcPipeSegment","IfcDuctSegment",
         "IfcCableSegment","IfcCableCarrierSegment","IfcFlowSegment","IfcReinforcingBar",
         "IfcTendon","IfcTendonConduit","IfcNavigationElement"}
_CIL  = {"IfcPile","IfcChimney","IfcTank","IfcBorehole","IfcCaissonFoundation","IfcBearing",
         "IfcDeepFoundation","IfcMooringDevice","IfcGeotechnicalStratum","IfcGeomodel"}

def arquetipo(clase):
    if clase in REALISTAS: return "realista"
    if clase in _LOSA: return "losa"
    if clase in _VIGA: return "viga"
    if clase in _CIL:  return "cilindro"
    return "caja"

_DIMS = {"losa": (2.0, 1.4, 0.20), "viga": (2.6, 0.30, 0.50),
         "cilindro": (0.35, 0.35, 2.0), "caja": (1.2, 1.2, 1.5)}

# ---- enumeración del esquema ------------------------------------------------
@lru_cache(maxsize=None)
def concretos(nombre):
    try: d = _sch.declaration_by_name(nombre)
    except Exception: return ()
    out = []
    def rec(decl):
        if not decl.is_abstract(): out.append(decl.name())
        for s in decl.subtypes(): rec(s)
    rec(d); return tuple(sorted(set(out)))

@lru_cache(maxsize=None)
def grupo_de(clase):
    for g in GRUPOS:
        if clase in concretos(g): return g
    return "IfcElement"

def bsdd_uri(clase): return BSDD_BASE + clase

@lru_cache(maxsize=None)
def predefined_types(clase):
    try: d = _sch.declaration_by_name(clase)
    except Exception: return ()
    for a in d.all_attributes():
        if a.name() == "PredefinedType":
            try: return tuple(a.type_of_attribute().declared_type().enumeration_items())
            except Exception: return ()
    return ()

@lru_cache(maxsize=None)
def psets_estandar(clase):
    try: aplicables = [p.Name for p in _pq.get_applicable(clase)]
    except Exception: aplicables = []
    elegidos = [n for n in aplicables if n.startswith("Pset_") and n.endswith("Common")]
    if not elegidos:
        elegidos = [n for n in aplicables if n.startswith("Pset_")][:1]
    out = {}
    for nm in elegidos:
        tmpl = _pq.get_by_name(nm)
        if not tmpl: continue
        props = {}
        for pt in getattr(tmpl, "HasPropertyTemplates", []) or []:
            if getattr(pt, "TemplateType", None) != "P_SINGLEVALUE": continue
            props[pt.Name] = _default(getattr(pt, "PrimaryMeasureType", None))
        if props: out[nm] = tuple(props.items())
    return tuple(out.items())

def _psets_dict(clase):
    return {k: dict(v) for k, v in psets_estandar(clase)}

def _default(measure):
    m = (measure or "").lower()
    if "boolean" in m or "logical" in m: return False
    if "integer" in m or "count" in m: return 0
    if any(k in m for k in ("length","area","volume","measure","angle","ratio","power",
                            "thermal","number","mass","time","force","pressure","frequency")):
        return 0.0
    return ""

# ---- catálogo completo ------------------------------------------------------
def construir_catalogo():
    cat = {}
    for clase in concretos("IfcElement"):
        cat[clase] = {
            "grupo": grupo_de(clase),
            "bsdd_uri": bsdd_uri(clase),
            "arquetipo": arquetipo(clase),
            "geometria": "realista" if clase in REALISTAS else "arquetipo",
            "predefined_types": list(predefined_types(clase)),
            "psets_estandar": list(_psets_dict(clase).keys()),
        }
    return cat

# ---- helpers de geometría ---------------------------------------------------
def _pt(m, c): return m.create_entity("IfcCartesianPoint", Coordinates=[float(x) for x in c])
def _dir(m, r): return m.create_entity("IfcDirection", DirectionRatios=[float(x) for x in r])
def _pos3(m, o=(0.,0.,0.)): return m.create_entity("IfcAxis2Placement3D", Location=_pt(m,o))
def _pos2(m, o=(0.,0.)): return m.create_entity("IfcAxis2Placement2D", Location=_pt(m,o))

def _place(m, o=(0.,0.,0.), axis=(0.,0.,1.), refdir=(1.,0.,0.)):
    return m.create_entity("IfcLocalPlacement",
        RelativePlacement=m.create_entity("IfcAxis2Placement3D",
            Location=_pt(m,o), Axis=_dir(m,axis), RefDirection=_dir(m,refdir)))

def _rect(m, sx, sy):
    return m.create_entity("IfcRectangleProfileDef", ProfileType="AREA", Position=_pos2(m), XDim=float(sx), YDim=float(sy))

def _circ(m, r):
    return m.create_entity("IfcCircleProfileDef", ProfileType="AREA", Position=_pos2(m), Radius=float(r))

def _ishape(m, b, h, tw, tf):
    return m.create_entity("IfcIShapeProfileDef", ProfileType="AREA", Position=_pos2(m),
        OverallWidth=float(b), OverallDepth=float(h), WebThickness=float(tw), FlangeThickness=float(tf))

def _box(m, sx, sy, sz, c=(0.,0.,0.)):
    """Caja: rectángulo (sx×sy) centrado en (cx,cy), extruido +Z desde cz una altura sz."""
    return m.create_entity("IfcExtrudedAreaSolid", SweptArea=_rect(m, sx, sy),
        Position=_pos3(m, c), ExtrudedDirection=_dir(m,(0.,0.,1.)), Depth=float(sz))

def _extr(m, profile, depth, c=(0.,0.,0.)):
    return m.create_entity("IfcExtrudedAreaSolid", SweptArea=profile, Position=_pos3(m, c),
        ExtrudedDirection=_dir(m,(0.,0.,1.)), Depth=float(depth))

def _shape(m, ctx, items):
    rep = m.create_entity("IfcShapeRepresentation", ContextOfItems=ctx, RepresentationIdentifier="Body",
        RepresentationType="SweptSolid", Items=items)
    return m.create_entity("IfcProductDefinitionShape", Representations=[rep])

# ---- tabla de perfiles I (m): (b, h, tw, tf) --------------------------------
_PERFILES = {
    "IPE200": (0.100,0.200,0.0056,0.0085), "IPE300": (0.150,0.300,0.0071,0.0107),
    "IPE400": (0.180,0.400,0.0086,0.0135), "IPE500": (0.200,0.500,0.0102,0.0160),
    "HEB200": (0.200,0.200,0.0090,0.0150), "HEB300": (0.300,0.300,0.0110,0.0190),
}

# ---- builders realistas: devuelven (items, axis, refdir) --------------------
def _b_viga_i(m, p):
    perfil = (p.get("perfil") or "IPE300").upper()
    b,h,tw,tf = _PERFILES.get(perfil, _PERFILES["IPE300"])
    L = float(p.get("longitud", 2.6))
    solid = _extr(m, _ishape(m, b,h,tw,tf), L)        # extruye +localZ -> se tumba con la placement
    return [solid], (1.,0.,0.), (0.,1.,0.)            # eje X = longitud; alma vertical

def _b_pilar(m, p):
    H = float(p.get("altura", 3.0))
    if (p.get("forma") or "rect").lower().startswith("circ"):
        r = float(p.get("d", p.get("diametro", 0.40))) / 2.0
        return [_extr(m, _circ(m, r), H)], (0.,0.,1.), (1.,0.,0.)
    sec = p.get("seccion", [0.40, 0.40]); bx, by = sec
    return [_box(m, bx, by, H)], (0.,0.,1.), (1.,0.,0.)

def _b_zapata(m, p):
    dims = p.get("dims", [1.5, 1.5, 0.40]); Lx, Ly, Hp = dims
    ped = p.get("pedestal", [0.40, 0.40, 0.40]); px, py, ph = ped
    pad = _box(m, Lx, Ly, Hp, c=(0.,0.,0.))
    pedestal = _box(m, px, py, ph, c=(0.,0., Hp))
    return [pad, pedestal], (0.,0.,1.), (1.,0.,0.)

def _b_puerta(m, p):
    W = float(p.get("ancho", 0.90)); H = float(p.get("alto", 2.10))
    t = float(p.get("espesor_muro", 0.10)); fw = float(p.get("marco", 0.05))
    jL = _box(m, fw, t, H, c=(-(W-fw)/2, 0., 0.))
    jR = _box(m, fw, t, H, c=( (W-fw)/2, 0., 0.))
    din = _box(m, W, t, fw, c=(0., 0., H-fw))
    hoja = _box(m, W-2*fw, 0.045, H-fw, c=(0., 0., 0.))
    return [jL, jR, din, hoja], (0.,0.,1.), (1.,0.,0.)

def _b_ventana(m, p):
    W = float(p.get("ancho", 1.20)); H = float(p.get("alto", 1.20))
    t = float(p.get("espesor_muro", 0.10)); fw = float(p.get("marco", 0.05))
    sill = _box(m, W, t, fw, c=(0.,0.,0.))
    head = _box(m, W, t, fw, c=(0.,0., H-fw))
    jL = _box(m, fw, t, H, c=(-(W-fw)/2, 0., 0.))
    jR = _box(m, fw, t, H, c=( (W-fw)/2, 0., 0.))
    vidrio = _box(m, W-2*fw, 0.02, H-2*fw, c=(0.,0., fw))
    return [sill, head, jL, jR, vidrio], (0.,0.,1.), (1.,0.,0.)

REALISTAS = {
    "IfcBeam": _b_viga_i, "IfcMember": _b_viga_i,
    "IfcColumn": _b_pilar, "IfcFooting": _b_zapata,
    "IfcDoor": _b_puerta, "IfcWindow": _b_ventana,
}

def _body_arquetipo(m, ctx, clase, name):
    a = arquetipo(clase); w, d, h = _DIMS.get(a, _DIMS["caja"])
    if a == "cilindro":
        solid = _extr(m, _circ(m, w), h)
    else:
        solid = _box(m, w, d, h)
    return _shape(m, ctx, [solid])

# ---- creación de un elemento enriquecido ------------------------------------
def crear_elemento(m, body_ctx, storey, clase, name, origin=(0.,0.,0.),
                   predefined=None, material=None, classif_cache=None, params=None):
    params = params or {}
    el = run("root.create_entity", m, ifc_class=clase, name=name)
    pts = predefined_types(clase)
    if pts:
        val = predefined if predefined in pts else next((p for p in pts if p not in ("USERDEFINED","NOTDEFINED")), None)
        if val:
            try: el.PredefinedType = val
            except Exception: pass
    # geometría
    try:
        if clase in REALISTAS:
            items, axis, refdir = REALISTAS[clase](m, params)
            el.ObjectPlacement = _place(m, origin, axis, refdir)
            el.Representation = _shape(m, body_ctx, items)
        else:
            el.ObjectPlacement = _place(m, origin)
            el.Representation = _body_arquetipo(m, body_ctx, clase, name)
    except Exception:
        el.ObjectPlacement = _place(m, origin)
    if storey is not None:
        try: run("spatial.assign_container", m, relating_structure=storey, products=[el])
        except Exception: pass
    n_props = 0
    for psname, props in _psets_dict(clase).items():
        ps = run("pset.add_pset", m, product=el, name=psname)
        try:
            run("pset.edit_pset", m, pset=ps, properties=props); n_props += len(props)
        except Exception: pass
    if material:
        ps = run("pset.add_pset", m, product=el, name="Pset_Estructurando_Spec")
        run("pset.edit_pset", m, pset=ps, properties={"Material": material})
    if classif_cache is not None:
        c = classif_cache.get("__classif__")
        if c is None:
            c = run("classification.add_classification", m, classification="bSDD - IFC 4.3")
            classif_cache["__classif__"] = c
        try:
            ref = run("classification.add_reference", m, products=[el],
                      identification=clase, name=clase, classification=c, is_lightweight=False)
            if ref is not None: ref.Location = bsdd_uri(clase)
        except Exception: pass
    return el, n_props
