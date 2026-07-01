"""
CASO 3 - Losa plana (forjado de losa maciza) sobre pilares. IFC4 ORTODOXO del
dominio de analisis estructural: SUPERFICIE (losa) + apoyos PUNTUALES (pilares).

Modelo (sintetico, realista):
  - Losa maciza de hormigon C30/37, espesor 0,28 m, en planta 10,0 x 10,0 m
    (dos vanos x dos vanos de 5,0 m), plano XY, z=0.
  - 9 pilares de hormigon C30/37, seccion 0,40 x 0,40 m, altura 3,0 m, en una
    retícula 3x3 a x,y = {0, 5, 10} m. Empotrados en su base (z=-3,0).
  - Cargas de SUPERFICIE sobre la losa (gravedad -Z):
      G = 8,5 kN/m2 (p.p. losa 0,28*25=7,0 + solado/tabiqueria 1,5)
      Q = 3,0 kN/m2 (sobrecarga de uso, Cat. B)
  - El PILAR INTERIOR (5,5) es el critico a punzonamiento (EC2 6.4).

Entidades ESTANDAR (sin Pset_Estructurando_*):
  - IfcStructuralSurfaceMember (Thickness=0,28; IfcFaceSurface/IfcPolyLoop) +
    material C30/37 por IfcRelAssociatesMaterial.
  - Pilares: IfcStructuralCurveMember (IfcEdge base->cabeza) + IfcMaterialProfileSet
    -> IfcRectangleProfileDef (0,40x0,40) + IfcRelAssociatesMaterial (C30/37).
  - Nodos cabeza (z=0) y base (z=-3,0, empotrados) por IfcStructuralPointConnection
    + IfcBoundaryNodeCondition.
  - Cargas: IfcStructuralLoadGroup (G,Q) + IfcStructuralSurfaceAction +
    IfcStructuralLoadPlanarForce.
Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

LADO = 10.0          # planta de la losa (m)
VANO = 5.0           # separacion entre pilares (m)
T_LOSA = 0.28
H_PILAR = 3.0
COL = dict(name="C 400x400", b=0.40, h=0.40)
CONC = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=33000e6, nu=0.2, rho=2500.0,
            G=33000e6 / (2 * (1 + 0.2)))
G_kN_m2 = 8.5e3
Q_kN_m2 = 3.0e3
GRID = [0.0, VANO, LADO]   # x,y de los pilares

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-03.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 3 - Losa plana sobre pilares",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    return f.create_entity("IfcPropertySingleValue", Name=name,
                           NominalValue=f.create_entity("IfcReal", wrappedValue=float(val)))


conc = f.create_entity("IfcMaterial", Name=CONC["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=conc,
                Properties=[prop("YoungModulus", CONC["E"]), prop("ShearModulus", CONC["G"]),
                            prop("PoissonRatio", CONC["nu"]), prop("MassDensity", CONC["rho"]),
                            prop("CompressiveStrength", CONC["fck"]),
                            prop("TensileStrength", CONC["fctm"])])

# perfil rectangular de pilar
rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=COL["name"],
                       XDim=COL["b"], YDim=COL["h"])
mprof = f.create_entity("IfcMaterialProfile", Name=COL["name"], Material=conc, Profile=rect)
mps_col = f.create_entity("IfcMaterialProfileSet", Name=COL["name"], MaterialProfiles=[mprof])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Losa plana caso 3", PredefinedType="LOADING_3D")


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


FIX = [True, True, True, True, True, True]   # base empotrada
heads = []
cols = []
all_objs = []
k = 0
for j, y in enumerate(GRID):
    for i, x in enumerate(GRID):
        k += 1
        nh, vh, ph = nodo("H%d" % k, x, y, 0.0)         # cabeza de pilar
        nb, vb, pb = nodo("B%d" % k, x, y, -H_PILAR, FIX)  # base empotrada
        edge = f.create_entity("IfcEdge", EdgeStart=vb, EdgeEnd=vh)
        rep = f.create_entity("IfcProductDefinitionShape", Representations=[
            f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                            RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])])
        col = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="P%d" % k,
                              PredefinedType="RIGID_JOINED_MEMBER",
                              Axis=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.)),
                              Representation=rep)
        f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                        RelatedObjects=[col], RelatingMaterial=mps_col)
        heads.append((nh, ph)); cols.append(col)
        all_objs += [nh, nb, col]


# --- Losa: IfcStructuralSurfaceMember (cara con poligono de esquinas) ---
c0 = f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))
c1 = f.create_entity("IfcCartesianPoint", Coordinates=(LADO, 0., 0.))
c2 = f.create_entity("IfcCartesianPoint", Coordinates=(LADO, LADO, 0.))
c3 = f.create_entity("IfcCartesianPoint", Coordinates=(0., LADO, 0.))
poly = f.create_entity("IfcPolyLoop", Polygon=[c0, c1, c2, c3])
bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)),
            Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
            RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
face = f.create_entity("IfcFaceSurface", Bounds=[bound], FaceSurface=plane, SameSense=True)
rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
LOSA = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="Losa",
                       PredefinedType="SHELL", Thickness=T_LOSA, Representation=rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                RelatedObjects=[LOSA], RelatingMaterial=conc)
all_objs.append(LOSA)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=all_objs, RelatingGroup=analysis)


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
print("IFC caso 3 (ortodoxo) escrito en:", OUT)
print("  Losa plana %.1f x %.1f m | C30/37 t=%.0f mm | 9 pilares %s sobre reticula %s m" % (
    LADO, LADO, T_LOSA * 1000, COL["name"], GRID))
print("  Cargas: G=%.1f Q=%.1f kN/m2" % (G_kN_m2 / 1e3, Q_kN_m2 / 1e3))
VEd = (1.35 * G_kN_m2 + 1.5 * Q_kN_m2) * VANO * VANO / 1e3
print("  V_Ed (pilar interior, tributario %.0f m2) ~ %.0f kN (ELU)" % (VANO * VANO, VEd))
