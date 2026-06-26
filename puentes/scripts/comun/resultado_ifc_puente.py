from __future__ import annotations
PSET = "Pset_Estructurando_ResultadoPuente"

def _vigas(resultado):
    elems = {}
    for v in resultado["vigas"]:
        elems[v["nombre"]] = {PSET: {
            "M_perm_kNm": round(v["M_perm"]/1e3,1), "M_LM1_max_kNm": round(v["M_lm1_max"]/1e3,1),
            "M_Ed_ELU_kNm": round(v["M_Ed_ELU"]/1e3,1), "V_Ed_ELU_kN": round(v["V_Ed_ELU"]/1e3,1),
            "M_Rd_kNm": round(v["M_Rd_Nm"]/1e3,1), "Aprovechamiento_flexion": round(v["aprov_flexion"],3),
            "Aprovechamiento_max": round(v["aprov_max"],3), "Veredicto": v["veredicto"]}}
    res=resultado
    elems[res.get("nombre_tablero","TABLERO")]={PSET:{
        "Perdidas_pretensado_pct": round(res["perdidas"]["perdidas_totales_pct"],1),
        "P0_kN": round(res["perdidas"]["P0_N"]/1e3,0), "P_inf_kN": round(res["perdidas"]["P_inf_N"]/1e3,0),
        "Frecuencia_fundamental_Hz": round(res.get("f1_Hz",0.0),2), "Veredicto_global": res["veredicto_global"]}}
    return {"elementos": elems}

def _losa(resultado):
    fc=next(f for f in resultado["franjas"] if f["elem"]==resultado["franja_critica"])
    elems={resultado.get("nombre_tablero","LOSA"):{PSET:{
        "Tipologia":"losa_postesada","M_Ed_ELU_vano_kNm_m": round(fc["M_Ed_ELU"]/1e3,1),
        "M_Rd_vano_kNm_m": round(fc["M_Rd_Nm_m"]/1e3,1),
        "Sigma_servicio_inf_MPa": round(fc["tensiones"]["servicio_inf_Pa"]/1e6,2),
        "Sigma_servicio_sup_MPa": round(fc["tensiones"]["servicio_sup_Pa"]/1e6,2),
        "w_postesado_kN_m2": round(resultado["postesado_balance"]["w_p_N_m2"]/1e3,2),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}}
    return {"elementos": elems}

def _portico(resultado):
    elems={}
    for m in resultado["elementos_chk"]:
        elems[m["nombre"]]={PSET:{"Tipologia":"portico","M_Ed_ELU_kNm": round(m["M_Ed_Nm"]/1e3,1),
            "M_Rd_kNm": round(m["M_Rd_Nm"]/1e3,1),"Aprovechamiento_max": round(m["aprov_max"],3),
            "Veredicto": m["veredicto"]}}
    cim=resultado.get("ec7",{})
    elems[resultado.get("nombre_tablero","PORTICO")]={PSET:{"Tipologia":"portico",
        "Empuje_K": round(resultado.get("K_empuje",0.0),3),
        "Tension_max_terreno_kPa": round(cim.get("sigma_max_kPa",0.0),1),
        "Aprov_hundimiento": round(cim.get("aprov_hundimiento",0.0),3),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}
    return {"elementos": elems}

def _celosia(resultado):
    bc=resultado["barra_critica"]
    elems={bc["nombre"]:{PSET:{"Tipologia":"celosia","N_Ed_kN": round(bc["N_Ed_N"]/1e3,1),
        "N_Rd_kN": round(bc["N_Rd_N"]/1e3,1),"Modo": bc["modo"],
        "Aprovechamiento": round(bc["aprov"],3),"Veredicto": bc["veredicto"]}}}
    elems[resultado.get("nombre_tablero","CELOSIA")]={PSET:{"Tipologia":"celosia",
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Fatiga": resultado.get("fatiga_nota","gancho diferido"),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}
    return {"elementos": elems}

def _pila(resultado):
    cim=resultado.get("cimentacion",{})
    elems={}
    for m in resultado["elementos_chk"]:
        d={PSET:{"Tipologia":"pila","Aprovechamiento_max": round(m.get("aprov_max",0.0),3),
            "Veredicto": m["veredicto"]}}
        if "M_Ed_kNm" in m: d[PSET]["M_Ed_ELU_kNm"]=round(m["M_Ed_kNm"],1)
        if "M_Rd_kNm" in m: d[PSET]["M_Rd_kNm"]=round(m["M_Rd_kNm"],1)
        if "N_Ed_kN" in m: d[PSET]["N_Ed_ELU_kN"]=round(m["N_Ed_kN"],1)
        elems[m["nombre"]]=d
    elems[resultado.get("nombre_tablero","PILA")]={PSET:{"Tipologia":"pila",
        "Cimentacion": cim.get("tipo","-"),
        "Aprov_cimentacion": round(cim.get("aprov",0.0),3),
        "Delta_2orden": round(resultado.get("delta_2orden",1.0),3),
        "Desplazamiento_cabeza_mm": round(resultado.get("dx_cabeza_m",0.0)*1e3,1),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}
    return {"elementos": elems}

def _estribo(resultado):
    ap=resultado.get("aprovechamientos",{})
    elems={resultado.get("nombre_tablero","ESTRIBO"):{PSET:{"Tipologia":"estribo",
        "Empuje": resultado.get("metodo_empuje","activo"),"Ka": round(resultado.get("Ka",0.0),3),
        "Aprov_vuelco": round(resultado.get("vuelco",{}).get("u",0.0),3),
        "Aprov_deslizamiento": round(resultado.get("deslizamiento",{}).get("u",0.0),3),
        "Aprov_hundimiento": round(resultado.get("hundimiento",{}).get("u",0.0),3),
        "As_alzado_cm2_m": round(resultado.get("alzado",{}).get("As_prov_cm2_m",0.0),1),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}}
    return {"elementos": elems}

def construir_mapping(resultado):
    if "vigas" in resultado: return _vigas(resultado)
    tip=resultado.get("tipologia")
    if tip=="losa_postesada": return _losa(resultado)
    if tip=="portico": return _portico(resultado)
    if tip=="celosia": return _celosia(resultado)
    if tip=="pila": return _pila(resultado)
    if tip=="estribo": return _estribo(resultado)
    return {"elementos":{resultado.get("nombre_tablero","ESTRUCTURA"):{PSET:{
        "Aprovechamiento_max": round(resultado.get("aprovechamiento_max",0.0),3),
        "Veredicto_global": resultado.get("veredicto_global","N/A")}}}}
