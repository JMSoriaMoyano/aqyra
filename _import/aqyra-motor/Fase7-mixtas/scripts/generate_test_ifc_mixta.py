"""
Genera un IFC4 de una VIGA MIXTA acero-hormigon (EN 1994-1-1) con FORJADO
COLABORANTE (chapa nervada perpendicular a la viga), como IfcStructuralCurveMember
de acero con la losa, los conectores, los materiales y las cargas por fase en Psets.

Caso: viga secundaria biapoyada, construccion SIN APEAR (unpropped):
  - Fase de construccion: el perfil de acero solo resiste el peso del hormigon fresco
    y la sobrecarga de ejecucion.
  - Fase mixta: la seccion mixta resiste las cargas muertas adicionales y la sobrecarga.

Unidades SI (m, N, Pa).
"""
import os
import ifcopenshell
import ifcopenshell.guid

# --- Geometria del sistema ---
L = 8.0            # luz de la viga (m)
SEP = 3.0          # separacion entre vigas = ancho tributario (m)
N_ELEM = 16

# --- Perfil de acero (IPE 360, S275) ---
PERFIL = "IPE360"
STEEL = dict(name="S275", fy=275e6, E=210e9, nu=0.3, rho=7850.0, G=80.77e9)
SEC = dict(A=72.73e-4, h=0.360, b=0.170, tw=0.008, tf=0.0127,
           Iy=16270e-8, Wply=1019e-6, Avz=35.14e-4)   # Iy = inercia fuerte

# --- Losa colaborante (chapa nervada perpendicular) ---
HT = 0.12          # canto total de la losa (m)
HP = 0.058         # altura del nervio / canto de la chapa (m)
HC = HT - HP       # hormigon sobre nervios (m) = 0.062
B0 = 0.100         # anchura media del nervio (m)
NR = 1             # conectores por nervio
CONC = dict(name="C25/30", fck=25e6, E=31e9, nu=0.2, rho=2500.0, G=12.9e9, fctm=2.6e6)

# --- Conectores (pernos) ---
D_STUD = 0.019     # diametro del vastago (m)
HSC = 0.100        # altura del perno (m)
FU_STUD = 450e6    # resistencia ultima del perno (Pa)
SEP_STUD = 0.207   # separacion longitudinal de conectores (m) ~ 1 por nervio (paso de chapa)

# --- Cargas (kN/m2 sobre el forjado; el solver multiplica por SEP) ---
G_LOSA = 2.5e3     # peso propio losa colaborante (Pa) [fase construccion: hormigon fresco]
G2_PERM = 1.5e3    # carga muerta adicional (solados, tabiqueria) (Pa) [fase mixta]
Q_USO = 3.0e3      # sobrecarga de uso (Pa) [fase mixta]
QC_EJEC = 0.75e3   # sobrecarga de ejecucion (Pa) [fase construccion]

PROPPED = 0        # 0 = sin apear (unpropped); 1 = apeado

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "proyecto-viga-mixta", "viga_mixta.ifc"))

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Viga mixta demo",
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


steel = f.create_entity("IfcMaterial", Name=STEEL["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical", Material=steel,
                Properties=[prop("YoungModulus", STEEL["E"]), prop("ShearModulus", STEEL["G"]),
                            prop("PoissonRatio", STEEL["nu"]), prop("MassDensity", STEEL["rho"]),
                            prop("YieldStress", STEEL["fy"])])
conc = f.create_entity("IfcMaterial", Name=CONC["name"])
f.create_entity("IfcMaterialProperties", Name="Pset_MaterialMechanical_C", Material=conc,
                Properties=[prop("CompressiveStrength", CONC["fck"]), prop("YoungModulus", CONC["E"]),
                            prop("MassDensity", CONC["rho"]), prop("TensileStrength", CONC["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Viga mixta", PredefinedType="NOTDEFINED")
v0 = f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)))
vL = f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(L, 0., 0.)))
edge = f.create_entity("IfcEdge", EdgeStart=v0, EdgeEnd=vL)
viga = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="VIGA_MIXTA",
    PredefinedType="RIGID_JOINED_MEMBER",
    Axis=f.create_entity("IfcDirection", DirectionRatios=(0., 0., 1.)),
    Representation=f.create_entity("IfcProductDefinitionShape",
        Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])]))
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[viga], RelatingMaterial=steel)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[viga], RelatingGroup=analysis)

pset_for(viga, "Pset_Estructurando_VigaMixta",
         {"Luz_m": L, "Separacion_m": SEP, "NumElementos": N_ELEM, "Perfil": PERFIL,
          "MaterialAcero": STEEL["name"], "MaterialHormigon": CONC["name"], "Apeado": PROPPED,
          "A_m2": SEC["A"], "h_m": SEC["h"], "b_m": SEC["b"], "tw_m": SEC["tw"], "tf_m": SEC["tf"],
          "Iy_m4": SEC["Iy"], "Wply_m3": SEC["Wply"], "Avz_m2": SEC["Avz"]})
pset_for(viga, "Pset_Estructurando_Losa",
         {"ht_m": HT, "hp_m": HP, "hc_m": HC, "b0_m": B0, "nervios": "perpendicular", "nr": NR})
pset_for(viga, "Pset_Estructurando_Conectores",
         {"d_m": D_STUD, "hsc_m": HSC, "fu_Pa": FU_STUD, "sep_long_m": SEP_STUD})
pset_for(viga, "Pset_Estructurando_Cargas_Mixta",
         {"G_losa_Pa": G_LOSA, "G2_perm_Pa": G2_PERM, "Q_uso_Pa": Q_USO, "Qc_ejec_Pa": QC_EJEC})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
f.write(OUT)
print("IFC viga mixta escrito en:", OUT)
print("  Viga %s S275  L=%.1f m  separacion=%.1f m  (%s)" % (PERFIL, L, SEP, "apeada" if PROPPED else "sin apear"))
print("  Losa %s  ht=%.0f hp=%.0f hc=%.0f mm  conector D%.0f h%.0f mm sep=%.0f mm"
      % (CONC["name"], HT * 1e3, HP * 1e3, HC * 1e3, D_STUD * 1e3, HSC * 1e3, SEP_STUD * 1e3))
print("  Cargas kN/m2: G_losa=%.1f G2=%.1f Q=%.1f Qc=%.2f" % (G_LOSA / 1e3, G2_PERM / 1e3, Q_USO / 1e3, QC_EJEC / 1e3))
