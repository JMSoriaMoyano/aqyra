"""Diagramas del caso 14 (viga postesada continua hiperestatica)."""
import os, json
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

C_PRIM = "#1f6fb2"; C_TOT = "#c0392b"; C_SEC = "#27ae60"; C_EXT = "#7f4fa0"
C_BAL = "#e08a1e"


def _supports(ax, sup, y=0.0):
    for sx in sup:
        ax.plot([sx], [y], marker="^", ms=11, color="#444", zorder=5)


def generar(arrays, veri, outdir):
    a = arrays
    x = np.array(a["x"]); sup = veri["geometria"]["apoyos_x_m"]
    h = veri["seccion"]["h_m"]; cdg = veri["seccion"]["cdg_m"]
    paths = []

    # 1) alzado + trazado del tendon
    fig, ax = plt.subplots(figsize=(11, 3.2))
    e = np.array(a["e_tendon"])
    ax.fill_between([0, sup[-1]], -cdg, h - cdg, color="#f0f0f0", zorder=0)
    ax.axhline(0, color="#999", lw=0.8, ls="--", label="c.d.g.")
    ax.plot(x, e, color=C_PRIM, lw=2.2, label="tendon e(x) (+abajo)")
    ax.plot(x, np.array(a["linea_presiones"]), color=C_TOT, lw=1.8, ls="--",
            label="linea de presiones e_p=M_p,tot/P")
    ax.invert_yaxis()
    _supports(ax, sup, y=cdg)
    for sx, lbl in [(sup[1], "e=%.2f" % veri["momentos_pretensado"]["apoyo_central"]["e_tendon_m"]),
                    (a["x_span"], "e=%.2f" % veri["momentos_pretensado"]["centro_vano"]["e_tendon_m"])]:
        ei = float(np.interp(sx, x, e))
        ax.annotate(lbl, (sx, ei), textcoords="offset points", xytext=(0, -14),
                    ha="center", fontsize=8, color=C_PRIM)
    ax.set_title("Caso 14 - Alzado y trazado del tendon (parabolico por vano)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("e (m, +abajo)")
    ax.legend(fontsize=8, loc="upper center", ncol=3); ax.grid(alpha=0.3)
    p = os.path.join(outdir, "alzado_tendon.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 2) cargas equivalentes
    fig, ax = plt.subplots(figsize=(11, 3.0))
    wp = veri["pretensado"]["w_p_kN_m"]
    gperm = (veri["momentos_pretensado"] and (16.25 + 5.0))
    ax.fill_between(x, 0, wp, color=C_BAL, alpha=0.5, step=None,
                    label="w_p=%.1f kN/m (hacia ARRIBA, pretensado)" % wp)
    ax.axhline(21.25, color="#444", lw=1.5, ls="--", label="permanente g0+g2=21.25 kN/m (abajo)")
    ax.annotate("fuerza de desvio (apoyo central, reaccionada)", (sup[1], wp),
                textcoords="offset points", xytext=(0, 8), ha="center", fontsize=8, color=C_TOT)
    ax.plot([sup[1]], [wp], marker="v", ms=12, color=C_TOT)
    _supports(ax, sup, y=0)
    ax.set_title("Caso 14 - Cargas equivalentes del pretensado (balance de cargas)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("w (kN/m)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    p = os.path.join(outdir, "cargas_equivalentes.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 3) M1 / M_p_tot / M_sec superpuestas
    fig, ax = plt.subplots(figsize=(11, 4.0))
    ax.plot(x, a["M1"], color=C_PRIM, lw=2, label="M1 = -P*e (primario)")
    ax.plot(x, a["M_p_tot"], color=C_TOT, lw=2, label="M_p,tot (cargas equiv., continua)")
    ax.plot(x, a["M_sec"], color=C_SEC, lw=2.4, label="M_sec = M_p,tot - M1 (secundario)")
    ax.axhline(0, color="#999", lw=0.8)
    _supports(ax, sup, y=0)
    ax.annotate("M_sec lineal, nula en extremos,\nmax en apoyo central = %.0f kNm"
                % veri["momentos_pretensado"]["apoyo_central"]["M_sec_kNm"],
                (sup[1], veri["momentos_pretensado"]["apoyo_central"]["M_sec_kNm"]),
                textcoords="offset points", xytext=(10, 20), fontsize=8, color=C_SEC)
    ax.set_title("Caso 14 - Momentos del pretensado: primario / total / SECUNDARIO")
    ax.set_xlabel("x (m)"); ax.set_ylabel("M (kN.m, sagging +)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    p = os.path.join(outdir, "momentos_M1_Mptot_Msec.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 4) linea de presiones vs tendon
    fig, ax = plt.subplots(figsize=(11, 3.2))
    ax.plot(x, np.array(a["e_tendon"]), color=C_PRIM, lw=2, label="tendon e(x)")
    ax.plot(x, np.array(a["linea_presiones"]), color=C_TOT, lw=2, ls="--",
            label="linea de presiones e_p = e + M_sec/P")
    ax.fill_between(x, np.array(a["e_tendon"]), np.array(a["linea_presiones"]),
                    color=C_SEC, alpha=0.25, label="desviacion = M_sec/P")
    ax.axhline(0, color="#999", lw=0.8, ls="--")
    ax.invert_yaxis(); _supports(ax, sup, y=0)
    ax.set_title("Caso 14 - Linea de presiones vs tendon (concordancia)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("posicion (m, +abajo)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    p = os.path.join(outdir, "linea_presiones.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 5) leyes M servicio / ELU
    fig, axs = plt.subplots(2, 1, figsize=(11, 6.2), sharex=True)
    axs[0].plot(x, a["M_perm"], label="M perm", color="#555")
    axs[0].plot(x, a["M_qp"], label="M cuasiperm", color="#2a8")
    axs[0].plot(x, a["M_rara"], label="M rara", color=C_PRIM)
    axs[0].plot(x, a["M_ELU"], label="M ELU (externo)", color=C_TOT, lw=2)
    axs[0].axhline(0, color="#999", lw=0.8); _supports(axs[0], sup, 0)
    axs[0].set_ylabel("M (kN.m)"); axs[0].legend(fontsize=8, ncol=4); axs[0].grid(alpha=0.3)
    axs[0].set_title("Caso 14 - Leyes de momentos (servicio y ELU externo)")
    axs[1].plot(x, a["V_perm"], color="#555", label="V perm")
    axs[1].axhline(0, color="#999", lw=0.8); _supports(axs[1], sup, 0)
    axs[1].set_ylabel("V (kN)"); axs[1].set_xlabel("x (m)"); axs[1].legend(fontsize=8); axs[1].grid(alpha=0.3)
    p = os.path.join(outdir, "leyes_MV.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 6) interaccion / ELU por seccion critica (barras M_Ed vs M_Rd)
    fig, ax = plt.subplots(figsize=(7.5, 4.2))
    labels = ["Apoyo central\n(hogging)", "Centro vano\n(sagging)"]
    MEd = [abs(veri["ELU_apoyo_central"]["M_Ed_con_secundario_kNm"]),
           abs(veri["ELU_centro_vano"]["M_Ed_con_secundario_kNm"])]
    MExt = [abs(veri["ELU_apoyo_central"]["M_ELU_ext_kNm"]),
            abs(veri["ELU_centro_vano"]["M_ELU_ext_kNm"])]
    MRd = [veri["ELU_apoyo_central"]["M_Rd_kNm"], veri["ELU_centro_vano"]["M_Rd_kNm"]]
    xpos = np.arange(2); w = 0.26
    ax.bar(xpos - w, MExt, w, label="M_Ed externo", color="#bbb")
    ax.bar(xpos, MEd, w, label="M_Ed con secundario (gamma_P=1.0)", color=C_TOT)
    ax.bar(xpos + w, MRd, w, label="M_Rd (fibras)", color=C_PRIM)
    for i in range(2):
        ax.annotate("u=%.2f" % [veri["ELU_apoyo_central"]["u"], veri["ELU_centro_vano"]["u"]][i],
                    (xpos[i], MRd[i]), textcoords="offset points", xytext=(0, 4), ha="center", fontsize=9)
    ax.set_xticks(xpos); ax.set_xticklabels(labels)
    ax.set_ylabel("|M| (kN.m)"); ax.set_title("Caso 14 - ELU de flexion por seccion critica")
    ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
    p = os.path.join(outdir, "interaccion_ELU.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 7) tensiones por fibra
    fig, axs = plt.subplots(1, 2, figsize=(11, 4.0))
    for ax, key, ttl in [(axs[0], "tensiones_apoyo_central", "Apoyo central"),
                         (axs[1], "tensiones_centro_vano", "Centro de vano")]:
        t = veri[key]
        ests = ["transferencia", "servicio_cuasiperm", "servicio_rara"]
        sup_s = [t[e]["sigma_sup_MPa"] for e in ests]
        inf_s = [t[e]["sigma_inf_MPa"] for e in ests]
        xx = np.arange(3); w = 0.35
        ax.bar(xx - w/2, sup_s, w, label="fibra superior", color=C_PRIM)
        ax.bar(xx + w/2, inf_s, w, label="fibra inferior", color=C_BAL)
        ax.axhline(0, color="#999", lw=0.8)
        ax.axhline(veri["material"]["fctm_Pa"]/1e6, color=C_TOT, ls="--", lw=1, label="fctm")
        ax.set_xticks(xx); ax.set_xticklabels(["transf.", "cuasip.", "rara"], fontsize=8)
        ax.set_title("%s" % ttl, fontsize=10); ax.set_ylabel("sigma (MPa, +tracc)")
        ax.legend(fontsize=7); ax.grid(alpha=0.3, axis="y")
    fig.suptitle("Caso 14 - Tensiones por fibra (con momento secundario)")
    p = os.path.join(outdir, "tensiones_fibra.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)

    # 8) flecha
    fig, ax = plt.subplots(figsize=(11, 3.0))
    ax.plot(x, a["flecha_residual"], color=C_PRIM, lw=2,
            label="flecha residual (perm+psi2 q - balance)")
    ax.axhline(0, color="#999", lw=0.8); _supports(ax, sup, 0)
    ax.set_title("Caso 14 - Flecha bajo carga residual neta (balance del pretensado)")
    ax.set_xlabel("x (m)"); ax.set_ylabel("flecha (mm)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3)
    p = os.path.join(outdir, "flecha.png"); fig.tight_layout(); fig.savefig(p, dpi=130); plt.close(fig); paths.append(p)
    return paths


if __name__ == "__main__":
    import sys
    outdir = sys.argv[1] if len(sys.argv) > 1 else "."
    arrays = json.load(open(os.path.join(outdir, "_arrays_plot.json")))
    veri = json.load(open(os.path.join(outdir, "verificacion_pretensado_continua.json")))
    pp = generar(arrays, veri, outdir)
    print("Diagramas:", len(pp))
    for p in pp: print("  ", os.path.basename(p))
