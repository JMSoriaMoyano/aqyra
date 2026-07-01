"""
Genera un IFC4 de prueba con el DOMINIO DE ANALISIS ESTRUCTURAL de un portico
plano de acero (2 pilares + 1 dintel). Incluye:
  - IfcStructuralAnalysisModel
  - Nodos  -> IfcStructuralPointConnection (topologia IfcVertexPoint + apoyos)
  - Barras -> IfcStructuralCurveMember (topologia IfcEdge + seccion + material)
  - Cargas -> IfcStructuralLoadCase / IfcStructuralLinearAction (G y Q)

Convencion de unidades del modelo analitico: m, N, N/m  (SI base).
Las propiedades de seccion y material se incrustan en Psets propios para una
relectura robusta, ademas de las entidades estandar del dominio.

Caso: portico de un vano.  Luz L = 6.0 m, altura H = 4.0 m.
  Pilares: HEB 200  (S275)
  Dintel : IPE 330  (S275)
  Apoyos : empotrados en bases de pilares.
  Cargas sobre dintel (gravitatoria, eje -Z global):
     G (permanente) = 12.0 kN/m
     Q (uso)        =  9.0 kN/m
"""
import time
import ifcopenshell
import ifcopenshell.guid

# ----------------------------------------------------------------------------
# Datos del caso (SI: m, N)
# ----------------------------------------------------------------------------
L = 6.0          # luz (m)
H = 4.0          # altura (m)

# Perfiles (propiedades en SI: m2, m4). Valores de catalogo (Arcelor / prontuario).
HEB200 = dict(name="HEB 200", A=7.808e-3, Iy=5.696e-5, Iz=2.003e-5, J=5.95e-7,
              h=0.200, Wply=6.425e-4, Wely=5.696e-4, Avz=24.83e-4, clase=1)  # Iy = eje fuerte
IPE330 = dict(name="IPE 330", A=6.261e-3, Iy=1.177e-4, Iz=7.881e-6, J=2.815e-7,
              h=0.330, Wply=8.044e-4, Wely=7.131e-4, Avz=30.81e-4, clase=1)

# Material S275
STEEL = dict(name="S275JR", E=210e9, nu=0.3, rho=7850.0, fy=275e6, G=80.77e9)

# Cargas distribuidas sobre el dintel (N/m), positivas hacia abajo
G_LIN = 12.0e3
Q_LIN = 9.0e3

OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase1-motor-calculo/proyecto-demo/portico_demo.ifc"

# ----------------------------------------------------------------------------
f = ifcopenshell.file(schema="IFC4")
def guid():
    return ifcopenshell.guid.new()

owner = None  # se omite OwnerHistory (opcional en IFC4 para muchas entidades)

# Unidades (m, N) ------------------------------------------------------------
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
unit_assignment = f.create_entity("IfcUnitAssignment", Units=[length, force])

# Contextos ------------------------------------------------------------------
ctx = f.create_entity("IfcGeometricRepresentationContext",
                      ContextType="Model", CoordinateSpaceDimension=3,
                      Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity(
                          "IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0.,0.,0.))))

project = f.create_entity("IfcProject", GlobalId=guid(), Name="Portico demo Fase 1",
                          UnitsInContext=unit_assignment,
                          RepresentationContexts=[ctx])

# Material + propiedades mecanicas (Pset estandar) ---------------------------
mat = f.create_entity("IfcMaterial", Name=STEEL["name"], Category="steel")
def make_prop(name, val):
    if isinstance(val, str):
        nominal = f.create_entity("IfcText", wrappedValue=val)
    else:
        nominal = f.create_entity("IfcReal", wrappedValue=float(val))
    return f.create_entity("IfcPropertySingleValue", Name=name, NominalValue=nominal)
mat_pset = f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical",
                           Material=mat,
                           Properties=[make_prop("YoungModulus", STEEL["E"]),
                                       make_prop("ShearModulus", STEEL["G"]),
                                       make_prop("PoissonRatio", STEEL["nu"]),
                                       make_prop("MassDensity", STEEL["rho"]),
                                       make_prop("YieldStress", STEEL["fy"])])

# Modelo de analisis estructural ---------------------------------------------
analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Modelo analitico portico",
                           PredefinedType="NOTDEFINED")

topo_ctx = ctx  # reutilizamos el contexto

# ---- Helpers ----------------------------------------------------------------
def vertex(x, y, z):
    p = f.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y), float(z)))
    return f.create_entity("IfcVertexPoint", VertexGeometry=p)

def topo_rep(items, rep_type):
    return f.create_entity("IfcTopologyRepresentation",
                           ContextOfItems=topo_ctx, RepresentationIdentifier="Reference",
                           RepresentationType=rep_type, Items=items)

def pset_for(obj, name, props):
    ps = f.create_entity("IfcPropertySet", GlobalId=guid(), Name=name,
                         HasProperties=[make_prop(k, v) for k, v in props.items()])
    f.create_entity("IfcRelDefinesByProperties", GlobalId=guid(),
                    RelatedObjects=[obj], RelatingPropertyDefinition=ps)
    return ps

# ---- Nodos (IfcStructuralPointConnection) -----------------------------------
# Coordenadas (m): plano XZ, Y=0
node_coords = {
    "N1": (0.0, 0.0, 0.0),   # base pilar izq (empotrado)
    "N2": (0.0, 0.0, H),     # cabeza pilar izq
    "N3": (L,   0.0, H),     # cabeza pilar der
    "N4": (L,   0.0, 0.0),   # base pilar der (empotrado)
}
support = {  # True = coaccion fija (rigida).  Orden: DX,DY,DZ,RX,RY,RZ
    "N1": (True, True, True, True, True, True),
    "N4": (True, True, True, True, True, True),
}
nodes = {}
verts = {}
for nid, (x, y, z) in node_coords.items():
    vp = vertex(x, y, z)
    verts[nid] = vp
    bc = None
    if nid in support:
        sx, sy, sz, rx, ry, rz = support[nid]
        bc = f.create_entity("IfcBoundaryNodeCondition", Name="empotramiento",
                             TranslationalStiffnessX=f.create_entity("IfcBoolean", wrappedValue=sx),
                             TranslationalStiffnessY=f.create_entity("IfcBoolean", wrappedValue=sy),
                             TranslationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=sz),
                             RotationalStiffnessX=f.create_entity("IfcBoolean", wrappedValue=rx),
                             RotationalStiffnessY=f.create_entity("IfcBoolean", wrappedValue=ry),
                             RotationalStiffnessZ=f.create_entity("IfcBoolean", wrappedValue=rz))
    conn = f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=nid,
                           Representation=f.create_entity("IfcProductDefinitionShape",
                                                          Representations=[topo_rep([vp], "Vertex")]),
                           AppliedCondition=bc)
    nodes[nid] = conn

# ---- Barras (IfcStructuralCurveMember) --------------------------------------
members_def = {
    "B1": ("N1", "N2", HEB200, "pilar"),
    "B2": ("N2", "N3", IPE330, "dintel"),
    "B3": ("N4", "N3", HEB200, "pilar"),
}
members = {}
for mid, (ni, nj, sec, kind) in members_def.items():
    edge = f.create_entity("IfcEdge", EdgeStart=verts[ni], EdgeEnd=verts[nj])
    mb = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name=mid,
                         PredefinedType="RIGID_JOINED_MEMBER",
                         Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 1., 0.)),
                         Representation=f.create_entity("IfcProductDefinitionShape",
                                                        Representations=[topo_rep([edge], "Edge")]))
    members[mid] = mb
    # Material
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(),
                    RelatedObjects=[mb], RelatingMaterial=mat)
    # Pset propio con la seccion y nodos (relectura robusta)
    pset_for(mb, "Pset_Estructurando_Analisis", {
        "Seccion": sec["name"], "Tipo": kind,
        "NodoInicial": ni, "NodoFinal": nj,
        "A": sec["A"], "Iy": sec["Iy"], "Iz": sec["Iz"], "J": sec["J"],
        "Wply": sec["Wply"], "Wely": sec["Wely"], "h": sec["h"],
        "Avz": sec["Avz"], "clase": sec["clase"],
    })

# Agrupar miembros y nodos en el modelo de analisis
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=list(members.values()) + list(nodes.values()),
                RelatingGroup=analysis)

# ---- Cargas (casos G y Q + acciones lineales sobre el dintel) ---------------
def linear_action(name, member, fz, case_obj):
    load = f.create_entity("IfcStructuralLoadLinearForce", Name=name,
                           LinearForceX=0.0, LinearForceY=0.0, LinearForceZ=float(fz))
    act = f.create_entity("IfcStructuralLinearAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS",
                          PredefinedType="NOTDEFINED")
    # vincular accion a la barra
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=member, RelatedStructuralActivity=act)
    # vincular accion al caso de carga
    case_obj.SourceOfResultGroup  # no-op
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                    RelatedObjects=[act], RelatingGroup=case_obj)
    # Pset con metadato de caso (relectura robusta)
    pset_for(act, "Pset_Estructurando_Carga",
             {"Caso": name, "Barra": member.Name, "Direccion": "GZ", "qz_N_m": float(fz)})
    return act

case_G = f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name="G",
                         PredefinedType="LOAD_GROUP", ActionType="PERMANENT_G",
                         ActionSource="DEAD_LOAD_G")
case_Q = f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name="Q",
                         PredefinedType="LOAD_GROUP", ActionType="VARIABLE_Q",
                         ActionSource="LIVE_LOAD_Q")

# fz negativo = hacia abajo (gravedad)
linear_action("G", members["B2"], -G_LIN, case_G)
linear_action("Q", members["B2"], -Q_LIN, case_Q)

f.write(OUT)
print("IFC escrito en:", OUT)
print("Entidades:", len(list(f)))
