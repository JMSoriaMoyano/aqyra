"""
Diagramas del Caso 13 - Losa plana postesada (EC2 §5.10 + §6.4.4). Backend Agg.

  - planta_tendones.png        : banded X (sobre pilares) + distribuido Y
  - cargas_equivalentes_2d.png : w_px + w_py vs permanente (residual ~0)
  - mapa_Mx.png / mapa_My.png  : mapas de momentos (ELU, sagging)
  - mapa_tension_fibra.png     : tension de fibra inferior por franja (rara)
  - perimetro_punzonamiento.png: u1 a 2d + tendones que lo cruzan
  - ELU_franjas.png            : M_Rd vs M_Ed por franja (campo/apoyo)
  - mapa_flecha.png            : flecha ELS caracteristica (con pretensado)
"""
import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.tri as mtri
import numpy as np


def _save(fig, path):
    fig.tight_layout(); fig.savefig(path, dpi=130); plt.close(fig); return path


def _mapa(quads, key, titulo, fname, signo=-1.0, unidad="kN·m/m"):
    x = np.array([q["x"] for q in quads]); y = np.array([q["y"] for q in quads])
    v = np.array([q[key] for q in quads]) * signo / 1e3
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, v, levels=14, cmap="RdYlBu_r")
    ax.tricontour(tri, v, levels=14, colors="k", linewidths=0.2, alpha=0.4)
    cb = fig.colorbar(c, ax=ax); cb.set_label(unidad)
    ax.set_aspect("equal"); ax.set_title(titulo)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    i = int(np.argmax(v)); ax.plot(x[i], y[i], "k*", ms=10)
    ax.annotate("%.1f" % v[i], (x[i], y[i]), fontsize=9, fontweight="bold")
    return _save(fig, fname)


def planta_tendones(model, out, fname):
    info = out["balance_2d"]
    pil = model["pilares"]
    xs = sorted(set(round(p["x"], 3) for p in pil))
    ys = sorted(set(round(p["y"], 3) for p in pil))
    x0, x1 = min(xs), max(xs); y0, y1 = min(ys), max(ys)
    fig, ax = plt.subplots(figsize=(6.4, 6.0))
    ax.add_patch(mpatches.Rectangle((x0, y0), x1 - x0, y1 - y0, fill=True,
                                    color="0.95", ec="0.5"))
    # banded X: bandas sobre las lineas de pilares (y = cada fila)
    bw = 1.2
    for yy in ys:
        ax.add_patch(mpatches.Rectangle((x0, yy - bw / 2), x1 - x0, bw,
                                        color="tab:red", alpha=0.25))
        ax.plot([x0, x1], [yy, yy], "r-", lw=1.5)
    # distribuido Y: tendones cada 0.8 m
    sep = 0.8
    yv = np.arange(x0, x1 + 1e-6, sep)
    for xx in yv:
        ax.plot([xx, xx], [y0, y1], "b-", lw=0.6, alpha=0.6)
    for p in pil:
        ax.add_patch(mpatches.Rectangle((p["x"] - p["lado"] / 2, p["y"] - p["lado"] / 2),
                                        p["lado"], p["lado"], color="0.3", zorder=5))
    ax.set_xlim(x0 - 1, x1 + 1); ax.set_ylim(y0 - 1, y1 + 1)
    ax.set_aspect("equal")
    ax.set_title("Planta de tendones: banded X (rojo) + distribuido Y (azul)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    ax.legend(handles=[mpatches.Patch(color="tab:red", alpha=0.4, label="banded X (sobre pilares)"),
                       mpatches.Patch(color="tab:blue", alpha=0.6, label="distribuido Y")],
              loc="upper right", fontsize=8)
    return _save(fig, fname)


def cargas_equivalentes_2d(out, fname):
    bal = out["balance_2d"]
    perm = out["modelo_resumen"]["permanente_kN_m2"]
    fig, ax = plt.subplots(figsize=(6.5, 4))
    barras = ["w_px (X)", "w_py (Y)", "w_p total", "permanente", "residual"]
    vals = [bal["w_px_N_m2"] / 1e3, bal["w_py_N_m2"] / 1e3, bal["w_p_N_m2"] / 1e3,
            perm, bal["residual_N_m2"] / 1e3]
    cols = ["tab:red", "tab:red", "tab:orange", "tab:blue", "tab:green"]
    ax.bar(barras, vals, color=cols)
    for i, v in enumerate(vals):
        ax.annotate("%.2f" % v, (i, v), ha="center", va="bottom", fontsize=9)
    ax.set_ylabel("carga [kN/m2]")
    ax.set_title("Balance de cargas 2D (residual %.3f%%)" % bal["residual_pct"])
    ax.grid(alpha=0.3, axis="y")
    return _save(fig, fname)


def mapa_tension_fibra(out, fname):
    ver = out["verificacion"]["tensiones_franja"]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    estados = ["transferencia", "servicio_cuasiperm", "servicio_rara"]
    franjas = list(ver.keys())
    x = np.arange(len(estados)); wbar = 0.35
    for j, fr in enumerate(franjas):
        inf = [ver[fr][e]["sigma_inf_MPa"] for e in estados]
        ax.bar(x + (j - 0.5) * wbar, inf, wbar, label="%s (fibra inf)" % fr)
    ax.axhline(0, color="k", lw=0.8)
    ax.axhline(out["modelo_resumen"]["fctm_MPa"], color="g", ls="--", label="fctm")
    ax.set_xticks(x); ax.set_xticklabels(estados, fontsize=8)
    ax.set_ylabel("sigma fibra inferior [MPa] (compr<0)")
    ax.set_title("Tensiones por fibra y franja")
    ax.legend(fontsize=7); ax.grid(alpha=0.3, axis="y")
    return _save(fig, fname)


def perimetro_punzonamiento(model, out, fname):
    pil = model["pilares"]
    # pilar interior (centro de la malla)
    xs = sorted(set(round(p["x"], 3) for p in pil)); ys = sorted(set(round(p["y"], 3) for p in pil))
    xc, yc = xs[len(xs) // 2], ys[len(ys) // 2]
    pint = min(pil, key=lambda p: (p["x"] - xc) ** 2 + (p["y"] - yc) ** 2)
    punz = out["verificacion"]["punzonamiento"].get("interior")
    fig, ax = plt.subplots(figsize=(6, 6))
    lado = pint["lado"]
    d = 0.25 - 0.030 - 0.016
    ax.add_patch(mpatches.Rectangle((pint["x"] - lado / 2, pint["y"] - lado / 2),
                                    lado, lado, color="0.3", zorder=5, label="pilar"))
    # perimetro de control u1 (rectangulo redondeado a 2d, aprox)
    a = lado + 4 * d
    ax.add_patch(mpatches.Rectangle((pint["x"] - a / 2, pint["y"] - a / 2), a, a,
                                    fill=False, ec="tab:red", lw=2, ls="--",
                                    label="u1 (2d)"))
    # tendones que cruzan u1: banded X (horizontal) + distribuido Y (vertical)
    for off in np.arange(-a / 2, a / 2 + 1e-6, 0.8):
        ax.plot([pint["x"] + off, pint["x"] + off], [pint["y"] - a / 2 - 0.5, pint["y"] + a / 2 + 0.5],
                "b-", lw=0.6, alpha=0.6)
    ax.plot([pint["x"] - a / 2 - 0.5, pint["x"] + a / 2 + 0.5], [pint["y"], pint["y"]],
            "r-", lw=2)
    ax.set_xlim(pint["x"] - a, pint["x"] + a); ax.set_ylim(pint["y"] - a, pint["y"] + a)
    ax.set_aspect("equal")
    tit = "Perimetro de control u1 (pilar interior)"
    if punz:
        tit += "\nV_p=%.0f kN  u SIN=%.2f / CON=%.2f" % (
            punz["V_p_kN"], punz["sin_pretensado"]["u_vRdc"], punz["con_pretensado"]["u_vRdc"])
    ax.set_title(tit, fontsize=9)
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    ax.legend(fontsize=8, loc="upper right")
    return _save(fig, fname)


def ELU_franjas(out, fname):
    elu = out["verificacion"]["ELU_flexion"]
    fig, ax = plt.subplots(figsize=(7, 4.2))
    etiquetas, med, mrd = [], [], []
    for fr, e in elu.items():
        for pos in ("campo", "apoyo"):
            etiquetas.append("%s\n%s" % (fr, pos))
            med.append(e[pos]["M_Ed_kNm_m"]); mrd.append(e[pos]["M_Rd_kNm_m"])
    x = np.arange(len(etiquetas)); w = 0.38
    ax.bar(x - w / 2, med, w, label="M_Ed", color="tab:orange")
    ax.bar(x + w / 2, mrd, w, label="M_Rd", color="tab:green")
    ax.set_xticks(x); ax.set_xticklabels(etiquetas, fontsize=7)
    ax.set_ylabel("M [kN*m/m]"); ax.set_title("ELU flexion por fibras (activa+pasiva)")
    ax.legend(fontsize=8); ax.grid(alpha=0.3, axis="y")
    return _save(fig, fname)


def mapa_flecha(res, fname):
    defl = res["losa"]["ELS_car"]["deformada"]
    x = np.array([p["x"] for p in defl]); y = np.array([p["y"] for p in defl])
    w = np.array([p["dz"] for p in defl]) * 1e3
    fig, ax = plt.subplots(figsize=(6.2, 5.4))
    tri = mtri.Triangulation(x, y)
    c = ax.tricontourf(tri, w, levels=14, cmap="viridis")
    cb = fig.colorbar(c, ax=ax); cb.set_label("dz [mm] (+arriba)")
    ax.set_aspect("equal"); ax.set_title("Flecha ELS caracteristica (con pretensado)")
    ax.set_xlabel("x [m]"); ax.set_ylabel("y [m]")
    return _save(fig, fname)


def generar(model, res, out, carpeta):
    os.makedirs(carpeta, exist_ok=True)
    files = []
    quads = res["losa"]["ELU"]["quads"]
    files.append(planta_tendones(model, out, os.path.join(carpeta, "planta_tendones.png")))
    files.append(cargas_equivalentes_2d(out, os.path.join(carpeta, "cargas_equivalentes_2d.png")))
    files.append(_mapa(quads, "Mx", "Momento losa Mx (sagging) - ELU",
                       os.path.join(carpeta, "mapa_Mx.png")))
    files.append(_mapa(quads, "My", "Momento losa My (sagging) - ELU",
                       os.path.join(carpeta, "mapa_My.png")))
    files.append(mapa_tension_fibra(out, os.path.join(carpeta, "mapa_tension_fibra.png")))
    files.append(perimetro_punzonamiento(model, out, os.path.join(carpeta, "perimetro_punzonamiento.png")))
    files.append(ELU_franjas(out, os.path.join(carpeta, "ELU_franjas.png")))
    files.append(mapa_flecha(res, os.path.join(carpeta, "mapa_flecha.png")))
    return files
