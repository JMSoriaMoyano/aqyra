"""
CASO 11 - PANTALLA DE CORTANTE + SISMICO EC8 (modal / fuerzas laterales).
Primer caso de la SEGUNDA TANDA: abre la familia sismica.

IFC4 ORTODOXO. Sistema de estabilizacion lateral de un edificio de 5 plantas:
una PANTALLA de hormigon armado C30/37 trabajando a cortante en su plano,
empotrada en la base, con la MASA SISMICA de cada planta y los parametros del
espectro EC8. El agente debe:
  - leer la pantalla (IfcStructuralSurfaceMember vertical: Lw, H, tw, material),
  - leer las MASAS por planta (IfcStructuralPointAction, ForceZ = -W_planta, grupo
    "Sismo_masas") a sus cotas z, y la base empotrada (IfcBoundaryNodeCondition),
  - construir el voladizo equivalente (stick) con masas concentradas por planta,
  - resolver EC8: T1 y modos (analisis MODAL ESPECTRAL) y/o FUERZAS LATERALES
    equivalentes con el ESPECTRO de respuesta (parametros en Pset_Estructurando_Sismo),
    combinacion modal (SRSS/CQC), cortante basal, fuerzas por planta, deriva,
  - verificar la pantalla: cortante del alma + armadura, elementos de BORDE
    (EC8 5.4.3.4), N-M en la base, y DERIVA entre plantas (limitacion de dano).

Datos SIN entidad de analisis estandar -> Pset (igual que ks/Rd, conectores, etc.):
  Pantalla -> Pset_Estructurando_Pantalla (Lw, tw, H, n_plantas, h_planta, ductilidad)
  Sismo    -> Pset_Estructurando_Sismo (ag, suelo, espectro, q, gammaI, amort., lambda)

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z. Pantalla en
el plano XZ (longitud Lw en X, altura H en Z, espesor tw, normal Y).
"""
import os
import ifcopenshell
import ifcopenshell.guid

# --------- material ----------
C30 = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=32.84e9, nu=0.2, rho=2500.0, G=32.84e9 / 2.4)

# --------- datos del caso ----------
LW = 4.0          # longitud de la pantalla (m)
TW = 0.30         # espesor (m)
NP = 5            # numero de plantas
HP = 3.0          # altura entre plantas (m)
H = NP * HP       # altura total (m) = 15.0
# peso sismico por planta (G + psi2*Q tributario a la pantalla), kN -> N
W_PLANTA = [1200e3, 1200e3, 1200e3, 1200e3, 900e3]   # plantas 1..4 y cubierta

# parametros sismicos EC8 (Anejo Nacional Espana) [confirmar AN]
SISMO = {
    "Norma": "EC8 (EN 1998-1)",
    "ag_g": 0.20,           # aceleracion de calculo / g
    "TipoSuelo": "C",       # tipo de terreno EC8
    "TipoEspectro": 1,      # espectro tipo 1 (Ms > 5,5)
    "S": 1.15, "TB_s": 0.20, "TC_s": 0.60, "TD_s": 2.0,   # parametros del suelo C, tipo 1
    "ClaseImportancia": "II", "gammaI": 1.0,
    "q": 3.0,               # factor de comportamiento (DCM, sistema de muros)
    "amortiguamiento": 0.05,
    "lambda": 0.85,         # factor de correccion (>=3 plantas, T1<=2TC)
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-11.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(),
                Name="Caso 11 - Pantalla de cortante + sismico EC8",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    if isinstance(val, str):
        nominal = f.create_entity("IfcText", wrappedValue=val)
    elif isinstance(val, bool):
        nominal = f.create_entity("IfcBoolean", wrappedValue=val)
    elif isinstance(val, int):
        nominal = f.create_entity("IfcInteger", wrappedValue=val)
    else:
        nominal = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)


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
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def boolwrap(b):
    return f.create_entity("IfcBoolean", wrappedValue=b) if b else None


def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint",
                           VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))


def point_connection(name, x, y, z, bc=None):
    vp = vertex(x, y, z)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])])
    return f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
                           Representation=rep, AppliedCondition=bc)


def bc_fixed(apoyo):
    return f.create_entity("IfcBoundaryNodeCondition", Name="empotrado",
        TranslationalStiffnessX=boolwrap(apoyo[0]), TranslationalStiffnessY=boolwrap(apoyo[1]),
        TranslationalStiffnessZ=boolwrap(apoyo[2]), RotationalStiffnessX=boolwrap(apoyo[3]),
        RotationalStiffnessY=boolwrap(apoyo[4]), RotationalStiffnessZ=boolwrap(apoyo[5]))


def surface(name, pts4, t, mat, axis=(0., 1., 0.), refd=(1., 0., 0.)):
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
    sm = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name=name,
                         PredefinedType="SHELL", Thickness=t, Representation=rep)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[sm], RelatingMaterial=mat)
    return sm


def load_group(name):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP", ActionType="PERMANENT_G",
                           ActionSource="DEAD_LOAD_G", Coefficient=1.0)


def point_mass(name, node, w, group):
    # peso sismico de la planta como fuerza gravitatoria (ForceZ negativa); el motor
    # deriva la masa m = W/g y la usa en el analisis modal/espectral EC8.
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name + "_W",
                           ForceX=0.0, ForceY=0.0, ForceZ=-w, MomentX=0.0, MomentY=0.0, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=group)
    return act


analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Pantalla de cortante caso 11", PredefinedType="LOADING_3D")
gS = load_group("Sismo_masas")
objs = []

# --------- PANTALLA (superficie vertical en plano XZ) ----------
pant = surface("PANTALLA_cortante",
               [(0.0, 0.0, 0.0), (LW, 0.0, 0.0), (LW, 0.0, H), (0.0, 0.0, H)],
               TW, c30, axis=(0., 1., 0.), refd=(1., 0., 0.))
pset_for(pant, "Pset_Estructurando_Pantalla",
         {"Sistema": "pantalla_cortante", "Lw_m": LW, "tw_m": TW, "H_m": H,
          "n_plantas": NP, "h_planta_m": HP, "ClaseDuctilidad": "DCM", "Norma": "EC8"})
pset_for(pant, "Pset_Estructurando_Sismo", SISMO)
objs.append(pant)

# --------- nodos por planta (centro de la pantalla) + base empotrada ----------
xc = LW / 2.0
base = point_connection("PISO_0_base", xc, 0.0, 0.0, bc_fixed([True, True, True, True, True, True]))
objs.append(base)
for i in range(1, NP + 1):
    z = i * HP
    n = point_connection("PISO_%d" % i, xc, 0.0, z)
    point_mass("MASA_PISO_%d" % i, n, W_PLANTA[i - 1], gS)
    objs.append(n)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=objs, RelatingGroup=analysis)
analysis.LoadedBy = [gS]
f.write(OUT)
print("IFC caso 11 (ortodoxo, pantalla de cortante + sismo EC8) escrito en:", OUT)
print("  Pantalla C30/37 Lw=%.1f tw=%.2f H=%.1f m (%d plantas x %.1f m)" % (LW, TW, H, NP, HP))
print("  Masas sismicas por planta (kN):", [w / 1e3 for w in W_PLANTA], " Sum =", sum(W_PLANTA) / 1e3)
print("  EC8: ag=%.2fg suelo %s espectro %d q=%.1f gammaI=%.1f lambda=%.2f" % (
    SISMO["ag_g"], SISMO["TipoSuelo"], SISMO["TipoEspectro"], SISMO["q"], SISMO["gammaI"], SISMO["lambda"]))
