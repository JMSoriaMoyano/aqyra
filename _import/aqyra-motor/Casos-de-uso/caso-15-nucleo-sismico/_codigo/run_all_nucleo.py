"""
Orquestador end-to-end del Caso 15 - NUCLEO DE PANTALLAS ACOPLADAS (EC8, PT 1.5).

  IFC -> modelo neutro (3 GdL/planta) -> ensamblaje diafragma rigido + CR/CM/e0
   -> modal (response spectrum, contraste) + fuerzas laterales por direccion
   (equilibrio) -> reparto de cortante por pantalla (directo + torsion natural +
   torsion accidental §4.3.2) -> par de muros acoplados (dinteles, DoC) ->
   verificacion EC8 (cortante alma / borde / N-M por pantalla + viga de
   acoplamiento DCM + deriva) -> JSON + diagramas.

Uso:
  python3 sismico/run_all_nucleo.py <carpeta_proyecto> <ruta caso-15.ifc>
"""
import sys, os, json, math
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, HERE)
import solver_nucleo, ec8, nucleo, verificacion_nucleo
import numpy as np
G = 9.81


def run(proj, ifc):
    print("[1/6] IFC -> modelo neutro (nucleo, 3 GdL/planta):", ifc)
    model = solver_nucleo.parse(ifc)
    os.makedirs(proj, exist_ok=True)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    return analizar(model, proj, do_plots=True)


def analizar(model, proj=None, do_plots=True, out_json="verificacion_nucleo.json"):
    e = model["ec8"]; ag = float(e["ag_g"]) * G; S = float(e["S"]); TB = float(e["TB_s"])
    TC = float(e["TC_s"]); TD = float(e["TD_s"]); q = float(e["q"]); lam = float(e["lambda"]); beta = 0.2
    E = model["material"]["E_Pa"]; Gsh = model["material"]["G_Pa"]
    z_full = model["diafragma"]["z_nodes_m"]; z_plant = model["diafragma"]["z_plantas_m"]
    masses = model["masas"]["por_planta_kg"]; n = len(masses)
    CMx = model["diafragma"]["CM_x_m"]; CMy = model["diafragma"]["CM_y_m"]
    Lx = model["diafragma"]["Edificio_Lx_m"]; Ly = model["diafragma"]["Edificio_Ly_m"]

    print("[2/6] Ensamblaje diafragma rigido + CR/CM + modal...")
    elems, coup = nucleo.build_elements(model["pantallas"], model["dinteles"], z_full, E, Gsh)
    K, M, info = nucleo.assemble(elems, z_full, masses, CMx, CMy, Lx, Ly)
    md = nucleo.modal(K, M, n)
    T1x = nucleo.T1_dir(md, "X"); T1y = nucleo.T1_dir(md, "Y")
    sd_meseta = ec8.Sd_meseta(ag, S, q)
    print("      CR=(%.2f,%.2f) CM=(%.2f,%.2f) e0x=%.2f e0y=%.2f | Sd_meseta=%.4f g" % (
        info["CRx"], info["CRy"], CMx, CMy, info["e0x_m"], info["e0y_m"], sd_meseta / G))
    print("      T1x=%.3f s  T1y=%.3f s  sumMeffX=%.2f sumMeffY=%.2f" % (
        T1x, T1y, md["sumMeffX"], md["sumMeffY"]))

    def sd(T):
        return ec8.Sd(T, ag, S, TB, TC, TD, q, beta)

    print("[3/6] Modal response spectrum (contraste) + fuerzas laterales (equilibrio)...")
    # contraste modal: base shear SRSS por direccion (Fb_i = Meff_i*Sd(T_i))
    FbX2 = FbY2 = 0.0
    for mm in md["modos"]:
        MeffX = mm["MeffX_frac"] * model["masas"]["M_total_kg"]
        MeffY = mm["MeffY_frac"] * model["masas"]["M_total_kg"]
        FbX2 += (MeffX * sd(mm["T_s"])) ** 2
        FbY2 += (MeffY * sd(mm["T_s"])) ** 2
    FbX_modal = math.sqrt(FbX2) / 1e3; FbY_modal = math.sqrt(FbY2) / 1e3
    flx = ec8.fuerzas_laterales(T1x, masses, z_plant, ag, S, TB, TC, TD, q, lam, beta)
    fly = ec8.fuerzas_laterales(T1y, masses, z_plant, ag, S, TB, TC, TD, q, lam, beta)
    print("      Fb lateral X=%.0f Y=%.0f kN | Fb modal SRSS X=%.0f Y=%.0f kN" % (
        flx["Fb_kN"], fly["Fb_kN"], FbX_modal, FbY_modal))
    Fx = [v * 1e3 for v in flx["F_i_kN"]]; Fy = [v * 1e3 for v in fly["F_i_kN"]]
    eaccx = 0.05 * Lx; eaccy = 0.05 * Ly
    dx = nucleo.distribuir(elems, K, n, info, Fx, "X", eaccx)
    dy = nucleo.distribuir(elems, K, n, info, Fy, "Y", eaccy)
    derX = nucleo.derivas_globales(dx["U"], z_plant, q, Ly / 2.0, "X")
    derY = nucleo.derivas_globales(dy["U"], z_plant, q, Lx / 2.0, "Y")

    print("[4/6] Par de muros acoplados (dinteles, DoC)...")
    piers = [p for p in model["pantallas"] if p.get("par_acoplado") == "ALMA"]
    ac = nucleo.acoplados(piers, model["dinteles"], z_full, Fy, E, Gsh) if len(piers) >= 2 else None
    if ac:
        print("      ell=%.2f m  DoC=%.2f  V_lintel_max=%.0f kN  N_acopl_base=%.0f kN  M_walls=%.0f kNm" % (
            ac["ell_m"], ac["DoC"], ac["V_lintel_max_kN"], ac["N_acopl_base_kN"], ac["M_walls_flexion_kNm"]))

    # ---- esfuerzos de diseno por pantalla (envolvente de torsion accidental) ----
    A_tot = sum(p["A_m2"] for p in model["pantallas"])
    W_tot = model["masas"]["W_total_kN"] * 1e3
    by_name = {p["nombre"]: p for p in model["pantallas"]}
    Vbyname = {}
    for d in (dx, dy):
        for w in d["por_pantalla"]:
            Vbyname.setdefault(w["nombre"], {})[d["direccion"]] = w
    esf = []
    # flanges (resisten X): envolvente de su cortante en X (directo) y en Y (torsion)
    for p in model["pantallas"]:
        if p["resiste"] == "X":
            wx = Vbyname["ALA_F1" if False else p["nombre"]]
            VX = wx.get("X", {}).get("V_envolvente_kN", 0.0)
            VY = wx.get("Y", {}).get("V_envolvente_kN", 0.0)
            V_Ed = max(abs(VX), abs(VY)) * 1e3
            fX = wx.get("X", {}).get("f_planta_kN", [0] * n)
            M_Ed = abs(sum(fX[j] * z_plant[j] for j in range(n))) * 1e3
            N_Ed = p["A_m2"] / A_tot * W_tot
            esf.append({"pan": p, "V_Ed_N": V_Ed, "M_Ed_Nm": M_Ed, "N_Ed_N": N_Ed})
    # machones acoplados (resisten Y): reparto del par + axil de acoplamiento
    if ac and piers:
        w_pair = Vbyname.get("NUCLEO_ALMA_acoplada", {}).get("Y", {})
        V_pair = w_pair.get("V_envolvente_kN", fly["Fb_kN"]) * 1e3
        V_pier = V_pair / 2.0
        M_pier = ac["M_walls_flexion_kNm"] / 2.0 * 1e3
        N_grav = piers[0]["A_m2"] / A_tot * W_tot
        N_ac = ac["N_acopl_base_kN"] * 1e3
        # machon comprimido (barlovento->sotavento) y traccionado
        esf.append({"pan": dict(piers[0], nombre=piers[0]["nombre"] + " (compr.)"),
                    "V_Ed_N": V_pier, "M_Ed_Nm": M_pier, "N_Ed_N": N_grav + N_ac,
                    "N_nm_N": N_grav + N_ac})
        # machon a barlovento: axil REAL (gravedad - acoplamiento, puede ser traccion neta)
        # para la armadura de borde; N-M con el gravitatorio (lado seguro)
        esf.append({"pan": dict(piers[1], nombre=piers[1]["nombre"] + " (tracc.)"),
                    "V_Ed_N": V_pier, "M_Ed_Nm": M_pier, "N_Ed_N": N_grav - N_ac,
                    "N_nm_N": N_grav})

    print("[5/6] Verificacion EC8 (pantallas + viga de acoplamiento + deriva)...")
    # deriva gobernante = la mayor de X/Y
    der_gov = derY if max(derY["deriva_rel"]) >= max(derX["deriva_rel"]) else derX
    ver = verificacion_nucleo.verificar(model, esf, ac, der_gov, eps_amplif=1.5)
    for p in ver["pantallas"]:
        print("      %-18s V=%.0f M=%.0f N=%.0f -> aprov_max=%.2f (%s)" % (
            p["nombre"], p["V_Ed_kN"], p["M_Ed_kNm"], p["N_Ed_kN"], p["aprov_max"], p["veredicto"]))
    if ver["viga_acoplamiento"]:
        va = ver["viga_acoplamiento"]
        print("      Dintel: l/h=%.1f regimen=%s aprov_biela=%.2f | %s" % (
            va["l_n_sobre_h"], va["regimen"], va["aprov_biela"], va["armado"]))
    print("      Deriva aprov=%.2f -> VEREDICTO %s (aprov_max=%.2f)" % (
        ver["deriva"]["aprov_max"], ver["veredicto"], ver["aprov_max"]))

    crit = {
        "Sd_meseta_g": sd_meseta / G, "Sd_meseta_ok": abs(sd_meseta / G - 0.20 * 1.15 * 2.5 / q) < 1e-3,
        "T1x_s": T1x, "T1y_s": T1y, "T1_en_meseta": (TB <= T1x <= TC and TB <= T1y <= TC),
        "sumMeffX": md["sumMeffX"], "sumMeffY": md["sumMeffY"],
        "Meff_ok": md["sumMeffX"] > 0.9 and md["sumMeffY"] > 0.9,
        "e0x_m": info["e0x_m"], "e0y_m": info["e0y_m"],
        "Fb_lateral_X_kN": flx["Fb_kN"], "Fb_lateral_Y_kN": fly["Fb_kN"],
        "Fb_modal_SRSS_X_kN": FbX_modal, "Fb_modal_SRSS_Y_kN": FbY_modal,
        "equilibrio_X_error_pct": flx["equilibrio_error_pct"],
        "equilibrio_Y_error_pct": fly["equilibrio_error_pct"],
        "reparto_X_suma_err_pct": abs(sum(w["V_directo_torsion_kN"] for w in dx["por_pantalla"] if w["resiste"] == "X") - dx["V_basal_kN"]) / dx["V_basal_kN"] * 100,
        "reparto_Y_suma_err_pct": abs(sum(w["V_directo_torsion_kN"] for w in dy["por_pantalla"] if w["resiste"] == "Y") - dy["V_basal_kN"]) / dy["V_basal_kN"] * 100,
        "DoC": ac["DoC"] if ac else None,
        "deriva_max_rel_pct": max(max(derX["deriva_rel"]), max(derY["deriva_rel"])) * 100,
        "aprov_max": ver["aprov_max"], "aprov_ok": ver["aprov_max"] <= 1.0,
    }
    res = {
        "caso": "15-nucleo-sismico-ec8",
        "parametros_EC8": {"ag_g": e["ag_g"], "suelo": e["TipoSuelo"], "tipo_espectro": e["TipoEspectro"],
            "S": S, "TB_s": TB, "TC_s": TC, "TD_s": TD, "q": q, "lambda": lam, "beta_limite": beta,
            "amortiguamiento": e["amortiguamiento"], "ductilidad": "DCM (muros acoplados)",
            "Sd_meseta_g": sd_meseta / G, "Sd_meseta_ms2": sd_meseta},
        "diafragma": {"CRx": info["CRx"], "CRy": info["CRy"], "CMx": CMx, "CMy": CMy,
            "e0x_m": info["e0x_m"], "e0y_m": info["e0y_m"], "e_acc_x_m": eaccx, "e_acc_y_m": eaccy,
            "Edificio_Lx_m": Lx, "Edificio_Ly_m": Ly, "M_total_t": model["masas"]["M_total_kg"] / 1e3,
            "W_total_kN": model["masas"]["W_total_kN"]},
        "modal": md, "fuerzas_laterales_X": flx, "fuerzas_laterales_Y": fly,
        "Fb_modal_SRSS_X_kN": FbX_modal, "Fb_modal_SRSS_Y_kN": FbY_modal,
        "reparto_X": {k: dx[k] for k in ("direccion", "V_basal_kN", "e_acc_m", "por_pantalla")},
        "reparto_Y": {k: dy[k] for k in ("direccion", "V_basal_kN", "e_acc_m", "por_pantalla")},
        "acoplamiento": ac, "deriva_X": derX, "deriva_Y": derY,
        "verificacion": ver, "criterios_aceptacion": crit,
    }
    if proj:
        json.dump(res, open(os.path.join(proj, out_json), "w", encoding="utf-8"),
                  indent=2, ensure_ascii=False)

    if proj and do_plots:
        print("[6/6] Diagramas...")
        try:
            import plots_nucleo
            for f in plots_nucleo.generar(model, res, proj):
                print("      ", f)
        except Exception as ex:
            print("      (plots) aviso:", ex)
        print("OK. Memoria: python3 sismico/generate_memoria_nucleo.py", proj)
    return res


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-nucleo-sismo"
    ifc = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "caso-15.ifc")
    run(proj, ifc)
