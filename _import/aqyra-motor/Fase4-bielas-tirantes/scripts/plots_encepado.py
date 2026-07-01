"""Esquema del modelo de bielas y tirantes del encepado de 2 pilotes."""
import sys
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


def esquema(out, fname):
    g = out["geom_in"]
    a = g["SeparacionPilotes"]; h = g["Canto"]; c = g["LadoPilar"]; dp = g["DiametroPilote"]
    z = out["geom"]["z_mm"] / 1e3
    overhang = max(0.5 * dp, 0.25)
    half = a / 2 + overhang
    fig, ax = plt.subplots(figsize=(7.0, 4.6))
    # contorno del encepado
    ax.add_patch(mpatches.Rectangle((-half, 0), 2 * half, h, fill=True, color="0.94", ec="0.5"))
    # pilar
    ax.add_patch(mpatches.Rectangle((-c / 2, h, ), c, 0.25, color="tab:gray"))
    ax.annotate(f"N_Ed = {out['N_Ed_kN']:.0f} kN", (0, h + 0.25), ha="center", va="bottom",
                fontsize=10, fontweight="bold")
    # pilotes
    for sx in (-a / 2, a / 2):
        ax.add_patch(mpatches.Rectangle((sx - dp / 2, -0.35), dp, 0.35, color="tab:gray"))
        ax.annotate(f"{out['celosia']['R_pilote_kN']:.0f} kN", (sx, -0.40), ha="center", va="top", fontsize=9)
    # nodos STM
    Ttop = (0, z); P1 = (-a / 2, 0); P2 = (a / 2, 0)
    # bielas (compresion, rojo)
    for P in (P1, P2):
        ax.plot([Ttop[0], P[0]], [Ttop[1], P[1]], color="tab:red", lw=3, zorder=3)
    ax.annotate(f"biela C = {out['celosia']['C_kN']:.0f} kN ({out['biela']['u']*100:.0f}%)",
                (-a / 4, z / 2), color="tab:red", fontsize=9, rotation=0, ha="center")
    # tirante (traccion, azul)
    ax.plot([P1[0], P2[0]], [P1[1], P2[1]], color="tab:blue", lw=3, zorder=3)
    ax.annotate(f"tirante T = {out['celosia']['T_kN']:.0f} kN  →  As = {out['tirante']['As_req_cm2']:.1f} cm²",
                (0, 0.04), color="tab:blue", fontsize=9, ha="center", va="bottom")
    # nodos
    for (P, lab) in [(Ttop, f"CCC {out['nudo_CCC']['u']*100:.0f}%"),
                     (P1, f"CCT {out['nudo_CCT']['u']*100:.0f}%"), (P2, "CCT")]:
        ax.plot(*P, "ko", ms=7, zorder=4)
        ax.annotate(lab, P, fontsize=8, xytext=(6, 6), textcoords="offset points")
    ax.annotate(f"θ = {out['geom']['theta_deg']:.0f}°  ·  z = {z*1e3:.0f} mm",
                (a / 4, z / 2), fontsize=9, ha="center")
    ax.set_xlim(-half - 0.3, half + 0.3); ax.set_ylim(-0.7, h + 0.6)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title(f"Modelo de bielas y tirantes — encepado 2 pilotes  ({out['veredicto']})")
    fig.tight_layout(); fig.savefig(fname, dpi=130); plt.close(fig)
    return fname


def generar(out, outdir="proyecto-encepado"):
    return [esquema(out, f"{outdir}/esquema_stm.png")]


if __name__ == "__main__":
    vp = sys.argv[1] if len(sys.argv) > 1 else "proyecto-encepado/verificacion.json"
    out = json.load(open(vp, encoding="utf-8"))
    for fn in generar(out):
        print("Figura:", fn)
