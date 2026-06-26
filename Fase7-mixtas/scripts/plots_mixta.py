"""Diagramas de la viga mixta: seccion transversal con PNA, y leyes M(x)/V(x) de ambas fases."""
import sys
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle


def generar(model, results, veri, outdir):
    v = model["viga"]; lo = model["losa"]
    h = v["h"]; b = v["b"]; tw = v["tw"]; tf = v["tf"]
    hp = lo["hp"]; hc = lo["hc"]; beff = veri["b_eff_m"]
    y_na = veri["flexion_mixta"]["PNA_desde_base_mm"] / 1e3

    fig, axs = plt.subplots(1, 3, figsize=(15.5, 5.2))

    # (1) seccion transversal (a escala, en mm)
    ax = axs[0]
    sc = 1e3
    # losa (cobertura) y nervios
    ax.add_patch(Rectangle((-beff / 2 * sc, (h + hp) * sc), beff * sc, hc * sc, fc="#cfe2f3", ec="#3a6ea5"))
    ax.add_patch(Rectangle((-0.30 * sc, h * sc), 0.60 * sc, hp * sc, fc="#e6eef7", ec="#9bb8d6", hatch="//"))
    # perfil de acero (I)
    ax.add_patch(Rectangle((-b / 2 * sc, (h - tf) * sc), b * sc, tf * sc, fc="#9aa0a6", ec="k"))   # ala sup
    ax.add_patch(Rectangle((-tw / 2 * sc, tf * sc), tw * sc, (h - 2 * tf) * sc, fc="#9aa0a6", ec="k"))  # alma
    ax.add_patch(Rectangle((-b / 2 * sc, 0), b * sc, tf * sc, fc="#9aa0a6", ec="k"))               # ala inf
    ax.axhline(y_na * sc, color="r", lw=1.6, ls="--")
    ax.annotate("PNA (%s)" % veri["flexion_mixta"]["PNA_zona"], (beff / 2 * sc * 0.2, y_na * sc + 6), color="r", fontsize=8)
    ax.set_xlim(-beff / 2 * sc * 1.05, beff / 2 * sc * 1.05); ax.set_ylim(-20, (h + hp + hc) * sc + 20)
    ax.set_aspect("equal"); ax.set_title("Sección mixta (b_eff=%.2f m)" % beff)
    ax.set_xlabel("[mm]"); ax.set_ylabel("y desde base acero [mm]")

    # (2) Momento M(x) ambas fases
    ax = axs[1]
    for fase, col, lab in (("mixta", "tab:blue", "mixta (servicio)"), ("construccion", "tab:orange", "construcción")):
        e = results[fase]["ELU"]
        ax.plot(e["x"], [m / 1e3 for m in e["M"]], color=col, lw=2, label=lab)
    ax.axhline(0, color="k", lw=0.6)
    ax.axhline(veri["flexion_mixta"]["M_Rd_kNm"], color="tab:blue", ls=":", lw=1, label="M_Rd mixta")
    ax.axhline(veri["construccion"]["Mc_Rd_kNm"], color="tab:orange", ls=":", lw=1, label="Mc,Rd acero")
    ax.set_title("Momento flector M(x) — ELU"); ax.set_xlabel("x [m]"); ax.set_ylabel("M [kN·m]")
    ax.legend(fontsize=8); ax.grid(True, ls=":", alpha=0.5)

    # (3) Cortante V(x)
    ax = axs[2]
    for fase, col, lab in (("mixta", "tab:blue", "mixta"), ("construccion", "tab:orange", "construcción")):
        e = results[fase]["ELU"]
        ax.plot(e["x"], [vv / 1e3 for vv in e["V"]], color=col, lw=2, label=lab)
    ax.axhline(0, color="k", lw=0.6)
    ax.axhline(veri["cortante"]["Vpl_Rd_kN"], color="g", ls=":", lw=1, label="Vpl,Rd")
    ax.axhline(-veri["cortante"]["Vpl_Rd_kN"], color="g", ls=":", lw=1)
    ax.set_title("Cortante V(x) — ELU"); ax.set_xlabel("x [m]"); ax.set_ylabel("V [kN]")
    ax.legend(fontsize=8); ax.grid(True, ls=":", alpha=0.5)

    fig.suptitle("Viga mixta %s — %s" % (results["info"]["perfil"], veri["veredicto"]),
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fn = os.path.join(outdir, "diag_mixta.png")
    fig.savefig(fn, dpi=125); plt.close(fig)
    return [fn]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-viga-mixta")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    veri = json.load(open(os.path.join(proj, "verificacion.json"), encoding="utf-8"))
    for fn in generar(model, results, veri, proj):
        print("Figura:", fn)
