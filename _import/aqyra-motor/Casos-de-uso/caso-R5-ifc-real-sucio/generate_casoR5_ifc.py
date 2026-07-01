"""
CASO R5 - IFC FISICO "REAL-SUCIO" de un exportador concreto. Quinto y ultimo
peldano de la DIRECCION 2 (cierre de INC-07). Reproduce la GEOMETRIA del portico
del caso 1 / R1 (2 IfcColumn HEB 200 + 1 IfcBeam IPE 330, S275, luz 6 m, altura
4 m, G=12 / Q=10 kN/m) PERO introduce a proposito las "suciedades" de un
entregable BIM real, PARAMETRIZADAS y DOCUMENTADAS para medir la robustez del
puente fisico->analitico:

  1. UNIDADES en MILIMETRO (no metro): IfcUnitAssignment con LENGTHUNIT MILLI.
     El puente debe leer el factor de escala y convertir a metros.
  2. EJES NO CENTRADOS / offset eje fisico<->analitico: cada elemento se barre
     desde un CardinalPoint != 5 (esquina / cara) del IfcMaterialProfileSetUsage;
     el origen del barrido NO esta en el eje baricentrico. El puente debe
     RECUPERAR el eje analitico aplicando el offset del cardinal point y
     DOCUMENTAR la excentricidad.
       - Pilar_1: CardinalPoint=1 (esquina inferior-izquierda) -> ecc 141 mm
       - Pilar_2: CardinalPoint=3 (esquina inferior-derecha)  -> ecc 141 mm
       - Dintel : CardinalPoint=8 (cara superior del ala)     -> ecc 165 mm
  3. BARRAS QUE NO SE CORTAN EN EL NUDO: huecos y solapes.
       - Pilares barridos 40 mm de MAS (pasan de largo: solape).
       - Dintel arranca/termina 30 mm ANTES del eje de cada pilar (hueco).
     El grafo necesita tolerancia de snap mayor (60 mm) para fusionar/puentear.
  4. ELEMENTOS NO ESTRUCTURALES / NO CONECTADOS (el puente debe FILTRARLOS):
       - IfcRailing  (barandilla decorativa, con geometria) -> clase no admitida
       - IfcBuildingElementProxy (generico) -> clase no admitida
       - IfcBeam suelto y aislado (no toca el grafo, sin apoyo) -> componente
         desconectada -> se filtra por conectividad (avisa y descarta).
  5. NOMENCLATURA Y TIPOS DE EXPORTADOR:
       - Nombres autogenerados estilo GUID/categoria del exportador.
       - PredefinedType variados (USERDEFINED / NOTDEFINED).
       - Perfiles por catalogo del exportador (alias): "HE 200 B" (Euronorm) y
         "IPE330" -> el puente los mapea a "HEB 200" / "IPE 330" (perfiles_db).
       - Placements anidados (Project->Site->Building->Storey->elemento).

Tras la LIMPIEZA el modelo analitico debe coincidir con el del caso limpio
(R1): mismos 4 nudos / 3 barras (salvo las excentricidades documentadas) ->
93,60 kN/apoyo; HEB 200 ~32 %; IPE 330 44,6 %.

Unidades del FICHERO: MILIMETRO (longitud), NEWTON (fuerza). Plano XY horizontal,
Z vertical, gravedad -Z.
"""
import os
import math
import ifcopenshell
import ifcopenshell.guid

MM = 1000.0  # factor metros -> milimetros (el fichero esta en mm)

STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
# perfiles con NOMBRE DE CATALOGO DEL EXPORTADOR (alias, no la clave de perfiles_db)
HEB200 = dict(name="HE 200 B", b=0.200, h=0.200, tw=0.009, tf=0.015, r=0.018)
IPE330 = dict(name="IPE330", b=0.160, h=0.330, tw=0.0075, tf=0.0115, r=0.018)

# --- suciedades parametrizadas (en metros; se convierten a mm al escribir) ---
OVERLAP = 0.040     # los pilares pasan 40 mm de largo (solape)
GAP = 0.030         # el dintel arranca/termina 30 mm antes (hueco)
SNAP_TOL = 0.060    # tolerancia de snap que necesitara el puente (m)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-R5.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new

# posiciones del CardinalPoint relativas al centroide, en fracciones de (b, h)
CP_FRAC = {1: (-0.5, -0.5), 2: (0.0, -0.5), 3: (0.5, -0.5),
           4: (-0.5, 0.0), 5: (0.0, 0.0), 6: (0.5, 0.0),
           7: (-0.5, 0.5), 8: (0.0, 0.5), 9: (0.5, 0.5)}


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


# ---- unidades en MILIMETRO + contextos ----
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE", Prefix="MILLI")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=a2p3d((0., 0., 0.)))
body = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                       ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")
project = f.create_entity("IfcProject", GlobalId=guid(),
                          Name="Caso R5 - IFC fisico real-sucio (exportador)",
                          UnitsInContext=ua, RepresentationContexts=[ctx])

# ---- estructura espacial (placements anidados) ----
site_pl = local_placement(None, a2p3d((0., 0., 0.)))
site = f.create_entity("IfcSite", GlobalId=guid(), Name="Parcela", ObjectPlacement=site_pl,
                       CompositionType="ELEMENT")
bld_pl = local_placement(site_pl, a2p3d((0., 0., 0.)))
building = f.create_entity("IfcBuilding", GlobalId=guid(), Name="Edificio R5", ObjectPlacement=bld_pl,
                           CompositionType="ELEMENT")
sto_pl = local_placement(bld_pl, a2p3d((0., 0., 0.)))
storey = f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name="Nivel 00", ObjectPlacement=sto_pl,
                         CompositionType="ELEMENT", Elevation=0.0)
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=project, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[building])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=building, RelatedObjects=[storey])


def material(M):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    props = [f.create_entity("IfcPropertySingleValue", Name=k,
                NominalValue=f.create_entity("IfcReal", wrappedValue=float(v)))
             for k, v in (("YoungModulus", M["E"]), ("ShearModulus", M["G"]),
                          ("PoissonRatio", M["nu"]), ("MassDensity", M["rho"]),
                          ("YieldStress", M["fy"]))]
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m


steel = material(STEEL)


def ishape(P):
    # dimensiones del perfil EN MILIMETRO (el fichero esta en mm)
    return f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.))),
                           OverallWidth=P["b"] * MM, OverallDepth=P["h"] * MM,
                           WebThickness=P["tw"] * MM, FlangeThickness=P["tf"] * MM,
                           FilletRadius=P["r"] * MM)


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


def member(cls, name, p0_an, p1_an, P, refdir, cardinal, predef, objtype=None):
    """Crea un IfcColumn/IfcBeam fisico REAL-SUCIO.
    p0_an, p1_an = eje ANALITICO deseado (m, con huecos/solapes ya incluidos).
    El eje FISICO = analitico + offset del CardinalPoint -> el puente lo recupera.
    Todo se escribe en MILIMETRO."""
    # offset del cardinal point en ejes locales del placement (X=refdir, Z=eje)
    v = [p1_an[i] - p0_an[i] for i in range(3)]
    L = math.sqrt(sum(c * c for c in v))
    zax = [c / L for c in v]
    xax = list(refdir)
    # Y local = Z x X
    yax = [zax[1] * xax[2] - zax[2] * xax[1],
           zax[2] * xax[0] - zax[0] * xax[2],
           zax[0] * xax[1] - zax[1] * xax[0]]
    fx, fy = CP_FRAC[cardinal]
    off_local = [fx * P["b"], fy * P["h"]]   # m
    off_world = [off_local[0] * xax[i] + off_local[1] * yax[i] for i in range(3)]
    p0 = [p0_an[i] + off_world[i] for i in range(3)]   # eje FISICO (m)

    prof = ishape(P)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=prof,
                            Position=a2p3d((0., 0., 0.)), ExtrudedDirection=dirn((0., 0., 1.)),
                            Depth=L * MM)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    pds = f.create_entity("IfcProductDefinitionShape", Representations=[shape])
    pl = local_placement(sto_pl, a2p3d([c * MM for c in p0], axis=zax, ref=refdir))
    kw = dict(GlobalId=guid(), Name=name, ObjectPlacement=pl, Representation=pds, PredefinedType=predef)
    if objtype is not None:
        kw["ObjectType"] = objtype
    el = f.create_entity(cls, **kw)
    mp = f.create_entity("IfcMaterialProfile", Name=name + "_perfil", Material=steel, Profile=prof)
    mps = f.create_entity("IfcMaterialProfileSet", Name=P["name"], MaterialProfiles=[mp])
    usage = f.create_entity("IfcMaterialProfileSetUsage", ForProfileSet=mps, CardinalPoint=cardinal)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[el], RelatingMaterial=usage)
    return el


# ---- los 3 elementos ESTRUCTURALES del portico (geometria = caso 1, "sucia") ----
H, Lspan = 4.0, 6.0
# pilares: ejes analiticos en x=0 y x=6, barridos OVERLAP de mas (pasan de largo)
col1 = member("IfcColumn", "0kZQ8aXf3:Structural Column:HE 200 B:418273",
              (0.0, 0.0, 0.0), (0.0, 0.0, H + OVERLAP), HEB200, refdir=(1., 0., 0.),
              cardinal=1, predef="COLUMN")
col2 = member("IfcColumn", "0kZQ8aXf3:Structural Column:HE 200 B:418274",
              (Lspan, 0.0, 0.0), (Lspan, 0.0, H + OVERLAP), HEB200, refdir=(1., 0., 0.),
              cardinal=3, predef="COLUMN")
# dintel: eje analitico en z=H, con HUECO de GAP en cada extremo (no llega al eje del pilar)
beam = member("IfcBeam", "1mPLr92Kx:Framing:IPE330:55012",
              (0.0 + GAP, 0.0, H), (Lspan - GAP, 0.0, H), IPE330, refdir=(0., 1., 0.),
              cardinal=8, predef="USERDEFINED", objtype="Girder")

# ---- ELEMENTOS NO ESTRUCTURALES (el puente debe filtrarlos por clase) ----
def simple_box_solid(dx, dy, dz):
    prof = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA",
                           Position=f.create_entity("IfcAxis2Placement2D",
                               Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.))),
                           XDim=dx * MM, YDim=dy * MM)
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=prof, Position=a2p3d((0., 0., 0.)),
                            ExtrudedDirection=dirn((0., 0., 1.)), Depth=dz * MM)
    shape = f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                            RepresentationIdentifier="Body", RepresentationType="SweptSolid", Items=[solid])
    return f.create_entity("IfcProductDefinitionShape", Representations=[shape])


rail_pl = local_placement(sto_pl, a2p3d([0. * MM, 0. * MM, H * MM]))
railing = f.create_entity("IfcRailing", GlobalId=guid(), Name="Baranda decorativa",
                          ObjectPlacement=rail_pl, Representation=simple_box_solid(0.05, 0.05, 1.0),
                          PredefinedType="GUARDRAIL")
proxy_pl = local_placement(sto_pl, a2p3d([3.0 * MM, 1.0 * MM, 0. * MM]))
proxy = f.create_entity("IfcBuildingElementProxy", GlobalId=guid(), Name="Elemento generico (mobiliario)",
                        ObjectPlacement=proxy_pl, Representation=simple_box_solid(0.4, 0.4, 0.8))

# ---- ELEMENTO ESTRUCTURAL PERO NO CONECTADO (componente aislada, sin apoyo) ----
stray = member("IfcBeam", "9zStray:Framing:IPE330:99001",
               (10.0, 5.0, 3.0), (13.0, 5.0, 3.0), IPE330, refdir=(0., 1., 0.),
               cardinal=5, predef="BEAM")

# ---- datos NO geometricos (hipotesis del calculista) -> Pset ----
pset_for(beam, "Pset_Estructurando_CargaHipotesis",
         {"Descripcion": "carga gravitatoria de servicio sobre el dintel",
          "G_kN_m": 12.0, "Q_kN_m": 10.0, "Direccion": "-Z"})
for c in (col1, col2):
    pset_for(c, "Pset_Estructurando_ApoyoBase", {"Cota_z_m": 0.0, "Tipo": "biarticulado"})
# tolerancia de snap del puente (geometria real-sucia) en el proyecto
pset_for(project, "Pset_Estructurando_Puente",
         {"Snap_tol_m": SNAP_TOL,
          "Nota": "IFC real-sucio: ejes con offset (cardinal point), huecos/solapes en nudos, mm"})
pset_for(building, "Pset_Estructurando_ProyectoAnalisis",
         {"Norma": "EC3", "Material_defecto": "S275", "Sistema": "portico_plano",
          "Nota": "IFC fisico REAL-SUCIO (exportador): unidades mm, cardinal point, huecos, no-estructurales"})

# ---- contener TODOS los elementos en la planta ----
f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=storey,
                RelatedElements=[col1, col2, beam, railing, proxy, stray])

f.write(OUT)
print("IFC caso R5 (FISICO REAL-SUCIO) escrito en:", OUT)
print("  Unidades: MILIMETRO. IfcColumn x2 (HE 200 B) + IfcBeam (IPE330), S275.")
print("  Suciedades: cardinal point (1/3/8), solape pilares %.0f mm, hueco dintel %.0f mm," % (OVERLAP*1000, GAP*1000))
print("  no-estructurales (IfcRailing, IfcBuildingElementProxy), IfcBeam suelto, snap_tol %.0f mm." % (SNAP_TOL*1000))
