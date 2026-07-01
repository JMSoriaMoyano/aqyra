"""
PARSER ESTRUCTURAL DE PUENTE (C1, Ola 7 / PT 7.3.1).

IFC FISICO del puente -> MODELO NEUTRO ESTRUCTURAL (clave aditiva del contrato C1;
modelo hermano del lineal/MEP). NO calcula: clasifica, extrae geometria/material/
seccion y resuelve asociaciones por proximidad.

Decision PT 7.3.1: GEOMETRIA EXTRUIDA REAL. Dimensiones y propiedades mecanicas de
seccion (A,Iy,Iz,J) del solido extruido + perfil (IfcExtrudedAreaSolid + IfcProfileDef
+ IfcStructuralProfileProperties: dominio perfil, NO Pset propietario). Los
Pset_Estructurando_* solo para lo NO geometrico (fck/fy, P0 pretensado, rigideces
suelo/apoyo, reacciones, q_adm). Reusa nucleo ifc_utils. Predim. ICCP.
"""
from __future__ import annotations
import os, sys, json, math
_here = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_here, "..", "nucleo"))
sys.path.insert(0, os.path.join(_here, "..", "lineal"))
import ifc_utils
import ifcopenshell

TOL = 1e-3

def _dir3(d, default):
    if d is None: return list(default)
    r = list(d.DirectionRatios)
    while len(r) < 3: r.append(0.0)
    return r[:3]

def _norm(v):
    n = math.sqrt(sum(c*c for c in v)) or 1.0
    return [c/n for c in v]

def _cross(a, b):
    return [a[1]*b[2]-a[2]*b[1], a[2]*b[0]-a[0]*b[2], a[0]*b[1]-a[1]*b[0]]

def _axis2_matrix(place, scale):
    if place is None: return ifc_utils.ident4()
    if place.is_a("IfcAxis2Placement2D"):
        loc = place.Location.Coordinates
        o = [loc[0]*scale, loc[1]*scale, 0.0]
        x = _dir3(place.RefDirection, (1.0,0.0,0.0)); x = _norm([x[0],x[1],0.0])
        z = [0.0,0.0,1.0]; y = _cross(z, x)
        return [[x[0],y[0],z[0],o[0]],[x[1],y[1],z[1],o[1]],[x[2],y[2],z[2],o[2]],[0,0,0,1]]
    loc = place.Location.Coordinates
    o = [loc[0]*scale, loc[1]*scale, (loc[2] if len(loc)>2 else 0.0)*scale]
    z = _norm(_dir3(getattr(place,"Axis",None),(0.0,0.0,1.0)))
    xref = _dir3(getattr(place,"RefDirection",None),(1.0,0.0,0.0))
    dotzx = sum(z[i]*xref[i] for i in range(3))
    x = _norm([xref[i]-dotzx*z[i] for i in range(3)]); y = _cross(z, x)
    return [[x[0],y[0],z[0],o[0]],[x[1],y[1],z[1],o[1]],[x[2],y[2],z[2],o[2]],[0,0,0,1]]

def _placement_matrix(obj_placement, scale):
    if obj_placement is None: return ifc_utils.ident4()
    chain = []; p = obj_placement
    while p is not None and p.is_a("IfcLocalPlacement"):
        chain.append(p.RelativePlacement); p = p.PlacementRelTo
    M = ifc_utils.ident4()
    for rel in reversed(chain):
        M = ifc_utils.matmul(M, _axis2_matrix(rel, scale))
    return M

def _extruded(element):
    rep = getattr(element, "Representation", None)
    if rep is None: return None
    for r in rep.Representations:
        for it in r.Items:
            if it.is_a("IfcExtrudedAreaSolid"): return it
            if it.is_a("IfcMappedItem"):
                for it2 in it.MappingSource.MappedRepresentation.Items:
                    if it2.is_a("IfcExtrudedAreaSolid"): return it2
    return None

def _profile_props_struct(profile, ifc):
    for pp in ifc.by_type("IfcProfileProperties"):
        if getattr(pp,"ProfileDefinition",None) is profile and pp.is_a("IfcStructuralProfileProperties"):
            d = {}
            A = getattr(pp,"CrossSectionArea",None)
            iy = getattr(pp,"MomentOfInertiaY",None); iz = getattr(pp,"MomentOfInertiaZ",None)
            jx = getattr(pp,"TorsionalConstantX",None)
            if A is not None: d["A"]=float(A)
            if iy is not None: d["Iy"]=float(iy)
            if iz is not None: d["Iz"]=float(iz)
            if jx is not None: d["J"]=float(jx)
            if "A" in d and "Iy" in d and "Iz" in d:
                d.setdefault("J", d["Iy"]+d["Iz"]); return d
    return None

def _rect_props(b, h):
    A=b*h; Iy=b*h**3/12.0; Iz=h*b**3/12.0
    a,c=max(b,h),min(b,h)
    J=a*c**3*(1.0/3.0-0.21*(c/a)*(1.0-(c**4)/(12.0*a**4)))
    return {"A":A,"Iy":Iy,"Iz":Iz,"J":J,"b":b,"h":h}

def _circle_props(r):
    A=math.pi*r**2; I=math.pi*r**4/4.0
    return {"A":A,"Iy":I,"Iz":I,"J":2*I,"D":2*r}

def _ishape_props(b, h, tw, tf):
    A=b*tf*2+(h-2*tf)*tw
    Iy=(b*h**3-(b-tw)*(h-2*tf)**3)/12.0
    Iz=(2*tf*b**3+(h-2*tf)*tw**3)/12.0
    J=(2*b*tf**3+(h-tf)*tw**3)/3.0
    return {"A":A,"Iy":Iy,"Iz":Iz,"J":J,"b":b,"h":h}

def _poly_moments(pts):
    """Polígono cerrado (lista de (x,y)) -> (A, Cx, Cy, Ix_c, Iy_c) por las
    fórmulas estándar de momentos de área; Ix_c=∫(y-Cy)^2 dA, Iy_c=∫(x-Cx)^2 dA."""
    n=len(pts)
    A2=0.0; Cx=0.0; Cy=0.0; Ix=0.0; Iy=0.0
    for i in range(n):
        x0,y0=pts[i]; x1,y1=pts[(i+1)%n]
        cr=x0*y1-x1*y0
        A2+=cr
        Cx+=(x0+x1)*cr; Cy+=(y0+y1)*cr
        Ix+=(y0*y0+y0*y1+y1*y1)*cr
        Iy+=(x0*x0+x0*x1+x1*x1)*cr
    A=A2/2.0
    if abs(A)<1e-12: return (0.0,0.0,0.0,0.0,0.0)
    Cx/=(3.0*A2); Cy/=(3.0*A2)
    Ix=Ix/12.0; Iy=Iy/12.0           # respecto a ejes globales del perfil
    A=abs(A)
    Ixc=abs(Ix)-A*Cy*Cy              # trasladar al centroide
    Iyc=abs(Iy)-A*Cx*Cx
    return (A, Cx, Cy, Ixc, Iyc)

def _poly_pts(curve, s):
    try:
        if curve.is_a("IfcPolyline"):
            P=[(p.Coordinates[0]*s, p.Coordinates[1]*s) for p in curve.Points]
        elif curve.is_a("IfcIndexedPolyCurve"):
            coo=curve.Points.CoordList
            P=[(c[0]*s, c[1]*s) for c in coo]
        else:
            return None
    except Exception:
        return None
    if len(P)>1 and P[0]==P[-1]: P=P[:-1]   # quitar cierre duplicado
    return P

def _arbitrary_props(profile, s):
    """IfcArbitraryClosedProfileDef / WithVoids -> A,Iy,Iz,J reales del polígono
    (huecos restados). Iy=fuerte (canto), Iz=débil. J aproximado: caja de pared
    delgada (Bredt) si hay huecos; si es macizo, J≈A^4/(40·Ip) (Roark). Predim."""
    outer=_poly_pts(profile.OuterCurve, s)
    if not outer: return None
    Ao,Cxo,Cyo,Ixo,Iyo=_poly_moments(outer)
    voids=[]
    if profile.is_a("IfcArbitraryProfileDefWithVoids"):
        for ic in (profile.InnerCurves or []):
            pv=_poly_pts(ic, s)
            if pv: voids.append(pv)
    A=Ao; Sx=Ao*Cyo; Sy=Ao*Cxo
    parts=[(Ao,Cxo,Cyo,Ixo,Iyo)]
    for pv in voids:
        Av,Cxv,Cyv,Ixv,Iyv=_poly_moments(pv)
        A-=Av; Sx-=Av*Cyv; Sy-=Av*Cxv
        parts.append((-Av,Cxv,Cyv,Ixv,Iyv))
    Cx=Sy/A; Cy=Sx/A
    Iy=0.0; Iz=0.0   # estructural: Iy=fuerte(∫(y-Cy)^2), Iz=débil(∫(x-Cx)^2)
    for (Ai,Cxi,Cyi,Ixci,Iyci) in parts:
        Iy+=Ixci+Ai*(Cyi-Cy)**2
        Iz+=Iyci+Ai*(Cxi-Cx)**2
    Ip=Iy+Iz
    if voids:   # caja hueca: Bredt con linea media outer/inner
        Av0,_,_,_,_=_poly_moments(voids[0])
        Am=0.5*(Ao+Av0)                      # area encerrada por la linea media (aprox)
        twall=(Ao-Av0)/_perimetro(outer) if _perimetro(outer)>0 else 0.0
        peri=_perimetro(outer)
        J=4.0*Am*Am*twall/peri if peri>0 and twall>0 else (A**4/(40.0*Ip) if Ip>0 else 0.0)
    else:
        J=A**4/(40.0*Ip) if Ip>0 else 0.0
    return {"A":A,"Iy":Iy,"Iz":Iz,"J":J,"h":_bbox_dim(outer,1),"b":_bbox_dim(outer,0)}

def _perimetro(pts):
    n=len(pts); P=0.0
    for i in range(n):
        x0,y0=pts[i]; x1,y1=pts[(i+1)%n]
        P+=math.hypot(x1-x0,y1-y0)
    return P

def _bbox_dim(pts,k):
    vals=[p[k] for p in pts]; return max(vals)-min(vals)

def _profile_dims(profile, ifc, scale):
    out={"tipo":profile.is_a()}; s=scale
    if profile.is_a("IfcRectangleProfileDef"):
        out.update(_rect_props(profile.XDim*s, profile.YDim*s))
    elif profile.is_a("IfcCircleProfileDef"):
        out.update(_circle_props(profile.Radius*s))
    elif profile.is_a("IfcIShapeProfileDef"):
        out.update(_ishape_props(profile.OverallWidth*s, profile.OverallDepth*s,
                                 profile.WebThickness*s, profile.FlangeThickness*s))
    elif profile.is_a("IfcArbitraryClosedProfileDef"):
        ap=_arbitrary_props(profile, s)
        if ap: out.update(ap)
    exact=_profile_props_struct(profile, ifc)
    if exact: out.update(exact)
    return out

def _material(element, ifc):
    mat={}; name=None
    for rel in getattr(element,"HasAssociations",[]) or []:
        if rel.is_a("IfcRelAssociatesMaterial"):
            m=rel.RelatingMaterial
            if m.is_a("IfcMaterial"): name=m.Name
            elif m.is_a("IfcMaterialLayerSetUsage"):
                try: name=m.ForLayerSet.MaterialLayers[0].Material.Name
                except Exception: pass
            elif m.is_a("IfcMaterialProfileSet"):
                try: name=m.MaterialProfiles[0].Material.Name
                except Exception: pass
    for mp in ifc.by_type("IfcMaterialProperties"):
        try:
            if mp.Material.Name!=name: continue
        except Exception: continue
        for pr in getattr(mp,"Properties",[]) or []:
            if pr.is_a("IfcPropertySingleValue") and pr.NominalValue is not None:
                mapk={"YoungModulus":"E","PoissonRatio":"nu","ShearModulus":"G",
                      "MassDensity":"rho","CompressiveStrength":"fck","YieldStress":"fy"}.get(pr.Name)
                if mapk: mat[mapk]=float(pr.NominalValue.wrappedValue)
    ps=ifc_utils.psets(element).get("Pset_Estructurando_Material",{})
    for k in ("E","nu","G","rho","fck","fy","fctm"):
        if k in ps and k not in mat: mat[k]=float(ps[k])
    if "E" in mat and "nu" in mat and "G" not in mat:
        mat["G"]=mat["E"]/(2*(1+mat["nu"]))
    mat["_nombre"]=name
    return mat

def _bar_geometry(element, ext, scale):
    Mg=_placement_matrix(element.ObjectPlacement, scale)
    Mloc=_axis2_matrix(ext.Position, scale) if ext.Position else ifc_utils.ident4()
    M=ifc_utils.matmul(Mg, Mloc)
    depth=ext.Depth*scale; d=_dir3(ext.ExtrudedDirection,(0.0,0.0,1.0))
    pi=ifc_utils.apply(M,[0.0,0.0,0.0])
    pj=ifc_utils.apply(M,[d[0]*depth,d[1]*depth,d[2]*depth])
    L=math.sqrt(sum((pj[i]-pi[i])**2 for i in range(3)))
    return {"pi":pi,"pj":pj,"L":L,"depth":depth}

def _orient(pi, pj):
    dz=abs(pj[2]-pi[2]); dxy=math.sqrt((pj[0]-pi[0])**2+(pj[1]-pi[1])**2)
    return "vertical" if dz>dxy else "horizontal"

_ROL_PSET="Pset_Estructurando_Puente"
def _rol(element, geom, ps):
    rol=(ps.get(_ROL_PSET,{}) or {}).get("Rol")
    if rol: return rol
    cls=element.is_a(); orient=geom.get("orient")
    if cls in ("IfcBeam","IfcMember"): return "viga" if orient=="horizontal" else "montante"
    if cls=="IfcColumn": return "pila_col"
    if cls=="IfcSlab": return "losa"
    if cls=="IfcWall": return "estribo_alzado"
    if cls=="IfcFooting": return "zapata"
    if cls=="IfcPile": return "pilote"
    if cls=="IfcBearing": return "aparato_apoyo"
    return cls

_CLASES=("IfcBeam","IfcMember","IfcColumn","IfcSlab","IfcWall","IfcFooting","IfcPile","IfcBearing")

def parse(ifc_path, out_path=None):
    ifc=ifcopenshell.open(ifc_path); scale=ifc_utils.length_scale(ifc)
    elementos=[]; idx=0
    for cls in _CLASES:
        try:
            _items = ifc.by_type(cls)
        except RuntimeError:
            continue  # clase no presente en el esquema (p.ej. IfcBearing en IFC4)
        for el in _items:
            ps=ifc_utils.psets(el); ext=_extruded(el)
            e={"id":"E%d"%idx,"global_id":el.GlobalId,"nombre":el.Name,
               "clase_ifc":el.is_a(),"psets":ps}
            if ext is not None:
                sec=_profile_dims(ext.SweptArea, ifc, scale)
                ov=ps.get("Pset_Estructurando_Seccion")
                if ov:  # override de constantes de seccion (dominio perfil), valida vs geom
                    sec["_A_geom"]=sec.get("A")
                    for k,v in ov.items():
                        if isinstance(v,(int,float)): sec[k]=float(v)
                e["seccion"]=sec
                geo=_bar_geometry(el, ext, scale); geo["orient"]=_orient(geo["pi"],geo["pj"])
                e["geom"]=geo
            else:
                e["geom"]={"orient":None}
            e["material"]=_material(el, ifc); e["rol"]=_rol(el, e["geom"], ps)
            elementos.append(e); idx+=1
    alineacion_ref=None
    if ifc.by_type("IfcAlignment"):
        try:
            import ifc_to_model_lineal
            ml=ifc_to_model_lineal.parse(ifc_path)
            alineacion_ref={"pk_inicio":ml.get("pk_inicio"),"pk_fin":ml.get("pk_fin"),
                            "longitud_total":ml.get("longitud_total"),
                            "planta":ml.get("alineacion",{}).get("planta")}
        except Exception as ex:
            alineacion_ref={"error":str(ex)}
    modelo={"unidades":{"longitud":"m","fuerza":"N","momento":"N*m"},
            "esquema":"estructural_puente","tipologia":_tipologia(elementos, alineacion_ref),
            "alineacion_ref":alineacion_ref,"elementos":elementos,
            "asociaciones":_asociar(elementos),"apoyos":_apoyos(elementos),
            "metricas":{"factor_escala_ifc":scale,"tol_snap_m":TOL,
                        "n_elementos":len(elementos),"esquema_ifc":ifc.schema}}
    if out_path: json.dump(modelo, open(out_path,"w"), indent=2, ensure_ascii=False)
    return modelo

def _dist(a, b): return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))

def _asociar(elementos):
    asoc=[]
    cols=[e for e in elementos if e["rol"]=="pila_col"]
    cims=[e for e in elementos if e["rol"] in ("zapata","pilote","encepado")]
    aps=[e for e in elementos if e["rol"]=="aparato_apoyo"]
    for c in cols:
        g=c.get("geom",{})
        if "pi" not in g: continue
        base=g["pi"] if g["pi"][2]<=g["pj"][2] else g["pj"]
        cab=g["pj"] if g["pi"][2]<=g["pj"][2] else g["pi"]
        for cim in cims:
            cg=cim.get("geom",{})
            ends=[cg.get("pi"),cg.get("pj")]
            if any(pt and _dist(base,pt)<0.6 for pt in ends):
                asoc.append({"a":c["id"],"b":cim["id"],"tipo":"pila-cimentacion"})
        for ap in aps:
            pt=ap.get("geom",{}).get("pi")
            if pt and _dist(cab,pt)<0.6: asoc.append({"a":c["id"],"b":ap["id"],"tipo":"pila-apoyo"})
    return asoc

def _apoyos(elementos):
    out=[]
    for e in elementos:
        if e["rol"]!="aparato_apoyo": continue
        ps=e["psets"].get("Pset_Estructurando_Apoyo",{})
        out.append({"id":e["id"],"tipo":ps.get("Tipo","elastomerico"),"a":ps.get("a"),
                    "b":ps.get("b"),"Te":ps.get("Te"),"t_capa":ps.get("t_capa"),
                    "n_capas":ps.get("n_capas"),"subtipo":ps.get("subtipo")})
    return out

def _tipologia(elementos, alin):
    roles=[e["rol"] for e in elementos]
    has=lambda r: r in roles
    if has("estribo_alzado") and (has("viga") or has("losa") or has("pila_col")): return "puente_completo"
    if has("estribo_alzado"): return "estribo"
    if has("dintel"): return "portico"
    if has("pila_col") and not (has("viga") or has("losa")): return "pila"
    if has("montante") or roles.count("viga")>6: return "celosia"
    if has("losa") and not has("viga"): return "losa_postesada"
    if has("viga") and has("pila_col"): return "portico"
    if has("viga"): return "vigas_pretensadas"
    if has("pila_col"): return "pila"
    return "desconocida"

if __name__=="__main__":
    m=parse(sys.argv[1], sys.argv[2] if len(sys.argv)>2 else None)
    print("tipologia:",m["tipologia"],"| n_elem:",m["metricas"]["n_elementos"],
          "| roles:",sorted(set(e["rol"] for e in m["elementos"])))
