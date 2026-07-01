"""
Graficas de la losa plana: mapas de momentos y flecha + plano de pilares con
estado de punzonamiento. Genera PNG en proyecto-losa-plana/.
"""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from plots_3d import _mapa, _mapa_flecha


def plano_pilares(pilares, punz, info, fname):
    fig, ax = plt.subplots(figsize=(6.2, 5.6))
    x0, y0, W, H = info["x0"], info["y0"], info["W"], info["H"]
    ax.add_patch(mpatches.Rectangle((x0, y0), W, H, fill=True, color="0.93", ec="0.5"))
    # estado por posicion
    estado = {}
    for pos, e in punz.items():
        estado[pos] = e["check"]["ok"]
    for nm, p in pilares.items():
        ok = estado.get(p["posicion"], True)
        col = "tab:green" if ok else "tab:red"
        lado = p["lado"]
        ax.add_patch(mpatches.Rectangle((p["x"] - lado / 2, p["y"] - lado / 2), lado, lado,
                                        color=col, zorder=3))
        ax.annotate(f"{abs(p['Rz']['ELU'])/1e3:.0f}", (p["x"], p["y"]),
                    ha="center", va="bottom", fontsize=8, fontweight="bold",
                    xytext=(0, 6), textcoords="offset points")
        ax.annotate(p["posicion"][:4], (p["x"], p["y"]), ha="center", va="top",
                    fontsize=6, color="0.3", xytext=(0, -6), textcoords="offset points")
    ax.set_xlim(x0 - 1, x0 + W + 1); ax.set_ylim(y0 - 1, y0 + H + 1)
    ax.set_aspect("equal"); ax.set_title("Pilares: reacción ELU [kN] y punzonamiento")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    ax.legend(handles=[mpatches.Patch(color="tab:green", label="punz. OK"),
                       mpatches.Patch(color="tab:red", label="punz. NO cumple")],
              loc="upper right", fontsize=8)
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def generar(results, ver, outdir="proyecto-losa-plana"):
    quads = results["losa"]["ELU"]["quads"]
    files = []
    files.append(_mapa(quads, "Mx", "Momento losa Mx (sagging vano) — ELU", f"{outdir}/mapa_Mx.png"))
    files.append(_mapa(quads, "My", "Momento losa My (sagging vano) — ELU", f"{outdir}/mapa_My.png"))
    files.append(_mapa(quads, "Mx", "Momento losa Mx (hogging sobre pilares) — ELU",
                       f"{outdir}/mapa_Mx_hog.png", signo=1.0))
    files.append(_mapa_flecha(results["losa"]["ELS_car"]["deformada"],
                              "Flecha de la losa — ELS característica", f"{outdir}/mapa_flecha.png"))
    files.append(plano_pilares(results["pilares"], ver["punzonamiento"], results["info"],
                               f"{outdir}/plano_pilares.png"))
    return files


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-losa-plana/resultados.json"
    vp = sys.argv[2] if len(sys.argv) > 2 else "proyecto-losa-plana/verificacion.json"
    results = json.load(open(rp, encoding="utf-8"))
    ver = json.load(open(vp, encoding="utf-8"))
    for fn in generar(results, ver):
        print("Figura:", fn)
