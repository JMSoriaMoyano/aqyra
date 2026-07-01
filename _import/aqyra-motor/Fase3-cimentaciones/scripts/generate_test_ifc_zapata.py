"""
Genera un IFC4 de una ZAPATA AISLADA de hormigon (cimentacion superficial) sobre
lecho elastico (modelo de Winkler), bajo un pilar central.

  - Zapata C30/37, B x B = 2.5 x 2.5 m, canto 0.50 m   -> IfcStructuralSurfaceMember
  - Pilar central 0.40 x 0.40 m
  - Terreno: modulo de balasto ks y resistencia de calculo Rd (Pset)
  - Cargas del pilar: N permanente (G) y variable (Q), momento opcional

Unidades SI (m, N). Modulo de balasto en N/m3; Rd en Pa.
"""
import ifcopenshell
import ifcopenshell.guid

B = 2.5
T = 0.50
MESH = 0.125
C_PILAR = 0.40

CONCRETE = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, G=13.68e9, fctm=2.9e6)
KS = 40e6          # modulo de balasto (N/m3) ~ 40 MN/m3 (terreno medio)
RD_SUELO = 250e3   # resistencia del terreno de calculo (Pa) = 250 kPa
N_G = 600e3        # axil permanente del pilar (N)
N_Q = 200e3        # axil variable del pilar (N)
M_G = 60e3         # momento permanente (N·m) en direccion x (excentricidad)
OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase3-cimentaciones/proyecto-zapata/zapata.ifc"

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Zapata aislada demo",
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
                           Name="Zapata", PredefinedType="NOTDEFINED")

corners = {"Z1": (0., 0., 0.), "Z2": (B, 0., 0.), "Z3": (B, B, 0.), "Z4": (0., B, 0.)}
nodes = []
for nm, (x, y, z) in corners.items():
    vp = f.create_entity("IfcVertexPoint",
                         VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=nm,
        Representation=f.create_entity("IfcProductDefinitionShape",
            Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])]))
    nodes.append(conn)

foot = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="ZAPATA",
                       PredefinedType="SHELL", Thickness=T)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[foot], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=nodes + [foot], RelatingGroup=analysis)
pset_for(foot, "Pset_Estructurando_Zapata",
         {"B": B, "L": B, "Espesor": T, "TamanoMalla": MESH, "Material": CONCRETE["name"],
          "LadoPilar": C_PILAR, "ModuloBalasto_N_m3": KS, "Rd_suelo_Pa": RD_SUELO,
          "xpilar": B / 2, "ypilar": B / 2})
pset_for(foot, "Pset_Estructurando_Carga_Pilar_G", {"Caso": "G", "N_N": -N_G, "Mx_Nm": M_G})
pset_for(foot, "Pset_Estructurando_Carga_Pilar_Q", {"Caso": "Q", "N_N": -N_Q, "Mx_Nm": 0.0})

f.write(OUT)
print("IFC zapata escrito en:", OUT)
print(f"  B={B} t={T} pilar={C_PILAR}  N_G={N_G/1e3} N_Q={N_Q/1e3} kN  ks={KS/1e6} MN/m3  Rd={RD_SUELO/1e3} kPa")
