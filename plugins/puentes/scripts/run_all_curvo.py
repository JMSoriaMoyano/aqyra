"""
Orquestador e2e del vertical TABLERO CURVO en planta (viga-cajon sobre eje curvo).
PT 7.5 (Ola 7).

Flujo: curvo -> idealizacion (malla de laminas curvas siguiendo la directriz del
eje, arco de radio R o IfcAlignment de la Ola 5) -> permanentes + LM1 estatico ->
motor-fem (estatico + modal informativo) -> recuperacion del MOMENTO de seccion y
del PAR TORSOR de apoyo (couple de reacciones entre almas; dT/ds=M/R) ->
comprobacion EC2 con TORSION de Bredt protagonista -> resultado JSON + write-back.
El motor-fem NO se toca. SI (N, m). Predimensionado/asistencia; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "comprobacion", "comun", "lectura"):
    sys.path.insert(0, os.path.join(_here, sub))
import curvo as CV
import ec_curvo
import resultado_ifc_puente
import fem1


def ejecutar(curvo, nombre_tablero="CURVO_PUE20"):
    M, meta = CV.construir_curvo(curvo)
    CV.aplicar_peso_propio(M, meta, "G1")
    if curvo.get("g2_N_m2"):
        CV.aplicar_carga_muerta(M, meta, curvo["g2_N_m2"], "G2")
    lm1 = CV.aplicar_lm1_estatico(M, meta, "Q")
    casos = {"ELU": {"G1": 1.35, "Q": 1.35}, "G": {"G1": 1.0}}
    if curvo.get("g2_N_m2"):
        casos["ELU"]["G2"] = 1.35
    est = M.resolver(casos)["combos"]

    try:
        modal = fem1.modal(M, nmodos=8, peso_propio=True)
        fis = [fr for fr in modal["frecuencias_Hz"] if fr > 0.5]
        f1 = fis[0] if fis else (modal["frecuencias_Hz"][-1] if modal["frecuencias_Hz"] else 0.0)
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    ix = meta["sec_crit"][0]["ix"]
    M_Ed = abs(CV.momento_seccion(M, est["ELU"], meta, ix))
    tors = CV.torsion_apoyo(est["ELU"], meta)
    # cortante de apoyo (suma de reacciones verticales / 2 lados)
    reac = est["ELU"]["reacciones"]
    V_Ed = sum(abs(reac.get(n, [0, 0, 0])[2]) for n in meta["apoyos"]["inicio"]["ext"]
               + meta["apoyos"]["inicio"]["int"])
    esf = {"M_Ed_Nm": M_Ed, "T_Ed_Nm": tors["T_apoyo_Nm"], "V_Ed_N": V_Ed}
    chk = ec_curvo.comprobar(curvo, esf, meta["props"])

    resultado = {"nombre_tablero": nombre_tablero, "tipologia": "curvo",
                 "curvo": curvo, "lm1": lm1,
                 "seccion_props": {k: meta["props"][k] for k in ("A", "Iy", "c_sup", "c_inf", "Am_bredt", "J_bredt")},
                 "n_nodos": len(M.norden), "n_elementos": len(M.elementos),
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "esfuerzos": esf, "torsion_apoyo": tors,
                 "acoplamiento_T_M": chk["acoplamiento_T_M"], "tau_Pa": chk["tau_Pa"],
                 "checks": chk["checks"], "tensiones": chk["tensiones"],
                 "aprovechamiento_max": chk["aprovechamiento_max"],
                 "veredicto_global": chk["veredicto"]}
    try:
        resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    except Exception as e:
        resultado["mapping_writeback"] = {"_error": str(e)}
    return resultado


if __name__ == "__main__":
    src = sys.argv[1]
    if src.lower().endswith(".ifc"):
        import desde_ifc
        cfg = desde_ifc.leer(src)
    else:
        cfg = json.load(open(src))
    r = ejecutar(cfg["curvo"], cfg.get("nombre", "CURVO_PUE20"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_curvo.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"],
          "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| R=%.0f m" % r["curvo"]["R"], "| T/M=%.3f" % r["acoplamiento_T_M"],
          "| T_apoyo=%.0f kNm" % (r["torsion_apoyo"]["T_apoyo_Nm"] / 1e3),
          "| f1=%.2f Hz" % r["f1_Hz"])
