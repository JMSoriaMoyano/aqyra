"""
Genera un IFC4 de un ENCEPADO DE 2 PILOTES (region D) bajo pilar centrado, para
calculo por BIELAS Y TIRANTES (EC2 §6.5).

  - Encepado C30/37: separacion entre pilotes a = 1.8 m, canto h = 0.9 m, ancho b = 0.9 m
  - Pilar 0.40 x 0.40 m ; pilotes Ø450 mm
  - Carga del pilar: N permanente (G) y variable (Q)

Unidades SI (m, N). La geometria del encepado va en un Pset; el modelo de celosia
lo construye el solver.
"""
import ifcopenshell
import ifcopenshell.guid

A = 1.8       # separacion entre pilotes
H = 0.9       # canto del encepado
B = 0.9       # ancho del encepado
C_COL = 0.40
D_PILOTE = 0.45

CONCRETE = dict(name="C30/37", fck=30e6, E=32.84e9, nu=0.2, rho=2500.0, G=13.68e9, fctm=2.9e6)
N_G = 1300e3
N_Q = 450e3
OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase4-bielas-tirantes/proyecto-encepado/encepado.ifc"

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Encepado 2 pilotes demo",
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
                Properties=[prop("CompressiveStrength", CONCRETE["fck"]),
                            prop("YoungModulus", CONCRETE["E"]), prop("PoissonRatio", CONCRETE["nu"]),
                            prop("MassDensity", CONCRETE["rho"]), prop("TensileStrength", CONCRETE["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Encepado", PredefinedType="NOTDEFINED")
# pilotes como apoyos puntuales
nodes = []
for nm, x in [("P1", -A / 2), ("P2", A / 2)]:
    vp = f.create_entity("IfcVertexPoint",
                         VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, 0., 0.)))
    bc = f.create_entity("IfcBoundaryNodeCondition", Name="pilote",
                         TranslationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=True))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=nm,
        Representation=f.create_entity("IfcProductDefinitionShape",
            Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])]),
        AppliedCondition=bc)
    nodes.append(conn)

cap = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="ENCEPADO",
                      PredefinedType="SHELL", Thickness=H)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[cap], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=nodes + [cap], RelatingGroup=analysis)
pset_for(cap, "Pset_Estructurando_Encepado",
         {"SeparacionPilotes": A, "Canto": H, "Ancho": B, "LadoPilar": C_COL,
          "DiametroPilote": D_PILOTE, "Material": CONCRETE["name"], "TipoRegionD": "encepado_2_pilotes"})
pset_for(cap, "Pset_Estructurando_Carga_Pilar_G", {"Caso": "G", "N_N": N_G})
pset_for(cap, "Pset_Estructurando_Carga_Pilar_Q", {"Caso": "Q", "N_N": N_Q})

f.write(OUT)
print("IFC encepado escrito en:", OUT)
print(f"  a={A} h={H} b={B}  pilar={C_COL} pilote Ø{D_PILOTE}  N_G={N_G/1e3} N_Q={N_Q/1e3} kN")
