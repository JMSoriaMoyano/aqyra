"""
ADAPTADOR DE LECTURA (puentes, PT 7.3.1): modelo neutro estructural (C1) ->
entrada_caso por tipologia. Capa thin: no recalcula; mapea geometria/Psets al
esquema que consumen los run_all_*. Predim. ICCP.
"""
from __future__ import annotations
import os, sys, json
_here=os.path.dirname(os.path.abspath(__file__))
# el parser C1 vive en iso19650 scripts/estructural; se provee por PYTHONPATH
import ifc_to_model_estructural as P

def _el(modelo, rol):
    return [e for e in modelo["elementos"] if e["rol"]==rol]

def _pset(e, name, key, default=None):
    return (e["psets"].get(name,{}) or {}).get(key, default)

def _pila(modelo):
    col=_el(modelo,"pila_col")[0]
    sec=col["seccion"]; mat={k:v for k,v in col["material"].items() if k!="_nombre"}
    pila={"H":round(col["geom"]["L"],6),
          "np":int(_pset(col,"Pset_Estructurando_Puente","np",10)),
          "e_long":0.0,
          "material":mat,
          "pila_sec":{"A":sec["A"],"Iy":sec["Iy"],"Iz":sec["Iz"],"J":sec["J"],
                      "b":sec.get("b"),"h":sec.get("h"),
                      "d":_pset(col,"Pset_Estructurando_Puente","d")},
          "suelo":{k:_pset(col,"Pset_Estructurando_Suelo",k) for k in ("kx","kz","kry")},
          "q_viento_pila_N_m":_pset(col,"Pset_Estructurando_Puente","q_viento_pila_N_m"),
          "As_pila_m2":_pset(col,"Pset_Estructurando_Puente","As_pila_m2"),
          "beta_pila":_pset(col,"Pset_Estructurando_Puente","beta_pila")}
    # apoyo
    aps=_el(modelo,"aparato_apoyo")
    if aps:
        a=aps[0]; s=a["seccion"]
        pila["apoyo"]={"tipo":_pset(a,"Pset_Estructurando_Apoyo","Tipo","elastomerico"),
                       "a":s.get("b"),"b":s.get("h"),"Te":round(a["geom"]["L"],6),
                       "t_capa":_pset(a,"Pset_Estructurando_Apoyo","t_capa"),
                       "n_capas":int(_pset(a,"Pset_Estructurando_Apoyo","n_capas",1))}
    # cimentacion
    caps=_el(modelo,"zapata")+_el(modelo,"encepado")
    if caps:
        c=caps[0]; s=c["seccion"]
        cm=dict(c["psets"].get("Pset_Estructurando_Cimentacion",{}))
        cm.setdefault("tipo","zapata")
        if cm["tipo"]=="zapata":
            cm["B"]=cm.get("B",s.get("b")); cm["Lf"]=cm.get("Lf",s.get("h"))
            cm["canto"]=round(c["geom"]["L"],6)
        # pilotes geometry desde IfcPile si existe
        pil=_el(modelo,"pilote")
        if pil and cm.get("tipo")=="pilotes":
            cm["D"]=cm.get("D",pil[0]["seccion"].get("D")); cm["L"]=cm.get("L",round(pil[0]["geom"]["L"],6))
            cm["n"]=int(cm.get("n",len(pil)))
        pila["cimentacion"]=cm
    # reacciones (cargas, no geometricas)
    reac={k:_pset(col,"Pset_Estructurando_Reacciones",k) for k in
          ("N_G_N","N_LM1_N","H_frenado_N","H_viento_N","H_termica_N","M_G_Nm","M_LM1_Nm")}
    reac={k:v for k,v in reac.items() if v is not None}
    return {"nombre":modelo.get("_nombre","PILA"),"pila":pila,"reacciones":reac}

def _estribo(modelo):
    alz=_el(modelo,"estribo_alzado")[0]
    zaps=_el(modelo,"zapata")
    # geometria del muro: alzado (IfcWall vertical) + zapata
    Hm=round(alz["geom"]["L"],6); t_alz=alz["seccion"].get("b") or alz["seccion"].get("h")
    geom={"Hm":Hm,"t_alz":t_alz}
    if zaps:
        z=zaps[0]; s=z["seccion"]
        geom["e_z"]=round(z["geom"]["L"],6)
        B=s.get("b"); 
        # puntera/talon: del Pset (reparto no deducible solo de la zapata)
        geom["puntera"]=_pset(z,"Pset_Estructurando_Cimentacion","puntera")
        geom["talon"]=_pset(z,"Pset_Estructurando_Cimentacion","talon")
        geom["Df"]=_pset(z,"Pset_Estructurando_Cimentacion","Df",geom["e_z"])
    terreno=alz["psets"].get("Pset_Estructurando_Terreno",{})
    material={k:v for k,v in alz["material"].items() if k in ("fck","E","nu","G","rho","fctm")}
    reac=alz["psets"].get("Pset_Estructurando_Reacciones",{})
    sob=_pset(alz,"Pset_Estructurando_Puente","sobrecarga",10000)
    est={"geom":geom,"terreno":dict(terreno),"material":material,
         "reacciones":dict(reac),"sobrecarga":sob}
    return {"nombre":modelo.get("_nombre","ESTRIBO"),"estribo":est}

# --- adaptadores de tablero (se inyectan en desde_ifc) ---
def _sorted_by(es,axis):
    return sorted(es,key=lambda e:e["geom"]["pi"][axis])

def _vigas(modelo, _el,_pset):
    vs=_sorted_by(_el(modelo,"viga"),1)
    v0=vs[0]; sec=v0["seccion"]
    ys=[v["geom"]["pi"][1] for v in vs]
    sep=abs(ys[1]-ys[0]) if len(ys)>1 else None
    mat={k:v for k,v in v0["material"].items() if k!="_nombre"}
    T=v0["psets"].get("Pset_Estructurando_Tablero",{})
    if "fctm" in T and "fctm" not in mat: mat["fctm"]=T["fctm"]
    tablero={"L":round(v0["geom"]["L"],6),"n_vigas":len(vs),"sep":sep,
        "voladizo":T.get("voladizo",sep),"ne":int(T.get("ne",20)),"n_riostras":int(T.get("n_riostras",2)),
        "g2_N_m2":T.get("g2_N_m2",0),"q_viento_N_m":T.get("q_viento_N_m",0),"posiciones":int(T.get("posiciones",41)),
        "alpha_termico":T.get("alpha_termico",1e-5),"dT_uniforme":T.get("dT_uniforme",15),"dT_gradiente":T.get("dT_gradiente",10),
        "fck_transferencia":T.get("fck_transferencia",0),"material":mat,
        "viga_sec":{k:sec[k] for k in ("A","Iy","Iz","J","h","c_sup","c_inf","bw") if k in sec},
        "riostra_sec":{"A":T.get("ri_A"),"Iy":T.get("ri_Iy"),"Iz":T.get("ri_Iz"),"J":T.get("ri_J")}}
    tendon=dict(v0["psets"].get("Pset_Estructurando_Tendon",{}))
    return {"nombre":modelo.get("_nombre","TABLERO"),"tablero":tablero,"tendon":tendon}

def _losa(modelo,_el,_pset):
    s=_el(modelo,"losa")[0]; sec=s["seccion"]
    mat={k:v for k,v in s["material"].items() if k!="_nombre"}
    T=s["psets"].get("Pset_Estructurando_Tablero",{})
    tablero={"L":round(sec["b"],6),"B":round(sec["h"],6),"t":round(s["geom"]["L"],6),
        "nx":int(T.get("nx",14)),"ny":int(T.get("ny",9)),"g2_N_m2":T.get("g2_N_m2",0),
        "posiciones":int(T.get("posiciones",15)),"n_carriles":int(T.get("n_carriles",2)),
        "fck_transferencia":T.get("fck_transferencia",0),"material":mat}
    if "vb_A" in T:
        tablero["viga_borde"]={"A":T["vb_A"],"Iy":T["vb_Iy"],"Iz":T["vb_Iz"],"J":T["vb_J"]}
    post=dict(s["psets"].get("Pset_Estructurando_Postesado",{}))
    return {"nombre":modelo.get("_nombre","LOSA"),"tablero":tablero,"postesado":post}

def _portico(modelo,_el,_pset):
    d=_el(modelo,"dintel")[0]; pilas=_el(modelo,"pila_col")
    p0=pilas[0]; ds=d["seccion"]; ps=p0["seccion"]
    mat={k:v for k,v in d["material"].items() if k!="_nombre"}
    DT=d["psets"].get("Pset_Estructurando_Puente",{}); PT=p0["psets"].get("Pset_Estructurando_Puente",{})
    portico={"L":round(d["geom"]["L"],6),"H":round(p0["geom"]["L"],6),
        "ne":int(DT.get("ne",10)),"np":int(DT.get("np",6)),"n_carriles":int(DT.get("n_carriles",2)),
        "g2_N_m":DT.get("g2_N_m",0),"beta_pila":PT.get("beta_pila",2.0),"material":mat,
        "dintel_sec":{"A":ds["A"],"Iy":ds["Iy"],"Iz":ds["Iz"],"J":ds["J"],"h":ds.get("h"),"b":ds.get("b"),"d":DT.get("d")},
        "pila_sec":{"A":ps["A"],"Iy":ps["Iy"],"Iz":ps["Iz"],"J":ps["J"],"h":ps.get("h"),"b":ps.get("b"),"d":PT.get("d")},
        "suelo":dict(p0["psets"].get("Pset_Estructurando_Suelo",{})),
        "empuje":dict(p0["psets"].get("Pset_Estructurando_Empuje",{})),
        "cimentacion":dict(p0["psets"].get("Pset_Estructurando_Cimentacion",{})),
        "As_dintel_m2":DT.get("As_dintel_m2"),"As_pila_m2":PT.get("As_pila_m2")}
    return {"nombre":modelo.get("_nombre","PORTICO"),"portico":portico}

def _celosia(modelo,_el,_pset):
    cor=_sorted_by(_el(modelo,"viga"),0)
    c0=cor[0]; C=c0["psets"].get("Pset_Estructurando_Celosia",{})
    mat={k:v for k,v in c0["material"].items() if k!="_nombre"}
    L=sum(round(c["geom"]["L"],6) for c in cor)
    cel={"L":round(L,6),"h":C.get("h"),"n":int(C.get("n",len(cor))),"material":mat,
        "g_N_m":C.get("g_N_m",0),"curva_pandeo":C.get("curva_pandeo","b"),
        "n_carriles":int(C.get("n_carriles",1)),"posiciones":int(C.get("posiciones",17)),
        "cordon_sec":{"A":C.get("co_A"),"Iy":C.get("co_Iy"),"Iz":C.get("co_Iz"),"J":C.get("co_J")},
        "diagonal_sec":{"A":C.get("di_A"),"Iy":C.get("di_Iy"),"Iz":C.get("di_Iz"),"J":C.get("di_J")},
        "montante_sec":{"A":C.get("mo_A"),"Iy":C.get("mo_Iy"),"Iz":C.get("mo_Iz"),"J":C.get("mo_J")}}
    return {"nombre":modelo.get("_nombre","CELOSIA"),"celosia":cel}

_DISPATCH={"pila":_pila,"estribo":_estribo,
           "vigas_pretensadas":lambda m:_vigas(m,_el,_pset),
           "losa_postesada":lambda m:_losa(m,_el,_pset),
           "portico":lambda m:_portico(m,_el,_pset),
           "celosia":lambda m:_celosia(m,_el,_pset)}

def leer(ifc_path):
    modelo=P.parse(ifc_path)
    tip=modelo["tipologia"]
    if tip not in _DISPATCH:
        raise ValueError("tipologia no soportada aun por el adaptador: %s"%tip)
    cfg=_DISPATCH[tip](modelo)
    cfg["_tipologia"]=tip
    return cfg

if __name__=="__main__":
    cfg=leer(sys.argv[1])
    if len(sys.argv)>2: json.dump(cfg,open(sys.argv[2],"w"),indent=2,ensure_ascii=False)
    print("tipologia:",cfg["_tipologia"])
    print(json.dumps(cfg,ensure_ascii=False)[:600])
