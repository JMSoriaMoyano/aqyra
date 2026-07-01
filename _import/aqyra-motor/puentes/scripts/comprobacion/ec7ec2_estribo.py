"""
Comprobacion EC7 + EC2 de un ESTRIBO de puente (PT 7.3).

Delega en `verificacion_muro.verificar` (motor-calculo, puro sin PyNite) toda la
verificacion del muro: EC7 (vuelco/deslizamiento/hundimiento) y EC2
(alzado/puntera/talon). La unica EXTENSION nueva del estribo respecto a un muro de
contension es la HORIZONTAL DE FRENADO del tablero en cabeza, que el muro estandar
no contempla en la estabilidad global: se inyecta como una componente de empuje
horizontal (caso Q) con brazo H sobre la base, de modo que `verificar` la incluye
automaticamente en vuelco/deslizamiento/hundimiento. El alzado (fuste) se resuelve
con motor-fem (estribo.solve_fuste_fem) e incluye ya esa horizontal.

(La reaccion VERTICAL del tablero entra por la coronacion -> pesos() -> ya la usa
`verificar`.) SI (N, m, Pa). Predimensionado; revisar y firmar por tecnico (ICCP).
"""
from __future__ import annotations
import verificacion_muro as vm


def comprobar(model, empujes_dict, pesos_items, alzado, H_frenado_N=0.0):
    """model: dict del muro/estribo. empujes_dict: salida de estribo.empujes().
    pesos_items: lista de estribo.pesos()[0]. alzado: {ELU,ELS_car,ELS_cp:{M_base,V_base}}.
    H_frenado_N: horizontal de frenado del tablero (cabeza). Devuelve la verificacion."""
    gc = model["materiales"][model["muro"]["material"]]["rho"] * 9.81
    emp = {k: v for k, v in empujes_dict.items()}
    emp["componentes"] = list(empujes_dict["componentes"])
    # --- EXTENSION ESTRIBO: frenado del tablero como empuje horizontal (Q), brazo H ---
    if H_frenado_N:
        emp["componentes"].append({"nombre": "frenado_tablero", "caso": "Q",
                                   "Eh_kN": H_frenado_N / 1e3, "Ev_kN": 0.0,
                                   "z_kN_m": emp["H"], "x_Ev_m": model["muro"]["B"]})
    info = {"Hm": model["muro"]["Hm"], "t_alz": model["muro"]["t_alz"], "n": 0,
            "B": model["muro"]["B"], "e_z": model["muro"]["e_z"],
            "puntera": model["muro"]["puntera"], "talon": model["muro"]["talon"],
            "material": model["muro"]["material"], "gamma_hormigon_kN_m3": gc / 1e3,
            "H": emp["H"], "Ka": emp["Ka"], "Kp": emp["Kp"], "metodo": emp["metodo"]}
    results = {"info": info, "empujes": emp, "pesos": pesos_items, "alzado": alzado}
    out = vm.verificar(model, results)
    # resumen de aprovechamientos
    aprovs = {"vuelco": out["vuelco"]["u"], "deslizamiento": out["deslizamiento"]["u"],
              "hundimiento": out["hundimiento"]["u"],
              "alzado_cortante": out["alzado"]["cortante"]["u"],
              "puntera_cortante": out["puntera"]["cortante"]["u"],
              "talon_cortante": out["talon"]["cortante"]["u"]}
    out["aprovechamiento_max"] = max(aprovs.values())
    out["aprovechamientos"] = aprovs
    out["veredicto_global"] = "CUMPLE" if out["veredicto"] == "CUMPLE" else "NO CUMPLE"
    return out
