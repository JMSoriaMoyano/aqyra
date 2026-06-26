"""
Generador de 3 IFC CO-LOCALIZADOS para la federacion multi-disciplina del Visor v0.6.
Los tres comparten:
  - mismo sistema de coordenadas mundo (WCS en 0,0,0)
  - misma georreferencia (IfcProjectedCRS EPSG:25830 + IfcMapConversion identicos)
  - el mismo emplazamiento fisico (un pequeno edificio y su obra lineal anexa)
Y TODOS llevan geometria Body (IfcExtrudedAreaSolid) -> teselan en web-ifc/fragments.

  A) estructura.ifc  -> portico 6x5 m, 4 pilares HEB240 + forjado losa + 4 zapatas
  B) mep.ifc         -> red MEP: bajante + 2 ramales horizontales (tuberia circular)
                        + conducto rectangular de clima, dentro del mismo edificio
  C) lineal.ifc      -> obra lineal anexa: firme de viario (losa) + colector enterrado
                        (tuberia) + bordillo, paralelos al edificio en X negativo

Coordenadas comunes (m), planta XY, Z vertical:
  edificio ocupa  X[0..6]  Y[0..5]  Z[-0.6 .. 3.6]
  vial    ocupa   X[-8..-2] (firme), colector en X=-5, bordillo en X=-2
"""
import sys, os, math
sys.path.insert(0, "/tmp/pylibs")
import ifcopenshell
import ifcopenshell.guid

OUTDIR = sys.argv[1] if len(sys.argv) > 1 else "."
os.makedirs(OUTDIR, exist_ok=True)

# --- Georreferencia comun a las 3 disciplinas (ETRS89 / UTM 30N, ejemplo Madrid) ---
CRS_NAME   = "EPSG:25830"
CRS_DESC   = "ETRS89 / UTM zone 30N"
GEO_E      = 440000.0      # Eastings (m)
GEO_N      = 4474000.0     # Northings (m)
GEO_H      = 650.0         # Orthogonal height (m)
GEO_XAXABS = 1.0           # rotacion 0 -> ejes alineados
GEO_XAXORD = 0.0
GEO_SCALE  = 1.0

# perfiles de acero
HEB240 = dict(name="HEB 240", b=0.240, h=0.240, tw=0.010, tf=0.017, r=0.021)


def build_common(f):
    guid = ifcopenshell.guid.new
    length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
    force  = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
    ua = f.create_entity("IfcUnitAssignment", Units=[length, force])

    def pt(c):   return f.create_entity("IfcCartesianPoint", Coordinates=tuple(float(x) for x in c))
    def dirn(v): return f.create_entity("IfcDirection", DirectionRatios=tuple(float(x) for x in v))
    def a2p3d(loc, axis=None, ref=None):
        kw = {"Location": pt(loc)}
        if axis is not None: kw["Axis"] = dirn(axis)
        if ref  is not None: kw["RefDirection"] = dirn(ref)
        return f.create_entity("IfcAxis2Placement3D", **kw)

    ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                          CoordinateSpaceDimension=3, Precision=1e-5,
                          WorldCoordinateSystem=a2p3d((0., 0., 0.)),
                          TrueNorth=dirn((0., 1., 0.)))
    body = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                           ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")
    return guid, pt, dirn, a2p3d, ctx, body, ua


def georef(f, ctx):
    """IfcProjectedCRS + IfcMapConversion identicos en los 3 modelos."""
    crs = f.create_entity("IfcProjectedCRS", Name=CRS_NAME, Description=CRS_DESC,
                          GeodeticDatum="ETRS89", VerticalDatum="EVRF2007",
                          MapProjection="UTM", MapZone="30N")
    f.create_entity("IfcMapConversion", SourceCRS=ctx, TargetCRS=crs,
                    Eastings=GEO_E, Northings=GEO_N, OrthogonalHeight=GEO_H,
                    XAxisAbscissa=GEO_XAXABS, XAxisOrdinate=GEO_XAXORD, Scale=GEO_SCALE)
    return crs


def lp(f, rel_to, a2p):
    return f.create_entity("IfcLocalPlacement", PlacementRelTo=rel_to, RelativePlacement=a2p)


def rect_profile(f, name, bx, ly, cx=0.0, cy=0.0):
    return f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=name,
        Position=f.create_entity("IfcAxis2Placement2D", Location=f.create_entity("IfcCartesianPoint", Coordinates=(cx, cy))),
        XDim=bx, YDim=ly)


def circ_profile(f, name, r, cx=0.0, cy=0.0):
    return f.create_entity("IfcCircleProfileDef", ProfileType="AREA", ProfileName=name,
        Position=f.create_entity("IfcAxis2Placement2D", Location=f.create_entity("IfcCartesianPoint", Coordinates=(cx, cy))),
        Radius=r)


def ishape(f, P):
    return f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
        Position=f.create_entity("IfcAxis2Placement2D", Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.))),
        OverallWidth=P["b"], OverallDepth=P["h"], WebThickness=P["tw"], FlangeThickness=P["tf"], FilletRadius=P["r"])


def extruded(f, body, a2p3d, profile, p0, depth, axis=None, ref=None):
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=profile,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)), Depth=depth)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    return f.create_entity("IfcProductDefinitionShape", Representations=[shape])


def prop(f, name, val):
    if isinstance(val, str):
        nv = f.create_entity("IfcText", wrappedValue=val)
    elif isinstance(val, bool):
        nv = f.create_entity("IfcBoolean", wrappedValue=val)
    else:
        nv = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nv)


def pset_for(f, guid, obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(f, k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(), RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def spatial(f, guid, lp, a2p3d, site_name, bld_name, storeys):
    """Crea IfcProject->Site->Building->Storeys. Devuelve (project, site, building, [(storey, placement)...])"""
    site_pl = lp(f, None, a2p3d((0., 0., 0.)))
    site = f.create_entity("IfcSite", GlobalId=guid(), Name=site_name, ObjectPlacement=site_pl, CompositionType="ELEMENT")
    bld_pl = lp(f, site_pl, a2p3d((0., 0., 0.)))
    bld = f.create_entity("IfcBuilding", GlobalId=guid(), Name=bld_name, ObjectPlacement=bld_pl, CompositionType="ELEMENT")
    sts = []
    for nm, elev in storeys:
        pl = lp(f, bld_pl, a2p3d((0., 0., 0.)))
        s = f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name=nm, ObjectPlacement=pl, CompositionType="ELEMENT", Elevation=float(elev))
        sts.append((s, pl))
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[bld])
    return site, bld, site_pl, bld_pl, sts


# =====================================================================
# A) ESTRUCTURA
# =====================================================================
def gen_estructura(path):
    f = ifcopenshell.file(schema="IFC4")
    guid, pt, dirn, a2p3d, ctx, body, ua = build_common(f)
    project = f.create_entity("IfcProject", GlobalId=guid(), Name="Federacion - ESTRUCTURA (edificio)",
                              UnitsInContext=ua, RepresentationContexts=[ctx])
    georef(f, ctx)
    site, bld, site_pl, bld_pl, sts = spatial(f, guid, lp, a2p3d, "Parcela comun", "Edificio", [("Cimentacion", -0.6), ("Planta Baja", 0.0), ("Cubierta", 3.5)])
    (sto_cim, plc_cim), (sto_baja, plc_baja), (sto_cub, plc_cub) = sts
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=bld, RelatedObjects=[sto_cim, sto_baja, sto_cub])

    cols, foots = [], []
    bay = [(0.0, 0.0), (6.0, 0.0), (0.0, 5.0), (6.0, 5.0)]
    H = 3.5
    for i, (x, y) in enumerate(bay, 1):
        # pilar HEB240 z 0..H
        pds = extruded(f, body, a2p3d, ishape(f, HEB240), (0,0,0), H)
        pl = lp(f, plc_baja, a2p3d((x, y, 0.0), axis=(0., 0., 1.), ref=(1., 0., 0.)))
        c = f.create_entity("IfcColumn", GlobalId=guid(), Name="Pilar_%d" % i, ObjectPlacement=pl, Representation=pds, PredefinedType="COLUMN")
        cols.append(c)
        # zapata 1.5x1.5x0.5 centrada en (x,y), base z=-0.6
        pdz = extruded(f, body, a2p3d, rect_profile(f, "Zapata_%d" % i, 1.5, 1.5, 0.75, 0.75), (0,0,0), 0.5)
        plz = lp(f, plc_cim, a2p3d((x - 0.75, y - 0.75, -0.6)))
        z = f.create_entity("IfcFooting", GlobalId=guid(), Name="Zapata_%d" % i, ObjectPlacement=plz, Representation=pdz, PredefinedType="PAD_FOOTING")
        foots.append(z)
    # vigas perimetrales (rect simplificado) z=H
    beams = []
    edges = [((0,0),(6,0)), ((0,5),(6,5)), ((0,0),(0,5)), ((6,0),(6,5))]
    for j, ((x0,y0),(x1,y1)) in enumerate(edges, 1):
        v = (x1-x0, y1-y0, 0.0); L = math.hypot(v[0], v[1]); ax = (v[0]/L, v[1]/L, 0.0)
        pdb = extruded(f, body, a2p3d, rect_profile(f, "Viga_%d" % j, 0.12, 0.30, 0.0, 0.15), (0,0,0), L)
        plb = lp(f, plc_cub, a2p3d((x0, y0, H), axis=ax, ref=(0.,0.,1.)))
        b = f.create_entity("IfcBeam", GlobalId=guid(), Name="Viga_%d" % j, ObjectPlacement=plb, Representation=pdb, PredefinedType="BEAM")
        beams.append(b)
    # forjado losa 6x5 t=0.25 a z=H
    pdl = extruded(f, body, a2p3d, rect_profile(f, "Losa", 6.4, 5.4, 3.2, 2.7), (0,0,0), 0.25)
    pll = lp(f, plc_cub, a2p3d((-0.2, -0.2, H)))
    losa = f.create_entity("IfcSlab", GlobalId=guid(), Name="Forjado_cubierta", ObjectPlacement=pll, Representation=pdl, PredefinedType="FLOOR")

    pset_for(f, guid, bld, "Pset_Estructurando_Disciplina", {"Disciplina": "estructura", "Norma": "EC2+EC3", "Modelo": "estructura"})
    pset_for(f, guid, losa, "Pset_Estructurando_Forjado", {"Canto_m": 0.25, "Material": "C30/37"})

    f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=sto_cim, RelatedElements=foots)
    f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=sto_baja, RelatedElements=cols)
    f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=sto_cub, RelatedElements=beams + [losa])
    f.write(path)
    return f


# =====================================================================
# B) MEP (instalaciones)
# =====================================================================
def gen_mep(path):
    f = ifcopenshell.file(schema="IFC4")
    guid, pt, dirn, a2p3d, ctx, body, ua = build_common(f)
    project = f.create_entity("IfcProject", GlobalId=guid(), Name="Federacion - MEP (instalaciones)",
                              UnitsInContext=ua, RepresentationContexts=[ctx])
    georef(f, ctx)
    site, bld, site_pl, bld_pl, sts = spatial(f, guid, lp, a2p3d, "Parcela comun", "Edificio", [("Instalaciones", 0.0)])
    (sto_mep, plc_mep), = sts
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=bld, RelatedObjects=[sto_mep])

    elems = []

    def pipe(name, p0, p1, r, cls="IfcPipeSegment", ptype="RIGIDSEGMENT"):
        v = (p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]); L = math.sqrt(sum(c*c for c in v)); ax = tuple(c/L for c in v)
        ref = (0.,0.,1.) if abs(ax[2]) < 0.9 else (1.,0.,0.)
        pds = extruded(f, body, a2p3d, circ_profile(f, name+"_DN", r), (0,0,0), L)
        pl = lp(f, plc_mep, a2p3d(p0, axis=ax, ref=ref))
        e = f.create_entity(cls, GlobalId=guid(), Name=name, ObjectPlacement=pl, Representation=pds, PredefinedType=ptype)
        elems.append(e); return e

    def duct(name, p0, p1, w, h):
        v = (p1[0]-p0[0], p1[1]-p0[1], p1[2]-p0[2]); L = math.sqrt(sum(c*c for c in v)); ax = tuple(c/L for c in v)
        ref = (0.,0.,1.) if abs(ax[2]) < 0.9 else (1.,0.,0.)
        pds = extruded(f, body, a2p3d, rect_profile(f, name+"_sec", w, h, 0.0, 0.0), (0,0,0), L)
        pl = lp(f, plc_mep, a2p3d(p0, axis=ax, ref=ref))
        e = f.create_entity("IfcDuctSegment", GlobalId=guid(), Name=name, ObjectPlacement=pl, Representation=pds, PredefinedType="RIGIDSEGMENT")
        elems.append(e); return e

    # bajante PCI vertical en esquina del edificio (x=0.3,y=0.3) z 0..3.2
    pipe("Bajante_PCI", (0.3, 0.3, 0.0), (0.3, 0.3, 3.2), 0.04)
    # ramal horizontal bajo cubierta a z=3.1, recorre el edificio en X
    pipe("Ramal_PCI_1", (0.3, 0.3, 3.1), (5.7, 0.3, 3.1), 0.032)
    # ramal en Y
    pipe("Ramal_PCI_2", (0.3, 0.3, 3.1), (0.3, 4.7, 3.1), 0.032)
    # montante de fontaneria (otra esquina)
    pipe("Montante_AF", (5.7, 4.7, 0.0), (5.7, 4.7, 3.0), 0.025)
    # conducto de clima rectangular bajo cubierta a z=2.9
    duct("Conducto_clima", (0.5, 2.5, 2.9), (5.5, 2.5, 2.9), 0.40, 0.25)

    pset_for(f, guid, bld, "Pset_Estructurando_Disciplina", {"Disciplina": "MEP", "Sistema": "PCI+fontaneria+clima", "Modelo": "mep"})
    f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=sto_mep, RelatedElements=elems)
    f.write(path)
    return f


# =====================================================================
# C) OBRA LINEAL (viario anexo)
# =====================================================================
def gen_lineal(path):
    f = ifcopenshell.file(schema="IFC4")
    guid, pt, dirn, a2p3d, ctx, body, ua = build_common(f)
    project = f.create_entity("IfcProject", GlobalId=guid(), Name="Federacion - OBRA LINEAL (viario anexo)",
                              UnitsInContext=ua, RepresentationContexts=[ctx])
    georef(f, ctx)
    site, bld, site_pl, bld_pl, sts = spatial(f, guid, lp, a2p3d, "Parcela comun", "Vial anexo", [("Plataforma", 0.0)])
    (sto_via, plc_via), = sts
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
    f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=bld, RelatedObjects=[sto_via])

    elems = []
    # firme del vial: losa 6 m ancho (X -8..-2) x 12 m largo (Y -2..10), e=0.30, cara sup z=0
    pdf = extruded(f, body, a2p3d, rect_profile(f, "Firme_sec", 6.0, 12.0, 3.0, 6.0), (0,0,0), 0.30)
    plf = lp(f, plc_via, a2p3d((-8.0, -2.0, -0.30)))
    firme = f.create_entity("IfcSlab", GlobalId=guid(), Name="Firme_viario", ObjectPlacement=plf, Representation=pdf, PredefinedType="BASESLAB")
    elems.append(firme)
    # bordillo a x=-2 (borde con el edificio), 0.15x0.20 a lo largo de Y
    pdb = extruded(f, body, a2p3d, rect_profile(f, "Bordillo_sec", 0.15, 12.0, 0.075, 6.0), (0,0,0), 0.20)
    plb = lp(f, plc_via, a2p3d((-2.15, -2.0, 0.0)))
    bordillo = f.create_entity("IfcBuildingElementProxy", GlobalId=guid(), Name="Bordillo", ObjectPlacement=plb, Representation=pdb)
    elems.append(bordillo)
    # colector enterrado: tuberia DN400 a lo largo de Y, eje x=-5, z=-1.0
    L = 12.0
    pdc = extruded(f, body, a2p3d, circ_profile(f, "Colector_DN400", 0.20), (0,0,0), L)
    plc = lp(f, plc_via, a2p3d((-5.0, -2.0, -1.0), axis=(0.,1.,0.), ref=(1.,0.,0.)))
    colector = f.create_entity("IfcPipeSegment", GlobalId=guid(), Name="Colector_pluviales", ObjectPlacement=plc, Representation=pdc, PredefinedType="CULVERT")
    elems.append(colector)
    # 2 pozos de registro (cilindros) sobre el colector
    for k, yy in enumerate((0.0, 8.0), 1):
        pdp = extruded(f, body, a2p3d, circ_profile(f, "Pozo_%d" % k, 0.5), (0,0,0), 1.2)
        plp = lp(f, plc_via, a2p3d((-5.0, yy, -1.2)))
        pozo = f.create_entity("IfcBuildingElementProxy", GlobalId=guid(), Name="Pozo_registro_%d" % k, ObjectPlacement=plp, Representation=pdp)
        elems.append(pozo)

    pset_for(f, guid, bld, "Pset_Estructurando_Disciplina", {"Disciplina": "lineal", "Tipo": "viario+saneamiento", "Modelo": "lineal"})
    pset_for(f, guid, firme, "Pset_Estructurando_Firme", {"Espesor_m": 0.30, "Ancho_m": 6.0, "Tipo": "mezcla_bituminosa"})
    f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(), RelatingStructure=sto_via, RelatedElements=elems)
    f.write(path)
    return f


def report(path):
    g = ifcopenshell.open(path)
    nsolid = len(g.by_type("IfcExtrudedAreaSolid"))
    nmap = len(g.by_type("IfcMapConversion"))
    prods = [e for e in g.by_type("IfcProduct") if getattr(e, "Representation", None)]
    return "%s: schema=%s solids=%d mapconv=%d productos_con_geom=%d" % (
        os.path.basename(path), g.schema, nsolid, nmap, len(prods))


if __name__ == "__main__":
    pe = os.path.join(OUTDIR, "estructura.ifc")
    pm = os.path.join(OUTDIR, "mep.ifc")
    pl_ = os.path.join(OUTDIR, "lineal.ifc")
    gen_estructura(pe)
    gen_mep(pm)
    gen_lineal(pl_)
    for p in (pe, pm, pl_):
        print(report(p))
       