"""
CASO R2 - FORJADO FISICO REAL. Segundo caso de la DIRECCION 2 (puente IFC fisico ->
modelo analitico con SUPERFICIES). A diferencia de los casos 1-11 (IFC ORTODOXO del
dominio de ANALISIS), este es un IFC FISICO como el que entrega una herramienta BIM:

  - Estructura espacial:  IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey
  - Elementos FISICOS con GEOMETRIA Body:
      * IfcSlab x1  (losa C30/37, canto 120 mm, planta 6,0 x 4,0 m) -> IfcExtrudedAreaSolid
        barriendo el contorno en planta; material/espesor por IfcMaterialLayerSetUsage ->
        IfcMaterialLayerSet (Sigma LayerThickness)
      * IfcBeam x2  (IPE 400, S275), paralelas, luz 6,0 m, separadas 4,0 m ->
        IfcExtrudedAreaSolid del IfcIShapeProfileDef; material/seccion por
        IfcMaterialProfileSetUsage -> IfcMaterialProfileSet -> IfcMaterialProfile
  - NO hay entidades de analisis ni cargas: el modelo analitico (superficie media de la
    losa, ejes de viga, nudos, apoyos) y las HIPOTESIS de carga NO estan -> el "puente"
    debe DERIVARLOS de la GEOMETRIA. Las hipotesis se aportan como Pset.

GEOMETRIA identica al caso 2 (losa C30/37 t=120 mm sobre 2 vigas IPE 400 S275, luz 6 m,
separacion 4 m, carga de superficie G=4,5 / Q=3,0 kN/m2) para VALIDAR el puente contra
un resultado ya conocido (caso 2: m_Ed=21,15 kN.m/m; vigas IPE 400 ~26,5 %; reaccion por
extremo 63,45 kN; equilibrio 0 %).

El agente (puente fisico->analitico, ampliacion a superficies) debe:
  - leer IfcBeam (eje+seccion+material, como en R1) y IfcSlab (SUPERFICIE MEDIA de la
    geometria + ESPESOR de IfcMaterialLayerSet + material),
  - asociar la losa a las vigas que la soportan (conectividad superficie<->barras) y
    construir el modelo neutro (superficie + barras),
  - inferir APOYOS (extremos de viga, Pset) y aplicar la HIPOTESIS de carga de superficie,
  - enrutar a `laminas` (losa EC2) + `barras` (EC3) con reparto por ancho tributario
    (run_forjado) -> debe reproducir el caso 2.

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import math
import ifcopenshell
import ifcopenshell.guid

CONC = dict(name="C30/37", E=33e9, nu=0.2, rho=2500.0, G=33e9 / (2 * (1 + 0.2)), fck=30e6)
STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
IPE400 = dict(name="IPE 400", b=0.180, h=0.400, tw=0.0086, tf=0.0135, r=0.021)

# geometria = caso 2
LUZ = 6.0     # luz de las vigas (X)
SEP = 4.0     # separacion entre vigas (Y) = vano de la losa
TSLAB = 0.12  # canto de la losa
G_SUP = 4.5   # kN/m2 (incluye p.p. losa 0,12*25=3,0 + 1,5 acabados)
Q_SUP = 3.0   # kN/m2

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-R2.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new


def dirn(v):
    return f.create_entity("IfcDirection", DirectionRatios=tuple(float(x) for x in v))


def pt(c):
    return f.create_entity("IfcCartesianPoint", Coordinates=tuple(float(x) for x in c))


def a2p3d(loc, axis=None, ref=None):
    kw = {"Location": pt(loc)}
    if axis is not None:
        kw["Axis"] = dirn(axis)
    if ref is not None:
        kw["RefDirection"] = dirn(ref)
    return f.create_entity("IfcAxis2Placement3D", **kw)


def local_placement(rel_to, a2p):
    return f.create_entity("IfcLocalPlacement", PlacementRelTo=rel_to, RelativePlacement=a2p)


# ---- unidades + contextos ----
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=a2p3d((0., 0., 0.)))
body = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                       ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")
project = f.create_entity("IfcProject", GlobalId=guid(),
                          Name="Caso R2 - Forjado fisico (puente IFC->analitico, superficies)",
                          UnitsInContext=ua, RepresentationContexts=[ctx])

# ---- estructura espacial ----
site_pl = local_placement(None, a2p3d((0., 0., 0.)))
site = f.create_entity("IfcSite", GlobalId=guid(), Name="Parcela", ObjectPlacement=site_pl,
                       CompositionType="ELEMENT")
bld_pl = local_placement(site_pl, a2p3d((0., 0., 0.)))
building = f.create_entity("IfcBuilding", GlobalId=guid(), Name="Edificio R2", ObjectPlacement=bld_pl,
                           CompositionType="ELEMENT")
sto_pl = local_placement(bld_pl, a2p3d((0., 0., 0.)))
storey = f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name="Forjado nivel 0",
                         ObjectPlacement=sto_pl, CompositionType="ELEMENT", Elevation=0.0)
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[building])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=building, RelatedObjects=[storey])


def material(M, extra=None):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    pairs = [("YoungModulus", M["E"]), ("ShearModulus", M["G"]),
             ("PoissonRatio", M["nu"]), ("MassDensity", M["rho"])]
    if "fy" in M:
        pairs.append(("YieldStress", M["fy"]))
    if "fck" in M:
        pairs.append(("CompressiveStrength", M["fck"]))
    props = [f.create_entity("IfcPropertySingleValue", Name=k,
                NominalValue=f.create_entity("IfcReal", wrappedValue=float(v))) for k, v in pairs]
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m


steel = material(STEEL)
concrete = material(CONC)


def ishape(P):
    return f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.))),
                           OverallWidth=P["b"], OverallDepth=P["h"],
                           WebThickness=P["tw"], FlangeThickness=P["tf"], FilletRadius=P["r"])


def prop(name, val):
    if isinstance(val, str):
        nv = f.create_entity("IfcText", wrappedValue=val)
    else:
        nv = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nv)


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def beam(name, p0, p1, P, refdir):
    v = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in v))
    axis = [c / L for c in v]
    prof = ishape(P)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=prof,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=L)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d(p0, axis=axis, ref=refdir))
    el = f.create_entity("IfcBeam", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="BEAM")
    mp = f.create_entity("IfcMaterialProfile", Name=name + "_perfil", Material=steel, Profile=prof)
    mps = f.create_entity("IfcMaterialProfileSet", Name=P["name"], MaterialProfiles=[mp])
    usage = f.create_entity("IfcMaterialProfileSetUsage", ForProfileSet=mps, CardinalPoint=5)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[el], RelatingMaterial=usage)
    return el


def slab(name, x0, y0, bx, ly, t, origin_z):
    """Losa horizontal: contorno rectangular bx (X) x ly (Y), canto t, barrido en -Z.
    Placement con origen en (x0,y0,origin_z); rectangulo centrado por su Position 2D."""
    rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=name + "_planta",
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(bx / 2.0, ly / 2.0))),
                           XDim=bx, YDim=ly)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rect,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., -1.)), Depth=t)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d((x0, y0, origin_z)))
    el = f.create_entity("IfcSlab", GlobalId=guid(), Name=name, ObjectPlacement=pl,
                         Representation=pds, PredefinedType="FLOOR")
    # material/espesor por IfcMaterialLayerSetUsage -> IfcMaterialLayerSet
    layer = f.create_entity("IfcMaterialLayer", Material=concrete, LayerThickness=t, Name="Losa HA")
    mls = f.create_entity("IfcMaterialLayerSet", MaterialLayers=[layer], LayerSetName=name + "_capas")
    usage = f.create_entity("IfcMaterialLayerSetUsage", ForLayerSet=mls, LayerSetDirection="AXIS3",
                            DirectionSense="NEGATIVE", OffsetFromReferenceLine=0.0)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[el], RelatingMaterial=usage)
    return el


# ---- los elementos del forjado (geometria = caso 2) ----
# 2 vigas IPE 400 paralelas a lo largo de X, en y=0 y y=SEP, a cota z=0
b1 = beam("Viga_1", (0.0, 0.0, 0.0), (LUZ, 0.0, 0.0), IPE400, refdir=(0., 1., 0.))
b2 = beam("Viga_2", (0.0, SEP, 0.0), (LUZ, SEP, 0.0), IPE400, refdir=(0., 1., 0.))
# losa 6,0 x 4,0, canto 0,12, top a z=0 (mid-surface z=-0,06); offsets eje fisico<->analitico -> R5
losa = slab("Losa_forjado", 0.0, 0.0, LUZ, SEP, TSLAB, origin_z=0.0)

# ---- datos NO geometricos (no existen en un IFC fisico) -> Pset hipotesis ----
pset_for(losa, "Pset_Estructurando_CargaHipotesis",
         {"Descripcion": "carga gravitatoria de superficie sobre el forjado (servicio)",
          "G_kN_m2": G_SUP, "Q_kN_m2": Q_SUP, "Direccion": "-Z"})
for b in (b1, b2):
    pset_for(b, "Pset_Estructurando_ApoyoBase",
             {"Cota_z_m": 0.0, "Tipo": "biarticulado", "Ubicacion": "extremos_viga"})
pset_for(building, "Pset_Estructurando_ProyectoAnalisis",
         {"Norma": "EC2+EC3", "Material_losa": "C30/37", "Material_vigas": "S275",
          "Sistema": "forjado_losa_sobre_vigas",
          "Nota": "IFC fisico: derivar superficie media + espesor (IfcMaterialLayerSet) y ejes de viga (puente Direccion 2)"})

# ---- contener los elementos en la planta ----
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=storey, RelatedElements=[b1, b2, losa])

f.write(OUT)
print("IFC caso R2 (FISICO, forjado, puente IFC->analitico) escrito en:", OUT)
print("  IfcSlab x1 (C30/37 t=%.0f mm) + IfcBeam x2 (IPE 400 S275), geometria Body" % (TSLAB * 1000))
print("  Geometria = caso 2: luz %.1f m, sep %.1f m, G=%.1f / Q=%.1f kN/m2 (Pset hipotesis)" % (LUZ, SEP, G_SUP, Q_SUP))
print("  Estructura espacial: Project->Site->Building->Storey; sin entidades de analisis ni cargas")
