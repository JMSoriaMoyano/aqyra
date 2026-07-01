"""
Representacion visual del modelo mixto barras + losa. Genera PNG en proyecto-demo/:
  - mapa_Mx.png, mapa_My.png : mapas de color de momentos de losa (ELU)
  - mapa_flecha.png          : mapa de flecha de la losa (ELS caracteristica)
  - modelo_3d.png            : vista 3D del modulo (pilares, vigas, contorno de losa)
"""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
from mpl_toolkits.mplot3d import Axes3D  # noqa
import numpy as np


def _mapa(quads, key, titulo, fname, signo=-1.0, unidad="kN·m/m"):
    x = np.array([q["x"] for q in quads])
    y = np.array([q["y"] for q in quads])
    v = np.array([q[key] for q in quads]) * signo / 1e3  # signo: sagging>0
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, v, levels=14, cmap="RdYlBu_r")
    ax.tricontour(tri, v, levels=14, colors="k", linewidths=0.2, alpha=0.4)
    cb = fig.colorbar(c, ax=ax); cb.set_label(unidad)
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    # marcar maximo
    i = int(np.argmax(v))
    ax.plot(x[i], y[i], "k*", ms=10)
    ax.annotate(f"{v[i]:.1f}", (x[i], y[i]), fontsize=9, fontweight="bold")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def _mapa_flecha(defl, titulo, fname):
    x = np.array([p["x"] for p in defl]); y = np.array([p["y"] for p in defl])
    w = np.abs(np.array([p["dz"] for p in defl])) * 1e3  # mm
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, w, levels=14, cmap="viridis")
    cb = fig.colorbar(c, ax=ax); cb.set_label("flecha |dz| [mm]")
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    i = int(np.argmax(w)); ax.plot(x[i], y[i], "w*", ms=10)
    ax.annotate(f"{w[i]:.2f} mm", (x[i], y[i]), fontsize=9, color="w", fontweight="bold")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def _modelo_3d(model, info, fname):
    fig = plt.figure(figsize=(6.5, 5.6))
    ax = fig.add_subplot(111, projection="3d")
    x0, y0, W, H, z = info["x0"], info["y0"], info["W"], info["H"], info["z"]
    # contorno losa
    xs = [x0, x0 + W, x0 + W, x0, x0]; ys = [y0, y0, y0 + H, y0 + H, y0]
    ax.plot(xs, ys, [z] * 5, color="tab:blue", lw=1.5)
    # relleno losa (semi)
    import numpy as np
    XX, YY = np.meshgrid([x0, x0 + W], [y0, y0 + H])
    ax.plot_surface(XX, YY, np.full_like(XX, z), alpha=0.15, color="tab:blue")
    # pilares
    for (cx, cy) in [(x0, y0), (x0 + W, y0), (x0 + W, y0 + H), (x0, y0 + H)]:
        ax.plot([cx, cx], [cy, cy], [0, z], color="tab:gray", lw=3)
        ax.scatter([cx], [cy], [0], color="k", marker="s", s=40)
    ax.set_title("Modelo 3D — módulo pórtico + losa")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]"); ax.set_zlabel("z [m]")
    ax.view_init(elev=20, azim=-60)
    try:
        ax.set_box_aspect((W, H, z))
    except Exception:
        pass
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def generar(model, results, outdir="proyecto-demo"):
    info = results["info"]
    quads = results["losa"]["ELU"]["quads"]
    files = []
    files.append(_mapa(quads, "Mx", "Momento losa Mx (sagging, tracción inferior) — ELU",
                       f"{outdir}/mapa_Mx.png"))
    files.append(_mapa(quads, "My", "Momento losa My (sagging, tracción inferior) — ELU",
                       f"{outdir}/mapa_My.png"))
    files.append(_mapa_flecha(results["losa"]["ELS_car"]["deformada"],
                              "Flecha de la losa — ELS característica", f"{outdir}/mapa_flecha.png"))
    files.append(_modelo_3d(model, info, f"{outdir}/modelo_3d.png"))
    return files


if __name__ == "__main__":
    mp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    rp = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    model = json.load(open(mp, encoding="utf-8"))
    results = json.load(open(rp, encoding="utf-8"))
    for f in generar(model, results):
        print("Figura:", f)
