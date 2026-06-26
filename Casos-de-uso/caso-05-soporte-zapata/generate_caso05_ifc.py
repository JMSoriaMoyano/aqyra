"""
CASO 5 - Soporte de hormigon + ZAPATA AISLADA. IFC4 ORTODOXO del dominio de
analisis estructural: CADENA pilar -> cimiento sobre LECHO ELASTICO (Winkler, EC7).

Modelo (sintetico, realista):
  - Pilar de hormigon C30/37, seccion 0,40 x 0,40 m, altura 3,0 m, arrancando del
    centro de la zapata (nodo base) hasta la cabeza (nodo de carga).
        IfcStructuralCurveMember vertical + IfcMaterialProfileSet ->
        IfcMaterialProfile -> IfcRectangleProfileDef (0,40 x 0,40).
  - Zapata aislada C30/37, B x B = 2,5 x 2,5 m, canto 0,60 m.
        IfcStructuralSurfaceMember (Thickness=0,60) con representacion
        IfcFaceSurface / IfcPolyLoop (4 esquinas en z=0) + material por
        IfcRelAssociatesMaterial.
  - LECHO ELASTICO (Winkler): el apoyo del terreno se expresa como RESORTES
    verticales en los nodos de la zapata mediante IfcBoundaryNodeCondition con
    rigidez TranslationalStiffnessZ = ks * area_tributaria (IfcLinearStiffnessMeasure,
    N/m). Modulo de balasto ks = 40 MN/m3. La resistencia de calculo del terreno
    Rd = 250 kPa se aporta como dato geotecnico (no existe entidad IFC estandar de
    analisis para la capacidad portante del suelo).
  - Cargas en CABEZA de pilar (gravedad -Z): IfcStructuralLoadGroup (G, Q) +
    IfcStructuralPointAction + IfcStructuralLoadSingleForce, con axil y momento:
        G: N = -700 kN, Mx = 80 kN.m (excentricidad)
        Q: N = -250 kN
    El axil baja por el pilar a la zapata (cadena pilar->cimiento) y se reparte al
    terreno por el lecho elastico.

Interes del caso: validar la CADENA pilar->cimiento (bajada de carga), el reparto
de presiones del terreno por Winkler (presion = ks*asiento), las comprobaciones
geotecnicas EC7 (hundimiento DA-2*/3, sin vuelco con e < B/6) y el armado EC2 de
la zapata (flexion + punzonamiento del pilar).

Entidades ESTANDAR (sin Pset_Estructurando_* salvo el dato geotecnico Rd):
  - Pilar: IfcStructuralCurveMember + IfcEdge (nodos base/cabeza) +
    IfcMaterialProfileSet -> IfcRectangleProfileDef.
  - Zapata: IfcStructuralSurfaceMember + IfcFaceSurface/IfcPolyLoop + material.
  - Lecho elastico: IfcStructuralPointConnection (nodos de la zapata) +
    IfcBoundaryNodeCondition con rigidez de muelle (N/m).
  - Cargas: IfcStructuralLoadGroup + IfcStructuralPointAction +
    IfcStructuralLoadSingleForce (FZ, MX) en la cabeza del pilar.
Unidades SI (m, N). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

B = 2.5                  # lado de la zapata (m)
T_ZAP = 0.60             # canto de la zapata (m)
C_PIL = 0.40             # lado del pilar (m)
H_PIL = 3.0              # altura del pilar (m)
KS = 40e6               # modulo de balasto (N/m3)
RD_SUELO = 250e3        # resistencia de calculo del terreno (Pa)
N_G = 700e3             # axil permanente en cabeza (N)
N_Q = 250e3             # axil variable en cabeza (N)
MX_G = 80e3            # momento permanente (N.m), excentricidad en X
XC, YC = B / 2.0, B / 2.0

CONC = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=33000e6, nu=0.2, rho=2500.0,
            G=33000e6 / (2 * (1 + 0.2)))

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-05.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 5 - Soporte + zapata aislada",
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
                           Name="Soporte + zapata caso 5", PredefinedType="LOADING_3D")


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


# --- nodos de la zapata (esquinas) con LECHO ELASTICO (muelles Winkler) ---
# rigidez del muelle por nodo de esquina = ks * area_tributaria_de_esquina = ks*(B/2)^2
k_corner = KS * (B / 2.0) ** 2          # N/m
corners = {"Z1": (0., 0., 0.), "Z2": (B, 0., 0.), "Z3": (B, B, 0.), "Z4": (0., B, 0.)}
zap_nodes = []
for nm, (x, y, z) in corners.items():
    bc = f.create_entity("IfcBoundaryNodeCondition", Name="lecho_elastico",
                         TranslationalStiffnessX=f.create_entity("IfcBoolean", wrappedValue=False),
                         TranslationalStiffnessY=f.create_entity("IfcBoolean", wrappedValue=False),
                         TranslationalStiffnessZ=f.create_entity("IfcLinearStiffnessMeasure", wrappedValue=k_corner))
    zap_nodes.append(point_connection(nm, x, y, z, bc))

# --- zapata: IfcStructuralSurfaceMember + IfcFaceSurface/IfcPolyLoop ---
poly = f.create_entity("IfcPolyLoop", Polygon=[
    f.create_entity("IfcCartesianPoint", Coordinates=c) for c in
    [(0., 0., 0.), (B, 0., 0.), (B, B, 0.), (0., B, 0.)]])
face_bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
    Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)),
    Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
    RefDirection=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.))))
face = f.create_entity("IfcFaceSurface", Bounds=[face_bound], FaceSurface=plane, SameSense=True)
zap_rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
zapata = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="Zapata",
                         PredefinedType="SHELL", Thickness=T_ZAP, Representation=zap_rep)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[zapata], RelatingMaterial=mat)
# dato geotecnico (Rd) -- no hay entidad IFC estandar de capacidad portante
pset_for(zapata, "Pset_Estructurando_Suelo", {"Rd_suelo_Pa": RD_SUELO, "ModuloBalasto_N_m3": KS})

# --- PILAR: IfcStructuralCurveMember vertical + IfcRectangleProfileDef ---
n_base = point_connection("P_base", XC, YC, 0.0)
n_head = point_connection("P_cabeza", XC, YC, H_PIL)
edge = f.create_entity("IfcEdge",
    EdgeStart=vertex(XC, YC, 0.0), EdgeEnd=vertex(XC, YC, H_PIL))
pil_rep = f.create_entity("IfcProductDefinitionShape", Representations=[
    f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                    RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])])
pilar = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="Pilar",
                        PredefinedType="RIGID_JOINED_MEMBER", Representation=pil_rep)
rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName="0.40x0.40",
                       XDim=C_PIL, YDim=C_PIL)
mprof = f.create_entity("IfcMaterialProfile", Name="Pilar 0.40x0.40", Material=mat, Profile=rect)
mpset = f.create_entity("IfcMaterialProfileSet", Name="Seccion pilar", MaterialProfiles=[mprof])
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[pilar], RelatingMaterial=mpset)

# --- todos los objetos al modelo de analisis ---
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=zap_nodes + [n_base, n_head, zapata, pilar], RelatingGroup=analysis)

# --- cargas en cabeza de pilar (G y Q) ---
def load_group(name, pred):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP",
                           ActionType="PERMANENT_G" if pred == "G" else "VARIABLE_Q",
                           ActionSource="DEAD_LOAD_G" if pred == "G" else "LIVE_LOAD_Q")

def point_action(name, node, fz, mx, group):
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name + "_F",
                           ForceX=0.0, ForceY=0.0, ForceZ=fz,
                           MomentX=mx, MomentY=0.0, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                    RelatedObjects=[act], RelatingGroup=group)

gG = load_group("G", "G")
gQ = load_group("Q", "Q")
point_action("N_G", n_head, -N_G, MX_G, gG)
point_action("N_Q", n_head, -N_Q, 0.0, gQ)

f.write(OUT)
print("IFC caso 5 escrito en:", OUT)
print("  Pilar %.2fx%.2f H=%.1f  Zapata %.1fx%.1f t=%.2f" % (C_PIL, C_PIL, H_PIL, B, B, T_ZAP))
print("  N_G=%.0f N_Q=%.0f kN  Mx_G=%.0f kN.m  ks=%.0f MN/m3  Rd=%.0f kPa"
      % (N_G/1e3, N_Q/1e3, MX_G/1e3, KS/1e6, RD_SUELO/1e3))
