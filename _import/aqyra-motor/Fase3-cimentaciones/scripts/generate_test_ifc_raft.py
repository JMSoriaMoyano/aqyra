"""
Genera un IFC4 de una LOSA DE CIMENTACION (raft) de hormigon sobre lecho elastico
(Winkler), bajo una reticula de pilares. Extension directa de la zapata: placa grande
(IfcStructuralSurfaceMember) + muelles verticales + varias cargas de pilar.

  - Losa C30/37 de 12 x 9 m, canto 0.70 m
  - Reticula de 3 x 3 pilares (esquina / borde / interior con cargas crecientes)
  - Terreno: modulo de balasto vertical ks y resistencia de calculo Rd
  - Cargas por pilar: N permanente (G) y variable (Q)

Unidades SI (m, N, Pa).
"""
import os
import ifcopenshell
import ifcopenshell.guid

BX = 12.0          # dimension en X (m)
LY = 9.0           # dimension en Y (m)
T = 0.70           # canto de la losa (m)
MESH = 0.50        # tamano de malla (m)
C_PILAR = 0.45     # lado de pilar (m)

CONCRETE = dict(name="C30/37", E=32.84e9, nu=0.2, rho=2500.0, fck=30e6, G=13.68e9, fctm=2.9e6)
KS = 40e6          # modulo de balasto vertical (N/m3) ~ 40 MN/m3
RD_SUELO = 300e3   # resistencia del terreno de calculo (Pa) = 300 kPa

# Retícula de pilares: posiciones (x,y) y cargas (G,Q) en N. Lado de pilar comun.
XS = [2.0, 6.0, 10.0]
YS = [1.5, 4.5, 7.5]


def carga_pilar(ix, iy):
    """Asigna cargas segun posicion: esquina < borde < interior."""
    borde_x = ix in (0, len(XS) - 1)
    borde_y = iy in (0, len(YS) - 1)
    if borde_x and borde_y:
        return 450e3, 150e3      # esquina
    if borde_x or borde_y:
        return 750e3, 250e3      # borde
    return 1300e3, 450e3         # interior


HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "proyecto-losa-cimentacion", "raft.ifc"))

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new
length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
force = f.create_entity("IfcSIUnit", UnitType="FORCEUNIT", Name="NEWTON")
ua = f.create_entity("IfcUnitAssignment", Units=[length, force])
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5,
                      WorldCoordinateSystem=f.create_entity("IfcAxis2Placement3D",
                          Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0., 0.))))
f.create_entity("IfcProject", GlobalId=guid(), Name="Losa de cimentacion demo",
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
                           Name="Losa de cimentacion", PredefinedType="NOTDEFINED")

losa = f.create_entity("IfcStructuralSurfaceMember", GlobalId=guid(), Name="LOSA_CIMENTACION",
                       PredefinedType="SHELL", Thickness=T)
f.create_entity("IfcRelAssociatesMaterial", GlobalId=guid(), RelatedObjects=[losa], RelatingMaterial=mat)
f.create_entity("IfcRelAssignsToGroup", GlobalId=guid(), RelatedObjects=[losa], RelatingGroup=analysis)

pset_for(losa, "Pset_Estructurando_Losa",
         {"BX": BX, "LY": LY, "Espesor": T, "TamanoMalla": MESH, "Material": CONCRETE["name"],
          "LadoPilar": C_PILAR, "ModuloBalasto_N_m3": KS, "Rd_suelo_Pa": RD_SUELO})

npil = 0
for ix, x in enumerate(XS):
    for iy, y in enumerate(YS):
        Ng, Nq = carga_pilar(ix, iy)
        npil += 1
        pset_for(losa, "Pset_Estructurando_Pilar_%d" % npil,
                 {"x": x, "y": y, "Lado": C_PILAR, "N_G_N": -Ng, "N_Q_N": -Nq})

os.makedirs(os.path.dirname(OUT), exist_ok=True)
f.write(OUT)
print("IFC losa de cimentacion escrito en:", OUT)
print("  Losa %.0f x %.0f m  canto=%.2f m  malla=%.2f m  %d pilares (%.2f m)"
      % (BX, LY, T, MESH, npil, C_PILAR))
print("  ks=%.0f MN/m3  Rd=%.0f kPa  hormigon %s" % (KS / 1e6, RD_SUELO / 1e3, CONCRETE["name"]))
