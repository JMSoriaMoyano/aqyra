import ifcopenshell, ifcopenshell.guid, math
f=ifcopenshell.file(schema="IFC4"); g=ifcopenshell.guid.new
def dirn(v): return f.create_entity("IfcDirection",DirectionRatios=tuple(map(float,v)))
def pt(c): return f.create_entity("IfcCartesianPoint",Coordinates=tuple(map(float,c)))
def a2(loc,axis=None,ref=None):
    kw={"Location":pt(loc)}
    if axis: kw["Axis"]=dirn(axis)
    if ref: kw["RefDirection"]=dirn(ref)
    return f.create_entity("IfcAxis2Placement3D",**kw)
def lp(rel,a): return f.create_entity("IfcLocalPlacement",PlacementRelTo=rel,RelativePlacement=a)
ln=f.create_entity("IfcSIUnit",UnitType="LENGTHUNIT",Name="METRE")
fo=f.create_entity("IfcSIUnit",UnitType="FORCEUNIT",Name="NEWTON")
ua=f.create_entity("IfcUnitAssignment",Units=[ln,fo])
ctx=f.create_entity("IfcGeometricRepresentationContext",ContextType="Model",CoordinateSpaceDimension=3,Precision=1e-5,WorldCoordinateSystem=a2((0,0,0)))
body=f.create_entity("IfcGeometricRepresentationSubContext",ContextIdentifier="Body",ContextType="Model",ParentContext=ctx,TargetView="MODEL_VIEW")
prj=f.create_entity("IfcProject",GlobalId=g(),Name="Ttest",UnitsInContext=ua,RepresentationContexts=[ctx])
spl=lp(None,a2((0,0,0))); st=f.create_entity("IfcBuildingStorey",GlobalId=g(),Name="s",ObjectPlacement=spl,CompositionType="ELEMENT",Elevation=0.)
steel=f.create_entity("IfcMaterial",Name="S275")
def ishape(): return f.create_entity("IfcIShapeProfileDef",ProfileType="AREA",ProfileName="IPE 330",Position=f.create_entity("IfcAxis2Placement2D",Location=f.create_entity("IfcCartesianPoint",Coordinates=(0.,0.))),OverallWidth=0.16,OverallDepth=0.33,WebThickness=0.0075,FlangeThickness=0.0115,FilletRadius=0.018)
def beam(name,p0,p1,refdir):
    v=[p1[i]-p0[i] for i in range(3)]; L=math.sqrt(sum(c*c for c in v)); ax=[c/L for c in v]
    prof=ishape()
    sol=f.create_entity("IfcExtrudedAreaSolid",SweptArea=prof,Position=a2((0,0,0)),ExtrudedDirection=dirn((0,0,1)),Depth=L)
    sh=f.create_entity("IfcShapeRepresentation",ContextOfItems=body,RepresentationIdentifier="Body",RepresentationType="SweptSolid",Items=[sol])
    pds=f.create_entity("IfcProductDefinitionShape",Representations=[sh])
    el=f.create_entity("IfcBeam",GlobalId=g(),Name=name,ObjectPlacement=lp(spl,a2(p0,axis=ax,ref=refdir)),Representation=pds,PredefinedType="BEAM")
    mp=f.create_entity("IfcMaterialProfile",Name=name,Material=steel,Profile=prof)
    mps=f.create_entity("IfcMaterialProfileSet",Name="IPE 330",MaterialProfiles=[mp])
    usage=f.create_entity("IfcMaterialProfileSetUsage",ForProfileSet=mps,CardinalPoint=5)
    f.create_entity("IfcRelAssociatesMaterial",GlobalId=g(),RelatedObjects=[el],RelatingMaterial=usage)
    return el
# through-beam y=0; stub coming in at x=3 with 50 mm offset in y
through=beam("PASANTE",(0,0,3),(6,0,3),(0,1,0))
stub=beam("STUB",(3,0.05,3),(3,3,3),(1,0,0))
# snap tol Pset
ps=f.create_entity("IfcPropertySet",GlobalId=g(),Name="Pset_Estructurando_Puente",HasProperties=[f.create_entity("IfcPropertySingleValue",Name="Snap_tol_m",NominalValue=f.create_entity("IfcReal",wrappedValue=0.06))])
f.create_entity("IfcRelDefinesByProperties",GlobalId=g(),RelatedObjects=[prj],RelatingPropertyDefinition=ps)
f.create_entity("IfcRelContainedInSpatialStructure",GlobalId=g(),RelatingStructure=st,RelatedElements=[through,stub])
f.write("/tmp/ttest.ifc"); print("wrote ttest.ifc")
