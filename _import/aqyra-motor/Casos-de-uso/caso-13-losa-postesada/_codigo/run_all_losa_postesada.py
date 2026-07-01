"""
Orquestador end-to-end del Caso 13 - LOSA PLANA POSTESADA (EC2 §5.10 + §6.4.4).

  IFC (losa + 9 pilares) -> modelo neutro (parser ortodoxo + Pset pretensado)
  -> balance de cargas 2D (banded X + distribuido Y) -> placa MITC4 con caso P
  -> perdidas (transferencia / servicio) -> verificacion (tensiones por franja,
     punzonamiento §6.4.4 con/sin efecto favorable, ELU flexion por fibras,
     fisuracion, flecha) -> JSON + diagramas.

Uso:
  python3 pretensado/run_all_losa_postesada.py <carpeta_proyecto> <ruta caso-13.ifc>
Memoria:
  python3 pretensado/generate_memoria_losa_postesada.py <carpeta_proyecto>
"""
import os
import sys
import json

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import solver_losa_postesada as solver
import balance_2d as b2
import verificacion_losa_postesada as verif

try:
    import ec2_pretensado as ec2
except Exception:
    ec2 = None
try:
    import plots_losa_postesada as plots
except Exception:
    plots = None


def run(proj, ifc):
    os.makedirs(proj, exist_ok=True)
    print("[1/6] IFC -> modelo neutro:", ifc)
    model = solver.parse(ifc)
    json.dump(model, open(os.path.join(proj, "modelo_neutro.json"), "w",
                          encoding="utf-8"), indent=2, ensure_ascii=False)
    pr = model["pretensado"]
    print("      pilares=%d  Pset pretensado: %s" % (
        len(model["pilares"]), pr.get("layout")))

    # --- magnitudes del pretensado por metro de ancho ---
    t = model["superficie"]["espesor"]
    Lx = Ly = 8.0
    drape = float(pr["drape_m"])
    rec_eje = float(pr["recubrimiento_eje_m"])
    P_x = float(pr["P_m_X_kN"]) * 1e3          # servicio Pm,inf (N/m)
    P_y = float(pr["P_m_Y_kN"]) * 1e3
    P0_m = float(pr["P0_m_kN"]) * 1e3          # transferencia (N/m), mismo en X/Y
    fpk = float(pr["fpk_MPa"]) * 1e6
    sigma_p0 = float(pr["sigma_p0_MPa"]) * 1e6
    sigma_pm_inf = float(pr["sigma_pm_inf_MPa"]) * 1e6

    # --- cargas (N/m2) ---
    mp = model["materiales"][model["superficie"]["material"]]
    g0 = t * 25000.0  # gamma_c=25 kN/m3 (EC2/EHE) -> 6.25 kN/m2
    g2 = 0.0; q = 0.0
    for cc in model["superficie"]["cargas"]:
        if cc["caso"] == "G":
            g2 += abs(cc["qz"])
        elif cc["caso"] == "Q":
            q += abs(cc["qz"])
    g_perm = g0 + g2
    print("      g0=%.2f g2=%.2f q=%.2f kN/m2 (permanente=%.2f)" % (
        g0 / 1e3, g2 / 1e3, q / 1e3, g_perm / 1e3))

    # --- balance de cargas 2D (equilibrar la permanente) ---
    print("[2/6] Balance de cargas 2D (banded X + distribuido Y)...")
    bal = b2.balance_2d(P_x, P_y, Lx, Ly, drape, drape, g_perm, t)
    # balance en transferencia (P0)
    w_p0 = b2.w_balance_direccion(P0_m, Lx, drape) + b2.w_balance_direccion(P0_m, Ly, drape)
    bal["w_p0_N_m2"] = w_p0
    print("      w_px=%.2f w_py=%.2f -> w_p=%.2f kN/m2 (perm=%.2f) residual=%.3f%%" % (
        bal["w_px_N_m2"] / 1e3, bal["w_py_N_m2"] / 1e3, bal["w_p_N_m2"] / 1e3,
        g_perm / 1e3, bal["residual_pct"]))
    print("      sigma_cp=%.3f MPa  P_para_equilibrar_perm=%.0f kN/m (cada direccion 1/2)" % (
        bal["sigma_cp_Pa"] / 1e6, bal["P_x_para_equilibrar_N_m"] / 1e3))

    # --- perdidas (resumen; el detalle 1D se reutiliza del caso 12) ---
    print("[3/6] Pretensado y perdidas...")
    sigma_pmax = 0.80 * fpk
    perd_pct = (sigma_pmax - sigma_pm_inf) / sigma_pmax * 100.0  # totales desde el gato
    perd_transfer_pct = (sigma_pmax - sigma_p0) / sigma_pmax * 100.0  # instantaneas
    # perdidas DIFERIDAS (transferencia -> infinito), el rango habitual 16-18%
    perd_diferidas_pct = (sigma_p0 - sigma_pm_inf) / sigma_p0 * 100.0
    relaj = None
    if ec2 is not None:
        try:
            relaj = ec2.relajacion(sigma_p0, fpk,
                                   float(pr.get("rho1000_pct", 2.5)),
                                   int(pr.get("relajacion_clase", 2))) / 1e6
        except Exception:
            relaj = None
    pretensado = {
        "Ap_cordon_mm2": float(pr["Ap_cordon_mm2"]),
        "fpk_MPa": fpk / 1e6, "fp01k_MPa": float(pr["fp01k_MPa"]),
        "Ep_GPa": float(pr["Ep_GPa"]), "drape_m": drape,
        "recubrimiento_eje_m": rec_eje,
        "Lx_m": Lx, "Ly_m": Ly,
        "P_m_X_N_m": P_x, "P_m_Y_N_m": P_y,
        "P0_m_X_N_m": P0_m, "P0_m_Y_N_m": P0_m,
        "sigma_p0_MPa": sigma_p0 / 1e6, "sigma_p0_frac_fpk": sigma_p0 / fpk,
        "sigma_pm_inf_MPa": sigma_pm_inf / 1e6, "sigma_pm_inf_frac_fpk": sigma_pm_inf / fpk,
        "sigma_pmax_MPa": sigma_pmax / 1e6,
        "perdidas_totales_pct": perd_pct, "perdidas_transferencia_pct": perd_transfer_pct,
        "perdidas_diferidas_pct": perd_diferidas_pct,
        "relajacion_MPa": relaj, "fck_t_Pa": 32e6,
        "w_p0_N_m2": w_p0,
        "n_cordones_m_X": float(pr.get("n_cordones_m_X", P_x / (float(pr["Ap_cordon_mm2"]) * 1e-6 * sigma_pm_inf))),
        "layout": pr.get("layout"),
    }
    print("      sigma_p0=%.0f MPa (%.3f fpk)  sigma_pm,inf=%.0f MPa (%.3f fpk)  perdidas tot=%.1f%%" % (
        sigma_p0 / 1e6, sigma_p0 / fpk, sigma_pm_inf / 1e6, sigma_pm_inf / fpk, perd_pct))

    # --- solver placa MITC4 con caso P ---
    print("[4/6] Solver placa MITC4 (apoyos puntuales) + caso P...")
    _, res = solver.solve(model, bal["w_p_N_m2"], w_p0_N_m2=w_p0)
    json.dump(res, open(os.path.join(proj, "resultados.json"), "w", encoding="utf-8"),
              indent=2, ensure_ascii=False)
    print("      equilibrio ELU (neto) error=%.2f%%" % res["equilibrio"]["error_pct"])

    # --- verificacion ---
    print("[5/6] Verificacion EC2 (tensiones/punzonamiento/ELU/fisuracion/flecha)...")
    ver = verif.verificar(model, res, bal, pretensado)

    out = {
        "caso": "13-losa-postesada",
        "modelo_resumen": {
            "t_m": t, "Lx_m": Lx, "Ly_m": Ly, "n_pilares": len(model["pilares"]),
            "material": model["superficie"]["material"],
            "fck_MPa": mp["fck"] / 1e6, "fctm_MPa": mp["fctm"] / 1e6,
            "g0_kN_m2": g0 / 1e3, "g2_kN_m2": g2 / 1e3, "q_kN_m2": q / 1e3,
            "permanente_kN_m2": g_perm / 1e3,
        },
        "pretensado": pretensado,
        "balance_2d": bal,
        "verificacion": ver,
        "criterios_aceptacion": {
            "w_p_kN_m2": bal["w_p_N_m2"] / 1e3,
            "residual_pct": bal["residual_pct"], "residual_ok": bal["residual_pct"] < 1.0,
            "P_m_X_kN": P_x / 1e3, "P_m_X_ok": abs(P_x / 1e3 - 212.0) < 10.0,
            "sigma_cp_MPa": bal["sigma_cp_Pa"] / 1e6,
            "sigma_cp_ok": abs(bal["sigma_cp_Pa"] / 1e6 - 0.85) < 0.05,
            "sigma_pm_inf_frac_fpk": sigma_pm_inf / fpk,
            "sigma_pm_inf_ok": abs(sigma_pm_inf / fpk - 0.60) < 0.02,
            "sigma_p0_frac_fpk": sigma_p0 / fpk,
            "sigma_p0_ok": abs(sigma_p0 / fpk - 0.72) < 0.02,
            "perdidas_totales_pct": perd_pct,
            "perdidas_diferidas_pct": perd_diferidas_pct,
            "perdidas_diferidas_ok": 16.0 <= perd_diferidas_pct <= 18.0,
            "aprov_max": ver["aprov_max"], "aprov_ok": ver["aprov_max"] <= 1.0,
            "veredicto": ver["veredicto"],
        },
        "avisos": [
            "Resultado de PREDIMENSIONADO. Debe ser revisado y FIRMADO por "
            "tecnico competente.",
            "[confirmar AN] EC2 §5.10/§6.4.4 (Anejo Nacional Espana): k1 del "
            "termino de pretensado en punzonamiento (0.10), coeficientes mu/k de "
            "rozamiento, penetracion de cuna, limites de tension del acero activo, "
            "retraccion y fluencia.",
            "Picos locales sobre pilares tratados como envolvente (percentil 97); "
            "valor de diseno en seccion critica (cara de pilar).",
            "Reparto de la carga a equilibrar 1/2 por direccion (banded X + "
            "distribuido Y); teoria de franjas col/middle 0.65/0.35.",
        ],
    }
    json.dump(out, open(os.path.join(proj, "verificacion_losa_postesada.json"), "w",
                        encoding="utf-8"), indent=2, ensure_ascii=False)

    # resumen de punzonamiento con/sin
    for pos, e in ver["punzonamiento"].items():
        cs = e["sin_pretensado"]; cc = e["con_pretensado"]
        print("      punz %-8s V_Ed=%.0f kN  SIN u=%.2f %s | CON u=%.2f %s (V_p=%.0f kN)" % (
            pos, e["V_Ed_sin_kN"], cs["u_vRdc"], "OK" if cs["ok"] else "NO",
            cc["u_vRdc"], "OK" if cc["ok"] else "NO", e["V_p_kN"]))
    print("      veredicto=%s  aprov_max=%.2f" % (ver["veredicto"], ver["aprov_max"]))

    # --- diagramas ---
    print("[6/6] Diagramas...")
    if plots is not None:
        try:
            for f in plots.generar(model, res, out, proj):
                print("      ", f)
        except Exception as ex:
            print("      AVISO: no se pudieron generar diagramas (%s)" % ex)
    print("OK. Memoria: python3 pretensado/generate_memoria_losa_postesada.py", proj)
    return out


if __name__ == "__main__":
    proj = sys.argv[1] if len(sys.argv) > 1 else "proyecto-losa-postesada"
    ifc = sys.argv[2] if len(sys.argv) > 2 else os.path.join(proj, "caso-13.ifc")
    run(proj, ifc)
