"""
Orquestador e2e del vertical CAJON POSTESADO (lamina pura MITC4 + IAP-11 + FEM-2 +
EC2). PT 7.4 (Ola 7).

Flujo: cajon -> idealizacion por LAMINA (motor-fem FEM-2: lamina curva +
rigidizadores de diafragma) -> permanentes (g1 peso propio + g2) + postesado
evolutivo (balance de cargas, P0/Pinf por fases) -> motor-fem (estatico por casos
+ envolventes LM1 via objetivo `esfuerzo_lamina` + modal) -> EC2 por seccion
critica (tensiones por FASE construccion/servicio, descompresion, flexion ELU,
cortante+torsion de Bredt, shear lag) -> resultado JSON + mapping write-back.

Consume el nucleo `motor-fem` (C5, FEM-2) por PYTHONPATH. Las fibras de tension se
toman del FEM (Nx de panel/t -> shear lag nativo); la precompresion del postesado
es analitica (sigma_cp=-P/A). SI. Predimensionado/asistencia; revisar y firmar (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
import cajon as CJ
import ec2_cajon
import resultado_ifc_puente
import fem1   # motor-fem (C5)


def _nx(esf, eid, comp="Nx"):
    return esf.get(eid, {}).get(comp, 0.0)


def ejecutar(cajon, postesado, nombre_tablero="CAJON_PUE17"):
    M, meta = CJ.construir_cajon(cajon)
    props = meta["props"]
    rho = cajon["material"].get("rho", 2500.0)
    CJ.aplicar_peso_propio(M, meta, rho, caso="G1")
    if cajon.get("g2_N_m2"):
        CJ.aplicar_carga_muerta(M, meta, cajon["g2_N_m2"], caso="G2")
    bal = CJ.inyectar_postesado(M, meta, postesado, caso="P")

    casos = {"G1": {"G1": 1.0}, "P": {"P": 1.0}}
    if cajon.get("g2_N_m2"):
        casos["G2"] = {"G2": 1.0}
    est = M.resolver(casos)["combos"]
    cm = CJ.lm1_cargas_moviles(meta, postesado)
    mov = fem1.movil(M, cm)
    # modal INFORMATIVO: la lamina con drilling ficticio y masa solo traslacional
    # genera modos espurios de muy baja energia -> se reporta el primer modo FISICO
    # (frecuencia por encima de un umbral). Degradar con gracia (criterios PT 7.3).
    try:
        modal = fem1.modal(M, nmodos=8, peso_propio=True)
        fis = [fr for fr in modal["frecuencias_Hz"] if fr > 0.5]
        f1 = fis[0] if fis else (modal["frecuencias_Hz"][-1] if modal["frecuencias_Hz"] else 0.0)
        modal["f1_fisica_Hz"] = f1
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    perd = postesado.get("perdidas_pct", 18.0) / 100.0
    ratio_P0 = 1.0 / (1.0 - perd)
    tt = cajon["t_top"]; tb = cajon["t_bot"]
    I = props["Iy"]; c_inf = props["c_inf"]

    secciones = []
    for sc in meta["sec_crit"]:
        top = sc["panel_top"]; bot = sc["panel_bot"]
        # fibra = Nx/t (traccion positiva). top: compresion (Nx<0) en sagging; bot: traccion.
        def sfem(panel, t, cases):
            return sum(_nx(est[c]["esfuerzos_lamina"], panel) for c in cases) / t
        # FEM bending fiber (sin precompresion axil; va en EC2)
        sig_top_g1 = _nx(est["G1"]["esfuerzos_lamina"], top) / tt
        sig_bot_g1 = _nx(est["G1"]["esfuerzos_lamina"], bot) / tb
        sig_top_g2 = (_nx(est["G2"]["esfuerzos_lamina"], top) / tt) if "G2" in est else 0.0
        sig_bot_g2 = (_nx(est["G2"]["esfuerzos_lamina"], bot) / tb) if "G2" in est else 0.0
        sig_top_P = _nx(est["P"]["esfuerzos_lamina"], top) / tt
        sig_bot_P = _nx(est["P"]["esfuerzos_lamina"], bot) / tb
        env_bot = mov["envolventes"]["Nx_bot_%d" % sc["vano"]]
        env_top = mov["envolventes"]["Nx_top_%d" % sc["vano"]]
        sig_bot_lm1 = max(env_bot["max"], abs(env_bot["min"])) / tb     # traccion fondo
        sig_top_lm1 = -max(env_top["max"], abs(env_top["min"])) / tt    # compresion cabeza

        esf = {
            "sig_top_transfer": sig_top_g1 + ratio_P0 * sig_top_P,
            "sig_bot_transfer": sig_bot_g1 + ratio_P0 * sig_bot_P,
            "sig_top_serv": sig_top_g1 + sig_top_g2 + sig_top_P + sig_top_lm1,
            "sig_bot_serv": sig_bot_g1 + sig_bot_g2 + sig_bot_P + sig_bot_lm1,
            "sig_bot_cp": sig_bot_g1 + sig_bot_g2 + sig_bot_P + 0.2 * sig_bot_lm1,
            "M_Ed_ELU_Nm": (1.35 * abs(sig_bot_g1 + sig_bot_g2) + 1.35 * abs(sig_bot_lm1)) * I / c_inf,
            "V_Ed_N": cajon.get("V_Ed_N", 0.0),
            "T_Ed_Nm": cajon.get("T_Ed_Nm", 0.0),
            "Nx_ala_borde": _nx(est["G1"]["esfuerzos_lamina"], "TOP_%d_0" % sc["ix"]),
            "Nx_ala_centro": _nx(est["G1"]["esfuerzos_lamina"], top),
        }
        chk = ec2_cajon.comprobar(cajon, postesado, esf, props)
        secciones.append({"vano": sc["vano"], "x": sc["x"], "panel_bot": bot, "panel_top": top,
                          "esfuerzos": esf, "veredicto": chk["veredicto"],
                          "aprov_max": chk["aprovechamiento_max"], "checks": chk["checks"],
                          "tensiones": chk["tensiones"], "M_Rd_Nm": chk["M_Rd_Nm"],
                          "interaccion_VT": chk["interaccion_VT"],
                          "shear_lag_beff_frac": chk["shear_lag_beff_frac"]})

    s_crit = max(secciones, key=lambda s: s["aprov_max"])
    veredicto = "CUMPLE" if all(s["veredicto"] == "CUMPLE" for s in secciones) else "NO CUMPLE"
    resultado = {"nombre_tablero": nombre_tablero, "tipologia": "cajon",
                 "cajon": cajon, "postesado": postesado, "balance_postesado": bal,
                 "seccion_props": {k: props[k] for k in ("A", "Iy", "c_sup", "c_inf", "Am_bredt", "J_bredt")},
                 "n_nodos": len(M.norden), "n_elementos": len(M.elementos),
                 "carriles": [c["id"] for c in meta["caminos"]],
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "secciones": secciones, "seccion_critica": s_crit["vano"],
                 "aprovechamiento_max": s_crit["aprov_max"], "veredicto_global": veredicto}
    try:
        resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    except Exception as e:
        resultado["mapping_writeback"] = {"_error": str(e)}
    return resultado


if __name__ == "__main__":
    src = sys.argv[1]
    if src.lower().endswith(".ifc"):
        sys.path.insert(0, os.path.join(_here, "lectura"))
        import desde_ifc
        cfg = desde_ifc.leer(src)
    else:
        cfg = json.load(open(src))
    r = ejecutar(cfg["cajon"], cfg["postesado"], cfg.get("nombre", "CAJON_PUE17"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_cajon.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"],
          "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| seccion critica vano=%s" % r["seccion_critica"])
