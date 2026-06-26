"""
CASO 12 - VIGA POSTESADA ISOSTATICA (EC2 §5.10).
Segundo caso de la SEGUNDA TANDA: abre la tipologia de elementos PRETENSADOS.

IFC4 ORTODOXO. Viga simplemente apoyada de gran luz de un forjado/cubierta,
hormigon C40/50, seccion rectangular b=0.50 x h=1.30 m, L=20.0 m, postesada con
un tendon parabolico (13 cordones Y1860S7, Ap=1950 mm2), conducto inyectado
(adherente). El agente debe:
  - leer la viga (IfcStructuralCurveMember + IfcRectangleProfileDef + material),
  - leer apoyos (IfcStructuralPointConnection + IfcBoundaryNodeCondition),
  - leer cargas g2/q (IfcStructuralCurveAction + IfcStructuralLoadGroup),
  - leer el PRETENSADO del Pset_Estructurando_Pretensado (P0/sigma_p0, Ap, fpk,
    trazado parabolico/e, conducto, coeficientes de perdidas, anclajes),
  - idealizar la viga isostatica biapoyada,
  - resolver EC2 §5.10: pretensado como cargas equivalentes (load balancing) y
    como fuerza+excentricidad, perdidas instantaneas y diferidas, combinaciones,
  - verificar: tensiones en transferencia y servicio por fibras, ELU de flexion
    por fibras (activa+pasiva), fisuracion, cortante con pretensado.

Datos SIN entidad de analisis estandar -> Pset (igual que ks/Rd, conectores,
terreno, sismo de casos 5/6/7/9/11):
  Viga       -> seccion/material por la via estandar.
  Pretensado -> Pset_Estructurando_Pretensado.

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
L = 20.0          # luz (m)

# --------- cargas (kN/m -> N/m) ----------
G2 = 5.0e3        # carga muerta (N/m)
Q = 12.0e3        # sobrecarga de uso (N/m)
PSI2 = 0.3        # coef. cuasipermanente de la sobrecarga

# --------- pretensado (Pset) ----------
# Fuerza media tras perdidas diferidas P_m,inf y fuerza en transferencia P0.
# Load balancing de la permanente g0+g2=21.25 kN/m con flecha e=0.50:
#   P_m,inf = (g0+g2)*L^2/(8*e) = 21.25*400/4 = 2125 kN.
#   P0 = P_m,inf/(1-perdidas_dif) con perdidas_dif ~ 16% totales sobre tesado.
PRET = {
    "Norma": "EC2 (EN 1992-1-1) §5.10",
    "Sistema": "postesado_adherente",
    "n_tendones": 1,
    "n_cordones": 13,
    "tipo_cordon": "Y1860S7 0.6\"",
    "Ap_mm2": 1950.0,           # area de acero activo (mm2)
    "fpk_MPa": 1860.0,          # resistencia caracteristica del acero activo
    "fp01k_MPa": 1640.0,        # limite elastico convencional 0.1%
    "Ep_GPa": 195.0,            # modulo del acero activo
    "P0_kN": 2535.0,            # fuerza de tesado en transferencia (tras perd. inst.)
    "sigma_p0_MPa": 1300.0,     # tension del acero en transferencia (~0.70 fpk)
    "Pm_inf_kN": 2125.0,        # fuerza media tras perdidas diferidas
    "sigma_pm_inf_MPa": 1089.7, # ~0.59 fpk
    "trazado": "parabolico",
    "e_centro_m": 0.50,         # excentricidad en centro de vano (hacia abajo)
    "e_apoyo_m": 0.0,           # excentricidad en apoyos (anclaje en c.d.g.)
    "recubrimiento_mec_m": 0.15,  # recubrimiento mecanico del tendon al fondo
    # coeficientes de perdidas [confirmar AN]
    "mu_rozamiento": 0.19,      # coef. de rozamiento en curva (rad^-1)
    "k_desviacion": 0.01,       # rozamiento parasito (m^-1)
    "penetracion_cuna_mm": 6.0, # penetracion de cuna en el anclaje
    "relajacion_clase": 2,      # clase 2 (baja relajacion)
    "rho1000_pct": 2.5,         # relajacion a 1000 h (clase 2)
    "tesado": "dos_extremos",
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-12.ifc")

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
                Name="Caso 12 - Viga postesada isostatica (EC2 5.10)",
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
    # asociar el perfil como material-profile-set (via estandar de seccion)
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
    # carga lineal gravitatoria (LinearForceZ negativa, N/m) sobre la viga.
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
                           Name="Viga postesada caso 12", PredefinedType="LOADING_3D")
gPerm = load_group("Cargas_muertas_g2", "PERMANENT_G", "DEAD_LOAD_G")
gVar = load_group("Sobrecarga_uso_q", "VARIABLE_Q", "LIVE_LOAD_Q")
objs = []

# --------- VIGA (curve member horizontal en X) ----------
prof = rect_profile("RECT_500x1300", B, H)
viga = curve_member("VIGA_postesada", 0.0, L, 0.0, prof, c40)
pset_for(viga, "Pset_Estructurando_Pretensado", PRET)
objs.append(viga)

# --------- apoyos (isostatico biapoyado) ----------
# x=0 fijo (Ux,Uy,Uz), x=L movil (Uy,Uz). Rotacion libre (giro de flexion Ry).
ap0 = point_connection("APOYO_0", 0.0, 0.0, 0.0,
                       bc_support([True, True, True, False, False, True]))
apL = point_connection("APOYO_L", L, 0.0, 0.0,
                       bc_support([False, True, True, False, False, True]))
objs.extend([ap0, apL])

# --------- cargas g2 y q (via ortodoxa) ----------
curve_action("g2_carga_muerta", viga, G2, gPerm)
curve_action("q_sobrecarga", viga, Q, gVar)

f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=objs,
                RelatingGroup=analysis)
analysis.LoadedBy = [gPerm, gVar]
f.write(OUT)

# resumen
A = B * H
I = B * H ** 3 / 12.0
W = I / (H / 2.0)
g0 = A * C40["rho"] * 9.81 / 1000.0   # kN/m (aprox; el solver usa A*rho*g)
print("IFC caso 12 (ortodoxo, viga postesada isostatica EC2 5.10) escrito en:", OUT)
print("  Viga C40/50  b=%.2f h=%.2f L=%.1f m" % (B, H, L))
print("  A=%.3f m2  I=%.6f m4  W=%.6f m3  g0~%.2f kN/m" % (A, I, W, g0))
print("  Cargas: g2=%.1f kN/m  q=%.1f kN/m (psi2=%.1f)" % (G2 / 1e3, Q / 1e3, PSI2))
print("  Pretensado: P0=%.0f kN  Pm,inf=%.0f kN  Ap=%.0f mm2  e_centro=%.2f m  %s" % (
    PRET["P0_kN"], PRET["Pm_inf_kN"], PRET["Ap_mm2"], PRET["e_centro_m"],
    PRET["tipo_cordon"]))
