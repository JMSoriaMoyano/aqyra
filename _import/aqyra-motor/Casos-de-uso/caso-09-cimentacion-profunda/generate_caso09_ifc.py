"""
CASO 9 - CIMENTACION PROFUNDA: PILOTE + ENCEPADO + PANTALLA ANCLADA.
IFC4 ORTODOXO del dominio de analisis estructural (entidades estandar + Pset de
respaldo para los datos sin entidad estandar: geotecnia y region D).

Modelo (sintetico, realista) de la cimentacion profunda de un edificio con un
sotano excavado y sostenido por una pantalla anclada. Tres subestructuras que el
agente debe CLASIFICAR y ENRUTAR a tres modulos encadenados:

  A) PILOTES (modulo `pilotes`, EC7) -- 2 pilotes C30/37 Ø600 mm, L=12 m, que
     bajan la carga del pilar al terreno (capacidad axil fuste+punta + flexion
     lateral como viga sobre muelles horizontales kh).
        IfcStructuralCurveMember vertical (edge z=0 -> z=-L) +
        IfcMaterialProfileSet -> IfcMaterialProfile -> IfcCircleProfileDef (R=0,30).
        Geotecnia (kh, qs, qb) en Pset (sin entidad de analisis estandar).
        Carga de cabeza por pilote: IfcStructuralPointAction (N_G, N_Q [+ H_Q]).
  B) ENCEPADO de 2 pilotes (modulo `bielas-tirantes`, region D, EC2 §6.5) -- bajo
     un pilar 0,45x0,45 centrado, canto 0,90 m, ancho 0,90 m, separacion entre
     pilotes a=1,80 m.
        IfcStructuralSurfaceMember (Thickness = canto) + IfcFaceSurface/IfcPolyLoop.
        Los 2 pilotes son IfcStructuralPointConnection (apoyos) = cabezas de los
        pilotes A. Carga del pilar: IfcStructuralPointAction en el nodo de pilar.
        Geometria de region D (a, h, b, lado pilar, Ø pilote) en Pset.
  C) PANTALLA ANCLADA (modulo `muros-contencion`, EC7) -- muro pantalla C30/37
     e=0,60 m, excavacion H=7,0 m, empotramiento d=4,5 m (L=11,5 m), una fila de
     anclajes a z=1,5 m.
        IfcStructuralCurveMember vertical (edge z=0 -> z=-L) +
        IfcMaterialProfileSet -> IfcRectangleProfileDef (XDim = espesor, YDim = 1 m).
        Terreno, ancla y sobrecarga en Pset (sin entidad de analisis estandar).

BRECHA esperada (proximo hilo): dar a `solver_pilote.py`, `run_all_encepado.py` y
`solver_pantalla.py` una via ORTODOXA (`parse_ortodoxo()` + `parse_auto()`, como en
los casos 5 y 8) que lea: el pilote/pantalla como barra vertical con su seccion
del profile (IfcCircleProfileDef / IfcRectangleProfileDef), las cargas de cabeza
de los IfcStructuralPointAction, el encepado como superficie con los pilotes en
IfcStructuralPointConnection; manteniendo en Pset SOLO los datos sin entidad de
analisis estandar (geotecnia kh/qs/qb, terreno, ancla, geometria de region D).

Unidades SI (m, N, Pa). Plano XY-Z; Z vertical, gravedad -Z; pilotes/pantalla
descienden en -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

# ----------------------------- DATOS DEL CASO -----------------------------
CONC = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=32.84e9, nu=0.2, rho=2500.0,
            G=32.84e9 / (2 * (1 + 0.2)))

# A) Pilotes
D_PIL = 0.60
L_PIL = 12.0
N_ELEM_PIL = 24
KH = 15e6           # balasto horizontal (N/m3) [estudio geotecnico]
QS = 60e3           # fuste unitario (Pa)
QB = 2500e3         # punta unitaria (Pa)
A_PIL = 1.80        # separacion entre pilotes (m)

# B) Encepado / pilar
H_ENC = 0.90        # canto encepado
B_ENC = 0.90        # ancho encepado
C_COL = 0.45        # lado del pilar
N_G_COL = 1300e3    # axil del pilar (G)
N_Q_COL = 450e3     # axil del pilar (Q)
H_Q_PIL = 60e3      # carga horizontal en cabeza de pilote (Q, viento), por pilote

# C) Pantalla anclada
X_PANT = 15.0       # offset en x para separarla del grupo de pilotes
T_PANT = 0.60
H_EXC = 7.0
D_EMP = 4.5
L_PANT = H_EXC + D_EMP
N_ELEM_PANT = 40
KH_PANT = 20e6
Z_ANCLA = 1.5
INCL_ANCLA = 25.0
SEP_ANCLA = 2.0
D_BULBO = 0.20
TAU_BULBO = 200e3
FS_BULBO = 2.0
GAMMA_S = 19.0e3
PHI = 30.0
COH = 0.0
RD_TERRENO = 350e3
Q_SOBRECARGA = 10e3

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-09.ifc")

# ----------------------------- IFC -----------------------------
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
                Name="Caso 9 - Cimentacion profunda (pilote + encepado + pantalla anclada)",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def prop(name, val):
    nominal = (f.create_entity("IfcText", wrappedValue=val) if isinstance(val, str)
               else f.create_entity("IfcReal", wrappedValue=float(val)))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


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


def curve_member(name, p0, p1, profile):
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


def load_group(name, pred):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP",
                           ActionType="PERMANENT_G" if pred == "G" else "VARIABLE_Q",
                           ActionSource="DEAD_LOAD_G" if pred == "G" else "LIVE_LOAD_Q")


def point_action(name, node, fz, group, fx=0.0):
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name + "_F",
                           ForceX=fx, ForceY=0.0, ForceZ=fz, MomentX=0.0, MomentY=0.0, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[act], RelatingGroup=group)
    return act


# --- material C30/37 ---
mat = f.create_entity("IfcMaterial", Name=CONC["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=mat,
                Properties=[prop("YoungModulus", CONC["E"]), prop("ShearModulus", CONC["G"]),
                            prop("PoissonRatio", CONC["nu"]), prop("MassDensity", CONC["rho"]),
                            prop("CompressiveStrength", CONC["fck"]), prop("TensileStrength", CONC["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Cimentacion profunda caso 9", PredefinedType="LOADING_3D")
gG = load_group("G", "G")
gQ = load_group("Q", "Q")
all_objs = []

# ============ A+B) PILOTES + ENCEPADO ============
circ = f.create_entity("IfcCircleProfileDef", ProfileType="AREA", ProfileName="Pilote D600", Radius=D_PIL / 2.0)
pilote_x = {"PIL-1": -A_PIL / 2.0, "PIL-2": A_PIL / 2.0}
head_nodes = []
for pnm, x in pilote_x.items():
    # cabeza (z=0) y punta (z=-L). La cabeza es apoyo del encepado (BC vertical).
    bc = f.create_entity("IfcBoundaryNodeCondition", Name="cabeza_pilote",
                         TranslationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=True))
    n_head = point_connection("%s_cabeza" % pnm, x, 0.0, 0.0, bc)
    n_tip = point_connection("%s_punta" % pnm, x, 0.0, -L_PIL)
    pil = curve_member("Pilote_%s" % pnm, (x, 0.0, 0.0), (x, 0.0, -L_PIL), circ)
    # geotecnia (sin entidad estandar) -> Pset ; respaldo geometria/cargas en Pset
    pset_for(pil, "Pset_Estructurando_Pilote",
             {"Diametro": D_PIL, "Longitud": L_PIL, "Material": CONC["name"], "NumElementos": N_ELEM_PIL,
              "BalastoHorizontal_N_m3": KH, "FusteUnit_Pa": QS, "PuntaUnit_Pa": QB, "Cabeza": "encepado"})
    pset_for(pil, "Pset_Estructurando_Carga_Pilote_G", {"Caso": "G", "N_N": N_G_COL / 2.0, "H_N": 0.0, "M_Nm": 0.0})
    pset_for(pil, "Pset_Estructurando_Carga_Pilote_Q", {"Caso": "Q", "N_N": N_Q_COL / 2.0, "H_N": H_Q_PIL, "M_Nm": 0.0})
    # carga de cabeza ORTODOXA (axil bajado del encepado + horizontal de viento)
    point_action("Ncab_G_%s" % pnm, n_head, -(N_G_COL / 2.0), gG)
    point_action("Ncab_Q_%s" % pnm, n_head, -(N_Q_COL / 2.0), gQ, fx=H_Q_PIL)
    head_nodes.append(n_head)
    all_objs += [n_head, n_tip, pil]

# encepado: superficie horizontal (z=0) que une las 2 cabezas
hx = A_PIL / 2.0 + 0.45      # vuelo del encepado
hy = B_ENC / 2.0
poly = f.create_entity("IfcPolyLoop", Polygon=[
    f.create_entity("IfcCartesianPoint", Coordinates=c) for c in
    [(-hx, -hy, 0.), (hx, -hy, 0.), (hx, hy, 0.), (-hx, hy, 0.)]])
fb = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
    Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)),
    Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
    RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
face = f.create_entity("IfcFaceSurface", Bounds=[fb], FaceSurface=plane, SameSense=True)
enc_rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
enc = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="ENCEPADO_2pilotes",
                      PredefinedType="SHELL", Thickness=H_ENC, Representation=enc_rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[enc], RelatingMaterial=mat)
pset_for(enc, "Pset_Estructurando_Encepado",
         {"SeparacionPilotes": A_PIL, "Canto": H_ENC, "Ancho": B_ENC, "LadoPilar": C_COL,
          "DiametroPilote": D_PIL, "Material": CONC["name"], "TipoRegionD": "encepado_2_pilotes"})
pset_for(enc, "Pset_Estructurando_Carga_Pilar_G", {"Caso": "G", "N_N": N_G_COL})
pset_for(enc, "Pset_Estructurando_Carga_Pilar_Q", {"Caso": "Q", "N_N": N_Q_COL})
# carga del pilar ORTODOXA en el nodo de arranque del pilar (centro del encepado)
n_col = point_connection("Pilar_base", 0.0, 0.0, 0.0)
point_action("Npilar_G", n_col, -N_G_COL, gG)
point_action("Npilar_Q", n_col, -N_Q_COL, gQ)
all_objs += [enc, n_col]

# ============ C) PANTALLA ANCLADA ============
rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName="Pantalla e600",
                       XDim=T_PANT, YDim=1.0)
n_cor = point_connection("PANT_coronacion", X_PANT, 0.0, 0.0)
n_pie = point_connection("PANT_pie", X_PANT, 0.0, -L_PANT)
pant = curve_member("PANTALLA", (X_PANT, 0.0, 0.0), (X_PANT, 0.0, -L_PANT), rect)
pset_for(pant, "Pset_Estructurando_Pantalla",
         {"Tipo": "anclada", "Espesor_m": T_PANT, "ExcavacionH_m": H_EXC, "Empotramiento_m": D_EMP,
          "Long_m": L_PANT, "Material": CONC["name"], "BalastoHorizontal_N_m3": KH_PANT, "NumElementos": N_ELEM_PANT})
pset_for(pant, "Pset_Estructurando_Ancla",
         {"Profundidad_m": Z_ANCLA, "Inclinacion_grados": INCL_ANCLA, "Separacion_m": SEP_ANCLA,
          "DiamBulbo_m": D_BULBO, "RozamientoBulbo_Pa": TAU_BULBO, "FS_Bulbo": FS_BULBO, "NumFilas": 1})
pset_for(pant, "Pset_Estructurando_Terreno",
         {"Metodo": "rankine", "Gamma_N_m3": GAMMA_S, "Phi_grados": PHI, "Cohesion_Pa": COH,
          "Beta_grados": 0.0, "DeltaMuro_grados": 0.0, "PhiPasivo_grados": PHI,
          "GammaPasivo_N_m3": GAMMA_S, "Rd_Pa": RD_TERRENO, "NivelFreatico_m": -1.0, "GammaAgua_N_m3": 9.81e3})
pset_for(pant, "Pset_Estructurando_Carga_q", {"Caso": "Q", "Sobrecarga_Pa": Q_SOBRECARGA})
all_objs += [n_cor, n_pie, pant]

# --- todos los objetos al modelo de analisis ---
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=all_objs, RelatingGroup=analysis)

f.write(OUT)
print("IFC caso 9 escrito en:", OUT)
print("  A) 2 pilotes C30/37 Ø%.2f L=%.1f  kh=%.0f MN/m3 qs=%.0f qb=%.0f kPa  a=%.2f m"
      % (D_PIL, L_PIL, KH / 1e6, QS / 1e3, QB / 1e3, A_PIL))
print("  B) encepado 2 pilotes  h=%.2f b=%.2f  pilar %.2f  N_G=%.0f N_Q=%.0f kN"
      % (H_ENC, B_ENC, C_COL, N_G_COL / 1e3, N_Q_COL / 1e3))
print("  C) pantalla anclada e=%.2f H_exc=%.1f d=%.1f L=%.1f  ancla z=%.2f  Rd=%.0f kPa"
      % (T_PANT, H_EXC, D_EMP, L_PANT, Z_ANCLA, RD_TERRENO / 1e3))
