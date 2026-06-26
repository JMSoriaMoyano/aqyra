"""
CASO 4 - Cubierta / forjado INCLINADO (faldon de hormigon). IFC4 ORTODOXO del
dominio de analisis estructural: SUPERFICIE inclinada (normal NO vertical) +
apoyos lineales en alero y cumbrera.

Modelo (sintetico, realista):
  - Faldon de losa maciza de hormigon C30/37, espesor 0,20 m.
  - Geometria: ancho Lv = 8,0 m (eje X, horizontal) y longitud de faldon
    Lu = 6,0 m medida sobre la pendiente, con inclinacion theta = 30 grados.
    Esquinas en 3D (z != 0):
        alero    c0=(0, 0, 0)            c1=(8, 0, 0)
        cumbrera c3=(0, 5.196, 3.0)      c2=(8, 5.196, 3.0)
    (proyeccion horizontal del faldon = Lu*cos30 = 5,196 m; altura = Lu*sin30 = 3,0 m)
  - Apoyos LINEALES simplemente apoyados en alero (z=0) y cumbrera (z=3,0):
    nodos de esquina por IfcStructuralPointConnection + IfcBoundaryNodeCondition
    (alero: traslaciones coartadas; cumbrera: vertical + normal coartadas, giro libre).
  - Cargas de SUPERFICIE verticales (gravedad -Z, true-length):
      G = 6,0 kN/m2 (p.p. losa 0,20*25=5,0 + cubricion 1,0)
      Q = 1,0 kN/m2 (nieve, Cat. H cubiertas) [confirmar AN/zona]
  - El interes del caso: el peso sobre el plano inclinado genera FLEXION (normal al
    faldon) y ESFUERZOS DE MEMBRANA (componente en el plano del faldon).

Entidades ESTANDAR (sin Pset_Estructurando_*):
  - IfcStructuralSurfaceMember (Thickness=0,20; IfcFaceSurface/IfcPolyLoop con
    esquinas z!=0; IfcPlane con normal inclinada) + material por IfcRelAssociatesMaterial.
  - Nodos de alero/cumbrera por IfcStructuralPointConnection + IfcBoundaryNodeCondition.
  - Cargas: IfcStructuralLoadGroup (G,Q) + IfcStructuralSurfaceAction +
    IfcStructuralLoadPlanarForce (componente Z, gravedad).
Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import math
import ifcopenshell
import ifcopenshell.guid

LV = 8.0                 # ancho del faldon (eje X, horizontal)
LU = 6.0                 # longitud del faldon sobre la pendiente
THETA = 30.0             # inclinacion (grados)
T_LOSA = 0.20
DY = LU * math.cos(math.radians(THETA))   # proyeccion horizontal
DZ = LU * math.sin(math.radians(THETA))   # altura
CONC = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=33000e6, nu=0.2, rho=2500.0,
            G=33000e6 / (2 * (1 + 0.2)))
G_kN_m2 = 6.0e3
Q_kN_m2 = 1.0e3

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-04.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 4 - Cubierta inclinada",
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

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Cubierta inclinada caso 4", PredefinedType="LOADING_3D")


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


# Apoyos: alero (fijo XYZ) y cumbrera (Z + lateral, giro libre)
PIN = [True, True, True, False, False, False]
ROL = [False, True, True, False, False, False]
n0, v0, p0 = nodo("A1", 0.0, 0.0, 0.0, PIN)    # alero izq
n1, v1, p1 = nodo("A2", LV, 0.0, 0.0, PIN)     # alero der
n2, v2, p2 = nodo("C2", LV, DY, DZ, ROL)       # cumbrera der
n3, v3, p3 = nodo("C1", 0.0, DY, DZ, ROL)      # cumbrera izq
all_objs = [n0, n1, n2, n3]

# --- Faldon: IfcStructuralSurfaceMember (cara con poligono de esquinas z!=0) ---
poly = f.create_entity("IfcPolyLoop", Polygon=[p0, p1, p2, p3])
bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
# normal del plano del faldon (perpendicular a la superficie inclinada)
nz = math.cos(math.radians(THETA)); ny = -math.sin(math.radians(THETA))
plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)),
            Axis=f.create_entity("IfcDirection", DirectionRatios=(0., ny, nz)),
            RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
face = f.create_entity("IfcFaceSurface", Bounds=[bound], FaceSurface=plane, SameSense=True)
rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
FALDON = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="Faldon",
                         PredefinedType="SHELL", Thickness=T_LOSA, Representation=rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                RelatedObjects=[FALDON], RelatingMaterial=conc)
all_objs.append(FALDON)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=all_objs, RelatingGroup=analysis)


def carga_superficie(nombre, action_type, action_source, q):
    grp = f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=nombre,
                          PredefinedType="LOAD_GROUP", ActionType=action_type,
                          ActionSource=action_source, Coefficient=1.0)
    load = f.create_entity("IfcStructuralLoadPlanarForce", Name=nombre + "_q",
                           PlanarForceX=0.0, PlanarForceY=0.0, PlanarForceZ=-q)
    act = f.create_entity("IfcStructuralSurfaceAction", GlobalId=guid(), Name=nombre + "_faldon",
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          ProjectedOrTrue="TRUE_LENGTH", PredefinedType="CONST")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=FALDON, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=grp)
    return grp


g_grp = carga_superficie("G", "PERMANENT_G", "DEAD_LOAD_G", G_kN_m2)
q_grp = carga_superficie("Q", "VARIABLE_Q", "SNOW_S", Q_kN_m2)
analysis.LoadedBy = [g_grp, q_grp]

f.write(OUT)
print("IFC caso 4 (ortodoxo) escrito en:", OUT)
print("  Faldon %.1f x %.1f m | C30/37 t=%.0f mm | theta=%.0f deg | esquinas z=0..%.2f m" % (
    LV, LU, T_LOSA * 1000, THETA, DZ))
print("  Cargas: G=%.1f Q=%.1f kN/m2 (true-length)" % (G_kN_m2 / 1e3, Q_kN_m2 / 1e3))
area_real = LV * LU
qELU = (1.35 * G_kN_m2 + 1.5 * Q_kN_m2)
print("  Carga total ELU ~ %.0f kN (area real %.1f m2)" % (qELU * area_real / 1e3, area_real))
