"""
Genera un IFC4 de una LOSA PLANA (flat slab) de hormigon armado apoyada
DIRECTAMENTE sobre pilares (sin vigas). Aqui el PUNZONAMIENTO es el mecanismo
real que gobierna.

  - Losa C30/37 t=0.25 m, 10 x 10 m (2x2 vanos de 5 m)   -> IfcStructuralSurfaceMember
  - 9 pilares (malla 3x3) como apoyos puntuales            -> IfcStructuralPointConnection
    clasificados en interior / borde (edge) / esquina (corner)
  - Cargas de superficie: G superpuesta + Q de uso (autopeso lo anade el solver)

Convencion: X,Y horizontales; Z vertical; gravedad -Z. Unidades SI (m, N).
"""
import ifcopenshell
import ifcopenshell.guid

LX, LY = 10.0, 10.0
T = 0.25
MESH = 0.50
LADO_PILAR = 0.35
GRID = [0.0, 5.0, 10.0]

CONCRETE = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, G=13.68e9, fctm=2.9e6)
G_SUP = 2.0e3
Q_SUP = 3.0e3
OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase2-laminas/proyecto-losa-plana/losa_plana.ifc"

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new

length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Losa plana demo Fase 2",
                UnitsInContext=ua, RepresentationContexts=[ctx])


def make_prop(name, val):
    nominal = (f.create_entity("IfcText", wrappedValue=val) if isinstance(val, str)
               else f.create_entity("IfcReal", wrappedValue=float(val)))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)


def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[make_prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)


mat = f.create_entity("IfcMaterial", Name=CONCRETE["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=mat,
                Properties=[make_prop("YoungModulus", CONCRETE["E"]),
                            make_prop("ShearModulus", CONCRETE["G"]),
                            make_prop("PoissonRatio", CONCRETE["nu"]),
                            make_prop("MassDensity", CONCRETE["rho"]),
                            make_prop("CompressiveStrength", CONCRETE["fck"]),
                            make_prop("TensileStrength", CONCRETE["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Losa plana", PredefinedType="NOTDEFINED")


def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint",
                           VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))


def topo_rep(items, t):
    return f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                           RepresentationIdentifier="Reference", RepresentationType=t, Items=items)


def posicion(ix, iy):
    bordx = ix in (0, len(GRID) - 1)
    bordy = iy in (0, len(GRID) - 1)
    if bordx and bordy:
        return "corner"
    if bordx or bordy:
        return "edge"
    return "interior"


# --- pilares (apoyos puntuales) ---
pilares = []
corner_names = {}
n = 0
for iy, y in enumerate(GRID):
    for ix, x in enumerate(GRID):
        n += 1
        name = f"P{n}"
        vp = vertex(x, y, 0.0)
        bc = f.create_entity("IfcBoundaryNodeCondition", Name="apoyo pilar",
                             TranslationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=True))
        conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
            Representation=f.create_entity("IfcProductDefinitionShape", Representations=[topo_rep([vp], "Vertex")]),
            AppliedCondition=bc)
        pos = posicion(ix, iy)
        pset_for(conn, "Pset_Estructurando_Pilar",
                 {"Lado": LADO_PILAR, "Posicion": pos, "x": x, "y": y})
        pilares.append(conn)
        if (x in (0.0, LX)) and (y in (0.0, LY)):
            corner_names[(x, y)] = name

# --- losa ---
slab = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="LOSA_PLANA",
                       PredefinedType="SHELL", Thickness=T)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[slab], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=pilares + [slab], RelatingGroup=analysis)
esquinas = ",".join(corner_names[k] for k in [(0., 0.), (LX, 0.), (LX, LY), (0., LY)])
pset_for(slab, "Pset_Estructurando_Superficie",
         {"Esquinas": esquinas, "Espesor": T, "TamanoMalla": MESH,
          "Material": CONCRETE["name"], "Apoyo": "pilares (losa plana)"})
pset_for(slab, "Pset_Estructurando_Carga_Superficie_G", {"Caso": "G", "qz_N_m2": -G_SUP})
pset_for(slab, "Pset_Estructurando_Carga_Superficie_Q", {"Caso": "Q", "qz_N_m2": -Q_SUP})

f.write(OUT)
print("IFC losa plana escrito en:", OUT)
print("Pilares:", len(pilares), "  Entidades:", len(list(f)))
