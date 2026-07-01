"""Graficas de la zapata: presion del terreno, momento de placa y planta con secciones criticas."""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.tri as mtri
import numpy as np


def _mapa_nodal(pts, key, signo, titulo, fname, unidad, cmap):
    x = np.array([p["x"] for p in pts]); y = np.array([p["y"] for p in pts])
    v = np.array([p[key] for p in pts]) * signo / 1e3
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, v, levels=14, cmap=cmap)
    cb = fig.colorbar(c, ax=ax); cb.set_label(unidad)
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def _mapa_quad(quads, key, signo, titulo, fname, unidad, cmap):
    x = np.array([q["x"] for q in quads]); y = np.array([q["y"] for q in quads])
    v = np.array([q[key] for q in quads]) * signo / 1e3
    # recortar pico de concentracion bajo el pilar
    vmax = np.percentile(np.abs(v), 97)
    v = np.clip(v, -vmax, vmax)
    fig, ax = plt.subplots(figsize=(6.0, 5.2))
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, v, levels=14, cmap=cmap)
    cb = fig.colorbar(c, ax=ax); cb.set_label(unidad)
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def planta(info, ver, fname):
    B = info["B"]; c = info["c_pilar"]; xp = info["xp"]; yp = info["yp"]
    fig, ax = plt.subplots(figsize=(5.6, 5.4))
    ax.add_patch(mpatches.Rectangle((0, 0), B, B, fill=True, color="0.93", ec="0.4"))
    ax.add_patch(mpatches.Rectangle((xp - c / 2, yp - c / 2), c, c, color="tab:gray"))
    g = ver["geotecnia"]
    ax.set_title(f"Zapata {B:.1f}×{B:.1f} m — pilar {c*1e3:.0f} mm\n"
                 f"p_max={g['p_max_kPa']:.0f} kPa / Rd={g['Rd_kPa']:.0f} kPa ({g['u_Rd']*100:.0f}%)")
    ax.set_xlim(-0.3, B + 0.3); ax.set_ylim(-0.3, B + 0.3); ax.set_aspect("equal")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def generar(results, ver, outdir="proyecto-zapata"):
    files = []
    files.append(_mapa_nodal(results["zapata"]["ELU"]["presion"], "p", 1.0,
                 "Presión del terreno — ELU [kPa]", f"{outdir}/mapa_presion.png", "kPa", "YlOrRd"))
    files.append(_mapa_quad(results["zapata"]["ELU"]["quads"], "Mx", -1.0,
                 "Momento de placa Mx (tracción inferior) — ELU [kN·m/m]\n(escala recortada bajo pilar)",
                 f"{outdir}/mapa_Mx.png", "kN·m/m", "viridis"))
    files.append(planta(results["info"], ver, f"{outdir}/planta.png"))
    return files


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-zapata/resultados.json"
    vp = sys.argv[2] if len(sys.argv) > 2 else "proyecto-zapata/verificacion.json"
    results = json.load(open(rp, encoding="utf-8"))
    ver = json.load(open(vp, encoding="utf-8"))
    for fn in generar(results, ver):
        print("Figura:", fn)
