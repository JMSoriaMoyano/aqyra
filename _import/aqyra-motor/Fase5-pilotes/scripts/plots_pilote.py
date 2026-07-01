"""Diagramas del pilote: ley de momentos M(z) y deformada lateral dx(z) en profundidad."""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


def generar(results, outdir="proyecto-pilote", combo="ELU"):
    esf = results["pilote"][combo]["esfuerzos"]
    defl_combo = "ELS_car" if "ELS_car" in results["pilote"] else combo
    df = results["pilote"][defl_combo]["deformada"]
    z_m = [pt["z"] for pt in esf]; M = [pt["M"] / 1e3 for pt in esf]
    z_d = [pt["z"] for pt in df]; dx = [pt["dx"] * 1e3 for pt in df]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(8.0, 6.0), sharey=True)
    ax1.plot(M, z_m, color="tab:red", lw=2); ax1.fill_betweenx(z_m, 0, M, color="tab:red", alpha=0.2)
    ax1.axvline(0, color="k", lw=0.8); ax1.set_title("Momento flector M [kN·m] (ELU)")
    ax1.set_xlabel("M [kN·m]"); ax1.set_ylabel("z [m] (0 = cabeza)"); ax1.grid(True, ls=":", alpha=0.5)
    Mmax = max(M, key=abs)
    ax1.annotate(f"M_max={Mmax:.0f}", (Mmax, z_m[M.index(Mmax)]), fontsize=9, fontweight="bold")

    ax2.plot(dx, z_d, color="tab:blue", lw=2); ax2.fill_betweenx(z_d, 0, dx, color="tab:blue", alpha=0.2)
    ax2.axvline(0, color="k", lw=0.8); ax2.set_title(f"Deformada lateral dx [mm] ({defl_combo})")
    ax2.set_xlabel("dx [mm]"); ax2.grid(True, ls=":", alpha=0.5)
    ax2.annotate(f"cabeza={dx[0]:.1f} mm", (dx[0], z_d[0]), fontsize=9, fontweight="bold")

    fig.suptitle(f"Pilote Ø{results['info']['D']} m, L={results['info']['L']} m — viga sobre muelles laterales")
    fig.tight_layout()
    fn = f"{outdir}/diag_pilote.png"
    fig.savefig(fn, dpi=130); plt.close(fig)
    return [fn]


if __name__ == "__main__":
    rp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-pilote/resultados.json"
    results = json.load(open(rp, encoding="utf-8"))
    for fn in generar(results):
        print("Figura:", fn)
