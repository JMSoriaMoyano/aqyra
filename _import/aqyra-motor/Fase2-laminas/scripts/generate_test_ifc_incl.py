"""
Genera un IFC4 de un ELEMENTO PLANO INCLINADO de hormigon (cubierta / forjado
inclinado a un agua), simplemente apoyado en sus 4 bordes.

  - Losa C30/37, longitud de faldon Lu = 6.0 m, ancho Lv = 5.0 m, canto 0.18 m
  - Inclinacion (pendiente) = 20 grados
  - Apoyo: 4 bordes simplemente apoyados (sobre muros/vigas de borde)
  - Cargas verticales (sobre area real de faldon): G superpuesta + Q/uso(nieve)

La geometria inclinada se describe por Lu, Lv y el angulo en un Pset; el solver
malla el plano y lo inclina. Unidades SI (m, N).
"""
import math
import ifcopenshell
import ifcopenshell.guid

LU, LV = 6.0, 5.0          # longitud de faldon (segun pendiente) y ancho
T = 0.18
MESH = 0.40
ANG = 20.0                 # grados

CONCRETE = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, G=13.68e9, fctm=2.9e6)
G_SUP = 1.5e3              # cubierta/acabados (N/m2 sobre area real)
Q_SUP = 1.0e3             # uso/nieve (N/m2 sobre area real, simplificado)
OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase2-laminas/proyecto-cubierta/cubierta.ifc"

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Cubierta inclinada demo",
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
                           Name="Cubierta", PredefinedType="NOTDEFINED")

# Esquinas 3D del faldon inclinado (para referencia/visualizacion)
th = math.radians(ANG)
corners3d = {"C1": (0.0, 0.0, 0.0), "C2": (LV, 0.0, 0.0),
             "C3": (LV, LU * math.cos(th), LU * math.sin(th)),
             "C4": (0.0, LU * math.cos(th), LU * math.sin(th))}
nodes = []
for nm, (x, y, z) in corners3d.items():
    vp = f.create_entity("IfcVertexPoint",
                         VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=nm,
        Representation=f.create_entity("IfcProductDefinitionShape",
            Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                RepresentationIdentifier="Reference", RepresentationType="Vertex", Items=[vp])]))
    nodes.append(conn)

slab = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="CUBIERTA",
                       PredefinedType="SHELL", Thickness=T)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[slab], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=nodes + [slab], RelatingGroup=analysis)
pset_for(slab, "Pset_Estructurando_Superficie_Inclinada",
         {"Lu": LU, "Lv": LV, "Espesor": T, "TamanoMalla": MESH, "AnguloGrados": ANG,
          "Material": CONCRETE["name"], "Apoyo": "4 bordes simplemente apoyados"})
pset_for(slab, "Pset_Estructurando_Carga_Vertical_G", {"Caso": "G", "qz_N_m2": -G_SUP})
pset_for(slab, "Pset_Estructurando_Carga_Vertical_Q", {"Caso": "Q", "qz_N_m2": -Q_SUP})

f.write(OUT)
print("IFC cubierta inclinada escrito en:", OUT)
print(f"  Lu={LU} Lv={LV} t={T} angulo={ANG} deg  Entidades:", len(list(f)))
