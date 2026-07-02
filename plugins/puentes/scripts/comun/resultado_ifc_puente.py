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


def _cajon(resultado):
    sc=next(s for s in resultado["secciones"] if s["vano"]==resultado["seccion_critica"])
    elems={resultado.get("nombre_tablero","CAJON"):{PSET:{
        "Tipologia":"cajon_postesado",
        "A_m2": round(resultado["seccion_props"]["A"],3),
        "Iy_m4": round(resultado["seccion_props"]["Iy"],4),
        "J_Bredt_m4": round(resultado["seccion_props"]["J_bredt"],4),
        "P0_kN": round(resultado["postesado"]["P0_N"]/1e3,0),
        "P_inf_kN": round(resultado["balance_postesado"]["Pinf_N"]/1e3,0),
        "w_postesado_kN_m": round(resultado["balance_postesado"]["w_p_N_m"]/1e3,2),
        "Sigma_constr_sup_MPa": round(sc["tensiones"]["constr_sup_Pa"]/1e6,2),
        "Sigma_constr_inf_MPa": round(sc["tensiones"]["constr_inf_Pa"]/1e6,2),
        "Sigma_servicio_sup_MPa": round(sc["tensiones"]["servicio_sup_Pa"]/1e6,2),
        "Sigma_servicio_inf_MPa": round(sc["tensiones"]["servicio_inf_Pa"]/1e6,2),
        "M_Ed_ELU_kNm": round(sc["esfuerzos"]["M_Ed_ELU_Nm"]/1e3,1),
        "M_Rd_kNm": round(sc["M_Rd_Nm"]/1e3,1),
        "Interaccion_V_T": round(sc["interaccion_VT"],3),
        "Shear_lag_beff_frac": round(sc["shear_lag_beff_frac"],3),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}}
    return {"elementos": elems}

def _mixto(resultado):
    sc=resultado["secciones"][resultado["seccion_critica"]]
    sp=resultado["seccion_props"]
    elems={resultado.get("nombre_tablero","MIXTO"):{PSET:{
        "Tipologia":"mixto_acero_hormigon",
        "Clase_seccion": resultado.get("clasificacion_seccion"),
        "A_acero_m2": round(sp["A_acero_m2"],4), "I_comp_m4": round(sp["I_comp_m4"],5),
        "b_eff_losa_m": round(sp["b_eff_losa_m"],3),
        "M_Ed_ELU_kNm": round(sc["esfuerzos"]["M_Ed_Nm"]/1e3,1),
        "M_Rd_total_kNm": round(sc["M_Rd_total_Nm"]/1e3,1),
        "PNA_zona": sc.get("PNA_zona"),
        "Conexion_eta": round((sc.get("conexion") or {}).get("grado_eta",0.0),3),
        "Fatiga_Dsigma_E2_MPa": round((sc.get("fatiga") or {}).get("delta_sigma_E2_MPa",0.0),1),
        "Fatiga_Dsigma_Rd_MPa": round((sc.get("fatiga") or {}).get("delta_sigma_Rd_MPa",0.0),1),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}}
    return {"elementos": elems}


def _oblicuo(resultado):
    det=resultado.get("detalle",{})
    elems={resultado.get("nombre_tablero","OBLICUO"):{PSET:{
        "Tipologia":"tablero_oblicuo",
        "Esviaje_deg": resultado["oblicuo"].get("esviaje_deg",0.0),
        "Concentracion_esquina_obtusa": round(resultado.get("concentracion_obtusa",0.0),2),
        "R_obtusa_kN": round(resultado["reacciones_esquinas"]["R_obtusa_N"]/1e3,0),
        "Factor_reparto_transversal": round(det.get("factor_reparto_transversal",1.0),3),
        "As_long_cm2_m": round((det.get("armado_long") or {}).get("As_prov_cm2_m",0.0),1),
        "As_transv_cm2_m": round((det.get("armado_transv") or {}).get("As_prov_cm2_m",0.0),1),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
        "Aprovechamiento_max": round(resultado["aprovechamiento_max"],3),
        "Veredicto_global": resultado["veredicto_global"]}}}
    return {"elementos": elems}


def _curvo(resultado):
    sp=resultado["seccion_props"]; tau=resultado.get("tau_Pa",{})
    elems={resultado.get("nombre_tablero","CURVO"):{PSET:{
        "Tipologia":"tablero_curvo",
        "R_m": resultado["curvo"].get("R"),
        "A_m2": round(sp["A"],3), "Iy_m4": round(sp["Iy"],4), "J_Bredt_m4": round(sp["J_bredt"],4),
        "M_Ed_kNm": round(resultado["esfuerzos"]["M_Ed_Nm"]/1e3,1),
        "T_apoyo_kNm": round(resultado["torsion_apoyo"]["T_apoyo_Nm"]/1e3,1),
        "Acoplamiento_T_M": round(resultado.get("acoplamiento_T_M",0.0),3),
        "Tau_total_MPa": round(tau.get("total",0.0)/1e6,2),
        "Tau_Rd_MPa": round(tau.get("Rd",0.0)/1e6,2),
        "Frecuencia_fundamental_Hz": round(resultado.get("f1_Hz",0.0),2),
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
    if tip=="cajon": return _cajon(resultado)
    if tip=="mixto": return _mixto(resultado)
    if tip=="oblicuo": return _oblicuo(resultado)
    if tip=="curvo": return _curvo(resultado)
    return {"elementos":{resultado.get("nombre_tablero","ESTRUCTURA"):{PSET:{
        "Aprovechamiento_max": round(resultado.get("aprovechamiento_max",0.0),3),
        "Veredicto_global": resultado.get("veredicto_global","N/A")}}}}
