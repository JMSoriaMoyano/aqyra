import sys; sys.path.insert(0,"/tmp/pylibs")
import numpy as np, matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, FancyArrow

L=11.37
# cargas (franja 1 m)
g=19.0; qudl=9.0; Ptand_char=68.3
wd=1.35*g+1.5*qudl          # 39.15 kN/m ULS
Pd=1.5*Ptand_char           # 102.45 kN ULS (tándem central)
x=np.linspace(0,L,400)
R=wd*L/2+Pd/2
# M(x): distribuida parabólica + carga central triangular
Mdist=wd*x*(L-x)/2
Mpt=np.where(x<=L/2, Pd/2*x, Pd/2*(L-x))
M=Mdist+Mpt
Mmax=M.max()
Mperm=1.35*g*L**2/8

AZUL="#1F4E79"; PASTEL="#9DB8D8"; PASTEL_S="#C7D6EC"; AMBAR="#E8B84B"
fig,(ax1,ax2)=plt.subplots(2,1,figsize=(8.6,6.4),gridspec_kw={'height_ratios':[1,1.25]})

# ---- Panel 1: esquema de carga ----
ax1.set_title("Losa de cubierta · franja de 1 m · luz 11,37 m — esquema de carga (ELU)",
              color=AZUL,fontsize=10.5,weight="bold")
ax1.plot([0,L],[0,0],color="#444",lw=3)
# apoyos (muros)
for xs in (0,L):
    ax1.add_patch(Polygon([[xs-0.25,-0.45],[xs+0.25,-0.45],[xs,0]],closed=True,
                  facecolor=PASTEL_S,edgecolor=AZUL,lw=1.2))
# UDL g+q
for xi in np.linspace(0.3,L-0.3,18):
    ax1.add_patch(FancyArrow(xi,1.05,0,-0.75,width=0.012,head_width=0.13,head_length=0.18,
                  color=PASTEL,length_includes_head=True))
ax1.plot([0.3,L-0.3],[1.05,1.05],color=AZUL,lw=1.2)
ax1.text(L/2,1.35,"g+q = 1,35·19 + 1,50·9 = 39,15 kN/m",ha="center",color=AZUL,fontsize=9)
# tándem 2 ejes a 1.2 m, central
for xi in (L/2-0.6,L/2+0.6):
    ax1.add_patch(FancyArrow(xi,2.1,0,-1.55,width=0.05,head_width=0.28,head_length=0.28,
                  color=AMBAR,length_includes_head=True,ec="#8a6d1f"))
ax1.text(L/2,2.35,"Tándem LM1  2×(1,5·… )=102,4 kN  (eje 300 kN)",ha="center",color="#8a6d1f",fontsize=9)
ax1.annotate(f"R = {R:.0f} kN",(0,-0.6),ha="center",va="top",fontsize=9,color="#444")
ax1.annotate(f"R = {R:.0f} kN",(L,-0.6),ha="center",va="top",fontsize=9,color="#444")
ax1.set_xlim(-0.8,L+0.8); ax1.set_ylim(-1.1,2.7); ax1.axis("off")

# ---- Panel 2: diagrama de momentos (transparencia, convención despacho) ----
ax2.set_title("Diagrama de flexión M(x) en ELU",color=AZUL,fontsize=10.5,weight="bold")
ax2.fill_between(x,0,-M,color=PASTEL,alpha=0.45,edgecolor=AZUL,lw=1.6)  # M positivo dibujado hacia abajo (tracción inferior)
ax2.plot([0,L],[0,0],color="#444",lw=2)
ax2.annotate(f"M_max = {Mmax:.1f} kN·m/m",(L/2,-Mmax),ha="center",va="top",fontsize=10,
             weight="bold",color=AZUL)
ax2.plot(L/2,-Mmax,'o',color=AZUL,ms=5)
# desglose
ax2.text(0.4,-Mmax*0.78,
   f"Permanente: {Mperm:.0f}\n+ UDL LM1: {1.5*qudl*L**2/8:.0f}\n+ Tándem LM1: {Pd*L/4:.0f}\n= {Mmax:.0f} kN·m/m",
   fontsize=8.6,color="#333",va="center",
   bbox=dict(boxstyle="round,pad=0.4",fc="#F2F6FC",ec=AZUL,lw=0.8))
ax2.text(L-0.3,-Mmax*0.25,"η flexión = 0,75\n(M_Rd = 1.235 kN·m/m, φ25/100)",
   fontsize=8.6,color="#2E7D32",ha="right",
   bbox=dict(boxstyle="round,pad=0.4",fc="#EAF4EA",ec="#2E7D32",lw=0.8))
ax2.set_xlim(-0.8,L+0.8); ax2.set_ylim(-Mmax*1.18,Mmax*0.18)
ax2.set_xlabel("x (m)",fontsize=9); ax2.set_yticks([])
for s in ("top","right","left"): ax2.spines[s].set_visible(False)
ax2.tick_params(labelsize=8.5)
plt.tight_layout()
fig.savefig("/tmp/flexion_losa_cubierta.png",dpi=160,bbox_inches="tight",facecolor="white")
print("Mmax=%.1f  R=%.1f  Mperm=%.1f"%(Mmax,R,Mperm))
