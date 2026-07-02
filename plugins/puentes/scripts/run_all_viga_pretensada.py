"""
Orquestador e2e del vertical VIGAS PRETENSADAS (emparrillado + IAP-11 + FEM-1 + EC2).

Flujo: tablero -> emparrillado (C5) -> permanentes/termica/viento -> inyeccion del
pretensado (cargas equivalentes) -> motor-fem (estatico + cargas moviles LM1 +
modal) -> comprobacion EC2 -> resultado JSON + mapping write-back.

Consume el nucleo `motor-fem` (C5) por PYTHONPATH (frontera: no recalcula la
mecanica). El emparrillado horizontal flecta FUERA de plano -> estabilizar_plano
DESACTIVADO (los apoyos isostaticos dan la estabilidad). SI. Predimensionado (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "pretensado", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
# motor-fem y pretensado se proveen por PYTHONPATH (el agente los anade)
import emparrillado, iap11, inyeccion_pretensado, ec2_tablero, resultado_ifc_puente
import mallador, fem1                      # motor-fem (C5)


def ejecutar(tablero, tendon, nombre_tablero="TABLERO_PUE01"):
    # 1) idealizacion
    model, meta = emparrillado.construir_emparrillado(tablero)
    # 2) acciones permanentes + viento (GZ/GY: mallador-friendly)
    perm = iap11.permanentes(tablero, model, meta)
    iap11.viento(tablero, model, meta)
    # 3) pretensado -> caso 'P'
    perdidas = inyeccion_pretensado.inyectar(model, meta, tendon)
    # 4) tren LM1 -> cargas_moviles
    cm = iap11.lm1(tablero, model, meta)
    # --- construir ModeloFEM (sin estabilizar_plano: grillage horizontal) ---
    termica_spec = iap11.termica(tablero, model, meta)   # anade cargas 'T' (nativas)
    termica_loads = [c for c in model["cargas"] if str(c.get("tipo", "")).startswith("termica")]
    model["cargas"] = [c for c in model["cargas"] if not str(c.get("tipo", "")).startswith("termica")]
    M = mallador.desde_modelo_neutro(model, estabilizar_plano=False)
    for c in termica_loads:                                # re-aplicar termica a las barras
        for el in M.elementos:
            if getattr(el, "eid", None) == c["barra"]:
                el.cargas.append({k: v for k, v in c.items() if k != "barra"})

    # 5a) estatico por casos
    casos = {"G": {"G": 1.0}, "P": {"P": 1.0}, "T": {"T": 1.0}, "V": {"V": 1.0}}
    est = M.resolver(casos)["combos"]
    # 5b) cargas moviles (envolvente LM1)
    mov = fem1.movil(M, cm)
    # 5c) modal (frecuencia fundamental, masa propia + perm cuasiperm)
    try:
        modal = fem1.modal(M, nmodos=4, peso_propio=True, masas_casos={"G": 1.0})
        f1 = modal["frecuencias_Hz"][0]
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    # --- esfuerzos por viga (My_j en centro, Vz_i en apoyo) ---
    n = meta["n_vigas"]; ne = meta["ne"]; mid = ne // 2
    psi0_T = 0.6; psi0_V = 0.6
    vigas = []
    for g in range(n):
        eid_c = "G_%d_%d" % (g, mid - 1); eid_a = "G_%d_0" % g
        M_G = est["G"]["esfuerzos_barra"][eid_c]["My_j"]
        M_T = est["T"]["esfuerzos_barra"][eid_c]["My_j"]
        M_V = est["V"]["esfuerzos_barra"][eid_c]["My_j"]
        V_G = est["G"]["esfuerzos_barra"][eid_a]["Vz_i"]
        M_lm1_max = mov["envolventes"]["M_centro_v%d" % g]["max"]
        M_lm1_min = mov["envolventes"]["M_centro_v%d" % g]["min"]
        _ev = mov["envolventes"]["V_apoyo_v%d" % g]; V_lm1 = max(abs(_ev["max"]), abs(_ev["min"]))
        M_perm = abs(M_G)
        M_Ed = 1.35 * abs(M_G) + 1.35 * abs(M_lm1_max) + 1.5 * psi0_T * abs(M_T) + 1.5 * psi0_V * abs(M_V)
        V_Ed = 1.35 * abs(V_G) + 1.35 * abs(V_lm1)
        esf = {"M_g1": perm["g1_N_m_viga"] * meta["L"] ** 2 / 8.0,
               "M_perm": M_perm, "M_lm1_max": abs(M_lm1_max), "M_lm1_min": M_lm1_min,
               "M_Ed_ELU": M_Ed, "V_Ed_ELU": V_Ed}
        chk = ec2_tablero.comprobar(tablero, tendon, perdidas, esf)
        flex = next(c for c in chk["checks"] if c["nombre"] == "flexion_ELU")
        vigas.append({"viga": g, "nombre": "VIGA_%d" % g, "M_perm": M_perm,
                      "M_lm1_max": abs(M_lm1_max), "M_Ed_ELU": M_Ed, "V_Ed_ELU": V_Ed,
                      "M_Rd_Nm": chk["M_Rd_Nm"], "V_Rdc_N": chk["V_Rdc_N"],
                      "aprov_flexion": flex["aprov"], "aprov_max": chk["aprovechamiento_max"],
                      "veredicto": chk["veredicto"], "checks": chk["checks"],
                      "tensiones": chk["tensiones"]})

    veredicto_global = "CUMPLE" if all(v["veredicto"] == "CUMPLE" for v in vigas) else "NO CUMPLE"
    g_critica = max(vigas, key=lambda v: v["aprov_max"])
    resultado = {"nombre_tablero": nombre_tablero, "tablero": tablero, "tendon": tendon,
                 "permanentes": perm, "perdidas": perdidas, "termica": termica_spec,
                 "carriles": [{"id": l["id"], "viga": l["viga"]} for l in cm["lineas"]],
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "vigas": vigas, "viga_critica": g_critica["viga"],
                 "aprovechamiento_max": g_critica["aprov_max"], "veredicto_global": veredicto_global}
    resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    return resultado


if __name__ == "__main__":
    import os as _o, sys as _s
    _s.path.insert(0, _o.path.join(_here, "lectura"))
    import cli_ifc as _cli
    cfg = _cli.load_cfg(sys.argv[1])  # JSON de caso o .ifc (lector C1)
    r = ejecutar(cfg["tablero"], cfg["tendon"], cfg.get("nombre", "TABLERO_PUE01"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_puente.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"], "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| viga critica=%d" % r["viga_critica"])
