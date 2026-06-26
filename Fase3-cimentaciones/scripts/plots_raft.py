"""Mapas de la losa de cimentacion: presion del terreno, momentos Mx/My y posicion de pilares."""
import sys
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import matplotlib.patches as mpatches
import numpy as np


def _cols(ax, info):
    for p in info["pilares"]:
        c = p["lado"]
        ax.add_patch(mpatches.Rectangle((p["x"] - c / 2, p["y"] - c / 2), c, c,
                     fill=False, ec="k", lw=1.2))


def generar(results, ver, outdir):
    info = results["info"]
    pres = results["losa"]["ELU"]["presion"]
    quads = results["losa"]["ELU"]["quads"]

    fig, axs = plt.subplots(1, 3, figsize=(16.5, 5.2))

    # (1) presion del terreno
    ax = axs[0]
    x = np.array([p["x"] for p in pres]); y = np.array([p["y"] for p in pres])
    v = np.array([p["p"] for p in pres]) / 1e3
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, v, levels=14, cmap="YlOrRd")
    fig.colorbar(c, ax=ax, label="kPa")
    _cols(ax, info)
    g = ver["geotecnia"]
    ax.set_title("Presión del terreno — ELU\np_max=%.0f / Rd=%.0f kPa (%.0f%%)"
                 % (g["p_max_kPa"], g["Rd_kPa"], g["u_Rd"] * 100))
    ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")

    # (2) y (3) momentos Mx, My (traccion inferior = -M), pico recortado
    for ax, key, ttl in ((axs[1], "Mx", "Mx (tracc. inferior) — ELU"),
                         (axs[2], "My", "My (tracc. inferior) — ELU")):
        xq = np.array([q["x"] for q in quads]); yq = np.array([q["y"] for q in quads])
        vq = -np.array([q[key] for q in quads]) / 1e3
        vmax = np.percentile(np.abs(vq), 97)
        vq = np.clip(vq, -vmax, vmax)
        triq = mtri.Triangulation(xq, yq)
        cc = ax.tricontourf(triq, vq, levels=14, cmap="RdBu_r")
        fig.colorbar(cc, ax=ax, label="kN·m/m")
        _cols(ax, info)
        ax.set_title(ttl + "\n(escala recortada bajo pilares)")
        ax.set_aspect("equal"); ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")

    fig.suptitle("Losa de cimentación %dx%d m — %s" % (info["BX"], info["LY"], ver["veredicto"]),
                 fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fn = os.path.join(outdir, "mapas_raft.png")
    fig.savefig(fn, dpi=120); plt.close(fig)
    return [fn]


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-losa-cimentacion")
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    ver = json.load(open(os.path.join(proj, "verificacion.json"), encoding="utf-8"))
    for fn in generar(results, ver, proj):
        print("Figura:", fn)
