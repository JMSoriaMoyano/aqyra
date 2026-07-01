"""Diagramas del muro de contension: seccion, empujes, presion bajo zapata y M(z) del alzado."""
import sys
import os
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon as MplPoly, Rectangle


def generar(model, results, veri, outdir):
    m = model["muro"]; t = model["terreno"]
    Hm, t_alz, e_z = m["Hm"], m["t_alz"], m["e_z"]
    pun, tal, B, Df = m["puntera"], m["talon"], m["B"], m["Df"]
    H = results["empujes"]["H"]; Ka = results["empujes"]["Ka"]
    comps = results["empujes"]["componentes"]

    fig, axs = plt.subplots(2, 2, figsize=(11.0, 9.0))

    # --- (1) Seccion del muro ---
    ax = axs[0, 0]
    # zapata
    ax.add_patch(Rectangle((0, 0), B, e_z, fc="#b0b0b0", ec="k"))
    # alzado
    ax.add_patch(Rectangle((pun, e_z), t_alz, Hm, fc="#c8c8c8", ec="k"))
    # relleno trasdos
    ax.add_patch(MplPoly([(pun + t_alz, e_z), (B, e_z), (B, e_z + Hm), (pun + t_alz, e_z + Hm)],
                         fc="#e0d2b0", ec="#b9a06a", alpha=0.7))
    # tierras delante (pasivo)
    ax.add_patch(Rectangle((0, e_z), pun, Df, fc="#e0d2b0", ec="#b9a06a", alpha=0.5))
    ax.annotate("relleno\n(γ=%.0f φ=%.0f)" % (t["gamma"] / 1e3, t["phi"]),
                (pun + t_alz + tal / 2, e_z + Hm * 0.6), ha="center", fontsize=8)
    ax.annotate("←q", (B, e_z + Hm + 0.1), fontsize=9)
    ax.plot([pun + t_alz, B], [e_z + Hm, e_z + Hm], "k--", lw=0.6)
    ax.set_xlim(-0.5, B + 0.5); ax.set_ylim(-0.5, e_z + Hm + 0.8)
    ax.set_aspect("equal"); ax.set_title("Sección del muro ménsula (B=%.2f m, H=%.2f m)" % (B, H))
    ax.set_xlabel("x [m]  (0 = puntera)"); ax.grid(True, ls=":", alpha=0.4)

    # --- (2) Diagrama de empujes (presion vs profundidad) ---
    ax = axs[0, 1]
    n = 50
    zs = [H * i / n for i in range(n + 1)]          # profundidad desde coronacion
    gw = t["gamma_w"]; zw = t["nf"]; has_w = zw is not None and zw >= 0.0
    p_soil = []; p_w = []
    sig = 0.0
    prev = 0.0
    for z in zs:
        g_eff = (t["gamma"] - gw) if (has_w and z > zw) else t["gamma"]
        p_soil.append(Ka * _sigv(t, z, has_w, zw, gw))
        p_w.append(gw * (z - zw) if (has_w and z > zw) else 0.0)
    p_q = Ka * model["sobrecarga"]
    ax.plot([p / 1e3 for p in p_soil], zs, "tab:brown", lw=2, label="activo suelo")
    ax.plot([p_q / 1e3] * len(zs), zs, "tab:orange", lw=1.5, ls="--", label="sobrecarga")
    if has_w:
        ax.plot([p / 1e3 for p in p_w], zs, "tab:blue", lw=1.5, label="agua")
    ax.fill_betweenx(zs, 0, [p / 1e3 for p in p_soil], color="tab:brown", alpha=0.15)
    ax.invert_yaxis(); ax.set_title("Empujes sobre el trasdós (Ka=%.3f)" % Ka)
    ax.set_xlabel("presión [kPa]"); ax.set_ylabel("profundidad z [m]")
    ax.legend(fontsize=8); ax.grid(True, ls=":", alpha=0.5)

    # --- (3) Presion bajo la zapata ---
    ax = axs[1, 0]
    h = veri["hundimiento"]
    p_toe = veri["puntera"]["p_borde_kPa"]; p_heel = veri["talon"]["p_borde_kPa"]
    e = h["e_m"]; Bp = h["Bp_m"]
    ax.fill([0, B, B, 0], [0, 0, max(p_heel, 0), max(p_toe, 0)], color="tab:green", alpha=0.25)
    ax.plot([0, B], [p_toe, p_heel], "tab:green", lw=2)
    ax.axhline(h["Rd_kPa"], color="r", ls="--", lw=1, label="Rd=%.0f kPa" % h["Rd_kPa"])
    ax.axhline(h["q_Ed_kPa"], color="purple", ls=":", lw=1, label="q_Ed=%.0f kPa" % h["q_Ed_kPa"])
    ax.set_title("Presión bajo la zapata (e=%.3f m, B'=%.2f m, u=%.2f)" % (e, Bp, h["u"]))
    ax.set_xlabel("x [m]  (0 = puntera)"); ax.set_ylabel("presión [kPa]")
    ax.legend(fontsize=8); ax.grid(True, ls=":", alpha=0.5)

    # --- (4) Momento flector del alzado M(z) ---
    ax = axs[1, 1]
    esf = results["alzado"]["ELU"]["esfuerzos"]
    z = [pt["z"] for pt in esf]; Mv = [pt["M"] / 1e3 for pt in esf]
    Mbase = results["alzado"]["ELU"]["M_base"] / 1e3
    z = [0.0] + z; Mv = [Mbase] + Mv
    ax.plot(Mv, z, "tab:red", lw=2); ax.fill_betweenx(z, 0, Mv, color="tab:red", alpha=0.2)
    ax.axvline(0, color="k", lw=0.8)
    ax.set_title("Alzado: momento flector M(z) — ELU (base=%.0f kN·m/m)" % abs(Mbase))
    ax.set_xlabel("M [kN·m/m]"); ax.set_ylabel("altura sobre la zapata [m]")
    ax.grid(True, ls=":", alpha=0.5)

    fig.suptitle("Muro de contención en ménsula — %s" % veri["veredicto"], fontsize=13, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    fn = os.path.join(outdir, "diag_muro.png")
    fig.savefig(fn, dpi=130); plt.close(fig)
    return [fn]


def _sigv(t, z, has_w, zw, gw):
    """Tension vertical efectiva del suelo a profundidad z (sin sobrecarga)."""
    if not has_w or z <= zw:
        return t["gamma"] * z
    return t["gamma"] * zw + (t["gamma"] - gw) * (z - zw)


if __name__ == "__main__":
    here = os.path.dirname(os.path.abspath(__file__))
    proj = sys.argv[1] if len(sys.argv) > 1 else os.path.join(here, "..", "proyecto-muro-mensula")
    model = json.load(open(os.path.join(proj, "modelo_neutro.json"), encoding="utf-8"))
    results = json.load(open(os.path.join(proj, "resultados.json"), encoding="utf-8"))
    veri = json.load(open(os.path.join(proj, "verificacion.json"), encoding="utf-8"))
    for fn in generar(model, results, veri, proj):
        print("Figura:", fn)
