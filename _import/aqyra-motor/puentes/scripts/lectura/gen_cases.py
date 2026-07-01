"""Builders IFC4X3 por tipologia (entrada_caso -> IFC). Geometria extruida real;
Pset solo para datos no geometricos (y Pset_Estructurando_Seccion para constantes de
seccion no reducibles a forma simple: artesa). Predim. ICCP."""
import sys; sys.path.insert(0,"/tmp/work_pt731"); sys.path.insert(0,"/tmp/ifclib"); sys.path.insert(0,"/tmp/pylibs")
import json, gen_ifc as G

def _box_para(A,Iy,Iz,h):
    """Polígono de cajón simétrico (ancho bo, alto h, pared t) que reproduce A e Iy.
    Resuelve bo de Iz si es posible; si no, ancho razonable. Devuelve (outer,inner) o None."""
    # cajón rectangular hueco: outer bo x h, inner (bo-2t) x (h-2t)
    # A = bo*h-(bo-2t)(h-2t); Iy=(bo*h^3-(bo-2t)(h-2t)^3)/12
    # estrategia: fija bo de Iz aprox; busca t por biseccion para casar A.
    import math
    bo=max(0.3, (12*Iz/h)**(1/3.0) if Iz>0 else h)   # ancho de un macizo equiv en Iz
    bo=min(bo, 3.0)
    lo,hi=0.02,min(bo,h)/2.0-1e-3
    for _ in range(60):
        t=(lo+hi)/2.0
        a=bo*h-(bo-2*t)*(h-2*t)
        if a<A: hi=t
        else: lo=t
    t=(lo+hi)/2.0
    outer=[(-bo/2,-h/2),(bo/2,-h/2),(bo/2,h/2),(-bo/2,h/2)]
    bi,hi2=bo-2*t,h-2*t
    inner=[(-bi/2,-hi2/2),(bi/2,-hi2/2),(bi/2,hi2/2),(-bi/2,hi2/2)] if bi>0 and hi2>0 else None
    return outer,inner

def estribo(entrada,out):
    p=entrada["estribo"]; g=p["geom"]; ter=p["terreno"]; mat=dict(p.get("material",{})); mat["_nombre"]="HA-estribo"
    B=g["puntera"]+g["t_alz"]+g["talon"]
    m,body,site=G.nuevo(entrada.get("nombre","ESTRIBO"))
    # zapata B x 1.0, canto e_z, desde z=0
    foot=G.elem(m,body,site,"IfcFooting","ZAPATA_E",G._rect(m,B,1.0),g["e_z"],base=(0,0,0),predef="STRIP_FOOTING")
    G.pset(m,foot,"Pset_Estructurando_Cimentacion",{"puntera":g["puntera"],"talon":g["talon"],"Df":g.get("Df",g["e_z"])})
    # alzado t_alz x 1.0, alto Hm, desde z=e_z, x=puntera
    alz=G.elem(m,body,site,"IfcWall","ALZADO",G._rect(m,g["t_alz"],1.0),g["Hm"],base=(g["puntera"]+g["t_alz"]/2,0,g["e_z"]))
    G.material(m,alz,mat)
    G.pset(m,alz,"Pset_Estructurando_Terreno",ter)
    G.pset(m,alz,"Pset_Estructurando_Reacciones",p.get("reacciones",{}))
    G.pset(m,alz,"Pset_Estructurando_Puente",{"Rol":"estribo_alzado","sobrecarga":p.get("sobrecarga",10000)})
    m.write(out); print("IFC estribo:",out)

def vigas(entrada,out):
    t=entrada["tablero"]; td=entrada["tendon"]; vs=t["viga_sec"]; mat=dict(t["material"]); mat["_nombre"]="HP-viga"
    m,body,site=G.nuevo(entrada.get("nombre","TABLERO"))
    outer,inner=_box_para(vs["A"],vs["Iy"],vs["Iz"],vs["h"])
    prof=lambda: G._profile_box(m,outer,inner) if inner else G._profile_box(m,outer)
    n=t["n_vigas"]; sep=t["sep"]; y0=-(n-1)*sep/2.0
    for i in range(n):
        b=G.elem(m,body,site,"IfcBeam","VIGA_%d"%i,prof(),t["L"],base=(0,y0+i*sep,0),dirv=(1,0,0))
        G.material(m,b,mat)
        G.pset(m,b,"Pset_Estructurando_Seccion",{k:vs[k] for k in ("A","Iy","Iz","J","h","c_sup","c_inf","bw") if k in vs})
        if i==0:
            G.pset(m,b,"Pset_Estructurando_Tablero",
                {"Rol":"viga","ne":t["ne"],"n_riostras":t.get("n_riostras",2),"voladizo":t.get("voladizo",sep),
                 "g2_N_m2":t.get("g2_N_m2",0),"q_viento_N_m":t.get("q_viento_N_m",0),"posiciones":t.get("posiciones",41),
                 "alpha_termico":t.get("alpha_termico",1e-5),"dT_uniforme":t.get("dT_uniforme",15),"dT_gradiente":t.get("dT_gradiente",10),
                 "fctm":mat.get("fctm",0),"fck_transferencia":t.get("fck_transferencia",0),
                 "ri_A":t["riostra_sec"]["A"],"ri_Iy":t["riostra_sec"]["Iy"],"ri_Iz":t["riostra_sec"]["Iz"],"ri_J":t["riostra_sec"]["J"]})
            G.pset(m,b,"Pset_Estructurando_Tendon",td)
    m.write(out); print("IFC vigas:",out)

def losa(entrada,out):
    t=entrada["tablero"]; po=entrada["postesado"]; mat=dict(t["material"]); mat["_nombre"]="HP-losa"
    m,body,site=G.nuevo(entrada.get("nombre","LOSA"))
    slab=G.elem(m,body,site,"IfcSlab","LOSA",G._rect(m,t["L"],t["B"]),t["t"],base=(0,0,0),predef="FLOOR")
    G.material(m,slab,mat)
    extra={"Rol":"losa","nx":t["nx"],"ny":t["ny"],"g2_N_m2":t.get("g2_N_m2",0),"posiciones":t.get("posiciones",15),
           "n_carriles":t.get("n_carriles",2),"fck_transferencia":t.get("fck_transferencia",0)}
    vb=t.get("viga_borde")
    if vb: extra.update({"vb_A":vb["A"],"vb_Iy":vb["Iy"],"vb_Iz":vb["Iz"],"vb_J":vb["J"]})
    G.pset(m,slab,"Pset_Estructurando_Tablero",extra)
    G.pset(m,slab,"Pset_Estructurando_Postesado",po)
    m.write(out); print("IFC losa:",out)

def portico(entrada,out):
    p=entrada["portico"]; mat=dict(p["material"]); mat["_nombre"]="HA-portico"
    ds=p["dintel_sec"]; ps=p["pila_sec"]
    m,body,site=G.nuevo(entrada.get("nombre","PORTICO"))
    H=p["H"]; L=p["L"]
    # pilas (IfcColumn) en x=0 y x=L, altura H
    for i,x in enumerate((0.0,L)):
        c=G.elem(m,body,site,"IfcColumn","PILA_%d"%i,G._rect(m,ps["b"],ps["h"]),H,base=(x,0,0))
        G.material(m,c,mat)
        G.pset(m,c,"Pset_Estructurando_Puente",{"Rol":"pila_col","d":ps.get("d"),"As_pila_m2":p.get("As_pila_m2"),"beta_pila":p.get("beta_pila")})
        if i==0:
            G.pset(m,c,"Pset_Estructurando_Suelo",p["suelo"])
            G.pset(m,c,"Pset_Estructurando_Empuje",p["empuje"])
            G.pset(m,c,"Pset_Estructurando_Cimentacion",p["cimentacion"])
    # dintel (IfcBeam) horizontal a z=H
    d=G.elem(m,body,site,"IfcBeam","DINTEL",G._rect(m,ds["b"],ds["h"]),L,base=(0,0,H),dirv=(1,0,0))
    G.material(m,d,mat)
    G.pset(m,d,"Pset_Estructurando_Puente",{"Rol":"dintel","d":ds.get("d"),"ne":p["ne"],"np":p["np"],
        "g2_N_m":p.get("g2_N_m",0),"n_carriles":p.get("n_carriles",1),"As_dintel_m2":p.get("As_dintel_m2")})
    m.write(out); print("IFC portico:",out)

def celosia(entrada,out):
    c=entrada["celosia"]; mat=dict(c["material"]); mat["_nombre"]="S355"
    m,body,site=G.nuevo(entrada.get("nombre","CELOSIA"))
    L=c["L"]; h=c["h"]; n=c["n"]; dx=L/n
    cs=c["cordon_sec"]
    # cordon inferior: n segmentos (IfcBeam) -> da L y n
    import math
    r=math.sqrt(cs["A"]/math.pi) if cs["A"]>0 else 0.08
    for i in range(n):
        b=G.elem(m,body,site,"IfcBeam","CORDON_INF_%d"%i,G._circ(m,r),dx,base=(i*dx,0,0),dirv=(1,0,0))
        G.material(m,b,mat)
        if i==0:
            G.pset(m,b,"Pset_Estructurando_Celosia",{"Rol":"viga","h":h,"n":n,"g_N_m":c.get("g_N_m",0),
                "curva_pandeo":c.get("curva_pandeo","b"),"n_carriles":c.get("n_carriles",1),"posiciones":c.get("posiciones",17),
                "co_A":cs["A"],"co_Iy":cs["Iy"],"co_Iz":cs["Iz"],"co_J":cs["J"],
                "di_A":c["diagonal_sec"]["A"],"di_Iy":c["diagonal_sec"]["Iy"],"di_Iz":c["diagonal_sec"]["Iz"],"di_J":c["diagonal_sec"]["J"],
                "mo_A":c["montante_sec"]["A"],"mo_Iy":c["montante_sec"]["Iy"],"mo_Iz":c["montante_sec"]["Iz"],"mo_J":c["montante_sec"]["J"]})
    # montantes verticales (IfcMember) -> da h, marca tipologia celosia
    rm=math.sqrt(c["montante_sec"]["A"]/math.pi)
    for i in range(n+1):
        G.elem(m,body,site,"IfcMember","MONTANTE_%d"%i,G._circ(m,rm),h,base=(i*dx,0,0),dirv=(0,0,1))
    m.write(out); print("IFC celosia:",out)

_B={"estribo":estribo,"vigas":vigas,"losa":losa,"portico":portico,"celosia":celosia}
if __name__=="__main__":
    tip=sys.argv[1]; _B[tip](json.load(open(sys.argv[2])), sys.argv[3])

def pila(entrada,out):
    p=entrada["pila"]; reac=entrada.get("reacciones",{}); sec=p["pila_sec"]
    mat=dict(p["material"]); mat["_nombre"]="HA-pila"; cim=p["cimentacion"]; ap=p["apoyo"]
    m,body,site=G.nuevo(entrada.get("nombre","PILA"))
    tipo=cim.get("tipo","zapata")
    if tipo=="zapata":
        canto=cim.get("canto",1.4); zbase=canto
        f=G.elem(m,body,site,"IfcFooting","ZAPATA",G._rect(m,cim["B"],cim["Lf"]),canto,base=(0,0,0),predef="PAD_FOOTING")
        G.pset(m,f,"Pset_Estructurando_Cimentacion",dict(cim))
    elif tipo=="pilotes":
        D=cim["D"]; Lp=cim["L"]; n=cim.get("n",2); sep=cim.get("sep",3*D); canto=cim.get("encepado_canto",1.2); zbase=canto
        cap=G.elem(m,body,site,"IfcFooting","ENCEPADO",G._rect(m,max(2*sep,2.0),2.0),canto,base=(0,0,0),predef="PILE_CAP")
        G.pset(m,cap,"Pset_Estructurando_Cimentacion",dict(cim))
        for i in range(n):
            x=(i-(n-1)/2.0)*sep
            G.elem(m,body,site,"IfcPile","PILOTE_%d"%i,G._circ(m,D/2.0),Lp,base=(x,0,-Lp),predef="BORED")
    else:  # encepado (2 pilotes, region D)
        canto=cim.get("h",1.2); zbase=canto
        cap=G.elem(m,body,site,"IfcFooting","ENCEPADO",G._rect(m,cim.get("a",2.0),cim.get("b",1.0)),canto,base=(0,0,0),predef="PILE_CAP")
        G.pset(m,cap,"Pset_Estructurando_Cimentacion",dict(cim))
        for i in range(2):
            x=(i-0.5)*cim.get("a",2.0)
            G.elem(m,body,site,"IfcPile","PILOTE_%d"%i,G._circ(m,cim.get("d_pilote",0.45)/2.0),8.0,base=(x,0,-8.0),predef="BORED")
    pp=G.elem(m,body,site,"IfcColumn","PILA",G._rect(m,sec["b"],sec["h"]),p["H"],base=(0,0,zbase))
    G.material(m,pp,mat)
    G.pset(m,pp,"Pset_Estructurando_Suelo",p["suelo"])
    G.pset(m,pp,"Pset_Estructurando_Reacciones",reac)
    G.pset(m,pp,"Pset_Estructurando_Puente",{"Rol":"pila_col","d":sec.get("d"),"np":p.get("np",10),
        "As_pila_m2":p.get("As_pila_m2"),"beta_pila":p.get("beta_pila"),"q_viento_pila_N_m":p.get("q_viento_pila_N_m")})
    ztop=zbase+p["H"]
    apo=G.elem(m,body,site,"IfcBearing","APOYO",G._rect(m,ap["a"],ap["b"]),ap["Te"],base=(0,0,ztop),predef="ELASTOMERIC")
    G.pset(m,apo,"Pset_Estructurando_Apoyo",{"Tipo":ap.get("tipo","elastomerico"),"t_capa":ap.get("t_capa"),
        "n_capas":ap.get("n_capas"),"a":ap["a"],"b":ap["b"],"Te":ap["Te"]})
    m.write(out); print("IFC pila(%s):"%tipo,out)
_B["pila"]=pila
