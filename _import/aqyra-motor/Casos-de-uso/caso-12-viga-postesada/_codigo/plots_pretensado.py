"""
Diagramas del Caso 12 - Viga postesada isostatica (EC2 §5.10).

Genera PNG (matplotlib, backend Agg):
  - trazado_tendon.png        : trazado parabolico del tendon y c.d.g.
  - cargas_equivalentes.png   : w_p (hacia arriba) vs carga permanente (hacia abajo)
  - leyes_MV.png              : leyes de momento y cortante (ELU)
  - tensiones_transferencia.png : tension por fibra en transferencia (P0+g0)
  - tensiones_servicio.png    : tension por fibra en servicio (qp y rara)
  - interaccion_ELU.png       : bloque de compresion / M_Rd vs M_Ed
  - perdidas_tendon.png       : tension del acero a lo largo del tendon (perdidas)

Uso: plots_pretensado.generar(model, res, carpeta)
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np


def _save(fig, path):
    fig.tight_layout()
    fig.savefig(path, dpi=130)
    plt.close(fig)
    return path


def generar(model, res, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    out = []
    s = model["seccion"]; pr = res["pretensado"]
    L = res["modelo_resumen"]["L_m"]
    e = pr["e_centro_m"]; e_ap = pr["e_apoyo_m"]
    cdg = s["cdg_m"]; h = s["h_m"]
    x = np.linspace(0, L, 101)

    # 1) trazado del tendon
    f_sag = e - e_ap
    e_x = e_ap + 4.0 * f_sag * (x / L) * (1.0 - x / L)
    y_tendon = cdg + e_x      # cota del tendon desde la fibra superior (hacia abajo +)
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(x, [0] * len(x), "k-", lw=1, label="fibra superior")
    ax.plot(x, [h] * len(x), "k-", lw=1, label="fibra inferior")
    ax.plot(x, [cdg] * len(x), "g--", lw=1, label="c.d.g.")
    ax.plot(x, y_tendon, "r-", lw=2, label="tendon (parabolico)")
    ax.invert_yaxis()
    ax.set_xlabel("x [m]"); ax.set_ylabel("cota desde fibra sup [m]")
    ax.set_title("Trazado del tendon  (e_centro=%.2f m, e_apoyo=%.2f m)" % (e, e_ap))
    ax.legend(loc="best", fontsize=8); ax.grid(alpha=0.3)
    out.append(_save(fig, os.path.join(carpeta, "trazado_tendon.png")))

    # 2) cargas equivalentes
    lb = res["load_balancing"]
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.axhline(0, color="k", lw=1)
    ax.bar(x, [-lb["w_permanente_kN_m"]] * len(x), width=L / 100,
           color="tab:blue", alpha=0.4, label="permanente g0+g2 (abajo)")
    ax.bar(x, [lb["w_p_kN_m"]] * len(x), width=L / 100,
           color="tab:red", alpha=0.4, label="w_p pretensado (arriba)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("carga [kN/m]")
    ax.set_title("Cargas equivalentes  w_p=%.2f kN/m  vs  perm=%.2f kN/m  (residual %.2f%%)"
                 % (lb["w_p_kN_m"], lb["w_permanente_kN_m"], lb["residual_pct"]))
    ax.legend(loc="best", fontsize=8); ax.grid(alpha=0.3)
    out.append(_save(fig, os.path.join(carpeta, "cargas_equivalentes.png")))

    # 3) leyes M/V (ELU)
    mr = res["modelo_resumen"]
    g0 = mr["g0_kN_m"]; g2 = mr["g2_kN_m"]; qq = mr["q_kN_m"]
    w_elu = 1.35 * (g0 + g2) + 1.5 * qq
    M = w_elu * x * (L - x) / 2.0
    V = w_elu * (L / 2.0 - x)
    fig, (a1, a2) = plt.subplots(2, 1, figsize=(8, 5), sharex=True)
    a1.plot(x, M, "b-"); a1.fill_between(x, M, alpha=0.2)
    a1.set_ylabel("M [kN*m]"); a1.set_title("Ley de momentos (ELU)  M_max=%.0f kN*m"
                                            % res["esfuerzos_diseno"]["M_ELU_kNm"])
    a1.grid(alpha=0.3)
    a2.plot(x, V, "r-"); a2.fill_between(x, V, alpha=0.2)
    a2.set_ylabel("V [kN]"); a2.set_xlabel("x [m]")
    a2.set_title("Ley de cortantes (ELU)  V_max=%.0f kN"
                 % res["esfuerzos_diseno"]["V_ELU_kN"])
    a2.grid(alpha=0.3)
    out.append(_save(fig, os.path.join(carpeta, "leyes_MV.png")))

    # 4) tensiones transferencia
    ten = res["verificacion"]["tensiones"]
    def fib_plot(ax, sup, inf, lim_c, lim_t, titulo):
        yy = [0, h]
        xx = [sup, inf]
        ax.plot(xx, yy, "o-", color="tab:purple")
        ax.axvline(0, color="k", lw=0.8)
        ax.axvline(lim_c, color="r", ls="--", lw=1, label="lim compresion")
        if lim_t is not None:
            ax.axvline(lim_t, color="g", ls="--", lw=1, label="fctm")
        ax.invert_yaxis()
        ax.set_xlabel("sigma [MPa] (compresion <0)")
        ax.set_ylabel("cota [m]"); ax.set_title(titulo, fontsize=9)
        ax.legend(fontsize=7); ax.grid(alpha=0.3)
    t = ten["transferencia"]
    fig, ax = plt.subplots(figsize=(5, 4))
    fib_plot(ax, t["sigma_sup_MPa"], t["sigma_inf_MPa"], t["lim_compresion_MPa"],
             t["lim_traccion_MPa"],
             "Transferencia (P0+g0)  sup=%.2f inf=%.2f MPa" % (
                 t["sigma_sup_MPa"], t["sigma_inf_MPa"]))
    out.append(_save(fig, os.path.join(carpeta, "tensiones_transferencia.png")))

    # 5) tensiones servicio (qp y rara)
    qp = ten["servicio_cuasiperm"]; ra = ten["servicio_rara"]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(9, 4))
    fib_plot(a1, qp["sigma_sup_MPa"], qp["sigma_inf_MPa"], qp["lim_compresion_MPa"],
             None, "Cuasipermanente  sup=%.2f inf=%.2f" % (
                 qp["sigma_sup_MPa"], qp["sigma_inf_MPa"]))
    fib_plot(a2, ra["sigma_sup_MPa"], ra["sigma_inf_MPa"], ra["lim_compresion_MPa"],
             ra["lim_traccion_fctm_MPa"], "Rara  sup=%.2f inf=%.2f" % (
                 ra["sigma_sup_MPa"], ra["sigma_inf_MPa"]))
    out.append(_save(fig, os.path.join(carpeta, "tensiones_servicio.png")))

    # 6) interaccion / ELU
    elu = res["verificacion"]["ELU_flexion"]
    fig, ax = plt.subplots(figsize=(6, 4))
    ax.bar(["M_Ed", "M_Rd"], [elu["M_Ed_kNm"], elu["M_Rd_kNm"]],
           color=["tab:orange", "tab:green"])
    ax.set_ylabel("M [kN*m]")
    ax.set_title("ELU flexion (fibras)  M_Ed=%.0f / M_Rd=%.0f kN*m (aprov %.2f)  x/d=%.2f"
                 % (elu["M_Ed_kNm"], elu["M_Rd_kNm"], elu["u"], elu["x_d_ratio"]))
    ax.grid(alpha=0.3, axis="y")
    out.append(_save(fig, os.path.join(carpeta, "interaccion_ELU.png")))

    # 7) perdidas a lo largo del tendon
    perf = res["perdidas_instantaneas"]["perfil_rozamiento"]
    xs = [p["x_m"] for p in perf]
    sig = [p["sigma_MPa"] for p in perf]
    fig, ax = plt.subplots(figsize=(8, 3))
    ax.plot(xs, sig, "b-o", ms=3, label="sigma_p tras rozamiento")
    ax.axhline(pr["sigma_p0_MPa"], color="g", ls="--", label="sigma_p0 (transferencia)")
    ax.axhline(pr["sigma_pinf_MPa"], color="r", ls="--", label="sigma_p,inf (servicio)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("sigma_p [MPa]")
    ax.set_title("Tension del acero activo a lo largo del tendon (perdidas)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    out.append(_save(fig, os.path.join(carpeta, "perdidas_tendon.png")))

    return out
