"""
CASO 7 - Muro de carga (esbeltez EC2) + muro de contencion en mensula (EC7 DA-2*).
IFC4 ORTODOXO del dominio de analisis estructural.

Modelo (sintetico, realista): un mismo IFC con DOS elementos que el agente debe
CLASIFICAR y ENRUTAR a modulos distintos (igual pauta multi-elemento de casos 2-5):

  A) MURO DE CARGA  ->  modulo 'laminas' (muro de carga, EC2 esbeltez).
     Muro de hormigon C25/30, altura H = 3,0 m, espesor t = 0,20 m (faja de 1,0 m),
     arriostrado, con carga vertical EXCENTRICA de cabeza (forjado superior).
       - IfcStructuralSurfaceMember vertical (plano Y=0; IfcFaceSurface/IfcPolyLoop,
         4 esquinas; Thickness = 0,20) + material por IfcRelAssociatesMaterial.
       - Apoyos: base e intrados de coronacion por IfcStructuralPointConnection +
         IfcBoundaryNodeCondition.
       - CARGA de cabeza N + M (excentricidad) por IfcStructuralPointAction +
         IfcStructuralLoadSingleForce (ForceZ = -N, MomentY = N*e), en grupos G y Q
         (IfcStructuralLoadGroup) -> MISMA pauta ortodoxa que la carga de cabeza del
         pilar del caso 5.

  B) MURO DE CONTENCION EN MENSULA (T-invertida) -> modulo 'muros-contencion' (EC7).
     Hormigon C30/37; alzado Hm = 5,0 m, espesor 0,40 m; zapata canto 0,50 m,
     puntera 1,0 m, talon 2,0 m, B = 3,4 m; relleno granular con sobrecarga.
       - ALZADO como IfcStructuralSurfaceMember vertical (plano X = x_alz;
         IfcFaceSurface/IfcPolyLoop; Thickness = 0,40) + material.
       - DATOS SIN ENTIDAD IFC ESTANDAR (se mantienen como Pset, igual que el
         R_d/k_s del caso 5 y los conectores/chapa del caso 6, porque NO hay
         entidad de analisis estructural estandar para la geometria en T de la
         cimentacion ni para los parametros del terreno):
           Pset_Estructurando_Muro     (geometria T-invertida: alzado, zapata,
                                         puntera, talon, B, Df, tipo).
           Pset_Estructurando_Terreno   (gamma, phi, c, beta, delta, pasivo,
                                         base, R_d, freatico).
           Pset_Estructurando_Carga_Muro_q (sobrecarga sobre el relleno).

El IFC es ORTODOXO: usa entidades estandar para muros (superficies), materiales,
apoyos y la carga axil de cabeza; los unicos datos no estandar son el terreno y la
geometria de la zapata en T (inherentes al problema, sin entidad de analisis).

Unidades SI (m, N, Pa). Plano XY horizontal, Z vertical, gravedad -Z.
"""
import os
import ifcopenshell
import ifcopenshell.guid

# ---------------- MURO DE CARGA (laminas, EC2 esbeltez) ----------------
MC = dict(H=3.0, t=0.20, ancho=1.0)         # altura, espesor, faja (m)
MC_N_G, MC_N_Q = 250e3, 120e3               # axil de cabeza por metro (N): perm / var
MC_ECC = 0.025                              # excentricidad de cabeza (m) -> M = N*e

# ---------------- MURO DE CONTENCION (muros-contencion, EC7 DA-2*) ----------------
MR = dict(tipo="mensula", Hm=5.0, t_alz=0.40, e_z=0.50,
          puntera=1.0, talon=2.0, Df=0.80)
MR["B"] = MR["puntera"] + MR["t_alz"] + MR["talon"]   # 3.40 m
TERR = dict(metodo="rankine", gamma=19e3, phi=30.0, c=0.0, beta=0.0, delta=20.0,
            phi_pas=30.0, gamma_pas=19e3, f_pas=0.5, phi_base=30.0, adh_base=0.0,
            Rd=300e3, nf=10.0, gamma_w=9.81e3)
MR_Q = 10e3                                 # sobrecarga sobre el relleno (Pa)

# materiales
C2530 = dict(name="C25/30", fck=25e6, fctm=2.6e6, E=31e9, nu=0.2, rho=2500.0, G=12.9e9)
C3037 = dict(name="C30/37", fck=30e6, fctm=2.9e6, E=33e9, nu=0.2, rho=2500.0, G=13.75e9)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-07.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 7 - Muro de carga + muro de contencion",
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


def material(m, psetname, extra):
    mat = f.create_entity("IfcMaterial", Name=m["name"])
    props = [prop("YoungModulus", m["E"]), prop("ShearModulus", m["G"]),
             prop("PoissonRatio", m["nu"]), prop("MassDensity", m["rho"])]
    props += extra(m)
    f.create_entity("IfcMaterialProperties", Name=psetname, Material=mat, Properties=props)
    return mat


c2530 = material(C2530, "Pset_MaterialMechanical_C2530",
                 lambda m: [prop("CompressiveStrength", m["fck"]), prop("TensileStrength", m["fctm"])])
c3037 = material(C3037, "Pset_MaterialMechanical_C3037",
                 lambda m: [prop("CompressiveStrength", m["fck"]), prop("TensileStrength", m["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Muros caso 7", PredefinedType="LOADING_3D")


def vertex(x, y, z):
    return f.create_entity("IfcVertexPoint",
                           VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(x, y, z)))


def bc(tx, ty, tz, rx=False, ry=False, rz=False):
    B = lambda v: f.create_entity("IfcBoolean", wrappedValue=bool(v))
    return f.create_entity("IfcBoundaryNodeCondition", Name="apoyo",
                           TranslationalStiffnessX=B(tx), TranslationalStiffnessY=B(ty),
                           TranslationalStiffnessZ=B(tz), RotationalStiffnessX=B(rx),
                           RotationalStiffnessY=B(ry), RotationalStiffnessZ=B(rz))


def point_connection(name, x, y, z, cond=None):
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Vertex",
                        Items=[vertex(x, y, z)])])
    return f.create_entity("IfcStructuralPointConnection", GlobalId=guid(), Name=name,
                           Representation=rep, AppliedCondition=cond)


def surface_member(name, corners, thickness, mat, normal):
    poly = f.create_entity("IfcPolyLoop", Polygon=[
        f.create_entity("IfcCartesianPoint", Coordinates=c) for c in corners])
    face_bound = f.create_entity("IfcFaceOuterBound", Bound=poly, Orientation=True)
    plane = f.create_entity("IfcPlane", Position=f.create_entity("IfcAxis2Placement3D",
        Location=f.create_entity("IfcCartesianPoint", Coordinates=corners[0]),
        Axis=f.create_entity("IfcDirection", DirectionRatios=normal),
        RefDirection=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.))))
    face = f.create_entity("IfcFaceSurface", Bounds=[face_bound], FaceSurface=plane, SameSense=True)
    rep = f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
                        RepresentationIdentifier="Reference", RepresentationType="Face", Items=[face])])
    sm = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name=name,
                         PredefinedType="SHELL", Thickness=thickness, Representation=rep)
    f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[sm], RelatingMaterial=mat)
    return sm


def load_group(name, permanent):
    return f.create_entity("IfcStructuralLoadGroup", GlobalId=guid(), Name=name,
                           PredefinedType="LOAD_GROUP",
                           ActionType="PERMANENT_G" if permanent else "VARIABLE_Q",
                           ActionSource="DEAD_LOAD_G" if permanent else "LIVE_LOAD_Q")


def point_action(name, node, fz, my, group):
    load = f.create_entity("IfcStructuralLoadSingleForce", Name=name + "_F",
                           ForceX=0.0, ForceY=0.0, ForceZ=fz,
                           MomentX=0.0, MomentY=my, MomentZ=0.0)
    act = f.create_entity("IfcStructuralPointAction", GlobalId=guid(), Name=name,
                          AppliedLoad=load, GlobalOrLocal="GLOBAL_COORDS")
    f.create_entity("IfcRelConnectsStructuralActivity", GlobalId=guid(),
                    RelatingElement=node, RelatedStructuralActivity=act)
    f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                    RelatedObjects=[act], RelatingGroup=group)


# ================= A) MURO DE CARGA (laminas, EC2 esbeltez) =================
# Superficie vertical en el plano Y=0; faja de 1,0 m de ancho, altura 3,0 m.
mc_corners = [(0.0, 0.0, 0.0), (MC["ancho"], 0.0, 0.0),
              (MC["ancho"], 0.0, MC["H"]), (0.0, 0.0, MC["H"])]
muro_carga = surface_member("Muro_carga", mc_corners, MC["t"], c2530, (0., 1., 0.))
pset_for(muro_carga, "Pset_Estructurando_MuroCarga",
         {"Tipo": "muro_carga", "Altura_m": MC["H"], "Espesor_m": MC["t"],
          "Ancho_m": MC["ancho"], "Arriostrado": 1, "Excentricidad_cabeza_m": MC_ECC})
# nodos: base empotrada en el plano (T,T,T) y coronacion arriostrada lateralmente
mc_base = point_connection("MC_base", MC["ancho"] / 2, 0.0, 0.0, bc(True, True, True))
mc_top = point_connection("MC_cabeza", MC["ancho"] / 2, 0.0, MC["H"], bc(True, True, False))
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=[muro_carga, mc_base, mc_top], RelatingGroup=analysis)
# carga de cabeza N + M = N*e (excentricidad), en grupos G y Q (como el pilar del caso 5)
point_action("Ncab_G", mc_top, -MC_N_G, MC_N_G * MC_ECC, load_group("Ncab_G", True))
point_action("Ncab_Q", mc_top, -MC_N_Q, MC_N_Q * MC_ECC, load_group("Ncab_Q", False))

# ============ B) MURO DE CONTENCION EN MENSULA (muros-contencion, EC7) ============
# Alzado como superficie vertical en el plano X = x_alz (trasdos del muro).
X0 = 10.0                                    # desplazado en X para separar del muro de carga
x_alz = X0 + MR["puntera"]                   # cara de la puntera + arranque del alzado
z0 = MR["e_z"]                               # arranque del alzado sobre la zapata
z1 = z0 + MR["Hm"]
mr_corners = [(x_alz, 0.0, z0), (x_alz, 1.0, z0), (x_alz, 1.0, z1), (x_alz, 0.0, z1)]
muro_cont = surface_member("Muro_contencion", mr_corners, MR["t_alz"], c3037, (1., 0., 0.))
# DATOS SIN ENTIDAD ESTANDAR (Pset, como R_d/k_s del caso 5): geometria T + terreno + q
pset_for(muro_cont, "Pset_Estructurando_Muro",
         {"Tipo": MR["tipo"], "AlturaAlzado_m": MR["Hm"], "EspesorAlzado_m": MR["t_alz"],
          "CantoZapata_m": MR["e_z"], "Puntera_m": MR["puntera"], "Talon_m": MR["talon"],
          "AnchoZapata_m": MR["B"], "ProfTierrasDelante_m": MR["Df"]})
pset_for(muro_cont, "Pset_Estructurando_Terreno",
         {"Metodo": TERR["metodo"], "Gamma_N_m3": TERR["gamma"], "Phi_grados": TERR["phi"],
          "Cohesion_Pa": TERR["c"], "Beta_grados": TERR["beta"], "DeltaMuro_grados": TERR["delta"],
          "PhiPasivo_grados": TERR["phi_pas"], "GammaPasivo_N_m3": TERR["gamma_pas"],
          "FraccionPasivo": TERR["f_pas"], "PhiBase_grados": TERR["phi_base"],
          "AdherenciaBase_Pa": TERR["adh_base"], "Rd_Pa": TERR["Rd"],
          "NivelFreatico_m": TERR["nf"], "GammaAgua_N_m3": TERR["gamma_w"]})
pset_for(muro_cont, "Pset_Estructurando_Carga_Muro_q", {"Sobrecarga_Pa": MR_Q})
# nodo de base del alzado (empotramiento en la zapata) -> mensula vertical
mr_base = point_connection("MR_base", x_alz, 0.5, z0, bc(True, True, True, True, True, True))
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(),
                RelatedObjects=[muro_cont, mr_base], RelatingGroup=analysis)

f.write(OUT)
print("IFC caso 7 escrito en:", OUT)
print("  A) Muro de carga C25/30 H=%.1f t=%.2f m  N_cab G=%.0f Q=%.0f kN  e=%.0f mm" % (
    MC["H"], MC["t"], MC_N_G / 1e3, MC_N_Q / 1e3, MC_ECC * 1e3))
print("  B) Muro contencion C30/37 mensula Hm=%.1f t_alz=%.2f B=%.2f m  (puntera %.1f / talon %.1f)" % (
    MR["Hm"], MR["t_alz"], MR["B"], MR["puntera"], MR["talon"]))
print("     Terreno phi=%.0f gamma=%.0f kN/m3  q=%.0f kPa  R_d=%.0f kPa" % (
    TERR["phi"], TERR["gamma"] / 1e3, MR_Q / 1e3, TERR["Rd"] / 1e3))
