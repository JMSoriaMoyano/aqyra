"""
Orquestador e2e del vertical TABLERO OBLICUO (esviado). PT 7.5 (Ola 7).

Flujo: oblicuo -> idealizacion (malla romboidal que sigue la linea de apoyo
esviada, laminas curvas MITC4) -> permanentes + LM1 estatico -> motor-fem
(estatico por casos + modal informativo) -> reparto transversal 2D, reaccion en la
esquina OBTUSA, momentos de franja -> EC2 (armado de losa) o EC3 (placa metalica)
-> resultado JSON + write-back. El motor-fem NO se toca. SI (N, m).
Predimensionado/asistencia; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "comprobacion", "comun", "lectura"):
    sys.path.insert(0, os.path.join(_here, sub))
import oblicuo as OB
import ec_oblicuo
import resultado_ifc_puente
import fem1


def ejecutar(obl, nombre_tablero="OBLICUO_PUE19"):
    M, meta = OB.construir_oblicuo(obl)
    OB.aplicar_peso_propio(M, meta, "G1")
    if obl.get("g2_N_m2"):
        OB.aplicar_carga_muerta(M, meta, obl["g2_N_m2"], "G2")
    lm1 = OB.aplicar_lm1_estatico(M, meta, "Q")
    casos = {"ELU": {"G1": 1.35, "Q": 1.35}, "ELS": {"G1": 1.0, "Q": 1.0}}
    if obl.get("g2_N_m2"):
        casos["ELU"]["G2"] = 1.35; casos["ELS"]["G2"] = 1.0
    est = M.resolver(casos)["combos"]

    try:
        modal = fem1.modal(M, nmodos=8, peso_propio=True)
        fis = [fr for fr in modal["frecuencias_Hz"] if fr > 0.5]
        f1 = fis[0] if fis else (modal["frecuencias_Hz"][-1] if modal["frecuencias_Hz"] else 0.0)
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    mx = OB.momentos_franja(est["ELU"], meta, "Mx")
    my = OB.momentos_franja(est["ELU"], meta, "My")
    reac = OB.reacciones_esquinas(est["ELU"], meta)
    esf = {"Mx_max_Nm_m": mx["M_max_Nm_m"], "My_max_Nm_m": my["M_max_Nm_m"],
           "factor_reparto": mx.get("factor_reparto", 1.0)}
    chk = ec_oblicuo.comprobar(obl, esf, reac)

    resultado = {"nombre_tablero": nombre_tablero, "tipologia": "oblicuo",
                 "oblicuo": obl, "lm1": lm1,
                 "n_nodos": len(M.norden), "n_elementos": len(M.elementos),
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "esfuerzos": esf, "reacciones_esquinas": reac,
                 "concentracion_obtusa": reac["concentracion_obtusa"],
                 "checks": chk["checks"], "detalle": chk["detalle"],
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
    r = ejecutar(cfg["oblicuo"], cfg.get("nombre", "OBLICUO_PUE19"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_oblicuo.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"],
          "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| esviaje=%.0f deg" % r["oblicuo"].get("esviaje_deg", 0.0),
          "| conc_obtusa=%.2f" % r["concentracion_obtusa"],
          "| f1=%.2f Hz" % r["f1_Hz"])
