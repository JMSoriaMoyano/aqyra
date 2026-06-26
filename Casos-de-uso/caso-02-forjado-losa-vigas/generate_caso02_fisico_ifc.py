"""
CASO 2 - version FISICA (geometria solida) para VISOR IFC.

El modelo de calculo (caso-02.ifc) es un IFC del dominio de ANALISIS estructural:
sus elementos son analiticos (IfcVertexPoint/IfcEdge/IfcFaceSurface) y NO tienen
geometria solida, por lo que un visor web-ifc no muestra nada. Este generador crea
el GEMELO FISICO con solidos extruidos para poder visualizarlo:

  - 2 vigas IPE 400 -> IfcBeam con IfcExtrudedAreaSolid de IfcIShapeProfileDef.
  - Losa 6x4x0,12 m -> IfcSlab con IfcExtrudedAreaSolid de IfcRectangleProfileDef.
  - Estructura espacial minima: Project -> Site -> Building -> Storey.

Mismas dimensiones y materiales que el modelo analitico. Unidades SI (m).
"""
import os
import ifcopenshell
import ifcopenshell.guid

LX, LY, T = 6.0, 4.0, 0.12
IPE400 = dict(name="IPE 400", b=0.180, h=0.400, tw=0.0086, tf=0.0135, r=0.021)

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "caso-02-fisico.ifc")

f = ifcopenshell.file(schema="IFC4")
guid = ifcopenshell.guid.new

def pt(x, y, z): return f.create_entity("IfcCartesianPoint", Coordinates=(float(x), float(y), float(z)))
def d3(x, y, z): return f.create_entity("IfcDirection", DirectionRatios=(float(x), float(y), float(z)))
def axis(loc, ax=None, ref=None):
    return f.create_entity("IfcAxis2Placement3D", Location=loc,
                           Axis=ax, RefDirection=ref)
def placement(rel, a): return f.create_entity("IfcLocalPlacement", PlacementRelTo=rel, RelativePlacement=a)

length = f.create_entity("IfcSIUnit", UnitType="LENGTHUNIT", Name="METRE")
area = f.create_entity("IfcSIUnit", UnitType="AREAUNIT", Name="SQUARE_METRE")
vol = f.create_entity("IfcSIUnit", UnitType="VOLUMEUNIT", Name="CUBIC_METRE")
ua = f.create_entity("IfcUnitAssignment", Units=[length, area, vol])

origin = axis(pt(0, 0, 0))
ctx = f.create_entity("IfcGeometricRepresentationContext", ContextType="Model",
                      CoordinateSpaceDimension=3, Precision=1e-5, WorldCoordinateSystem=origin)
body = f.create_entity("IfcGeometricRepresentationSubContext", ContextIdentifier="Body",
                       ContextType="Model", ParentContext=ctx, TargetView="MODEL_VIEW")

proj = f.create_entity("IfcProject", GlobalId=guid(), Name="Caso 2 - Forjado (fisico)",
                       UnitsInContext=ua, RepresentationContexts=[ctx])

site = f.create_entity("IfcSite", GlobalId=guid(), Name="Parcela",
                       ObjectPlacement=placement(None, axis(pt(0, 0, 0))), CompositionType="ELEMENT")
bld = f.create_entity("IfcBuilding", GlobalId=guid(), Name="Edificio",
                      ObjectPlacement=placement(site.ObjectPlacement, axis(pt(0, 0, 0))),
                      CompositionType="ELEMENT")
storey = f.create_entity("IfcBuildingStorey", GlobalId=guid(), Name="Forjado",
                         ObjectPlacement=placement(bld.ObjectPlacement, axis(pt(0, 0, 0))),
                         CompositionType="ELEMENT", Elevation=0.0)
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=proj, RelatedObjects=[site])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=site, RelatedObjects=[bld])
f.create_entity("IfcRelAggregates", GlobalId=guid(), RelatingObject=bld, RelatedObjects=[storey])

def shape(solid):
    return f.create_entity("IfcProductDefinitionShape", Representations=[
        f.create_entity("IfcShapeRepresentation", ContextOfItems=body,
                        RepresentationIdentifier="Body", RepresentationType="SweptSolid",
                        Items=[solid])])

# --- Vigas IPE 400: perfil en plano XY local, extrusion en Z local = global X ---
iprof = f.create_entity("IfcIShapeProfileDef", ProfileType="AREA", ProfileName=IPE400["name"],
                        Position=f.create_entity("IfcAxis2Placement2D",
                            Location=f.create_entity("IfcCartesianPoint", Coordinates=(0., 0.))),
                        OverallWidth=IPE400["b"], OverallDepth=IPE400["h"],
                        WebThickness=IPE400["tw"], FlangeThickness=IPE400["tf"], FilletRadius=IPE400["r"])

def viga(name, y0):
    solid = f.create_entity("IfcExtrudedAreaSolid", SweptArea=iprof,
                            Position=axis(pt(0, 0, 0)), ExtrudedDirection=d3(0, 0, 1), Depth=LX)
    # local Z -> global X (eje viga); local X -> global Y (ancho ala) ; local Y -> global Z (canto)
    plc = placement(storey.ObjectPlacement, axis(pt(0, y0, -IPE400["h"] / 2), d3(1, 0, 0), d3(0, 1, 0)))
    return f.create_entity("IfcBeam", GlobalId=guid(), Name=name, ObjectPlacement=plc,
                           Representation=shape(solid), PredefinedType="BEAM")

V1 = viga("V1", 0.0)
V2 = viga("V2", LY)

# --- Losa: rectangulo 6x4 extruido 0,12 m, apoyada sobre las vigas ---
rect = f.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName="Losa",
                       Position=f.create_entity("IfcAxis2Placement2D",
                           Location=f.create_entity("IfcCartesianPoint", Coordinates=(LX / 2, LY / 2))),
                       XDim=LX, YDim=LY)
solid_losa = f.create_entity("IfcExtrudedAreaSolid", SweptArea=rect,
                             Position=axis(pt(0, 0, 0)), ExtrudedDirection=d3(0, 0, 1), Depth=T)
plc_losa = placement(storey.ObjectPlacement, axis(pt(0, 0, IPE400["h"] / 2)))
LOSA = f.create_entity("IfcSlab", GlobalId=guid(), Name="Losa C30/37", ObjectPlacement=plc_losa,
                       Representation=shape(solid_losa), PredefinedType="FLOOR")

f.create_entity("IfcRelContainedInSpatialStructure", GlobalId=guid(),
                RelatingStructure=storey, RelatedElements=[V1, V2, LOSA])

f.write(OUT)
print("IFC fisico caso 2 escrito en:", OUT)
