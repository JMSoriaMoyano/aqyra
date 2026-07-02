"""
Orquestador e2e del vertical PORTICO (barras+resortes + IAP-11 + empuje + FEM-1 + EC2/EC7).

Flujo: portico -> barras+resortes Winkler (C5) -> permanentes (dintel) + empuje de
tierras K0 (pilas) + LM1 (camino del dintel) -> motor-fem (estatico G/E +
envolventes LM1 + modal) -> EC2 (dintel flexion/cortante; pilas flexion con 2.º
orden aproximado) + EC7 (cimentacion) -> resultado JSON + mapping write-back.

Consume `motor-fem` (C5) y `verificacion_muro` por PYTHONPATH. Marco plano XZ:
estabilizar_plano=True; los resortes de base dan la estabilidad en el plano.
Empuje K0 reposo (decision PT 7.2). 2.º orden aproximado. SI. Predim. (ICCP).
"""
from __future__ import annotations
import os, sys, json, math
_here = os.path.dirname(os.path.abspath(__file__))
for sub in ("idealizacion", "acciones", "comprobacion", "comun"):
    sys.path.insert(0, os.path.join(_here, sub))
import portico, iap11, ec2ec7_portico, resultado_ifc_puente
import mallador, fem1   # motor-fem (C5)


def K0_reposo(phi_grados):
    return 1.0 - math.sin(math.radians(phi_grados))


def ejecutar(p, nombre="PORTICO_PUE03"):
    model, meta = portico.construir_portico(p)
    perm = iap11.permanentes_portico(p, model, meta)
    # empuje K0 (reposo) a partir de phi del relleno
    p.setdefault("empuje", {})
    p["empuje"]["K"] = p["empuje"].get("K", K0_reposo(p["empuje"].get("phi", 30.0)))
    emp = iap11.empuje_tierras(p, model, meta)
    cm = iap11.lm1_portico(p, model, meta)

    M = mallador.desde_modelo_neutro(model, estabilizar_plano=True)
    suelo = meta["suelo"]
    for bn in meta["base_nodes"]:
        M.add_resorte(bn, [suelo["kx"], 0.0, suelo["kz"], 0.0, suelo["kry"], 0.0])

    casos = {"G": {"G": 1.0}, "E": {"E": 1.0}}
    est = M.resolver(casos)["combos"]
    mov = fem1.movil(M, cm)
    try:
        modal = fem1.modal(M, nmodos=4, peso_propio=True)
        f1 = modal["frecuencias_Hz"][0]
    except Exception as e:
        f1 = 0.0; modal = {"error": str(e)}

    L = meta["L"]; H = meta["H"]; ne = meta["ne"]
    A_p = model["secciones"]["PILA"]["A"]; rho = model["materiales"]["HORM"]["rho"]
    g1 = perm["g1_N_m"]; g2 = perm["g2_N_m"]
    # LM1 totales (carril dominante de lm1_portico)
    tren = cm["lineas"][0]["tren"]
    Qe_tot = sum(a["P"] for a in tren["axles"]); udl = tren["udl"]
    LM1_vert = Qe_tot + udl * L

    # --- dintel ---
    mid = ne // 2
    M_G_d = est["G"]["esfuerzos_barra"]["DIN_%d" % mid]["My_i"]
    env_d = mov["envolventes"]["M_dintel"]; M_lm1_d = max(abs(env_d["max"]), abs(env_d["min"]))
    M_dintel_Ed = 1.35 * abs(M_G_d) + 1.35 * M_lm1_d
    V_dintel_Ed = 1.35 * (g1 + g2) * L / 2.0 + 1.35 * (Qe_tot + udl * L / 2.0)

    # --- pila (base) ---
    M_G_p = est["G"]["esfuerzos_barra"][meta["pilaL_barras"][0]]["My_i"]
    M_E_p = est["E"]["esfuerzos_barra"][meta["pilaL_barras"][0]]["My_i"]
    env_p = mov["envolventes"]["M_pilaL_base"]; M_lm1_p = max(abs(env_p["max"]), abs(env_p["min"]))
    M_pila_Ed = 1.35 * abs(M_G_p + M_E_p) + 1.35 * M_lm1_p
    N_G_pila = 0.5 * ((g1 + g2) * L + 2.0 * rho * 9.81 * A_p * H)
    N_pila_Ed = 1.35 * N_G_pila + 1.35 * 0.5 * LM1_vert
    # reaccion HORIZONTAL real en la base (kx*dx): en un marco cerrado los empujes
    # de las dos pilas se equilibran por el dintel -> deslizamiento gobernado por la
    # parte NO equilibrada (FEM), no por el empuje total de una pila.
    bn = meta["base_nodes"][0]; kx = suelo["kx"]
    dx_G = est["G"]["desplazamientos"][bn][0]; dx_E = est["E"]["desplazamientos"][bn][0]
    H_base = abs(1.35 * kx * dx_G + 1.35 * kx * dx_E)

    esf = {"M_dintel_Ed": M_dintel_Ed, "V_dintel_Ed": V_dintel_Ed,
           "N_pila_Ed": N_pila_Ed, "M_pila_Ed": M_pila_Ed,
           "N_base": N_pila_Ed, "M_base": M_pila_Ed, "H_base": H_base}
    chk = ec2ec7_portico.comprobar(p, esf)

    resultado = {"nombre_tablero": nombre, "tipologia": "portico", "portico": p,
                 "permanentes": perm, "empuje": emp, "K_empuje": p["empuje"]["K"],
                 "f1_Hz": f1, "modal": {k: modal[k] for k in ("frecuencias_Hz",) if k in modal},
                 "esfuerzos": esf, "elementos_chk": chk["elementos_chk"], "checks": chk["checks"],
                 "ec7": chk["ec7"], "delta_2orden": chk["delta_2orden"],
                 "aprovechamiento_max": chk["aprovechamiento_max"], "veredicto_global": chk["veredicto"]}
    resultado["mapping_writeback"] = resultado_ifc_puente.construir_mapping(resultado)
    return resultado


if __name__ == "__main__":
    import os as _o, sys as _s
    _s.path.insert(0, _o.path.join(_here, "lectura"))
    import cli_ifc as _cli
    cfg = _cli.load_cfg(sys.argv[1])  # JSON de caso o .ifc (lector C1)
    r = ejecutar(cfg["portico"], cfg.get("nombre", "PORTICO_PUE03"))
    out = sys.argv[2] if len(sys.argv) > 2 else "resultado_portico.json"
    json.dump(r, open(out, "w"), indent=2, ensure_ascii=False)
    print("VEREDICTO GLOBAL:", r["veredicto_global"], "| aprov_max=%.3f" % r["aprovechamiento_max"],
          "| f1=%.2f Hz" % r["f1_Hz"], "| delta_2orden=%.3f" % r["delta_2orden"], "| K=%.3f" % r["K_empuje"])
