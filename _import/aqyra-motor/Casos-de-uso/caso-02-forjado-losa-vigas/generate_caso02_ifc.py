"""
CASO 2 - Forjado: losa de hormigon sobre vigas de acero. IFC4 ORTODOXO del
dominio de analisis estructural, con SUPERFICIE + BARRAS en el mismo modelo.

Modelo (sintetico, realista):
  - Losa de hormigon C30/37, espesor 0,12 m, en planta 6,0 x 4,0 m (plano XY, z=0).
    Apoyada (unidireccional) en las dos vigas de acero (bordes y=0 e y=4).
  - Dos vigas de acero IPE 400 (S275), luz 6,0 m, biapoyadas, separadas 4,0 m.
  - Apoyos: bases biarticuladas en los 4 extremos de viga (sobre pilares/muros).
  - Cargas de SUPERFICIE sobre la losa (gravedad -Z):
      G = 4,5 kN/m2 (p.p. losa 0,12*25=3,0 + solado/tabiqueria 1,5)
      Q = 3,0 kN/m2 (sobrecarga de uso)
    El reparto losa -> vigas (ancho tributario 2,0 m) es el objetivo de aprendizaje
    del caso (cada viga: G=9,0 kN/m, Q=6,0 kN/m).

Entidades ESTANDAR (sin Pset_Estructurando_*):
  - IfcStructuralPointConnection (+IfcVertexPoint) y apoyos IfcBoundaryNodeCondition.
  - Vigas: IfcStructuralCurveMember (IfcEdge) + IfcMaterialProfileSet ->
    IfcIShapeProfileDef (IPE 400) + IfcRelAssociatesMaterial.
  - Losa: IfcStructuralSurfaceMember (Thickness=0,12; representacion por IfcFaceSurface
    con polilinea de esquinas) + material C30/37 por IfcRelAssociatesMaterial.
  - Cargas: IfcStructuralLoadGroup (G,Q) + IfcStructuralSurfaceAction +
    IfcStructuralLoadPlanarForce, conectadas a la losa por IfcRelConnectsStructuralActivity.

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

LX = 6.0   # luz de las vigas (m)
LY = 4.0   # separacion entre vigas / ancho del forjado (m)
T_LOSA = 0.12

STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
CONC = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=33000e6, nu=0.2, rho=2500.0,
            G=33000e6 / (2 * (1 + 0.2)))
IPE400 = dict(name="IPE 400", b=0.180, h=0.400, tw=0.0086, tf=0.0135, r=0.021)

G_kN_m2 = 4.5e3   # carga permanente de superficie (N/m2)
Q_kN_m2 = 3.0e3   # sobrecarga de uso de superficie (N/m2)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-02.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 2 - Forjado losa sobre vigas",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    return f.create_entity("IfcPropertySingleValue", Name=name,
                           NominalValue=f.create_entity("IfcReal", wrappedValue=float(val)))


# --- Materiales (Pset_MaterialMechanical estandar) ---
steel = f.create_entity("IfcMaterial", Name=STEEL["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=steel,
                Properties=[prop("YoungModulus", STEEL["E"]), prop("ShearModulus", STEEL["G"]),
                            prop("PoissonRatio", STEEL["nu"]), prop("MassDensity", STEEL["rho"]),
                            prop("YieldStress", STEEL["fy"])])
conc = f.create_entity("IfcMaterial", Name=CONC["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=conc,
                Properties=[prop("YoungModulus", CONC["E"]), prop("ShearModulus", CONC["G"]),
                            prop("PoissonRatio", CONC["nu"]), prop("MassDensity", CONC["rho"]),
                            prop("CompressiveStrength", CONC["fck"]),
                            prop("TensileStrength", CONC["fctm"])])


def profile_set(P):
    prof = f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
                           OverallWidth=P["b"], OverallDepth=P["h"],
                           WebThickness=P["tw"], FlangeThickness=P["tf"], FilletRadius=P["r"])
    mprof = f.create_entity("IfcMaterialProfile", Name=P["name"], Material=steel, Profile=prof)
    return f.create_entity("IfcMaterialProfileSet", Name=P["name"], MaterialProfiles=[mprof])


mps_beam = profile_set(IPE400)
analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Forjado caso 2", PredefinedType="LOADING_3D")


def boolwrap(b):
    return f.create_entity("IfcBoolean", wrappedValue=b) if b else None


def nodo(name, x, y, z, apoyo=None):
    pt = f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z))
    vp = f.create_entity("IfcVertexPoint", VertexGeometry=pt)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])])
    cond = None
    if apoyo:
        cond = f.create_entity("IfcBoundaryNodeCondition", Name="apoyo",
            TranslationalStiffnessX=boolwrap(apoyo[0]), TranslationalStiffnessY=boolwrap(apoyo[1]),
            TranslationalStiffnessZ=boolwrap(apoyo[2]), RotationalStiffnessX=boolwrap(apoyo[3]),
            RotationalStiffnessY=boolwrap(apoyo[4]), RotationalStiffnessZ=boolwrap(apoyo[5]))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
                           Representation=rep, AppliedCondition=cond)
    return conn, vp, pt


# Apoyo biarticulado: traslaciones coaccionadas, giros libres (RZ fijo: estabilidad)
PIN = [True, True, True, False, False, True]
# 4 esquinas del forjado = extremos de las dos vigas
N1, v1, p1 = nodo("N1", 0.0, 0.0, 0.0, PIN)
N2, v2, p2 = nodo("N2", LX, 0.0, 0.0, PIN)
N3, v3, p3 = nodo("N3", LX, LY, 0.0, PIN)
N4, v4, p4 = nodo("N4", 0.0, LY, 0.0, PIN)


def barra(name, na, va, nb, vb, mps):
    edge = f.create_entity("IfcEdge", EdgeStart=va, EdgeEnd=vb)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])])
    mb = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name=name,
                         PredefinedType="RIGID_JOINED_MEMBER",
                         Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
                         Representation=rep)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                    RelatedObjects=[mb], RelatingMaterial=mps)
    return mb


# Vigas: borde y=0 (V1: N1->N2) y borde y=LY (V2: N4->N3)
V1 = barra("V1", N1, v1, N2, v2, mps_beam)
V2 = barra("V2", N4, v4, N3, v3, mps_beam)


# --- Losa: IfcStructuralSurfaceMember con representacion de cara (IfcFaceSurface) ---
def losa(name, pts, t):
    poly = f.create_entity("IfcPolyLoop", Polygon=pts)
    bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
    plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
                Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)),
                Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
                RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
    face = f.create_entity("IfcFaceSurface", Bounds=[bound], FaceSurface=plane, SameSense=True)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
    sm = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name=name,
                         PredefinedType="SHELL", Thickness=t, Representation=rep)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                    RelatedObjects=[sm], RelatingMaterial=conc)
    return sm


LOSA = losa("Losa", [p1, p2, p3, p4], T_LOSA)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=[N1, N2, N3, N4, V1, V2, LOSA], RelatingGroup=analysis)


# --- Cargas de superficie sobre la losa ---
def carga_superficie(nombre, action_type, action_source, q):
    grp = f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=nombre,
                          PredefinedType="LOAD_GROUP", ActionType=action_type,
                          ActionSource=action_source, Coefficient=1.0)
    load = f.create_entity("IfcStructuralLoadPlanarForce", Name=nombre + "_q",
                           PlanarForceX=0.0, PlanarForceY=0.0, PlanarForceZ=-q)
    act = f.create_entity("IfcStructuralSurfaceAction", GlobalId=guid(), Name=nombre + "_losa",
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          ProjectedOrTrue="TRUE_LENGTH", PredefinedType="CONST")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=LOSA, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=grp)
    return grp


g_grp = carga_superficie("G", "PERMANENT_G", "DEAD_LOAD_G", G_kN_m2)
q_grp = carga_superficie("Q", "VARIABLE_Q", "LIVE_LOAD_Q", Q_kN_m2)
analysis.LoadedBy = [g_grp, q_grp]

f.write(OUT)
print("IFC caso 2 (ortodoxo) escrito en:", OUT)
print("  Forjado %.1f x %.1f m | losa C30/37 t=%.0f mm | vigas %s S275 luz %.1f m" % (
    LX, LY, T_LOSA * 1000, IPE400["name"], LX))
print("  Cargas superficie losa: G=%.1f kN/m2, Q=%.1f kN/m2 (gravedad -Z)" % (
    G_kN_m2 / 1e3, Q_kN_m2 / 1e3))
print("  Reparto esperado a cada viga (tributario %.1f m): G=%.1f kN/m, Q=%.1f kN/m" % (
    LY / 2, G_kN_m2 / 1e3 * LY / 2, Q_kN_m2 / 1e3 * LY / 2))
