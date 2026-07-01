"""
CASO 14 - VIGA POSTESADA HIPERESTATICA (continua, 2 vanos) (EC2 §5.10).
Cuarto caso de la SEGUNDA TANDA: lleva el PRETENSADO a estructuras HIPERESTATICAS.

IFC4 ORTODOXO. Viga postesada CONTINUA de dos vanos de un forjado/estructura de
aparcamiento, hormigon C40/50, seccion rectangular b=0.50 x h=1.30 m, dos vanos
de L=20.0 m (total 40 m, L/h=15.4), apoyada en 3 apoyos: dos extremos
(articulados) y uno central (introduce la hiperestaticidad). Postesado adherente
con tendon parabolico continuo por vano (14 cordones Y1860S7 0.6", Ap=2100 mm2).

  - Geometria/seccion/material -> via estandar (IfcStructuralCurveMember +
    IfcRectangleProfileDef via IfcMaterialProfileSet, C40/50).
  - 3 apoyos -> IfcStructuralPointConnection + IfcBoundaryNodeCondition.
  - Cargas g2/q -> IfcStructuralCurveAction + IfcStructuralLoadGroup.
  - Pretensado -> Pset_Estructurando_Pretensado del curve member (trazado
    parabolico POR VANO: e en vanos, e sobre el apoyo central, drape, P/sigma,
    mu/k, penetracion de cuna, relajacion).

Trazado (excentricidad e positiva HACIA ABAJO; c.d.g. a 0.65 m de cada fibra):
  - e=0 en los apoyos extremos (anclaje en c.d.g.),
  - e=+0.30 m (hacia abajo) en centro de vano,
  - e=-0.30 m (hacia arriba) sobre el apoyo central.
  Drape de vano a=0.45 m -> w_p = 8*P*a/L^2 equilibra la permanente g0+g2=21.25
  kN/m con P_m,inf = 2344 kN (14 cordones, sigma_pm,inf=0.60*fpk=1116 MPa).
  [El enunciado original sugeria e=+/-0.50; se REFINA a +/-0.30 para que el
   balance equilibre la permanente con residual ~0 (a=0.50 sobre-equilibraria).]

Unidades SI (m, N, Pa). Eje de la viga en X, Z vertical, gravedad -Z.
"""
import os
import math
import ifcopenshell
import ifcopenshell.guid

# --------- material ----------
# C40/50: fck=40 MPa, fcm=48, Ecm=35 GPa, fctm=3.5 MPa, fck(t)=32 MPa (transferencia)
C40 = dict(name="C40/50", fck=40e6, fctm=3.5e6, fck_t=32e6, E=35e9, nu=0.2,
           rho=2500.0, G=35e9 / 2.4)

# --------- geometria del caso ----------
B = 0.50          # ancho de la seccion (m)
H = 1.30          # canto de la seccion (m)
L = 20.0          # luz de cada vano (m)
NV = 2            # numero de vanos

# --------- cargas (kN/m -> N/m) ----------
G2 = 5.0e3        # carga muerta (N/m)
Q = 12.0e3        # sobrecarga de uso (N/m)
PSI2 = 0.3        # coef. cuasipermanente de la sobrecarga

# --------- pretensado (Pset) ----------
# 14 cordones Y1860S7 0.6" (Ap=150 mm2/cordon -> 2100 mm2).
# sigma_pm,inf = 0.60*fpk = 1116 MPa -> P_m,inf = 1116*2100/1000 = 2343.6 kN.
# Balance de la permanente g0+g2=21.25 kN/m con drape a=0.45 m:
#   w_p = 8*P*a/L^2 = 8*2343.6*0.45/400 = 21.09 kN/m ~ 21.25 (residual ~-0.7%).
# Transferencia sigma_p0 = 0.72*fpk = 1339 MPa -> P0 = 1339*2100/1000 = 2811 kN.
PRET = {
    "Norma": "EC2 (EN 1992-1-1) §5.10",
    "Sistema": "postesado_adherente",
    "tipo_estructura": "viga_continua_2vanos",
    "n_tendones": 1,
    "n_cordones": 14,
    "tipo_cordon": "Y1860S7 0.6\"",
    "Ap_mm2": 2100.0,            # area de acero activo (mm2) = 14*150
    "fpk_MPa": 1860.0,           # resistencia caracteristica del acero activo
    "fp01k_MPa": 1640.0,         # limite elastico convencional 0.1%
    "Ep_GPa": 195.0,             # modulo del acero activo
    "P0_kN": 2811.0,             # fuerza de tesado en transferencia (tras perd. inst.)
    "sigma_p0_MPa": 1339.0,      # tension del acero en transferencia (~0.72 fpk)
    "Pm_inf_kN": 2343.6,         # fuerza media tras perdidas diferidas
    "sigma_pm_inf_MPa": 1116.0,  # 0.60 fpk
    "trazado": "parabolico_por_vano",
    # trazado por vano (m, e positiva hacia abajo):
    "e_apoyo_ext_m": 0.0,        # excentricidad en apoyos extremos (anclaje c.d.g.)
    "e_centro_vano_m": 0.30,     # excentricidad en centro de vano (hacia abajo)
    "e_apoyo_central_m": -0.30,  # excentricidad sobre el apoyo central (hacia arriba)
    "drape_vano_m": 0.45,        # flecha (drape) efectiva de la parabola de vano
    "recubrimiento_mec_m": 0.15, # recubrimiento mecanico del tendon
    # coeficientes de perdidas [confirmar AN]
    "mu_rozamiento": 0.19,       # coef. de rozamiento en curva (rad^-1)
    "k_desviacion": 0.01,        # rozamiento parasito (m^-1)
    "penetracion_cuna_mm": 6.0,  # penetracion de cuna en el anclaje
    "relajacion_clase": 2,       # clase 2 (baja relajacion)
    "rho1000_pct": 2.5,          # relajacion a 1000 h (clase 2)
    "tesado": "dos_extremos",
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-14.ifc")

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
                Name="Caso 14 - Viga postesada hiperestatica continua (EC2 5.10)",
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
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical",
                    Material=m, Properties=props)
    return m


c40 = material(C40, [prop("CompressiveStrength", C40["fck"]),
                     prop("TensileStrength", C40["fctm"])])


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def boolwrap(b):
    return f.create_entity("IfcBoolean", wrappedValue=b) if b else None


def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint",
                           VertexGeometry=f.create_entity("IfcCartesianPoint",
                                                          Coordinates=(x, y, z)))


def point_connection(name, x, y, z, bc=None):
    vp = vertex(x, y, z)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference",
                        RepresentationType="Vertex", Items=[vp])])
    return f.create_entity("IfcStructuralPointConnection", GlobalId=guid(),
                           Name=name, Representation=rep, AppliedCondition=bc)


def bc_support(apoyo):
    return f.create_entity("IfcBoundaryNodeCondition", Name="apoyo",
        TranslationalStiffnessX=boolwrap(apoyo[0]),
        TranslationalStiffnessY=boolwrap(apoyo[1]),
        TranslationalStiffnessZ=boolwrap(apoyo[2]),
        RotationalStiffnessX=boolwrap(apoyo[3]),
        RotationalStiffnessY=boolwrap(apoyo[4]),
        RotationalStiffnessZ=boolwrap(apoyo[5]))


def rect_profile(name, b, h):
    pos = f.create_entity("IfcAxis2Placement2D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.)))
    return f.create_entity("IfcRectangleProfileDef", ProfileType="AREA",
                           ProfileName=name, Position=pos, XDim=b, YDim=h)


def curve_member(name, x0, x1, z, profile, mat):
    p0 = f.create_entity("IfcCartesianPoint", Coordinates=(x0, 0.0, z))
    p1 = f.create_entity("IfcCartesianPoint", Coordinates=(x1, 0.0, z))
    poly = f.create_entity("IfcPolyline", Points=[p0, p1])
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference",
                        RepresentationType="Edge", Items=[poly])])
    cm = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name=name,
                         PredefinedType="RIGID_JOINED_MEMBER", Representation=rep)
    mps = f.create_entity("IfcMaterialProfile", Name=name + "_sec",
                          Material=mat, Profile=profile)
    mpset = f.create_entity("IfcMaterialProfileSet", Name=name + "_secset",
                            MaterialProfiles=[mps])
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                    RelatedObjects=[cm], RelatingMaterial=mpset)
    return cm


def load_group(name, action_type, source):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP", ActionType=action_type,
                           ActionSource=source, Coefficient=1.0)


def curve_action(name, member, wz, group):
    load = f.create_entity("IfcStructuralLoadLinearForce", Name=name + "_q",
                           LinearForceX=0.0, LinearForceY=0.0, LinearForceZ=-wz,
                           LinearMomentX=0.0, LinearMomentY=0.0, LinearMomentZ=0.0)
    act = f.create_entity("IfcStructuralCurveAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          ProjectedOrTrue="TRUE_LENGTH")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=member, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                    RelatedObjects=[act], RelatingGroup=group)
    return act


analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Viga postesada continua caso 14", PredefinedType="LOADING_3D")
gPerm = load_group("Cargas_muertas_g2", "PERMANENT_G", "DEAD_LOAD_G")
gVar = load_group("Sobrecarga_uso_q", "VARIABLE_Q", "LIVE_LOAD_Q")
objs = []

# --------- VIGA CONTINUA: 2 curve members (vano 1 y vano 2) ----------
prof = rect_profile("RECT_500x1300", B, H)
vano1 = curve_member("VIGA_vano1", 0.0, L, 0.0, prof, c40)
vano2 = curve_member("VIGA_vano2", L, 2.0 * L, 0.0, prof, c40)
# el Pset de pretensado describe el trazado continuo (mismo en ambos vanos)
pset_for(vano1, "Pset_Estructurando_Pretensado", PRET)
pset_for(vano2, "Pset_Estructurando_Pretensado", PRET)
objs.extend([vano1, vano2])

# --------- apoyos (continua de 2 vanos: 3 apoyos) ----------
# extremo x=0 fijo (Ux,Uy,Uz); central x=L (Uy,Uz); extremo x=2L (Uy,Uz).
# Rotacion de flexion Ry libre en los 3 (apoyos simples).
ap0 = point_connection("APOYO_ext_0", 0.0, 0.0, 0.0,
                       bc_support([True, True, True, False, False, True]))
apC = point_connection("APOYO_central", L, 0.0, 0.0,
                       bc_support([False, True, True, False, False, True]))
ap2 = point_connection("APOYO_ext_2", 2.0 * L, 0.0, 0.0,
                       bc_support([False, True, True, False, False, True]))
objs.extend([ap0, apC, ap2])

# --------- cargas g2 y q (via ortodoxa) en ambos vanos ----------
curve_action("g2_carga_muerta_v1", vano1, G2, gPerm)
curve_action("g2_carga_muerta_v2", vano2, G2, gPerm)
curve_action("q_sobrecarga_v1", vano1, Q, gVar)
curve_action("q_sobrecarga_v2", vano2, Q, gVar)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=objs,
                RelatingGroup=analysis)
analysis.LoadedBy = [gPerm, gVar]
f.write(OUT)

# resumen
A = B * H
I = B * H ** 3 / 12.0
W = I / (H / 2.0)
g0 = A * 25.0   # kN/m (el solver usa A*25, gamma_c=25 kN/m3 EC2/EHE)
wp = 8.0 * PRET["Pm_inf_kN"] * PRET["drape_vano_m"] / L ** 2
print("IFC caso 14 (ortodoxo, viga postesada CONTINUA 2 vanos EC2 5.10) escrito en:", OUT)
print("  Viga C40/50  b=%.2f h=%.2f  2 vanos de L=%.1f m (total %.0f m, L/h=%.1f)" % (
    B, H, L, NV * L, L / H))
print("  A=%.4f m2  I=%.5f m4  W=%.5f m3  g0=A*25=%.2f kN/m" % (A, I, W, g0))
print("  Cargas: g2=%.1f kN/m  q=%.1f kN/m (psi2=%.1f)" % (G2 / 1e3, Q / 1e3, PSI2))
print("  Pretensado: P0=%.0f kN  Pm,inf=%.0f kN  Ap=%.0f mm2  %s" % (
    PRET["P0_kN"], PRET["Pm_inf_kN"], PRET["Ap_mm2"], PRET["tipo_cordon"]))
print("  Trazado: e_vano=+%.2f m  e_apoyo_central=%.2f m  drape a=%.2f m" % (
    PRET["e_centro_vano_m"], PRET["e_apoyo_central_m"], PRET["drape_vano_m"]))
print("  Balance: w_p=8*P*a/L^2=%.2f kN/m  vs permanente g0+g2=%.2f kN/m (residual %.1f%%)" % (
    wp, g0 + G2 / 1e3, 100.0 * (wp - (g0 + G2 / 1e3)) / (g0 + G2 / 1e3)))
