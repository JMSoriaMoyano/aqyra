"""
Genera un IFC4 de un PILOTE de hormigon (cimentacion profunda) como
IfcStructuralCurveMember vertical, con datos de terreno en un Pset.

  - Pilote C30/37 Ø600 mm, L = 12 m
  - Terreno: balasto horizontal kh, fuste unitario qs, punta unitaria qb
  - Cargas en cabeza: N (G,Q), H lateral (Q), momento (opcional)

Unidades SI (m, N, Pa).
"""
import ifcopenshell
import ifcopenshell.guid

D = 0.60
L = 12.0
N_ELEM = 24
KH = 15e6          # balasto horizontal (N/m3)
QS = 60e3          # resistencia de fuste unitaria (Pa)
QB = 2500e3        # resistencia de punta unitaria (Pa)

CONCRETE = dict(name="C30/37", fck=30e6, E=32.84e9, nu=0.2, rho=2500.0, G=13.68e9, fctm=2.9e6)
N_G, N_Q = 900e3, 300e3
H_Q = 80e3         # carga horizontal en cabeza (viento/sismo), caso Q
OUT = "/sessions/friendly-trusting-carson/mnt/Estrucutrando/Fase5-pilotes/proyecto-pilote/pilote.ifc"

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Pilote demo",
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
                Properties=[prop("CompressiveStrength", CONCRETE["fck"]), prop("YoungModulus", CONCRETE["E"]),
                            prop("ShearModulus", CONCRETE["G"]), prop("PoissonRatio", CONCRETE["nu"]),
                            prop("MassDensity", CONCRETE["rho"]), prop("TensileStrength", CONCRETE["fctm"])])

analysis = f.create_entity("IfcStructuralAnalysisModel", GlobalId=guid(),
                           Name="Pilote", PredefinedType="NOTDEFINED")
v0 = f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.)))
vL = f.create_entity("IfcVertexPoint", VertexGeometry=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., -L)))
edge = f.create_entity("IfcEdge", EdgeStart=v0, EdgeEnd=vL)
pilote = f.create_entity("IfcStructuralCurveMember", GlobalId=guid(), Name="PILOTE",
    PredefinedType="RIGID_JOINED_MEMBER",
    Axis=f.create_entity("IfcDirection", DirectionRatios=(1., 0., 0.)),
    Representation=f.create_entity("IfcProductDefinitionShape",
        Representations=[f.create_entity("IfcTopologyRepresentation", ContextOfItems=ctx,
            RepresentationIdentifier="Reference", RepresentationType="Edge", Items=[edge])]))
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[pilote], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[pilote], RelatingGroup=analysis)
pset_for(pilote, "Pset_Estructurando_Pilote",
         {"Diametro": D, "Longitud": L, "Material": CONCRETE["name"], "NumElementos": N_ELEM,
          "BalastoHorizontal_N_m3": KH, "FusteUnit_Pa": QS, "PuntaUnit_Pa": QB, "Cabeza": "libre"})
pset_for(pilote, "Pset_Estructurando_Carga_Pilote_G", {"Caso": "G", "N_N": N_G, "H_N": 0.0, "M_Nm": 0.0})
pset_for(pilote, "Pset_Estructurando_Carga_Pilote_Q", {"Caso": "Q", "N_N": N_Q, "H_N": H_Q, "M_Nm": 0.0})

f.write(OUT)
print("IFC pilote escrito en:", OUT)
print(f"  Ø{D} L={L}  kh={KH/1e6} MN/m3  qs={QS/1e3} qb={QB/1e3} kPa  N_G={N_G/1e3} N_Q={N_Q/1e3} H_Q={H_Q/1e3} kN")
