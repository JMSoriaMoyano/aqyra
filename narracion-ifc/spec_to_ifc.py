#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
spec_to_ifc.py  --  Generador parametrico Estructurando (Ruta 1, v0.6)

Primitivas (metros). Novedades v0.6:
  losas[].tipo:"unidireccional"  -> capa compresion + viguetas + BOVEDILLAS (IfcBuildingElementPart)
  escaleras[] con meseta + giro(0/180 en U) + zanca (zancas inclinadas laterales)
  rampas[].peldaneada:true       -> resaltos transversales sobre la superficie inclinada
Mantiene: pilares, muros(+huecos reales), losas(macizo/nervado/reticular), rampas, elementos(catalogo bsDD).
"""
import sys, json, math
import ifcopenshell, ifcopenshell.guid
from ifcopenshell.api import run


def _pt(m, c): return m.create_entity("IfcCartesianPoint", Coordinates=[float(x) for x in c])
def _dir(m, r): return m.create_entity("IfcDirection", DirectionRatios=[float(x) for x in r])
def _placement(m, o=(0.,0.,0.), z=(0.,0.,1.), x=(1.,0.,0.)):
    return m.create_entity("IfcAxis2Placement3D", Location=_pt(m,o), Axis=_dir(m,z), RefDirection=_dir(m,x))
def _lp(m, rel, o=(0.,0.,0.), z=(0.,0.,1.), x=(1.,0.,0.)):
    return m.create_entity("IfcLocalPlacement", PlacementRelTo=rel, RelativePlacement=_placement(m,o,z,x))
def _rect(m, name, sx, sy):
    return m.create_entity("IfcRectangleProfileDef", ProfileType="AREA", ProfileName=name,
        Position=m.create_entity("IfcAxis2Placement2D", Location=_pt(m,(0.,0.))), XDim=float(sx), YDim=float(sy))
def _poly(m, name, cont):
    pts=[_pt(m,(p[0],p[1])) for p in cont]; pts.append(pts[0])
    return m.create_entity("IfcArbitraryClosedProfileDef", ProfileType="AREA", ProfileName=name,
        OuterCurve=m.create_entity("IfcPolyline", Points=pts))
def _ext(m, profile, depth, o=(0.,0.,0.), z=(0.,0.,1.), x=(1.,0.,0.)):
    return m.create_entity("IfcExtrudedAreaSolid", SweptArea=profile, Position=_placement(m,o,z,x),
        ExtrudedDirection=_dir(m,(0.,0.,1.)), Depth=float(depth))
def _box(m, name, sx, sy, sz, c=(0.,0.,0.)):
    return _ext(m, _rect(m,name,sx,sy), sz, o=c)
def _shape(m, ctx, items):
    if not isinstance(items, list): items=[items]
    rep=m.create_entity("IfcShapeRepresentation", ContextOfItems=ctx, RepresentationIdentifier="Body",
        RepresentationType="SweptSolid", Items=items)
    return m.create_entity("IfcProductDefinitionShape", Representations=[rep])
def _cross(a,b): return (a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0])
def _voids(m,w,o): return m.create_entity("IfcRelVoidsElement", GlobalId=ifcopenshell.guid.new(),
        RelatingBuildingElement=w, RelatedOpeningElement=o)
def _fills(m,o,f): return m.create_entity("IfcRelFillsElement", GlobalId=ifcopenshell.guid.new(),
        RelatingOpeningElement=o, RelatedBuildingElement=f)

def _beam_between(m, name, p0, p1, w, h):
    """Prisma rect (w x h) que corre del punto p0 a p1 (eje del prisma = recta p0p1)."""
    d=(p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]); L=math.sqrt(sum(v*v for v in d)) or 1.0
    S=(d[0]/L,d[1]/L,d[2]/L); wn=math.hypot(-S[1],S[0]) or 1.0; Wd=(-S[1]/wn,S[0]/wn,0.0)
    return _ext(m, _rect(m,name,w,h), L, o=p0, z=S, x=Wd)


def generar(spec, out):
    m = ifcopenshell.file(schema=spec.get("esquema","IFC4"))
    project=run("root.create_entity",m,ifc_class="IfcProject",name=spec.get("proyecto","Proyecto"))
    run("unit.assign_unit",m,length={"is_metric":True,"raw":"METERS"})
    mctx=run("context.add_context",m,context_type="Model")
    bctx=run("context.add_context",m,context_type="Model",context_identifier="Body",target_view="MODEL_VIEW",parent=mctx)
    site=run("root.create_entity",m,ifc_class="IfcSite",name="Emplazamiento")
    building=run("root.create_entity",m,ifc_class="IfcBuilding",name="Edificio")
    run("aggregate.assign_object",m,relating_object=project,products=[site])
    run("aggregate.assign_object",m,relating_object=site,products=[building])
    storeys={}
    for niv in spec.get("niveles",[]):
        st=run("root.create_entity",m,ifc_class="IfcBuildingStorey",name=niv["nombre"]); st.Elevation=float(niv.get("cota",0.0))
        run("aggregate.assign_object",m,relating_object=building,products=[st]); storeys[niv["nombre"]]=st
    if not storeys:
        st=run("root.create_entity",m,ifc_class="IfcBuildingStorey",name="Planta 00"); st.Elevation=0.0
        run("aggregate.assign_object",m,relating_object=building,products=[st]); storeys["Planta 00"]=st
    def cota(n): return float(storeys[n].Elevation or 0.0)
    def nivel_cota(z): return min(storeys.values(), key=lambda s: abs(float(s.Elevation or 0.0)-z))
    def mat(p,material):
        if material:
            ps=run("pset.add_pset",m,product=p,name="Pset_Estructurando_Spec"); run("pset.edit_pset",m,pset=ps,properties={"Material":material})
    c={"pilares":0,"muros":0,"losas":0,"rampas":0,"escaleras":0,"huecos":0,"bovedillas":0,"elementos":0}
    import catalogo_ifc as C; ecache={}

    for p in spec.get("pilares",[]):
        bx,by=p["seccion"]; x,y=p["pos"]; z=cota(p["nivel"])
        col=run("root.create_entity",m,ifc_class="IfcColumn",name=p["nombre"])
        col.ObjectPlacement=_lp(m,None,(x,y,z)); col.Representation=_shape(m,bctx,_ext(m,_rect(m,p["nombre"],bx,by),p["altura"]))
        run("spatial.assign_container",m,relating_structure=storeys[p["nivel"]],products=[col])
        _pc=run("pset.add_pset",m,product=col,name="Pset_ColumnCommon"); run("pset.edit_pset",m,pset=_pc,properties={"LoadBearing":True,"IsExternal":bool(p.get("exterior",False))})
        mat(col,p.get("material")); c["pilares"]+=1

    for w in spec.get("muros",[]):
        (x0,y0),(x1,y1)=w["inicio"],w["fin"]; e=w["espesor"]; H=w["altura"]
        L=math.hypot(x1-x0,y1-y0); ang=math.atan2(y1-y0,x1-x0); z=cota(w["nivel"])
        wall=run("root.create_entity",m,ifc_class="IfcWall",name=w["nombre"])
        wall.ObjectPlacement=_lp(m,None,((x0+x1)/2,(y0+y1)/2,z),x=(math.cos(ang),math.sin(ang),0.))
        wall.Representation=_shape(m,bctx,_ext(m,_rect(m,w["nombre"],L,e),H))
        run("spatial.assign_container",m,relating_structure=storeys[w["nivel"]],products=[wall])
        ps=run("pset.add_pset",m,product=wall,name="Pset_WallCommon")
        run("pset.edit_pset",m,pset=ps,properties={"IsExternal":bool(w.get("exterior",False)),"LoadBearing":True})
        mat(wall,w.get("material")); c["muros"]+=1
        for h in w.get("huecos",[]):
            ancho=float(h["ancho"]); alto=float(h["alto"]); alf=float(h.get("alfeizar",0.0)); xc=float(h["pos"])-L/2.0
            op=run("root.create_entity",m,ifc_class="IfcOpeningElement",name=f"{w['nombre']}_Hueco")
            try: op.PredefinedType="OPENING"
            except Exception: pass
            op.ObjectPlacement=_lp(m,wall.ObjectPlacement,(xc,0.,alf)); op.Representation=_shape(m,bctx,_box(m,"hueco",ancho,e+0.10,alto))
            _voids(m,wall,op); c["huecos"]+=1
            tipo=h.get("tipo")
            if tipo in ("puerta","ventana"):
                clase="IfcDoor" if tipo=="puerta" else "IfcWindow"
                fill,_=C.crear_elemento(m,bctx,storeys[w["nivel"]],clase,f"{w['nombre']}_{tipo}",origin=(0.,0.,0.),
                                        classif_cache=ecache,params={"ancho":ancho,"alto":alto,"espesor_muro":e})
                fill.ObjectPlacement=_lp(m,wall.ObjectPlacement,(xc,0.,alf)); _fills(m,op,fill)

    for s in spec.get("losas",[]):
        z=cota(s["nivel"]); tipo=s.get("tipo","macizo")
        xs=[p[0] for p in s["contorno"]]; ys=[p[1] for p in s["contorno"]]
        xmin,xmax,ymin,ymax=min(xs),max(xs),min(ys),max(ys)
        if tipo in ("nervado","reticular"):
            capa=float(s.get("capa",0.05)); canto=float(s.get("canto",0.30)); sep=float(s.get("sep",0.80)); bn=float(s.get("b_nervio",0.10)); rib=canto-capa
            items=[_ext(m,_poly(m,s["nombre"],s["contorno"]),capa,o=(0.,0.,-capa))]
            dirn=s.get("direccion","x" if tipo=="nervado" else "ambas")
            if dirn in ("x","ambas"):
                y=ymin+sep/2.0
                while y<ymax: items.append(_box(m,"nervio",xmax-xmin,bn,rib,c=((xmin+xmax)/2.,y,-canto))); y+=sep
            if dirn in ("y","ambas"):
                x=xmin+sep/2.0
                while x<xmax: items.append(_box(m,"nervio",bn,ymax-ymin,rib,c=(x,(ymin+ymax)/2.,-canto))); x+=sep
            sh=_shape(m,bctx,items)
        elif tipo=="unidireccional":
            capa=float(s.get("capa",0.05)); canto=float(s.get("canto",0.30)); inter=float(s.get("intereje",s.get("sep",0.72)))
            bn=float(s.get("b_nervio",0.12)); recess=float(s.get("recess",0.04)); rib=canto-capa
            dirn=s.get("direccion","x")  # las viguetas corren en esta direccion
            items=[_ext(m,_poly(m,s["nombre"],s["contorno"]),capa,o=(0.,0.,-capa))]
            bov=[]  # (sx,sy,depth,cx,cy)
            if dirn=="x":
                ejes=[]; y=ymin+bn/2.0
                while y<=ymax-bn/2.0+1e-9: ejes.append(y); y+=inter
                for ye in ejes: items.append(_box(m,"vigueta",xmax-xmin,bn,rib,c=((xmin+xmax)/2.,ye,-canto)))
                for a,b in zip(ejes,ejes[1:]):
                    bov.append((xmax-xmin, (b-a)-bn, rib-recess, (xmin+xmax)/2., (a+b)/2.))
            else:
                ejes=[]; x=xmin+bn/2.0
                while x<=xmax-bn/2.0+1e-9: ejes.append(x); x+=inter
                for xe in ejes: items.append(_box(m,"vigueta",bn,ymax-ymin,rib,c=(xe,(ymin+ymax)/2.,-canto)))
                for a,b in zip(ejes,ejes[1:]):
                    bov.append(((b-a)-bn, ymax-ymin, rib-recess, (a+b)/2., (ymin+ymax)/2.))
            sh=_shape(m,bctx,items)
        else:
            sh=_shape(m,bctx,_ext(m,_poly(m,s["nombre"],s["contorno"]),s["espesor"],o=(0.,0.,-float(s["espesor"]))))
            bov=[]
        slab=run("root.create_entity",m,ifc_class="IfcSlab",name=s["nombre"]); slab.PredefinedType="FLOOR"
        slab.ObjectPlacement=_lp(m,None,(0.,0.,z)); slab.Representation=sh
        run("spatial.assign_container",m,relating_structure=storeys[s["nivel"]],products=[slab])
        _ps=run("pset.add_pset",m,product=slab,name="Pset_SlabCommon"); run("pset.edit_pset",m,pset=_ps,properties={"LoadBearing":True,"IsExternal":bool(s.get("exterior",False))})
        mat(slab,s.get("material")); c["losas"]+=1
        for i,(sx,sy,dp,cx,cy) in enumerate(locals().get("bov",[]) or [],1):
            if sx<=0 or sy<=0 or dp<=0: continue
            part=run("root.create_entity",m,ifc_class="IfcBuildingElementPart",name=f"{s['nombre']}_Bovedilla_{i}")
            try: part.PredefinedType="INSULATION" if False else None
            except Exception: pass
            part.ObjectPlacement=_lp(m,None,(0.,0.,z)); part.Representation=_shape(m,bctx,_box(m,"bovedilla",sx,sy,dp,c=(cx,cy,-(float(s.get('canto',0.30))-float(s.get('recess',0.04))))))
            run("spatial.assign_container",m,relating_structure=storeys[s["nivel"]],products=[part]); mat(part,"Bovedilla"); c["bovedillas"]+=1

    for r in spec.get("rampas",[]):
        p0,p1=r["inicio"],r["fin"]; d=(p1[0]-p0[0],p1[1]-p0[1],p1[2]-p0[2]); Lr=math.sqrt(sum(v*v for v in d)) or 1.0
        X=(d[0]/Lr,d[1]/Lr,d[2]/Lr); wn=math.hypot(-X[1],X[0]) or 1.0; Y=(-X[1]/wn,X[0]/wn,0.0); Z=_cross(X,Y); esp=float(r["espesor"])
        items=[_ext(m,_rect(m,r["nombre"],Lr,r["ancho"]),esp)]
        if r.get("peldaneada"):
            paso=float(r.get("paso_peldano",0.35)); hp=float(r.get("alto_peldano",0.05)); ancho=float(r["ancho"])
            t=-Lr/2.0+paso
            while t<Lr/2.0:
                items.append(_ext(m,_rect(m,"resalto",paso*0.5,ancho),hp,o=(t,0.,esp))); t+=paso
        sh=_shape(m,bctx,items)
        mid=((p0[0]+p1[0])/2,(p0[1]+p1[1])/2,(p0[2]+p1[2])/2); origin=(mid[0]-Z[0]*esp,mid[1]-Z[1]*esp,mid[2]-Z[2]*esp)
        fl=run("root.create_entity",m,ifc_class="IfcRampFlight",name=r["nombre"])
        fl.ObjectPlacement=_lp(m,None,origin,z=Z,x=X); fl.Representation=sh
        st=storeys[r["nivel"]] if r.get("nivel") in storeys else nivel_cota(min(p0[2],p1[2]))
        run("spatial.assign_container",m,relating_structure=st,products=[fl]); mat(fl,r.get("material")); c["rampas"]+=1

    for e_ in spec.get("escaleras",[]):
        x,y=e_.get("pos",[0.,0.]); z=cota(e_["nivel"]); a=float(e_.get("ancho",1.20))
        hue=float(e_.get("huella",0.28)); ch=float(e_.get("contrahuella",0.18)); n=int(e_.get("n_escalones",1))
        ang=math.radians(float(e_.get("direccion",0.0)))
        meseta=bool(e_.get("meseta",False)); giro=float(e_.get("giro",0.0)); zanca=bool(e_.get("zanca",False))
        items=[]
        if not meseta:
            for i in range(n): items.append(_box(m,"peldano",hue,a,(i+1)*ch,c=((i+0.5)*hue,0.,0.)))
            if zanca:
                x_top=n*hue; z_top=n*ch
                items.append(_beam_between(m,"zanca",(0.,a/2.,0.),(x_top,a/2.,z_top),0.08,0.30))
                items.append(_beam_between(m,"zanca",(0.,-a/2.,0.),(x_top,-a/2.,z_top),0.08,0.30))
        else:
            n1=(n+1)//2; n2=n-n1; x1=n1*hue; z1=n1*ch; ml=float(e_.get("meseta_largo",a))
            for i in range(n1): items.append(_box(m,"peldano",hue,a,(i+1)*ch,c=((i+0.5)*hue,0.,0.)))
            if zanca:
                items.append(_beam_between(m,"zanca",(0.,a/2.,0.),(x1,a/2.,z1),0.08,0.30))
                items.append(_beam_between(m,"zanca",(0.,-a/2.,0.),(x1,-a/2.,z1),0.08,0.30))
            if abs(giro-180.0)<1.0:   # U: meseta cubre dos bandas, 2º tramo paralelo en -X, banda Y=+a
                items.append(_box(m,"meseta",a,2*a,0.20,c=(x1+a/2.,a/2.,z1-0.20)))
                for j in range(n2): items.append(_box(m,"peldano",hue,a,(j+1)*ch,c=(x1+a-(j+0.5)*hue,a,z1)))
                if zanca:
                    items.append(_beam_between(m,"zanca",(x1+a,a/2.,z1),(x1+a-n2*hue,a/2.,z1+n2*ch),0.08,0.30))
                    items.append(_beam_between(m,"zanca",(x1+a,3*a/2.,z1),(x1+a-n2*hue,3*a/2.,z1+n2*ch),0.08,0.30))
            else:                      # recta: meseta + 2º tramo continua en +X
                items.append(_box(m,"meseta",ml,a,0.20,c=(x1+ml/2.,0.,z1-0.20)))
                for j in range(n2): items.append(_box(m,"peldano",hue,a,(j+1)*ch,c=(x1+ml+(j+0.5)*hue,0.,z1)))
                if zanca:
                    items.append(_beam_between(m,"zanca",(x1+ml,a/2.,z1),(x1+ml+n2*hue,a/2.,z1+n2*ch),0.08,0.30))
                    items.append(_beam_between(m,"zanca",(x1+ml,-a/2.,z1),(x1+ml+n2*hue,-a/2.,z1+n2*ch),0.08,0.30))
        stair=run("root.create_entity",m,ifc_class="IfcStair",name=e_["nombre"])
        stair.ObjectPlacement=_lp(m,None,(x,y,z),x=(math.cos(ang),math.sin(ang),0.))
        run("spatial.assign_container",m,relating_structure=storeys[e_["nivel"]],products=[stair])
        flight=run("root.create_entity",m,ifc_class="IfcStairFlight",name=f"{e_['nombre']}_tramo")
        try: flight.NumberOfRisers=n
        except Exception: pass
        flight.ObjectPlacement=_lp(m,stair.ObjectPlacement,(0.,0.,0.)); flight.Representation=_shape(m,bctx,items)
        m.create_entity("IfcRelAggregates",GlobalId=ifcopenshell.guid.new(),RelatingObject=stair,RelatedObjects=[flight])
        mat(stair,e_.get("material")); c["escaleras"]+=1

    for el in spec.get("elementos",[]):
        clase=el["clase"]; name=el.get("nombre",clase); x,y=el.get("pos",[0.,0.]); st=storeys.get(el.get("nivel"))
        z=cota(el["nivel"]) if el.get("nivel") in storeys else float(el.get("cota",0.0))
        C.crear_elemento(m,bctx,st,clase,name,origin=(x,y,z),predefined=el.get("predefined"),material=el.get("material"),classif_cache=ecache,params=el); c["elementos"]+=1

    m.write(out); return m,c


def main():
    args=[a for a in sys.argv[1:] if not a.startswith("--")]
    flags=[a for a in sys.argv[1:] if a.startswith("--")]
    if len(args)<2:
        print("Uso: python3 spec_to_ifc.py entrada.spec.json salida.ifc [--estricto] [--no-validar]"); sys.exit(1)
    spec=json.load(open(args[0],encoding="utf-8")); m,c=generar(spec,args[1])
    print(f"OK  esquema={m.schema}  ->  {args[1]}")
    print(f"    pilares={c['pilares']} muros={c['muros']}(huecos={c['huecos']}) losas={c['losas']}(bovedillas={c['bovedillas']}) rampas={c['rampas']} escaleras={c['escaleras']} elementos={c['elementos']}")
    print(f"    productos con geometria={len([p for p in m.by_type('IfcProduct') if p.Representation])}")
    if "--no-validar" not in flags:
        try:
            import validar
            print()
            _, I = validar.validar(args[1], esquema_esperado=spec.get("esquema"))
            n = validar.informe(_, I)
            if "--estricto" in flags and n["ERROR"] > 0:
                print(f"\n>>> NO APTO (estricto): {n['ERROR']} ERROR <<<"); sys.exit(1)
        except ImportError:
            print("[aviso] validar.py no disponible; se omite la validacion")

if __name__=="__main__": main()
