"""Graficas del muro: mapa de compresion de membrana (vertical) y flecha fuera de plano."""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.tri as mtri
import numpy as np


def _mapa_xz(pts, key, signo, titulo, fname, unidad, clip_pct=98):
    x = np.array([p["x"] for p in pts]); z = np.array([p["z"] for p in pts])
    v = np.array([p[key] for p in pts]) * signo / 1e3
    vmax = np.percentile(np.abs(v), clip_pct)
    v = np.clip(v, -vmax, vmax)
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    tri = mtri.Triangulation(x, z)
    c = ax.tricontourf(tri, v, levels=14, cmap="inferno")
    cb = fig.colorbar(c, ax=ax); cb.set_label(unidad)
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m] (largo)"); ax.set_ylabel("z [m] (altura)")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def _mapa_flecha(defl, titulo, fname):
    x = np.array([p["x"] for p in defl]); z = np.array([p["z"] for p in defl])
    w = np.abs(np.array([p["dy"] for p in defl])) * 1e3
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    tri = mtri.Triangulation(x, z)
    c = ax.tricontourf(tri, w, levels=14, cmap="viridis")
    cb = fig.colorbar(c, ax=ax); cb.set_label("flecha fuera de plano |dy| [mm]")
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m]"); ax.set_ylabel("z [m]")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def generar(results, outdir="proyecto-muro"):
    q = results["muro"]["ELU"]["quads"]
    files = []
    files.append(_mapa_xz(q, "ny", -1.0, "Compresión vertical de membrana — ELU [kN/m]\n(escala recortada; picos en esquinas de base)",
                          f"{outdir}/mapa_compresion.png", "kN/m"))
    files.append(_mapa_flecha(results["muro"]["ELS_car"]["deformada"],
                              "Flecha fuera de plano (viento) — ELS", f"{outdir}/mapa_flecha.png"))
    return files


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-muro/resultados.json"
    results = json.load(open(rp, encoding="utf-8"))
    for fn in generar(results):
        print("Figura:", fn)
