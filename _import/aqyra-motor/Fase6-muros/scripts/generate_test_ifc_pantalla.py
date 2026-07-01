"""
Genera un IFC4 de una PANTALLA DE CONTENCION ANCLADA (muro pantalla de hormigon)
como IfcStructuralCurveMember vertical, con una fila de anclajes al terreno, los
parametros del terreno y la sobrecarga en Property Sets de Estructurando.

Modelo (plano XZ; Z vertical, z hacia abajo desde la coronacion):

   z=0  ___ coronacion
        |==O==  <- ancla (prof. z_a, inclinacion theta, separacion s)
        |  |   |  relleno (activo en el trasdos)
        |  |   |
   z=h  |  |___|___ nivel de excavacion (delante)
        |  |#######  terreno delante (pasivo) sobre el empotramiento d
        |  |#######
   z=L  |__|####### pie (L = h + d)

Unidades SI (m, N, Pa).
"""
import os
import ifcopenshell
import ifcopenshell.guid

# ---------------- DATOS DEL CASO ----------------
# Pantalla (hormigon)
T_PANT = 0.60      # espesor de la pantalla (m)
H_EXC = 7.00       # altura de excavacion (retenida) (m)
D_EMP = 4.50       # empotramiento por debajo de la excavacion (m)
L = H_EXC + D_EMP  # longitud total (m)
N_ELEM = 40        # discretizacion
KH = 20e6          # balasto horizontal del terreno (N/m3) [estudio geotecnico]

# Ancla (una fila)
Z_ANCLA = 1.50     # profundidad del ancla desde coronacion (m)
INCL_ANCLA = 25.0  # inclinacion del ancla respecto a la horizontal (grados)
SEP_ANCLA = 2.00   # separacion horizontal entre anclas (m)
D_BULBO = 0.20     # diametro del bulbo (m)
TAU_BULBO = 200e3  # rozamiento unitario lechada-terreno (Pa) [ensayo/estudio]
FS_BULBO = 2.0     # coef. de seguridad del bulbo [criterio]
N_FILAS = 1

# Terreno
GAMMA_S = 19.0e3
PHI = 30.0
COH = 0.0
BETA = 0.0
DELTA_MURO = 0.0   # 0 = Rankine; >0 = Coulomb
METODO = "rankine"
PHI_PAS = 30.0
GAMMA_PAS = 19.0e3
RD_TERRENO = 350.0e3
NF_TRASDOS = -1.0  # profundidad del NF desde coronacion (m); <0 = sin agua
GAMMA_W = 9.81e3

# Sobrecarga en coronacion del trasdos
Q_SOBRECARGA = 10.0e3

CONCRETE = dict(name="C30/37", fck=30e6, E=32.84e9, nu=0.2, rho=2500.0, G=13.68e9, fctm=2.9e6)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "proyecto-pantalla-anclada", "pantalla.ifc"))

# ---------------- CONSTRUCCION DEL IFC ----------------
f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Pantalla anclada demo",
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


mat = f.create_entity("IfcMaterial", Name=CONCRETE["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=mat,
                Properties=[prop("CompressiveStrength", CONCRETE["fck"]), prop("YoungModulus", CONCRETE["E"]),
                            prop("ShearModulus", CONCRETE["G"]), prop("PoissonRatio", CONCRETE["nu"]),
                            prop("MassDensity", CONCRETE["rho"]), prop("TensileStrength", CONCRETE["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Pantalla anclada", PredefinedType="NOTDEFINED")
v0 = f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)))
vL = f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., -L)))
edge = f.create_entity("IfcEdge", EdgeStart=v0, EdgeEnd=vL)
pant = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="PANTALLA",
    PredefinedType="RIGID_JOINED_MEMBER",
    Axis=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.)),
    Representation=f.create_entity("IfcProductDefinitionShape",
        Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])]))
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[pant], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[pant], RelatingGroup=analysis)

pset_for(pant, "Pset_Estructurando_Pantalla",
         {"Tipo": "anclada", "Espesor_m": T_PANT, "ExcavacionH_m": H_EXC, "Empotramiento_m": D_EMP,
          "Long_m": L, "Material": CONCRETE["name"], "BalastoHorizontal_N_m3": KH, "NumElementos": N_ELEM})

pset_for(pant, "Pset_Estructurando_Ancla",
         {"Profundidad_m": Z_ANCLA, "Inclinacion_grados": INCL_ANCLA, "Separacion_m": SEP_ANCLA,
          "DiamBulbo_m": D_BULBO, "RozamientoBulbo_Pa": TAU_BULBO, "FS_Bulbo": FS_BULBO, "NumFilas": N_FILAS})

pset_for(pant, "Pset_Estructurando_Terreno",
         {"Metodo": METODO, "Gamma_N_m3": GAMMA_S, "Phi_grados": PHI, "Cohesion_Pa": COH,
          "Beta_grados": BETA, "DeltaMuro_grados": DELTA_MURO,
          "PhiPasivo_grados": PHI_PAS, "GammaPasivo_N_m3": GAMMA_PAS, "Rd_Pa": RD_TERRENO,
          "NivelFreatico_m": NF_TRASDOS, "GammaAgua_N_m3": GAMMA_W})

pset_for(pant, "Pset_Estructurando_Carga_q", {"Caso": "Q", "Sobrecarga_Pa": Q_SOBRECARGA})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
f.write(OUT)
print("IFC pantalla escrito en:", OUT)
print("  Pantalla e=%.2f m  H_exc=%.1f m  empotramiento=%.1f m  L=%.1f m  kh=%.0f MN/m3"
      % (T_PANT, H_EXC, D_EMP, L, KH / 1e6))
print("  Ancla z=%.2f m  incl=%.0f deg  sep=%.2f m  bulbo D=%.2f tau=%.0f kPa"
      % (Z_ANCLA, INCL_ANCLA, SEP_ANCLA, D_BULBO, TAU_BULBO / 1e3))
print("  Terreno %s gamma=%.0f phi=%.0f  q=%.0f kPa  NF=%.1f m" % (METODO, GAMMA_S / 1e3, PHI, Q_SOBRECARGA / 1e3, NF_TRASDOS))
