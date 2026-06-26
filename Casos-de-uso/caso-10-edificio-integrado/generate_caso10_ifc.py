"""
CASO 10 - EDIFICIO INTEGRADO. IFC4 ORTODOXO multi-elemento: en UN solo modelo de
analisis conviven los cuatro sistemas estructurales del catalogo, separados en
planta para que el agente CLASIFIQUE y ENRUTE CADA elemento a su modulo:

  A) PORTICO DE ACERO (modulo `barras`, EC3) -- 2 pilares HEB 240 + 1 dintel
     IPE 360 (S275), luz 6 m, altura 4 m. Cargas de linea en el dintel
     (IfcStructuralCurveAction + IfcStructuralLoadLinearForce).
  B) FORJADO MIXTO / viga mixta (modulo `mixtas`, EC4) -- viga IPE 400 (S275)
     L=8 m con losa colaborante C25/30 (IfcStructuralSurfaceMember). Cargas por
     fase (IfcStructuralLoadGroup *_construccion / *_mixta). Conectores y chapa
     nervada en Pset (sin entidad de analisis estandar).
  C) MURO DE CARGA / nucleo (modulo `laminas`, EC2 esbeltez) -- pantalla vertical
     C30/37 H=3,0 t=0,20 (IfcStructuralSurfaceMember vertical, Thickness=espesor),
     con carga de cabeza excentrica (IfcStructuralPointAction N + M).
  D) CIMENTACION superficial (modulo `cimentaciones`, EC2 + EC7) -- pilar HA
     0,40x0,40 (IfcStructuralCurveMember vertical + IfcRectangleProfileDef) sobre
     zapata aislada 2,5x2,5 t=0,60 (IfcStructuralSurfaceMember horizontal) en
     lecho elastico (IfcBoundaryNodeCondition en esquinas). Carga de cabeza del
     pilar (IfcStructuralPointAction N + M). Suelo (ks, Rd) en Pset.

El agente debe iterar TODOS los elementos del IFC y, por la combinacion de
(geometria + seccion del perfil + material + Pset marcador), enrutar cada uno:
  - barra horizontal/inclinada de acero I  -> barras (viga/dintel EC3)
  - barra vertical de acero I              -> barras (pilar EC3)
  - barra vertical de hormigon rectangular -> cimentaciones (pilar->zapata) o pilar
  - superficie horizontal de hormigon + perfil de acero asociado -> mixtas (EC4)
  - superficie horizontal de hormigon con lecho -> cimentaciones (zapata/raft)
  - superficie vertical de hormigon con carga de cabeza -> laminas (muro de carga)

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

# ----------------------------- MATERIALES -----------------------------
STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
C30 = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=32.84e9, nu=0.2, rho=2500.0, G=32.84e9 / 2.4)
C25 = dict(name="C25/30", fck=25e6, fctm=2.6e6, E=31.0e9, nu=0.2, rho=2500.0, G=31.0e9 / 2.4)

# ----------------------------- PERFILES -----------------------------
HEB240 = dict(name="HEB 240", b=0.240, h=0.240, tw=0.010, tf=0.017, r=0.021)
IPE360 = dict(name="IPE 360", b=0.170, h=0.360, tw=0.008, tf=0.0127, r=0.018)
IPE400 = dict(name="IPE 400", b=0.180, h=0.400, tw=0.0086, tf=0.0135, r=0.021)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-10.ifc")

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
                Name="Caso 10 - Edificio integrado (portico + mixta + muro + cimentacion)",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    nominal = (f.create_entity("IfcText", wrappedValue=val) if isinstance(val, str)
               else f.create_entity("IfcReal", wrappedValue=float(val)))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)


def material(M, extra):
    m = f.create_entity("IfcMaterial", Name=M["name"])
    props = [prop("YoungModulus", M["E"]), prop("ShearModulus", M["G"]),
             prop("PoissonRatio", M["nu"]), prop("MassDensity", M["rho"])]
    props += extra
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=m, Properties=props)
    return m


steel = material(STEEL, [prop("YieldStress", STEEL["fy"])])
c30 = material(C30, [prop("CompressiveStrength", C30["fck"]), prop("TensileStrength", C30["fctm"])])
c25 = material(C25, [prop("CompressiveStrength", C25["fck"]), prop("TensileStrength", C25["fctm"])])


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


def boolwrap(b):
    return f.create_entity("IfcBoolean", wrappedValue=b) if b else None


def realwrap(v):
    return f.create_entity("IfcReal", wrappedValue=float(v)) if v else None


def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint",
                           VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))


def point_connection(name, x, y, z, bc=None):
    vp = vertex(x, y, z)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])])
    return f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
                           Representation=rep, AppliedCondition=bc), vp


def bc_node(apoyo=None, kz=None):
    if kz is not None:
        return f.create_entity("IfcBoundaryNodeCondition", Name="lecho",
                               TranslationalStiffnessZ=realwrap(kz))
    if apoyo:
        return f.create_entity("IfcBoundaryNodeCondition", Name="apoyo",
            TranslationalStiffnessX=boolwrap(apoyo[0]), TranslationalStiffnessY=boolwrap(apoyo[1]),
            TranslationalStiffnessZ=boolwrap(apoyo[2]), RotationalStiffnessX=boolwrap(apoyo[3]),
            RotationalStiffnessY=boolwrap(apoyo[4]), RotationalStiffnessZ=boolwrap(apoyo[5]))
    return None


def ishape(P):
    return f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=P["name"],
                           OverallWidth=P["b"], OverallDepth=P["h"],
                           WebThickness=P["tw"], FlangeThickness=P["tf"], FilletRadius=P["r"])


def rect(name, bx, by):
    return f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=name, XDim=bx, YDim=by)


def curve_member(name, p0, p1, profile, mat):
    edge = f.create_entity("IfcEdge", EdgeStart=vertex(*p0), EdgeEnd=vertex(*p1))
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])])
    mb = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name=name,
                         PredefinedType="RIGID_JOINED_MEMBER",
                         Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 1., 0.)),
                         Representation=rep)
    mprof = f.create_entity("IfcMaterialProfile", Name=name + "_perfil", Material=mat, Profile=profile)
    mps = f.create_entity("IfcMaterialProfileSet", Name=name + "_seccion", MaterialProfiles=[mprof])
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[mb], RelatingMaterial=mps)
    return mb


def surface(name, pts4, t, mat, axis=(0., 0., 1.), refd=(1., 0., 0.)):
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


def load_group(name, pred):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP",
                           ActionType="PERMANENT_G" if pred == "G" else "VARIABLE_Q",
                           ActionSource="DEAD_LOAD_G" if pred == "G" else "LIVE_LOAD_Q", Coefficient=1.0)


def line_load(name, member, qz, group):
    load = f.create_entity("IfcStructuralLoadLinearForce", Name=name + "_q",
                           LinearForceX=0.0, LinearForceY=0.0, LinearForceZ=-qz)
    act = f.create_entity("IfcStructuralCurveAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          ProjectedOrTrue="TRUE_LENGTH", PredefinedType="CONST")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=member, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=group)
    return act


def surface_load(name, sm, qz, group):
    load = f.create_entity("IfcStructuralLoadPlanarForce", Name=name + "_q",
                           PlanarForceX=0.0, PlanarForceY=0.0, PlanarForceZ=-qz)
    act = f.create_entity("IfcStructuralSurfaceAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          ProjectedOrTrue="TRUE_LENGTH", PredefinedType="CONST")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=sm, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=group)
    return act


def point_action(name, node, fz, group, fx=0.0, my=0.0):
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name + "_F",
                           ForceX=fx, ForceY=0.0, ForceZ=fz, MomentX=0.0, MomentY=my, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=group)
    return act


analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Edificio integrado caso 10", PredefinedType="LOADING_3D")
gG = load_group("G", "G")
gQ = load_group("Q", "Q")
gGc = load_group("G_construccion", "G")
gQc = load_group("Q_construccion", "Q")
gGm = load_group("G_mixta", "G")
gQm = load_group("Q_mixta", "Q")
objs = []

# ============ A) PORTICO DE ACERO (barras EC3) ============
PIN = [True, True, True, False, False, True]
xA = 0.0
a1, _ = point_connection("PORT_base_1", xA + 0.0, 0.0, 0.0, bc_node(PIN))
a2, _ = point_connection("PORT_base_2", xA + 6.0, 0.0, 0.0, bc_node(PIN))
a3, _ = point_connection("PORT_top_1", xA + 0.0, 0.0, 4.0)
a4, _ = point_connection("PORT_top_2", xA + 6.0, 0.0, 4.0)
C1 = curve_member("PORT_pilar_1", (xA + 0.0, 0.0, 0.0), (xA + 0.0, 0.0, 4.0), ishape(HEB240), steel)
C2 = curve_member("PORT_pilar_2", (xA + 6.0, 0.0, 0.0), (xA + 6.0, 0.0, 4.0), ishape(HEB240), steel)
B1 = curve_member("PORT_dintel", (xA + 0.0, 0.0, 4.0), (xA + 6.0, 0.0, 4.0), ishape(IPE360), steel)
for el in (C1, C2, B1):
    pset_for(el, "Pset_Estructurando_Portico", {"Sistema": "portico_acero", "Norma": "EC3"})
line_load("PORT_G", B1, 12e3, gG)
line_load("PORT_Q", B1, 10e3, gQ)
objs += [a1, a2, a3, a4, C1, C2, B1]

# ============ B) FORJADO MIXTO / viga mixta (mixtas EC4) ============
yB = 20.0
L_MIX = 8.0
SEP_MIX = 3.0
b1, _ = point_connection("MIX_ap_1", 0.0, yB, 0.0, bc_node(PIN))
b2, _ = point_connection("MIX_ap_2", L_MIX, yB, 0.0, bc_node(PIN))
VM = curve_member("MIX_viga", (0.0, yB, 0.0), (L_MIX, yB, 0.0), ishape(IPE400), steel)
pset_for(VM, "Pset_Estructurando_Conectores",
         {"TipoPerno": "headed", "Diametro_m": 0.019, "Altura_m": 0.100, "fu_Pa": 450e6,
          "nr_por_nervio": 1, "Apeado": "no"})
pset_for(VM, "Pset_Estructurando_Losa",
         {"Canto_m": 0.12, "CantoChapa_hp_m": 0.058, "CantoHorm_hc_m": 0.062, "b0_m": 0.10,
          "Orientacion": "perpendicular", "Material": C25["name"]})
losaM = surface("MIX_losa",
                [(0.0, yB - SEP_MIX / 2, 0.0), (L_MIX, yB - SEP_MIX / 2, 0.0),
                 (L_MIX, yB + SEP_MIX / 2, 0.0), (0.0, yB + SEP_MIX / 2, 0.0)], 0.12, c25)
pset_for(losaM, "Pset_Estructurando_Mixta", {"Sistema": "viga_mixta", "Norma": "EC4", "VigaAsociada": "MIX_viga"})
surface_load("MIX_Ghormigon_construccion", losaM, 2.5e3, gGc)
surface_load("MIX_Qejecucion_construccion", losaM, 0.75e3, gQc)
surface_load("MIX_G2_mixta", losaM, 2.0e3, gGm)
surface_load("MIX_Quso_mixta", losaM, 5.0e3, gQm)
objs += [b1, b2, VM, losaM]

# ============ C) MURO DE CARGA / nucleo (laminas EC2 esbeltez) ============
xC = 30.0
H_MURO = 3.0
T_MURO = 0.20
muro = surface("MURO_carga",
               [(xC, 0.0, 0.0), (xC + 1.0, 0.0, 0.0), (xC + 1.0, 0.0, H_MURO), (xC, 0.0, H_MURO)],
               T_MURO, c30, axis=(0., 1., 0.), refd=(1., 0., 0.))
pset_for(muro, "Pset_Estructurando_MuroCarga",
         {"Sistema": "muro_carga", "Altura_m": H_MURO, "Espesor_m": T_MURO, "Faja_m": 1.0,
          "Arriostrado": "si", "Excentricidad_m": 0.025})
n_muro, _ = point_connection("MURO_cabeza", xC + 0.5, 0.0, H_MURO)
point_action("MURO_N_G", n_muro, -250e3, gG, my=250e3 * 0.025)
point_action("MURO_N_Q", n_muro, -120e3, gQ, my=120e3 * 0.025)
objs += [muro, n_muro]

# ============ D) CIMENTACION superficial: pilar + zapata (cimentaciones EC2+EC7) ============
xD = 40.0
B_ZAP = 2.5
T_ZAP = 0.60
KS = 40e6
corner_trib = (B_ZAP / 2.0) * (B_ZAP / 2.0)
k_corner = KS * corner_trib
zc = []
for sx in (-1, 1):
    for sy in (-1, 1):
        nc, _ = point_connection("ZAP_esq_%d_%d" % (sx, sy),
                                 xD + sx * B_ZAP / 2, sy * B_ZAP / 2, 0.0, bc_node(kz=k_corner))
        zc.append(nc)
zap = surface("ZAPATA_aislada",
              [(xD - B_ZAP / 2, -B_ZAP / 2, 0.0), (xD + B_ZAP / 2, -B_ZAP / 2, 0.0),
               (xD + B_ZAP / 2, B_ZAP / 2, 0.0), (xD - B_ZAP / 2, B_ZAP / 2, 0.0)], T_ZAP, c30)
pset_for(zap, "Pset_Estructurando_Suelo", {"ModuloBalasto_N_m3": KS, "Rd_suelo_Pa": 250e3})
pset_for(zap, "Pset_Estructurando_Zapata", {"B_m": B_ZAP, "L_m": B_ZAP, "Canto_m": T_ZAP, "LadoPilar_m": 0.40})
n_pcab, _ = point_connection("ZAP_pilar_cabeza", xD, 0.0, 1.0)
n_ppie, _ = point_connection("ZAP_pilar_pie", xD, 0.0, 0.0)
pilar = curve_member("ZAP_pilar", (xD, 0.0, 0.0), (xD, 0.0, 1.0), rect("Pilar 400x400", 0.40, 0.40), c30)
pset_for(pilar, "Pset_Estructurando_PilarCimiento", {"Sistema": "pilar_zapata", "Lado_m": 0.40})
point_action("ZAP_N_G", n_pcab, -700e3, gG, my=80e3)
point_action("ZAP_N_Q", n_pcab, -250e3, gQ, my=40e3)
objs += zc + [zap, n_pcab, n_ppie, pilar]

# --- todos los objetos al modelo de analisis ---
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=objs, RelatingGroup=analysis)
analysis.LoadedBy = [gG, gQ, gGc, gQc, gGm, gQm]

f.write(OUT)
print("IFC caso 10 (ortodoxo, multi-elemento) escrito en:", OUT)
print("  A) Portico acero: 2 HEB 240 + dintel IPE 360 (S275), luz 6 m h=4 m")
print("  B) Viga mixta IPE 400 + losa colaborante C25/30 L=8 m sep=3 m (fases constr/mixta)")
print("  C) Muro de carga C30/37 H=3,0 t=0,20 con carga de cabeza excentrica")
print("  D) Pilar HA 0,40 + zapata 2,5x2,5 t=0,60 sobre lecho ks=40 MN/m3 (Rd=250 kPa)")
