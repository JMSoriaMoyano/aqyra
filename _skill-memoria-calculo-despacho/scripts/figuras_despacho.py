# -*- coding: utf-8 -*-
"""Libreria de figuras del despacho (matplotlib).

REGLA: los ESQUEMAS de carga/seccion van en pastel SOLIDO (alpha=1);
los DIAGRAMAS de esfuerzos van con TRANSPARENCIA (ALPHA_DIAG).

Funciones de alto nivel:
- esquema_portico(...), esquema_columna(...)      -> esquemas SOLIDOS
- diagrama_portico(...), diagrama_columna(...)     -> diagramas TRANSLUCIDOS
- grafico_aprovechamientos(items)                  -> barras de eta con limite 1,0
Primitivas: diag_member(), paleta de colores.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Polygon, FancyArrow
import numpy as np

# ---- paleta pastel ----
AZUL = "#1F4E79"
PAS_AZUL = "#A6C5E8"; ED_AZUL = "#2E6DA4"      # axil N
PAS_VERDE = "#B5DDA8"; ED_VERDE = "#4F8A45"    # cortante V
PAS_ROJO = "#F3B0AA"; ED_ROJO = "#C0504D"      # momento M
PAS_HORM = "#D8DCE0"; PAS_TIERRA = "#E7D8B8"
PAS_AMBAR = "#E6A100"
ALPHA_DIAG = 0.45     # transparencia SOLO en diagramas
SOLIDO = 1.0          # esquemas


def _save(fig, path, dpi=160):
    fig.tight_layout(); fig.savefig(path, dpi=dpi, bbox_inches="tight"); plt.close(fig)


# ======================== primitiva de diagrama ========================
def diag_member(ax, P0, P1, s, val, scale, face, edge, sign=1, alpha=ALPHA_DIAG):
    """Dibuja un diagrama (relleno pastel translucido) perpendicular a una barra."""
    P0 = np.array(P0, float); P1 = np.array(P1, float)
    L = np.linalg.norm(P1 - P0); u = (P1 - P0) / L
    n = np.array([-u[1], u[0]]) * sign
    base = np.array([P0 + u * si for si in s])
    tip = np.array([base[i] + n * (val[i] * scale) for i in range(len(s))])
    ax.add_patch(Polygon(np.vstack([base, tip[::-1]]), closed=True, facecolor=face,
                         edgecolor="none", alpha=alpha, zorder=2))
    ax.plot(tip[:, 0], tip[:, 1], color=edge, lw=1.3, zorder=3)
    ax.plot(base[:, 0], base[:, 1], color=AZUL, lw=2.2, zorder=4)


# ======================== ESQUEMAS (solido) ========================
def esquema_portico(path, luz=6.0, altura=4.0, q_texto="q$_{Ed}$ = 1,35·G + 1,50·Q"):
    N1, N2, N3, N4 = (0, 0), (0, altura), (luz, altura), (luz, 0)
    fig, ax = plt.subplots(figsize=(6.4, 4.6))
    for a, b in [(N1, N2), (N2, N3), (N3, N4)]:
        ax.plot([a[0], b[0]], [a[1], b[1]], color=AZUL, lw=3, zorder=4, solid_capstyle="round")
    for nd in (N1, N4):
        ax.add_patch(Polygon([(nd[0]-0.25, nd[1]-0.45), (nd[0]+0.25, nd[1]-0.45), (nd[0], nd[1])],
                             closed=True, facecolor=PAS_HORM, edgecolor=AZUL, alpha=SOLIDO, zorder=3))
        ax.text(nd[0], nd[1]-0.7, "articulado", ha="center", fontsize=8, color="#555")
    for xx in np.linspace(0.2, luz-0.2, 13):
        ax.add_patch(FancyArrow(xx, altura+1.05, 0, -0.85, width=0.015, head_width=0.16,
                                head_length=0.18, length_includes_head=True,
                                color=PAS_VERDE, ec=ED_VERDE, alpha=SOLIDO, zorder=5))
    ax.plot([0, luz], [altura+1.05, altura+1.05], color=ED_VERDE, lw=1.2)
    ax.text(luz/2, altura+1.55, q_texto, ha="center", color=ED_VERDE, fontsize=9.5)
    ax.annotate("", (-0.9, 0), (-0.9, altura), arrowprops=dict(arrowstyle="<->", color="#555"))
    ax.text(-1.05, altura/2, f"h = {altura:.1f} m", rotation=90, va="center", ha="right",
            fontsize=8.5, color="#333")
    ax.text(luz/2, altura+0.15, f"L = {luz:.1f} m", ha="center", color=AZUL, fontsize=9)
    ax.set_xlim(-1.8, luz+0.8); ax.set_ylim(-1.1, altura+2.0)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Portico - esquema de cargas (ELU)", color=AZUL, fontsize=10.5, weight="bold")
    _save(fig, path)


def esquema_columna(path, H=8.0, N_cabeza="N", H_horiz="H", viento="q", B=6.0):
    fig, ax = plt.subplots(figsize=(5.6, 5.2))
    ax.add_patch(Rectangle((-0.75, 0), 1.5, H, facecolor=PAS_HORM, edgecolor=AZUL, lw=1.6, alpha=SOLIDO, zorder=3))
    ax.add_patch(Rectangle((-B/2, -1.4), B, 1.4, facecolor=PAS_HORM, edgecolor=AZUL, lw=1.6, alpha=SOLIDO, zorder=3))
    ax.add_patch(Rectangle((-B/2-1.2, -1.4), B+2.4, 1.4, facecolor=PAS_TIERRA, edgecolor="none", alpha=SOLIDO, zorder=1))
    for xx in np.linspace(-B/2+0.6, B/2-0.6, 7):
        ax.plot([xx, xx], [-1.4, -1.75], color=ED_VERDE, lw=1, alpha=SOLIDO)
    ax.text(0, -2.05, "resortes Winkler (cimentacion)", ha="center", fontsize=8, color="#555")
    ax.add_patch(Rectangle((-0.5, H), 1.0, 0.35, facecolor=PAS_VERDE, edgecolor=ED_VERDE, alpha=SOLIDO, zorder=4))
    ax.text(0.7, H+0.18, "aparato de apoyo", fontsize=8, color="#555", va="center")
    ax.add_patch(FancyArrow(0, H+1.7, 0, -1.2, width=0.06, head_width=0.28, head_length=0.28,
                            length_includes_head=True, color=PAS_AZUL, ec=ED_AZUL, alpha=SOLIDO, zorder=6))
    ax.text(0.2, H+1.4, N_cabeza, color=ED_AZUL, fontsize=9)
    ax.add_patch(FancyArrow(-2.0, H+0.15, 1.3, 0, width=0.06, head_width=0.28, head_length=0.28,
                            length_includes_head=True, color=PAS_ROJO, ec=ED_ROJO, alpha=SOLIDO, zorder=6))
    ax.text(-3.9, H+0.15, H_horiz, color=ED_ROJO, fontsize=8.5, va="center")
    for yy in np.linspace(0.6, H-0.4, 7):
        ax.add_patch(FancyArrow(1.6, yy, -0.75, 0, width=0.02, head_width=0.16, head_length=0.14,
                                length_includes_head=True, color=PAS_ROJO, ec=ED_ROJO, alpha=SOLIDO, zorder=5))
    ax.text(1.7, H/2, viento, color=ED_ROJO, fontsize=8, va="center")
    ax.annotate("", (3.4, 0), (3.4, H), arrowprops=dict(arrowstyle="<->", color="#555"))
    ax.text(3.6, H/2, f"H = {H:.1f} m", rotation=90, va="center", fontsize=8.5, color="#333")
    ax.set_xlim(-4.3, 4.6); ax.set_ylim(-2.4, H+2.2)
    ax.set_aspect("equal"); ax.axis("off")
    ax.set_title("Pila/columna - esquema de cargas (ELU)", color=AZUL, fontsize=10.5, weight="bold")
    _save(fig, path)


# ======================== DIAGRAMAS (translucido) ========================
def diagrama_portico(path, Mb, Vb, Nb, luz=6.0, altura=4.0, titulo="Diagramas de esfuerzos (ELU)"):
    """Mb, Vb: dict barra->(x_array, val_array) en kN·m y kN. Nb: dict barra->axil (kN).
    Barras: 'C1' (N1->N2), 'B1' (N2->N3), 'C2' (N3->N4)."""
    N1, N2, N3, N4 = (0, 0), (0, altura), (luz, altura), (luz, 0)
    members = {"C1": (N1, N2), "B1": (N2, N3), "C2": (N3, N4)}
    fig, axes = plt.subplots(1, 3, figsize=(11.0, 4.2))
    mmax = max(np.max(np.abs(Mb[b][1])) for b in members)
    vmax = max(np.max(np.abs(Vb[b][1])) for b in members)
    nmax = max(abs(v) for v in Nb.values())
    sc_M, sc_V, sc_N = 1.6/mmax, 1.4/vmax, 1.2/nmax
    axN, axV, axM = axes
    for ax in axes:
        for a, b in members.values():
            ax.plot([a[0], b[0]], [a[1], b[1]], color=AZUL, lw=3, zorder=4)
        for nd in (N1, N4):
            ax.add_patch(Polygon([(nd[0]-0.25, nd[1]-0.45), (nd[0]+0.25, nd[1]-0.45), (nd[0], nd[1])],
                                 closed=True, facecolor=PAS_HORM, edgecolor=AZUL, alpha=0.9, zorder=3))
    for b, (a, c) in members.items():
        diag_member(axM, a, c, Mb[b][0], Mb[b][1], sc_M, PAS_ROJO, ED_ROJO)
        diag_member(axV, a, c, Vb[b][0], Vb[b][1], sc_V, PAS_VERDE, ED_VERDE)
        ss = np.array([0.0, np.linalg.norm(np.array(c)-np.array(a))])
        diag_member(axN, a, c, ss, np.array([Nb[b], Nb[b]]), sc_N, PAS_AZUL, ED_AZUL)
    for ax, t in [(axN, "Axil N (kN)"), (axV, "Cortante V (kN)"), (axM, "Momento M (kN·m)")]:
        ax.set_xlim(-1.6, luz+1.6); ax.set_ylim(-1.2, altura+2.2)
        ax.set_aspect("equal"); ax.axis("off")
        ax.set_title(t, color=AZUL, fontsize=10.5, weight="bold")
    fig.suptitle(titulo, color=AZUL, fontsize=11.5, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.95]); fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig)


def diagrama_columna(path, H=8.0, N_base=0.0, V_base=0.0, M_base=0.0, N_top=None,
                     titulo="Diagramas de esfuerzos (ELU, esquematicos)"):
    """Diagramas N/V/M esquematicos de una columna en mensula, anclados a los valores de base."""
    s = np.linspace(0, H, 21)
    if N_top is None:
        N_top = N_base
    N_s = N_base + (N_top - N_base) * (s / H)
    V_s = 0.95*V_base + (V_base - 0.95*V_base) * (1 - s / H)
    M_s = M_base * ((H - s) / H) ** 1.12
    fig, axes = plt.subplots(1, 3, figsize=(9.6, 4.6))
    data = [("Axil N (kN)", N_s, PAS_AZUL, ED_AZUL, f"{N_base:.0f}"),
            ("Cortante V (kN)", V_s, PAS_VERDE, ED_VERDE, f"{V_base:.1f}"),
            ("Momento M (kN·m)", M_s, PAS_ROJO, ED_ROJO, f"{M_base:.0f}")]
    for ax, (title, vals, face, edge, lab) in zip(axes, data):
        ax.plot([0, 0], [0, H], color=AZUL, lw=2.4, zorder=4)
        sc = 2.4 / max(np.max(np.abs(vals)), 1e-9)
        xv = vals * sc
        ax.fill_betweenx(s, 0, xv, facecolor=face, alpha=ALPHA_DIAG, zorder=2)
        ax.plot(xv, s, color=edge, lw=1.4, zorder=3)
        ax.scatter([xv[0]], [0], color=edge, s=18, zorder=5)
        ax.text(xv[0], -0.5, lab, ha="center", color=edge, fontsize=9, weight="bold")
        ax.text(0.05, H+0.15, "cabeza", fontsize=7.5, color="#777")
        ax.text(0.05, -0.9, "base", fontsize=7.5, color="#777")
        ax.set_title(title, color=AZUL, fontsize=10, weight="bold")
        ax.set_xlim(-0.5, 3.1); ax.set_ylim(-1.3, H+0.8); ax.axis("off")
    fig.suptitle(titulo, color=AZUL, fontsize=11, weight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.94]); fig.savefig(path, dpi=160, bbox_inches="tight"); plt.close(fig)


def grafico_aprovechamientos(path, items, titulo="Aprovechamientos por comprobacion"):
    """items: lista de (etiqueta, eta). Barras coloreadas por nivel con limite eta=1,0."""
    labels = [a for a, _ in items][::-1]
    vals = [b for _, b in items][::-1]
    cols = ["#2E7D32" if v < 0.85 else (PAS_AMBAR if v <= 1.0 else "#B00000") for v in vals]
    fig, ax = plt.subplots(figsize=(7.4, max(2.4, 0.5*len(items)+1.2)))
    bars = ax.barh(labels, vals, color=cols, edgecolor="white", height=0.62)
    ax.axvline(1.0, color="#B00000", lw=1.4, ls="--")
    ax.text(1.0, len(labels)-0.3, " limite eta = 1,0", color="#B00000", fontsize=8.5, va="center")
    for b, v in zip(bars, vals):
        ax.text(b.get_width()+0.015, b.get_y()+b.get_height()/2, f"{v:.3f}".replace(".", ","),
                va="center", fontsize=8.8, color="#222")
    ax.set_xlim(0, 1.15); ax.set_xlabel("Coeficiente de aprovechamiento  eta = E_d / R_d", fontsize=9)
    ax.set_title(titulo, color=AZUL, fontsize=10.5, weight="bold")
    ax.spines["top"].set_visible(False); ax.spines["right"].set_visible(False)
    ax.tick_params(labelsize=8.8)
    _save(fig, path)
