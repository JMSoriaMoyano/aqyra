"""
Representacion visual de resultados sobre el portico (plano x-z).
Genera PNGs en proyecto-demo/:
  - diag_momentos.png  (ley de flectores ELU sobre la geometria)
  - diag_cortantes.png (ley de cortantes ELU)
  - diag_axiles.png    (ley de axiles ELU)
  - deformada.png      (deformada ELS caracteristica, amplificada)
"""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def _node_xz(model, nid):
    n = model["nodos"][nid]
    return n["x"], n["z"]


def _draw_frame(ax, model, color="0.6", lw=2):
    for bid, b in model["barras"].items():
        xi, zi = _node_xz(model, b["ni"])
        xj, zj = _node_xz(model, b["nj"])
        ax.plot([xi, xj], [zi, zj], color=color, lw=lw, zorder=1)
    # apoyos
    for nid, n in model["nodos"].items():
        if any(n["apoyo"]):
            ax.plot(n["x"], n["z"], "s", color="k", ms=8, zorder=3)
    ax.set_aspect("equal")
    ax.grid(True, ls=":", alpha=0.4)


def _diagram(model, results, combo, key, title, fname, scale_frac=0.18, fill="tab:red"):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    _draw_frame(ax, model)
    # escala global: max valor absoluto entre barras
    vmax = 1e-9
    for bid in model["barras"]:
        vmax = max(vmax, max(abs(v) for v in results["barras"][bid][combo][key]))
    # tamano de referencia del portico
    xs = [model["nodos"][n]["x"] for n in model["nodos"]]
    zs = [model["nodos"][n]["z"] for n in model["nodos"]]
    ref = max(max(xs) - min(xs), max(zs) - min(zs))
    s = scale_frac * ref / vmax

    for bid, b in model["barras"].items():
        xi, zi = _node_xz(model, b["ni"])
        xj, zj = _node_xz(model, b["nj"])
        L = results["longitudes"][bid]
        dx, dz = (xj - xi) / L, (zj - zi) / L      # direccion barra
        px, pz = -dz, dx                            # perpendicular en plano
        xv = results["barras"][bid][combo]["x"]
        val = results["barras"][bid][combo][key]
        X, Z = [], []
        for t, v in zip(xv, val):
            bx = xi + dx * t
            bz = zi + dz * t
            X.append(bx + px * v * s)
            Z.append(bz + pz * v * s)
        # contorno + relleno entre barra y diagrama
        ax.plot(X, Z, color=fill, lw=1.0, zorder=2)
        for t, v, xx, zz in zip(xv, val, X, Z):
            ax.plot([xi + dx * t, xx], [zi + dz * t, zz], color=fill, lw=0.4, alpha=0.5, zorder=1)
        # etiquetas de extremos
        ax.annotate(f"{val[0]/1e3:.1f}", (X[0], Z[0]), fontsize=7, color=fill)
        ax.annotate(f"{val[-1]/1e3:.1f}", (X[-1], Z[-1]), fontsize=7, color=fill)
        imax = max(range(len(val)), key=lambda i: abs(val[i]))
        ax.annotate(f"{val[imax]/1e3:.1f}", (X[imax], Z[imax]), fontsize=8,
                    color=fill, fontweight="bold")

    ax.set_title(title)
    ax.set_xlabel("x [m]"); ax.set_ylabel("z [m]")
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)
    return fname


def _deformada(model, results, combo, fname, n_amp=None):
    fig, ax = plt.subplots(figsize=(7, 5.5))
    _draw_frame(ax, model, color="0.75", lw=1.2)
    # amplificacion automatica
    dmax = 1e-12
    for bid in model["barras"]:
        dmax = max(dmax, max(abs(d) for d in results["barras"][bid][combo]["defl"]))
    xs = [model["nodos"][n]["x"] for n in model["nodos"]]
    zs = [model["nodos"][n]["z"] for n in model["nodos"]]
    ref = max(max(xs) - min(xs), max(zs) - min(zs))
    amp = (0.10 * ref / dmax) if n_amp is None else n_amp

    for bid, b in model["barras"].items():
        xi, zi = _node_xz(model, b["ni"])
        xj, zj = _node_xz(model, b["nj"])
        L = results["longitudes"][bid]
        dx, dz = (xj - xi) / L, (zj - zi) / L
        px, pz = -dz, dx
        xv = results["barras"][bid][combo]["x"]
        defl = results["barras"][bid][combo]["defl"]
        X = [xi + dx * t + px * d * amp for t, d in zip(xv, defl)]
        Z = [zi + dz * t + pz * d * amp for t, d in zip(xv, defl)]
        ax.plot(X, Z, color="tab:blue", lw=2, zorder=2)

    ax.set_title(f"Deformada ({combo}) — amplificacion x{amp:.0f}")
    ax.set_xlabel("x [m]"); ax.set_ylabel("z [m]")
    fig.tight_layout()
    fig.savefig(fname, dpi=130)
    plt.close(fig)
    return fname


def generar(model, results, outdir="proyecto-demo"):
    files = []
    files.append(_diagram(model, results, "ELU", "M",
                          "Ley de momentos flectores M [kN·m] — ELU (1.35G+1.50Q)",
                          f"{outdir}/diag_momentos.png", fill="tab:red"))
    files.append(_diagram(model, results, "ELU", "V",
                          "Ley de cortantes V [kN] — ELU (1.35G+1.50Q)",
                          f"{outdir}/diag_cortantes.png", fill="tab:green"))
    # axil: usar arrays N? solver guardo N_i/N_j; reconstruimos constante por barra
    for bid in model["barras"]:
        e = results["barras"][bid]["ELU"]
        n = len(results["barras"][bid]["ELU"]["x"])
        results["barras"][bid]["ELU"]["N"] = [e["N_i"]] * n
    files.append(_diagram(model, results, "ELU", "N",
                          "Ley de axiles N [kN] — ELU (1.35G+1.50Q)",
                          f"{outdir}/diag_axiles.png", fill="tab:purple"))
    files.append(_deformada(model, results, "ELS_car", f"{outdir}/deformada.png"))
    return files


if __name__ == "__main__":
    model_path = sys.argv[1] if len(sys.argv) > 1 else "proyecto-demo/modelo_neutro.json"
    res_path = sys.argv[2] if len(sys.argv) > 2 else "proyecto-demo/resultados.json"
    with open(model_path, encoding="utf-8") as fh:
        model = json.load(fh)
    with open(res_path, encoding="utf-8") as fh:
        results = json.load(fh)
    for f in generar(model, results):
        print("Figura:", f)
