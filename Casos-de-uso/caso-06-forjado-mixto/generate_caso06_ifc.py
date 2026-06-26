"""
CASO 6 - Forjado colaborante / VIGA MIXTA acero-hormigon (EN 1994-1-1, EC4).
IFC4 ORTODOXO del dominio de analisis estructural.

Modelo (sintetico, realista): viga mixta secundaria biapoyada, construccion SIN
APEAR (unpropped), con forjado colaborante (chapa nervada perpendicular a la viga):
  - Perfil de ACERO IPE 360, S275, luz L = 8,0 m -> IfcStructuralCurveMember
    horizontal (eje X) + IfcMaterialProfileSet -> IfcMaterialProfile ->
    IfcIShapeProfileDef (geometria completa: OverallDepth/Width, WebThickness,
    FlangeThickness, FilletRadius).
  - LOSA de hormigon C25/30 colaborante, canto total 0,12 m, sobre el ancho
    tributario SEP = 3,0 m -> IfcStructuralSurfaceMember (Thickness=0,12) con
    representacion IfcFaceSurface/IfcPolyLoop (4 esquinas sobre la viga) +
    material por IfcRelAssociatesMaterial.
  - CARGAS POR FASE (gravedad -Z), por IfcStructuralLoadGroup +
    IfcStructuralSurfaceAction + IfcStructuralLoadPlanarForce sobre la losa, con
    la FASE codificada en el nombre del grupo:
      * Fase CONSTRUCCION (el acero solo resiste): G_construccion = peso del
        hormigon fresco (2,5 kN/m2) ; Qc_construccion = sobrecarga de ejecucion
        (0,75 kN/m2).
      * Fase MIXTA (seccion mixta): G2_mixta = carga muerta adicional (1,5 kN/m2) ;
        Q_mixta = sobrecarga de uso (3,0 kN/m2).
  - DATOS SIN ENTIDAD IFC ESTANDAR (se mantienen como Pset, como el R_d/k_s del
    caso 5): conectores (pernos) y chapa colaborante (nervio).
        Pset_Estructurando_Conectores: d, hsc, fu, sep_long.
        Pset_Estructurando_Losa: ht, hp, hc, b0, nervios, nr.

Interes del caso: validar la lectura ORTODOXA de la viga mixta (perfil de acero
de IfcIShapeProfileDef, losa de IfcStructuralSurfaceMember, cargas por fase de
IfcStructuralLoadGroup) y el calculo EC4: ancho eficaz, M_pl,Rd por fibras, M_Rd
con grado de conexion, conexion a cortante, cortante, fase de construccion y flecha.

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

L = 8.0                 # luz de la viga (m)
SEP = 3.0               # separacion entre vigas = ancho tributario / ancho de losa (m)

# Perfil de acero IPE 360, S275 (geometria nominal)
STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
IPE360 = dict(name="IPE360", h=0.360, b=0.170, tw=0.008, tf=0.0127, r=0.018)

# Losa colaborante C25/30 (chapa nervada perpendicular)
CONC = dict(name="C25/30", fck=25e6, fctm=2.6e6, E=31e9, nu=0.2, rho=2500.0, G=12.9e9)
HT, HP, HC, B0, NR = 0.12, 0.058, 0.062, 0.100, 1

# Conectores (pernos)
D_STUD, HSC, FU_STUD, SEP_STUD = 0.019, 0.100, 450e6, 0.207

# Cargas por fase (Pa sobre el forjado)
G_LOSA, QC_EJEC = 2.5e3, 0.75e3      # fase construccion (acero solo)
G2_PERM, Q_USO = 1.5e3, 3.0e3        # fase mixta

Z_SLAB = IPE360["h"] / 2.0 + (HT - HC) / 2.0   # cota geometrica de la losa (sobre la viga)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-06.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 6 - Viga mixta / forjado colaborante",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    nominal = (f.create_entity("IfcText", wrappedValue=val) if isinstance(val, str)
               else f.create_entity("IfcReal", wrappedValue=float(val)))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


# --- materiales ---
steel = f.create_entity("IfcMaterial", Name=STEEL["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical_S", Material=steel,
                Properties=[prop("YoungModulus", STEEL["E"]), prop("ShearModulus", STEEL["G"]),
                            prop("PoissonRatio", STEEL["nu"]), prop("MassDensity", STEEL["rho"]),
                            prop("YieldStress", STEEL["fy"])])
conc = f.create_entity("IfcMaterial", Name=CONC["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical_C", Material=conc,
                Properties=[prop("YoungModulus", CONC["E"]), prop("ShearModulus", CONC["G"]),
                            prop("PoissonRatio", CONC["nu"]), prop("MassDensity", CONC["rho"]),
                            prop("CompressiveStrength", CONC["fck"]), prop("TensileStrength", CONC["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Viga mixta caso 6", PredefinedType="LOADING_3D")


def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint",
                           VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))


def point_connection(name, x, y, z, bc=None):
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Vertex",
                        Items=[vertex(x, y, z)])])
    return f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
                           Representation=rep, AppliedCondition=bc)


# --- apoyos de la viga (biapoyada) ---
n0 = point_connection("V0", 0.0, 0.0, 0.0, f.create_entity("IfcBoundaryNodeCondition",
        Name="apoyo_fijo",
        TranslationalStiffnessX=f.create_entity("IfcBoolean", wrappedValue=True),
        TranslationalStiffnessY=f.create_entity("IfcBoolean", wrappedValue=True),
        TranslationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=True)))
nL = point_connection("VL", L, 0.0, 0.0, f.create_entity("IfcBoundaryNodeCondition",
        Name="apoyo_movil",
        TranslationalStiffnessX=f.create_entity("IfcBoolean", wrappedValue=False),
        TranslationalStiffnessY=f.create_entity("IfcBoolean", wrappedValue=True),
        TranslationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=True)))

# --- VIGA de acero IPE 360 (IfcStructuralCurveMember + IfcIShapeProfileDef) ---
edge = f.create_entity("IfcEdge", EdgeStart=vertex(0., 0., 0.), EdgeEnd=vertex(L, 0., 0.))
viga = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="Viga_mixta",
    PredefinedType="RIGID_JOINED_MEMBER",
    Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
    Representation=f.create_entity("IfcProductDefinitionShape",
        Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])]))
ishape = f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=IPE360["name"],
    OverallWidth=IPE360["b"], OverallDepth=IPE360["h"], WebThickness=IPE360["tw"],
    FlangeThickness=IPE360["tf"], FilletRadius=IPE360["r"])
mprof = f.create_entity("IfcMaterialProfile", Name="IPE360 S275", Material=steel, Profile=ishape)
mpset = f.create_entity("IfcMaterialProfileSet", Name="Seccion viga", MaterialProfiles=[mprof])
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[viga], RelatingMaterial=mpset)
# datos sin entidad IFC estandar: conectores y chapa colaborante (Pset, como R_d/k_s del caso 5)
pset_for(viga, "Pset_Estructurando_Conectores",
         {"d_m": D_STUD, "hsc_m": HSC, "fu_Pa": FU_STUD, "sep_long_m": SEP_STUD})
pset_for(viga, "Pset_Estructurando_Losa",
         {"ht_m": HT, "hp_m": HP, "hc_m": HC, "b0_m": B0, "nervios": "perpendicular", "nr": NR,
          "apeado": 0})

# --- LOSA colaborante (IfcStructuralSurfaceMember + IfcFaceSurface) ---
ys = SEP / 2.0
slab_pts = [(0., -ys, Z_SLAB), (L, -ys, Z_SLAB), (L, ys, Z_SLAB), (0., ys, Z_SLAB)]
poly = f.create_entity("IfcPolyLoop", Polygon=[
    f.create_entity("IfcCartesianPoint", Coordinates=c) for c in slab_pts])
face_bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
    Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., Z_SLAB)),
    Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
    RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
face = f.create_entity("IfcFaceSurface", Bounds=[face_bound], FaceSurface=plane, SameSense=True)
slab_rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
losa = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="Losa_colaborante",
                       PredefinedType="SHELL", Thickness=HT, Representation=slab_rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[losa], RelatingMaterial=conc)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=[n0, nL, viga, losa], RelatingGroup=analysis)


# --- cargas por fase (IfcStructuralLoadGroup + IfcStructuralSurfaceAction) ---
def load_group(name, permanent):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP",
                           ActionType="PERMANENT_G" if permanent else "VARIABLE_Q",
                           ActionSource="DEAD_LOAD_G" if permanent else "LIVE_LOAD_Q")


def surface_action(name, qz_Pa, group):
    load = f.create_entity("IfcStructuralLoadPlanarForce", Name=name + "_q",
                           PlanarForceX=0.0, PlanarForceY=0.0, PlanarForceZ=qz_Pa)
    act = f.create_entity("IfcStructuralSurfaceAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=losa, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                    RelatedObjects=[act], RelatingGroup=group)


# Fase codificada en el nombre del grupo: *_construccion (acero solo) / *_mixta (mixta)
surface_action("G_construccion", -G_LOSA, load_group("G_construccion", True))
surface_action("Qc_construccion", -QC_EJEC, load_group("Qc_construccion", False))
surface_action("G2_mixta", -G2_PERM, load_group("G2_mixta", True))
surface_action("Q_mixta", -Q_USO, load_group("Q_mixta", False))

f.write(OUT)
print("IFC caso 6 escrito en:", OUT)
print("  Viga IPE360 S275 L=%.1f m  losa %s ht=%.0f mm  ancho=%.1f m" % (L, CONC["name"], HT * 1e3, SEP))
print("  Cargas kN/m2: G_constr=%.2f Qc=%.2f | G2=%.2f Q=%.2f" % (
    G_LOSA / 1e3, QC_EJEC / 1e3, G2_PERM / 1e3, Q_USO / 1e3))
print("  Conector D%.0f h%.0f sep=%.0f mm | nervio hp=%.0f b0=%.0f mm" % (
    D_STUD * 1e3, HSC * 1e3, SEP_STUD * 1e3, HP * 1e3, B0 * 1e3))
