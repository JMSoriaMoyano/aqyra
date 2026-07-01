"""
Genera un IFC4 3D con el dominio de analisis estructural de un MODULO de edificio:
  - 4 pilares HEB 200 (S275)            -> IfcStructuralCurveMember
  - 4 vigas perimetrales IPE 330 (S275) -> IfcStructuralCurveMember
  - 1 losa HA C30/37 t=0.20 m           -> IfcStructuralSurfaceMember
  - Apoyos: 4 bases de pilar empotradas
  - Cargas de superficie sobre la losa: G (perm.) y Q (uso)

Convencion: ejes X,Y horizontales; Z vertical; gravedad -Z. Unidades SI (m, N).
La losa se define por sus 4 esquinas + espesor + tamano de malla en un Pset; el
mallado en elementos finitos lo realiza el solver (separacion modelo/malla).

Geometria: vano Lx = Ly = 5.0 m, altura H = 4.0 m.
"""
import ifcopenshell
import ifcopenshell.guid

Lx, Ly, H = 5.0, 5.0, 4.0
T_LOSA = 0.20
MESH = 0.50

HEB200 = dict(name="HEB 200", A=7.808e-3, Iy=5.696e-5, Iz=2.003e-5, J=5.95e-7,
              h=0.200, Wply=6.425e-4, Wely=5.696e-4, Avz=24.83e-4, clase=1)
IPE330 = dict(name="IPE 330", A=6.261e-3, Iy=1.177e-4, Iz=7.881e-6, J=2.815e-7,
              h=0.330, Wply=8.044e-4, Wely=7.131e-4, Avz=30.81e-4, clase=1)

STEEL = dict(name="S275JR", E=210e9, nu=0.3, rho=7850.0, fy=275e6, G=80.77e9)
CONCRETE = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, G=13.68e9,
                fctm=2.9e6)

# Cargas de superficie (N/m2), hacia abajo (signo negativo en Z)
G_SUP = 2.0e3   # carga permanente superpuesta (acabados, tabiqueria)
Q_SUP = 3.0e3   # sobrecarga de uso (Cat. B oficinas)

OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase2-laminas/proyecto-demo/modulo_demo.ifc"

f = ifcopenshell.file(schema="IFC4")
def guid():
    return ifcopenshell.guid.new()

length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Modulo demo Fase 2",
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


def material(props):
    mat = f.create_entity("IfcMaterial", Name=props["name"])
    pr = [make_prop("YoungModulus", props["E"]), make_prop("ShearModulus", props["G"]),
          make_prop("PoissonRatio", props["nu"]), make_prop("MassDensity", props["rho"])]
    if "fy" in props:
        pr.append(make_prop("YieldStress", props["fy"]))
    if "fck" in props:
        pr.append(make_prop("CompressiveStrength", props["fck"]))
        pr.append(make_prop("TensileStrength", props["fctm"]))
    f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical",
                    Material=mat, Properties=pr)
    return mat


mat_steel = material(STEEL)
mat_conc = material(CONCRETE)

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Modelo analitico modulo", PredefinedType="NOTDEFINED")


def vertex(x, y, z):
    p = f.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y), float(z)))
    return f.create_entity("IfcVertexPoint", VertexGeometry=p)


def topo_rep(items, rep_type):
    return f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                           RepresentationIdentifier="Reference",
                           RepresentationType=rep_type, Items=items)


# ---- Nodos -----------------------------------------------------------------
node_coords = {
    "N1": (0.0, 0.0, 0.0), "N2": (Lx, 0.0, 0.0), "N3": (Lx, Ly, 0.0), "N4": (0.0, Ly, 0.0),
    "N5": (0.0, 0.0, H),   "N6": (Lx, 0.0, H),   "N7": (Lx, Ly, H),   "N8": (0.0, Ly, H),
}
support = {n: (True,) * 6 for n in ("N1", "N2", "N3", "N4")}
verts, members, nodes = {}, {}, {}
for nid, (x, y, z) in node_coords.items():
    vp = vertex(x, y, z); verts[nid] = vp
    bc = None
    if nid in support:
        bc = f.create_entity("IfcBoundaryNodeCondition", Name="empotramiento",
                **{f"{k}Stiffness{ax}": f.create_entity("IfcBoolean", wrappedValue=True)
                   for k in ("Translational", "Rotational") for ax in "XYZ"})
    nodes[nid] = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=nid,
        Representation=f.create_entity("IfcProductDefinitionShape",
                                       Representations=[topo_rep([vp], "Vertex")]),
        AppliedCondition=bc)

# ---- Barras ----------------------------------------------------------------
members_def = {
    "C1": ("N1", "N5", HEB200, "pilar"), "C2": ("N2", "N6", HEB200, "pilar"),
    "C3": ("N3", "N7", HEB200, "pilar"), "C4": ("N4", "N8", HEB200, "pilar"),
    "V1": ("N5", "N6", IPE330, "viga"), "V2": ("N6", "N7", IPE330, "viga"),
    "V3": ("N7", "N8", IPE330, "viga"), "V4": ("N8", "N5", IPE330, "viga"),
}
for mid, (ni, nj, sec, kind) in members_def.items():
    edge = f.create_entity("IfcEdge", EdgeStart=verts[ni], EdgeEnd=verts[nj])
    mb = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name=mid,
        PredefinedType="RIGID_JOINED_MEMBER",
        Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
        Representation=f.create_entity("IfcProductDefinitionShape",
                                       Representations=[topo_rep([edge], "Edge")]))
    members[mid] = mb
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                    RelatedObjects=[mb], RelatingMaterial=mat_steel)
    pset_for(mb, "Pset_Estructurando_Analisis", {
        "Seccion": sec["name"], "Tipo": kind, "NodoInicial": ni, "NodoFinal": nj,
        "A": sec["A"], "Iy": sec["Iy"], "Iz": sec["Iz"], "J": sec["J"],
        "Wply": sec["Wply"], "Wely": sec["Wely"], "h": sec["h"],
        "Avz": sec["Avz"], "clase": sec["clase"]})

# ---- Losa (IfcStructuralSurfaceMember) -------------------------------------
slab = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="LOSA1",
                       PredefinedType="SHELL", Thickness=T_LOSA)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                RelatedObjects=[slab], RelatingMaterial=mat_conc)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=list(members.values()) + list(nodes.values()) + [slab],
                RelatingGroup=analysis)
pset_for(slab, "Pset_Estructurando_Superficie", {
    "Esquinas": "N5,N6,N7,N8", "Espesor": T_LOSA, "TamanoMalla": MESH,
    "Material": CONCRETE["name"], "Apoyo": "bordes sobre vigas"})
pset_for(slab, "Pset_Estructurando_Carga_Superficie_G",
         {"Caso": "G", "qz_N_m2": -G_SUP})
pset_for(slab, "Pset_Estructurando_Carga_Superficie_Q",
         {"Caso": "Q", "qz_N_m2": -Q_SUP})

f.write(OUT)
print("IFC 3D escrito en:", OUT)
print("Entidades:", len(list(f)))
