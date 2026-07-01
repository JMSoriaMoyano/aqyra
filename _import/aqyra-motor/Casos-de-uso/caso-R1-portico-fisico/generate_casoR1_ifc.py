"""
CASO R1 - PORTICO FISICO REAL. Primer caso de la DIRECCION 2 (puente IFC fisico ->
modelo analitico). A diferencia de los casos 1-11 (IFC ORTODOXO del dominio de
ANALISIS: IfcStructuralCurveMember/SurfaceMember, acciones, apoyos explicitos),
este es un IFC FISICO como el que entrega una herramienta BIM real:

  - Estructura espacial:  IfcProject -> IfcSite -> IfcBuilding -> IfcBuildingStorey
  - Elementos FISICOS con GEOMETRIA Body (IfcExtrudedAreaSolid barriendo un
    IfcIShapeProfileDef a lo largo del eje del elemento) y placement propio:
      * IfcColumn x2 (HEB 200, S275), verticales, 4,0 m
      * IfcBeam   x1 (IPE 330, S275), horizontal, luz 6,0 m
  - Material y seccion por IfcMaterialProfileSetUsage -> IfcMaterialProfileSet ->
    IfcMaterialProfile (IfcMaterial S275 + IfcIShapeProfileDef)
  - NO hay entidades de analisis ni cargas: como en BIM real, el modelo analitico
    (ejes, nudos, apoyos) y las HIPOTESIS de carga NO estan. Se aportan como Pset
    (datos sin entidad estandar): hipotesis de carga del dintel y condicion de apoyo
    de la base -> el "puente" debe DERIVAR el modelo analitico desde la GEOMETRIA.

GEOMETRIA identica al caso 1 (portico HEB 200 + IPE 330, S275, luz 6 m, altura 4 m,
G=12 / Q=10 kN/m) para poder VALIDAR el puente contra un resultado ya conocido
(caso 1: 93,60 kN/apoyo; pilares 32,0 %; dintel 44,6 %).

El agente (puente fisico->analitico) debe:
  - leer IfcColumn/IfcBeam, su GEOMETRIA (eje = directriz del barrido) y su seccion
    (IfcIShapeProfileDef del profile set) y material,
  - construir NUDOS por interseccion de ejes (con tolerancia) y el modelo neutro,
  - inferir APOYOS (base, Pset) y aplicar las HIPOTESIS de carga (Pset del dintel),
  - enrutar a `barras` (EC3) y comprobar -> debe reproducir el caso 1.

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import math
import ifcopenshell
import ifcopenshell.guid

STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
HEB200 = dict(name="HEB 200", b=0.200, h=0.200, tw=0.009, tf=0.015, r=0.018)
IPE330 = dict(name="IPE 330", b=0.160, h=0.330, tw=0.0075, tf=0.0115, r=0.018)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-R1.ifc")

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


# ---- unidades + contextos (Model + subcontexto Body) ----
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=a2p3d((0., 0., 0.)))
body = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                       ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")
project = f.create_entity("IfcProject", GlobalId=guid(), Name="Caso R1 - Portico fisico (puente IFC->analitico)",
                          UnitsInContext=ua, RepresentationContexts=[ctx])

# ---- estructura espacial ----
site_pl = local_placement(None, a2p3d((0., 0., 0.)))
site = f.create_entity("IfcSite", GlobalId=guid(), Name="Parcela", ObjectPlacement=site_pl,
                       CompositionType="ELEMENT")
bld_pl = local_placement(site_pl, a2p3d((0., 0., 0.)))
building = f.create_entity("IfcBuilding", GlobalId=guid(), Name="Edificio R1", ObjectPlacement=bld_pl,
                           CompositionType="ELEMENT")
sto_pl = local_placement(bld_pl, a2p3d((0., 0., 0.)))
storey = f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name="Planta baja", ObjectPlacement=sto_pl,
                         CompositionType="ELEMENT", Elevation=0.0)
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[building])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=building, RelatedObjects=[storey])


def material(M):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    props = [f.create_entity("IfcPropertySingleValue", Name=k,
                NominalValue=f.create_entity("IfcReal", wrappedValue=float(v)))
             for k, v in (("YoungModulus", M["E"]), ("ShearModulus", M["G"]),
                          ("PoissonRatio", M["nu"]), ("MassDensity", M["rho"]), ("YieldStress", M["fy"]))]
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m


steel = material(STEEL)


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


def member(kind, name, p0, p1, P, refdir):
    """Crea un IfcColumn/IfcBeam fisico: barrido del perfil a lo largo del eje p0->p1."""
    v = [p1[i] - p0[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in v))
    axis = [c / L for c in v]
    prof = ishape(P)
    # solido: extrusion del perfil (en su plano XY local) a lo largo de +Z local por L
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=prof,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)), Depth=L)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    # placement del elemento: origen en p0, Z local = eje, X local = refdir
    pl = local_placement(sto_pl, a2p3d(p0, axis=axis, ref=refdir))
    cls = "IfcColumn" if kind == "col" else "IfcBeam"
    el = f.create_entity(cls, GlobalId=guid(), Name=name, ObjectPlacement=pl, Representation=pds,
                         PredefinedType="COLUMN" if kind == "col" else "BEAM")
    # material + seccion (IfcMaterialProfileSetUsage)
    mp = f.create_entity("IfcMaterialProfile", Name=name + "_perfil", Material=steel, Profile=prof)
    mps = f.create_entity("IfcMaterialProfileSet", Name=P["name"], MaterialProfiles=[mp])
    usage = f.create_entity("IfcMaterialProfileSetUsage", ForProfileSet=mps, CardinalPoint=5)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[el], RelatingMaterial=usage)
    return el


# ---- los 3 elementos del portico (geometria = caso 1) ----
H, Lspan = 4.0, 6.0
col1 = member("col", "Pilar_1", (0.0, 0.0, 0.0), (0.0, 0.0, H), HEB200, refdir=(1., 0., 0.))
col2 = member("col", "Pilar_2", (Lspan, 0.0, 0.0), (Lspan, 0.0, H), HEB200, refdir=(1., 0., 0.))
beam = member("beam", "Dintel", (0.0, 0.0, H), (Lspan, 0.0, H), IPE330, refdir=(0., 1., 0.))

# ---- datos NO geometricos (no existen en un IFC fisico) -> Pset hipotesis ----
# hipotesis de carga del dintel (kN/m) y condicion de apoyo de la base
pset_for(beam, "Pset_Estructurando_CargaHipotesis",
         {"Descripcion": "carga gravitatoria de servicio sobre el dintel",
          "G_kN_m": 12.0, "Q_kN_m": 10.0, "Direccion": "-Z"})
for c in (col1, col2):
    pset_for(c, "Pset_Estructurando_ApoyoBase",
             {"Cota_z_m": 0.0, "Tipo": "biarticulado"})
pset_for(building, "Pset_Estructurando_ProyectoAnalisis",
         {"Norma": "EC3", "Material_defecto": "S275", "Sistema": "portico_plano",
          "Nota": "IFC fisico: derivar modelo analitico de la geometria (puente Direccion 2)"})

# ---- contener los elementos en la planta ----
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=storey, RelatedElements=[col1, col2, beam])

f.write(OUT)
print("IFC caso R1 (FISICO, puente IFC->analitico) escrito en:", OUT)
print("  IfcColumn x2 (HEB 200) + IfcBeam (IPE 330), S275, geometria Body (SweptSolid)")
print("  Geometria = caso 1: luz %.1f m, altura %.1f m, G=12 / Q=10 kN/m (Pset hipotesis)" % (Lspan, H))
print("  Estructura espacial: Project->Site->Building->Storey; sin entidades de analisis ni cargas")
