"""
CASO 1 — Portico de acero simple. IFC4 ORTODOXO del dominio de analisis estructural.

A diferencia de los generadores del catalogo (que usan Psets propios
'Pset_Estructurando_*'), este modelo usa SOLO entidades IFC estandar, para servir de
banco de pruebas de un parser verdaderamente ortodoxo:

  - Nodos:    IfcStructuralPointConnection (+ IfcVertexPoint) con apoyos en
              IfcBoundaryNodeCondition.
  - Barras:   IfcStructuralCurveMember (topologia por IfcEdge) con la SECCION via
              IfcMaterialProfileSet -> IfcMaterialProfile -> IfcIShapeProfileDef
              (geometria real del perfil) y el material via IfcRelAssociatesMaterial.
  - Material: IfcMaterial + IfcMaterialProperties (Pset_MaterialMechanical, estandar).
  - Cargas:   IfcStructuralLoadGroup (G y Q) + IfcStructuralCurveAction +
              IfcStructuralLoadLinearForce, conectadas a la barra con
              IfcRelConnectsStructuralActivity; el modelo las referencia en LoadedBy.

Geometria: portico biarticulado, luz 6 m, altura 4 m. Pilares HEB 200, dintel
IPE 330, acero S275. Cargas en el dintel: G = 12 kN/m, Q = 10 kN/m (gravedad, -Z).

Plano XZ (Y=0), Z vertical, gravedad -Z (convencion del modulo 'barras').
Unidades SI (m, N, Pa).
"""
import os
import ifcopenshell
import ifcopenshell.guid

S = 6.0   # luz (m)
Hc = 4.0  # altura de pilares (m)

STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
# Perfiles I (dimensiones reales)
HEB200 = dict(name="HEB 200", b=0.200, h=0.200, tw=0.009, tf=0.015, r=0.018)
IPE330 = dict(name="IPE 330", b=0.160, h=0.330, tw=0.0075, tf=0.0115, r=0.018)

G_kN_m = 12.0e3   # carga permanente en el dintel (N/m)
Q_kN_m = 10.0e3   # sobrecarga en el dintel (N/m)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-01.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 1 - Portico de acero",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    return f.create_entity("IfcPropertySingleValue", Name=name,
                           NominalValue=f.create_entity("IfcReal", wrappedValue=float(val)))


# --- Material S275 con propiedades mecanicas (Pset estandar) ---
steel = f.create_entity("IfcMaterial", Name=STEEL["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=steel,
                Properties=[prop("YoungModulus", STEEL["E"]), prop("ShearModulus", STEEL["G"]),
                            prop("PoissonRatio", STEEL["nu"]), prop("MassDensity", STEEL["rho"]),
                            prop("YieldStress", STEEL["fy"])])


def profile_set(P):
    """IfcMaterialProfileSet con un IfcIShapeProfileDef (geometria real)."""
    prof = f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
                           OverallWidth=P["b"], OverallDepth=P["h"],
                           WebThickness=P["tw"], FlangeThickness=P["tf"], FilletRadius=P["r"])
    mprof = f.create_entity("IfcMaterialProfile", Name=P["name"], Material=steel, Profile=prof)
    return f.create_entity("IfcMaterialProfileSet", Name=P["name"], MaterialProfiles=[mprof])


mps_col = profile_set(HEB200)
mps_beam = profile_set(IPE330)

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Portico caso 1", PredefinedType="LOADING_3D")

# --- Nodos (IfcStructuralPointConnection + apoyos) ---
def boolwrap(b):
    return f.create_entity("IfcBoolean", wrappedValue=b) if b else None

def nodo(name, x, y, z, apoyo=None):
    vp = f.create_entity("IfcVertexPoint",
                         VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])])
    cond = None
    if apoyo:
        # apoyo = [DX,DY,DZ,RX,RY,RZ] (True = coaccionado rigido)
        cond = f.create_entity("IfcBoundaryNodeCondition", Name="apoyo",
            TranslationalStiffnessX=boolwrap(apoyo[0]), TranslationalStiffnessY=boolwrap(apoyo[1]),
            TranslationalStiffnessZ=boolwrap(apoyo[2]), RotationalStiffnessX=boolwrap(apoyo[3]),
            RotationalStiffnessY=boolwrap(apoyo[4]), RotationalStiffnessZ=boolwrap(apoyo[5]))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
                           Representation=rep, AppliedCondition=cond)
    return conn, vp

# pinned base: traslaciones coaccionadas (y fuera de plano), giros libres
PIN = [True, True, True, False, False, True]   # DX,DY,DZ fijos; RX,RY libres; RZ fijo (estab. plano)
N1, v1 = nodo("N1", 0.0, 0.0, 0.0, PIN)
N2, v2 = nodo("N2", 0.0, 0.0, Hc)
N3, v3 = nodo("N3", S, 0.0, Hc)
N4, v4 = nodo("N4", S, 0.0, 0.0, PIN)


def barra(name, na, va, nb, vb, mps):
    edge = f.create_entity("IfcEdge", EdgeStart=va, EdgeEnd=vb)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])])
    mb = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name=name,
                         PredefinedType="RIGID_JOINED_MEMBER",
                         Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 1., 0.)),
                         Representation=rep)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                    RelatedObjects=[mb], RelatingMaterial=mps)
    return mb

C1 = barra("C1", N1, v1, N2, v2, mps_col)    # pilar izquierdo
B1 = barra("B1", N2, v2, N3, v3, mps_beam)   # dintel
C2 = barra("C2", N4, v4, N3, v3, mps_col)    # pilar derecho

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=[N1, N2, N3, N4, C1, B1, C2], RelatingGroup=analysis)


# --- Cargas: IfcStructuralLoadGroup (G,Q) + IfcStructuralCurveAction sobre el dintel ---
def carga_grupo(nombre, action_type, action_source, q):
    grp = f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=nombre,
                          PredefinedType="LOAD_GROUP", ActionType=action_type,
                          ActionSource=action_source, Coefficient=1.0)
    load = f.create_entity("IfcStructuralLoadLinearForce", Name=nombre + "_q",
                           LinearForceX=0.0, LinearForceY=0.0, LinearForceZ=-q)
    act = f.create_entity("IfcStructuralCurveAction", GlobalId=guid(), Name=nombre + "_dintel",
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          ProjectedOrTrue="TRUE_LENGTH", PredefinedType="CONST")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=B1, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=grp)
    return grp

g_grp = carga_grupo("G", "PERMANENT_G", "DEAD_LOAD_G", G_kN_m)
q_grp = carga_grupo("Q", "VARIABLE_Q", "LIVE_LOAD_Q", Q_kN_m)
analysis.LoadedBy = [g_grp, q_grp]

f.write(OUT)
print("IFC caso 1 (ortodoxo) escrito en:", OUT)
print("  Portico S275: luz %.1f m, altura %.1f m  | pilares %s, dintel %s" % (S, Hc, HEB200["name"], IPE330["name"]))
print("  Cargas dintel: G=%.0f kN/m, Q=%.0f kN/m (gravedad -Z)" % (G_kN_m / 1e3, Q_kN_m / 1e3))
