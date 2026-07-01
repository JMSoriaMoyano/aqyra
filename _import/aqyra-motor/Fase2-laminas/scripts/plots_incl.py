"""Graficas de la cubierta inclinada: vista 3D + mapas de momentos, membrana y flecha."""
import sys
import json
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D  # noqa
import numpy as np
from plots_3d import _mapa, _mapa_flecha


def vista_3d(info, fname):
    Lu, Lv = info["Lu"], info["Lv"]; th = math.radians(info["angulo"])
    fig = plt.figure(figsize=(6.4, 5.2)); ax = fig.add_subplot(111, projection="3d")
    P = {"C1": (0, 0, 0), "C2": (Lv, 0, 0), "C3": (Lv, Lu * math.cos(th), Lu * math.sin(th)),
         "C4": (0, Lu * math.cos(th), Lu * math.sin(th))}
    order = ["C1", "C2", "C3", "C4", "C1"]
    xs = [P[k][0] for k in order]; ys = [P[k][1] for k in order]; zs = [P[k][2] for k in order]
    ax.plot(xs, ys, zs, color="tab:blue", lw=2)
    XX = np.array([[P["C1"][0], P["C2"][0]], [P["C4"][0], P["C3"][0]]])
    YY = np.array([[P["C1"][1], P["C2"][1]], [P["C4"][1], P["C3"][1]]])
    ZZ = np.array([[P["C1"][2], P["C2"][2]], [P["C4"][2], P["C3"][2]]])
    ax.plot_surface(XX, YY, ZZ, alpha=0.25, color="tab:blue")
    # aleros (borde inferior) apoyo
    ax.plot([0, Lv], [0, 0], [0, 0], color="k", lw=4)
    ax.set_title(f"Cubierta inclinada {info['angulo']:.0f}° (Lu={Lu} m, Lv={Lv} m)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    ax.view_init(elev=18, azim=-70)
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def generar(results, outdir="proyecto-cubierta"):
    q = results["losa"]["ELU"]["quads"]
    files = [vista_3d(results["info"], f"{outdir}/vista_3d.png")]
    files.append(_mapa(q, "Mx", "Momento Mx (sagging) — ELU", f"{outdir}/mapa_Mx.png"))
    files.append(_mapa(q, "My", "Momento My (sagging) — ELU", f"{outdir}/mapa_My.png"))
    # membrana ny: signo propio (compresion negativa); mostramos -ny como compresion>0
    files.append(_mapa(q, "ny", "Membrana n_y (compresión faldón) — ELU [kN/m]",
                       f"{outdir}/mapa_membrana.png", signo=-1.0, unidad="kN/m"))
    files.append(_mapa_flecha([{"x": p["x"], "y": p["y"], "dz": p["dn"]}
                               for p in results["losa"]["ELS_car"]["deformada"]],
                              "Flecha normal al faldón — ELS car.", f"{outdir}/mapa_flecha.png"))
    return files


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-cubierta/resultados.json"
    results = json.load(open(rp, encoding="utf-8"))
    for fn in generar(results):
        print("Figura:", fn)
