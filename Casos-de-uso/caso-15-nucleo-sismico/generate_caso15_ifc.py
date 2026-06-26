"""
CASO 15 - NUCLEO DE PANTALLAS ACOPLADAS + SISMICO EC8 (PT 1.5, Ola 1).
Extiende el caso 11 (pantalla aislada) al NUCLEO EN U ABIERTO (canal):
  - ALMA partida por una puerta en dos machones (P1, P2) ACOPLADOS por un
    dintel en cada planta (muros acoplados, DCM).
  - Dos ALAS (F1, F2) que dan la rigidez en X.
  - Seccion ABIERTA -> centro de rigidez CR != centro de masa CM -> torsion.
IFC4 ORTODOXO. SI (m, N, Pa). XY horizontal, Z vertical, gravedad -Z.

Cada pantalla = IfcStructuralSurfaceMember vertical (plano YZ los machones,
plano XZ las alas). Masas de planta = IfcStructuralPointAction (ForceZ=-W) en
el nodo maestro de diafragma (CM) de cada planta, grupo "Sismo_masas".
Datos sin entidad de analisis estandar -> Pset (igual que caso 11):
  por pantalla -> Pset_Estructurando_Pantalla (Rol, Lw, tw, H, ResisteDir, ParAcoplado)
  global       -> Pset_Estructurando_Sismo  (ag, suelo, espectro, q=3.6, lambda)
                  Pset_Estructurando_Nucleo (dintel b/h/ln, abertura, dir. acopl.,
                                              plano de edificio Lx/Ly, tipologia)
"""
import os, ifcopenshell, ifcopenshell.guid

C30 = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=32.84e9, nu=0.2, rho=2500.0, G=32.84e9/2.4)
TW = 0.30; NP = 6; HP = 3.0; H = NP*HP            # 6 plantas x 3.0 = 18 m
W_PLANTA = [700e3, 700e3, 700e3, 700e3, 700e3, 500e3]   # N (G + psi2*Q tributario, torre compacta sobre nucleo)

# --- geometria del nucleo en U (planta), edificio compacto 8 x 8 m, nucleo casi-pleno ---
EDIF_LX, EDIF_LY = 8.0, 8.0
CMx, CMy = 4.0, 4.0                                # centro de masa = centro de planta
XW = 3.4                                           # plano del alma (machones); CR_x=3.4 -> e0x=0.6
DEPTH = 4.0; XFA, XFB = XW, XW + DEPTH             # alas x[3.4,7.4] (Lw=4.0)
LW_PIER = 2.0; DOOR = 1.4                           # machon 2.0 m + puerta 1.4 m
# P1 y[1.3,3.3], P2 y[4.7,6.7]; puerta y[3.3,4.7]
P1Y0 = CMy - (DOOR/2 + LW_PIER); P2Y0 = CMy + DOOR/2
LW_FLA = XFB - XFA                                  # 4.0
YF1, YF2 = 1.3, 6.7                                 # alas (extremos del nucleo en Y)
DINTEL = dict(b=0.30, h=0.70, ln=DOOR)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-15.ifc")
f = ifcopenshell.file(schema="IFC4"); guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
    CoordinateSpaceDimension=3, Precision=1e-5,
    WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.,0.,0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 15 - Nucleo de pantallas acopladas + sismico EC8",
    UnitsInContext=ua, RepresentationContexts=[ctx])

def prop(name, val):
    if isinstance(val, bool): nv = f.create_entity("IfcBoolean", wrappedValue=val)
    elif isinstance(val, str): nv = f.create_entity("IfcText", wrappedValue=val)
    elif isinstance(val, int): nv = f.create_entity("IfcInteger", wrappedValue=val)
    else: nv = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nv)

def material(M, extra):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    props = [prop("YoungModulus", M["E"]), prop("ShearModulus", M["G"]),
             prop("PoissonRatio", M["nu"]), prop("MassDensity", M["rho"])] + extra
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m
c30 = material(C30, [prop("CompressiveStrength", C30["fck"]), prop("TensileStrength", C30["fctm"])])

def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
        HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(), RelatedObjects=[obj], RelatingPropertyDefinition=ps)

def boolwrap(b): return f.create_entity("IfcBoolean", wrappedValue=b) if b else None
def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x,y,z)))
def point_connection(name, x, y, z, bc=None):
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vertex(x,y,z)])])
    return f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name, Representation=rep, AppliedCondition=bc)
def bc_fixed(a):
    return f.create_entity("IfcBoundaryNodeCondition", Name="empotrado",
        TranslationalStiffnessX=boolwrap(a[0]), TranslationalStiffnessY=boolwrap(a[1]),
        TranslationalStiffnessZ=boolwrap(a[2]), RotationalStiffnessX=boolwrap(a[3]),
        RotationalStiffnessY=boolwrap(a[4]), RotationalStiffnessZ=boolwrap(a[5]))
def surface(name, pts4, t, mat, axis, refd):
    poly = f.create_entity("IfcPolyLoop", Polygon=[f.create_entity("IfcCartesianPoint", Coordinates=c) for c in pts4])
    bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
    plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=pts4[0]),
        Axis=f.create_entity("IfcDirection", DirectionRatios=axis),
        RefDirection=f.create_entity("IfcDirection", DirectionRatios=refd)))
    face = f.create_entity("IfcFaceSurface", Bounds=[bound], FaceSurface=plane, SameSense=True)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
    sm = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name=name, PredefinedType="SHELL", Thickness=t, Representation=rep)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[sm], RelatingMaterial=mat)
    return sm
def load_group(name):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
        PredefinedType="LOAD_GROUP", ActionType="PERMANENT_G", ActionSource="DEAD_LOAD_G", Coefficient=1.0)
def point_mass(name, node, w, group):
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name+"_W",
        ForceX=0.0, ForceY=0.0, ForceZ=-w, MomentX=0.0, MomentY=0.0, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name, AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(), RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=group)
    return act

SISMO = {"Norma": "EC8 (EN 1998-1)", "ag_g": 0.20, "TipoSuelo": "C", "TipoEspectro": 1,
    "S": 1.15, "TB_s": 0.20, "TC_s": 0.60, "TD_s": 2.0, "ClaseImportancia": "II", "gammaI": 1.0,
    "q": 3.6, "amortiguamiento": 0.05, "lambda": 0.85}
NUCLEO = {"Tipologia": "nucleo_U_abierto", "Dintel_b_m": DINTEL["b"], "Dintel_h_m": DINTEL["h"],
    "Dintel_ln_m": DINTEL["ln"], "Dinteles_por_planta": 1, "AberturaPuerta_m": DOOR,
    "DireccionAcoplamiento": "Y", "Edificio_Lx_m": EDIF_LX, "Edificio_Ly_m": EDIF_LY,
    "CM_x_m": CMx, "CM_y_m": CMy, "ClaseDuctilidad": "DCM"}

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(), Name="Nucleo en U caso 15", PredefinedType="LOADING_3D")
gS = load_group("Sismo_masas"); objs = []

# pantallas: (name, pts4, axis, refd, rol, Lw, resiste, par)
walls = [
  ("ALMA_P1", [(XW,P1Y0,0.),(XW,P1Y0+LW_PIER,0.),(XW,P1Y0+LW_PIER,H),(XW,P1Y0,H)], (1.,0.,0.), (0.,1.,0.), "alma_pier", LW_PIER, "Y", "ALMA"),
  ("ALMA_P2", [(XW,P2Y0,0.),(XW,P2Y0+LW_PIER,0.),(XW,P2Y0+LW_PIER,H),(XW,P2Y0,H)], (1.,0.,0.), (0.,1.,0.), "alma_pier", LW_PIER, "Y", "ALMA"),
  ("ALA_F1",  [(XFA,YF1,0.),(XFB,YF1,0.),(XFB,YF1,H),(XFA,YF1,H)], (0.,1.,0.), (1.,0.,0.), "ala", LW_FLA, "X", ""),
  ("ALA_F2",  [(XFA,YF2,0.),(XFB,YF2,0.),(XFB,YF2,H),(XFA,YF2,H)], (0.,1.,0.), (1.,0.,0.), "ala", LW_FLA, "X", ""),
]
for (nm, pts, ax, rd, rol, lw, resd, par) in walls:
    sm = surface(nm, pts, TW, c30, ax, rd)
    pset_for(sm, "Pset_Estructurando_Pantalla", {"Sistema": "nucleo_pantallas", "Rol": rol,
        "Lw_m": lw, "tw_m": TW, "H_m": H, "n_plantas": NP, "h_planta_m": HP,
        "ClaseDuctilidad": "DCM", "ResisteDir": resd, "ParAcoplado": par})
    pset_for(sm, "Pset_Estructurando_Sismo", SISMO)
    pset_for(sm, "Pset_Estructurando_Nucleo", NUCLEO)
    # base empotrada de cada pantalla (en su linea media de planta)
    cx = sum(p[0] for p in pts[:2])/2.0; cy = sum(p[1] for p in pts[:2])/2.0
    base = point_connection("BASE_%s" % nm, cx, cy, 0.0, bc_fixed([True]*6))
    objs += [sm, base]

# nodos maestros de diafragma (CM) por planta + masa
for i in range(1, NP+1):
    z = i*HP
    n = point_connection("DIAFRAGMA_%d" % i, CMx, CMy, z)
    point_mass("MASA_PISO_%d" % i, n, W_PLANTA[i-1], gS)
    objs.append(n)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=objs, RelatingGroup=analysis)
analysis.LoadedBy = [gS]
f.write(OUT)
print("IFC caso 15 escrito en:", OUT)
print("  Nucleo U: 2 machones (alma) Lw=%.1f + 2 alas Lw=%.1f, tw=%.2f, H=%.0f (%d x %.1f)" % (LW_PIER, LW_FLA, TW, H, NP, HP))
print("  Masas (kN):", [w/1e3 for w in W_PLANTA], " Sum=%.0f kN" % (sum(W_PLANTA)/1e3))
print("  EC8 q=%.1f suelo %s ag=%.2fg lambda=%.2f | Edificio %.0fx%.0f CM(%.1f,%.1f)" % (
    SISMO["q"], SISMO["TipoSuelo"], SISMO["ag_g"], SISMO["lambda"], EDIF_LX, EDIF_LY, CMx, CMy))
