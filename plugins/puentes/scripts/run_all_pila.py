"""
Orquestador e2e del vertical PILA + APARATO DE APOYO + CIMENTACION (PT 7.3).

Flujo: pila (columna barra 3D) -> aparato de apoyo en cabeza (resorte) + base sobre
resorte Winkler -> reacciones del tablero en cabeza (modo 'caso' o 'acoplado') +
viento sobre el fuste + peso propio -> motor-fem (estatico G/M/F/V/T + modal) ->
EC2 fuste (M-N + cortante bielas + 2.o orden) + EC7 cimentacion (router) ->
resultado JSON + mapping write-back.

Consume `motor-fem` (C5) y reutiliza cimentaciones/pilotes/encepado por formula.
Pila plana XZ: estabilizar_plano=True; base y apoyo sobre resortes. gamma_Q=1.35
(trafico IAP-11). SI. Predim. (ICCP).
"""
from __future__ import annotations
import os, sys, json
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
import pila, iap11, ec2ec7_pila, resultado_ifc_puente, aparatos_apoyo
import mallador, fem1   # motor-fem (C5)


def ejecutar(p, nombre="PILA_PUE05", reac_tablero=None, resultado_tablero=None, apoyo_id=None):
    model, meta = pila.construir_pila(p)

    # aparato de apoyo (resorte 6 GdL) en cabeza
    ap_cfg = p.get("apoyo", {"tipo": "elastomerico", "a": 0.4, "b": 0.5, "Te": 0.063})
    if ap_cfg.get("tipo", "elastomerico") == "elastomerico":
        apoyo = aparatos_apoyo.elastomerico(ap_cfg["a"], ap_cfg["b"], ap_cfg["Te"],
                                            ap_cfg.get("t_capa"), ap_cfg.get("n_capas"),
                                            ap_cfg.get("G", 0.9e6), ap_cfg.get("Ec"))
    else:
        apoyo = aparatos_apoyo.pot(ap_cfg.get("subtipo", "fijo"))

    # reacciones del tablero (modo caso o acoplado al tablero PT 7.1/7.2)
    if resultado_tablero is not None:
        reac = aparatos_apoyo.reacciones_desde_tablero(resultado_tablero, apoyo_id)
    else:
        reac = aparatos_apoyo.reacciones_desde_caso(reac_tablero or p.get("reacciones", {}))

    M = mallador.desde_modelo_neutro(model, estabilizar_plano=True)
    s = meta["suelo"]
    M.add_resorte(meta["base_node"], [s["kx"], 0.0, s["kz"], 0.0, s["kry"], 0.0])
    # aparato de apoyo en cabeza: el resorte vertical/giro acompana, el horizontal
    # define la rigidez longitudinal; se anade como resorte de cabeza (a tierra =
    # tablero que aporta la reaccion). Para el modelo LOCAL de la pila el apoyo da
    # rigidez de cabeza adicional (serie con el fuste) sin restar la reaccion aplicada.
    av = apoyo["vector"]
    M.add_resorte(meta["head_node"], [0.0, av[1], 0.0, av[3], 0.0, av[5]])

    iap11.peso_propio_pila(p, M, meta)
    res_cab = iap11.cargas_cabeza_pila(reac, M, meta, e_long=p.get("e_long", 0.0))
    iap11.viento_pila(p, M, meta)

    combos = iap11.combinaciones_pila()
    sol = M.resolver(combos)["combos"]
    f1 = 0.0; modal = {"error": "no calculado"}
    for nm in (3, 2, 1):
        try:
            modal = fem1.modal(M, nmodos=nm, peso_propio=True)
            f1 = modal["frecuencias_Hz"][0]; break
        except Exception as e:
            modal = {"error": str(e)}

    base = meta["pila_barras"][0]
    ef = sol["ELU"]["esfuerzos_barra"][base]
    N_base = abs(ef["axial_i"]); M_base = abs(ef["My_i"]); V_base = abs(ef["Vz_i"])
    esf = {"N_base": N_base, "M_base": M_base, "V_base": V_base}

    chk = ec2ec7_pila.comprobar(p, esf)
    dx_head = sol["ELU"]["desplazamientos"][meta["head_node"]][0]

    resultado = {"nombre_tablero": nombre, "tipologia": "pila", "pila": p,
                 "aparato_apoyo": apoyo, "reacciones": reac, "cargas_cabeza": res_cab,
                 "f1_Hz": f1, "esfuerzos_base": esf, "dx_cabeza_m": dx_head,
                 "checks": chk["checks"], "cimentacion": chk["cimentacion"],
                 "elementos_chk": chk["elementos_chk"], "delta_2orden": chk["delta_2orden"],
                 "aprovechamiento_max": chk["aprovechamiento_max"], "veredicto_global": chk["veredicto"]}
    resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    return resultado


if __name__ == "__main__":
    import os as _o, sys as _s
    _s.path.insert(0, _o.path.join(_here, "lectura"))
    import cli_ifc as _cli
    cfg = _cli.load_cfg(sys.argv[1])  # JSON de caso o .ifc (lector C1)
    r = ejecutar(cfg["pila"], cfg.get("nombre", "PILA_PUE05"),
                 reac_tablero=cfg.get("reacciones"),
                 resultado_tablero=cfg.get("resultado_tablero"), apoyo_id=cfg.get("apoyo_id"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_pila.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"], "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| delta=%.3f" % r["delta_2orden"],
          "| cim=%s/%s" % (r["cimentacion"]["tipo"], r["cimentacion"]["veredicto"]))
