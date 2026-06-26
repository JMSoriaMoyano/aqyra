"""
CASO 13 - Losa plana POSTESADA (post-tensioned flat slab). IFC4 ORTODOXO del
dominio de analisis estructural: SUPERFICIE (losa) + apoyos PUNTUALES (pilares)
+ datos del pretensado en Pset_Estructurando_Pretensado de la SUPERFICIE.

Modelo (sintetico, realista):
  - Losa maciza postesada C40/50, espesor 0,25 m, planta 16,0 x 16,0 m
    (dos vanos x dos vanos de 8,0 m), plano XY, z=0. L/h ~ 32.
  - 9 pilares C40/50, seccion 0,45 x 0,45 m, altura 3,0 m, reticula 3x3 a
    x,y = {0, 8, 16} m. Empotrados en su base (z=-3,0). Cabezas = apoyos de la losa.
  - Cargas de SUPERFICIE sobre la losa (gravedad -Z), vía ortodoxa:
      G (carga muerta g2) = 2,75 kN/m2 (solado/tabiqueria). El p.p. g0=t*25=6,25
        kN/m2 lo añade el solver desde el espesor y la densidad (como en el caso 12).
      Q (sobrecarga de uso) = 5,0 kN/m2 (Cat. B oficinas), psi2=0,3.
  - PRETENSADO postesado NO adherente (monotorones Y1860S7 0,6", Ap=150 mm2/cordon):
    tendones BANDED sobre las lineas de pilares en X + DISTRIBUIDOS en Y, trazado
    parabolico drape a=0,17 m. Datos en Pset_Estructurando_Pretensado de la LOSA.
  - El PILAR INTERIOR (8,8) es el critico a punzonamiento (EC2 6.4 / 6.4.4 con
    efecto favorable del pretensado).

Entidades ESTANDAR + Pset_Estructurando_Pretensado (sin entidad de analisis para
el pretensado, igual que ks/Rd/conectores/terreno/sismo de los casos 5/6/7/9/11/12).
Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

LADO = 16.0          # planta de la losa (m)
VANO = 8.0           # separacion entre pilares (m)
T_LOSA = 0.25
H_PILAR = 3.0
COL = dict(name="C 450x450", b=0.45, h=0.45)
C40 = dict(name="C40/50", fck=40e6, fctm=3.5e6, E=35000e6, nu=0.2, rho=2500.0,
           G=35000e6 / (2 * (1 + 0.2)))
G2_kN_m2 = 2.75e3    # carga muerta (sin p.p.; el solver añade g0=t*25)
Q_kN_m2 = 5.0e3      # sobrecarga de uso
GRID = [0.0, VANO, LADO]

# --- Pretensado (2D) -> Pset_Estructurando_Pretensado de la SUPERFICIE ---
PRET = {
    "Norma": "EC2 (EN 1992-1-1) 5.10 + 6.4.4",
    "Sistema": "postesado_no_adherente_monotoron",
    "tipo_cordon": "Y1860S7 0.6\"",
    "Ap_cordon_mm2": 150.0,
    "fpk_MPa": 1860.0,
    "fp01k_MPa": 1640.0,
    "Ep_GPa": 195.0,
    "trazado": "parabolico",
    "drape_m": 0.17,                 # flecha del tendon (alto sobre pilar, bajo en vano)
    "recubrimiento_eje_m": 0.04,     # recubrimiento mecanico al eje del tendon
    "layout": "banded_X + distribuido_Y",
    # direccion X (banded sobre lineas de pilares)
    "P_m_X_kN": 212.0,               # fuerza media tras perdidas, por metro de ancho
    "n_cordones_m_X": 1.27,
    "ancho_banda_X_m": 1.20,
    # direccion Y (distribuido)
    "P_m_Y_kN": 212.0,
    "n_cordones_m_Y": 1.27,
    "sep_distribuido_Y_m": 0.80,
    # estado de tension del acero activo
    "P0_m_kN": 255.0,                # transferencia, por metro (tras perd. inst.)
    "sigma_p0_MPa": 1339.0,          # ~0.72 fpk
    "Pm_inf_m_kN": 212.0,            # tras perd. diferidas, por metro
    "sigma_pm_inf_MPa": 1116.0,      # ~0.60 fpk
    "sigma_cp_MPa": 0.85,            # precompresion media (P/(m*t))
    "w_balance_kN_m2": 9.0,          # carga equilibrada (= permanente g0+g2)
    # coeficientes de perdidas [confirmar AN] (monotoron engrasado: mu/k bajos)
    "mu_rozamiento": 0.06,
    "k_desviacion": 0.005,
    "penetracion_cuna_mm": 6.0,
    "relajacion_clase": 2,
    "rho1000_pct": 2.5,
    "tesado": "un_extremo",
}

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-13.ifc")

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
                Name="Caso 13 - Losa plana postesada (EC2 5.10 + 6.4.4)",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    if isinstance(val, bool):
        nominal = f.create_entity("IfcBoolean", wrappedValue=val)
    elif isinstance(val, str):
        nominal = f.create_entity("IfcText", wrappedValue=val)
    elif isinstance(val, int):
        nominal = f.create_entity("IfcInteger", wrappedValue=val)
    else:
        nominal = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)


conc = f.create_entity("IfcMaterial", Name=C40["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=conc,
                Properties=[prop("YoungModulus", C40["E"]), prop("ShearModulus", C40["G"]),
                            prop("PoissonRatio", C40["nu"]), prop("MassDensity", C40["rho"]),
                            prop("CompressiveStrength", C40["fck"]),
                            prop("TensileStrength", C40["fctm"])])

rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=COL["name"],
                       XDim=COL["b"], YDim=COL["h"])
mprof = f.create_entity("IfcMaterialProfile", Name=COL["name"], Material=conc, Profile=rect)
mps_col = f.create_entity("IfcMaterialProfileSet", Name=COL["name"], MaterialProfiles=[mprof])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Losa plana postesada caso 13", PredefinedType="LOADING_3D")


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


FIX = [True, True, True, True, True, True]
all_objs = []
k = 0
for j, y in enumerate(GRID):
    for i, x in enumerate(GRID):
        k += 1
        nh, vh, ph = nodo("H%d" % k, x, y, 0.0)
        nb, vb, pb = nodo("B%d" % k, x, y, -H_PILAR, FIX)
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
        all_objs += [nh, nb, col]

# --- Losa: IfcStructuralSurfaceMember ---
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
LOSA = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="Losa postesada",
                       PredefinedType="SHELL", Thickness=T_LOSA, Representation=rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                RelatedObjects=[LOSA], RelatingMaterial=conc)
all_objs.append(LOSA)

# Pset del pretensado en la superficie
ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name="Pset_Estructurando_Pretensado",
                     HasProperties=[prop(kk, vv) for kk, vv in PRET.items()])
f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                RelatedObjects=[LOSA], RelatingPropertyDefinition=ps)

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


g_grp = carga_superficie("G", "PERMANENT_G", "DEAD_LOAD_G", G2_kN_m2)
q_grp = carga_superficie("Q", "VARIABLE_Q", "LIVE_LOAD_Q", Q_kN_m2)
analysis.LoadedBy = [g_grp, q_grp]

f.write(OUT)
g0 = T_LOSA * 25.0
print("IFC caso 13 (ortodoxo, losa plana postesada EC2 5.10 + 6.4.4) escrito en:", OUT)
print("  Losa %.1f x %.1f m | C40/50 t=%.0f mm (L/h~%.0f) | 9 pilares %s reticula %s m" % (
    LADO, LADO, T_LOSA * 1000, VANO / T_LOSA, COL["name"], GRID))
print("  Cargas: g0(pp)=%.2f  g2(muerta)=%.2f  q=%.1f kN/m2 (psi2=0.3)" % (
    g0, G2_kN_m2 / 1e3, Q_kN_m2 / 1e3))
print("  Pretensado: sigma_cp=%.2f MPa  P/m=%.0f kN/m  drape=%.2f m  %s" % (
    PRET["sigma_cp_MPa"], PRET["P_m_X_kN"], PRET["drape_m"], PRET["layout"]))
VEd = (1.35 * (g0 * 1e3 + G2_kN_m2) + 1.5 * Q_kN_m2) * VANO * VANO / 1e3
print("  V_Ed punzonamiento (pilar interior, tributario %.0f m2) ~ %.0f kN (ELU, sin efecto favorable)" % (
    VANO * VANO, VEd))
