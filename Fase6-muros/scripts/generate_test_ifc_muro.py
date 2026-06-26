"""
Genera un IFC4 de un MURO DE CONTENCION en MENSULA (T-invertida) de hormigon
armado, como IfcStructuralSurfaceMember (el alzado) con la geometria completa del
muro, los parametros del terreno y las cargas en Property Sets de Estructurando.

Geometria (seccion por metro lineal de muro, plano XZ; Z vertical):

        q (sobrecarga)
   ||||||||||||||||||||||
   +----+ <- coronacion        ___________________________
   |    |                     |  relleno (gamma, phi, c)   |
   |alz.| t_alz               | trasdos                    |
   |    | Hm                   |                            |
   |    |                      |                            |
 __|    |______________________|____ top zapata
|  pun. |        talon              |  e_z (canto zapata)
|_______|___________________________|
   <----------- B = puntera + t_alz + talon ----------->
   (Df = profundidad de tierras sobre la puntera -> empuje pasivo)

Unidades SI (m, N, Pa).
"""
import os
import ifcopenshell
import ifcopenshell.guid

# ---------------- DATOS DEL CASO ----------------
# Geometria del muro (m)
HM = 5.50          # altura del alzado (stem) sobre la cara superior de la zapata
T_ALZ = 0.45       # espesor del alzado (constante en v1)
E_Z = 0.70         # canto de la zapata
B_PUNTERA = 1.00   # longitud de puntera (delante)
B_TALON = 2.55     # longitud de talon (detras, bajo el relleno)
DF = 0.80          # profundidad de tierras delante (sobre la puntera) -> pasivo

# Terreno (relleno de trasdos)
GAMMA_S = 19.0e3   # peso especifico del relleno (N/m3)
PHI = 30.0         # angulo de rozamiento interno (grados)
COH = 0.0          # cohesion efectiva c' (Pa)
BETA = 0.0         # inclinacion del talud del relleno (grados)
DELTA_MURO = 0.0   # rozamiento muro-terreno (grados): 0 = Rankine; >0 = Coulomb
METODO = "rankine" # "rankine" | "coulomb"

# Terreno delante (pasivo) y cimiento
PHI_PAS = 30.0     # angulo de rozamiento del terreno delante (grados)
GAMMA_PAS = 19.0e3 # peso especifico del terreno delante (N/m3)
F_PASIVO = 0.50    # fraccion movilizable del empuje pasivo (reductor) [criterio]
PHI_BASE = 30.0    # rozamiento base-terreno para deslizamiento (grados)
ADH_BASE = 0.0     # adherencia base-terreno (Pa)
RD_TERRENO = 350.0e3  # resistencia de calculo del terreno (Pa) [confirmar AN/DA-2*]

# Agua
NF_TRASDOS = -1.0  # profundidad del nivel freatico desde coronacion (m); <0 = sin agua (drenado)
GAMMA_W = 9.81e3   # peso especifico del agua (N/m3)

# Sobrecarga en coronacion del relleno
Q_SOBRECARGA = 10.0e3   # (Pa) uniforme sobre el trasdos

# Cargas exteriores en coronacion del alzado (estructura apoyada): opcional
N_CORON_G = 0.0    # axil permanente (N/m)
N_CORON_Q = 0.0    # axil variable (N/m)
H_CORON_Q = 0.0    # horizontal variable (N/m)

CONCRETE = dict(name="C30/37", fck=30e6, E=32.84e9, nu=0.2, rho=2500.0, G=13.68e9, fctm=2.9e6)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "proyecto-muro-mensula", "muro.ifc"))

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
f.create_entity("IfcProject", GlobalId=guid(), Name="Muro mensula demo",
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
                           Name="Muro mensula", PredefinedType="NOTDEFINED")

# El alzado del muro como superficie estructural (placa vertical), por metro de muro
B = B_PUNTERA + T_ALZ + B_TALON
pts = [(0., 0., 0.), (1., 0., 0.), (1., 0., HM), (0., 0., HM)]
poly = f.create_entity("IfcPolyloop", Polygon=[f.create_entity("IfcCartesianPoint", Coordinates=p) for p in pts])
face = f.create_entity("IfcFaceSurface",
    Bounds=[f.create_entity("IfcFaceBound", Bound=poly, Orientation=True)],
    FaceSurface=f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)))),
    SameSense=True)
muro = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="MURO_ALZADO",
    PredefinedType="SHELL", Thickness=T_ALZ,
    Representation=f.create_entity("IfcProductDefinitionShape",
        Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])]))
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[muro], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[muro], RelatingGroup=analysis)

pset_for(muro, "Pset_Estructurando_Muro",
         {"Tipo": "mensula", "AlturaAlzado_m": HM, "EspesorAlzado_m": T_ALZ,
          "CantoZapata_m": E_Z, "Puntera_m": B_PUNTERA, "Talon_m": B_TALON,
          "AnchoZapata_m": B, "ProfTierrasDelante_m": DF, "Material": CONCRETE["name"]})

pset_for(muro, "Pset_Estructurando_Terreno",
         {"Metodo": METODO, "Gamma_N_m3": GAMMA_S, "Phi_grados": PHI, "Cohesion_Pa": COH,
          "Beta_grados": BETA, "DeltaMuro_grados": DELTA_MURO,
          "PhiPasivo_grados": PHI_PAS, "GammaPasivo_N_m3": GAMMA_PAS, "FraccionPasivo": F_PASIVO,
          "PhiBase_grados": PHI_BASE, "AdherenciaBase_Pa": ADH_BASE, "Rd_Pa": RD_TERRENO,
          "NivelFreatico_m": NF_TRASDOS, "GammaAgua_N_m3": GAMMA_W})

pset_for(muro, "Pset_Estructurando_Carga_Muro_q", {"Caso": "Q", "Sobrecarga_Pa": Q_SOBRECARGA})
pset_for(muro, "Pset_Estructurando_Carga_Muro_coronacion",
         {"N_G_N": N_CORON_G, "N_Q_N": N_CORON_Q, "H_Q_N": H_CORON_Q})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
f.write(OUT)
print("IFC muro escrito en:", OUT)
print(f"  Mensula H_alzado={HM} m  zapata B={B:.2f} m (pun {B_PUNTERA}+alz {T_ALZ}+talon {B_TALON})  e_z={E_Z} m")
print(f"  terreno: {METODO}  gamma={GAMMA_S/1e3} phi={PHI} c={COH/1e3}kPa  q={Q_SOBRECARGA/1e3}kPa  NF={NF_TRASDOS}m")
print(f"  Rd={RD_TERRENO/1e3}kPa  phi_base={PHI_BASE}  pasivo x{F_PASIVO} (Df={DF}m)")
