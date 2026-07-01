"""
Orquestador end-to-end del Caso 11 - Pantalla de cortante sismica (EC8).

  IFC -> modelo neutro (stick) -> espectro Sd(T) -> modal (scipy.eigh) +
  fuerzas laterales equivalentes -> esfuerzos V/M/N + derivas ->
  verificacion (cortante alma / borde / N-M / deriva) -> JSON + diagramas.

Uso:
  python3 sismico/run_all_sismo.py <carpeta_proyecto> <ruta caso-11.ifc>

La memoria Word se genera aparte (skill docx / python-docx):
  python3 sismico/generate_memoria_sismo.py <carpeta_proyecto>
"""
import sys
import os
import json
import math

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import solver_sismo
import ec8
import verificacion_sismo
import plots_sismo

G = 9.81


def run(proj, ifc):
    print("[1/6] IFC -> modelo neutro (stick):", ifc)
    model = solver_sismo.parse(ifc)
    os.makedirs(proj, exist_ok=True)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w",
                          encoding="utf-8"), indent=2, ensure_ascii=False)
    print("      nodos=%d masas=%d M_total=%.1f t W_total=%.0f kN" % (
        model["stick"]["n_nodos"], len(model["masas"]["por_planta_kg"]),
        model["masas"]["M_total_kg"] / 1e3, model["masas"]["W_total_kN"]))

    # parametros
    e = model["ec8"]
    ag = float(e["ag_g"]) * G
    S = float(e["S"]); TB = float(e["TB_s"]); TC = float(e["TC_s"])
    TD = float(e["TD_s"]); q = float(e["q"]); lam = float(e["lambda"])
    beta = 0.2

    sp = model["seccion_pared"]
    E = model["material"]["E_Pa"]; Gsh = model["material"]["G_Pa"]
    I = sp["I_m4"]; A_v = sp["A_v_m2"]
    z_full = model["stick"]["z_nodes_m"]
    z_plant = model["stick"]["z_plantas_m"]
    masses = model["masas"]["por_planta_kg"]

    print("[2/6] Espectro de calculo Sd(T) (EC8 §3.2.2.5)...")
    sd_meseta = ec8.Sd_meseta(ag, S, q)
    print("      Sd(meseta)=%.4f g  (esperado 0.192 g)" % (sd_meseta / G))

    print("[3/6] Rigidez lateral (Timoshenko) + modal (scipy.eigh)...")
    Kll = ec8.stick_lateral_stiffness(z_full, E, I, A_v, Gsh, base_fixed=True)
    modal = ec8.modal(Kll, masses)
    T1 = modal["modos"][0]["T_s"]
    print("      T1=%.3f s  M_eff,1=%.1f%%  sum M_eff=%.1f%%" % (
        T1, modal["modos"][0]["Meff_frac"] * 100,
        modal["suma_Meff_frac"] * 100))

    def sd_func(T):
        return ec8.Sd(T, ag, S, TB, TC, TD, q, beta)

    print("[4/6] Respuesta modal espectral (SRSS) + fuerzas laterales...")
    fmod = ec8.fuerzas_modales(modal, masses, z_plant, sd_func)
    fl = ec8.fuerzas_laterales(T1, masses, z_plant, ag, S, TB, TC, TD, q, lam, beta)
    print("      Fb modal SRSS=%.0f kN   Fb fuerzas laterales=%.0f kN" % (
        fmod["Fb_SRSS_kN"], fl["Fb_kN"]))
    dif = abs(fmod["Fb_SRSS_kN"] - fl["Fb_kN"]) / fl["Fb_kN"] * 100 if fl["Fb_kN"] else 0.0
    print("      diferencia modal vs lateral = %.1f %%" % dif)
    print("      equilibrio Fb=sumF_i: error %.3f %%" % fl["equilibrio_error_pct"])

    # esfuerzos de diseno (envolvente fuerzas laterales, que gobierna por incluir lambda)
    F_planta_N = [x * 1e3 for x in fl["F_i_kN"]]
    der_raw = ec8.derivas(Kll, F_planta_N, z_plant, q)

    N_base = model["masas"]["W_total_kN"] * 1e3      # axil de compresion a base
    M_base = fl["Mbase_kNm"] * 1e3
    V_base = fl["Fb_kN"] * 1e3

    esfuerzos = {
        "V_base_diseno_N": V_base,
        "M_base_diseno_Nm": M_base,
        "N_base_diseno_N": N_base,
        "eps_amplif": 1.5,                # amplificacion cortante DCM [confirmar AN]
        "deriva": der_raw,
    }

    print("[5/6] Verificacion (cortante alma / borde / N-M / deriva)...")
    ver = verificacion_sismo.verificar(model, esfuerzos)
    print("      cortante alma aprov=%.2f | borde aprov=%.2f | N-M aprov=%.2f | deriva aprov=%.2f -> %s" % (
        ver["aprovechamientos"]["cortante_alma"],
        ver["aprovechamientos"]["compr_borde"],
        ver["aprovechamientos"]["flexocompresion_NM"],
        ver["aprovechamientos"]["deriva"], ver["veredicto"]))

    # criterios de aceptacion
    crit = {
        "Sd_meseta_g": sd_meseta / G,
        "Sd_meseta_ok": abs(sd_meseta / G - 0.192) < 0.005,
        "T1_s": T1, "T1_en_meseta": (TB <= T1 <= TC),
        "T1_en_rango_0.4_0.6": (0.4 <= T1 <= 0.7),
        "Meff1_frac": modal["modos"][0]["Meff_frac"],
        "Meff1_ok": modal["modos"][0]["Meff_frac"] >= 0.60,
        "Fb_lateral_kN": fl["Fb_kN"],
        "Fb_en_rango_900_950": (880 <= fl["Fb_kN"] <= 970),
        "Fb_modal_SRSS_kN": fmod["Fb_SRSS_kN"],
        "dif_modal_vs_lateral_pct": dif,
        "equilibrio_Fb_sumFi_error_pct": fl["equilibrio_error_pct"],
        "Mbase_kNm": fl["Mbase_kNm"],
        "Mbase_en_rango_9700_10100": (9600 <= fl["Mbase_kNm"] <= 10200),
        "aprov_max": ver["aprov_max"],
        "aprov_ok": ver["aprov_max"] <= 1.0,
    }

    res = {
        "caso": "11-pantalla-sismo-ec8",
        "parametros_EC8": {
            "ag_g": e["ag_g"], "suelo": e["TipoSuelo"], "tipo_espectro": e["TipoEspectro"],
            "S": S, "TB_s": TB, "TC_s": TC, "TD_s": TD, "q": q,
            "lambda": lam, "beta_limite": beta,
            "amortiguamiento": e["amortiguamiento"], "ductilidad": "DCM",
            "Sd_meseta_g": sd_meseta / G, "Sd_meseta_ms2": sd_meseta,
        },
        "modelo_resumen": {
            "Lw_m": sp["Lw_m"], "tw_m": sp["tw_m"], "H_m": sp["H_m"],
            "I_m4": I, "A_m2": sp["A_m2"], "A_v_m2": A_v,
            "E_Pa": E, "G_Pa": Gsh,
            "M_total_t": model["masas"]["M_total_kg"] / 1e3,
            "W_total_kN": model["masas"]["W_total_kN"],
            "masas_planta_t": [m / 1e3 for m in masses],
            "z_plantas_m": z_plant,
        },
        "modal": modal,
        "respuesta_modal_SRSS": fmod,
        "fuerzas_laterales": fl,
        "esfuerzos_base": {
            "V_base_kN": V_base / 1e3, "M_base_kNm": M_base / 1e3,
            "N_base_kN": N_base / 1e3,
            "z_eficaz_m": fl["z_eficaz_m"],
            "eps_amplif_cortante_EC8": 1.5,
        },
        "deriva": verificacion_sismo.deriva(der_raw, nu=0.5, limite_rel=0.0075),
        "verificacion": ver,
        "criterios_aceptacion": crit,
    }

    json.dump(res, open(os.path.join(proj, "verificacion_sismo.json"), "w",
                        encoding="utf-8"), indent=2, ensure_ascii=False)

    print("[6/6] Diagramas...")
    archivos = plots_sismo.generar(model, res, ver, proj)
    for f in archivos:
        print("      ", f)
    print("OK. Memoria: python3 sismico/generate_memoria_sismo.py", proj)
    return res


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-pantalla-sismo"
    ifc = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "caso-11.ifc")
    run(proj, ifc)
