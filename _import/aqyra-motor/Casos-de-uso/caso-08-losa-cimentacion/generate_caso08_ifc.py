"""
CASO 8 - LOSA DE CIMENTACION (RAFT) MULTIPILAR sobre LECHO ELASTICO (Winkler, EC7).
IFC4 ORTODOXO del dominio de analisis estructural.

Modelo (sintetico, realista):
  - Losa de cimentacion C30/37, BX x LY = 6,0 x 4,0 m, canto 0,60 m.
        IfcStructuralSurfaceMember (Thickness=0,60) con representacion
        IfcFaceSurface / IfcPolyLoop (4 esquinas en z=0) + material por
        IfcRelAssociatesMaterial.
  - RETICULA de 6 PILARES de hormigon C30/37, seccion 0,40 x 0,40 m, altura 3,0 m,
    en una malla 3x2 (x={1,3,5}, y={1,3}), arrancando de la losa (nodo base z=0)
    hasta la cabeza (nodo de carga z=3,0).
        IfcStructuralCurveMember vertical + IfcMaterialProfileSet ->
        IfcMaterialProfile -> IfcRectangleProfileDef (0,40 x 0,40).
  - LECHO ELASTICO (Winkler): el apoyo del terreno se expresa como RESORTES
    verticales en los nodos de esquina de la losa mediante IfcBoundaryNodeCondition
    con rigidez TranslationalStiffnessZ = ks * area_tributaria_de_esquina
    (= ks*(BX/2)*(LY/2)). Modulo de balasto ks = 40 MN/m3. Resistencia de calculo
    del terreno Rd = 300 kPa como dato geotecnico (no hay entidad IFC estandar de
    capacidad portante del suelo).
  - Cargas en CABEZA de cada pilar (gravedad -Z): IfcStructuralLoadGroup (G, Q) +
    IfcStructuralPointAction + IfcStructuralLoadSingleForce (FZ). Los pilares
    CENTRALES llevan mas carga que los de esquina -> ASIENTO DIFERENCIAL.

Interes del caso (proximo hilo): generalizar el solver de la zapata (1 pilar) al
RAFT MULTIPILAR ortodoxo -> placa Winkler con varias cargas, asiento diferencial,
flexion EC2 por bandas, punzonamiento de cada pilar y comprobacion del terreno
(presion media <= Rd). Brecha esperada: dar a 'cimentaciones/solver_raft.py' una
via ORTODOXA que lea la losa (superficie), identifique los pilares (barras
verticales) y baje sus cargas de cabeza (IfcStructuralPointAction), reconstruyendo
el lecho elastico de la rigidez de los nodos de borde (como el ks del caso 5),
manteniendo el Pset como respaldo.

Entidades ESTANDAR (sin Pset_Estructurando_* salvo el dato geotecnico):
  - Losa: IfcStructuralSurfaceMember + IfcFaceSurface/IfcPolyLoop + material.
  - Pilares: IfcStructuralCurveMember + IfcEdge + IfcMaterialProfileSet ->
    IfcRectangleProfileDef.
  - Lecho elastico: IfcStructuralPointConnection (esquinas) + IfcBoundaryNodeCondition.
  - Cargas: IfcStructuralLoadGroup + IfcStructuralPointAction + IfcStructuralLoadSingleForce.
Se conservan Pset_Estructurando_Losa y _Pilar_* como respaldo (compatibilidad con
el solver actual basado en Pset).
Unidades SI (m, N). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

BX = 6.0                 # dimension X de la losa (m)
LY = 4.0                 # dimension Y de la losa (m)
T_LOSA = 0.60            # canto de la losa (m)
C_PIL = 0.40             # lado del pilar (m)
H_PIL = 3.0              # altura del pilar (m)
MESH = 0.25             # tamano de malla de la placa (m)
KS = 40e6               # modulo de balasto (N/m3)
RD_SUELO = 300e3        # resistencia de calculo del terreno (Pa)

# reticula de pilares 3x2: (x, y, N_G_N, N_Q_N)  -- centrales mas cargados
PILARES = [
    ("P11", 1.0, 1.0, 550e3, 180e3),
    ("P21", 3.0, 1.0, 850e3, 300e3),
    ("P31", 5.0, 1.0, 550e3, 180e3),
    ("P12", 1.0, 3.0, 550e3, 180e3),
    ("P22", 3.0, 3.0, 850e3, 300e3),
    ("P32", 5.0, 3.0, 550e3, 180e3),
]

CONC = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=33000e6, nu=0.2, rho=2500.0,
            G=33000e6 / (2 * (1 + 0.2)))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-08.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 8 - Losa de cimentacion (raft) multipilar",
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


# --- material C30/37 ---
mat = f.create_entity("IfcMaterial", Name=CONC["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=mat,
                Properties=[prop("YoungModulus", CONC["E"]), prop("ShearModulus", CONC["G"]),
                            prop("PoissonRatio", CONC["nu"]), prop("MassDensity", CONC["rho"]),
                            prop("CompressiveStrength", CONC["fck"]), prop("TensileStrength", CONC["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Losa de cimentacion caso 8", PredefinedType="LOADING_3D")


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


# --- nodos de esquina de la losa con LECHO ELASTICO (muelles Winkler) ---
# rigidez del muelle por esquina = ks * area_tributaria_de_esquina = ks*(BX/2)*(LY/2)
k_corner = KS * (BX / 2.0) * (LY / 2.0)          # N/m
corners = {"L1": (0., 0., 0.), "L2": (BX, 0., 0.), "L3": (BX, LY, 0.), "L4": (0., LY, 0.)}
losa_nodes = []
for nm, (x, y, z) in corners.items():
    bc = f.create_entity("IfcBoundaryNodeCondition", Name="lecho_elastico",
                         TranslationalStiffnessX=f.create_entity("IfcBoolean", wrappedValue=False),
                         TranslationalStiffnessY=f.create_entity("IfcBoolean", wrappedValue=False),
                         TranslationalStiffnessZ=f.create_entity("IfcLinearStiffnessMeasure", wrappedValue=k_corner))
    losa_nodes.append(point_connection(nm, x, y, z, bc))

# --- losa: IfcStructuralSurfaceMember + IfcFaceSurface/IfcPolyLoop ---
poly = f.create_entity("IfcPolyLoop", Polygon=[
    f.create_entity("IfcCartesianPoint", Coordinates=c) for c in
    [(0., 0., 0.), (BX, 0., 0.), (BX, LY, 0.), (0., LY, 0.)]])
face_bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
    Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)),
    Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
    RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
face = f.create_entity("IfcFaceSurface", Bounds=[face_bound], FaceSurface=plane, SameSense=True)
losa_rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
losa = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="Losa_cimentacion",
                       PredefinedType="SHELL", Thickness=T_LOSA, Representation=losa_rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[losa], RelatingMaterial=mat)
# dato geotecnico (Rd, ks) -- no hay entidad IFC estandar de capacidad portante
pset_for(losa, "Pset_Estructurando_Suelo", {"Rd_suelo_Pa": RD_SUELO, "ModuloBalasto_N_m3": KS})
# Pset de respaldo (compatibilidad con el solver de raft basado en Pset)
pset_for(losa, "Pset_Estructurando_Losa",
         {"BX": BX, "LY": LY, "Espesor": T_LOSA, "TamanoMalla": MESH, "LadoPilar": C_PIL,
          "ModuloBalasto_N_m3": KS, "Rd_suelo_Pa": RD_SUELO, "Material": CONC["name"]})

# --- PILARES: IfcStructuralCurveMember vertical + IfcRectangleProfileDef ---
rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName="0.40x0.40",
                       XDim=C_PIL, YDim=C_PIL)


def load_group(name, pred):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP",
                           ActionType="PERMANENT_G" if pred == "G" else "VARIABLE_Q",
                           ActionSource="DEAD_LOAD_G" if pred == "G" else "LIVE_LOAD_Q")


def point_action(name, node, fz, group):
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name + "_F",
                           ForceX=0.0, ForceY=0.0, ForceZ=fz,
                           MomentX=0.0, MomentY=0.0, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                    RelatedObjects=[act], RelatingGroup=group)


gG = load_group("G", "G")
gQ = load_group("Q", "Q")

all_objs = list(losa_nodes) + [losa]
for i, (pnm, x, y, ng, nq) in enumerate(PILARES, start=1):
    n_base = point_connection("%s_base" % pnm, x, y, 0.0)
    n_head = point_connection("%s_cabeza" % pnm, x, y, H_PIL)
    edge = f.create_entity("IfcEdge", EdgeStart=vertex(x, y, 0.0), EdgeEnd=vertex(x, y, H_PIL))
    pil_rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])])
    pilar = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="Pilar_%s" % pnm,
                            PredefinedType="RIGID_JOINED_MEMBER", Representation=pil_rep)
    mprof = f.create_entity("IfcMaterialProfile", Name="Pilar 0.40x0.40", Material=mat, Profile=rect)
    mpset = f.create_entity("IfcMaterialProfileSet", Name="Seccion pilar %s" % pnm, MaterialProfiles=[mprof])
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[pilar], RelatingMaterial=mpset)
    point_action("N_G_%s" % pnm, n_head, -ng, gG)
    point_action("N_Q_%s" % pnm, n_head, -nq, gQ)
    # Pset de respaldo del pilar
    pset_for(losa, "Pset_Estructurando_Pilar_%d" % i,
             {"x": x, "y": y, "Lado": C_PIL, "N_G_N": ng, "N_Q_N": nq})
    all_objs += [n_base, n_head, pilar]

# --- todos los objetos al modelo de analisis ---
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=all_objs, RelatingGroup=analysis)

f.write(OUT)
sumG = sum(p[3] for p in PILARES)
sumQ = sum(p[4] for p in PILARES)
print("IFC caso 8 escrito en:", OUT)
print("  Losa %.1fx%.1f t=%.2f  |  %d pilares %.2fx%.2f H=%.1f" % (BX, LY, T_LOSA, len(PILARES), C_PIL, C_PIL, H_PIL))
print("  Sum N_G=%.0f kN  Sum N_Q=%.0f kN  ks=%.0f MN/m3  Rd=%.0f kPa"
      % (sumG / 1e3, sumQ / 1e3, KS / 1e6, RD_SUELO / 1e3))
