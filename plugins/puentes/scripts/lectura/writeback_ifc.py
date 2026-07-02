import sys; sys.path.insert(0,"/tmp/ifclib"); sys.path.insert(0,"/tmp/pylibs")
import json, ifcopenshell
from ifcopenshell.api import run
def _route(key):
    k=key.lower()
    if any(t in k for t in ("cimentacion","zapata","pilote","encepado")): return "cim"
    return "fuste"
def aplicar(ifc_in, mapping, ifc_out):
    m=ifcopenshell.open(ifc_in)
    col=(m.by_type("IfcColumn") or m.by_type("IfcBeam") or m.by_type("IfcSlab") or [None])[0]
    foot=(m.by_type("IfcFooting") or m.by_type("IfcPile") or [None])[0]
    for key,psets in mapping.get("elementos",{}).items():
        tgt = foot if _route(key)=="cim" else col
        if tgt is None: continue
        for pname,props in psets.items():
            ps=run("pset.add_pset",m,product=tgt,name=pname)
            run("pset.edit_pset",m,pset=ps,properties={k:(float(v) if isinstance(v,bool)==False and isinstance(v,(int,float)) else v) for k,v in props.items()})
    m.write(ifc_out); print("write-back IFC:",ifc_out)
if __name__=="__main__":
    aplicar(sys.argv[1], json.load(open(sys.argv[2])), sys.argv[3])
