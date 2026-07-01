"""
Diagramas (PNG) del Caso 11 - Pantalla de cortante sismica EC8.

  - espectro Sd(T) con el punto T1
  - formas modales en altura
  - fuerzas por planta
  - ley de cortante en altura
  - ley de momento en altura
  - deriva entre plantas
  - diagrama N-M con el punto de diseno
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

import ec8


def generar(model, res, out, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    archivos = []
    e = model["ec8"]
    G = 9.81
    ag = float(e["ag_g"]) * G
    S = float(e["S"]); TB = float(e["TB_s"]); TC = float(e["TC_s"])
    TD = float(e["TD_s"]); q = float(e["q"])
    z = model["stick"]["z_plantas_m"]
    z_full = [0.0] + list(z)

    # 1) espectro
    Ts, Ss = ec8.espectro_curva(ag, S, TB, TC, TD, q)
    T1 = res["modal"]["modos"][0]["T_s"]
    Sd_T1 = ec8.Sd(T1, ag, S, TB, TC, TD, q)
    fig, ax = plt.subplots(figsize=(7, 4.5))
    ax.plot(Ts, Ss / G, "b-", lw=2, label="Sd(T)/g (q=%.1f)" % q)
    ax.axhline(ec8.Sd_meseta(ag, S, q) / G, color="gray", ls="--", lw=1,
               label="meseta=%.3f g" % (ec8.Sd_meseta(ag, S, q) / G))
    ax.plot([T1], [Sd_T1 / G], "ro", ms=9, label="T1=%.3f s -> %.3f g" % (T1, Sd_T1 / G))
    for tt, lb in [(TB, "TB"), (TC, "TC"), (TD, "TD")]:
        ax.axvline(tt, color="0.8", ls=":")
    ax.set_xlabel("T [s]"); ax.set_ylabel("Sd / g")
    ax.set_title("Espectro de calculo EC8 (suelo C, tipo 1)")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    f1 = os.path.join(carpeta, "espectro_Sd.png")
    fig.tight_layout(); fig.savefig(f1, dpi=130); plt.close(fig); archivos.append(f1)

    # 2) modos
    fig, ax = plt.subplots(figsize=(6, 5))
    for m in res["modal"]["modos"]:
        phi = [0.0] + list(m["phi"])
        phin = np.array(phi)
        mx = max(abs(phin)) or 1.0
        ax.plot(phin / mx, z_full, "-o", ms=4,
                label="Modo %d  T=%.3f s  M_eff=%.0f%%" %
                      (m["modo"], m["T_s"], m["Meff_frac"] * 100))
    ax.axvline(0, color="k", lw=0.8)
    ax.set_xlabel("phi (normalizado)"); ax.set_ylabel("z [m]")
    ax.set_title("Formas modales (stick voladizo)")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=7)
    f2 = os.path.join(carpeta, "modos.png")
    fig.tight_layout(); fig.savefig(f2, dpi=130); plt.close(fig); archivos.append(f2)

    # 3) fuerzas por planta (fuerzas laterales gobernante)
    Fl = res["fuerzas_laterales"]["F_i_kN"]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.barh(z, Fl, height=1.5, color="steelblue", alpha=0.8)
    for zi, fi in zip(z, Fl):
        ax.text(fi, zi, " %.0f" % fi, va="center", fontsize=8)
    ax.set_xlabel("F_i [kN]"); ax.set_ylabel("z [m]")
    ax.set_title("Fuerzas laterales por planta (Fb=%.0f kN)" %
                 res["fuerzas_laterales"]["Fb_kN"])
    ax.grid(True, alpha=0.3)
    f3 = os.path.join(carpeta, "fuerzas_planta.png")
    fig.tight_layout(); fig.savefig(f3, dpi=130); plt.close(fig); archivos.append(f3)

    # 4) ley de cortante en altura
    V = res["fuerzas_laterales"]["V_kN"]
    Vstep_z = []; Vstep_v = []
    for j in range(len(V)):
        z0 = z_full[j]; z1 = z_full[j + 1]
        Vstep_z += [z0, z1]; Vstep_v += [V[j], V[j]]
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot(Vstep_v, Vstep_z, "r-", lw=2)
    ax.fill_betweenx(Vstep_z, 0, Vstep_v, color="red", alpha=0.15)
    ax.set_xlabel("V [kN]"); ax.set_ylabel("z [m]")
    ax.set_title("Ley de cortante (voladizo)")
    ax.grid(True, alpha=0.3)
    f4 = os.path.join(carpeta, "cortante_altura.png")
    fig.tight_layout(); fig.savefig(f4, dpi=130); plt.close(fig); archivos.append(f4)

    # 5) ley de momento en altura
    M = res["fuerzas_laterales"]["M_niveles_kNm"]
    fig, ax = plt.subplots(figsize=(5.5, 5))
    ax.plot(M, z_full, "g-", lw=2, marker="o", ms=4)
    ax.fill_betweenx(z_full, 0, M, color="green", alpha=0.15)
    ax.set_xlabel("M [kN*m]"); ax.set_ylabel("z [m]")
    ax.set_title("Ley de momento (M_base=%.0f kN*m)" %
                 res["fuerzas_laterales"]["Mbase_kNm"])
    ax.grid(True, alpha=0.3)
    f5 = os.path.join(carpeta, "momento_altura.png")
    fig.tight_layout(); fig.savefig(f5, dpi=130); plt.close(fig); archivos.append(f5)

    # 6) deriva entre plantas
    der = res["deriva"]["por_planta"]
    plantas = [d["planta"] for d in der]
    drnu = [d["dr_nu_mm"] for d in der]
    lim = [d["limite_mm"] for d in der]
    fig, ax = plt.subplots(figsize=(6, 4.5))
    ax.bar([p - 0.18 for p in plantas], drnu, width=0.36, label="d_r*nu", color="orange")
    ax.bar([p + 0.18 for p in plantas], lim, width=0.36, label="limite", color="gray", alpha=0.6)
    ax.set_xlabel("planta"); ax.set_ylabel("deriva [mm]")
    ax.set_title("Deriva entre plantas vs limite (§4.4.3.2)")
    ax.set_xticks(plantas); ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    f6 = os.path.join(carpeta, "deriva.png")
    fig.tight_layout(); fig.savefig(f6, dpi=130); plt.close(fig); archivos.append(f6)

    # 7) diagrama N-M con punto de diseno
    nm = res["verificacion"]["interaccion_NM"]
    fr = nm["frontera_NM"]
    Ns = [p["N_kN"] for p in fr]; Ms = [p["M_kNm"] for p in fr]
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.plot(Ms, Ns, "b-o", ms=3, label="frontera N-M")
    ax.plot([nm["M_Ed_kNm"]], [nm["N_Ed_kN"]], "rs", ms=10,
            label="diseno (N=%.0f kN, M=%.0f kN*m)" % (nm["N_Ed_kN"], nm["M_Ed_kNm"]))
    ax.set_xlabel("M [kN*m]"); ax.set_ylabel("N [kN] (+compresion)")
    ax.set_title("Diagrama N-M base de la pantalla")
    ax.grid(True, alpha=0.3); ax.legend(fontsize=8)
    f7 = os.path.join(carpeta, "diagrama_NM.png")
    fig.tight_layout(); fig.savefig(f7, dpi=130); plt.close(fig); archivos.append(f7)

    return archivos
