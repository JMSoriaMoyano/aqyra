"""
Genera un IFC4 de un MURO DE CARGA de hormigon (elemento plano vertical) en el
plano XZ. El mecanismo gobernante es la COMPRESION con efectos de esbeltez.

  - Muro C30/37, alto H = 3.5 m, largo L = 4.0 m, espesor 0.20 m
  - Base empotrada en cimentacion; cabeza arriostrada por el forjado (fuera de plano)
  - Cargas: vertical en cabeza (G + Q de forjados) + viento fuera de plano + autopeso

Unidades SI (m, N). Acciones verticales en kN/m (linea en cabeza); viento en kN/m2.
"""
import ifcopenshell
import ifcopenshell.guid

H, L = 3.5, 4.0
T = 0.20
MESH = 0.25
BETA = 1.0                  # factor de longitud de pandeo (lo = beta*H)

CONCRETE = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, G=13.68e9, fctm=2.9e6)
G_TOP = 900e3              # carga vertical permanente en cabeza (N/m)
Q_TOP = 300e3             # carga vertical variable en cabeza (N/m)
W_NORM = 1.0e3            # viento fuera de plano (N/m2)
OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase2-laminas/proyecto-muro/muro.ifc"

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Muro de carga demo",
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
                Properties=[prop("YoungModulus", CONCRETE["E"]), prop("ShearModulus", CONCRETE["G"]),
                            prop("PoissonRatio", CONCRETE["nu"]), prop("MassDensity", CONCRETE["rho"]),
                            prop("CompressiveStrength", CONCRETE["fck"]), prop("TensileStrength", CONCRETE["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Muro", PredefinedType="NOTDEFINED")

# esquinas (plano XZ, y=0)
corners = {"M1": (0., 0., 0.), "M2": (L, 0., 0.), "M3": (L, 0., H), "M4": (0., 0., H)}
nodes = []
for nm, (x, y, z) in corners.items():
    vp = f.create_entity("IfcVertexPoint",
                         VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=nm,
        Representation=f.create_entity("IfcProductDefinitionShape",
            Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])]))
    nodes.append(conn)

wall = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="MURO",
                       PredefinedType="SHELL", Thickness=T)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[wall], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=nodes + [wall], RelatingGroup=analysis)
pset_for(wall, "Pset_Estructurando_Muro",
         {"H": H, "L": L, "Espesor": T, "TamanoMalla": MESH, "Beta": BETA,
          "Material": CONCRETE["name"], "Apoyo": "base empotrada, cabeza arriostrada"})
pset_for(wall, "Pset_Estructurando_Carga_Muro_Gtop", {"Tipo": "top_vertical", "Caso": "G", "valor_N_m": -G_TOP})
pset_for(wall, "Pset_Estructurando_Carga_Muro_Qtop", {"Tipo": "top_vertical", "Caso": "Q", "valor_N_m": -Q_TOP})
pset_for(wall, "Pset_Estructurando_Carga_Muro_Viento", {"Tipo": "viento_normal", "Caso": "Q", "valor_N_m2": W_NORM})

f.write(OUT)
print("IFC muro escrito en:", OUT)
print(f"  H={H} L={L} t={T}  Gtop={G_TOP/1e3} Qtop={Q_TOP/1e3} kN/m  viento={W_NORM/1e3} kN/m2")
