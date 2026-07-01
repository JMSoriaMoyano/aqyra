"""Diagramas de la pantalla anclada: esquema, empujes, M(z) del fuste y deformada."""
import sys
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, FancyArrow


def generar(model, results, veri, outdir):
    info = results["info"]; t = model["terreno"]
    L = info["L"]; h = info["h"]; d = info["d"]; tp = info["t"]; Ka = info["Ka"]; Kp = info["Kp"]
    z_a = info["z_ancla"]
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    q = model["sobrecarga"]

    fig, axs = plt.subplots(1, 4, figsize=(15.0, 6.5))

    # (1) Esquema
    ax = axs[0]
    ax.add_patch(Rectangle((0, -L), tp, L, fc="#bdbdbd", ec="k"))           # pantalla
    ax.add_patch(Rectangle((tp, -L), 2.2, L, fc="#e0d2b0", ec="#b9a06a", alpha=0.6))  # trasdos
    ax.add_patch(Rectangle((-2.2, -L), 2.2, (L - h), fc="#d6c39a", ec="#b9a06a", alpha=0.6))  # delante (empotramiento)
    ax.annotate("excavación", (-2.0, -h + 0.2), fontsize=8)
    ax.plot([-2.2, 0], [-h, -h], "k--", lw=0.8)
    ax.annotate("ancla", (tp + 0.2, -z_a), fontsize=8, color="b")
    ax.add_patch(FancyArrow(tp, -z_a, 1.8, 0.9, width=0.05, color="b", length_includes_head=True))
    ax.annotate("pasivo", (-1.5, -(h + d / 2)), fontsize=8, color="g")
    ax.set_xlim(-2.6, 3.2); ax.set_ylim(-L - 0.5, 0.7); ax.set_aspect("equal")
    ax.set_title("Esquema (L=%.1f, h=%.1f, d=%.1f m)" % (L, h, d)); ax.set_ylabel("cota [m]")
    ax.grid(True, ls=":", alpha=0.4)

    # (2) Empujes activo/pasivo
    ax = axs[1]
    n = 40; zs = [L * i / n for i in range(n + 1)]
    pa = [(Ka * _sigv(t, z, has_w, zw, gw) + Ka * q + (gw * max(z - zw, 0) if has_w else 0)) / 1e3 for z in zs]
    pp = [(Kp * t["gamma_pas"] * (z - h)) / 1e3 if z > h else 0.0 for z in zs]
    ax.plot(pa, [-z for z in zs], "tab:brown", lw=2, label="activo (trasdós)")
    ax.plot([-x for x in pp], [-z for z in zs], "tab:green", lw=2, label="pasivo (delante)")
    ax.fill_betweenx([-z for z in zs], 0, pa, color="tab:brown", alpha=0.15)
    ax.fill_betweenx([-z for z in zs], 0, [-x for x in pp], color="tab:green", alpha=0.15)
    ax.axhline(-h, color="k", ls="--", lw=0.8); ax.axvline(0, color="k", lw=0.6)
    ax.set_title("Empujes (Ka=%.3f, Kp=%.2f)" % (Ka, Kp)); ax.set_xlabel("presión [kPa]")
    ax.set_ylabel("cota [m]"); ax.legend(fontsize=8); ax.grid(True, ls=":", alpha=0.5)

    # (3) Momento flector M(z)
    ax = axs[2]
    esf = results["ELU"]["esfuerzos"]
    zc = [-pt["z"] for pt in esf]; Mv = [pt["M"] / 1e3 for pt in esf]
    ax.plot(Mv, zc, "tab:red", lw=2); ax.fill_betweenx(zc, 0, Mv, color="tab:red", alpha=0.2)
    ax.axhline(-z_a, color="b", ls=":", lw=1, label="ancla")
    ax.axhline(-h, color="k", ls="--", lw=0.8, label="excavación")
    ax.axvline(0, color="k", lw=0.6)
    Mmax = max(Mv, key=abs)
    ax.set_title("Momento flector M(z) — ELU (máx %.0f kN·m/m)" % abs(Mmax))
    ax.set_xlabel("M [kN·m/m]"); ax.legend(fontsize=8); ax.grid(True, ls=":", alpha=0.5)

    # (4) Deformada
    ax = axs[3]
    df = results["ELS_car"]["deformada"] if "ELS_car" in results else results["ELU"]["deformada"]
    zc = [-pt["z"] for pt in df]; dx = [pt["dx"] * 1e3 for pt in df]
    ax.plot(dx, zc, "tab:blue", lw=2); ax.fill_betweenx(zc, 0, dx, color="tab:blue", alpha=0.2)
    ax.axhline(-z_a, color="b", ls=":", lw=1); ax.axhline(-h, color="k", ls="--", lw=0.8)
    ax.axvline(0, color="k", lw=0.6)
    ax.set_title("Deformada dx [mm] (cabeza %.1f mm)" % dx[0])
    ax.set_xlabel("dx [mm]"); ax.grid(True, ls=":", alpha=0.5)

    fig.suptitle("Pantalla anclada — %s" % veri["veredicto"], fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.96])
    fn = os.path.join(outdir, "diag_pantalla.png")
    fig.savefig(fn, dpi=125); plt.close(fig)
    return [fn]


def _sigv(t, z, has_w, zw, gw):
    if not has_w or z <= zw:
        return t["gamma"] * z
    return t["gamma"] * zw + (t["gamma"] - gw) * (z - zw)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-pantalla-anclada")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    veri = json.load(open(os.path.join(proj, "verificacion.json"), encoding="utf-8"))
    for fn in generar(model, results, veri, proj):
        print("Figura:", fn)
