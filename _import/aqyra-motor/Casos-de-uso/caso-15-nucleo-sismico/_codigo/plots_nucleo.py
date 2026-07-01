"""
Diagramas (PNG) del Caso 15 - Nucleo de pantallas acopladas (EC8).
  - espectro Sd(T) con T1x, T1y
  - planta del nucleo con CR, CM y excentricidad e0
  - reparto de cortante por pantalla (directo+torsion y envolvente con accidental)
  - vigas de acoplamiento: cortante del dintel por planta + axil de acoplamiento
  - deriva entre plantas (borde, X e Y)
  - diagrama N-M del machon comprimido con el punto de diseno
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import ec8

G = 9.81


def generar(model, res, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    archivos = []
    e = model["ec8"]; ag = float(e["ag_g"]) * G
    S = float(e["S"]); TB = float(e["TB_s"]); TC = float(e["TC_s"]); TD = float(e["TD_s"]); q = float(e["q"])
    z = model["diafragma"]["z_plantas_m"]; z_full = model["diafragma"]["z_nodes_m"]
    dia = res["diafragma"]

    # 1) espectro con T1x, T1y
    Ts, Ss = ec8.espectro_curva(ag, S, TB, TC, TD, q)
    T1x = res["criterios_aceptacion"]["T1x_s"]; T1y = res["criterios_aceptacion"]["T1y_s"]
    fig, ax = plt.subplots(figsize=(7, 4.3))
    ax.plot(Ts, Ss / G, "b-", lw=2, label="Sd(T)/g  (q=%.1f)" % q)
    ax.axhline(ec8.Sd_meseta(ag, S, q) / G, color="gray", ls="--", lw=1, label="meseta=%.3f g" % (ec8.Sd_meseta(ag, S, q) / G))
    for T1, c, lb in [(T1x, "ro", "T1x=%.3f s" % T1x), (T1y, "g^", "T1y=%.3f s" % T1y)]:
        ax.plot([T1], [ec8.Sd(T1, ag, S, TB, TC, TD, q) / G], c, ms=9, label=lb)
    for tt in (TB, TC, TD):
        ax.axvline(tt, color="0.85", ls=":")
    ax.set_xlabel("T [s]"); ax.set_ylabel("Sd / g"); ax.set_title("Espectro de calculo EC8 (suelo C, tipo 1)")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    f = os.path.join(carpeta, "espectro_Sd.png"); fig.tight_layout(); fig.savefig(f, dpi=130); plt.close(fig); archivos.append(f)

    # 2) planta del nucleo: pantallas + CR + CM + e0
    fig, ax = plt.subplots(figsize=(6, 6))
    for p in model["pantallas"]:
        tw = p["tw_m"]; Lw = p["Lw_m"]
        if p["resiste"] == "Y":      # plano YZ: linea en x=xc, de yc-Lw/2 a yc+Lw/2
            x0 = p["xc_m"] - tw / 2; y0 = p["yc_m"] - Lw / 2
            ax.add_patch(plt.Rectangle((x0, y0), tw, Lw, color="steelblue", alpha=0.7))
        else:                         # plano XZ: linea en y=yc
            x0 = p["xc_m"] - Lw / 2; y0 = p["yc_m"] - tw / 2
            ax.add_patch(plt.Rectangle((x0, y0), Lw, tw, color="seagreen", alpha=0.7))
        ax.text(p["xc_m"], p["yc_m"], p["nombre"].replace("ALMA_", "").replace("ALA_", ""), fontsize=7, ha="center", va="center")
    ax.plot([dia["CMx"]], [dia["CMy"]], "ko", ms=10, label="CM (%.2f,%.2f)" % (dia["CMx"], dia["CMy"]))
    ax.plot([dia["CRx"]], [dia["CRy"]], "rx", ms=12, mew=3, label="CR (%.2f,%.2f)" % (dia["CRx"], dia["CRy"]))
    ax.annotate("", xy=(dia["CMx"], dia["CMy"]), xytext=(dia["CRx"], dia["CRy"]),
                arrowprops=dict(arrowstyle="->", color="purple", lw=1.5))
    ax.text((dia["CMx"] + dia["CRx"]) / 2, (dia["CMy"] + dia["CRy"]) / 2 - 0.25,
            "e0=%.2f m" % abs(dia["e0x_m"]), color="purple", fontsize=8)
    ax.add_patch(plt.Rectangle((0, 0), dia["Edificio_Lx_m"], dia["Edificio_Ly_m"], fill=False, ls="--", ec="0.6"))
    ax.set_xlim(-0.5, dia["Edificio_Lx_m"] + 0.5); ax.set_ylim(-0.5, dia["Edificio_Ly_m"] + 0.5)
    ax.set_aspect("equal"); ax.set_xlabel("X [m]"); ax.set_ylabel("Y [m]")
    ax.set_title("Planta del nucleo en U: CR vs CM"); ax.grid(True, alpha=0.3); ax.legend(fontsize=8, loc="upper right")
    f = os.path.join(carpeta, "planta_CR_CM.png"); fig.tight_layout(); fig.savefig(f, dpi=130); plt.close(fig); archivos.append(f)

    # 3) reparto de cortante por pantalla (X e Y)
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.5))
    for ax, rep, lab in [(axes[0], res["reparto_X"], "Sismo X"), (axes[1], res["reparto_Y"], "Sismo Y")]:
        names = [w["nombre"].replace("NUCLEO_ALMA_acoplada", "ALMA(acopl)") for w in rep["por_pantalla"]]
        vdir = [abs(w["V_directo_torsion_kN"]) for w in rep["por_pantalla"]]
        venv = [w["V_envolvente_kN"] for w in rep["por_pantalla"]]
        x = np.arange(len(names))
        ax.bar(x - 0.2, vdir, 0.4, label="directo+torsion", color="steelblue")
        ax.bar(x + 0.2, venv, 0.4, label="envolvente (+acc.)", color="indianred", alpha=0.8)
        ax.set_xticks(x); ax.set_xticklabels(names, rotation=25, ha="right", fontsize=7)
        ax.set_ylabel("V [kN]"); ax.set_title("%s (Fb=%.0f kN)" % (lab, rep["V_basal_kN"]))
        ax.grid(True, alpha=0.3, axis="y"); ax.legend(fontsize=7)
    f = os.path.join(carpeta, "reparto_cortante.png"); fig.tight_layout(); fig.savefig(f, dpi=130); plt.close(fig); archivos.append(f)

    # 4) vigas de acoplamiento: cortante del dintel + axil de acoplamiento
    ac = res.get("acoplamiento")
    if ac:
        Vl = ac["V_lintel_kN"]
        N_cum = [float(np.sum(Vl[j:])) for j in range(len(Vl))]
        fig, ax = plt.subplots(figsize=(6.5, 4.8))
        ax.barh(z, Vl, height=1.6, color="darkorange", alpha=0.85, label="V dintel por planta")
        ax.plot(N_cum, z, "k-s", ms=4, label="axil acopl. N(z) acumulado")
        for zi, vi in zip(z, Vl):
            ax.text(vi, zi, " %.0f" % vi, va="center", fontsize=7)
        ax.set_xlabel("kN"); ax.set_ylabel("z [m]")
        ax.set_title("Vigas de acoplamiento: DoC=%.2f  N_acopl,base=%.0f kN" % (ac["DoC"], ac["N_acopl_base_kN"]))
        ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
        f = os.path.join(carpeta, "vigas_acoplamiento.png"); fig.tight_layout(); fig.savefig(f, dpi=130); plt.close(fig); archivos.append(f)

    # 5) deriva entre plantas (X e Y borde)
    derX = res["deriva_X"]; derY = res["deriva_Y"]
    plantas = list(range(1, len(z) + 1))
    fig, ax = plt.subplots(figsize=(6.5, 4.5))
    ax.plot([d * 100 for d in derX["deriva_rel"]], plantas, "-o", label="deriva X borde", color="steelblue")
    ax.plot([d * 100 for d in derY["deriva_rel"]], plantas, "-s", label="deriva Y borde", color="seagreen")
    ax.axvline(0.75, color="red", ls="--", lw=1, label="limite 0.75%h")
    ax.set_xlabel("deriva entre plantas [% h]"); ax.set_ylabel("planta")
    ax.set_yticks(plantas); ax.set_title("Deriva entre plantas (borde, q*d_e)")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    f = os.path.join(carpeta, "deriva.png"); fig.tight_layout(); fig.savefig(f, dpi=130); plt.close(fig); archivos.append(f)

    # 6) N-M del machon comprimido
    pcompr = None
    for p in res["verificacion"]["pantallas"]:
        if "compr" in p["nombre"]:
            pcompr = p; break
    if pcompr is None:
        pcompr = res["verificacion"]["pantallas"][0]
    nm = pcompr["interaccion_NM"]; fr = nm["frontera_NM"]
    Ns = [pp["N_kN"] for pp in fr]; Ms = [pp["M_kNm"] for pp in fr]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(Ms, Ns, "b-o", ms=3, label="frontera N-M")
    ax.plot([nm["M_Ed_kNm"]], [nm["N_Ed_kN"]], "rs", ms=11, label="diseno (N=%.0f, M=%.0f)" % (nm["N_Ed_kN"], nm["M_Ed_kNm"]))
    ax.set_xlabel("M [kN*m]"); ax.set_ylabel("N [kN] (+compresion)")
    ax.set_title("Diagrama N-M base (%s)" % pcompr["nombre"])
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    f = os.path.join(carpeta, "diagrama_NM.png"); fig.tight_layout(); fig.savefig(f, dpi=130); plt.close(fig); archivos.append(f)
    return archivos
