"""
Generador IFC4X3 de puentes para los casos PUE (geometria extruida REAL + Psets solo
para datos NO geometricos). Reusable por tipologia. Predim. ICCP.
"""
import sys; sys.path.insert(0,"/tmp/ifclib"); sys.path.insert(0,"/tmp/pylibs")
import math, ifcopenshell
from ifcopenshell.api import run

def nuevo(nombre="PUENTE"):
    m=ifcopenshell.file(schema="IFC4X3")
    run("root.create_entity",m,ifc_class="IfcProject",name=nombre)
    u=run("unit.add_si_unit",m,unit_type="LENGTHUNIT"); run("unit.assign_unit",m,units=[u])
    ctx=run("context.add_context",m,context_type="Model")
    body=run("context.add_context",m,context_type="Model",context_identifier="Body",
             target_view="MODEL_VIEW",parent=ctx)
    site=run("root.create_entity",m,ifc_class="IfcSite",name="Emplazamiento")
    run("aggregate.assign_object",m,relating_object=m.by_type("IfcProject")[0],products=[site])
    return m, body, site

def _pt(m,c): return m.create_entity("IfcCartesianPoint",Coordinates=[float(x) for x in c])
def _dir(m,c): return m.create_entity("IfcDirection",DirectionRatios=[float(x) for x in c])
def _axis(m,o=(0,0,0),z=(0,0,1),x=(1,0,0)):
    return m.create_entity("IfcAxis2Placement3D",Location=_pt(m,o),Axis=_dir(m,z),RefDirection=_dir(m,x))
def _lp(m,o=(0,0,0),z=(0,0,1),x=(1,0,0)):
    return m.create_entity("IfcLocalPlacement",RelativePlacement=_axis(m,o,z,x))
def _shape(m,body,solid):
    shp=m.create_entity("IfcShapeRepresentation",ContextOfItems=body,
        RepresentationIdentifier="Body",RepresentationType="SweptSolid",Items=[solid])
    return m.create_entity("IfcProductDefinitionShape",Representations=[shp])
def _rect(m,b,h): return m.create_entity("IfcRectangleProfileDef",ProfileType="AREA",
    Position=m.create_entity("IfcAxis2Placement2D",Location=_pt2(m,(0,0))),XDim=float(b),YDim=float(h))
def _pt2(m,c): return m.create_entity("IfcCartesianPoint",Coordinates=[float(c[0]),float(c[1])])
def _circ(m,r): return m.create_entity("IfcCircleProfileDef",ProfileType="AREA",
    Position=m.create_entity("IfcAxis2Placement2D",Location=_pt2(m,(0,0))),Radius=float(r))
def _poly(m,pts):
    cps=[_pt2(m,p) for p in pts]+[_pt2(m,pts[0])]
    return m.create_entity("IfcPolyline",Points=cps)
def _profile_box(m,outer,inner=None):
    oc=_poly(m,outer)
    if inner:
        return m.create_entity("IfcArbitraryProfileDefWithVoids",ProfileType="AREA",
            OuterCurve=oc,InnerCurves=[_poly(m,inner)])
    return m.create_entity("IfcArbitraryClosedProfileDef",ProfileType="AREA",OuterCurve=oc)
def _ext(m,profile,depth,dirv=(0,0,1)):
    return m.create_entity("IfcExtrudedAreaSolid",SweptArea=profile,Position=_axis(m),
        ExtrudedDirection=_dir(m,dirv),Depth=float(depth))
def elem(m,body,site,cls,name,profile,depth,base=(0,0,0),dirv=(0,0,1),predef=None):
    e=run("root.create_entity",m,ifc_class=cls,name=name)
    if predef is not None:
        try: e.PredefinedType=predef
        except Exception: pass
    e.ObjectPlacement=_lp(m,base); e.Representation=_shape(m,body,_ext(m,profile,depth,dirv))
    run("spatial.assign_container",m,products=[e],relating_structure=site)
    return e
def pset(m,el,name,props):
    ps=run("pset.add_pset",m,product=el,name=name)
    run("pset.edit_pset",m,pset=ps,properties={k:(float(v) if isinstance(v,(int,float)) else v)
                                               for k,v in props.items() if v is not None})
def material(m,el,mat):
    nm=mat.get("_nombre","HA")
    mt=None
    for x in m.by_type("IfcMaterial"):
        if x.Name==nm: mt=x;break
    if mt is None: mt=m.create_entity("IfcMaterial",Name=nm)
    m.create_entity("IfcRelAssociatesMaterial",GlobalId=ifcopenshell.guid.new(),
        RelatedObjects=[el],RelatingMaterial=mt)
    props=[]
    for k_ifc,k in (("YoungModulus","E"),("PoissonRatio","nu"),("ShearModulus","G"),
                    ("MassDensity","rho"),("CompressiveStrength","fck"),("YieldStress","fy")):
        if k in mat:
            props.append(m.create_entity("IfcPropertySingleValue",Name=k_ifc,
                NominalValue=m.create_entity("IfcReal",wrappedValue=float(mat[k]))))
    if props:
        m.create_entity("IfcMaterialProperties",Name="Mecanicas",Material=mt,Properties=props)
    # respaldo no geometrico de resistencias:
    pset(m,el,"Pset_Estructurando_Material",{k:mat[k] for k in ("E","nu","G","rho","fck","fy","fctm") if k in mat})

if __name__=="__main__":
    print("gen_ifc helpers OK")
