"""
Orquestador e2e del vertical LOSA POSTESADA (lamina DKMQ + IAP-11 + FEM-1 + EC2).

Flujo: tablero -> losa_lamina (malla DKMQ, C5) -> permanentes (g1/g2) + postesado
biaxial (balance de cargas, P_inf) -> motor-fem (estatico por casos + envolventes
LM1 via objetivo `esfuerzo_lamina` + modal) -> EC2 por franja de vano (tensiones
en vacio/servicio, descompresion, flexion ELU, punzonamiento si hay apoyo puntual)
-> resultado JSON + mapping write-back.

Consume el nucleo `motor-fem` (C5, FEM-1) y los modulos de postesado/EC2 por
PYTHONPATH (frontera de reuso). El momento de VANO es `Mx` (placa); gravedad p<0,
postesado p>0. Termica: en losa de UN vano (isostatica) el gradiente es libre
(sin restriccion) -> momento de restriccion ~0 (se documenta). SI. Predim. (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
import losa_lamina, iap11, ec2_losa, resultado_ifc_puente
import fem1   # motor-fem (C5)


def ejecutar(tablero, postesado, nombre_tablero="LOSA_PUE02"):
    M, meta = losa_lamina.construir_losa(tablero)
    perm = iap11.permanentes_losa(tablero, M, meta)
    post = iap11.postesado_losa(tablero, M, meta, postesado)
    caminos = losa_lamina.caminos_carriles(meta, tablero.get("n_carriles"))
    cm = iap11.lm1_losa(tablero, meta, caminos)

    casos = {"G1": {"G1": 1.0}, "G2": {"G2": 1.0}, "P": {"P": 1.0}}
    est = M.resolver(casos)["combos"]
    mov = fem1.movil(M, cm)
    try:
        modal = fem1.modal(M, nmodos=4, peso_propio=True)
        f1 = modal["frecuencias_Hz"][0]
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    perd = postesado.get("perdidas_pct", 18.0) / 100.0
    ratio_P0 = 1.0 / (1.0 - perd)          # P0/Pinf
    c = meta["t"] / 2.0; I = meta["t"] ** 3 / 12.0

    franjas = []
    for eid in meta["franja_centro"]:
        Mx_G1 = est["G1"]["esfuerzos_lamina"][eid]["Mx"]
        Mx_G2 = est["G2"]["esfuerzos_lamina"][eid]["Mx"] if "G2" in est else 0.0
        Mx_P = est["P"]["esfuerzos_lamina"][eid]["Mx"]
        env = mov["envolventes"]["Mx_%s" % eid]
        Mx_lm1 = env["min"]                 # mas negativo = mas sagging
        # sagging positivo = -Mx_fem
        M_net_transfer = -(Mx_G1 + Mx_P * ratio_P0)
        M_net_serv = -(Mx_G1 + Mx_G2 + Mx_P + Mx_lm1)
        M_net_cp = -(Mx_G1 + Mx_G2 + Mx_P + 0.2 * Mx_lm1)
        M_Ed_ELU = 1.35 * abs(Mx_G1 + Mx_G2) + 1.35 * abs(Mx_lm1)
        esf = {"M_net_transfer": M_net_transfer, "M_net_serv": M_net_serv,
               "M_net_cp": M_net_cp, "M_Ed_ELU": M_Ed_ELU,
               "w_equilibrar_N_m2": perm["w_equilibrar_N_m2"]}
        chk = ec2_losa.comprobar(tablero, postesado, esf, punz=tablero.get("punzonamiento"))
        franjas.append({"elem": eid, "Mx_G1": Mx_G1, "Mx_G2": Mx_G2, "Mx_P": Mx_P,
                        "Mx_lm1_sag": -Mx_lm1, "M_Ed_ELU": M_Ed_ELU, "M_Rd_Nm_m": chk["M_Rd_Nm_m"],
                        "aprov_max": chk["aprovechamiento_max"], "veredicto": chk["veredicto"],
                        "checks": chk["checks"], "tensiones": chk["tensiones"],
                        "As_pas_req_cm2_m": chk["As_pas_req_cm2_m"], "balance": chk["balance"]})

    f_crit = max(franjas, key=lambda f: f["aprov_max"])
    veredicto_global = "CUMPLE" if all(f["veredicto"] == "CUMPLE" for f in franjas) else "NO CUMPLE"
    resultado = {"nombre_tablero": nombre_tablero, "tipologia": "losa_postesada",
                 "tablero": tablero, "postesado": postesado, "permanentes": perm,
                 "postesado_balance": post, "carriles": [c["id"] for c in caminos],
                 "termica_nota": "Losa de un vano (isostatica): gradiente termico libre, M_restriccion ~ 0.",
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "franjas": franjas, "franja_critica": f_crit["elem"],
                 "aprovechamiento_max": f_crit["aprov_max"], "veredicto_global": veredicto_global}
    resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    return resultado


if __name__ == "__main__":
    cfg = json.load(open(sys.argv[1]))
    r = ejecutar(cfg["tablero"], cfg["postesado"], cfg.get("nombre", "LOSA_PUE02"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_losa.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"], "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| franja critica=%s" % r["franja_critica"])
